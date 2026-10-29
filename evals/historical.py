#!/usr/bin/env python3
"""Controller-only pinned upstream bug tasks, hidden upstream tests and oracle checks.

Fetch dependencies/source explicitly. Never provide this controller or source cache
to an evaluated agent: public upstream history itself can leak the oracle.
"""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile

from benchmark import BRIEF_AGENTS, REPO, git, package_fingerprint, write_json
import uuid

MANIFEST = Path(__file__).with_name("historical-tasks.json")


def tasks():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["tasks"]


def archive(cache, commit, destination):
    data = subprocess.run(["git", "-C", str(cache), "archive", commit], check=True, capture_output=True).stdout
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        for member in tar.getmembers():
            target = destination / member.name
            if not target.resolve().is_relative_to(destination.resolve()) or member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                raise ValueError("unsafe upstream archive member")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(tar.extractfile(member).read())


def check_cache(cache, task):
    for ref in (task["base"], task["fixed"]):
        if git(cache, "rev-parse", "--verify", ref + "^{commit}") != ref:
            raise ValueError("pinned upstream object missing")
    if git(cache, "rev-parse", task["fixed"] + "^") != task["base"]:
        raise ValueError("task must bind a single-parent upstream fix")
    for path, expected in task["test_blobs"].items():
        if git(cache, "rev-parse", task["fixed"] + ":" + path) != expected:
            raise ValueError("upstream hidden test identity changed")


