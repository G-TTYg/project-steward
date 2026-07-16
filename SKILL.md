---
name: project-steward
description: Project-scoped stewardship and anti-sprawl workflow for Codex and coding agents working in one or many repositories. Use when starting or continuing project work, entering an unfamiliar repo/subproject, creating or refactoring features, preserving architecture, enforcing maintainable engineering defaults, maintaining production-grade Git hygiene for multi-agent work, writing or repairing AGENTS.md/README/docs/logs/ADRs/specs, preventing architecture drift, keeping durable project memory, creating handoffs, or carrying long-running work through checkpoints and verification without mixing state across projects.
---

# Project Steward

Project Steward makes Codex act like a careful maintainer, not a drive-by coder. The first duty is to keep the project stable, clear, and continuable by both humans and future agents.

This skill is project-scoped. Always identify the current project root first, and write governance artifacts inside that project. Do not let an agent workspace, global memory folder, or unrelated repository stand in for the actual project.

Long-running execution support is included, but it is a means, not the identity of the skill. Checkpoints, handoffs, and agent-run logs exist to protect execution continuity; they are not the canonical home for durable project facts.

## Stewardship Principle

Optimize for the next competent maintainer:

- clear project boundaries;
- readable architecture and ownership;
- explicit contracts between modules;
- local, reversible changes when possible;
- durable facts in the correct project files;
- disciplined Git state that preserves collaboration, rollback, and ownership;
- local commits for completed agent-owned work so others can inspect, revert, or continue it;
- decisions recorded where future work will find them;
- verification that matches the risk of the change.
- willingness to redesign or refactor a broken area when repeated patches would make the project less stable.

If speed and stewardship conflict, choose the smallest move that preserves project stability unless the user explicitly asks for a throwaway patch.

## Canonical Fact Placement

Before writing project memory, classify the fact and put it in the canonical location:

| Fact type | Canonical location | Use for |
|---|---|---|
| Stable facts | `README.md`, `AGENTS.md`, `docs/` | Project purpose, setup, commands, architecture, module boundaries, contracts, testing, runbooks. |
| Decision facts | `DECISIONS.md`, `docs/adr/` | Why a durable choice was made, alternatives, consequences, policy-level tradeoffs. |
| Process facts | `logs/YYYY-MM-DD.md` | Work chronology, discoveries, changed/planned files, verification, risks, next steps. |
| Agent execution state | `docs/agent-runs/<date-task>/` | Current slice, checkpoints, handoff, recovery after interruption or compaction. |

Do not use `docs/agent-runs/` as the only place for stable facts, decisions, or project process history. Promote durable facts out of the run directory into the canonical files above before delivery or handoff.

## Default Engineering Posture

Unless the user clearly asks for a tiny patch or prototype, assume the desired outcome is maintainable engineering, not the shortest diff.

Default to:

- **Layered architecture**: separate entrypoints/presentation, application/use-case orchestration, domain logic, infrastructure/adapters, persistence, and external integration concerns when project scale warrants it.
- **Modularity and cohesion**: keep modules focused; avoid dumping grounds and hidden global state.
- **Explicit contracts**: define interfaces, schemas, command contracts, events, type boundaries, and data models where modules cross boundaries.
- **Decoupling by default**: prevent framework, vendor, I/O, and UI details from leaking into domain logic.
- **Progressive abstraction**: abstract only when a boundary, duplicated concept, or future change point is real.
- **Change locality**: make changes so one feature or provider swap does not require unrelated edits.
- **Fact-backed docs**: keep README, AGENTS, docs, ADRs/decisions, and process logs aligned with actual code and with their distinct responsibilities.

Avoid ceremonial architecture for trivial scripts. The goal is clarity under future change.

## Non-Negotiables

For non-trivial project work, do these unless the user explicitly says to skip stewardship:

