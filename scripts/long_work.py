#!/usr/bin/env python3
"""Create and update durable run state for long Codex work."""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
from pathlib import Path
from typing import Any


def now_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def today() -> str:
    return _dt.date.today().isoformat()


def slugify(text: str, limit: int = 48) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    return (slug[:limit].strip("-") or "task")


def unique_dir(base: Path, name: str) -> Path:
    candidate = base / name
    if not candidate.exists():
        return candidate
    for i in range(2, 1000):
        candidate = base / f"{name}-{i}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"could not allocate unique directory under {base}")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def read_state(run: Path) -> dict[str, Any]:
    state_path = run / "STATE.json"
    if not state_path.exists():
        return {}
    return json.loads(state_path.read_text(encoding="utf-8"))


def write_state(run: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now_utc()
    write_text(run / "STATE.json", json.dumps(state, indent=2, sort_keys=True) + "\n")


def git(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(project), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def require_git_root(project: Path) -> Path:
    result = git(project, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        raise SystemExit(f"not a Git repository: {project}")
    return Path(result.stdout.strip()).resolve()


def relative_to(path: Path, parent: Path) -> Path:
    try:
        return path.resolve().relative_to(parent.resolve())
    except ValueError:
        raise SystemExit(f"path is outside repository root: {path}") from None


def commit_run_state(project: Path, run: Path, message: str) -> str | None:
    repo = require_git_root(project)
    run_rel = relative_to(run, repo)

    staged = git(repo, "diff", "--cached", "--name-only")
    if staged.returncode != 0:
        raise SystemExit(staged.stderr.strip() or "failed to inspect staged changes")
    staged_files = [line for line in staged.stdout.splitlines() if line.strip()]
    if staged_files:
        raise SystemExit(
            "refusing to commit run state because staged changes already exist:\n"
            + "\n".join(staged_files)
        )

    add = git(repo, "add", "--", run_rel.as_posix())
    if add.returncode != 0:
        raise SystemExit(add.stderr.strip() or "failed to stage run state")

    staged_after = git(repo, "diff", "--cached", "--name-only")
    if staged_after.returncode != 0:
        raise SystemExit(staged_after.stderr.strip() or "failed to inspect staged run state")
    files = [line for line in staged_after.stdout.splitlines() if line.strip()]
    if not files:
        return None

    prefix = str(run_rel).replace("\\", "/").rstrip("/") + "/"
    unsafe = [path for path in files if not path.replace("\\", "/").startswith(prefix)]
    if unsafe:
        raise SystemExit(
            "refusing to commit because staged paths escaped the run directory:\n"
            + "\n".join(unsafe)
        )

    commit = git(
        repo,
        "commit",
        "-m",
        message,
        "-m",
        "Agent-owned Project Steward run-state checkpoint. No business-code paths should be included.",
    )
    if commit.returncode != 0:
        raise SystemExit(commit.stderr.strip() or "failed to commit run state")

    head = git(repo, "rev-parse", "--short", "HEAD")
    if head.returncode != 0:
        raise SystemExit(head.stderr.strip() or "failed to read new commit")
    return head.stdout.strip()


def init_run(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    base = project / args.base
    run_name = f"{today()}-{slugify(args.task)}"
    run = unique_dir(base, run_name)
    run.mkdir(parents=True, exist_ok=False)

    created_at = now_utc()
    state = {
        "task": args.task,
        "project": str(project),
        "mode": args.mode,
        "created_at": created_at,
        "updated_at": created_at,
        "status": "active",
        "next": "Fill PLAN.md with slices and start the first verified slice.",
        "verification": "Not run yet.",
    }

    write_text(
        run / "PLAN.md",
        f"""# Long Work Plan: {args.task}

Created: {created_at}
Project: `{project}`
Mode: {args.mode}

## Goal

- User outcome:
- Acceptance criteria:
- Non-goals:

## Context Read

- Project instructions:
- Existing patterns:
- Similar modules/tests:

## Slices

1. Slice:
   - Files/modules:
   - Verification:
   - Stop condition:

## Verification Plan

- Targeted:
- Broader:
- Manual:

## Risks And Rollback

- Risks:
- Rollback/safest undo:
""",
    )

    write_text(
        run / "LOG.md",
        f"""# Long Work Log: {args.task}

## {created_at}

- Initialized run state.
- Project: `{project}`
- Next: Fill PLAN.md and start the first verified slice.
""",
    )

    write_text(
        run / "HANDOFF.md",
        f"""# Handoff: {args.task}

Updated: {created_at}
Status: active
Project: `{project}`

## Current Objective

{args.task}

## Completed

- Run state initialized.

## Current State

- PLAN.md needs slice details.
- No verification has run yet.

## Next Safest Step

Fill PLAN.md with context, slices, and verification, then execute the first small slice.

## Important Files

- `PLAN.md`
- `LOG.md`
- `STATE.json`

## Git State

- Branch:
- Base commit:
- Current HEAD:
- Dirty/untracked files:
- Unpushed commits:

## Verification

Not run yet.

## Risks Or Blockers

- None recorded.
""",
    )

    write_state(run, state)
    if args.commit_run_state:
        commit = commit_run_state(project, run, f"chore(agent-run): initialize {slugify(args.task)}")
        if commit:
            print(f"committed run state: {commit}")
    print(run)


def checkpoint(args: argparse.Namespace) -> None:
    run = Path(args.run).resolve()
    if not run.exists():
        raise SystemExit(f"run directory does not exist: {run}")

    stamp = now_utc()
    state = read_state(run)
    state.setdefault("task", run.name)
    state["status"] = args.status
    if args.next:
        state["next"] = args.next
    if args.verify:
        state["verification"] = args.verify
    if args.risk:
        state["risk"] = args.risk

    log_bits = [f"## {stamp}", "", f"- Summary: {args.summary}"]
    if args.next:
        log_bits.append(f"- Next: {args.next}")
    if args.verify:
        log_bits.append(f"- Verification: {args.verify}")
    if args.risk:
        log_bits.append(f"- Risk/blocker: {args.risk}")
    log_bits.append("")

    with (run / "LOG.md").open("a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(log_bits))

    handoff = f"""# Handoff: {state.get("task", run.name)}

Updated: {stamp}
Status: {args.status}

## Current Objective

{state.get("task", run.name)}

## Latest Checkpoint

{args.summary}

## Next Safest Step

{args.next or state.get("next", "Not recorded.")}

## Verification

{args.verify or state.get("verification", "Not recorded.")}

## Git State

- Branch:
- Base commit:
- Current HEAD:
- Dirty/untracked files:
- Unpushed commits:

## Risks Or Blockers

{args.risk or state.get("risk", "None recorded.")}

## Recovery Notes

- Read PLAN.md for intended slices.
- Read recent LOG.md entries for chronology.
- Check git status and relevant diffs before editing.
"""
    write_text(run / "HANDOFF.md", handoff)
    write_state(run, state)
    if args.commit_run_state:
        task = str(state.get("task", run.name))
        commit = commit_run_state(run, run, f"chore(agent-run): checkpoint {slugify(task)}")
        if commit:
            print(f"committed run state: {commit}")
    print(run / "HANDOFF.md")


def show_status(args: argparse.Namespace) -> None:
    run = Path(args.run).resolve()
    handoff = run / "HANDOFF.md"
    if not handoff.exists():
        raise SystemExit(f"HANDOFF.md not found in {run}")
    print(handoff.read_text(encoding="utf-8"))


def find_runs(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    base = project / args.base
    if not base.exists():
        return
    runs = sorted((p for p in base.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True)
    for run in runs[: args.limit]:
        state = read_state(run)
        status = state.get("status", "unknown")
        task = state.get("task", run.name)
        print(f"{run}\t{status}\t{task}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage long-work run state.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create PLAN.md, LOG.md, HANDOFF.md, and STATE.json")
    init.add_argument("--project", default=".", help="project root")
    init.add_argument("--task", required=True, help="short task title")
    init.add_argument("--base", default="docs/agent-runs", help="run directory relative to project")
    init.add_argument("--mode", default="stewarded", choices=["stewarded", "fast", "recovery"])
    init.add_argument(
        "--commit-run-state",
        action="store_true",
        help="commit only the created run directory; refuses existing staged changes and never pushes",
    )
    init.set_defaults(func=init_run)

    cp = sub.add_parser("checkpoint", help="append a log entry and refresh HANDOFF.md")
    cp.add_argument("--run", required=True, help="run directory")
    cp.add_argument("--summary", required=True, help="what changed or was learned")
    cp.add_argument("--next", default="", help="next safest action")
    cp.add_argument("--verify", default="", help="verification result or pending check")
    cp.add_argument("--risk", default="", help="risk, blocker, or residual uncertainty")
    cp.add_argument("--status", default="active", choices=["active", "paused", "blocked", "verified", "complete"])
    cp.add_argument(
        "--commit-run-state",
        action="store_true",
        help="commit only this run directory; refuses existing staged changes and never pushes",
    )
    cp.set_defaults(func=checkpoint)

    status = sub.add_parser("status", help="print HANDOFF.md")
    status.add_argument("--run", required=True, help="run directory")
    status.set_defaults(func=show_status)

    find = sub.add_parser("find", help="list recent run directories")
    find.add_argument("--project", default=".", help="project root")
    find.add_argument("--base", default="docs/agent-runs", help="run directory relative to project")
    find.add_argument("--limit", type=int, default=10)
    find.set_defaults(func=find_runs)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
