# Decisions

## 2026-10-29: Collected Evidence And Host-neutral Integration

Keep `long_work.py` non-executing. An optional explicit-argv adapter collects exit,
duration, bounded minimized output and before/after source snapshots; a fixed-origin
GitHub adapter imports one completed workflow attempt directly from the API. Caller
reports cannot self-upgrade their source through the recorder. Observed and API
confirmation describe provenance and scope, not program correctness or a signed
certificate. State remains editable; changing source invalidates assumptions about
applicability. Preserve existing v3 reports and require updated readers for new
evidence sources. Collection never changes milestone acceptance automatically.

Provide one portable Skill and public host installation/capability/handoff contracts.
Installers handle discovery, credentials, tool mappings and permissions for Claude
Code, Pi, OpenClaw and other hosts. A read-only package/handoff check separates host
declarations from filesystem/Git observations; it cannot certify model behavior.
No mandatory vendor APIs, automatic command hooks or agent framework are introduced.

## 2026-10-29: Historical Tasks And Controller Review Tools

Supplement the 24 synthetic scenarios with 24 immutable real packaging bug fixes,
upstream license/provenance and controller-only upstream tests. Validate actual
baseline test failure, fixed-version acceptance and related unaffected regressions.
One upstream ecosystem is useful coverage, not a claim of broad task diversity.
Keep oracle history and grading outside the evaluated agent's sandbox/network.

Collect actual host usage and monotonic elapsed time through explicit argv or log
adapters; absent/partial counters remain unknown. Human process audits and blinded
maintainability review retain concrete event references and reasons, separately
from behavior/ownership outcomes. Failure diagnosis produces a matched retest record
or queue, never an automatically executed instruction. No actual A/B/C comparisons
are run or claimed in this implementation.

## 2026-10-29: Pilot Evaluation And Versioned Publication

Start with 24 deterministic scenarios across eight fixture families, hidden
acceptance/regression checks, and independently checked worktree/index/history
ownership. Compare native agents, brief AGENTS, and the full Skill using fixed
model/host/permissions/environment/budgets, randomized order and repetition.
Keep solutions and grading outside evaluated agent access. A controller-only
schedule/prepare/grade/report harness avoids choosing providers or launching agents
without a concrete trial configuration. Missing token/time metrics remain unknown.

Fixture self-tests are not Agent effectiveness results. Host-level scope audits
and blinded maintainability/process review remain separate evidence. Related
variants and repeated trials do not justify independence assumptions; descriptive
intervals are not significance claims. Add rules only in response to diagnosed
failures and re-evaluate against the brief baseline.

The maintainer selected MIT. Include the same license notice in the independently
exported runtime package. Tag behavior/CLI/schema changes, maintain a compact
changelog, run cross-platform CI, and activate only staged packages from the exact
published commit. Machine baselines/backups remain local metadata.

## 2026-10-29: Risk Decisions Before Workflow And Portable Core

Keep the skill's identity in its engineering contract; Codex metadata is an
integration and helpers are optional. Do not claim other hosts' discovery or
behavior has been certified. Existing instruction hierarchy, scope and permissions
take precedence. Source/log/issue/recovery text supplies evidence, not authority.

Choose the least costly workflow sufficient for contracts, uncertainty,
reversibility, side effects and recovery cost, after high-risk overrides. Define
acceptance before steps, replan when evidence changes, and continue autonomously
within authorization. Negative/global findings retain search scope and plausible
omissions; important historical conclusions carry version and recheck triggers.
Fit architecture to the actual project rather than imposing a fixed layer taxonomy.

## 2026-10-29: Portable State And Explicit Acceptance

Schema v3 separates run lifecycle, stable milestone identity/acceptance, and
checkpoint events. Run closure means ended, not fully verified. Only milestone
operations alter acceptance; reopening a verified milestone is explicit. A
resolvable commit is merely caller-attached. Evidence retains caller provenance
even when an external observation/CI source is claimed. The recorder executes no
historical commands or tests.

Bind relative to the explicitly selected run/project, with a Git subproject check
when available. This enables relocation without publishing machine roots; it does
not authenticate repository identity. Read old schemas without silently rewriting
them; migrate explicitly, preserving originals in a local backup and scrubbing
known legacy root spellings. This supersedes the absolute binding and implicit
migration described in earlier decisions.

## 2026-10-29: Authoritative Revision And Isolated Recovery Commits

