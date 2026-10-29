#!/usr/bin/env python3
"""Manage project-local recovery state without certifying tests or committing code.

The CLI owns four recovery files. Generated handoff status is replaceable; text
outside its markers belongs to maintainers and survives updates. Git snapshots
are observations taken before writing/committing the current recovery checkpoint.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import subprocess
from typing import Any

MANAGED_FILES = ("PLAN.md", "LOG.md", "HANDOFF.md", "STATE.json")
START = "<!-- project-steward:status:start -->"
END = "<!-- project-steward:status:end -->"
VERIFIED = {"verified", "complete"}
STATUSES = ["active", "paused", "blocked", "verified", "complete"]


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def slugify(text: str, limit: int = 48) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")[:limit].rstrip("-") or "task"


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def check_managed_paths(run: Path) -> None:
    for name in MANAGED_FILES:
        path = run / name
        if path.is_symlink() or path.resolve().parent != run or (path.exists() and not path.is_file()):
            raise SystemExit(f"managed recovery file must be a regular file inside the run: {path}")


def read_state(run: Path) -> dict[str, Any]:
    try:
        state = json.loads((run / "STATE.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"cannot read initialized run state at {run}: {exc}") from None
    if (not isinstance(state, dict) or not isinstance(state.get("project"), str)
            or not state["project"] or not isinstance(state.get("task"), str)):
        raise SystemExit("run state must be an object with its initialized project path and task")
    version = state.get("schema_version", 1)
    if type(version) is not int or version not in (1, 2):
        raise SystemExit(f"unsupported run-state schema: {version}")
    milestones = state.setdefault("milestones", [])
    if not isinstance(milestones, list) or any(not isinstance(item, dict) for item in milestones):
        raise SystemExit("run-state milestones must be a list of objects")
    if not isinstance(state.get("workflow", {}), dict):
        raise SystemExit("run-state workflow must be an object")
    last = state.get("last_verified")
    if last is not None and not isinstance(last, dict):
        raise SystemExit("run-state last_verified must be an object or null")
    if "last_verified" not in state:
        state["last_verified"] = next(
            (item.copy() for item in reversed(milestones) if item.get("status") in VERIFIED), None
        )
    state["schema_version"] = 2
    return state


def load_run(run: Path) -> dict[str, Any]:
    if not run.is_dir():
        raise SystemExit(f"run directory does not exist: {run}")
    check_managed_paths(run)
    state = read_state(run)
    project = Path(state["project"]).resolve()
    if not project.is_dir() or run == project or not run.is_relative_to(project):
        raise SystemExit("run must be a subdirectory of its initialized, existing project")
    for name in MANAGED_FILES:
        if not (run / name).is_file():
            raise SystemExit(f"incomplete initialized run: missing {name}")
    return state


def git(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    command = ["git", "--literal-pathspecs", "-c", "core.quotepath=false", "-C", str(project), *args]
    try:
        return subprocess.run(command, check=False, text=True, encoding="utf-8", errors="replace",
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        return subprocess.CompletedProcess(command, 127, "", "Git executable is unavailable")


def git_value(project: Path, *args: str) -> str | None:
    result = git(project, *args)
    return result.stdout.strip() if result.returncode == 0 else None


def observe_git(project: Path) -> dict[str, Any]:
    root = git_value(project, "rev-parse", "--show-toplevel")
    if root is None:
        return {"available": False, "reason": "Git unavailable or project is not a Git repository."}
    upstream = git_value(project, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    count = git_value(project, "rev-list", "--count", "@{u}..HEAD") if upstream else None
    status = git(project, "status", "--short", "--untracked-files=normal")
    return {
        "available": True,
        "observed_at": now_utc(),
        "repository": root,
        "branch": git_value(project, "symbolic-ref", "--quiet", "--short", "HEAD") or "detached HEAD",
        "head": git_value(project, "rev-parse", "--verify", "HEAD"),
        "upstream": upstream,
        "unpushed_count": int(count) if count is not None else None,
        "dirty": status.stdout.splitlines() if status.returncode == 0 else None,
        "status_error": status.stderr.strip() if status.returncode else "",
    }


def require_empty_index(project: Path) -> Path:
    root = git_value(project, "rev-parse", "--show-toplevel")
    if root is None:
        raise SystemExit(f"run-state commit requires a Git repository: {project}")
    staged = git(project, "diff", "--cached", "--name-only", "-z")
    if staged.returncode:
        raise SystemExit(staged.stderr.strip() or "failed to inspect staging")
    if staged.stdout:
        raise SystemExit("refusing run-state commit: staged changes already exist; preserve their ownership")
    return Path(root).resolve()


def commit_run_state(project: Path, run: Path, message: str) -> str | None:
    """Stage only regular managed files; never capture arbitrary run-directory content."""
    repo = require_empty_index(project)
    check_managed_paths(run)
    if run == project or not run.is_relative_to(project) or not run.is_relative_to(repo):
        raise SystemExit("run-state commit path is outside the project/repository")
    paths = [(run / name).relative_to(repo).as_posix() for name in MANAGED_FILES]
    add = git(repo, "add", "--", *paths)
    if add.returncode:
        raise SystemExit(add.stderr.strip() or "failed to stage recovery files")
    staged = git(repo, "diff", "--cached", "--name-only", "-z")
    if staged.returncode:
        raise SystemExit(staged.stderr.strip() or "failed to inspect staged recovery files")
    files = set(filter(None, staged.stdout.split("\0")))
    if not files:
        return None
    if not files.issubset(set(paths)):
        raise SystemExit("refusing commit: staging contains paths outside the four managed recovery files")
    result = git(repo, "commit", "-m", message)
    if result.returncode:
        raise SystemExit(result.stderr.strip() or "failed to commit recovery files; inspect Git staging")
    return git_value(repo, "rev-parse", "--short", "HEAD")


def merge_handoff(run: Path, state: dict[str, Any], generated: str) -> str:
    """Replace only our marked block; preserve a legacy handoff in full on first update."""
    path = run / "HANDOFF.md"
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    block = f"{START}\n{generated.rstrip()}\n{END}"
    if START in previous or END in previous:
        if previous.count(START) != 1 or previous.count(END) != 1 or previous.index(END) < previous.index(START):
            raise SystemExit("malformed generated handoff markers; repair them before updating")
        before, rest = previous.split(START)
        _, after = rest.split(END)
        content = before + block + after
    else:
        notes = ("## Preserved Legacy Handoff\n\n" + previous) if previous else (
            "## Maintainer Notes\n\nKeep manual continuation context outside the generated status block. "
            "Record the next action, unresolved question, and canonical file/section/symbol "
            "or scoped query; link to detailed history.\n"
        )
        content = f"# Handoff: {state['task']}\n\n{block}\n\n{notes}"
    if content.count(START) != 1 or content.count(END) != 1:
        raise SystemExit("handoff content contains reserved generated-status markers")
    return content


def render_handoff(state: dict[str, Any]) -> str:
    last = state.get("last_verified")
    latest = last.get("name", "unnamed") if last else "None recorded."
    history = "\n".join(
        f"- {item.get('status', 'unknown')}: {item.get('name', 'unnamed')} — {item.get('summary', '')} "
        f"Verification report: {item.get('verification', 'Not recorded.')} "
        f"Commit: {item.get('commit', 'not recorded')}"
        for item in state.get("milestones", [])[-10:]
    ) or "- None recorded."
    observed = state.get("git", {})
    if observed.get("available"):
        dirty = observed.get("dirty")
        dirty_text = "\n".join(dirty) if dirty else (observed.get("status_error") or "Clean.")
        git_text = (
            f"- Observed at: {observed['observed_at']} (before this recovery update/commit)\n"
            f"- Repository: {observed['repository']}\n"
            f"- Branch: {observed['branch']}\n- HEAD: {observed.get('head') or 'No commits yet.'}\n"
            f"- Upstream: {observed.get('upstream') or 'Not configured.'}\n"
            f"- Unpushed count: {observed['unpushed_count'] if observed.get('unpushed_count') is not None else 'Unknown (no upstream or comparison unavailable).'}\n"
            f"- Worktree at observation:\n\n```text\n{dirty_text}\n```"
        )
    else:
        git_text = observed.get("reason", "Not observed.")
    workflow = state.get("workflow", {})
    return f"""Updated: {state['updated_at']}
