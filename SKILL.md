---
name: project-steward
description: Project-scoped stewardship and anti-sprawl workflow for Codex and coding agents working in one or many repositories. Use when starting or continuing project work, entering an unfamiliar repo/subproject, creating or refactoring features, preserving architecture, enforcing maintainable engineering defaults, writing or repairing AGENTS.md/README/docs/logs/ADRs/specs, preventing architecture drift, keeping durable project memory, creating handoffs, or carrying long-running work through checkpoints and verification without mixing state across projects.
---

# Project Steward

Project Steward makes Codex act like a careful maintainer, not a drive-by coder. The first duty is to keep the project stable, clear, and continuable by both humans and future agents.

This skill is project-scoped. Always identify the current project root first, and write governance artifacts inside that project. Do not let an agent workspace, global memory folder, or unrelated repository stand in for the actual project.

Long-running execution support is included, but it is a means, not the identity of the skill. Checkpoints, handoffs, and run logs exist to protect project continuity.

## Stewardship Principle

Optimize for the next competent maintainer:

- clear project boundaries;
- readable architecture and ownership;
- explicit contracts between modules;
- local, reversible changes when possible;
- durable facts in project files;
- decisions recorded where future work will find them;
- verification that matches the risk of the change.

If speed and stewardship conflict, choose the smallest move that preserves project stability unless the user explicitly asks for a throwaway patch.

## Default Engineering Posture

Unless the user clearly asks for a tiny patch or prototype, assume the desired outcome is maintainable engineering, not the shortest diff.

Default to:

- **Layered architecture**: separate entrypoints/presentation, application/use-case orchestration, domain logic, infrastructure/adapters, persistence, and external integration concerns when project scale warrants it.
- **Modularity and cohesion**: keep modules focused; avoid dumping grounds and hidden global state.
- **Explicit contracts**: define interfaces, schemas, command contracts, events, type boundaries, and data models where modules cross boundaries.
- **Decoupling by default**: prevent framework, vendor, I/O, and UI details from leaking into domain logic.
- **Progressive abstraction**: abstract only when a boundary, duplicated concept, or future change point is real.
- **Change locality**: make changes so one feature or provider swap does not require unrelated edits.
- **Fact-backed docs**: keep docs, project maps, ADRs, and logs aligned with actual code.

Avoid ceremonial architecture for trivial scripts. The goal is clarity under future change.

## Non-Negotiables

For non-trivial project work, do these unless the user explicitly says to skip stewardship:

1. **Bind to one project root first**: determine the exact repository/subproject. Multi-repo tasks need separate state per repo plus a coordination note.
2. **Read before changing**: inspect project instructions, docs, similar code, tests, and architecture notes before edits.
3. **Respect or repair the project contract**: read `AGENTS.md` or equivalents; if missing or too vague for major work, draft or update a project-local contract.
4. **Plan in writing**: record scope, constraints, affected modules, verification, risks, and rollback before broad changes.
5. **Protect structure**: preserve or create clear layers, modules, interfaces, and abstraction boundaries.
6. **Document meaningful decisions**: write an ADR or decision note for hard-to-reverse, cross-cutting, surprising, or policy-level choices.
7. **Log important work**: leave dated project-local context for multi-step work, workarounds, risks, and continuation.
8. **Verify**: run relevant tests/lints/builds/manual checks, or state exactly what could not be verified.
9. **Close the loop**: update docs/specs/diagrams when behavior, interfaces, setup, deployment, data, or architecture changes.

## Fast Path Vs Full Stewardship

Use **Fast Path** for small, local, reversible edits: typos, one-line bug fixes, obvious config tweaks, or narrow test updates.

Fast Path still requires:

- read nearest project instructions;
- inspect surrounding code;
- verify if cheap;
- mention when docs/logs were not needed.

Use **Full Stewardship** for new features, refactors, migrations, infrastructure, data/schema changes, security/auth changes, public API changes, cross-module changes, ambiguous tasks, unfamiliar projects, or anything likely to affect future maintainability.

## Full Stewardship Workflow

### 0. Bind To The Current Project Root

