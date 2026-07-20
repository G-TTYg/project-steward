# AGENTS.md

## Project Scope

- Project root: this `project-steward` skill repository.
- Install target: `~/.codex/skills/project-steward` or `%USERPROFILE%\.codex\skills\project-steward`.
- Public repository: `https://github.com/G-TTYg/project-steward`.

## Project Purpose

Project Steward is a Codex skill that makes agents act like maintainers of a project, not drive-by code editors. Its core job is to protect project stability, clarity, structure, Git history, durable facts, and verified handoff.

Long-running work support is included only as a continuity mechanism. It is not the identity of the skill.

## Design Contract

Keep every description and rule aligned with these pillars:

1. Bind work to the correct project root.
2. Preserve architecture, module boundaries, and project-wide structure.
3. Keep code understandable through names, structure, and necessary comments/docstrings.
4. Store facts in canonical project files.
5. Maintain production-grade Git hygiene and commit agent-owned completed work.
6. Record durable decisions and process logs in the right places.
7. Use `docs/agent-runs/` only for execution recovery and handoff state.
8. Verify work and report residual risk.

Do not let any part of the skill imply that agent-run state replaces README/AGENTS/docs, ADRs, process logs, project structure, code comments, tests, or Git commits.

## Repository Map

- `SKILL.md` - primary skill instructions and trigger-facing workflow.
- `README.md` - install, update, use, validate, and design summary for humans and agents.
- `agents/openai.yaml` - Codex UI metadata; keep it consistent with `SKILL.md`.
- `scripts/long_work.py` - deterministic helper for agent-run execution state.
- `references/project-files.md` - project-root, fact placement, project structure, and governance file rules.
- `references/stewardship-standards.md` - architecture, anti-sprawl, project structure, comment, redesign, and review standards.
- `references/git-stewardship.md` - production Git workflow, commits, rollback, PRs, and handoffs.
- `references/operating-patterns.md` - long-running work, recovery, context, and handoff patterns.
- `references/templates.md` - templates for AGENTS, plans, logs, ADRs, architecture notes, handoffs, blockers, and verification.

## Writing Rules

- Use `Project Steward` for the skill name and `project-steward` for the folder/invocation name.
- Use `project structure`, not `source layout`, when describing folder organization.
- Use `agent execution state` or `agent-run state` for `docs/agent-runs/`; do not call it canonical memory.
- Use `stable facts`, `decision facts`, `process facts`, and `agent execution state` consistently.
- Keep `SKILL.md` focused on core workflow; put detailed standards in `references/`.
- Keep reference files one level deep and directly linked from `SKILL.md`.

## Commands

- Validate skill:
  `python "%USERPROFILE%\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "%USERPROFILE%\.codex\skills\project-steward"`
- Check whitespace:
  `git diff --check`
- Check Git state:
  `git status --short --branch`

## Git Rules

- Check `git status --short --branch` before edits.
- Stage only intentional files.
- Commit verified agent-owned changes.
- Push only when requested or when updating this skill repo as part of the task.
- Do not rewrite shared history or discard user work without explicit approval.

## Verification Rules

Before delivery, run:

- `quick_validate.py` for the skill folder.
- `git diff --check`.
- A targeted script smoke test when `scripts/long_work.py` changes.

Report validation, Git commit, push state, and any residual risk.
