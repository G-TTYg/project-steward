"""Exercise the recovery CLI in disposable projects, including real Git index boundaries.

Shared disposable CLI fixtures. No test reads or mutates the user's installed skill or Git configuration.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(os.environ.get("STEWARD_TEST_SCRIPT", str(Path(__file__).resolve().parents[1] / "project-steward" / "scripts" / "long_work.py")))
sys.path.insert(0, str(SCRIPT.parent))


class RecoveryCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="steward-test-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "project"
        self.project.mkdir()
        self.env = os.environ.copy()
        self.env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})

    def cli(self, *args, ok=True):
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPT), *map(str, args)],
            capture_output=True, text=True, encoding="utf-8", env=self.env,
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def git(self, *args):
        result = subprocess.run(
            ["git", "-C", str(self.project), *args],
            capture_output=True, text=True, encoding="utf-8", env=self.env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def init_git(self):
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Steward Test")
        self.git("config", "user.email", "steward@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", str(Path(self.temp.name) / "no-hooks"))
        (self.project / "app.txt").write_text("baseline\n", encoding="utf-8")
        self.git("add", "--", "app.txt")
        self.git("commit", "-m", "baseline")

    def init_run(self, *args):
        self.cli("init", "--project", self.project, "--task", "review", *args)
        return sorted((self.project / "docs" / "agent-runs").iterdir())[-1]

    def state(self, run):
        return json.loads((run / "STATE.json").read_text(encoding="utf-8"))

    def verified(self, run):
        state = self.state(run)
        return next((m for m in state["milestones"] if m["id"] == state["last_verified"]), None)

    def milestone(self, run, name="first", *args):
        return self.cli(
            "milestone", "--run", run, "--name", name, "--summary", "slice outcome",
            "--verify", "unit tests passed", "--next", "continue", *args,
        )
