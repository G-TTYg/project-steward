#!/usr/bin/env python3
"""Controller-only telemetry, process audit, blind review and failure/retest tools.

No command is loaded from trial/recovery state. A capture requires explicit argv.
Human audit/review judgments are kept separate from deterministic outcome grading.
"""

import argparse
import difflib
import hashlib
import json
import math
from pathlib import Path
import secrets
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "project-steward" / "scripts"))
from verify import execute
from benchmark import git, write_json


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def usage_metrics(events, adapter):
    """Cached tokens are a subset of input, never added twice."""
    usages = []
    failed = False
    open_turn = False
    for event in events:
        if adapter == "codex-jsonl-v1":
            if event.get("type") == "turn.started":
                if open_turn:
                    raise ValueError("overlapping Codex turns")
                open_turn = True
            elif event.get("type") in {"turn.completed", "turn.failed"}:
                if not open_turn:
                    raise ValueError("duplicate/orphan terminal turn event")
                open_turn = False
                if event["type"] == "turn.failed":
                    failed = True
                else:
                    usages.append(event.get("usage"))
            elif event.get("type") == "error":
                failed = True
        elif adapter == "steward-host-v1":
            if event.get("type") == "session.final":
                if usages:
                    raise ValueError("duplicate session final")
                usages.append(event.get("usage"))
                failed |= event.get("status") != "completed"
        else:
            raise ValueError("unknown telemetry adapter")
    complete = bool(usages) and not open_turn and not failed
    totals = {"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0}
    for usage in usages:
        if not isinstance(usage, dict):
            complete = False
            continue
        for key in totals:
            value = usage.get(key, 0 if key == "cached_input_tokens" else None)
            if type(value) is not int or value < 0:
                raise ValueError("usage must contain nonnegative integer counts")
            totals[key] += value
        if usage.get("cached_input_tokens", 0) > usage["input_tokens"]:
            raise ValueError("cached input exceeds input")
    return {**{k: v if complete else None for k, v in totals.items()},
            "tokens": totals["input_tokens"] + totals["output_tokens"] if complete else None,
            "usage_complete": complete, "completed_turns": len(usages), "adapter": adapter}


def load_events(path):
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("event file exceeds 16 MiB; split/normalize explicitly")
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(e, dict) for e in events):
        raise ValueError("events must be JSON objects")
    return events


def audit(events, judgments):
    indexed = {str(i): event for i, event in enumerate(events, 1)}
    categories = {"document", "branch", "command", "confirmation"}
    totals = dict.fromkeys(categories, 0)
    seen = set()
    for item in judgments:
        event_id = item.get("event_id")
        if event_id not in indexed or event_id in seen or item.get("category") not in categories:
            raise ValueError("audit requires unique existing event IDs and valid categories")
        if type(item.get("unnecessary")) is not bool or not item.get("reason", "").strip() or not item.get("reviewer", "").strip():
            raise ValueError("audit requires explicit judgment, reason and reviewer")
        seen.add(event_id)
        totals[item["category"]] += int(item["unnecessary"])
    return {"measurement": "human_process_audit", "events": len(events), "reviewed_events": len(seen),
            "unnecessary": totals, "judgments": judgments, "unreviewed_events": len(events) - len(seen)}


RUBRIC = {"responsibility": "Responsibilities cohesive; no needless abstraction",
          "contracts": "Invariants, names and failure behavior understandable",
          "cohesion": "Change stays on task and fits existing project structure"}


def blind_bundle(trials, out, mapping):
    if out.exists() or mapping.exists():
        raise ValueError("blind output and private mapping must be new")
    if mapping.resolve().is_relative_to(out.resolve()):
        raise ValueError("private mapping must remain outside reviewer bundle")
    out.mkdir(parents=True)
    private = {}
    for trial in trials:
        control = read(trial / "controller.json")
        key = secrets.token_hex(12)
        # No commit messages, condition, model or trial IDs in the review artifact.
        workspace = trial / "workspace"
        patch = git(workspace, "diff", "--no-ext-diff", "--no-textconv", "--no-renames", "--no-color",
                    control["baseline"], "--", ".", ":(exclude)AGENTS.md", ":(exclude)docs/agent-runs/**")
        for name in git(workspace, "ls-files", "--others", "--exclude-standard", "-z").split("\0"):
            if not name or name == "AGENTS.md" or name.startswith("docs/agent-runs/"):
                continue
            path = workspace / name
            if path.is_symlink():
                patch += f"\nNew symlink: {name}\n"
                continue
            try:
                content = path.read_text(encoding="utf-8")
                patch += "\n" + "".join(difflib.unified_diff([], content.splitlines(keepends=True), fromfile="/dev/null", tofile="b/" + name))
            except UnicodeError:
                patch += f"\nNew binary file: {name}; requires separate review\n"
        (out / (key + ".diff")).write_text(patch + "\n", encoding="utf-8")
        private[key] = {"trial_id": control["trial_id"], "group": control["group"], "task": control["task"],
                        "diff_sha256": hashlib.sha256((patch + "\n").encode()).hexdigest()}
    write_json(out / "rubric.json", {"criteria": RUBRIC, "scale": {"1": "poor", "2": "mixed", "3": "clear"},
                                    "reviews": [{"artifact": key, "reviewer": "", "scores": dict.fromkeys(RUBRIC), "rationale": ""} for key in private]})
    write_json(mapping, private)


