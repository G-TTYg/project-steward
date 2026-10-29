"""Observe portable Git facts and commit only owned recovery files.

Recovery commits use an isolated index, an index lock, pre-commit validation, and
compare-and-swap ref publication. No reset/stash or shared-history rollback occurs.
This plumbing path is opt-in and does not implement the full porcelain hook cycle.
"""

import os
from pathlib import Path
import subprocess
import tempfile

from .state import now_utc, require
from .storage import MANAGED_FILES, check_managed_paths


def git(project: Path, *args: str, env: dict | None = None, input: str | None = None):
    command = ["git", "--literal-pathspecs", "-c", "core.quotepath=false", "-C", str(project), *args]
    try:
        return subprocess.run(command, check=False, text=True, encoding="utf-8", errors="replace",
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, input=input)
    except FileNotFoundError:
        return subprocess.CompletedProcess(command, 127, "", "Git executable is unavailable")


def git_value(project: Path, *args: str) -> str | None:
    result = git(project, *args)
    return result.stdout.strip() if result.returncode == 0 else None


def repository_root(project: Path) -> Path | None:
    root = git_value(project, "rev-parse", "--show-toplevel")
    return Path(root).resolve() if root else None


def observe_git(project: Path) -> dict:
    root = repository_root(project)
    if root is None:
        return {"available": False, "reason": "Git unavailable or project is not a Git repository."}
    upstream = git_value(project, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    count = git_value(project, "rev-list", "--count", "@{u}..HEAD") if upstream else None
    status = git(project, "status", "--short", "--untracked-files=normal")
    # Suppress stderr here: tools/hooks may embed absolute machine paths in errors.
    return {"available": True, "observed_at": now_utc(), "repository_subpath": project.relative_to(root).as_posix(),
            "branch": git_value(project, "symbolic-ref", "--quiet", "--short", "HEAD") or "detached HEAD",
            "head": git_value(project, "rev-parse", "--verify", "HEAD"), "upstream": upstream,
            "unpushed_count": int(count) if count is not None else None,
            "dirty": status.stdout.splitlines() if status.returncode == 0 else None,
            "status_error": "Git status failed; inspect locally." if status.returncode else ""}


def check_repository_binding(project: Path, state: dict) -> list[str]:
    expected = state["project"].get("repository_subpath")
    root = repository_root(project)
    if expected is not None and root is None:
        return ["Git association unavailable; restore repository metadata/Git before mutation"]
    if root is not None and expected is not None and project.relative_to(root).as_posix() != expected:
        return ["project subpath differs from its recorded Git association"]
    return []


def require_empty_index(project: Path) -> Path:
    root = repository_root(project)
    require(root is not None, "run-state commit requires a Git repository")
    staged = git(project, "diff", "--cached", "--name-only", "-z")
    require(staged.returncode == 0, staged.stderr.strip() or "failed to inspect staging")
    require(not staged.stdout, "refusing run-state commit: staged changes already exist; preserve their ownership")
    return root


def commit_run_state(project: Path, run: Path, message: str) -> str | None:
    repo = require_empty_index(project)
    check_managed_paths(run)
    require(run != project and run.is_relative_to(project) and run.is_relative_to(repo),
            "run-state commit path is outside the project/repository")
    paths = [(run / name).relative_to(repo).as_posix() for name in MANAGED_FILES]
    prepared_files = {name: (run / name).read_bytes() for name in MANAGED_FILES}
    index_name = git_value(repo, "rev-parse", "--git-path", "index")
    require(bool(index_name), "cannot locate Git index")
    index = Path(index_name)
    if not index.is_absolute():
        index = repo / index
    index = index.resolve()
    lock = index.with_name(index.name + ".lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise SystemExit("Git index is locked; preserve the lock and inspect the other writer") from None
    published = None
    try:
        with os.fdopen(fd, "wb") as locked_index, tempfile.TemporaryDirectory(prefix="steward-index-") as temp:
            require_empty_index(repo)
            old_index = index.read_bytes() if index.exists() else None
            head = git_value(repo, "rev-parse", "--verify", "HEAD")
            ref = git_value(repo, "symbolic-ref", "--quiet", "HEAD") or "HEAD"
            env = os.environ.copy()
            env["GIT_INDEX_FILE"] = str(Path(temp) / "index")

            def checked(*args, input=None):
                result = git(repo, *args, env=env, input=input)
                require(result.returncode == 0, result.stderr.strip() or f"Git {args[0]} failed")
                return result.stdout.strip()

            checked("read-tree", head if head else "--empty")
            checked("add", "--", *paths)
            tree = checked("write-tree")
            if head and tree == git_value(repo, "rev-parse", "HEAD^{tree}"):
                return None
            # Run the project's pre-commit hook against the private index. A hook
            # may validate, but any change to staged content invalidates preparation.
            checked("hook", "run", "--ignore-missing", "pre-commit")
            require(checked("write-tree") == tree, "pre-commit hook changed staged content; inspect files and retry explicitly")
            check_managed_paths(run)
            require(all((run / name).read_bytes() == content for name, content in prepared_files.items()),
                    "pre-commit hook changed managed worktree content; preserve it and reobserve")
            require(git_value(repo, "rev-parse", "--verify", "HEAD") == head
                    and (git_value(repo, "symbolic-ref", "--quiet", "HEAD") or "HEAD") == ref,
                    "HEAD changed during recovery commit; preserve work and reobserve")
            require((index.read_bytes() if index.exists() else None) == old_index,
                    "shared Git index changed concurrently; preserve it and reobserve")
            parent = ("-p", head) if head else ()
            commit = checked("commit-tree", tree, *parent, input=message + "\n")
            changed = checked("diff-tree", "--root", "--no-commit-id", "--name-only", "--no-renames", "-r", "-z", commit)
            require(set(filter(None, changed.split("\0"))).issubset(paths),
                    "prepared commit contains paths outside the four managed recovery files")
            locked_index.write(Path(env["GIT_INDEX_FILE"]).read_bytes())
            locked_index.flush()
            os.fsync(locked_index.fileno())
            # Publish only if the original ref still has the observed full SHA.
            checked("update-ref", "-m", message, ref, commit, head or "0" * len(commit))
            published = commit
        os.replace(lock, index)
        return published
    except (OSError, SystemExit) as exc:
        staged = git(repo, "diff", "--cached", "--name-only").stdout.strip() or "(none)"
        current = git_value(repo, "rev-parse", "--verify", "HEAD") or "unborn"
        raise SystemExit(f"recovery commit failed: {exc}\nHEAD: {current}\nStaged paths: {staged}\n"
                         f"Published recovery commit: {published or 'none'}\n"
                         "No reset performed. Inspect status/diffs and preserve other work before retrying.") from None
    finally:
        # If ref publication succeeded but index activation failed, preserve the
        # prepared index for manual recovery rather than silently deleting it.
        if published is None:
            lock.unlink(missing_ok=True)
