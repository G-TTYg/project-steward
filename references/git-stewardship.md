# Git Stewardship

Use this reference for production-grade Git hygiene in projects touched by multiple humans or agents. Git state is project state. Preserve it deliberately.

## Core Principles

- Protect work you did not create.
- Keep every change attributable, reviewable, and reversible.
- Prefer small verified commits over large mixed snapshots.
- Treat every verified milestone slice as the normal commit boundary for non-trivial agent-owned work.
- Isolate milestone work on a short-lived local `leg` branch and merge it back after verification when milestone branch control is in use.
- Make completed agent-owned work into explicit local commits so others can inspect, revert, cherry-pick, or continue it.
- Use Git to communicate project state, not just to save files.
- Never trade short-term convenience for lost rollback or unclear ownership.

## Start-Of-Work Baseline

For non-trivial work, run and interpret:

```bash
git status --short --branch
```

When useful, also inspect:

```bash
git log --oneline --decorate -5
git diff --stat
git diff --name-only
git branch --show-current
```

Record or mention:

- current branch and upstream;
- dirty tracked files;
- untracked files;
- unpushed commits;
- likely owner of existing changes;
- whether the worktree is safe to edit.

If the worktree is dirty, do not assume the changes are yours. Read relevant diffs before editing files that are already modified.

## Agent-Owned Commit Closure

For non-trivial completed work in a Git repository, the default stewarded outcome is a local commit for the changes the agent owns. Do this when the user requested implementation, the work reached a stable verified milestone slice, and the project workflow does not forbid local commits. Do not wait for the whole plan to finish when a smaller verified slice can be committed safely.

Do not commit when:

- the user explicitly asked not to commit;
- verification is materially incomplete and the change is not a useful checkpoint;
- ownership of modified files is unclear;
- staging would require mixing user work, unrelated agent work, secrets, local artifacts, or generated noise;
- the repository has a policy requiring review before any local commit.

If you leave completed work uncommitted, record the reason, exact dirty files, likely owner, verification state, and next Git action. Do not leave an ambiguous dirty worktree as the final project state.

Local commits are not publication. Do not push unless the user requested it or the project workflow clearly requires it.

## Milestone Commit Cadence

A milestone is a recoverable work slice with a concrete outcome, known touched areas, verification, a commit decision, and a next or rollback path. Use checkpoints for intermediate or unverified progress; use local commits for every verified milestone slice.

For each milestone:

- verify the slice before committing unless the commit is explicitly a documentation-only agent execution state checkpoint;
- write a compact checkpoint/handoff before moving to the next slice;
- stage only paths owned by the agent for that milestone;
- keep code, tests, docs, and migrations together when they prove one milestone outcome;
- avoid mixing independent milestones, unrelated refactors, formatting churn, generated noise, or user-owned work;
- record the commit hash in the handoff, run state, project log, or final response;
- if no commit is created, record the exact reason, dirty files, ownership, verification state, and next Git action.

If a milestone is too large to commit as one clear unit, split it into smaller verified slices before staging.

Do not treat `docs/agent-runs/` checkpoints as substitutes for business-code commits. A run-state commit preserves recovery files only; a milestone commit preserves the verified repository change itself.

## Milestone Branch Loop

When milestone branch control is requested or expected, keep the original branch as the base branch and use a local `leg` branch for each milestone.

Default loop:

```bash
git status --short --branch
git branch --show-current   # record base branch, for example Alpha
git switch -c leg           # create milestone branch from the base branch
# work, checkpoint, verify, and commit the milestone on leg
git switch <base-branch>
git merge --ff-only leg     # prefer fast-forward merge when the base has not moved
git branch -d leg           # only after the merge succeeds
git switch -c leg           # create the next milestone branch from updated base
```

Use `git merge --no-ff leg` only when the project explicitly wants merge commits for milestone branch boundaries. Do not force-delete or reset `leg`. If `leg` already exists, inspect it first:

```bash
git log --oneline --decorate <base-branch>..leg
git branch --merged <base-branch>
```

Reuse or delete `leg` only when it is clearly the current task's milestone branch and fully merged or otherwise safe. If ownership, merge safety, or divergence is unclear, stop and ask.

## Multi-Agent Rules

In multi-agent or multi-human work:

- Prefer one agent per branch or worktree for overlapping changes.
- If multiple agents share a branch, partition files/modules explicitly and record ownership in the plan or handoff.
- Do not edit files already modified by another agent unless the plan says so.
- Do not stage or commit another agent's work without stating it and getting approval when ownership is uncertain.
- Commit your own completed slices before handoff when safe, so another agent can revert or continue without reconstructing ownership from dirty files.
- Pull/sync intentionally. Prefer `git pull --ff-only` on shared branches to avoid surprise merge commits.
- Stop on merge conflicts unless conflict ownership and resolution are clear.
- Handoffs must include branch, base commit, HEAD commit, dirty status, unpushed commits, and open PR/issue if relevant.
- When using the `leg` loop, handoffs must also include base branch, current `leg` commit, merge status, and whether `leg` was deleted/recreated for the next milestone.

## Branch And Worktree Standards

Use the repository's existing branch strategy first. If absent:

- create a short-lived feature branch for non-trivial changes;
- keep branch names descriptive, for example `feat/auth-session-boundary` or `fix/payment-webhook-retry`;
- avoid long-lived divergent branches;
- for milestone branch control inside an already chosen working branch, use local `leg` as the short-lived milestone branch unless it conflicts with existing work;
- use separate worktrees for parallel agents touching the same repo when practical;
- never switch branches with dirty user changes unless you know they carry cleanly or the user approves.

Before changing branches:

```bash
git status --short
```

If dirty state exists, decide explicitly: keep working, commit, ask, or create a safe patch. Do not auto-stash user changes as a reflex.

## Commit Standards

Commit agent-owned work at every stable, verified milestone slice. A good commit:

- does one logical thing;
- includes code, tests, docs, and migrations that belong to that slice;
- excludes unrelated formatting, generated churn, local config, secrets, and user-owned changes;
- has a clear message explaining the behavior or project state change;
- can be reverted without destroying unrelated work.

Prefer explicit staging:

```bash
git add path/to/file path/to/test
```

Use `git add -p` or equivalent when a file contains mixed concerns. Avoid blind `git add -A` unless the repo convention explicitly expects it and you have checked the full diff.

Before committing, check what will be recorded:

```bash
git diff --cached --stat
git diff --cached --name-only
```

If unrelated staged files appear, unstage only your own mistaken staging or stop and ask when ownership is unclear.

Suggested commit message shape:

```text
<type>: <short imperative summary>

Why:
- <context if not obvious>

Verified:
- <command/result>
```

Keep the message shorter when the change is obvious; include verification for risky or non-trivial commits.

For agent execution state documentation created by Project Steward, it is acceptable to create a documentation-only checkpoint commit, for example:

```text
chore(agent-state): checkpoint <task>
```

Such commits must stage only the relevant `docs/agent-runs/<run>/` files and must never include business-code changes by accident.
Milestone run-state commits are also acceptable before interruption or after milestone updates, but they still must be limited to the run directory and are separate from business-code milestone commits.

## Generated Files, Secrets, And Large Files

Before staging:

- check for `.env`, tokens, keys, credentials, private data, and local machine paths;
- verify generated files are expected by the project;
- do not add large binaries unless the repo already manages them intentionally;
- update `.gitignore` when local artifacts are repeatedly produced and should not be tracked.

If a secret is staged or committed, stop and ask. Do not try to silently rewrite history.

## Pull, Push, And Remote Safety

Use remote operations deliberately:

- `git fetch` is safe for inspection.
- `git pull --ff-only` is preferred on shared branches.
- Avoid merge commits from accidental pulls unless the repo expects them.
- Do not push unless the user requested publication or the workflow clearly requires it.
- Never force-push, rewrite shared history, delete remote branches, or change protected branch settings without explicit approval.

Before pushing:

```bash
git status --short --branch
git log --oneline @{u}..HEAD
```

If no upstream exists, state the intended remote/branch before pushing.

## Rollback And Recovery

For shared or pushed history, prefer `git revert` over rewriting history.

Use destructive commands only with explicit approval and a confirmed target:

- `git reset --hard`
- `git clean -fd`
- branch deletion
- force push
- history rewrite

For local unpushed mistakes, make the safest reversible move first:

- inspect `git diff`;
- create a patch if needed;
- commit a repair;
- revert a specific commit;
- reset only when the user explicitly approves and the affected changes are yours.

## Pull Request / Review Standards

For PR-oriented projects, a stewarded PR should include:

- problem and solution summary;
- notable architecture/contracts/data changes;
- docs/ADR/log updates;
- verification commands and results;
- migration/rollback notes;
- risks or follow-ups;
- screenshots or traces for UI/runtime changes when relevant.

Keep PRs reviewable. If a PR mixes independent features, refactors, formatting, and generated churn, split it unless the project explicitly accepts that bundle.

## Handoff Checklist

Include Git state in any durable handoff:

- branch name;
- base commit before work;
- current HEAD;
- dirty status;
- untracked files;
- commits created;
- unpushed commits;
- remote/PR URL if relevant;
- files intentionally left modified;
- why any agent-owned completed work was not committed;
- milestone names, verification, and commit hashes or no-commit reasons;
- compression checkpoint location for the latest verified slice;
- base branch, `leg` branch commit, merge result, and next `leg` recreation state;
- files not owned by this agent that must not be overwritten.

## Red Flags

- The agent cannot explain the current branch or dirty status.
- A broad `git add -A` stages unrelated work.
- A commit includes unrelated formatting churn.
- Completed agent-owned work remains dirty without a reason and next Git action.
- A milestone is marked verified but has no local commit, no commit hash, and no no-commit reason.
- A verified slice is followed by more implementation without a checkpoint/handoff refresh.
- A plan waits until the end for one large commit even though smaller verified slices were available.
- Milestone work is committed on the base branch instead of `leg` without a recorded reason.
- `leg` is force-deleted, reset, or recreated without checking whether it contains unmerged or user-owned work.
- A worktree has untracked files with unclear purpose.
- Multiple agents edit the same files without coordination.
- A shared branch is rebased or force-pushed casually.
- Verification results are not tied to commits or handoff state.
- Recovery would require guessing which files belong to whom.