1. **Bind to one project root first**: determine the exact repository/subproject. Multi-repo tasks need separate state per repo plus a coordination note.
2. **Read before changing**: inspect project instructions, docs, similar code, tests, and architecture notes before edits.
3. **Respect or repair the project contract**: read `AGENTS.md` or equivalents; if missing or too vague for major work, draft or update a project-local contract.
4. **Maintain Git hygiene**: check branch/status before edits, protect uncommitted user work, stage explicit paths, and keep rollback possible.
5. **Classify facts before writing**: stable facts go to README/AGENTS/docs, decisions to DECISIONS/docs/adr, process facts to `logs/YYYY-MM-DD.md`, and agent execution state to `docs/agent-runs/`.
6. **Plan in writing**: record scope, constraints, affected modules, verification, risks, and rollback before broad changes.
7. **Protect structure**: preserve or create clear layers, modules, interfaces, and abstraction boundaries.
8. **Document meaningful decisions**: write an ADR or decision note for hard-to-reverse, cross-cutting, surprising, or policy-level choices.
9. **Log important work**: leave dated project-local process context for multi-step work, workarounds, risks, and continuation.
10. **Verify**: run relevant tests/lints/builds/manual checks, or state exactly what could not be verified.
11. **Commit agent-owned completed work**: for non-trivial completed work in Git repositories, create explicit local commits for your own verified changes unless the user or project workflow says not to commit.
12. **Close the loop**: update docs/specs/diagrams when behavior, interfaces, setup, deployment, data, or architecture changes.

## Fast Path Vs Full Stewardship

Use **Fast Path** for small, local, reversible edits: typos, one-line bug fixes, obvious config tweaks, or narrow test updates.

Fast Path still requires:

- check `git status --short --branch` when inside a Git repository;
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
- Do not create `docs/logs/`, `memory/`, `.agents/logs/`, or other parallel fact stores unless the project already has that convention and `AGENTS.md` points to it.
- If the project root is ambiguous, state the chosen root before modifying files or ask one precise question.
- When handing off, include the absolute project root and any subproject path.

Read `references/project-files.md` when root selection, monorepo layout, governance file placement, or per-project memory boundaries are unclear.

### 1. Establish The Project Contract

Within the project root, read relevant files in this order when present:

- `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.windsurfrules`, `.github/copilot-instructions.md`
- `README.md`, `docs/`, `architecture/`, `specs/`, `.claude/specs/`
- `CHANGELOG.md`, `DECISIONS.md`, `docs/adr/`, `docs/decisions/`
- build/test/package config
- recent process logs: `logs/YYYY-MM-DD.md`
- recent agent execution state: `docs/agent-runs/<date-task>/HANDOFF.md` only when resuming or auditing a specific long-running agent task

If no useful project contract exists and the work is non-trivial, create or propose a project-local `AGENTS.md` using `references/templates.md`.

### 2. Establish Git Baseline

For any work in a Git repository, establish at least a lightweight baseline. For non-trivial work, record it in the plan/log/handoff:

- run `git status --short --branch` before editing;
- identify the current branch, upstream, dirty files, untracked files, and unpushed commits;
- distinguish user changes from your own changes, especially in a dirty worktree;
- do not overwrite, move, stage, stash, discard, rebase, reset, or merge user work without explicit approval;
- stage only intentional paths, not blind `git add -A`, unless the repository workflow explicitly expects it;
- create local commits at stable, verified slices for agent-owned completed work unless commits are explicitly out of scope;
- if you do not commit completed work, record why and list the remaining dirty files, ownership, verification state, and next Git action.

Read `references/git-stewardship.md` for multi-agent branch/worktree, commit, push, rollback, and PR standards.

### 3. Build Context Before Coding

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

### 4. Plan The Work

For Full Stewardship, write a short plan in the smallest durable place that fits:

- chat plan for small tasks;
- `logs/YYYY-MM-DD.md` for durable process facts in multi-step work;
- `docs/agent-runs/<task>/PLAN.md` only when the work needs recovery/checkpoints/handoff;
- `docs/tasks/<task>.md` or an issue/PR description for larger work.

Plan shape: Goal, Context read, Affected areas, Steps, Verification, Risks, Docs to update.

### 5. Implement With Architecture And Git Hygiene

While editing:

- keep Git status understandable; know which files you touched and why;
- preserve user changes and unrelated agent changes in the worktree;
- commit your own completed, verified slices with explicit staging so rollback and review do not depend on guessing;
- search for existing patterns before adding abstractions;
- keep module boundaries explicit;
- prefer small cohesive changes over sweeping rewrites;
- stop patching when evidence shows a local design is fundamentally wrong, repeatedly repaired, or too tangled to change safely;
- introduce interfaces/contracts at real boundaries;
- keep public contracts backward-compatible unless the task requires a break;
- avoid parallel frameworks, duplicated modules, and cross-layer shortcuts;
- do not add dependencies without recording why;
- update tests near changed behavior;
- update the correct project file when facts change: stable facts in README/AGENTS/docs, decisions in DECISIONS/docs/adr, process facts in `logs/YYYY-MM-DD.md`, and recovery state in `docs/agent-runs/`.