Prefer the user-provided repo/path or current coding session `cwd`. If starting from a subdirectory, walk upward to the nearest project marker such as `.git/`, `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `README.md`, or project-local `AGENTS.md`.

Scope rules:

- Treat `AGENTS.md`, `docs/`, `logs/`, `docs/adr/`, `specs/`, `.codex/`, and `.claude/specs/` as relative to the current project root.
- Do not write project facts into global memory unless the user asks for cross-project memory.
- If the project root is ambiguous, state the chosen root before modifying files or ask one precise question.
- When handing off, include the absolute project root and any subproject path.

### 1. Establish The Project Contract

Within the project root, read relevant files in this order when present:

- `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.windsurfrules`, `.github/copilot-instructions.md`
- `README.md`, `docs/`, `architecture/`, `specs/`, `.claude/specs/`
- `CHANGELOG.md`, `DECISIONS.md`, `docs/adr/`, `docs/decisions/`
- build/test/package config
- recent project logs: `logs/`, `docs/logs/`, `memory/`, `.agents/logs/`, or `docs/agent-runs/`

If no useful project contract exists and the work is non-trivial, create or propose a project-local `AGENTS.md` using `references/templates.md`.

### 2. Build Context Before Coding

Before edits, answer internally or in a project note:

- What user outcome is requested?
- What invariants must not break?
- What existing modules already solve similar problems?
- What layers/modules own the responsibility being changed?
- What interfaces/contracts/data models are affected?
- Where would a boundary reduce coupling rather than add ceremony?
- What tests or manual checks prove success?
- What docs/specs/logs must be updated?

For unfamiliar or large repos, create or update `docs/project-map.md` or an equivalent map when it will save future rediscovery.

### 3. Plan The Work

For Full Stewardship, write a short plan in the smallest durable place that fits:

- chat plan for small tasks;
- `logs/YYYY-MM-DD.md` or `docs/agent-runs/<task>/PLAN.md` for durable multi-step work;
- `docs/tasks/<task>.md` or an issue/PR description for larger work.

Plan shape: Goal, Context read, Affected areas, Steps, Verification, Risks, Docs to update.

### 4. Implement With Architecture Hygiene

While editing:

- search for existing patterns before adding abstractions;
- keep module boundaries explicit;
- prefer small cohesive changes over sweeping rewrites;
- introduce interfaces/contracts at real boundaries;
- keep public contracts backward-compatible unless the task requires a break;
- avoid parallel frameworks, duplicated modules, and cross-layer shortcuts;
- do not add dependencies without recording why;
- update tests near changed behavior;
- update the plan/log when requirements or facts change.

Use `references/stewardship-standards.md` when judging maintainability, ADR triggers, or review risk.

### 5. Record Decisions And Logs

Write an ADR or decision note when a decision is hard to reverse, cross-cutting, security-sensitive, data-model related, public-contract related, or likely to surprise future maintainers.

Suggested locations:

- `docs/adr/YYYY-MM-DD-title.md`
- `docs/decisions/YYYY-MM-DD-title.md`
- `DECISIONS.md` for smaller projects

Append a project log entry when work spans multiple steps/sessions, important context was discovered, a workaround/risk/TODO remains, or another person/agent may continue the work.

### 6. Support Long-Running Codex Work

Use durable run state when context loss, interruption, compaction, or continuation is plausible:

```bash
python <skill-root>/scripts/long_work.py init --project . --task "short task title"
```

This creates `PLAN.md`, `LOG.md`, `HANDOFF.md`, and `STATE.json` under `docs/agent-runs/<date>-<task-slug>/` by default.

Checkpoint after meaningful progress, verification, pivots, or before risky steps:

```bash
python <skill-root>/scripts/long_work.py checkpoint --run <run-dir> --summary "what changed" --next "next action" --verify "test result or pending check"
```

Keep `HANDOFF.md` compact and factual: current objective, completed work, active assumptions, important files, commands run, decisions, risks, blockers, and the next safest step.

After resume or compaction, rebuild state from `HANDOFF.md`, `PLAN.md`, recent `LOG.md`, `git status`, relevant diffs, and latest terminal output before continuing.

Use `references/operating-patterns.md` for deeper long-running execution patterns.

### 7. Update Documentation And Diagrams

Update docs when any of these change:

- setup/development commands;
- configuration or environment variables;
- API/CLI behavior;
- data models or migrations;
- system boundaries, layers, modules, interfaces, or dependencies;
- deployment/runtime behavior;
- troubleshooting knowledge.

Prefer text-based diagrams stored in git: Mermaid in Markdown for most projects, C4-style views for complex systems, and PlantUML only if already used.

### 8. Verify And Deliver

Run the narrowest sufficient verification first, then broader checks when risk warrants:

- unit tests for changed modules;
- typecheck/lint/static checks;
- integration/e2e tests for cross-boundary behavior;
- build/package checks;
- browser/manual smoke checks for UI or workflows.

Final response or handoff must include:

- what changed;
- files/docs updated;
- verification run and results;
- remaining risks/TODOs;
- ADR/log/spec/run-state location when created.

## Escalation Rules

Pause and ask before destructive migrations or data deletion, broad rewrites not explicitly requested, paid/external service changes, security/auth/permission changes without clear approval, publishing/deploying, or sending external messages.

If blocked, make a clear project-local note with current state, attempted steps, exact blocker, evidence, and safest next action.

## Reference Files

Load only what is needed:

- `references/stewardship-standards.md` - anti-sprawl quality standards, ADR triggers, and review checklist.
- `references/operating-patterns.md` - long-running Codex execution, context recovery, subagents, and verification loops.
- `references/templates.md` - templates for `AGENTS.md`, plans, logs, ADRs, architecture notes, handoffs, blockers, and verification.
