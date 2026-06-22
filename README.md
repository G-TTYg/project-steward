# Project Steward

Project Steward is a Codex skill for long-running project work: context binding, project-scoped plans, checkpoints, resumable handoffs, architecture hygiene, and verified delivery.

This repository is the skill folder itself. Install it as `project-steward` so Codex can invoke it as `$project-steward`.

## Install For Codex

Install into the user-level Codex skills directory when you want the skill available across projects.

### Windows PowerShell

```powershell
$skillRoot = Join-Path $env:USERPROFILE ".codex\skills"
$dest = Join-Path $skillRoot "project-steward"
New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null

if (Test-Path (Join-Path $dest ".git")) {
  git -C $dest pull --ff-only
} else {
  git clone https://github.com/G-TTYg/project-steward.git $dest
}
```

### macOS Or Linux

```bash
skill_root="$HOME/.codex/skills"
dest="$skill_root/project-steward"
mkdir -p "$skill_root"

if [ -d "$dest/.git" ]; then
  git -C "$dest" pull --ff-only
else
  git clone https://github.com/G-TTYg/project-steward.git "$dest"
fi
```

If this repository is private, authenticate with GitHub first:

```bash
gh auth login
```

or make sure `git clone` has access through Git Credential Manager, SSH, or a token.

## Use

Start a new Codex session or refresh Codex if the skill is not detected immediately, then invoke:

```text
Use $project-steward to steward this project task with scoped context, checkpoints, verification, and a clean handoff.
```

Good prompts:

```text
Use $project-steward to refactor this module without losing context across a long session.
```

```text
Use $project-steward to continue this migration from the existing handoff and verify each slice.
```

## Update

```bash
git -C ~/.codex/skills/project-steward pull --ff-only
```

Windows PowerShell:

```powershell
git -C "$env:USERPROFILE\.codex\skills\project-steward" pull --ff-only
```

## Validate

When the Codex system skill creator utilities are available:

```bash
python ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ~/.codex/skills/project-steward
```

Windows PowerShell:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "$env:USERPROFILE\.codex\skills\project-steward"
```

Expected result:

```text
Skill is valid!
```

## What Agents Should Read

For installation or updates, read this README first.

For task execution, read `SKILL.md` first. Load `references/operating-patterns.md` only for deeper long-running workflow guidance, and load `references/templates.md` only when creating durable plans, logs, handoffs, blocker notes, or verification matrices.

Use `scripts/long_work.py` when a task needs durable run state:

```bash
python ~/.codex/skills/project-steward/scripts/long_work.py init --project . --task "short task title"
```

Then checkpoint meaningful progress:

```bash
python ~/.codex/skills/project-steward/scripts/long_work.py checkpoint --run <run-dir> --summary "what changed" --next "next action" --verify "test result"
```

