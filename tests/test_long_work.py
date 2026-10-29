"""Exercise the recovery CLI in disposable projects, including real Git index boundaries.

Assertions focus on recoverable state and preserved content, rather than generated
headings. No test reads or mutates the user's installed skill or Git configuration.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "project-steward" / "scripts" / "long_work.py"


from support import RecoveryCase


class RecoveryCLI(RecoveryCase):
    def test_pending_checkpoint_does_not_verify_a_slice(self):
        run = self.init_run()
        self.cli("checkpoint", "--run", run, "--milestone", "unfinished",
                 "--summary", "implementing", "--verify", "pending")
        self.assertIsNone(self.state(run).get("last_verified"))
        self.assertNotIn("Latest verified slice: unfinished",
                         (run / "HANDOFF.md").read_text(encoding="utf-8"))

    def test_milestone_verification_does_not_finish_run(self):
        run = self.init_run()
        self.milestone(run)
        state = self.state(run)
        self.assertEqual(state["status"], "active")
        self.assertEqual(self.verified(run)["name"], "first")
        self.assertEqual(state["milestones"][-1]["status"], "verified")

    def test_unverified_milestones_preserve_previous_verified_slice(self):
        run = self.init_run()
        self.milestone(run)
        for status in ("active", "paused", "blocked"):
            with self.subTest(status=status):
                self.milestone(run, "unfinished", "--status", status)
                state = self.state(run)
                self.assertEqual(self.verified(run)["name"], "first")
                self.assertNotIn("completed_at", state["milestones"][-1])

    def test_handoff_notes_survive_repeated_updates(self):
        run = self.init_run()
        note = "\n## Recovery detail\nKeep the compatibility fixture; owner: Alice.\n"
        with (run / "HANDOFF.md").open("a", encoding="utf-8") as stream:
            stream.write(note)
        self.milestone(run)
        self.cli("checkpoint", "--run", run, "--summary", "next slice")
        self.assertEqual((run / "HANDOFF.md").read_text(encoding="utf-8").count(note), 1)

    def test_legacy_state_and_handoff_are_preserved(self):
        run = self.init_run()
        state = self.state(run)
        state.pop("schema_version", None)
        state.pop("last_verified", None)
        state["project"] = str(self.project)
        state["milestones"] = [{"name": "old", "status": "verified", "summary": "legacy"}]
        (run / "STATE.json").write_text(json.dumps(state), encoding="utf-8")
        legacy = "# Old handoff\n\nManual Git merge evidence: keep this.\n"
        (run / "HANDOFF.md").write_text(legacy, encoding="utf-8")
        self.backup_from_output(self.cli("migrate", "--run", run).stdout)
        self.cli("checkpoint", "--run", run, "--summary", "resuming")
        self.cli("checkpoint", "--run", run, "--summary", "continuing")
        self.assertIsNone(self.verified(run))
        self.assertEqual(self.state(run)["milestones"][0]["legacy_status"], "verified")
        self.assertEqual((run / "HANDOFF.md").read_text(encoding="utf-8").count(legacy), 1)

    def test_git_observations_and_attached_commit_are_real(self):
        self.init_git()
        commit = self.git("rev-parse", "HEAD")
        run = self.init_run()
        self.milestone(run, "first", "--commit", commit[:10],
                       "--base-branch", "main", "--merge-result", "not needed")
        state = self.state(run)
        self.assertEqual(state["git"]["branch"], "main")
        self.assertEqual(state["git"]["head"], commit)
        self.assertIsNone(state["git"]["upstream"])
        self.assertIsNone(state["git"]["unpushed_count"])
        self.assertEqual(self.verified(run)["commit"], commit)
        self.assertEqual(state["workflow"]["base_branch"], "main")

    def test_upstream_comparison_counts_local_commits(self):
        self.init_git()
        self.git("branch", "baseline")
        self.git("branch", "--set-upstream-to", "baseline", "main")
        (self.project / "app.txt").write_text("local commit\n", encoding="utf-8")
        self.git("add", "--", "app.txt")
        self.git("commit", "-m", "local change")
        state = self.state(self.init_run())
        self.assertEqual(state["git"]["upstream"], "baseline")
        self.assertEqual(state["git"]["unpushed_count"], 1)

    def test_checkpoint_cannot_change_verified_slice_history(self):
        self.init_git()
        run = self.init_run()
        self.milestone(run)
        commit = self.git("rev-parse", "HEAD")
        self.cli("checkpoint", "--run", run, "--summary", "recording commit", "--commit", commit)
        self.assertNotIn("commit", self.verified(run))
        self.assertNotIn("commit", self.state(run)["milestones"][-1])

    def test_invalid_commit_leaves_files_and_index_unchanged(self):
        self.init_git()
        run = self.init_run()
        before = {p.name: p.read_bytes() for p in run.iterdir()}
        self.cli("checkpoint", "--run", run, "--summary", "bad commit",
                 "--commit", "no-such-commit", "--commit-run-state", ok=False)
        self.assertEqual(before, {p.name: p.read_bytes() for p in run.iterdir()})
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")

    def test_run_state_commit_excludes_other_files_and_code(self):
        self.init_git()
        run = self.init_run()
        (run / "private.txt").write_text("not a managed recovery file", encoding="utf-8")
        (self.project / "app.txt").write_text("user edit\n", encoding="utf-8")
        self.cli("checkpoint", "--run", run, "--summary", "recoverable",
                 "--commit-run-state")
        committed = self.git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()
        self.assertEqual({Path(p).name for p in committed}, {"PLAN.md", "LOG.md", "HANDOFF.md", "STATE.json"})
        self.assertIn("private.txt", self.git("status", "--short"))
        self.assertEqual((self.project / "app.txt").read_text(encoding="utf-8"), "user edit\n")
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")

    def test_staged_user_work_is_refused_before_writing(self):
        self.init_git()
        run = self.init_run()
        (self.project / "app.txt").write_text("staged user edit\n", encoding="utf-8")
        self.git("add", "--", "app.txt")
        before = {p.name: p.read_bytes() for p in run.iterdir()}
        self.cli("checkpoint", "--run", run, "--summary", "refuse",
                 "--commit-run-state", ok=False)
        self.assertEqual(before, {p.name: p.read_bytes() for p in run.iterdir()})
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "app.txt")

    def test_init_rejects_escape_and_missing_project(self):
        outside = Path(self.temp.name) / "outside"
        for base in ("../outside", str(outside)):
            self.cli("init", "--project", self.project, "--task", "escape", "--base", base, ok=False)
        self.assertFalse(outside.exists())
        missing = Path(self.temp.name) / "missing"
        self.cli("init", "--project", missing, "--task", "missing", ok=False)
        self.assertFalse(missing.exists())

    def test_arbitrary_run_directory_does_not_stage_project(self):
        self.init_git()
        (self.project / "app.txt").write_text("user edit\n", encoding="utf-8")
        self.cli("checkpoint", "--run", self.project, "--summary", "invalid",
                 "--commit-run-state", ok=False)
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")
        self.assertFalse((self.project / "STATE.json").exists())

    def test_new_slice_does_not_inherit_old_verification_or_commit(self):
        self.init_git()
        run = self.init_run()
        self.milestone(run, "first", "--commit", self.git("rev-parse", "HEAD"))
        self.cli("checkpoint", "--run", run, "--milestone", "second", "--summary", "starting")
        state = self.state(run)
        self.assertNotEqual(state["verification"], "unit tests passed")
        self.assertNotIn("commit", state["workflow"])
        self.assertEqual(self.verified(run)["name"], "first")

    def test_run_closes_explicitly_and_risk_can_be_cleared(self):
        run = self.init_run()
        self.cli("checkpoint", "--run", run, "--summary", "risk", "--risk", "blocked on fixture")
        self.cli("checkpoint", "--run", run, "--summary", "resolved", "--risk", "",
                 "--status", "complete", "--verify", "checks passed")
        self.assertEqual(self.state(run)["status"], "complete")
        self.assertEqual(self.state(run)["risk"], "")
        self.assertIsNone(self.state(run)["last_verified"])

    def test_run_closure_retains_recorded_implementation_commit(self):
        self.init_git()
        run = self.init_run()
        commit = self.git("rev-parse", "HEAD")
        self.milestone(run, "first", "--commit", commit)
        verified = self.state(run)["last_verified"]
        self.cli("checkpoint", "--run", run, "--summary", "close run",
                 "--status", "complete", "--verify", "all checks passed")
        self.assertEqual(self.verified(run)["commit"], commit)
        self.assertEqual(self.state(run)["last_verified"], verified)

    def test_complete_milestone_is_distinct_from_complete_run(self):
        run = self.init_run()
        self.milestone(run, "first", "--status", "complete")
        self.assertEqual(self.state(run)["status"], "active")
        self.assertEqual(self.verified(run)["status"], "verified")

    def test_invalid_handoff_markers_fail_without_partial_writes(self):
        run = self.init_run()
        with (run / "HANDOFF.md").open("a", encoding="utf-8") as stream:
            stream.write("\n<!-- project-steward:status:start -->\n")
        before = {p.name: p.read_bytes() for p in run.iterdir()}
        self.cli("checkpoint", "--run", run, "--summary", "reject damaged handoff", ok=False)
        self.assertEqual(before, {p.name: p.read_bytes() for p in run.iterdir()})

    def test_verified_status_requires_explicit_evidence(self):
        run = self.init_run()
        before = {p.name: p.read_bytes() for p in run.iterdir()}
        self.cli("checkpoint", "--run", run, "--summary", "no evidence",
                 "--status", "verified", ok=False)
        self.assertEqual(before, {p.name: p.read_bytes() for p in run.iterdir()})

    def test_corrupt_state_is_refused_without_other_writes(self):
        run = self.init_run()
        for invalid in ("[]", "{", '{"project": 123}',
                        json.dumps({"task": "review", "project": str(self.project), "schema_version": 99})):
            with self.subTest(invalid=invalid):
                (run / "STATE.json").write_text(invalid, encoding="utf-8")
                before = {p.name: p.read_bytes() for p in run.iterdir()}
                self.cli("checkpoint", "--run", run, "--summary", "invalid state", ok=False)
                self.assertEqual(before, {p.name: p.read_bytes() for p in run.iterdir()})

    def test_copied_run_cannot_write_outside_original_project(self):
        run = self.init_run()
        other = Path(self.temp.name) / "copied-run"
        other.mkdir()
        for source in run.iterdir():
            (other / source.name).write_bytes(source.read_bytes())
        before = {p.name: p.read_bytes() for p in other.iterdir()}
        self.cli("checkpoint", "--run", other, "--summary", "outside original project", ok=False)
        self.assertEqual(before, {p.name: p.read_bytes() for p in other.iterdir()})

    def test_status_find_and_unique_run_names(self):
        first = self.init_run()
        self.assertIn(str(first), self.cli("find", "--project", self.project).stdout)
        before = {p.name: p.read_bytes() for p in first.iterdir()}
        self.assertIn("review", self.cli("status", "--run", first).stdout)
        self.assertEqual(before, {p.name: p.read_bytes() for p in first.iterdir()})
        self.init_run()
        self.assertEqual(len(list(first.parent.iterdir())), 2)

    def test_gitless_project_still_supports_recovery(self):
        self.env["PATH"] = ""
        run = self.init_run()
        self.milestone(run)
        self.assertFalse(self.state(run)["git"]["available"])
        self.assertEqual(self.verified(run)["name"], "first")

    def test_unborn_and_detached_git_states_are_observed(self):
        self.git("init", "-b", "main")
        run = self.init_run()
        self.assertEqual(self.state(run)["git"]["branch"], "main")
        self.assertIsNone(self.state(run)["git"]["head"])
        self.init_git()
        commit = self.git("rev-parse", "HEAD")
        self.git("checkout", "--detach", commit)
        self.cli("checkpoint", "--run", run, "--summary", "detached checkout")
        self.assertEqual(self.state(run)["git"]["branch"], "detached HEAD")
        self.assertEqual(self.state(run)["git"]["head"], commit)


if __name__ == "__main__":
    unittest.main()
