# Project Steward

Project Steward is a Codex skill for maintainable project work. It makes agents bind to the right project root, preserve architecture and project structure, keep code intent visible, store facts in the right project files, maintain production-grade Git hygiene, and deliver verified changes that humans and future agents can continue.

Its identity is project stewardship. Long-running checkpoints and handoffs are support tools, not the center of the skill.

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
Use $project-steward to keep this project change stable, clear, documented, verified, and easy for the next maintainer to continue.
```

Good prompts:

```text
Use $project-steward to refactor this module while preserving architecture boundaries, docs, and tests.
```

```text
Use $project-steward to continue this migration from the existing handoff, protect project structure, and verify each slice.
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

For installation or updates, read this README first. For changes to this skill repository, read `AGENTS.md` first.

For task execution, read `SKILL.md` first. Load `references/project-files.md` when deciding project root, monorepo layout, or governance file placement. Load `references/git-stewardship.md` when coordinating branches, commits, dirty worktrees, rollback, PRs, or multi-agent Git ownership. Load `references/stewardship-standards.md` when judging architecture/anti-sprawl risk. Load `references/operating-patterns.md` only for deeper long-running workflow guidance, and load `references/templates.md` only when creating durable plans, logs, ADRs, handoffs, blocker notes, or verification matrices.

## Design Vocabulary

Use these terms consistently across the skill:

- `Project Steward` - display name.
- `project-steward` - skill folder and invocation name.
- `project structure` - whole project tree organization, not only source files.
- `stable facts` - README, AGENTS, and docs facts.
- `decision facts` - DECISIONS or ADR facts.
- `process facts` - daily project log facts.
- `agent execution state` - `docs/agent-runs/` recovery and handoff state.

Fact placement is strict:

- Stable facts -> `README.md`, `AGENTS.md`, `docs/`
- Decision facts -> `DECISIONS.md`, `docs/adr/`
- Process facts -> `logs/YYYY-MM-DD.md`
- Agent execution state -> `docs/agent-runs/<date-task>/`

Code and project-structure clarity are strict too:

- Project structure should expose layer, feature, adapter, provider, artifact-type, verification-scope, or bounded-context ownership instead of dumping files into flat catch-all folders.
- Comments/docstrings should capture non-obvious intent, invariants, external constraints, edge cases, risks, and public contracts close to the code.

## Repository Design

- `SKILL.md` is the runtime contract loaded by Codex after the skill triggers.
- `AGENTS.md` is the maintenance contract for humans and agents editing this skill repository.
- `README.md` is the install, update, usage, and design summary.
- `references/` holds detailed standards loaded only when needed.
- `scripts/long_work.py` manages agent execution state only; it does not own canonical project memory.
- `agents/openai.yaml` is UI metadata and must stay aligned with `SKILL.md`.

Use `scripts/long_work.py` when a task needs agent execution state for recovery or handoff:

```bash
python ~/.codex/skills/project-steward/scripts/long_work.py init --project . --task "short task title"
```

Then checkpoint meaningful progress:

```bash
python ~/.codex/skills/project-steward/scripts/long_work.py checkpoint --run <run-dir> --summary "what changed" --next "next action" --verify "test result"
```

When the agent execution-state files are agent-owned and ready to preserve in project history, add an explicit local commit:

```bash
python ~/.codex/skills/project-steward/scripts/long_work.py checkpoint --run <run-dir> --summary "what changed" --commit-run-state
```

`--commit-run-state` stages only that run directory, refuses to continue if unrelated staged changes already exist, and never pushes.
