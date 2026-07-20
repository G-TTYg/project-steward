# Git Stewardship

Use this reference for production-grade Git hygiene in projects touched by multiple humans or agents. Git state is project state. Preserve it deliberately.

## Core Principles

- Protect work you did not create.
- Keep every change attributable, reviewable, and reversible.
- Prefer small verified commits over large mixed snapshots.
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

For non-trivial completed work in a Git repository, the default stewarded outcome is a local commit for the changes the agent owns. Do this when the user requested implementation, the work reached a stable verified slice, and the project workflow does not forbid local commits.

Do not commit when:

- the user explicitly asked not to commit;
- verification is materially incomplete and the change is not a useful checkpoint;
- ownership of modified files is unclear;
- staging would require mixing user work, unrelated agent work, secrets, local artifacts, or generated noise;
- the repository has a policy requiring review before any local commit.

If you leave completed work uncommitted, record the reason, exact dirty files, likely owner, verification state, and next Git action. Do not leave an ambiguous dirty worktree as the final project state.

Local commits are not publication. Do not push unless the user requested it or the project workflow clearly requires it.

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

Commit agent-owned work at stable, verified slices. A good commit:

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
- files not owned by this agent that must not be overwritten.

## Red Flags

- The agent cannot explain the current branch or dirty status.
- A broad `git add -A` stages unrelated work.
- A commit includes unrelated formatting churn.
- Completed agent-owned work remains dirty without a reason and next Git action.
- A worktree has untracked files with unclear purpose.
- Multiple agents edit the same files without coordination.
- A shared branch is rebased or force-pushed casually.
- Verification results are not tied to commits or handoff state.
- Recovery would require guessing which files belong to whom.