Use `references/stewardship-standards.md` when judging maintainability, ADR triggers, or review risk.

If an area has had multiple failed fixes, contradictory invariants, unclear ownership, or patch-on-patch complexity, pause implementation and write a small redesign/refactor plan. Identify the root cause, intended boundary, migration steps, verification, rollback, and docs/ADR impact before changing code broadly.

### 6. Record Decisions And Logs

Write an ADR or decision note when a decision is hard to reverse, cross-cutting, security-sensitive, data-model related, public-contract related, or likely to surprise future maintainers.

Suggested locations:

- `docs/adr/YYYY-MM-DD-title.md`
- `docs/decisions/YYYY-MM-DD-title.md`
- `DECISIONS.md` for smaller projects

Append a project log entry when work spans multiple steps/sessions, important context was discovered, a workaround/risk/TODO remains, or another person/agent may continue the work.

Use `logs/YYYY-MM-DD.md` for process facts only. If a process log reveals a stable command, architecture boundary, public contract, setup rule, or testing rule, promote that fact to `README.md`, `AGENTS.md`, or `docs/`. If it records a durable choice, promote that choice to `DECISIONS.md` or `docs/adr/`.

### 7. Support Long-Running Codex Work

Use durable run state when context loss, interruption, compaction, or continuation is plausible:

```bash
python <skill-root>/scripts/long_work.py init --project . --task "short task title"
```

This creates `PLAN.md`, `LOG.md`, `HANDOFF.md`, and `STATE.json` under `docs/agent-runs/<date>-<task-slug>/` by default.

`docs/agent-runs/` is an execution-state area, not the canonical project memory. Use it for interruption recovery, active checkpoints, and handoff. Before delivery, promote stable facts to README/AGENTS/docs, decision facts to DECISIONS/docs/adr, and process facts to `logs/YYYY-MM-DD.md`.

Checkpoint after meaningful progress, verification, pivots, or before risky steps:

```bash
python <skill-root>/scripts/long_work.py checkpoint --run <run-dir> --summary "what changed" --next "next action" --verify "test result or pending check"
```

For agent-run documentation you created yourself, the script can create an explicit local commit when requested:

```bash
python <skill-root>/scripts/long_work.py checkpoint --run <run-dir> --summary "what changed" --commit-run-state
```

This only stages files inside that run directory, refuses to run when unrelated staged changes already exist, and never pushes.

Keep `HANDOFF.md` compact and factual: current objective, completed work, active assumptions, important files, Git branch/status/commit state, commands run, decisions, risks, blockers, and the next safest step.

After resume or compaction, rebuild state from `HANDOFF.md`, `PLAN.md`, recent `LOG.md`, `git status`, relevant diffs, and latest terminal output before continuing.

Use `references/operating-patterns.md` for deeper long-running execution patterns.

### 8. Update Documentation And Diagrams

Update docs when any of these change:

- setup/development commands;
- configuration or environment variables;
- API/CLI behavior;
- data models or migrations;
- system boundaries, layers, modules, interfaces, or dependencies;
- deployment/runtime behavior;
- troubleshooting knowledge.

Prefer text-based diagrams stored in git: Mermaid in Markdown for most projects, C4-style views for complex systems, and PlantUML only if already used.

### 9. Verify And Deliver

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
- fact placement: stable facts, decisions, process facts, and agent-run state were written to the correct places or intentionally skipped;
- Git state: branch, commit(s), dirty status, unpushed work, PR/remote if relevant;
- whether agent-owned completed work was committed; if not, why it remains dirty and what exact Git action should happen next;
- remaining risks/TODOs;
- ADR/log/spec/run-state location when created.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This is small, so I can skip reading project instructions." | Small edits still inherit project conventions. Read the nearest instructions and surrounding code first. |
| "I will update AGENTS.md/docs later." | Missing project context is how future humans and agents repeat the same discovery work. Update durable docs when behavior, commands, boundaries, or conventions change. |
| "The handoff has the facts, so docs/logs are covered." | Handoffs are execution state. Stable facts, decisions, and process history belong in their canonical project files. |
| "The architecture issue is nearby, so I should fix it while I am here." | Stewardship is not drive-by renovation. Record unrelated cleanup as a follow-up unless it is required for the requested change. |
| "One more patch will be safer than refactoring." | Sometimes yes, but repeated patches around the same failure are evidence that the design may be wrong. Stop and assess root cause before adding another layer. |
| "A global note is enough." | Project facts belong in the project. Global memory cannot substitute for repo-local `AGENTS.md`, docs, logs, ADRs, or handoffs. |
| "I can clean up Git at the end." | Dirty, mixed work destroys rollback and multi-agent coordination. Keep Git understandable throughout the work. |
| "AI agents should just leave files modified." | Completed agent-owned work should usually become explicit local commits so humans and agents can inspect, revert, cherry-pick, or continue it. |
| "git add -A is faster." | Blind staging can capture user work, generated noise, secrets, or unrelated agent edits. Stage explicit paths unless the repo workflow says otherwise. |
| "The code looks right." | Verification requires evidence: tests, build output, typecheck/lint, runtime/manual checks, or a stated unverified gap. |
| "I can keep the plan in my head." | Long tasks cross context boundaries. A written plan/log/handoff is the continuity mechanism for the next maintainer. |
| "This new abstraction will help later." | Abstractions must earn their cost now by clarifying a real boundary, reducing duplication, or preventing coupling. |