Project: `{state['project']}`
Run status: {state['status']}

## Current Progress

{state.get('summary', 'Recovery state initialized; fill PLAN.md before implementation.')}

- Current milestone: {state.get('current_milestone') or 'Not recorded.'}
- Current slice status: {state.get('current_milestone_status', 'Not recorded.')}
- Latest verified slice: {latest}
- Latest verified commit: {last.get('commit', 'Not recorded.') if last else 'Not recorded.'}

## Verification Report

{state.get('verification', 'Not run yet.')}

This is caller-reported evidence; the helper does not execute or certify tests.

## Next Safest Step

{state.get('next') or 'Not recorded.'}

## Milestone History (Latest 10)

{history}

## Git Observation

{git_text}

## Reported Workflow Context

- Base branch: {workflow.get('base_branch') or 'Not specified.'}
- Current slice implementation commit: {workflow.get('commit') or 'Not recorded.'}
- Merge result: {workflow.get('merge_result') or 'Not specified / not needed.'}

## Risks Or Blockers

{state.get('risk') or 'None recorded.'}

## Fact Placement And Recovery

Start with this handoff and current Git status/relevant diffs. Reuse applicable
instructions already in context; discover any missing ones for the target path.
Open PLAN.md only for missing scope/acceptance, query LOG.md for a chronology gap,
or inspect relevant STATE.json fields for structured details absent here. Follow
next-action source pointers/queries instead of loading every run file or old log.
Promote stable facts to their README/AGENTS/docs owner, decisions to DECISIONS/ADRs,
and process history to project logs. Keep manual retrieval pointers below.
"""


def save_run(run: Path, state: dict[str, Any], log_entry: str) -> None:
    # Validate preservation before changing any file, so damaged markers fail safely.
    handoff = merge_handoff(run, state, render_handoff(state))
    with (run / "LOG.md").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(log_entry)
    write_text(run / "STATE.json", json.dumps(state, indent=2, sort_keys=True) + "\n")
    write_text(run / "HANDOFF.md", handoff)


def init_run(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    if not project.is_dir():
        raise SystemExit(f"project must be an existing directory: {project}")
    base_arg = Path(args.base)
    base = (project / base_arg).resolve()
    if base_arg.is_absolute() or not base.is_relative_to(project):
        raise SystemExit("run base must be relative and remain inside the project")
    if args.commit_run_state:
        require_empty_index(project)
    observed = observe_git(project)
    name = f"{dt.date.today().isoformat()}-{slugify(args.task)}"
    run = base / name
    for suffix in range(1, 1000):
        run = base / (name if suffix == 1 else f"{name}-{suffix}")
        if not run.exists():
            break
    else:
        raise SystemExit("could not allocate a unique run directory")
    run.mkdir(parents=True)
    stamp = now_utc()
    state = {
        "schema_version": 2, "task": args.task, "project": str(project), "mode": args.mode,
        "created_at": stamp, "updated_at": stamp, "status": "active",
        "summary": "Recovery state initialized; complete the plan before implementation.",
        "next": "Fill PLAN.md with scope, slices, and verification.", "verification": "Not run yet.",
        "current_milestone": "", "milestones": [], "last_verified": None, "git": observed,
        "workflow": {"base_branch": args.base_branch} if args.base_branch else {},
    }
    write_text(run / "PLAN.md", f"""# Work Plan: {args.task}

