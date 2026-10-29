# Recovery State And CLI

Use this reference for the optional Python helper's data, failure, and compatibility
contract. It requires Python 3.10+; Git observations are optional. Automatic state
commits require Git 2.36+ and the narrower hook policy below. Existing project
instructions and authorization still govern use. Examples omit the common prefix
`python <skill-root>/scripts/long_work.py`.

## Lifecycle And IDs

- Run: one task across sessions/agents; `active`, `paused`, `blocked`, `complete`,
  `cancelled`. `complete` means ended, with outstanding acceptance still visible.
- Milestone: a concrete outcome with stable `M-001` ID; `pending`, `in_progress`,
  `verified`, `failed`, `skipped`. Names may duplicate and never establish identity.
- Checkpoint: a progress event, optionally linked through `--id`; no completion state.
  Only milestone operations change milestone acceptance. Verification never closes a run.

```text
milestone add --run RUN --name "Caller migration" --summary "Preserve API compatibility"
milestone start --run RUN --id M-001 --summary "Migrate remaining caller"
checkpoint --run RUN --id M-001 --summary "Two callers remain" --next "Inspect src/session.py"
milestone verify --run RUN --id M-001 --summary "Callers migrated" --verify "API regression passed"
run close --run RUN --reason "Delivered; production behavior remains unverified"
```

`run pause|block|activate|cancel` also require `--reason`. Closed runs reject updates
until explicit `run reopen`. Milestone actions other than `add` require an existing
ID; verified milestones reject changes until explicit `start` reopens acceptance.
The historical verification remains in the event journal. `last_verified` references
the latest currently verified milestone ID; checkpoints never change it.

Legacy `milestone --name ... --summary ... --verify ... --next ...` creates a new
reported slice; `complete` maps to `verified` and `active/paused/blocked` to
`in_progress`. Prefer explicit actions. Legacy `checkpoint --status` wraps the run
lifecycle; `complete` still requires `--verify` for compatibility, but does not
change milestone history. Default checkpoints preserve paused/blocked lifecycle.
Legacy `--milestone` is a display label; only a unique matching name can be linked.

## Portable Binding And Migration

Schema v3 stores `project.root_relative` as parent steps **from the run directory**,
`run_relative` from the project, and `repository_subpath` from the current Git root
when available. Copy/clone the whole project preserving its relative structure and
Git metadata when originally bound. Subprojects retain their monorepo association.
Absolute machine roots and remote URLs are not identities. This is a consistency
check for an explicitly selected local run, not authentication of repository trust.

v1/v2 remain readable with `status`. Updates require explicit migration:

```text
migrate --run RUN
migrate --run MOVED_RUN --project CURRENT_PROJECT_ROOT
```

The second form is required when the old project binding cannot be resolved.
Migration validates before writing, gives milestones stable IDs, recomputes the
latest verified reference exclusively from milestones, and preserves original files
in a local temporary backup outside the project. Preserve that backup somewhere
durable if needed; it can contain machine paths and must not be published. Known
legacy project/repository path spellings are replaced with `.` in generated state,
plan, log, and notes. Review free-form content for other private paths/secrets;
this is not a general redaction tool. Legacy verified entries without an actual
verification report retain their old status as history but reopen acceptance as
`in_progress`; migration never fabricates a pass. Corrupt or unknown schemas are
safely refused.

## Consistency And Repair

`STATE.json` is the authoritative structured state. Its monotonically increasing
`revision` and ordered event journal reconstruct `LOG.md` and the generated handoff
block. LOG history is append-only in meaning; the complete view is atomically
replaced. Write manual continuation notes outside the handoff markers. PLAN remains
maintainer-owned; no ordinary repair reconstructs a missing plan.

All temporary file contents are prepared and flushed before replacing STATE, then
LOG and HANDOFF. Atomic replacement protects each file; it is not a multi-file
transaction or a guarantee against every filesystem/power failure. A local OS lock
serializes helper writers and releases on process death; it is not a distributed
lock or a sandbox against arbitrary filesystem edits.

```text
doctor --run RUN
resume --run RUN
repair --run RUN
```

`doctor`/`resume` are read-only and reject stale/missing views, invalid references,
unsafe managed paths, or inconsistent project binding. `resume` reports current
HEAD/worktree discrepancies and displays next-action text without executing it,
switching branches, or changing code. Neither proves code correctness.

After a partial write, `repair` regenerates views from valid STATE and preserves
notes outside the markers. It accepts recognizable prior log revisions; unknown
manual LOG edits or damaged markers require preserving/repairing them first.
Migration carries sanitized plan/handoff seeds and original-file hashes so an
interrupted migration can also finish its derived replacements. Uncommitted temp
files from a killed writer are not state; inspect and remove only those known to
be abandoned. Never choose a state by file modification time.

`find --project . --status active` filters lifecycle; corrupted candidates warn
without hiding healthy runs. Sorting uses the recorded update time. A complete
run is not evidence that all milestones passed.

## Evidence

```text
evidence --run RUN --id M-001 --summary "API suite" --result passed --exit-code 0 --command-text "python -m unittest" --code-revision FULL_SHA --environment "python-3.13" --scope "API tests"
```

Records use `V-001` IDs and milestone IDs. Outcomes are `passed`, `failed`, `skipped`,
`unavailable`, `not_run`; supplied exit codes must agree with passed/failed.
`source` is always `reported` because this tool only records the caller's data.
`--claimed-source observed|independently_confirmed` preserves an external collector
or CI claim without attesting it. Include the artifact/CI pointer in the summary
and code/dirty-state details in scope. No recorded command is executed. Native
execution collection is deliberately not part of this recorder.

## Git Commit Boundary

`--commit FULL_OR_RESOLVABLE_SHA` resolves an existing commit and labels it
`caller_attached`; existence is not proof that it belongs to this task. A checkpoint
can report a commit in workflow context but cannot rewrite a milestone's commit.

`--commit-run-state` requires an initially empty real index, four regular managed
files inside the project/repository, and authorized ownership. It uses a private
index and holds the real index lock; runs `pre-commit` against the private index;
rejects hook changes to its prepared tree; verifies the final commit paths; creates
the commit object and publishes its full SHA with a compare-and-swap ref update.
On success it activates the prepared index so staging remains coherent with HEAD.
Other dirty code stays untouched. On failure it reports HEAD/staging and never
resets or rolls back another writer. If ref publication succeeds but index
activation fails, the lock/prepared index is preserved for manual recovery.

This uses Git plumbing: commit-message/post-commit hooks and automatic signing are
not supplied. Use explicit ordinary Git staging/commit when those policies apply.
Hooks themselves are trusted project programs, not sandboxed; their worktree or
external side effects cannot be undone by this helper. Concurrent processes that
ignore Git locks or arbitrary HEAD/filesystem changes are outside its isolation
guarantee. It never creates/merges implementation branches or pushes.
