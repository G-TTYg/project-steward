"""Use real hooks and repositories to exercise commit failure and ownership."""

from pathlib import Path

from support import RecoveryCase
from steward_core.git_ops import commit_run_state


class ProtectedGitCommits(RecoveryCase):
    def hook(self, text):
        directory = Path(self.temp.name) / "hooks"
        directory.mkdir(exist_ok=True)
        path = directory / "pre-commit"
        path.write_text("#!/bin/sh\n" + text + "\n", encoding="utf-8", newline="\n")
        path.chmod(0o755)
        self.git("config", "core.hooksPath", str(directory))

    def test_failed_hook_preserves_original_index_and_head(self):
        self.init_git()
        run = self.init_run()
        head = self.git("rev-parse", "HEAD")
        self.hook("exit 1")
        with self.assertRaisesRegex(SystemExit, "No reset performed"):
            commit_run_state(self.project, run, "recovery")
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")

    def test_hook_cannot_add_unrelated_paths_to_recovery_commit(self):
        self.init_git()
        run = self.init_run()
        head = self.git("rev-parse", "HEAD")
        (self.project / "app.txt").write_text("user work\n", encoding="utf-8")
        self.hook("git add -- app.txt")
        with self.assertRaisesRegex(SystemExit, "changed staged content"):
            commit_run_state(self.project, run, "recovery")
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")
        self.assertEqual((self.project / "app.txt").read_text(encoding="utf-8"), "user work\n")

    def test_concurrent_head_update_is_detected_without_rollback(self):
        self.init_git()
        run = self.init_run()
        old = self.git("rev-parse", "HEAD")
        tree = self.git("rev-parse", "HEAD^{tree}")
        concurrent = self.git("commit-tree", tree, "-p", old, "-m", "other process")
        self.hook(f"git update-ref refs/heads/main {concurrent} {old}")
        with self.assertRaisesRegex(SystemExit, "HEAD changed"):
            commit_run_state(self.project, run, "recovery")
        self.assertEqual(self.git("rev-parse", "HEAD"), concurrent)
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")

    def test_hook_worktree_edits_are_preserved_but_prevent_stale_commit(self):
        self.init_git()
        run = self.init_run()
        head = self.git("rev-parse", "HEAD")
        relative = (run / "PLAN.md").relative_to(self.project).as_posix()
        self.hook(f"printf '\\nhook edit\\n' >> '{relative}'")
        with self.assertRaisesRegex(SystemExit, "changed managed worktree"):
            commit_run_state(self.project, run, "recovery")
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        self.assertIn("hook edit", (run / "PLAN.md").read_text(encoding="utf-8"))

    def test_unborn_repository_can_commit_only_the_four_files(self):
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Steward Test")
        self.git("config", "user.email", "steward@example.invalid")
        self.git("config", "core.hooksPath", str(Path(self.temp.name) / "no-hooks"))
        run = self.init_run()
        result = commit_run_state(self.project, run / ".." / run.name, "initialize recovery")
        self.assertRegex(result, r"^[0-9a-f]{40,64}$")
        self.assertEqual(self.git("rev-parse", "HEAD"), result)
        paths = self.git("diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()
        self.assertEqual({Path(p).name for p in paths}, {"PLAN.md", "LOG.md", "HANDOFF.md", "STATE.json"})
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")

    def test_identity_failure_does_not_leave_managed_files_staged(self):
        self.init_git()
        run = self.init_run()
        head = self.git("rev-parse", "HEAD")
        self.git("config", "user.name", "")
        self.git("config", "user.email", "")
        with self.assertRaises(SystemExit):
            commit_run_state(self.project, run, "recovery")
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")

    def test_existing_index_lock_is_preserved(self):
        self.init_git()
        run = self.init_run()
        lock = self.project / ".git" / "index.lock"
        lock.write_bytes(b"owned by another process")
        with self.assertRaises(SystemExit):
            commit_run_state(self.project, run, "recovery")
        self.assertEqual(lock.read_bytes(), b"owned by another process")
