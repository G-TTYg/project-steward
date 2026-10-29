"""Verify the evaluation machinery without pretending to run evaluated agents."""

from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
import benchmark
from corpus import TASKS


PROFILE = {"model_version": "fixture-self-test", "permissions": "disposable local tests",
           "environment": "self-test only", "token_budget": 1, "wall_seconds": 1}


class EvaluationFixtures(unittest.TestCase):
    def test_all_broken_baselines_fail_and_reference_solutions_pass(self):
        self.assertEqual(len(TASKS), 24)
        self.assertEqual(len({task.family for task in TASKS.values()}), 8)
        with tempfile.TemporaryDirectory(prefix="steward-eval-selftest-") as temp:
            for task in TASKS.values():
                with self.subTest(task=task.id):
                    trial = Path(temp) / task.id
                    workspace = benchmark.prepare(task.id, "A", trial, PROFILE)
                    self.assertFalse(benchmark.grade(trial)["success"])
                    for name, content in task.solution.items():
                        (workspace / name).write_text(content, encoding="utf-8")
                    result = benchmark.grade(trial)
                    self.assertTrue(result["success"], result)
                    self.assertIsNone(result["tokens"])
                    self.assertIsNone(result["elapsed_seconds"])

    def test_conditions_hide_solutions_and_preserve_protected_staging(self):
        with tempfile.TemporaryDirectory(prefix="steward-eval-selftest-") as temp:
            for group in "ABC":
                trial = Path(temp) / group
                workspace = benchmark.prepare("ownership-index-1", group, trial, PROFILE)
                self.assertEqual((workspace / "AGENTS.md").exists(), group == "B")
                self.assertEqual((trial / "skill-support").exists(), group == "C")
                self.assertFalse((workspace / "controller.json").exists())
                self.assertFalse((workspace / "corpus.py").exists())
                task = TASKS["ownership-index-1"]
                for name, content in task.solution.items():
                    (workspace / name).write_text(content, encoding="utf-8")
                self.assertTrue(benchmark.grade(trial)["success"])
                benchmark.git(workspace, "add", "--all")
                benchmark.git(workspace, "commit", "-m", "accidental foreign commit")
                result = benchmark.grade(trial)
                self.assertFalse(result["ownership_passed"])
                self.assertTrue(any("foreign work" in v for v in result["ownership_violations"]))

    def test_report_rejects_duplicates_and_mixed_profiles(self):
        record = {"trial_id": "one", "profile": PROFILE, "group": "A", "success": True,
                  "regression_passed": True, "ownership_passed": True, "family": "local_bug",
                  "tokens": None, "elapsed_seconds": None, "measurement": "agent_trial"}
        with self.assertRaises(ValueError):
            benchmark.summarize([record, deepcopy(record)])
        other = deepcopy(record)
        other["trial_id"] = "two"
        other["profile"] = {**PROFILE, "model_version": "different"}
        with self.assertRaises(ValueError):
            benchmark.summarize([record, other])
        report = benchmark.summarize([record])
        self.assertIsNone(report["groups"]["A"]["costs"]["tokens"]["mean"])
        self.assertIsNone(report["groups"]["B"]["success_rate"])
