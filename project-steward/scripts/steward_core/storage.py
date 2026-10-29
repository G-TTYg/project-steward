"""STATE is the atomic commit point; LOG/HANDOFF are revisioned repairable views.

An ordered event journal preserves log history inside authoritative state. This
does not claim a multi-file transaction or power-loss durability on all filesystems.
Local OS locks serialize helper writers and release automatically after a crash.
"""

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile

from .state import require, validate

MANAGED_FILES = ("PLAN.md", "LOG.md", "HANDOFF.md", "STATE.json")
START = "<!-- project-steward:status:start -->"
END = "<!-- project-steward:status:end -->"


def check_managed_paths(run: Path) -> None:
    require(run.is_dir(), f"run directory does not exist: {run}")
    for name in MANAGED_FILES:
        path = run / name
        require(not path.is_symlink() and path.resolve().parent == run
                and (not path.exists() or path.is_file()),
                f"managed recovery file must be a regular file inside the run: {path}")


def read_state(run: Path) -> dict:
    check_managed_paths(run)
    try:
        state = json.loads((run / "STATE.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"cannot read initialized run state at {run}: {exc}") from None
    require(isinstance(state, dict), "run state must be an object")
    version = state.get("schema_version", 1)
    require(type(version) is int and version in (1, 2, 3), f"unsupported run-state schema: {version}")
    if version == 3:
        validate(state)
    else:
        require(isinstance(state.get("project"), str) and bool(state["project"])
                and isinstance(state.get("task"), str), "legacy state requires project path and task")
    return state


def log_view(state: dict, revision: int | None = None) -> str:
    revision = state["revision"] if revision is None else revision
    return (f"<!-- project-steward:revision:{revision} -->\n" + state["log_prefix"]
            + "".join(event["text"] for event in state["events"][:revision]))


def split_handoff(text: str) -> tuple[str, str, str] | None:
    if START not in text and END not in text:
        return None
    require(text.count(START) == 1 and text.count(END) == 1 and text.index(START) < text.index(END),
            "malformed generated handoff markers; preserve notes and repair markers before updating")
    before, rest = text.split(START)
    block, after = rest.split(END)
    return before, block, after


def handoff_view(state: dict, previous: str) -> str:
    block = render_handoff(state)
    require(START not in block and END not in block, "content contains reserved handoff markers")
    parts = split_handoff(previous)
    if parts:
        return parts[0] + START + "\n" + block + "\n" + END + parts[2]
    notes = ("## Preserved Legacy Handoff\n\n" + previous) if previous else (
        "## Maintainer Notes\n\nKeep continuation context and canonical file/symbol pointers here.\n")
    return f"# Handoff: {state['task']}\n\n{START}\n{block}\n{END}\n\n{notes}"


def render_handoff(state: dict) -> str:
    milestones = {item["id"]: item for item in state["milestones"]}
    last = milestones.get(state["last_verified"])
    current = milestones.get(state["current_milestone"])
    last_text = (f"{last['id']} · {last['name']} · {last['verification']}\n"
                 f"Commit: {last.get('commit', 'not attached')} (caller-attached, not proof of ownership)") if last else "None recorded."
    current_text = f"{current['id']} · {current['name']} · {current['status']}" if current else state.get("current_slice_name") or "Not associated."
    pending = [f"{m['id']} ({m['status']})" for m in state["milestones"] if m["status"] != "verified"]
    evidence = state["evidence"][-3:]
    evidence_text = "\n".join(
        f"- {e['id']} / {e['milestone_id']}: {e['status']}; reported (claimed {e['claimed_source']}); "
        f"{e['summary']}; revision: {e.get('revision') or 'unspecified'}; scope: {e.get('scope') or 'unspecified'}"
        for e in evidence) or "- No structured evidence recorded."
    observed = state["git"]
    git_text = (f"Branch: {observed.get('branch')}; HEAD: {observed.get('head') or 'unborn'}; "
                f"dirty paths: {len(observed.get('dirty') or [])}; upstream: {observed.get('upstream') or 'unknown'}; "
                f"unpushed: {observed.get('unpushed_count') if observed.get('unpushed_count') is not None else 'unknown'}") if observed.get("available") else observed.get("reason", "Git not observed.")
    return f"""Revision: {state['revision']} · Updated: {state['updated_at']}
Task: {state['task']}
Project: `{state['project']['root_relative']}` relative to this run directory
Run: {state['run_id']} · {state['status']}

## Next Safest Step

{state['next'] or 'Reobserve the project and identify the next authorized action.'}

## Current Progress

{state['summary']}

- Current milestone: {current_text}
- Latest verified slice: {last_text}
- Unverified or skipped milestones: {', '.join(pending) or 'None recorded.'}

## Key Evidence

{state['verification']}

{evidence_text}

The recorder does not run checks or attest imported claims. Historical passes
apply only to their recorded version/scope. Run closure does not verify milestones.

## Do Not Assume

{state.get('risk') or 'No additional risks recorded; this does not establish absence of risk.'}

## Git Observation

{git_text}
Observed before this recovery write/commit. Compare current HEAD, status/diffs,
affected contracts and blockers before acting. No branch, deployment, or merge is inferred.

Query PLAN.md for missing acceptance/scope, LOG.md for a chronology gap, and STATE.json
for exact evidence/history. Follow canonical file/symbol pointers in the notes below."""


def view_issues(run: Path, state: dict) -> list[str]:
    issues = []
    for name in MANAGED_FILES:
        if not (run / name).is_file():
            issues.append(f"missing {name}")
    migration = state.get("migration", {})
    if legacy_file_unchanged(run, state, "PLAN.md") and (run / "PLAN.md").read_text(encoding="utf-8") != migration.get("plan_text"):
        issues.append("PLAN.md migration replacement is incomplete")
    if (run / "LOG.md").is_file() and (run / "LOG.md").read_text(encoding="utf-8") != log_view(state):
        issues.append("LOG.md revision/content differs from authoritative STATE.json")
    if (run / "HANDOFF.md").is_file():
        previous = (run / "HANDOFF.md").read_text(encoding="utf-8")
        if previous != handoff_view(state, previous):
            issues.append("HANDOFF.md revision/content differs from authoritative STATE.json")
    return issues


def legacy_file_unchanged(run: Path, state: dict, name: str) -> bool:
    expected = state.get("migration", {}).get("legacy_file_hashes", {}).get(name)
    return bool(expected and (run / name).is_file()
                and hashlib.sha256((run / name).read_bytes()).hexdigest() == expected)


def replace_files(run: Path, contents: dict[str, str]) -> None:
    """Prepare/fsync every temp file before replacing STATE and then derived views."""
    check_managed_paths(run)
    prepared = {}
    try:
        for name, content in contents.items():
            fd, temporary = tempfile.mkstemp(prefix=".steward-tmp-", dir=run)
            prepared[name] = Path(temporary)
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        for name, temporary in prepared.items():
            os.replace(temporary, run / name)
    finally:
        for temporary in prepared.values():
            temporary.unlink(missing_ok=True)


def save_run(run: Path, state: dict, expected_revision: int | None) -> None:
    validate(state)
    if expected_revision is not None:
        require(read_state(run).get("revision") == expected_revision,
                "state changed concurrently; re-read before retrying")
    previous = (run / "HANDOFF.md").read_text(encoding="utf-8") if (run / "HANDOFF.md").exists() else ""
    handoff = handoff_view(state, previous)
    replace_files(run, {"STATE.json": json.dumps(state, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                        "LOG.md": log_view(state), "HANDOFF.md": handoff})


def repair_views(run: Path, state: dict) -> None:
    migration = state.get("migration", {})
    plan_repair = (not (run / "PLAN.md").exists() or legacy_file_unchanged(run, state, "PLAN.md")) and "plan_text" in migration
    require((run / "PLAN.md").is_file() or plan_repair, "missing PLAN.md is not derivable; restore it from backup")
    if (run / "LOG.md").exists():
        existing = (run / "LOG.md").read_text(encoding="utf-8")
        require(legacy_file_unchanged(run, state, "LOG.md") or any(existing == log_view(state, revision) for revision in range(1, state["revision"] + 1)),
                "LOG.md contains unrecognized edits; preserve it externally before repair")
    previous = (run / "HANDOFF.md").read_text(encoding="utf-8") if (run / "HANDOFF.md").exists() else ""
    if legacy_file_unchanged(run, state, "HANDOFF.md"):
        previous = migration["handoff_seed"]
    contents = {"LOG.md": log_view(state), "HANDOFF.md": handoff_view(state, previous)}
    if plan_repair:
        contents["PLAN.md"] = migration["plan_text"]
    replace_files(run, contents)


@contextmanager
def run_lock(run: Path):
    directory = Path(tempfile.gettempdir()) / "project-steward-locks"
    directory.mkdir(exist_ok=True)
    name = hashlib.sha256(os.path.normcase(str(run)).encode()).hexdigest()
    with (directory / name).open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise SystemExit("another local helper writer holds this run; retry after it exits") from None
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
