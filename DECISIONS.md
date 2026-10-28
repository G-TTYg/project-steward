# Decisions

## 2026-10-28: Proportional Milestones And Branch Isolation

Milestones describe verifiable progress. They do not require a new branch, a fixed `leg` name, or a run directory. Use existing project conventions and keep an appropriate task branch; introduce a branch/worktree when isolation helps. Preserve the `leg` loop when explicitly requested.

The previous universal-sounding loop conflicted with Medium task guidance and could collide with branches owned by other tasks. Keeping progress and isolation separate preserves verified-slice commits without branch churn. Detailed Git procedures remain in `references/git-stewardship.md`.

## 2026-10-28: Reported Verification And Preserved Recovery Context

The recovery helper records caller-reported verification and observed Git state. It does not run tests, certify success, or perform implementation branch/merge operations. A milestone's status is separate from the whole run's status; explicitly close a run with `checkpoint --status complete`.

Only explicitly verified/completed slices become the latest verified slice. Generated handoff status lives between markers; manual text outside them survives regeneration. On first update, preserve an unmarked legacy handoff in full. Keep existing CLI commands and options while adding optional commit/workflow context.

Run-state commits include only the four managed recovery files, refuse pre-existing staging, and validate project/run boundaries before changing files or the index. The helper must never stage arbitrary run-directory contents as a side effect of a recovery commit.

## 2026-10-28: Minimal Core And Question-Driven Context Retrieval

The startup core is the current request, the skill contract, and applicable project instructions, reusing content already supplied. Additional scoped instructions and explicit reading requirements remain binding. There is no universal README/architecture/decision/log reading bundle; retrieve the evidence needed for a concrete unresolved question.

Keep skill-reference routing in SKILL and this repository's maintenance routes in AGENTS. Retrieval mechanics belong to `references/context-management.md`; project Markdown responsibilities and index shape belong to `references/project-files.md`. Templates and generated recovery guidance follow those contracts. README remains a human entry point, not another runtime instruction layer.

Use existing AGENTS/README/index routes first; known targets can bypass navigation. Add a separate index only when the real documentation set warrants it. An index owns paths, sections/symbols, retrieval keys, and read triggers; canonical files own facts. A project map locates code ownership, architecture explains current relationships, decisions preserve rationale, logs preserve history, and a handoff points to the next action.

This avoids front-loading unrelated documents or duplicating their contents in multiple summaries. A missing/stale route falls back to scoped search and targeted repair. Stop expanding when task constraints, affected contracts, implementation, and verification have adequate evidence; never use an arbitrary file/token limit to omit necessary context. On resume, open the handoff first and consult PLAN/LOG/STATE selectively for remaining gaps.
