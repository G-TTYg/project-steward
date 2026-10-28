# AGENTS.md

## Project Scope

- Project root: this `project-steward` skill repository.
- Install target: `~/.codex/skills/project-steward` or `%USERPROFILE%\.codex\skills\project-steward`.
- Public repository: `https://github.com/G-TTYg/project-steward`.

## Maintenance Checkout

- Use the user-selected development checkout as the source for future improvements, verification, commits, and GitHub pushes.
- The installed copy under the Codex skills directory is a runtime installation. Do not edit it as the development source; synchronize it deliberately from the published branch after checking its Git state.
- Keep machine-specific checkout paths and installation notes in `.git/info/maintenance.md`, outside published repository content.
- Validate the development checkout with `.` as the target. Validate an installed copy separately when intentionally updating that installation.
- Use `codex/` for new maintenance branch names.
- Standing maintainer workflow, requested on 2026-10-28: after completing and verifying improvements to this skill, publish them to `origin/main` and then fast-forward the clean local runtime installation to the same commit. Do this together for future completed improvements unless the user requests review-only work, a local draft, or a different publication target.
- This standing workflow applies only to this skill repository. Preserve local installation changes and shared history; if clean fast-forward synchronization is unavailable, inspect and report the obstacle without discarding work or force-pushing. Machine-specific paths and network preferences remain in `.git/info/maintenance.md`.

## Project Purpose

Project Steward is a Codex skill that makes agents act like maintainers of a project, not drive-by code editors. Its core job is to protect project stability, clarity, structure, Git history, durable facts, and verified handoff.

Long-running work support is included only as a continuity mechanism. It is not the identity of the skill.

## Design Contract

Keep every description and rule aligned with these pillars:

1. Bind work to the correct project root.
2. Preserve architecture, module boundaries, and project-wide structure.
3. Keep code understandable through names, structure, necessary comments/docstrings, and module/file headers where they clarify responsibility or risk.
4. Store facts in canonical project files.
5. Maintain production-grade Git hygiene and commit agent-owned completed work.
6. Record durable decisions and process logs in the right places.
7. Use `docs/agent-runs/` only for execution recovery and handoff state.
8. Verify work and report residual risk.

Do not let any part of the skill imply that agent execution state replaces README/AGENTS/docs, ADRs, process logs, project structure, code comments, tests, or Git commits.

## Context Entry

Use the current request and these applicable instructions as the maintenance core. If they are already supplied in context, do not reread them. Follow only the route needed for an unanswered task question; a known target can be inspected directly. Do not preload README, decisions, logs, all references, or the whole helper to begin every task. Discover any nested instructions governing target files before editing.

## Context Routes

| Task question | Canonical target | Query / section |
| --- | --- | --- |
| Runtime behavior or task sizing? | [SKILL.md](SKILL.md) | `Core Contract`, `Choose Proportional Stewardship`, relevant numbered workflow section |
| Context retrieval or stopping rules? | [context-management.md](references/context-management.md) | `Retrieve By Question`, `Working Context`, `Missing Or Stale Routes` |
| Markdown responsibilities or project index shape? | [project-files.md](references/project-files.md) | `Markdown Responsibilities`, `Index Contract` |
| Recovery helper behavior? | `scripts/long_work.py`, `tests/test_long_work.py` | `rg -n '^def ' scripts/long_work.py`; search the affected function or test name |
| Architecture, structure, or comment standard? | `references/stewardship-standards.md` | matching architecture/structure/comment heading |
| Git ownership, staging, branch, or publication edge case? | `references/git-stewardship.md` | matching Git workflow heading |
| Creating a needed artifact? | `references/templates.md` | `Template Index`, then only the selected skeleton |
| Resuming a run? | `references/operating-patterns.md` | `Selective Recovery` |
| Install/update? | `README.md` | matching install/update section |
| UI metadata? | `agents/openai.yaml` | the relevant interface key |
| Why was a policy chosen? | `DECISIONS.md` | matching policy heading |
| What happened in a prior task? | `logs/YYYY-MM-DD.md` | search the task/date/result; historical lookup only |

The route table points to owners; it does not duplicate their contents. Update its target or query when a path, heading, symbol, or responsibility changes.

## Writing Rules

- Use `Project Steward` for the skill name and `project-steward` for the folder/invocation name.
- Use `project structure`, not `source layout`, when describing folder organization.
- Use `agent execution state` for `docs/agent-runs/`; do not call it canonical memory.
- Use `stable facts`, `decision facts`, `process facts`, and `agent execution state` consistently.
- Keep `SKILL.md` focused on core workflow; put detailed standards in `references/`.
- Keep reference files one level deep and directly linked from `SKILL.md`.

## Commands

- Validate skill:
  `python -X utf8 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .`
- Check whitespace:
  `git diff --check`
- Run helper regressions:
  `python -X utf8 -m unittest discover -s tests -v`
- Check Git state:
  `git status --short --branch`

## Git Rules

- Check `git status --short --branch` before edits.
- Stage only intentional files.
- Commit verified agent-owned changes.
- Publish only within the user's requested scope and existing authorization; editing this skill does not itself authorize a push.
- Do not rewrite shared history or discard user work without explicit approval.

## Verification Rules

Before delivery, run:

- `quick_validate.py` for the skill folder.
- `git diff --check`.
- Helper regression tests when `scripts/long_work.py` changes.

Report validation, Git commit, push state, and any residual risk.
