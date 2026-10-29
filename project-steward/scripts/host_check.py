#!/usr/bin/env python3
"""Read-only installation/continuity checks; never launches or configures an agent."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True

from long_work import load_run
from steward_core.git_ops import observe_git


def inspect(package, project, capabilities=None, run=None):
    package, project = package.resolve(), project.resolve()
    if not project.is_dir():
        raise ValueError("selected project must exist")
    text = (package / "SKILL.md").read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\nname: project-steward\n" not in text:
        raise ValueError("package does not expose Project Steward at its root")
    digest = hashlib.sha256()
    for path in sorted(package.rglob("*")):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError("exported package must contain regular files")
        if path.is_file():
            digest.update(path.relative_to(package).as_posix().encode() + b"\0" + hashlib.sha256(path.read_bytes()).digest())
    result = {"contract": "steward-host-v1", "package_sha256": digest.hexdigest(),
              "checks": {"skill_entry": "passed", "project_directory": "passed", "python_helper": "passed"},
              "git_available": shutil.which("git") is not None, "host": "unspecified", "host_declarations": None,
              "host_behavior": "not_tested", "git_observation": observe_git(project)}
    if capabilities is not None:
        if not isinstance(capabilities, dict) or capabilities.get("contract") != "steward-host-v1" or not capabilities.get("host"):
            raise ValueError("invalid host capability declaration")
        required = {"skill_discovery", "project_binding", "instruction_precedence", "authorization", "filesystem_scope", "command_execution", "git", "telemetry"}
        if not isinstance(capabilities.get("capabilities"), dict) or set(capabilities["capabilities"]) != required:
            raise ValueError("declare every host capability, including unavailable ones")
        if any(v not in {"available", "unavailable", "manual"} for v in capabilities["capabilities"].values()):
            raise ValueError("invalid capability status")
        result.update(host=capabilities["host"], host_declarations=capabilities)
    if run:
        state, bound = load_run(run.resolve())
        if bound != project:
            raise ValueError("handoff belongs to another selected project")
        current = result["git_observation"]
        result["handoff"] = {"run_id": state["run_id"], "revision": state["revision"], "status": state["status"],
                             "head_changed": state["git"].get("head") != current.get("head"),
                             "dirty_changed": state["git"].get("dirty") != current.get("dirty"),
                             "next_suggestion": state["next"], "suggestion_trust": "historical data; never executed"}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--capabilities", type=Path)
    parser.add_argument("--run", type=Path)
    args = parser.parse_args()
    capabilities = json.loads(args.capabilities.read_text(encoding="utf-8")) if args.capabilities else None
    print(json.dumps(inspect(args.package, args.project, capabilities, args.run), indent=2))


if __name__ == "__main__":
    main()
