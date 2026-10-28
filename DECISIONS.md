# Decisions

## 2026-10-28: Proportional Milestones And Branch Isolation

Milestones describe verifiable progress. They do not require a new branch, a fixed `leg` name, or a run directory. Use existing project conventions and keep an appropriate task branch; introduce a branch/worktree when isolation helps. Preserve the `leg` loop when explicitly requested.

The previous universal-sounding loop conflicted with Medium task guidance and could collide with branches owned by other tasks. Keeping progress and isolation separate preserves verified-slice commits without branch churn. Detailed Git procedures remain in `references/git-stewardship.md`.

## 2026-10-28: Reported Verification And Preserved Recovery Context

The recovery helper records caller-reported verification and observed Git state. It does not run tests, certify success, or perform implementation branch/merge operations. A milestone's status is separate from the whole run's status; explicitly close a run with `checkpoint --status complete`.

Only explicitly verified/completed slices become the latest verified slice. Generated handoff status lives between markers; manual text outside them survives regeneration. On first update, preserve an unmarked legacy handoff in full. Keep existing CLI commands and options while adding optional commit/workflow context.

Run-state commits include only the four managed recovery files, refuse pre-existing staging, and validate project/run boundaries before changing files or the index. The helper must never stage arbitrary run-directory contents as a side effect of a recovery commit.
