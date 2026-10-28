# Project Steward

Project Steward is a Codex skill for maintainable project work. It makes agents bind to the right project root, preserve architecture and project structure, keep code intent visible, store facts in the right project files, maintain production-grade Git hygiene, and deliver verified slices with proportional branch isolation and durable handoff checkpoints that humans and future agents can continue.

Its identity is project stewardship. Long-running checkpoints and handoffs are support tools, not the center of the skill.

This repository is the skill folder itself. Install it as `project-steward` so Codex can invoke it as `$project-steward`.

## Install For Codex

Install into the user-level Codex skills directory when you want the skill available across projects.

### Windows PowerShell

```powershell
$skillRoot = Join-Path $env:USERPROFILE ".codex\skills"
$dest = Join-Path $skillRoot "project-steward"
New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null

if (Test-Path (Join-Path $dest ".git")) {
  git -C $dest pull --ff-only
} else {
  git clone https://github.com/G-TTYg/project-steward.git $dest
}
```

### macOS Or Linux

```bash
skill_root="$HOME/.codex/skills"
dest="$skill_root/project-steward"
mkdir -p "$skill_root"

if [ -d "$dest/.git" ]; then
  git -C "$dest" pull --ff-only
else
  git clone https://github.com/G-TTYg/project-steward.git "$dest"
fi
```

If this repository is private, authenticate with GitHub first:

```bash
gh auth login
```

or make sure `git clone` has access through Git Credential Manager, SSH, or a token.

## Use

Start a new Codex session or refresh Codex if the skill is not detected immediately, then invoke:

```text
Use $project-steward to keep this project change stable, clear, documented, verified, and easy for the next maintainer to continue.
```

Good prompts:

```text
Use $project-steward to refactor this module while preserving architecture boundaries, docs, and tests.
```

```text
Use $project-steward to continue this migration from the existing handoff, protect project structure, and verify each slice.
```

## Update

```bash
git -C ~/.codex/skills/project-steward pull --ff-only
```

Windows PowerShell:

```powershell
git -C "$env:USERPROFILE\.codex\skills\project-steward" pull --ff-only
```

## Develop And Publish From A Separate Checkout

Use a dedicated project checkout for improvements and GitHub pushes. Keep the copy under `~/.codex/skills/project-steward` as the runtime installation. When a project checkout already exists, continue there.

Run these commands from the development checkout:

```bash
git status --short --branch
git fetch origin
git switch -c codex/describe-change
# Edit, validate this checkout, and commit explicit paths.
```

When publication is requested, push the reviewed maintenance branch:

```bash
git push -u origin codex/describe-change
```

Update the runtime installation separately after the desired changes reach the branch it tracks, using the Update commands above. Check that installation's Git status first and preserve any local work. Machine-specific maintenance notes belong in `.git/info/maintenance.md` and are not published.

## Validate

When the Codex system skill creator utilities are available:

```bash
python ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ~/.codex/skills/project-steward
```

