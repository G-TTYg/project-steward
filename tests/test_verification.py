"""Collector provenance, bounded output and CI identity boundaries."""

import copy
import os
import subprocess
import sys
from unittest.mock import patch

from support import RecoveryCase, SCRIPT
import verify


class VerificationTests(RecoveryCase):
    def test_observed_cli_and_changed_snapshot(self):
        self.init_git()
        run = self.init_run()
        self.cli("milestone", "add", "--run", run, "--name", "check", "--summary", "goal")
        args = [sys.executable, str(SCRIPT.parent / "verify.py"), "--run", str(run), "--id", "M-001",
                "--summary", "regression", "--scope", "API", "exec", "--", sys.executable, "-c",
                "from pathlib import Path; Path('app.txt').write_text('changed'); print('ok')"]
        result = subprocess.run(args, capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        evidence = self.state(run)["evidence"][0]
        self.assertEqual(evidence["source"], "observed")
        self.assertTrue(evidence["provenance"]["source_changed"])
        self.assertIsNone(self.state(run)["last_verified"])
        self.cli("doctor", "--run", run)
        self.assertNotIn(str(self.project), (run / "STATE.json").read_text())

    def test_failed_timeout_bounded_redacted_and_no_shell(self):
        with patch.dict(os.environ, {"TEST_API_KEY": "private-value-123"}):
            result = verify.execute([sys.executable, "-c", "print('private-value-123'); print('x'*10000); raise SystemExit(3)"], self.project, 10, 256)
        self.assertEqual(result["exit_code"], 3)
        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["output_truncated"])
        self.assertNotIn("private-value-123", result["output"])
        result = verify.execute([sys.executable, "-c", "import time; time.sleep(20)"], self.project, .1)
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["status"], "failed")

    def test_ci_attempt_pagination_identity_and_failure(self):
        run = {"repository": {"full_name": "a/b"}, "head_sha": "a" * 40, "path": ".github/workflows/ci.yml",
               "id": 12, "run_attempt": 2, "updated_at": "time", "status": "completed", "conclusion": "success",
               "html_url": "https://github.com/a/b/actions/runs/12"}
        jobs = {"total_count": 1, "jobs": [{"id": 1, "name": "unit", "status": "completed", "conclusion": "success"}]}
        def fetch(path):
            return copy.deepcopy(jobs if "/jobs?" in path else run)
        record = verify.github_evidence("a/b", 12, run["path"], "a" * 40, fetch)
        self.assertEqual(record["source"], "independently_confirmed")
        local_run = self.init_run()
        self.cli("milestone", "add", "--run", local_run, "--name", "CI", "--summary", "goal")
        state = self.state(local_run)
        record.update(id="V-001", milestone_id="M-001", summary="CI API observation", recorded_at=verify.now_utc())
        state["evidence"].append(record)
        verify.append_event(state, "CI observed")
        from steward_core.state import validate
        validate(state)
        record["provenance"]["jobs"][0]["conclusion"] = "failure"
        with self.assertRaises(SystemExit):
            validate(state)
        jobs["jobs"][0]["conclusion"] = "skipped"
        self.assertEqual(verify.github_evidence("a/b", 12, run["path"], "a" * 40, fetch)["status"], "failed")
        for field, value in (("head_sha", "b" * 40), ("path", ".github/workflows/evil.yml"), ("status", "in_progress")):
            with patch.dict(run, {field: value}):
                with self.assertRaises(SystemExit):
                    verify.github_evidence("a/b", 12, ".github/workflows/ci.yml", "a" * 40, fetch)
        calls = 0
        def rerun(path):
            nonlocal calls
            result = fetch(path)
            if "/jobs?" not in path:
                calls += 1
                result["run_attempt"] = calls
            return result
        with self.assertRaises(SystemExit):
            verify.github_evidence("a/b", 12, run["path"], "a" * 40, rerun)

    def test_report_claim_cannot_become_observed(self):
        run = self.init_run()
        self.cli("milestone", "add", "--run", run, "--name", "check", "--summary", "goal")
        self.cli("evidence", "--run", run, "--id", "M-001", "--summary", "claim", "--result", "passed", "--claimed-source", "observed")
        self.assertEqual(self.state(run)["evidence"][0]["source"], "reported")
