# Changelog

## 0.4.0 — 2026-10-29

- Add optional explicit-argv verification collection with bounded output,
  minimization, timeout/exit/duration and before/after source fingerprints.
- Import one GitHub Actions attempt from the API with repository, workflow,
  SHA and complete-job checks; keep caller reports separate from collected sources.
  New sources require this reader; existing v3 reports remain compatible.
- Add public host installation/capability/handoff contracts and a read-only check;
  installers own host details. No cross-host model behavior is certified.
- Add 24 pinned real upstream bug tasks and hidden/oracle/regression validation,
  alongside the original 24 synthetic scenarios. Provide a manual upstream CI check.
- Add trial-bound host token/time collection, process-audit validation, opaque blind
  review bundles and matched diagnosis/retest tooling. No real A/B/C experiment or
  measured Skill efficacy claim is included.

## 0.3.1 — 2026-10-29

- Compare license text after normalizing platform newlines when checking an
  exported LF package against a Windows CRLF checkout. Exact package/Git-blob
  verification is unaffected. The runtime package is unchanged from 0.3.0.

## 0.3.0 — 2026-10-29

- Separate Run lifecycle, stable Milestone IDs/acceptance, and Checkpoint events.
  Closing a run no longer changes verified history or claims pending work passed.
- Add portable schema v3 with explicit backed-up v1/v2 migration, authoritative
  revisions/journal, per-file atomic replacement, view repair and local writer locks.
- Add read-only doctor/resume, resilient filtered discovery, structured reported
  evidence, and explicit commit relationship/provenance.
- Isolate state commits from the user's index, check pre-commit tree changes and
  concurrent HEAD, and report failure without reset. The plumbing path has a
  narrower hook/signing cycle; use normal Git where project policies require it.
- Refine risk decisions, acceptance-first planning, replanning, evidence scope and
  expiry, portable core/optional tools, and project-specific architecture choices.
- Add MIT licensing, cross-platform CI, package/export checks, and an initial
  controlled Agent evaluation corpus/protocol. This release does not claim a
  measured improvement in Agent task success.

Compatibility: legacy flat CLI forms remain wrappers. Old states are readable;
updates require explicit `migrate`. `last_verified` and `current_milestone` are
stable IDs in v3. Python 3.10+; Git 2.36+ for opt-in recovery commits.