Windows PowerShell:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "$env:USERPROFILE\.codex\skills\project-steward"
```

Expected result:

```text
Skill is valid!
```

When developing this skill, validate the current checkout instead of the installed copy. From the project root on Windows PowerShell:

```powershell
python -X utf8 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .
git diff --check
```

For helper changes, run the standard-library regression suite from the development checkout:

```bash
python -X utf8 -m unittest discover -s tests -v
```

The tests use disposable directories and local Git repositories; they do not change the installed skill or publish anything.

## Context And Document Ownership

The runtime entry point is [SKILL.md](SKILL.md#1-bind-and-inspect): start with the task and applicable project instructions, reuse context already supplied, and query only the evidence needed for the next decision. A known target can be inspected directly; an unknown owner is located through existing routes or scoped search. There is no required README/architecture/ADR/log reading bundle.

For maintenance of this skill package, [AGENTS.md](AGENTS.md#context-routes) supplies this repository's routes and verification commands. Installation and update questions use the corresponding sections of this README. Those are different tasks from using the skill in another project.

Each Markdown has a defined owner and read trigger in [project file responsibilities](references/project-files.md#markdown-responsibilities). [Context retrieval](references/context-management.md#retrieve-by-question) explains how to query files and stop; [the template index](references/templates.md#template-index) provides optional index and document skeletons. These links are lookup routes, not a reading list.

A project's AGENTS holds core constraints and a few direct routes. An optional `docs/index.md` routes a larger documentation set; a project map identifies implementation ownership; architecture explains current boundaries; decisions preserve rationale; logs preserve history; a handoff records only current continuation state. Link to each canonical fact instead of copying it across these files.

## Design Vocabulary

Use these terms consistently across the skill:

- `Project Steward` - display name.
- `project-steward` - skill folder and invocation name.
- `project structure` - whole project tree organization, not only source files.
- `stable facts` - README, AGENTS, and docs facts.
- `decision facts` - DECISIONS or ADR facts.
- `process facts` - daily project log facts.
- `agent execution state` - `docs/agent-runs/` recovery and handoff state.

Fact placement is strict:

- Stable facts -> `README.md`, `AGENTS.md`, `docs/`
- Decision facts -> `DECISIONS.md`, `docs/adr/`
- Process facts -> `logs/YYYY-MM-DD.md`
- Agent execution state -> `docs/agent-runs/<date-task>/`

Code and project-structure clarity are strict too:

- Project structure should expose layer, feature, adapter, provider, artifact-type, verification-scope, or bounded-context ownership instead of dumping files into flat catch-all folders.
- Comments, docstrings, and module/file headers should capture non-obvious intent, module responsibility, invariants, external constraints, edge cases, risks, and public contracts close to the code.

Task sizing is explicit:

- Small tasks use Fast Path for narrow, low-risk, easily verified changes.
- Medium tasks use milestone-lite stewardship for bounded behavior changes, related file sets, or initially ambiguous work.
- Large tasks use Full Stewardship for cross-boundary changes, public contracts, migrations, security, infrastructure, broad refactors, or other work with high recovery cost.
- If task size is unclear, default to Medium until repository evidence supports Small or Large.

## Repository Design

- `SKILL.md` is the runtime contract loaded by Codex after the skill triggers.
- `AGENTS.md` is the maintenance contract for humans and agents editing this skill repository.
- `README.md` is the install, update, usage, and design summary.
- `references/` holds detailed standards retrieved by question through the SKILL reference index. Context retrieval mechanics and project Markdown responsibilities have separate owners.
- `scripts/long_work.py` manages agent execution state only; it does not own canonical durable facts or business-code commits.
- `agents/openai.yaml` is UI metadata and must stay aligned with `SKILL.md`.

Use `scripts/long_work.py` when a task needs agent execution state for recovery or handoff:

```bash
python ~/.codex/skills/project-steward/scripts/long_work.py init --project . --task "short task title"
```

Then checkpoint meaningful progress:

```bash
python ~/.codex/skills/project-steward/scripts/long_work.py checkpoint --run <run-dir> --summary "what changed" --next "next action" --verify "test result"
```

Attach checkpoints to a milestone when the work is broad or likely to be resumed:

```bash
python ~/.codex/skills/project-steward/scripts/long_work.py checkpoint --run <run-dir> --milestone "parser compatibility" --summary "what changed" --next "next action" --verify "pending check"
```

Record a verified milestone (use `--status active`, `paused`, or `blocked` for unfinished work):

```bash
python ~/.codex/skills/project-steward/scripts/long_work.py milestone --run <run-dir> --name "parser compatibility" --summary "slice outcome" --verify "test result" --next "next milestone or handoff action"
```

For multi-step implementation, map steps to verifiable slices and commit completed agent-owned work unless the user or project workflow says otherwise. Keep the current task branch when it is appropriate; separate branches/worktrees are optional isolation tools. The fixed `leg` loop is supported only when explicitly requested. Refresh recovery state after verified slices when that state is in use.

The helper records verification supplied by the caller; it does not run tests, compact conversations, or create/merge implementation branches. Milestone status applies to a slice; close the entire run with `checkpoint --status complete --verify "observed results"`. `HANDOFF.md` keeps generated status between markers and preserves manual text outside them. Git observations are refreshed automatically before writing/committing the checkpoint; no upstream means the unpushed count is unknown. Attach an existing implementation commit with `--commit <hash>` and optional workflow context with `--base-branch <branch>` / `--merge-result <text>`.

On the first update of an older run, the helper preserves the unmarked legacy handoff in full. Do not relocate a run outside its recorded project; updates require its initialized state and four regular managed files. A new checkpoint without `--verify` reports its verification as unreported rather than inheriting an older slice's success. Use `--risk ""` to clear a resolved risk.

When the agent execution state files are agent-owned and ready to preserve in project history, add an explicit local run-state commit:

```bash
python ~/.codex/skills/project-steward/scripts/long_work.py checkpoint --run <run-dir> --summary "what changed" --commit-run-state
```

`--commit-run-state` stages only the four managed recovery files (`PLAN.md`, `LOG.md`, `HANDOFF.md`, `STATE.json`), refuses pre-existing staged changes, and never pushes. It never commits business-code paths; verified milestone code commits must use explicit Git staging outside the script.
