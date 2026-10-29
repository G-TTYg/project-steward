# Operating Patterns

Use this reference when stewardship work becomes long-running, risky, ambiguous, or likely to survive context compaction. These patterns support project stability; they do not replace architecture and documentation discipline.

## Selective Recovery

Start a resumed run with its active `HANDOFF.md` and current Git status/relevant diffs. Reuse applicable instructions already in context and discover missing ones for the target path. Do not read every run file, old daily log, or architecture document merely because the run was interrupted.

| Missing information | Query next | Avoid |
| --- | --- | --- |
| Scope, acceptance, or intended slice? | Relevant section of this run's `PLAN.md`. | Reloading completed plans for other tasks. |
| What command failed or why was a path chosen? | This run's `LOG.md`, searched by command, error, symbol, or checkpoint. | Reading the entire chronology. |
| Precise milestone history or Git snapshot fields? | Relevant keys/entries in `STATE.json`. | Recopying the JSON into the handoff. |
| Current module contract or implementation? | Canonical project doc or code/test pointer from the handoff. | Treating historical notes as current code facts. |
| A past durable choice? | Matching DECISIONS/ADR section, only when rationale affects the next step. | Loading all decisions. |

A useful handoff carries the next action, blockers, actual verification/commit state, and direct file/section/symbol pointers or exact queries. Keep history in LOG/STATE and durable rules in their canonical owners. If evidence is missing or stale, follow [question-driven retrieval](context-management.md#retrieve-by-question) and inspect current code/tests before editing.

Recovery combines historical state with current observation. Compare HEAD and
worktree changes, affected module contracts, unresolved blockers, and the version
and scope of verification. A recorded suggestion to commit is not permission to
commit another agent's new edits. `doctor` checks the helper's files/binding and
`resume` shows discrepancies and next-action text; neither can establish that code
still satisfies the task. See [Recovery state](recovery-state.md) for repair/migration.

## Verification By Risk

Ask what is most likely to fail and whether the chosen evidence could detect it.

| Change | Relevant evidence |
| --- | --- |
| Local behavior bug | Reproduction, regression, related module checks. |
| Public API or protocol | Compatibility, static/dynamic consumers, boundary behavior. |
| Data migration | Before/after invariants, interrupted migration, recovery/rollback. |
| Concurrency | Races, stress where reproducible, fault injection. |
| Authentication/authorization | Denial paths, privilege boundaries, regression. |
| Performance | Preserved correctness and repeatable benchmark. |
| Configuration/deployment | Environment differences, startup, rollback. |

Use only applicable checks. Record passed, failed, skipped, unavailable, and not_run
separately, with version, dirty state and scope where consequential. Distinguish a
caller report, an execution observed by a collector, and independent CI/environment
confirmation. Each establishes only its own scope. The recovery recorder accepts
reports and claimed external provenance; it does not elevate them to certified facts.

## Planning Patterns

### Self-contained plan

Write a plan that a fresh coding agent could execute without remembering the chat:

- goal and acceptance criteria;
- exact project root and relevant subprojects;
- constraints from project instructions;
- facts discovered with file paths or command outputs;
- ordered milestones and slices with verification for each milestone;
- commit/checkpoint plan for each milestone;
- branch/worktree strategy when isolation is needed; an optional user-requested milestone loop includes its base and merge point;
- compression checkpoint plan for each verified slice;
- rollback path and risks;
- current open questions.
- fact placement: which stable facts, decision facts, process facts, and agent execution state must be written where.

Keep the plan live. If reality changes, edit the plan before continuing.

### Recon first, design second

Use this order for unfamiliar systems:

1. Reuse applicable instructions; identify the concrete unknown blocking the next decision.
2. Locate the relevant owner/entrypoint through an existing route or scoped filename/symbol search.
3. Inspect the affected runtime path and contracts, following dependencies when needed.
4. Query the relevant tests/configuration to establish a verification path.
5. Choose the design when those questions are answered; widen the scope if a real boundary remains unresolved.

Avoid designing from filenames alone. Prefer evidence from code, tests, docs, and runtime output.

### Vertical slices

Prefer a small end-to-end working path over a large partial rewrite. Good slices often look like:

- add a failing reproduction, then fix one path;
- introduce an adapter behind an existing interface, then move callers;
- add a feature flag or compatibility layer, then migrate consumers;
- update data model plus one read/write path, then broaden;
- make UI state visible in one flow, then harden edge cases.

Promote a slice to a milestone when it is recoverable: the outcome is clear, the touched files are known, verification has run or is explicitly pending, and the commit or no-commit decision can be recorded.

When executing an approved plan, require milestone slices. Do not treat plan steps as a flat checklist; map each step to a verified slice or label it as non-commit work such as research, reproduction, or setup.

Use the current task branch for sequential milestones unless project workflow or isolation needs call for a separate branch/worktree. An explicitly requested `leg` loop follows the optional procedure in `git-stewardship.md`.

## Context Budget Patterns

### Three ledgers

Maintain three separate ledgers:

- **Facts**: confirmed by files, commands, tests, or docs.
- **Assumptions**: plausible but not yet proven.
- **Decisions**: chosen direction plus why alternatives were rejected.

Never let assumptions silently become facts.

Place confirmed facts by type. Stable facts belong in README/AGENTS/docs, decision facts in DECISIONS/docs/adr, process facts in `logs/YYYY-MM-DD.md`, and agent execution state in `docs/agent-runs/`.

### Compression checkpoints

When recovery state is in use, update `HANDOFF.md` after each verified milestone slice and before interruption. Do not create a run directory solely to satisfy this checklist. A compression checkpoint is a compact durable handoff, not automatic conversation compaction. Include:

- active task and current slice;
- current milestone and milestone status;
- observed branch/HEAD and, when relevant, base branch, slice commit, and merge result;
- changed files;
- tests run and results;
- commit created for the verified milestone, or the reason no commit exists;
- exact next command or edit;
- known risks;
- user-facing commitments.
- durable facts that still need promotion from the run directory into README/AGENTS/docs, DECISIONS/docs/adr, or `logs/YYYY-MM-DD.md`.

After writing the compression checkpoint, use the handoff as the continuation entry and check current Git state. Open plan/log/state sections only to answer a missing question, using the Selective Recovery table. Do not reread stable context that is already available.

### Search discipline

Use [context retrieval](context-management.md#retrieve-by-question) for the question → route → scoped search → evidence loop. In run state, retain the next useful query and the canonical source pointer, not copied manuals or raw search output.

## Stewarded Execution Techniques

### Preserve a working state

Keep the repository runnable between slices when practical. If a slice must temporarily break the build, record why, keep the broken interval short, and checkpoint before and after.

Use milestones as recovery boundaries. Checkpoint when context may be lost, distinguish pending checks from verified results, and create an explicit local commit when verification and ownership are clear. Refresh existing recovery state with that outcome; merge only when the chosen branch workflow requires it.

### Reduce blast radius

Use project-native boundaries:

- interfaces or ports for external services;
- data transfer objects or schemas for module boundaries;
- feature flags or compatibility shims for migrations;
- adapters for vendor/framework details;
- tests at the narrowest stable contract.

Do not add layers just to look architectural. Add boundaries where change, risk, or coupling is real. If the boundary is architectural, document it in the project map or ADR.

### Verification ladder

Climb from cheap to expensive:

1. Static/local sanity checks.
2. Focused unit or reproduction tests.
3. Module integration tests.
4. Build/typecheck/lint.
5. End-to-end, browser, or manual smoke checks.

Stop early only when the remaining checks are irrelevant or impossible; record why.

### Recovery-first debugging

For hard failures:

1. Capture the exact failing command and error.
2. Minimize the reproduction.
3. Compare with the closest passing path.
4. Inspect recent changes and dependency/config boundaries.
5. Try the smallest reversible fix.

Write the reproduction into the run log if another agent might need it.

## Subagent Patterns

When delegation is authorized and useful, use subagents for independent passes with explicit ownership and isolated side effects. Do not infer authorization to spawn agents from this reference.

Good subagent tasks:

- "Inspect these files and identify likely regression risks."
- "Find the tests that should cover this behavior."
- "Research current docs for this API and summarize constraints."
- "Review this diff for correctness and missing verification."

Poor subagent tasks:

- vague implementation ownership without a merge plan;
- tasks requiring hidden context you have not provided;
- decisions that require user approval;
- work that can modify production or external systems.

Merge subagent output into the main agent execution state with confidence and action taken.

## Handoff Quality

A good handoff lets a human or fresh agent continue without guessing:

- exact project root;
- current objective and current slice;
- current milestone, milestone history, verification, and commit/no-commit state;
- observed Git state and any base branch, slice commit, or merge outcome relevant to the chosen workflow;
- changed files and why;
- commands run and results;
- facts, assumptions, and decisions separated;
- unresolved risks;
- next safest step.
- fact placement status: what has been promoted to stable docs, decision records, process logs, and what remains only in agent execution state.

Do not bury critical project facts in chat-only summaries.
Do not leave critical stable facts or decisions only in `docs/agent-runs/`.

## User Communication

For long work, concise updates should tell the user what changed in your understanding:

- "I found the request crosses the API and persistence layers; I am adding a small compatibility path before touching callers."
- "The targeted test now reproduces the bug; next I am fixing the parser path and then I will rerun that test."
- "The broad build fails in unrelated generated code; I recorded the exact failure and verified the changed module directly."

Avoid updates that only say you are still working.