def prepare(task, cache, output, group, profile):
    check_cache(cache, task)
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    archive(cache, task["base"], workspace)
    # Remove bundled GitHub automation from trial workspace; no credentials or upstream history.
    shutil.rmtree(workspace / ".github", ignore_errors=True)
    if group == "B":
        (workspace / "AGENTS.md").write_text(BRIEF_AGENTS, encoding="utf-8")
    git(workspace, "init", "-b", "main")
    git(workspace, "config", "user.name", "Historical benchmark")
    git(workspace, "config", "user.email", "benchmark@example.invalid")
    git(workspace, "config", "commit.gpgsign", "false")
    git(workspace, "config", "core.hooksPath", str(output / "no-hooks"))
    git(workspace, "add", "--all")
    git(workspace, "commit", "-m", "historical task baseline")
    control = {"trial_id": str(uuid.uuid4()), "task": task["id"], "family": task["family"], "group": group,
               "profile": profile, "baseline": git(workspace, "rev-parse", "HEAD"),
               "upstream_base": task["base"], "upstream_fixed": task["fixed"],
               "skill_commit": git(REPO, "rev-parse", "HEAD") if group == "C" else None,
               "skill_fingerprint": package_fingerprint(REPO / "project-steward") if group == "C" else None}
    request = task["prompt"] + "\nPreserve existing behavior. Add a focused regression. No network or publication is authorized.\n"
    if group == "C":
        support = output / "skill-support" / "project-steward"
        shutil.copytree(REPO / "project-steward", support, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        request += "Use Project Steward from the separately supplied skill-support directory.\n"
    (output / "request.txt").write_text(request, encoding="utf-8")
    write_json(output / "controller.json", control)
    return workspace


def check(task, cache, workspace, python, hidden):
    """Grade a disposable candidate copy. Hidden tests never enter the live workspace."""
    with tempfile.TemporaryDirectory(prefix="steward-hidden-") as temp:
        candidate = Path(temp) / "candidate"
        shutil.copytree(workspace, candidate, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", ".hypothesis", ".venv"))
        # Agent modifications to public tests/config cannot weaken the controller's checks.
        trusted = Path(temp) / "trusted"
        archive(cache, task["base"], trusted)
        shutil.rmtree(candidate / "tests", ignore_errors=True)
        shutil.copytree(trusted / "tests", candidate / "tests")
        config = Path(temp) / "pytest.ini"
        config.write_text("[pytest]\n", encoding="utf-8")
        if hidden:
            for name in task["test_blobs"]:
                content = subprocess.run(["git", "-C", str(cache), "show", task["fixed"] + ":" + name], check=True, capture_output=True).stdout
                (candidate / name).parent.mkdir(parents=True, exist_ok=True)
                (candidate / name).write_bytes(content)
        env = os.environ.copy()
        env.update(PYTHONPATH=str(candidate / "src"), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
        command = [str(python), "-B", "-m", "pytest", "-c", str(config), "-q", *(task["test_paths"] if hidden else task["regression_paths"])]
        try:
            result = subprocess.run(command, cwd=candidate, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            return {"passed": result.returncode == 0, "exit_code": result.returncode,
                    "diagnostic": (result.stdout + result.stderr)[-6000:].replace(str(candidate), "<candidate>")}
        except subprocess.TimeoutExpired:
            return {"passed": False, "exit_code": None, "diagnostic": "180 second grading timeout"}


def oracle(task, cache, python):
    check_cache(cache, task)
    with tempfile.TemporaryDirectory(prefix="steward-oracle-") as temp:
        base, fixed = Path(temp) / "base", Path(temp) / "fixed"
        archive(cache, task["base"], base)
        archive(cache, task["fixed"], fixed)
        before = check(task, cache, base, python, True)
        after = check(task, cache, fixed, python, True)
        regression = check(task, cache, fixed, python, False)
    return {"task": task["id"], "measurement": "historical_oracle_self_test", "base": task["base"], "fixed": task["fixed"],
            "valid": before["exit_code"] == 1 and after["passed"] and regression["passed"],
            "baseline": before, "oracle": after, "regression": regression}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["list", "prepare", "grade", "oracle"])
    parser.add_argument("--task")
    parser.add_argument("--cache", type=Path, help="controller-only clone of pinned upstream")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--trial", type=Path)
    parser.add_argument("--group", choices=list("ABC"))
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--metrics", type=Path)
    args = parser.parse_args()
    selected = [t for t in tasks() if args.task is None or t["id"] == args.task]
    if not selected:
        raise ValueError("unknown historical task")
    if args.action == "list":
        for task in selected:
            print(task["id"], task["title"])
        return
    if not args.cache or not args.out or args.out.exists():
        raise ValueError("supply cache and a new output path")
    if args.action == "oracle":
        results = []
        for task in selected:
            result = oracle(task, args.cache.resolve(), args.python.resolve())
            results.append(result)
            print(task["id"], "valid" if result["valid"] else "INVALID", flush=True)
        write_json(args.out, {"measurement": "historical_oracle_self_test", "results": results})
        if not all(r["valid"] for r in results):
            raise SystemExit(1)
    elif args.action == "prepare":
        if len(selected) != 1 or not args.group or not args.profile:
            raise ValueError("prepare needs one task, condition and fixed profile")
        from benchmark import read_profile
        prepare(selected[0], args.cache.resolve(), args.out.resolve(), args.group, read_profile(args.profile))
    else:
        control = json.loads((args.trial / "controller.json").read_text(encoding="utf-8"))
        task = next(t for t in tasks() if t["id"] == control["task"])
        check_cache(args.cache, task)
        if (control["upstream_base"], control["upstream_fixed"]) != (task["base"], task["fixed"]):
            raise ValueError("controller/manifest mismatch")
        behavior = check(task, args.cache, args.trial / "workspace", args.python.resolve(), True)
        regression = check(task, args.cache, args.trial / "workspace", args.python.resolve(), False)
        violations = []
        try:
            git(args.trial / "workspace", "merge-base", "--is-ancestor", control["baseline"], "HEAD")
        except subprocess.CalledProcessError:
            violations.append("baseline history missing")
        result = {**control, "measurement": "agent_trial", "behavior_passed": behavior["passed"],
                             "regression_passed": regression["passed"], "ownership_passed": not violations,
                             "success": behavior["passed"] and regression["passed"] and not violations,
                             "checks": {"behavior": behavior, "regression": regression}, "ownership_violations": violations,
                             "tokens": None, "elapsed_seconds": None}
        if args.metrics:
            from benchmark import attach_metrics
            attach_metrics(result, json.loads(args.metrics.read_text(encoding="utf-8")))
        write_json(args.out, result)


if __name__ == "__main__":
    main()