## Red Flags

- Project root was never stated or inferred from weak evidence.
- Work touches multiple modules but no plan or affected-boundary note exists.
- Git status was not checked before edits in a non-trivial repository task.
- Dirty user changes are present and the agent cannot say who owns them.
- A commit mixes feature work, refactor, formatting, generated files, and docs without a clear reason.
- Completed agent-owned work is left dirty with no reason, no ownership note, and no next Git action.
- A shared branch is rebased, reset, force-pushed, or conflict-resolved without explicit approval.
- `AGENTS.md` is missing or stale during non-trivial work and nobody repairs or proposes it.
- New modules, dependencies, services, schemas, or public contracts appear without docs or an ADR/decision note.
- Logs or handoffs are written outside the project root for project-specific facts.
- `docs/agent-runs/` is the only place where stable facts, decisions, or process history were recorded.
- Stable facts are buried in `logs/`; decisions are buried in daily logs; process facts are scattered through README/AGENTS/docs.
- A feature/refactor accumulates large unverified changes.
- The same bug, edge case, or module has been patched repeatedly without a root-cause design fix.
- The code path is so tangled that a small requested change requires unrelated edits across many files.
- Cross-layer shortcuts are introduced because they are faster than using or creating a contract.
- Tests/build/lint are skipped with vague wording such as "should be fine."
- Long-running run state replaces architecture docs instead of supporting them.
- The final answer does not name verification results or residual risk.

## Verification Gate

Before final delivery, confirm:

- [ ] Current project root and subproject scope are correct.
- [ ] Relevant project instructions, docs, nearby code, and tests were read.
- [ ] Git baseline was checked and user/unrelated changes were preserved.
- [ ] Completed agent-owned work was locally committed at a verified slice, or the reason for leaving it dirty is explicit.
- [ ] Fast Path or Full Stewardship choice matches the risk.
- [ ] Affected layers/modules/contracts are understood and kept clear.
- [ ] Repeatedly patched or fundamentally flawed areas were assessed for redesign/refactor instead of receiving another blind patch.
- [ ] Required docs/logs/ADRs/handoffs were updated or intentionally skipped with a reason.
- [ ] Stable facts, decision facts, process facts, and agent execution state were placed in their canonical locations.
- [ ] Relevant verification ran, with exact commands/results, or unverified areas are explicit.
- [ ] Remaining risks, TODOs, and next safe step are recorded when work is incomplete.

## Escalation Rules

Pause and ask before destructive migrations or data deletion, broad rewrites not explicitly requested, paid/external service changes, security/auth/permission changes without clear approval, publishing/deploying, sending external messages, force-pushing, rebasing shared branches, resetting history, discarding changes, resolving conflicts that touch user-owned work, or pushing commits the user did not ask to publish.

If blocked, make a clear project-local note with current state, attempted steps, exact blocker, evidence, and safest next action.

## Reference Files

Load only what is needed:

- `references/project-files.md` - project-scoped file layout, multi-project workspace rules, and where governance artifacts belong.
- `references/git-stewardship.md` - production Git standards for multi-agent work, commits, branches, rollback, PRs, and handoffs.
- `references/stewardship-standards.md` - anti-sprawl quality standards, ADR triggers, and review checklist.
- `references/operating-patterns.md` - long-running Codex execution, context recovery, subagents, and verification loops.
- `references/templates.md` - templates for `AGENTS.md`, plans, logs, ADRs, architecture notes, handoffs, blockers, and verification.
