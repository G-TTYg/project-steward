---
name: project-steward
description: Maintain project continuity during repository changes, refactors, reviews, and handoffs. Use for question-driven context retrieval, architecture and code-intent preservation, canonical documentation, reviewable Git history, and verified progress.
---

# Project Steward

Keep the project stable, clear, structured, verified, and continuable by the next maintainer. Checkpoints and Git routines support that outcome; they do not replace implementation or expand the user's scope.

## Core Contract

- Bind work to the user-selected repository or subproject before editing. Keep state separate for unrelated projects.
- Respect user instructions, existing authorization, and project conventions. Apply only the process needed for the current risk.
- Preserve architecture, project structure, module boundaries, and explicit contracts. Prefer cohesive changes and existing patterns over new frameworks or speculative abstractions.
- Keep non-obvious intent, invariants, integration constraints, and operational risks close to code in useful comments/docstrings. Use module/file headers when responsibility or constraints need explanation; avoid boilerplate on trivial files.
- Protect user and unrelated agent work. Make completed agent-owned work reviewable and reversible with explicit local commits when appropriate.
- Put durable facts in canonical project files. Recovery state is not a substitute for documentation, decisions, process logs, tests, or commits.
- Verify observed behavior and report the evidence. Distinguish pending, failed, and passed checks.

## Choose Proportional Stewardship

Classify by risk, affected boundaries, and recovery cost. File count is a hint, not a threshold. When uncertain, start at Medium and reassess after inspection; explicit high-risk evidence takes precedence.

| Size | Typical evidence | Required work |
| --- | --- | --- |
| Small / Fast Path | Local, low-risk, reversible typo, comment, narrow bug, or isolated configuration correction. | Read relevant instructions and surrounding code; check Git state; make the edit and verify cheaply. No new log, run directory, or branch ritual unless needed. |
| Medium | Bounded behavior change within a clear responsibility, with related tests/docs or several dependent steps. | Write a brief plan; use independently verifiable slices; verify and commit completed owned work. Add a project log or recovery state only when it helps continuation. |
| Large / Full Stewardship | Cross-boundary feature/refactor, public contracts, schemas/migrations, auth/security, infrastructure/deployment, dependencies, or costly recovery. | Record affected boundaries, milestones, verification, risks, rollback, and relevant docs/decisions. Keep recoverable progress and commit each verified slice. |

A narrow read-only question or review does not authorize implementation, new governance files, or commits. An unfamiliar repository requires inspection, but its unfamiliarity alone does not make a tiny edit Large.

## 1. Bind And Inspect

Prefer the user's path or current project root. When starting below it, inspect parent project markers and applicable instructions; remember `.git` may be a file in a worktree. State the selected root if ambiguous and ask only when the choice materially affects the work.

Start with the **minimum core**: the current request, this skill, and applicable project instructions. Reuse instructions already supplied in context; do not reread them just to satisfy a checklist. Discover any additional instructions governing the target path before editing. Explicit reading requirements in those instructions still apply.

Then retrieve evidence for the task, not a standard bundle of files:

- If the target is known, inspect the relevant passage, implementation, or contract directly and identify checks appropriate to the requested action.
- If ownership is unknown, use a concise existing route in AGENTS, README, or the project index. Follow only the relevant row; an index is not a required extra hop.
- Before each lookup, name the unanswered question. Search filenames, then headings/symbols and surrounding passages in the smallest plausible scope. Expand when evidence exposes another boundary or the first scope is insufficient.
- Stop expanding when the requested answer/action has adequate evidence, including applicable constraints and affected contracts, implementation, or verification where relevant. Avoid arbitrary file/token limits, recursive link following, and bulk-reading documentation or logs.

README, architecture, specs, decisions, logs, and references are **conditional sources**, not startup prerequisites. Task size changes the depth of necessary evidence, not the number of files to preload. Missing or stale indexes fall back to scoped search; they do not require a documentation project before work can proceed.

### Skill Reference Index

