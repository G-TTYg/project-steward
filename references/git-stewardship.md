# Git Stewardship

Use this reference for production-grade Git hygiene in projects touched by multiple humans or agents. Git state is project state. Preserve it deliberately.

## Core Principles

- Protect work you did not create.
- Keep every change attributable, reviewable, and reversible.
- Prefer small verified commits over large mixed snapshots.
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

## Multi-Agent Rules

In multi-agent or multi-human work:

- Prefer one agent per branch or worktree for overlapping changes.
- If multiple agents share a branch, partition files/modules explicitly and record ownership in the plan or handoff.
- Do not edit files already modified by another agent unless the plan says so.
- Do not stage or commit another agent's work without stating it and getting approval when ownership is uncertain.
- Pull/sync intentionally. Prefer `git pull --ff-only` on shared branches to avoid surprise merge commits.
- Stop on merge conflicts unless conflict ownership and resolution are clear.
- Handoffs must include branch, base commit, HEAD commit, dirty status, unpushed commits, and open PR/issue if relevant.

## Branch And Worktree Standards

Use the repository's existing branch strategy first. If absent:

- create a short-lived feature branch for non-trivial changes;
- keep branch names descriptive, for example `feat/auth-session-boundary` or `fix/payment-webhook-retry`;
- avoid long-lived divergent branches;
- use separate worktrees for parallel agents touching the same repo when practical;
- never switch branches with dirty user changes unless you know they carry cleanly or the user approves.

Before changing branches:

```bash
git status --short
```

If dirty state exists, decide explicitly: keep working, commit, ask, or create a safe patch. Do not auto-stash user changes as a reflex.

## Commit Standards

Commit at stable, verified slices. A good commit:

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

Suggested commit message shape:

```text
<type>: <short imperative summary>

Why:
- <context if not obvious>

Verified:
- <command/result>
```

Keep the message shorter when the change is obvious; include verification for risky or non-trivial commits.

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
- files not owned by this agent that must not be overwritten.

## Red Flags

- The agent cannot explain the current branch or dirty status.
- A broad `git add -A` stages unrelated work.
- A commit includes unrelated formatting churn.
- A worktree has untracked files with unclear purpose.
- Multiple agents edit the same files without coordination.
- A shared branch is rebased or force-pushed casually.
- Verification results are not tied to commits or handoff state.
- Recovery would require guessing which files belong to whom.

