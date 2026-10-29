# Changelog

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
