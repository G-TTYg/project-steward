---
name: project-steward
description: Project-scoped stewardship and long-running Codex work system for complex coding, refactoring, research, migration, debugging, architecture hygiene, documentation, or multi-repository tasks that may span many tool calls, context compaction, subagents, or verification cycles. Use when Codex needs sustained autonomous execution, durable task state, project-scoped plans/logs/handoffs, checkpoint recovery, careful context budgeting, multi-step engineering plans, blocker handling, clean continuation across long sessions, anti-sprawl project governance, or verified delivery.
---

# Project Steward

Use this skill to make Codex behave like a durable project operator during long or risky work. The goal is not extra paperwork; the goal is to keep project facts scoped, maintain momentum, recover cleanly after context loss, and finish with evidence.

Treat stewardship as two intertwined responsibilities: preserve project quality, and keep the work itself resumable. Architecture, documentation, checkpoints, verification, and handoff should support each other instead of becoming separate rituals.

## Mode Selection

Use **Fast Track** for local, reversible changes that fit in one short edit/test loop. Keep state in chat and `update_plan`; do not create run files unless the task grows.

Use **Stewarded Run** for any task with one or more of these signals:

- the user asks Codex to keep working for a long time;
- scope is ambiguous, cross-module, multi-repo, or likely to change;
- work includes refactors, migrations, performance, security, infrastructure, data, public APIs, or UI flows;
- success requires multiple verification layers;
- context compaction, interruption, or handoff is plausible;
- subagents or external research will be useful.

## Stewarded Run Workflow

### 1. Bind scope

Identify the project root and the task boundary before editing. Read the nearest project instructions first: `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, README files, docs, test/build config, and nearby code.

For multi-repo work, track one run state per repository plus one coordination note. Never mix state from unrelated projects just because they share an agent workspace.

### 2. Create durable run state

Use the project's existing issue, spec, log, or docs convention when one exists. If there is no convention and the task is a Stewarded Run, create a run folder with:

```bash
python <skill-root>/scripts/long_work.py init --project . --task "short task title"
```

The script creates `PLAN.md`, `LOG.md`, `HANDOFF.md`, and `STATE.json` under `docs/agent-runs/<date>-<task-slug>/` by default. Use `--base <relative/path>` when the repository already has a better place for agent run records.

Keep the chat `update_plan` and durable `PLAN.md` aligned at milestone level. The chat plan is for live coordination; durable files are for recovery.

### 3. Build a working model

Before broad edits, capture enough context to answer:

- requested user outcome and acceptance criteria;
- constraints from project instructions and existing behavior;
- affected modules, owners, interfaces, data models, and external services;
- similar code paths and tests;
- verification commands and manual checks;
- rollback path or safest undo strategy;
- docs, diagrams, logs, or ADRs that must change.

Read only what is relevant to the next slice. Write findings into the run log when they would help a future continuation.

### 4. Slice for momentum

Turn the task into small, verifiable slices. Prefer vertical slices that produce a working state over large speculative rewrites.

Each slice should have:

- a concrete outcome;
- files or modules likely to change;
- a cheap verification signal;
- a stop condition;
- a next action if verification fails.

When uncertainty is high, do a probe first: inspect, spike, test, or produce a minimal failing reproduction. Do not commit to a large design before evidence exists.

### 5. Execute the loop

Repeat this loop until the task is verified, blocked, or explicitly paused:

1. Choose the next slice.
2. Read the smallest useful context.
3. Edit within existing project patterns.
4. Verify the slice with the narrowest meaningful check.
5. Record what changed, what was learned, and the next action.
6. Update the live plan and send a concise user update at natural milestones.

Before any risky step, record a checkpoint. After every meaningful test/build/review result, record the result.

```bash
python <skill-root>/scripts/long_work.py checkpoint --run <run-dir> --summary "what changed" --next "next action" --verify "test result or pending check"
```

### 6. Manage context like a resource

Keep a recoverable "compressed state" in `HANDOFF.md`:

- current objective;
- completed work;
- active assumptions;
- important files and line anchors;
- commands run and results;
- decisions made and why;
- risks, blockers, and next safest step.

Refresh `HANDOFF.md` before long tool runs, context-heavy pivots, risky migrations, user pauses, or any point where another Codex instance might need to continue.

After a resume or compaction, rebuild state from durable artifacts first: read `HANDOFF.md`, `PLAN.md`, recent `LOG.md` entries, `git status`, relevant diffs, and the latest terminal output when needed. Then continue from the next safest step.

### 7. Use subagents deliberately

Use subagents when independent work reduces risk or time: code review, test strategy, documentation scan, root-cause hypotheses, API research, or parallel repository inspection.

Give subagents raw artifacts and a narrow task. Do not leak your expected answer unless the task requires it. Merge their findings into the run log with source, confidence, and action taken.

### 8. Handle blockers without stalling

When blocked, make three passes before handing it back unless the next step is dangerous or impossible:

1. Reproduce or isolate the failure.
2. Search local project history, docs, and similar code.
3. Try one safer alternate route or reduce the scope to a smaller proof.

If still blocked, update `HANDOFF.md` with attempted steps, evidence, exact blocker, and the smallest question for the user. Ask one precise question or state the external dependency needed.

### 9. Verify and deliver

Run verification in layers:

- changed-unit tests or targeted reproductions;
- typecheck/lint/static checks;
- integration, build, package, or UI/browser checks when behavior crosses boundaries;
- manual smoke checks for workflows that automated tests do not cover.

If a check cannot run, record the exact reason and the residual risk. Do not present unverified assumptions as completed facts.

Final response or handoff should include: changed behavior, important files/docs, verification run, remaining risks, and where the run state lives.

## Codex Surface Choices

Use the smallest durable surface that fits:

- prompt/thread context for one-off constraints;
- `AGENTS.md` for repository conventions and commands;
- this skill for reusable long-work procedure;
- project `.codex/config.toml` or hooks for mechanical enforcement;
- MCP/connectors for live private data or authorized external systems;
- automations for scheduled follow-up or recurring checks;
- a plugin when the workflow needs bundled skills plus tools, MCP, hooks, or assets.

Do not hide project facts in global memory when they belong in the repository.

## References

Load only what the task needs:

- `references/operating-patterns.md` - deeper patterns for long-running engineering, context budgets, subagents, verification, and recovery.
- `references/templates.md` - compact templates for run plans, logs, handoffs, blocker notes, verification matrices, and final summaries.
