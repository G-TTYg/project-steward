# Codex Operating Patterns

Use this reference when stewardship work becomes long-running, risky, ambiguous, or likely to survive context compaction. These patterns support project stability; they do not replace architecture and documentation discipline.

## Planning Patterns

### Self-contained plan

Write a plan that a fresh Codex instance could execute without remembering the chat:

- goal and acceptance criteria;
- exact project root and relevant subprojects;
- constraints from project instructions;
- facts discovered with file paths or command outputs;
- ordered slices with verification for each slice;
- rollback path and risks;
- current open questions.
- fact placement: which stable facts, decisions, process facts, and agent-run state must be written where.

Keep the plan live. If reality changes, edit the plan before continuing.

### Recon first, design second

Use this order for unfamiliar systems:

1. Read project instructions and build/test config.
2. Search for existing similar behavior.
3. Trace the runtime path from entrypoint to affected domain logic.
4. Identify tests or missing tests.
5. Only then choose the design.

Avoid designing from filenames alone. Prefer evidence from code, tests, docs, and runtime output.

### Vertical slices

Prefer a small end-to-end working path over a large partial rewrite. Good slices often look like:

- add a failing reproduction, then fix one path;
- introduce an adapter behind an existing interface, then move callers;
- add a feature flag or compatibility layer, then migrate consumers;
- update data model plus one read/write path, then broaden;
- make UI state visible in one flow, then harden edge cases.

## Context Budget Patterns

### Three ledgers

Maintain three separate ledgers:

- **Facts**: confirmed by files, commands, tests, or docs.
- **Assumptions**: plausible but not yet proven.
- **Decisions**: chosen direction plus why alternatives were rejected.

Never let assumptions silently become facts.

Place confirmed facts by type. Stable facts belong in README/AGENTS/docs, decision facts in DECISIONS/docs/adr, process facts in `logs/YYYY-MM-DD.md`, and execution recovery state in `docs/agent-runs/`.

### Compression checkpoints

Before context-heavy transitions, update `HANDOFF.md` with:

- active task and current slice;
- changed files;
- tests run and results;
- exact next command or edit;
- known risks;
- user-facing commitments.
- durable facts that still need promotion from the run directory into README/AGENTS/docs, DECISIONS/docs/adr, or `logs/YYYY-MM-DD.md`.

After compaction, read the handoff before trusting memory.

### Search discipline

Use targeted searches rather than broad rereads:

- symbols, routes, commands, config keys, error strings;
- test names and fixtures;
- API paths, database tables, event names;
- package names and build scripts.

Record search conclusions only when they change the plan.

## Stewarded Execution Techniques

### Preserve a working state

Keep the repository runnable between slices when practical. If a slice must temporarily break the build, record why, keep the broken interval short, and checkpoint before and after.

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

Use subagents for independent passes, not as a substitute for ownership.

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

Merge subagent output into the main run state with confidence and action taken.

## Handoff Quality

A good handoff lets a human or fresh agent continue without guessing:

- exact project root;
- current objective and current slice;
- changed files and why;
- commands run and results;
- facts, assumptions, and decisions separated;
- unresolved risks;
- next safest step.
- fact placement status: what has been promoted to stable docs, decisions, process logs, and what remains only in agent-run state.

Do not bury critical project facts in chat-only summaries.
Do not leave critical stable facts or decisions only in `docs/agent-runs/`.

## User Communication

For long work, concise updates should tell the user what changed in your understanding:

- "I found the request crosses the API and persistence layers; I am adding a small compatibility path before touching callers."
- "The targeted test now reproduces the bug; next I am fixing the parser path and then I will rerun that test."
- "The broad build fails in unrelated generated code; I recorded the exact failure and verified the changed module directly."

Avoid updates that only say you are still working.