def review_scores(bundle, mapping, reviews):
    results = []
    seen = set()
    for row in reviews:
        key, reviewer = row.get("artifact"), row.get("reviewer", "").strip()
        if key not in mapping or not reviewer or (key, reviewer) in seen or not row.get("rationale", "").strip():
            raise ValueError("unknown artifact/duplicate/incomplete review")
        path = bundle / (key + ".diff")
        if hashlib.sha256(path.read_bytes()).hexdigest() != mapping[key]["diff_sha256"]:
            raise ValueError("blind artifact changed after assignment")
        if set(row.get("scores", {})) != set(RUBRIC) or any(type(v) is not int or v not in (1, 2, 3) for v in row["scores"].values()):
            raise ValueError("score each rubric criterion from 1 to 3")
        seen.add((key, reviewer))
        results.append({**row, **mapping[key]})
    return {"measurement": "blinded_human_review", "reviews": results, "artifacts_unreviewed": sorted(set(mapping) - {r["artifact"] for r in reviews})}


def failure_record(before, after, diagnosis):
    required = ("decision_point", "cause", "evidence", "intervention")
    if any(not isinstance(diagnosis.get(k), str) or not diagnosis[k].strip() for k in required):
        raise ValueError("failure diagnosis is incomplete")
    if diagnosis["cause"] not in {"model", "rule", "helper", "environment"} or before.get("success") is not False:
        raise ValueError("expected a failed result and a known cause")
    if after:
        if any(before.get(k) != after.get(k) for k in ("task", "group", "profile")) or before["trial_id"] == after["trial_id"]:
            raise ValueError("retest must be a new trial with the same task/condition/profile")
    return {"measurement": "failure_retest", "before": before["trial_id"], "after": after["trial_id"] if after else None,
            "diagnosis": diagnosis, "retest": {k: before[k] for k in ("task", "group", "profile")},
            "resolved": after.get("success") if after else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    metrics = sub.add_parser("metrics")
    metrics.add_argument("--events", type=Path, required=True)
    metrics.add_argument("--adapter", choices=["codex-jsonl-v1", "steward-host-v1"], required=True)
    metrics.add_argument("--capture", type=Path, help="collector metadata from capture; supplies measured elapsed time")
    metrics.add_argument("--trial-id", required=True)
    capture = sub.add_parser("capture")
    capture.add_argument("--workspace", type=Path, required=True)
    capture.add_argument("--timeout", type=float, default=900)
    capture.add_argument("--trial-id", required=True)
    capture.add_argument("argv", nargs=argparse.REMAINDER)
    aud = sub.add_parser("audit")
    aud.add_argument("--events", type=Path, required=True)
    aud.add_argument("--judgments", type=Path, required=True)
    blind = sub.add_parser("blind")
    blind.add_argument("--trials", type=Path, nargs="+", required=True)
    blind.add_argument("--mapping", type=Path, required=True)
    review = sub.add_parser("review")
    review.add_argument("--bundle", type=Path, required=True)
    review.add_argument("--mapping", type=Path, required=True)
    review.add_argument("--reviews", type=Path, required=True)
    fail = sub.add_parser("failure")
    fail.add_argument("--before", type=Path, required=True)
    fail.add_argument("--after", type=Path)
    fail.add_argument("--diagnosis", type=Path, required=True)
    for command in (metrics, capture, aud, blind, review, fail):
        command.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("output already exists; preserve previous measurements")
    if args.action == "capture":
        argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
        result = execute(argv, args.workspace.resolve(), args.timeout, 1048576, merge_stderr=False)
        # Local controller record may contain sensitive host text. Never publish it by default.
        write_json(args.out, {"measurement": "host_capture", "trial_id": args.trial_id, **result})
    elif args.action == "metrics":
        result = usage_metrics(load_events(args.events), args.adapter)
        result.update(trial_id=args.trial_id, events_sha256=hashlib.sha256(args.events.read_bytes()).hexdigest(), elapsed_seconds=None)
        if args.capture:
            capture = read(args.capture)
            seconds = capture.get("duration_seconds")
            if capture.get("measurement") != "host_capture" or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
                raise ValueError("invalid capture metadata")
            # Bind measured time to the exact captured events, not another session.
            if (capture.get("trial_id") != args.trial_id or capture.get("output_truncated")
                    or capture.get("output", "").replace("\r\n", "\n") != args.events.read_text(encoding="utf-8")):
                raise ValueError("capture/events mismatch or truncated output")
            result.update(elapsed_seconds=seconds, capture_exit_code=capture["exit_code"])
            if capture.get("timed_out") or capture["exit_code"] != 0:
                result.update(tokens=None, input_tokens=None, output_tokens=None, cached_input_tokens=None, usage_complete=False)
        write_json(args.out, result)
    elif args.action == "audit":
        write_json(args.out, audit(load_events(args.events), read(args.judgments)))
    elif args.action == "blind":
        blind_bundle(args.trials, args.out, args.mapping)
    elif args.action == "review":
        write_json(args.out, review_scores(args.bundle, read(args.mapping), read(args.reviews)))
    else:
        write_json(args.out, failure_record(read(args.before), read(args.after) if args.after else None, read(args.diagnosis)))


if __name__ == "__main__":
    main()