Project: `{project}`
Created: {stamp}
Mode: {args.mode}

## Goal And Scope

- User outcome / acceptance criteria:
- Constraints / non-goals:
- Applicable instructions / confirmed evidence already available:
- Task size and risk (start Medium if uncertain):

## Next Context Queries

| Question blocking the next slice | Canonical path + section/symbol | Scope / query |
| --- | --- | --- |
| | | |

Retrieve only missing evidence. Keep stable facts at their canonical owner and
link to them; a plan does not require preloading README, architecture, or logs.

## Milestones And Verification

| Slice | Outcome / files | Verification | Commit decision | Rollback / next |
| --- | --- | --- | --- | --- |
| | | | | |

## Git Strategy

- Current task branch / ownership:
- Separate branch or worktree only if isolation is needed or requested:
- Existing user changes to preserve:

## Fact Placement

- Stable facts -> README / AGENTS / docs:
- Decision facts -> DECISIONS / ADRs:
- Process facts -> project logs:
- Agent execution state -> this directory:

## Risks And Rollback

- Risks:
- Rollback / next safest step:
""")
    save_run(run, state, f"# Work Log: {args.task}\n\n## {stamp}\n\n- Initialized recovery state.\n")
    if args.commit_run_state:
        commit = commit_run_state(project, run, f"chore(agent-state): initialize {slugify(args.task)}")
        if commit:
            print(f"committed agent execution state: {commit}")
    print(run)


def update_run(args: argparse.Namespace) -> None:
    run = Path(args.run).resolve()
    state = load_run(run)
    project = Path(state["project"]).resolve()
    if args.commit_run_state:
        require_empty_index(project)
    commit = None
    if args.commit is not None:
        commit = git_value(project, "rev-parse", "--verify", "--end-of-options", f"{args.commit}^{{commit}}")
        if not commit:
            raise SystemExit(f"implementation commit does not resolve in this repository: {args.commit}")
    is_milestone = args.command == "milestone"
    status = args.status
    if status in VERIFIED and not (args.verify and args.verify.strip()):
        raise SystemExit("verified/complete status requires an explicit non-empty verification report")
    name = args.name if is_milestone else (args.milestone or state.get("current_milestone", ""))
    stamp = now_utc()
    workflow = state.setdefault("workflow", {})
    if name != state.get("current_milestone"):
        workflow.pop("commit", None)
        workflow.pop("merge_result", None)
    if commit:
        workflow["commit"] = commit
    for field in ("base_branch", "merge_result"):
        value = getattr(args, field)
        if value is not None:
            workflow[field] = value
    state.update({"updated_at": stamp, "summary": args.summary, "current_milestone": name,
                  "current_milestone_status": status, "verification": args.verify or "Not reported for this checkpoint.",
                  "git": observe_git(project)})
    if not is_milestone:
        state["status"] = status
    if args.next is not None:
        state["next"] = args.next
    if args.risk is not None:
        state["risk"] = args.risk
    entry = {"name": name or "checkpoint", "status": status, "summary": args.summary,
             "verification": state["verification"], "next": state.get("next", ""), "recorded_at": stamp}
    if status in VERIFIED:
        entry["completed_at"] = stamp
    if workflow.get("commit"):
        entry["commit"] = workflow["commit"]
    if args.risk:
        entry["risk"] = args.risk
    if is_milestone:
        state["milestones"].append(entry)
    if is_milestone and status in VERIFIED:
        state["last_verified"] = entry.copy()
    log = (f"\n## {stamp}\n\n- {args.command}: {args.summary}\n- Slice: {name or 'not specified'}\n"
           f"- Slice status: {status}\n- Verification report: {state['verification']}\n"
           f"- Next: {state.get('next', '')}\n")
    if commit:
        log += f"- Recorded implementation commit: {commit}\n"
    if args.risk is not None:
        log += f"- Risk: {args.risk or 'cleared'}\n"
    save_run(run, state, log)
    if args.commit_run_state:
        saved = commit_run_state(project, run, f"chore(agent-state): {args.command} {slugify(state['task'])}")
        if saved:
            print(f"committed agent execution state: {saved}")
    print(run / "HANDOFF.md")


def show_status(args: argparse.Namespace) -> None:
    handoff = Path(args.run).resolve() / "HANDOFF.md"
    if not handoff.is_file():
        raise SystemExit(f"HANDOFF.md not found: {handoff}")
    print(handoff.read_text(encoding="utf-8"))


def find_runs(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    base = (project / args.base).resolve()
    if not base.is_relative_to(project):
        raise SystemExit("run base is outside the project")
    if not base.is_dir():
        return
    runs = sorted((p for p in base.iterdir() if p.is_dir() and (p / "STATE.json").is_file()),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    for run in runs[:args.limit]:
        state = read_state(run)
        print(f"{run}\t{state.get('status', 'unknown')}\t{state.get('task', run.name)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage project-local recovery state and reported milestones.")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="initialize the four recovery files")
    init.add_argument("--project", default=".")
    init.add_argument("--task", required=True)
    init.add_argument("--base", default="docs/agent-runs")
    init.add_argument("--mode", default="stewarded", choices=["stewarded", "fast", "recovery"])
    init.add_argument("--base-branch", help="optional workflow context")
    init.add_argument("--commit-run-state", action="store_true", help="commit only the four managed recovery files; never push")
    init.set_defaults(func=init_run)
    for command in ("checkpoint", "milestone"):
        ms = command == "milestone"
        update = sub.add_parser(command, help="record reported slice results" if ms else "save ongoing progress")
        update.add_argument("--run", required=True)
        update.add_argument("--summary", required=True)
        update.add_argument("--name" if ms else "--milestone", required=ms)
        update.add_argument("--verify", required=ms, help="caller-reported evidence; no tests are executed")
        update.add_argument("--next", required=ms)
        update.add_argument("--risk", help="risk/blocker; pass an empty string to clear")
        update.add_argument("--status", default="verified" if ms else "active", choices=STATUSES,
                            help="slice status" if ms else "run/checkpoint status; complete closes the run")
        update.add_argument("--commit", help="existing implementation commit for this slice")
        update.add_argument("--base-branch", help="optional base branch for an isolation workflow")
        update.add_argument("--merge-result", help="caller-reported merge outcome, if relevant")
        update.add_argument("--commit-run-state", action="store_true", help="commit only the four managed recovery files; never push")
        update.set_defaults(func=update_run)
    status = sub.add_parser("status", help="print the handoff")
    status.add_argument("--run", required=True)
    status.set_defaults(func=show_status)
    find = sub.add_parser("find", help="list initialized runs")
    find.add_argument("--project", default=".")
    find.add_argument("--base", default="docs/agent-runs")
    find.add_argument("--limit", type=int, default=10)
    find.set_defaults(func=find_runs)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
