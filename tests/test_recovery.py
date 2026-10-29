"""Behavioral coverage for portable identity, explicit lifecycle, and evidence."""

from copy import deepcopy
from contextlib import redirect_stdout
import argparse
import io
import json
from pathlib import Path
import shutil
from unittest.mock import patch

from support import RecoveryCase
from long_work import migrate_run
from steward_core import storage


class PortableRecovery(RecoveryCase):
    def snapshot(self, run):
        return {p.name: p.read_bytes() for p in run.iterdir()}

    def test_relocated_git_repository_resumes_without_original(self):
        self.init_git()
        run = self.init_run()
        self.milestone(run)
        target = Path(self.temp.name) / "relocated"
        relative = run.relative_to(self.project)
        shutil.copytree(self.project, target)
        hidden = Path(self.temp.name) / "original-hidden"
        self.assertTrue(hidden.resolve().is_relative_to(Path(self.temp.name).resolve()))
        self.project.rename(hidden)
        moved = target / relative
        self.cli("doctor", "--run", moved)
        self.cli("resume", "--run", moved)
        self.cli("checkpoint", "--run", moved, "--summary", "continued elsewhere")
        for name in ("PLAN.md", "HANDOFF.md", "STATE.json", "LOG.md"):
            self.assertNotIn(str(self.project), (moved / name).read_text(encoding="utf-8"))
            self.assertNotIn(self.project.as_posix(), (moved / name).read_text(encoding="utf-8"))

    def test_monorepo_project_binding_survives_move_but_rejects_wrong_git_root(self):
        self.init_git()
        self.project = self.project / "packages" / "api"
        self.project.mkdir(parents=True)
        run = self.init_run()
        self.assertEqual(self.state(run)["project"]["repository_subpath"], "packages/api")
        self.cli("doctor", "--run", run)
        self.git("init", "-b", "main")
        # A different subproject/repository association requires investigation.
        self.cli("doctor", "--run", run, ok=False)

    def test_checkpoint_and_close_preserve_all_milestone_fields(self):
        run = self.init_run()
        self.milestone(run)
        milestones = deepcopy(self.state(run)["milestones"])
        self.cli("checkpoint", "--run", run, "--id", "M-001", "--summary", "snapshot", "--verify", "unavailable")
        self.cli("run", "close", "--run", run, "--reason", "user ended work")
        state = self.state(run)
        self.assertEqual(state["milestones"], milestones)
        self.assertEqual(state["last_verified"], "M-001")
        self.cli("checkpoint", "--run", run, "--summary", "implicit reopen", ok=False)
        self.cli("run", "reopen", "--run", run, "--reason", "authorized follow-up")
        self.assertEqual(self.state(run)["status"], "active")

    def test_unverified_run_can_close_without_claiming_acceptance(self):
        run = self.init_run()
        self.cli("milestone", "add", "--run", run, "--name", "remaining", "--summary", "planned")
        self.cli("run", "close", "--run", run, "--reason", "stop after investigation")
        state = self.state(run)
        self.assertEqual(state["status"], "complete")
        self.assertEqual(state["milestones"][0]["status"], "pending")
        self.assertIsNone(state["last_verified"])

    def test_stable_ids_disambiguate_duplicate_names(self):
        run = self.init_run()
        for _ in range(2):
            self.cli("milestone", "add", "--run", run, "--name", "same", "--summary", "planned")
        before = self.snapshot(run)
        self.cli("milestone", "verify", "--run", run, "--id", "M-999", "--summary", "bad", "--verify", "pass", ok=False)
        self.assertEqual(before, self.snapshot(run))
        self.cli("milestone", "verify", "--run", run, "--id", "M-002", "--summary", "second done", "--verify", "regression passed")
        state = self.state(run)
        self.assertEqual(state["last_verified"], "M-002")
        self.assertEqual(state["milestones"][0]["status"], "pending")
        self.cli("checkpoint", "--run", run, "--milestone", "same", "--summary", "ambiguous label")
        self.assertIsNone(self.state(run)["current_milestone"])

    def test_reopening_verified_milestone_requires_explicit_action(self):
        run = self.init_run()
        self.milestone(run)
        self.cli("milestone", "verify", "--run", run, "--id", "M-001", "--summary", "repeat", "--verify", "pass", ok=False)
        self.cli("milestone", "start", "--run", run, "--id", "M-001", "--summary", "revalidate changed dependency")
        self.assertIsNone(self.state(run)["last_verified"])
        self.assertEqual(self.state(run)["milestones"][0]["status"], "in_progress")

    def test_checkpoint_preserves_paused_lifecycle_by_default(self):
        run = self.init_run()
        self.cli("run", "pause", "--run", run, "--reason", "waiting")
        self.cli("checkpoint", "--run", run, "--summary", "saved")
        self.assertEqual(self.state(run)["status"], "paused")

    def test_structured_evidence_retains_reported_provenance_and_outcomes(self):
        run = self.init_run()
        self.milestone(run)
        for outcome in ("passed", "failed", "skipped", "unavailable", "not_run"):
            flags = ["--exit-code", "0" if outcome == "passed" else "1"] if outcome in {"passed", "failed"} else []
            self.cli("evidence", "--run", run, "--id", "M-001", "--summary", "suite status", "--result", outcome,
                     "--claimed-source", "observed", "--command-text", "never execute this", "--scope", "unit only", *flags)
        records = self.state(run)["evidence"]
        self.assertEqual({r["status"] for r in records}, {"passed", "failed", "skipped", "unavailable", "not_run"})
        self.assertTrue(all(r["source"] == "reported" and r["claimed_source"] == "observed" for r in records))
        before = self.snapshot(run)
        self.cli("evidence", "--run", run, "--id", "M-001", "--summary", "contradiction", "--result", "passed", "--exit-code", "5", ok=False)
        self.assertEqual(before, self.snapshot(run))

    def test_resume_does_not_execute_recorded_commands_and_is_read_only(self):
        run = self.init_run()
        marker = self.project / "should-not-exist"
        self.cli("checkpoint", "--run", run, "--summary", "untrusted next", "--next", f"touch {marker}")
        before = self.snapshot(run)
        self.cli("resume", "--run", run)
        self.cli("doctor", "--run", run)
        self.assertEqual(before, self.snapshot(run))
        self.assertFalse(marker.exists())

    def test_find_filters_and_warns_without_losing_healthy_runs(self):
        run = self.init_run()
        broken = run.parent / "broken"
        broken.mkdir()
        (broken / "STATE.json").write_text("{", encoding="utf-8")
        result = self.cli("find", "--project", self.project, "--status", "active")
        self.assertIn(str(run), result.stdout)
        self.assertIn("WARNING", result.stderr)
        self.assertEqual(self.cli("find", "--project", self.project, "--status", "complete").stdout, "")

    def legacy(self, run, version):
        stamp = self.state(run)["created_at"]
        state = {"schema_version": version, "task": "review", "project": str(self.project),
                 "status": "active", "created_at": stamp, "updated_at": stamp,
                 "milestones": [{"name": "old", "status": "complete", "verification": "regression passed", "recorded_at": stamp}],
                 "last_verified": {"name": "checkpoint", "status": "complete"}, "git": {"repository": str(self.project)}}
        (run / "STATE.json").write_text(json.dumps(state), encoding="utf-8")
        (run / "LOG.md").write_text(f"old log {self.project}\n", encoding="utf-8")
        (run / "PLAN.md").write_text(f"old plan {self.project}\n", encoding="utf-8")
        (run / "HANDOFF.md").write_text(f"old note {self.project}\n", encoding="utf-8")

    def test_both_legacy_schemas_migrate_with_backup_and_scrubbed_paths(self):
        for version in (1, 2):
            with self.subTest(version=version):
                run = self.init_run()
                self.legacy(run, version)
                before = self.snapshot(run)
                output = self.cli("migrate", "--run", run).stdout
                backup = Path(next(line.split("locally: ")[-1] for line in output.splitlines() if "locally: " in line))
                self.addCleanup(shutil.rmtree, backup)
                self.assertEqual(before, self.snapshot(backup))
                self.assertEqual(self.state(run)["last_verified"], "M-001")
                self.cli("doctor", "--run", run)
                for content in self.snapshot(run).values():
                    self.assertNotIn(str(self.project).encode(), content)

    def test_moved_legacy_run_needs_explicit_project_binding(self):
        run = self.init_run()
        self.legacy(run, 2)
        target = Path(self.temp.name) / "new-project"
        relative = run.relative_to(self.project)
        shutil.copytree(self.project, target)
        shutil.rmtree(self.project)
        moved = target / relative
        self.cli("migrate", "--run", moved, ok=False)
        output = self.cli("migrate", "--run", moved, "--project", target).stdout
        self.addCleanup(shutil.rmtree, Path(next(line.split("locally: ")[-1] for line in output.splitlines() if "locally: " in line)))
        self.cli("doctor", "--run", moved)

    def test_each_migration_replace_failure_preserves_recoverable_originals(self):
        for failure in (1, 2, 3, 4):
            with self.subTest(failure=failure):
                run = self.init_run()
                self.legacy(run, 2)
                before = self.snapshot(run)
                original = storage.os.replace
                count = 0

                def fail(source, target):
                    nonlocal count
                    count += 1
                    if count == failure:
                        raise OSError("migration interrupted")
                    return original(source, target)

                output = io.StringIO()
                with redirect_stdout(output), patch.object(storage.os, "replace", side_effect=fail), self.assertRaises(OSError):
                    migrate_run(argparse.Namespace(run=str(run), project=None))
                backup = Path(next(line.split("locally: ")[-1] for line in output.getvalue().splitlines() if "locally: " in line))
                self.addCleanup(shutil.rmtree, backup)
                self.assertEqual(before, self.snapshot(backup))
                if failure == 1:
                    self.assertEqual(before, self.snapshot(run))
                else:
                    self.cli("doctor", "--run", run, ok=False)
                    self.cli("repair", "--run", run)
                    self.cli("doctor", "--run", run)
                    for content in self.snapshot(run).values():
                        self.assertNotIn(str(self.project).encode(), content)
