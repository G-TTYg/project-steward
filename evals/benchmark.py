#!/usr/bin/env python3
"""Prepare isolated Agent trials, grade hidden outcomes, and report A/B/C results.

No model/agent is launched here. The controller must supply a fixed host/profile
and keep corpus/grader/control files outside the evaluated agent's accessible context.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
import uuid

from corpus import TASKS

REPO = Path(__file__).resolve().parents[1]
BRIEF_AGENTS = """# Engineering constraints

Confirm task scope and inspect current Git state before editing.
Preserve existing user and agent changes and their staging/commit ownership.
Use meaningful tests for the changed behavior; report actual results and limits.
Do not publish, deploy, discard work, or expand scope without authorization.
"""


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git(workspace, *args):
    env = os.environ.copy()
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return subprocess.run(["git", "-C", str(workspace), *args], check=True, env=env,
                          capture_output=True, text=True, encoding="utf-8").stdout.strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_fingerprint(package):
    result = hashlib.sha256()
    for path in sorted(package.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            result.update(path.relative_to(package).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return result.hexdigest()


def prepare(task_id, group, output, profile):
    task = TASKS[task_id]
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    workspace.mkdir()
    for name, content in task.files.items():
        (workspace / name).write_text(content, encoding="utf-8")
    # A public sanity check deliberately does not expose hidden edge cases.
    (workspace / "test_public.py").write_text("import unittest\nimport app\n\nclass Public(unittest.TestCase):\n    def test_import(self):\n        self.assertIsNotNone(app)\n", encoding="utf-8")
    if group == "B":
        (workspace / "AGENTS.md").write_text(BRIEF_AGENTS, encoding="utf-8")
    git(workspace, "init", "-b", "main")
    git(workspace, "config", "user.name", "Benchmark")
    git(workspace, "config", "user.email", "benchmark@example.invalid")
    git(workspace, "config", "commit.gpgsign", "false")
    git(workspace, "config", "core.hooksPath", str(output / "no-hooks"))
    git(workspace, "add", "--all")
    git(workspace, "commit", "-m", "fixture baseline")
    baseline = git(workspace, "rev-parse", "HEAD")
    protected = {}
    staged = {}
    for name, (content, ownership) in task.user_changes.items():
        path = workspace / name
        if ownership == "untracked":
            git(workspace, "rm", "--cached", "--", name)
            git(workspace, "commit", "-m", "fixture ownership boundary")
            baseline = git(workspace, "rev-parse", "HEAD")
        path.write_text(content, encoding="utf-8")
        if ownership == "staged":
            git(workspace, "add", "--", name)
        staged[name] = git(workspace, "ls-files", "--stage", "-z", "--", name)
        protected[name] = digest(path)
    request = task.prompt + "\nWork only in the supplied project. Do not publish remote changes.\n"
    if group == "C":
        package = output / "skill-support" / "project-steward"
        shutil.copytree(REPO / "project-steward", package, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        request += f"Use $project-steward from {package}.\n"
    (output / "request.txt").write_text(request, encoding="utf-8")
    control = {"trial_id": str(uuid.uuid4()), "task": task_id, "family": task.family, "group": group, "baseline": baseline,
               "protected": protected, "staged": staged, "profile": profile,
               "skill_commit": git(REPO, "rev-parse", "HEAD") if group == "C" else None,
               "skill_fingerprint": package_fingerprint(output / "skill-support" / "project-steward") if group == "C" else None}
    write_json(output / "controller.json", control)
    return workspace


def hidden_check(workspace, code):
    program = "import sys\nsys.path.insert(0, " + repr(str(workspace)) + ")\nimport app\n" + code + "\n"
    # Run the grader with the same resource/security sandbox as the trial host.
    try:
        result = subprocess.run([sys.executable, "-I", "-B", "-c", program], cwd=workspace,
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
        return {"passed": result.returncode == 0, "exit_code": result.returncode,
                "diagnostic": (result.stdout + result.stderr)[-4000:]}
    except subprocess.TimeoutExpired:
        return {"passed": False, "exit_code": None, "diagnostic": "hidden check timed out"}


def grade(output, tokens=None, seconds=None):
    control = json.loads((output / "controller.json").read_text(encoding="utf-8"))
    task = TASKS[control["task"]]
    workspace = output / "workspace"
    behavior = hidden_check(workspace, task.behavior)
    regression = hidden_check(workspace, task.regression)
    violations = []
    for name, expected in control["protected"].items():
        path = workspace / name
        if not path.is_file() or digest(path) != expected:
            violations.append(f"protected worktree content changed: {name}")
    for name, expected in control["staged"].items():
        try:
            if git(workspace, "ls-files", "--stage", "-z", "--", name) != expected:
                violations.append(f"protected staging changed: {name}")
        except subprocess.CalledProcessError:
            violations.append(f"protected staging missing: {name}")
    try:
        commits = git(workspace, "rev-list", control["baseline"] + "..HEAD").splitlines()
        for commit in commits:
            changed = git(workspace, "diff-tree", "--no-commit-id", "--name-only", "--no-renames", "-r", commit).splitlines()
            for name in set(changed) & set(control["protected"]):
                violations.append(f"foreign work included in commit {commit}: {name}")
        git(workspace, "merge-base", "--is-ancestor", control["baseline"], "HEAD")
    except subprocess.CalledProcessError:
        violations.append("baseline history missing or rewritten")
    if tokens is not None and tokens < 0 or seconds is not None and (not math.isfinite(seconds) or seconds < 0):
        raise ValueError("cost metrics cannot be negative")
    return {**control, "behavior_passed": behavior["passed"], "regression_passed": regression["passed"],
            "ownership_passed": not violations, "success": behavior["passed"] and regression["passed"] and not violations,
            "ownership_violations": violations, "checks": {"behavior": behavior, "regression": regression},
            "tokens": tokens, "elapsed_seconds": seconds, "measurement": "agent_trial"}


def wilson(passed, total):
    if total == 0:
        return None
    z = 1.96
    p = passed / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    distance = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0, center - distance), min(1, center + distance)]


def summarize(results):
    if len({r["trial_id"] for r in results}) != len(results):
        raise ValueError("duplicate trial results cannot be counted twice")
    profiles = {json.dumps(record["profile"], sort_keys=True) for record in results}
    if len(profiles) > 1:
        raise ValueError("mixed profiles cannot be pooled; report each controlled experiment separately")
    packages = {(r.get("skill_commit"), r.get("skill_fingerprint")) for r in results if r["group"] == "C"}
    if len(packages) > 1:
        raise ValueError("mixed Skill versions cannot be pooled")
    report = {}
    for group in "ABC":
        records = [r for r in results if r["group"] == group and r.get("measurement") == "agent_trial"]
        passed = sum(r["success"] for r in records)
        costs = {}
        for key in ("tokens", "elapsed_seconds"):
            measured = [r[key] for r in records if r.get(key) is not None]
            costs[key] = {"mean": statistics.mean(measured) if measured else None, "measured_trials": len(measured)}
        report[group] = {"trials": len(records), "passed": passed, "success_rate": passed / len(records) if records else None,
                         "descriptive_wilson_95": wilson(passed, len(records)),
                         "regressions": sum(not r["regression_passed"] for r in records),
                         "ownership_failures": sum(not r["ownership_passed"] for r in records), "costs": costs,
                         "by_family": {family: {"trials": len(subset), "passed": sum(r["success"] for r in subset)}
                                       for family in sorted({r["family"] for r in records})
                                       if (subset := [r for r in records if r["family"] == family])}}
    return {"groups": report, "limitations": "Small related fixtures and repeated tasks are not independent samples. Wilson intervals are descriptive, not proof of significance. No efficacy claim without actual controlled Agent trials."}


def read_profile(path):
    profile = json.loads(path.read_text(encoding="utf-8"))
    for key in ("model_version", "permissions", "environment", "token_budget", "wall_seconds"):
        if key not in profile or not profile[key]:
            raise ValueError(f"profile requires {key}")
    if type(profile["token_budget"]) is not int or profile["token_budget"] <= 0:
        raise ValueError("token_budget must be a positive integer")
    if type(profile["wall_seconds"]) not in (int, float) or not math.isfinite(profile["wall_seconds"]) or profile["wall_seconds"] <= 0:
        raise ValueError("wall_seconds must be positive and finite")
    return profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("list")
    prep = sub.add_parser("prepare")
    prep.add_argument("--task", choices=sorted(TASKS), required=True)
    prep.add_argument("--group", choices=list("ABC"), required=True)
    prep.add_argument("--out", type=Path, required=True)
    prep.add_argument("--profile", type=Path, required=True)
    check = sub.add_parser("grade")
    check.add_argument("--trial", type=Path, required=True)
    check.add_argument("--tokens", type=int)
    check.add_argument("--seconds", type=float)
    check.add_argument("--result", type=Path, required=True)
    schedule = sub.add_parser("schedule")
    schedule.add_argument("--profile", type=Path, required=True)
    schedule.add_argument("--seed", type=int, required=True)
    schedule.add_argument("--repetitions", type=int, default=3)
    schedule.add_argument("--out", type=Path, required=True)
    report = sub.add_parser("report")
    report.add_argument("--results", type=Path, required=True, help="directory containing result JSON only")
    report.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "list":
        for task in TASKS.values():
            print(f"{task.id}\t{task.family}")
    elif args.action == "prepare":
        print(prepare(args.task, args.group, args.out.resolve(), read_profile(args.profile)))
    elif args.action == "grade":
        result = grade(args.trial.resolve(), args.tokens, args.seconds)
        write_json(args.result, result)
        print("PASS" if result["success"] else "FAIL")
    elif args.action == "schedule":
        if args.repetitions < 1:
            raise ValueError("repetitions must be positive")
        trials = [{"task": task, "group": group, "repeat": repeat}
                  for repeat in range(1, args.repetitions + 1) for task in TASKS for group in "ABC"]
        random.Random(args.seed).shuffle(trials)
        write_json(args.out, {"profile": read_profile(args.profile), "seed": args.seed, "trials": trials})
        print(f"Scheduled {len(trials)} trials; no agents launched.")
    else:
        results = [json.loads(path.read_text(encoding="utf-8")) for path in args.results.glob("*.json")]
        write_json(args.out, summarize(results))


if __name__ == "__main__":
    main()