This table routes questions about stewardship itself. Open the matching section only if the core instructions leave a relevant question; do not load every reference. Project-specific facts are located through that project's own routes.

| Unanswered question | Reference / section | Useful search terms |
| --- | --- | --- |
| How do I discover, narrow, or stop a context lookup? | [Context retrieval](references/context-management.md#retrieve-by-question) | `Retrieve By Question`, `Working Context`, `Missing Or Stale` |
| Which Markdown owns a fact, or where should an index live? | [Project file responsibilities](references/project-files.md#markdown-responsibilities) | `Markdown Responsibilities`, `Index Contract`, `Change Propagation` |
| Which architecture, structure, or code-comment standard applies? | [Stewardship standards](references/stewardship-standards.md) | `Default Architecture Shape`, `Code Comment Standards`, `ADR Triggers` |
| How should this Git ownership, staging, branch, or publication case work? | [Git stewardship](references/git-stewardship.md) | `Agent-Owned Commit Closure`, `Milestone Branch Loop`, `Remote Safety` |
| How do I resume a specific run or handle a long execution? | [Operating patterns](references/operating-patterns.md#selective-recovery) | `Selective Recovery`, `Compression checkpoints` |
| Which skeleton should I use for a needed document? | [Template index](references/templates.md#template-index) | exact template heading; copy only that template |

Before editing a Git repository, inspect `git status --short --branch`, current branch/upstream, relevant diffs, and existing changes. Identify ownership before touching dirty files. Do not auto-stash, stage, discard, or mix another person's work.

Repair a missing project contract when major work would otherwise lack necessary guidance; keep its core constraints and routes concise. Reuse existing names and locations. File responsibilities and index design live in the reference index above; do not copy detailed manuals into the entry point.

## 2. Plan Recoverable Progress

For Medium work, a short chat plan or project log is enough. For Large or interruption-prone work, use the existing task document or a run plan. Record goal, constraints, affected areas, ordered slices, verification, risk, rollback, and docs to update.

A milestone is a recoverable slice with a concrete outcome, clear ownership, verification evidence, a commit/no-commit decision, and a next step. Split unrelated behavior into separate slices. Research, reproduction, and setup may be checkpoints without implementation commits.

Use the repository's branch strategy. **A milestone does not require a new branch.** Keep an appropriate current task branch, or use a dedicated branch/worktree when isolation helps or the user requests it. Do not force every task through a fixed `leg` branch or delete/recreate branches after each commit. If the user explicitly requests that loop, preserve it and follow [Git stewardship](references/git-stewardship.md).

## 3. Implement Within Clear Boundaries

- Search existing solutions before adding modules or dependencies.
- Organize the whole project tree by responsibility, layer, feature, adapter, artifact type, or verification scope when those boundaries are real. Avoid catch-all dumping grounds and ceremonial empty layers.
- Keep domain rules independent of UI, vendor, framework, and I/O details where practical. Introduce interfaces at meaningful boundaries, not everywhere.
- Preserve public contracts unless the requested change includes a break; document compatibility and migration consequences.
- Update nearby comments and useful headers along with behavior. Capture intent and constraints that names, types, and structure cannot explain.
- If repeated patches expose contradictory invariants or unclear ownership, record a focused redesign plan before broadening the change. Avoid unrelated renovation.

Read [stewardship standards](references/stewardship-standards.md) for architecture, structure, code documentation, redesign, or ADR criteria.

## 4. Place Facts Correctly

Follow existing equivalent locations; do not create parallel fact stores.

| Fact type | Canonical location | Content |
| --- | --- | --- |
| Stable facts | `README.md`, `AGENTS.md`, `docs/` | Setup, commands, architecture, module ownership, contracts, verification, runbooks. |
| Decision facts | `DECISIONS.md`, `docs/adr/` | Durable choices, alternatives, consequences, policy tradeoffs. |
| Process facts | `logs/YYYY-MM-DD.md` | Multi-step chronology, discoveries, verification, risks, next steps. |
| Agent execution state | `docs/agent-runs/<date-task>/` | Active plan, checkpoints, recovery and handoff. |

Promote durable facts out of run state before delivery. Record a decision for a hard-to-reverse, cross-cutting, public-contract, or surprising choice; skip redundant ADRs for routine fixes. Update docs/specs/diagrams when behavior, setup, contracts, ownership, or architecture changes. Do not log secrets.

Use [templates](references/templates.md) only for artifacts that the task actually needs.

## 5. Verify And Close Each Slice

1. Run the narrowest checks that prove the changed contract; broaden when boundaries or risk require it. Reuse meaningful tests and add regressions for demonstrated behavioral defects. Do not add tests that merely repeat implementation or documentation wording.
2. Record actual results, including failures or unavailable checks. An unverified checkpoint is useful recovery state and must remain labeled unverified.
3. For non-trivial completed agent-owned work, explicitly stage intentional paths and create a local commit unless the user/project workflow says otherwise. Check staged content first. Do not postpone safe verified slices until the entire feature is complete.
4. If recovery state is in use, refresh it before the next slice or interruption and record the actual commit/no-commit outcome. Merge only when the chosen branch workflow requires it.

When no commit is appropriate, explain why, identify remaining dirty files and ownership, and give the next Git action. A run-state commit is separate from an implementation commit. A local commit does not authorize a push. Read [Git stewardship](references/git-stewardship.md) for staging, branches, merges, publication, rollback, and multi-agent ownership.

## Recovery Helper (Only When Needed)

Use recovery files when interruption, context loss, or handoff is plausible; do not create them just because a plan has steps.

```bash
python <skill-root>/scripts/long_work.py init --project . --task "short task title"
python <skill-root>/scripts/long_work.py checkpoint --run <run-dir> --milestone "slice name" --summary "progress" --verify "pending" --next "next action"
python <skill-root>/scripts/long_work.py milestone --run <run-dir> --name "slice name" --summary "outcome" --verify "command and observed result" --next "next action"
```

`checkpoint` records ongoing progress. `milestone` defaults to an explicitly reported verified slice; use `--status active`, `paused`, or `blocked` for unfinished work. The helper records the caller's verification report; it does not run tests or prove that a milestone passed.

`milestone` status describes that slice. Use `checkpoint --status complete --verify "observed results"` to close the whole run. Verified/complete reports require explicit evidence text. Use `--commit <hash>` to attach an existing implementation commit and `--base-branch <branch>` / `--merge-result <text>` when relevant. The helper observes Git state before writing the checkpoint but never creates or merges implementation branches.

`HANDOFF.md` has a generated status block and a persistent maintainer-notes area. Put manual continuation context outside the generated block. A compression checkpoint means a compact durable handoff, not automatic conversation compaction.

For agent-owned recovery files, `--commit-run-state` explicitly commits only `PLAN.md`, `LOG.md`, `HANDOFF.md`, and `STATE.json`. It refuses pre-existing staged changes and never pushes. Record implementation commits outside that operation.

After interruption, start with the active handoff and current Git status/diffs. Query PLAN only for missing scope/acceptance details, LOG for a specific chronology gap, and STATE for structured details the handoff does not contain. Follow the next-action file/section/symbol pointers; do not reload all recovery files or project history by default. The operating-patterns route above covers selective recovery.

## Deliver

Scale the report to the task. State the outcome, meaningful changes, verification and its limits, residual risks, and Git state (branch, commits, dirty/unpushed work, publication when relevant). Point to docs, decisions, logs, and recovery state when created; explain intentional omissions only when they affect continuation.

For a read-only review, lead with actionable findings and file/line evidence. For implementation, make clear which findings were fixed and which remain. Check project scope, ownership, verification, fact placement, and commit closure before delivery.

Do not infer authorization for publishing, deployment, destructive data changes, history rewrites, or external messages from the skill itself. Follow the user's scope and existing authorization; complete the concrete reviewable preparation before requesting any genuinely missing approval.