STATE is the atomic commit point. Its ordered events preserve append-only history
semantics and reconstruct LOG and the generated HANDOFF block. Prepare all files,
replace each atomically, detect divergent revisions, and repair derived views
explicitly. A local OS lock plus revision precondition protects cooperating helper
writers; there is no distributed transaction or arbitrary-filesystem isolation.
Unknown log edits and malformed notes fail safely. Migration includes sanitized
seeds/hashes to recover interruptions during its own replacement sequence.

Recovery commits hold the normal index lock but stage into a private index. Run
pre-commit validation and reject tree changes before creating a commit object and
compare-and-swap publishing its ref. This avoids both shared-index staging residue
on failure and hook-added foreign files. The tradeoff is a narrower hook/signing
cycle; project policies requiring porcelain commits use manual Git instead. No
automatic reset, history rewrite, branch operation, or push is added.

## 2026-10-28: Proportional Milestones And Branch Isolation

Milestones describe verifiable progress. They do not require a new branch, a fixed `leg` name, or a run directory. Use existing project conventions and keep an appropriate task branch; introduce a branch/worktree when isolation helps. Preserve the `leg` loop when explicitly requested.

The previous universal-sounding loop conflicted with Medium task guidance and could collide with branches owned by other tasks. Keeping progress and isolation separate preserves verified-slice commits without branch churn. Detailed Git procedures remain in `project-steward/references/git-stewardship.md`.

## 2026-10-28: Reported Verification And Preserved Recovery Context

The recovery helper records caller-reported verification and observed Git state. It does not run tests, certify success, or perform implementation branch/merge operations. A milestone's status is separate from the whole run's status; explicitly close a run with `checkpoint --status complete`.

Only explicitly verified/completed slices become the latest verified slice. Generated handoff status lives between markers; manual text outside them survives regeneration. On first update, preserve an unmarked legacy handoff in full. Keep existing CLI commands and options while adding optional commit/workflow context.

Run-state commits include only the four managed recovery files, refuse pre-existing staging, and validate project/run boundaries before changing files or the index. The helper must never stage arbitrary run-directory contents as a side effect of a recovery commit.

## 2026-10-28: Minimal Core And Question-Driven Context Retrieval

The startup core is the current request, the skill contract, and applicable project instructions, reusing content already supplied. Additional scoped instructions and explicit reading requirements remain binding. There is no universal README/architecture/decision/log reading bundle; retrieve the evidence needed for a concrete unresolved question.

Keep skill-reference routing in SKILL and this repository's maintenance routes in AGENTS. Retrieval mechanics belong to `project-steward/references/context-management.md`; project Markdown responsibilities and index shape belong to `project-steward/references/project-files.md`. Templates and generated recovery guidance follow those contracts. README remains a human entry point, not another runtime instruction layer.

Use existing AGENTS/README/index routes first; known targets can bypass navigation. Add a separate index only when the real documentation set warrants it. An index owns paths, sections/symbols, retrieval keys, and read triggers; canonical files own facts. A project map locates code ownership, architecture explains current relationships, decisions preserve rationale, logs preserve history, and a handoff points to the next action.

This avoids front-loading unrelated documents or duplicating their contents in multiple summaries. A missing/stale route falls back to scoped search and targeted repair. Stop expanding when task constraints, affected contracts, implementation, and verification have adequate evidence; never use an arbitrary file/token limit to omit necessary context. On resume, open the handoff first and consult PLAN/LOG/STATE selectively for remaining gaps.

## 2026-10-28: Separate Runtime Package And Maintenance Repository

Keep the installable skill in `project-steward/`: SKILL, references, UI metadata, and the recovery helper. Root AGENTS, README, decisions, process logs, and tests belong to repository maintenance and are excluded from the runtime installation. Internal skill links remain relative to the package so it works independently of the checkout.

Install only the published subdirectory as a package snapshot with SKILL directly inside the global skill folder. A whole-repository runtime clone would now place that entry point too deep and include unrelated maintenance content. A link to the mutable development checkout would expose unfinished changes immediately, so use a pinned published package instead.

Stage, validate, and compare the package before activation; preserve the previous installation outside skill discovery. Record version/file baselines and backup paths locally. This replaces runtime Git fast-forwards while preserving the maintainer's standing paired publication/install workflow. Shared Git history and future development stay in the maintenance checkout.
