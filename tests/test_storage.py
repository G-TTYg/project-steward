"""Fault injection at every authoritative/derived replacement boundary."""

from copy import deepcopy
from unittest.mock import patch

from support import RecoveryCase
from long_work import append_event
from steward_core import storage


class InterruptedStorage(RecoveryCase):
    def test_each_replace_failure_is_detected_and_repairable(self):
        for failure in (1, 2, 3):
            with self.subTest(failure=failure):
                run = self.init_run()
                with (run / "HANDOFF.md").open("a", encoding="utf-8") as stream:
                    stream.write("\nmanual owner: Alice\n")
                before = self.state(run)
                after = deepcopy(before)
                after["summary"] = "after interruption"
                append_event(after, "- Saved progress.")
                original = storage.os.replace
                count = 0

                def fail(source, target):
                    nonlocal count
                    count += 1
                    if count == failure:
                        raise OSError("injected interruption")
                    return original(source, target)

                with patch.object(storage.os, "replace", side_effect=fail), self.assertRaises(OSError):
                    storage.save_run(run, after, before["revision"])
                if failure == 1:
                    self.assertEqual(self.state(run), before)
                    self.cli("doctor", "--run", run)
                else:
                    self.assertEqual(self.state(run), after)
                    self.cli("doctor", "--run", run, ok=False)
                    self.cli("checkpoint", "--run", run, "--summary", "refuse stale views", ok=False)
                    self.cli("repair", "--run", run)
                    self.cli("doctor", "--run", run)
                self.assertIn("manual owner: Alice", (run / "HANDOFF.md").read_text(encoding="utf-8"))

    def test_prepare_failure_leaves_all_original_files_intact(self):
        run = self.init_run()
        before = {p.name: p.read_bytes() for p in run.iterdir()}
        state = self.state(run)
        append_event(state, "- prepared")
        with patch.object(storage.os, "fsync", side_effect=OSError("disk full")), self.assertRaises(OSError):
            storage.save_run(run, state, state["revision"] - 1)
        self.assertEqual(before, {p.name: p.read_bytes() for p in run.iterdir()})

    def test_repair_preserves_unrecognized_log_edits(self):
        run = self.init_run()
        with (run / "LOG.md").open("a", encoding="utf-8") as stream:
            stream.write("\nimportant manual history\n")
        before = (run / "LOG.md").read_bytes()
        self.cli("repair", "--run", run, ok=False)
        self.assertEqual(before, (run / "LOG.md").read_bytes())

    def test_stale_revision_and_concurrent_writer_are_refused(self):
        run = self.init_run()
        old = self.state(run)
        self.cli("checkpoint", "--run", run, "--summary", "newer writer")
        append_event(old, "- stale writer")
        with self.assertRaises(SystemExit):
            storage.save_run(run, old, old["revision"] - 1)
        with storage.run_lock(run):
            self.cli("checkpoint", "--run", run, "--summary", "second writer", ok=False)
