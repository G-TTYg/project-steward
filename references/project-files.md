# Project Steward File Layout

Use existing project conventions first. If absent, prefer this layout. All paths in this file are relative to the current project root, not necessarily the Codex agent workspace.

## Multi-Project Agent Rule

One Codex agent may manage many unrelated projects from one workspace. Before applying this layout, bind to the current project root.

Project root selection priority:

1. Explicit path/repo requested by the user or coding session.
2. Current working directory if it is clearly a repository root.
3. Nearest parent containing `.git/`, `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, a project `README.md`, or a project-local `AGENTS.md`.
4. Ask the user if multiple plausible roots exist.

Rules:

- Keep `AGENTS.md`, `docs/`, `logs/`, ADRs, specs, and architecture diagrams inside that project root.
- Do not mix logs from different projects in a shared agent-level `logs/` directory.
- Do not put project facts into global agent memory unless they are intentionally cross-project or the user asks to remember them globally.
- Do not create parallel fact stores such as `docs/logs/`, `memory/`, or `.agents/logs/` unless the repository already uses them and `AGENTS.md` names them.
- If a monorepo has multiple apps/packages, either follow the monorepo root governance or create subproject notes under `docs/projects/<name>/` / `packages/<name>/docs/` according to existing conventions.
- Handoffs must include `project_root` and, for monorepos, `subproject`.

## Canonical Fact Placement

Use this classification before creating or updating files:

| Fact type | Canonical location | Examples | Do not put only in |
|---|---|---|---|
| Stable facts | `README.md`, `AGENTS.md`, `docs/` | Purpose, commands, setup, architecture, project map, module ownership, APIs, data contracts, testing rules, runbooks. | `logs/`, `docs/agent-runs/`, chat. |
| Decision facts | `DECISIONS.md`, `docs/adr/` | Chosen design, rejected alternatives, dependency choices, migration strategy, security posture, public contract changes. | Daily logs, handoffs, chat. |
| Process facts | `logs/YYYY-MM-DD.md` | Work chronology, discoveries, files changed/planned, verification, risks, next steps. | README/AGENTS as narrative history, `docs/agent-runs/` only. |
| Agent execution state | `docs/agent-runs/<date-task>/` | Active plan, checkpoints, handoff, current slice, recovery notes, local machine state. | Stable docs as noisy run state. |

Promotion rule: when a run log or daily log discovers a stable fact, move that fact to README/AGENTS/docs. When it records a durable choice, move that choice to DECISIONS/docs/adr. Leave only the chronology and pointers in `logs/YYYY-MM-DD.md`.

## Core Contract

Per-project files should make the codebase navigable by facts. For non-trivial projects, `AGENTS.md`, architecture docs, and project maps should describe actual layers, modules, public contracts, and dependency rules so future agents can load the map first and then inspect only relevant implementation files.

### `AGENTS.md`

Required for agent-heavy projects. It should tell coding agents how to work in this repo/project, not every repo the agent can access.

Include:

- Project purpose and non-goals.
- Required reading order.
- Build/test/dev commands.
- Architecture boundaries, layers, modules, and dependency direction.
- Coding conventions.
- Documentation/logging requirements.
- Verification requirements.
- Safety and deployment rules.
- Where to write plans, logs, ADRs, diagrams.

### `README.md`

Human-facing overview:

- What the project does.
- Quick start.
- Common commands.
- Links to docs/architecture/runbooks.

## Documentation

Recommended:

```text
docs/
  architecture.md                 # current system overview
  project-map.md                  # directories/modules/layers, public contracts, and responsibilities
  testing.md                      # how to verify changes
  runbook.md                      # operations/troubleshooting if relevant
  adr/
    YYYY-MM-DD-title.md           # architecture decision records
  tasks/
    YYYY-MM-DD-task-name.md       # larger implementation plans when useful
  agent-runs/
    YYYY-MM-DD-task/              # optional execution state for long-running agent work
logs/
  YYYY-MM-DD.md                   # durable work log
```

Alternative names are fine if the project already uses them:

- `architecture/`
- `specs/`
- `.claude/specs/`
- `decisions/`
- `CHANGELOG.md`
- `DECISIONS.md`
- `notes/`

## Minimal Governance For Small Repos

If a repo is small, avoid bureaucracy. Use:

```text
AGENTS.md
README.md
DECISIONS.md
logs/YYYY-MM-DD.md
```

Small repos still use the same fact placement. They simply keep stable facts compact in README/AGENTS, decisions in DECISIONS.md, and process facts in one daily log instead of many docs.

## What Must Be Updated When

| Change type | Required artifact |
|---|---|
| New dev/build/test command | `README.md` and/or `AGENTS.md` |
| New module/service/boundary/interface/layer | `docs/architecture.md` or `docs/project-map.md` |
| API/CLI behavior change | API docs, README, tests |
| Data/schema migration | migration docs, ADR if strategic |
| New dependency/framework | ADR or `DECISIONS.md` entry |
| Cross-cutting refactor | plan + log + architecture update |
| Security/auth/permissions | ADR + runbook/security notes |
| Workaround or known risk | log + TODO/issue reference |

## Project Log Rules

Project logs are project-local, not agent-global. They are not chat transcripts and not stable documentation. They should preserve process facts useful to future maintainers of this specific project:

- Date/time.
- Task intent.
- Key discoveries.
- Files changed or planned.
- Decision summaries and links to `DECISIONS.md` or `docs/adr/` when durable.
- Verification results.
- Remaining risks and next steps.
- Links to stable docs, decisions, ADRs, commits, issues, or agent-runs when relevant.

Do not bury stable project facts or durable decisions only in daily logs. Promote them to the canonical stable or decision files and leave a short pointer in the log.

## Agent Run State Rules

Use `docs/agent-runs/<date-task>/` only when a task needs checkpointing, recovery after context loss, or handoff to another agent.

Agent-run files may contain temporary execution detail:

- active plan and slice;
- checkpoints;
- current assumptions and blockers;
- handoff state;
- commands run during the run;
- machine-readable `STATE.json`.

Before final delivery, promote durable facts out of `docs/agent-runs/`:

- stable facts -> `README.md`, `AGENTS.md`, or `docs/`;
- decision facts -> `DECISIONS.md` or `docs/adr/`;
- process summary -> `logs/YYYY-MM-DD.md`.

Do not log secrets. Redact credentials, tokens, personal data, and private messages.
