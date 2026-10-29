"""Reject logically impossible state before any mutation can reach disk."""

from copy import deepcopy
import json

from support import RecoveryCase
from steward_core.state import refresh_verified, validate


class StateInvariants(RecoveryCase):
    def test_same_timestamp_reverification_uses_event_revision(self):
        run = self.init_run()
        self.milestone(run)
        state = self.state(run)
        first = state["milestones"][0]
        second = deepcopy(first)
        second.update(id="M-002", verified_revision=1)
        state["milestones"].append(second)
        first["verified_revision"] = state["revision"]
        refresh_verified(state)
        self.assertEqual(state["last_verified"], "M-001")
        validate(state)

    def test_impossible_references_times_statuses_and_evidence_are_rejected(self):
        run = self.init_run()
        self.milestone(run)
        valid = self.state(run)
        alterations = [
            lambda s: s.update(last_verified="M-999"),
            lambda s: s.update(current_milestone="same-name"),
            lambda s: s.update(status="verified"),
            lambda s: s.update(revision=True),
            lambda s: s.update(updated_at="not a timestamp"),
            lambda s: s.update(created_at="2999-01-01T00:00:00+00:00"),
            lambda s: s["milestones"].append(deepcopy(s["milestones"][0])),
            lambda s: s["milestones"][0].update(status="active"),
            lambda s: s["milestones"][0].update(verification=""),
            lambda s: s["milestones"][0].update(commit="abc123", commit_relationship="caller_attached"),
            lambda s: s["events"][0].update(revision=99),
        ]
        validate(valid)
        for change in alterations:
            state = deepcopy(valid)
            change(state)
            with self.subTest(state=state), self.assertRaises(SystemExit):
                validate(state)
        self.assertEqual(self.state(run), valid)

    def test_invalid_binding_and_managed_symlinks_are_refused(self):
        run = self.init_run()
        original = self.state(run)
        for root in ("/absolute", "C:/private", "../../../../../../", ".", "../x"):
            state = deepcopy(original)
            state["project"]["root_relative"] = root
            (run / "STATE.json").write_text(json.dumps(state), encoding="utf-8")
            self.cli("doctor", "--run", run, ok=False)
        (run / "STATE.json").write_text(json.dumps(original), encoding="utf-8")
        target = self.project / "outside-notes"
        target.write_text("preserve", encoding="utf-8")
        (run / "HANDOFF.md").unlink()
        try:
            (run / "HANDOFF.md").symlink_to(target)
        except OSError:
            self.skipTest("symlink creation is not available")
        self.cli("checkpoint", "--run", run, "--summary", "unsafe", ok=False)
        self.assertEqual(target.read_text(encoding="utf-8"), "preserve")
