#!/usr/bin/env python3
"""Explicit, optional verification adapter. Never executes recovery-file commands."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.request

sys.dont_write_bytecode = True

from long_work import append_event, load_run, select_milestone
from steward_core.git_ops import git_value, observe_git
from steward_core.state import next_id, now_utc, require
from steward_core.storage import run_lock, save_run


def scrub(text, project):
    """Best effort minimization; do not put secrets in argv or test output."""
    for value in sorted({str(project), str(Path.home()), str(Path(sys.prefix))}, key=len, reverse=True):
        if len(value) > 3:
            text = text.replace(value, "<local>").replace(value.replace("\\", "/"), "<local>")
    for key, value in os.environ.items():
        if re.search(r"TOKEN|SECRET|PASSWORD|API_KEY", key, re.I) and len(value) >= 4:
            text = text.replace(value, "<redacted>")
    text = re.sub(r"(?i)(bearer\s+|(?:password|token|api[_-]?key)[=: ]+)[^\s,;]+", r"\1<redacted>", text)
    return text


def snapshot(project, run):
    """Bind evidence to HEAD plus nonignored file bytes, excluding this run."""
    head = git_value(project, "rev-parse", "HEAD")
    require(bool(head), "observed checks require an existing Git commit")
    result = subprocess.run(["git", "-C", str(project), "ls-files", "-c", "-o", "--exclude-standard", "-z"],
                            capture_output=True, check=True)
    digest = hashlib.sha256()
    for name in sorted(set(os.fsdecode(result.stdout).split("\0")) - {""}):
        path = project / name
        if path.resolve().is_relative_to(run):
            continue
        digest.update(name.encode("utf-8", "surrogateescape") + b"\0")
        entry = hashlib.sha256()
        if path.is_symlink():
            entry.update(b"link:" + os.fsencode(os.readlink(path)))
        elif path.is_file():
            entry.update(str(path.stat().st_mode & 0o111).encode() + b"\0")
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(65536), b""):
                    entry.update(chunk)
        else:
            entry.update(b"<missing>")
        digest.update(entry.digest())
    return {"head": head, "files_sha256": digest.hexdigest(), "scope": "Git tracked and nonignored untracked files; run excluded"}


def execute(argv, project, timeout, limit=65536, *, merge_stderr=True):
    require(bool(argv), "supply an explicit argv after --")
    require(timeout > 0 and timeout <= 86400 and 0 < limit <= 1048576, "invalid timeout/output limit")
    started = time.monotonic()
    process = subprocess.Popen(argv, cwd=project, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT if merge_stderr else subprocess.PIPE,
                               shell=False, start_new_session=os.name != "nt",
                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
    buffers = [bytearray(), bytearray()]
    sizes = [0, 0]
    hashes = [hashlib.sha256(), hashlib.sha256()]

    def drain(stream, index):
        while True:
            chunk = stream.read(8192)
            if not chunk:
                break
            sizes[index] += len(chunk)
            hashes[index].update(chunk)
            buffers[index].extend(chunk[:max(0, limit - len(buffers[index]))])

    streams = [process.stdout] + ([process.stderr] if not merge_stderr else [])
    readers = [threading.Thread(target=drain, args=(stream, i), daemon=True) for i, stream in enumerate(streams)]
    for reader in readers:
        reader.start()
    timed_out = False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.kill()
        process.wait()
    for reader in readers:
        reader.join(timeout=2)
    require(not any(reader.is_alive() for reader in readers), "descendant retained output pipe; output incomplete, no evidence recorded")
    for stream in streams:
        stream.close()
    return {"status": "failed" if timed_out or process.returncode else "passed", "exit_code": process.returncode,
            "duration_seconds": round(time.monotonic() - started, 6), "timed_out": timed_out,
            "output": scrub(buffers[0].decode("utf-8", "replace"), project), "output_bytes": sizes[0],
            "output_truncated": sizes[0] > limit, "output_sha256": hashes[0].hexdigest(),
            **({"stderr": scrub(buffers[1].decode("utf-8", "replace"), project), "stderr_bytes": sizes[1],
                "stderr_truncated": sizes[1] > limit} if not merge_stderr else {})}


def github_get(endpoint, transport="https"):
    if transport == "gh":
        # Optional authenticated CLI transport; the endpoint/hostname stay fixed.
        result = subprocess.run(["gh", "api", "--hostname", "github.com", "repos/" + endpoint],
                                capture_output=True, timeout=30, check=True)
        require(len(result.stdout) <= 4_000_000, "GitHub response exceeds limit")
        return json.loads(result.stdout)
    # Fixed origin; disable redirects so credentials cannot cross origins.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "project-steward", "X-GitHub-Api-Version": "2022-11-28"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    request = urllib.request.Request("https://api.github.com/repos/" + endpoint, headers=headers)
    with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
        raw = response.read(4_000_001)
    require(len(raw) <= 4_000_000, "GitHub response exceeds limit")
    return json.loads(raw)


def github_evidence(repository, run_id, workflow, sha, fetch=github_get):
    require(bool(re.fullmatch(r"[\w.-]+/[\w.-]+", repository)), "expected GitHub owner/repository")
    require(all(part not in {".", ".."} for part in repository.split("/")), "invalid GitHub repository")
    require(type(run_id) is int and run_id > 0, "invalid Actions run ID")
    require(bool(re.fullmatch(r"[0-9a-f]{40}", sha)), "expected full GitHub commit SHA")
    require(workflow.startswith(".github/workflows/") and ".." not in workflow, "explicit workflow path required")
    run = fetch(f"{repository}/actions/runs/{run_id}")
    require(run["repository"]["full_name"].lower() == repository.lower()
            and run["head_sha"] == sha and run["path"] == workflow and run["id"] == run_id,
            "CI repository/SHA/workflow/run mismatch")
    require(run["status"] == "completed" and run["conclusion"] in {"success", "failure", "cancelled", "timed_out"},
            "CI must be completed with a decisive outcome")
    attempt = run["run_attempt"]
    jobs = []
    for page in range(1, 102):
        payload = fetch(f"{repository}/actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100&page={page}")
        jobs.extend(payload["jobs"])
        if len(jobs) >= payload["total_count"]:
            break
    require(jobs and len(jobs) == payload["total_count"] and all(j["status"] == "completed" for j in jobs),
            "CI job list incomplete")
    # Re-fetch after pagination: a concurrent rerun must not mix attempts.
    latest = fetch(f"{repository}/actions/runs/{run_id}")
    require(latest["run_attempt"] == attempt and latest["updated_at"] == run["updated_at"], "CI changed while importing; retry")
    passed = run["conclusion"] == "success" and all(j["conclusion"] == "success" for j in jobs)
    return {"status": "passed" if passed else "failed", "exit_code": None, "revision": sha,
            "source": "independently_confirmed", "claimed_source": "independently_confirmed",
            "provenance": {"adapter": "github-actions-api-v1", "repository": repository, "run_id": run_id,
                           "workflow": workflow, "attempt": attempt, "conclusion": run["conclusion"], "url": run["html_url"],
                           "observed_at": now_utc(), "jobs": [{"id": j["id"], "name": j["name"],
                           "conclusion": j["conclusion"]} for j in jobs]}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--id", required=True, help="milestone ID")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--scope", required=True, help="what risk/contract this check covers")
    sub = parser.add_subparsers(dest="action", required=True)
    local = sub.add_parser("exec", help="execute an explicitly supplied, already authorized argv")
    local.add_argument("--timeout", type=float, default=300)
    local.add_argument("--output-limit", type=int, default=65536)
    local.add_argument("argv", nargs=argparse.REMAINDER)
    ci = sub.add_parser("github", help="fetch a completed workflow from GitHub API, never a local report")
    ci.add_argument("--repository", required=True)
    ci.add_argument("--run-id", type=int, required=True)
    ci.add_argument("--workflow", required=True)
    ci.add_argument("--sha", required=True)
    ci.add_argument("--transport", choices=["https", "gh"], default="https")
    args = parser.parse_args()
    run = args.run.resolve()
    # Preflight before execution/network; don't hold a state lock during long checks.
    state, project = load_run(run)
    require(state["status"] not in {"complete", "cancelled"}, "run is closed")
    require(select_milestone(state, args.id) is not None and args.summary.strip() and args.scope.strip(), "milestone/summary/scope required")
    revision = state["revision"]
    if args.action == "exec":
        argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
        before = snapshot(project, run)
        record = execute(argv, project, args.timeout, args.output_limit)
        after = snapshot(project, run)
        record.update(source="observed", claimed_source="observed", revision=before["head"],
                      command=scrub(json.dumps(argv), project), environment=f"{sys.platform}; python {sys.version.split()[0]}",
                      provenance={"adapter": "explicit-argv-v1", "before": before, "after": after,
                                  "source_changed": before != after, "observed_at": now_utc()})
    else:
        require(git_value(project, "rev-parse", "--verify", args.sha + "^{commit}") == args.sha,
                "CI SHA must exist as a local project commit; fetch it explicitly first")
        remote = git_value(project, "remote", "get-url", "origin") or ""
        require(remote.rstrip("/").removesuffix(".git").lower() in {
            "https://github.com/" + args.repository.lower(), "git@github.com:" + args.repository.lower()},
            "explicit GitHub repository must match local origin")
        record = github_evidence(args.repository, args.run_id, args.workflow, args.sha,
                                 lambda endpoint: github_get(endpoint, args.transport))
        record["provenance"]["transport"] = args.transport
        record.update(command=None, environment="GitHub Actions")
    with run_lock(run):
        state, project = load_run(run)
        require(state["revision"] == revision, "run changed while collecting; no evidence appended; rerun/reconcile explicitly")
        record.update(id=next_id(state["evidence"], "V"), milestone_id=args.id,
                      summary=scrub(args.summary, project), scope=scrub(args.scope, project), recorded_at=now_utc())
        state["evidence"].append(record)
        state["git"] = observe_git(project)
        append_event(state, f"- Collected {record['id']}: {record['source']}; {record['status']}; {record['summary']}", args.id)
        save_run(run, state, revision)
    print(json.dumps({k: record[k] for k in ("id", "source", "status", "revision")}, sort_keys=True))
    return 1 if record["status"] == "failed" else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        raise SystemExit(f"verification collection refused: {type(exc).__name__}; inspect inputs/environment") from None
