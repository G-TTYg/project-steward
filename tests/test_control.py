"""Deterministic evaluation tooling checks; no Agent comparisons are run."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from support import RecoveryCase

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
import control
import historical
import host_check


class ControlTests(RecoveryCase):
    def test_usage_unknowns_cached_subset_and_duplicate_turn(self):
        events = [{"type": "turn.started"}, {"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 80, "output_tokens": 10}}]
        self.assertEqual(control.usage_metrics(events, "codex-jsonl-v1")["tokens"], 110)
        self.assertIsNone(control.usage_metrics([], "codex-jsonl-v1")["tokens"])
        self.assertIsNone(control.usage_metrics(events + [{"type": "turn.started"}, {"type": "turn.failed"}], "codex-jsonl-v1")["tokens"])
        with self.assertRaises(ValueError):
            control.usage_metrics(events + [events[-1]], "codex-jsonl-v1")
        with self.assertRaises(ValueError):
            control.usage_metrics([{"type": "session.final", "status": "completed", "usage": {"input_tokens": -1, "output_tokens": 3}}], "steward-host-v1")

    def test_audit_requires_concrete_event_and_human_reason(self):
        row = {"event_id": "1", "category": "command", "unnecessary": True, "reason": "repeat after unchanged passing check", "reviewer": "r1"}
        result = control.audit([{"command": "test"}, {"command": "test"}], [row])
        self.assertEqual(result["unnecessary"]["command"], 1)
        self.assertEqual(result["unreviewed_events"], 1)
        with self.assertRaises(ValueError):
            control.audit([], [row])
        with self.assertRaises(ValueError):
            control.audit([{}], [row, row])

    def test_blind_artifact_integrity_and_retest_matching(self):
        key = "opaque"
        patch = b"diff --git a/app.py b/app.py\n"
        (self.project / (key + ".diff")).write_bytes(patch)
        mapping = {key: {"trial_id": "t1", "group": "C", "task": "bug", "diff_sha256": hashlib.sha256(patch).hexdigest()}}
        review = {"artifact": key, "reviewer": "r1", "rationale": "cohesive fix", "scores": dict.fromkeys(control.RUBRIC, 3)}
        self.assertEqual(control.review_scores(self.project, mapping, [review])["reviews"][0]["group"], "C")
        (self.project / (key + ".diff")).write_text("tampered")
        with self.assertRaises(ValueError):
            control.review_scores(self.project, mapping, [review])
        before = {"trial_id": "t1", "task": "bug", "group": "C", "profile": {}, "success": False}
        after = {**before, "trial_id": "t2", "success": True}
        diagnosis = {"decision_point": "lookup", "cause": "rule", "evidence": "missed call", "intervention": "expand scope"}
        self.assertTrue(control.failure_record(before, after, diagnosis)["resolved"])
        with self.assertRaises(ValueError):
            control.failure_record(before, {**after, "group": "B"}, diagnosis)

    def test_historical_manifest_is_pinned_and_controller_only(self):
        tasks = historical.tasks()
        self.assertEqual(len(tasks), 24)
        self.assertEqual(len({t["id"] for t in tasks}), 24)
        for task in tasks:
            for key in ("base", "fixed"):
                self.assertRegex(task[key], r"^[0-9a-f]{40}$")
            self.assertTrue(task["test_blobs"])
            self.assertTrue(task["source_pull_request"].startswith("https://github.com/"))
            self.assertTrue(all(p.startswith("tests/") and ".." not in p for p in task["test_blobs"]))

    def test_historical_prepare_excludes_future_objects_and_hidden_tests(self):
        self.init_git()
        (self.project / "tests").mkdir()
        (self.project / "tests/test_app.py").write_text("# public old tests\n")
        self.git("add", ".")
        self.git("commit", "-m", "parent")
        base = self.git("rev-parse", "HEAD")
        (self.project / "tests/test_app.py").write_text("# hidden new regression\n")
        (self.project / "app.txt").write_text("fixed\n")
        self.git("add", ".")
        self.git("commit", "-m", "oracle")
        fixed = self.git("rev-parse", "HEAD")
        task = {"id": "real", "family": "historical", "base": base, "fixed": fixed,
                "prompt": "Fix behavior", "test_blobs": {"tests/test_app.py": self.git("rev-parse", fixed + ":tests/test_app.py")}}
        out = Path(self.temp.name) / "trial"
        workspace = historical.prepare(task, self.project, out, "A", {})
        self.assertEqual((workspace / "app.txt").read_text(), "baseline\n")
        self.assertIn("public old", (workspace / "tests/test_app.py").read_text())
        check = subprocess.run(["git", "-C", str(workspace), "cat-file", "-e", fixed], capture_output=True)
        self.assertNotEqual(check.returncode, 0)
        self.assertNotIn(fixed, (out / "request.txt").read_text())

    def test_capture_metrics_and_trial_binding_cli(self):
        events = [{"type": "session.final", "status": "completed", "usage": {"input_tokens": 8, "output_tokens": 2}}]
        raw = json.dumps(events[0]) + "\n"
        capture = Path(self.temp.name) / "capture.json"
        result = subprocess.run([sys.executable, str(Path(control.__file__)), "capture", "--workspace", str(self.project),
                                 "--trial-id", "t1", "--out", str(capture), "--", sys.executable, "-c",
                                 "import sys; print('host diagnostic',file=sys.stderr); print(" + repr(raw.rstrip()) + ")"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("host diagnostic", json.loads(capture.read_text())["stderr"])
        event_file = Path(self.temp.name) / "events.jsonl"
        event_file.write_text(json.loads(capture.read_text())["output"], encoding="utf-8", newline="\n")
        out = Path(self.temp.name) / "metrics.json"
        result = subprocess.run([sys.executable, str(Path(control.__file__)), "metrics", "--adapter", "steward-host-v1",
                                 "--trial-id", "t1", "--capture", str(capture), "--events", str(event_file), "--out", str(out)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        metrics = json.loads(out.read_text())
        self.assertEqual(metrics["tokens"], 10)
        self.assertGreater(metrics["elapsed_seconds"], 0)
        from benchmark import attach_metrics
        with self.assertRaises(ValueError):
            attach_metrics({"trial_id": "other"}, metrics)

    def test_blind_bundle_includes_untracked_and_omits_condition_metadata(self):
        self.init_git()
        trial = Path(self.temp.name) / "trial"
        trial.mkdir()
        # Use the fixture repository as workspace without copying Git history.
        self.project.rename(trial / "workspace")
        workspace = trial / "workspace"
        baseline = control.git(workspace, "rev-parse", "HEAD")
        (workspace / "feature.py").write_text("def feature(): return 1\n")
        (workspace / "AGENTS.md").write_text("condition C\n")
        (trial / "controller.json").write_text(json.dumps({"trial_id": "secret-trial", "group": "C", "task": "bug", "baseline": baseline}))
        bundle = Path(self.temp.name) / "bundle"
        mapping = Path(self.temp.name) / "private.json"
        control.blind_bundle([trial], bundle, mapping)
        patch = next(bundle.glob("*.diff")).read_text()
        self.assertIn("feature.py", patch)
        self.assertIn("def feature", patch)
        self.assertNotIn("secret-trial", patch)
        self.assertNotIn("condition C", patch)

    def test_host_contract_reports_declaration_separately(self):
        package = Path(host_check.__file__).resolve().parents[1]
        run = self.init_run()
        report = host_check.inspect(package, self.project, run=run)
        self.assertEqual(report["host_behavior"], "not_tested")
        self.assertFalse(report["handoff"]["head_changed"])
        capabilities = {"contract": "steward-host-v1", "host": "custom",
                        "capabilities": dict.fromkeys(["skill_discovery", "project_binding", "instruction_precedence", "authorization", "filesystem_scope", "command_execution", "git", "telemetry"], "manual")}
        self.assertEqual(host_check.inspect(package, self.project, capabilities)["host"], "custom")
        with self.assertRaises(ValueError):
            host_check.inspect(package, self.project, {**capabilities, "capabilities": {}})
