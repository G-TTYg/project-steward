# Project File Responsibilities

Use existing project conventions and names first. This reference owns project-root rules, Markdown responsibilities, canonical placement, and index structure. It is a lookup contract, not a list of documents to create or read. For retrieval mechanics, use [context management](context-management.md#retrieve-by-question).

## Project Scope

Prefer the explicit user-selected repository/subproject, otherwise use the current repository root or nearest credible project marker. `.git` can be a directory or worktree file. Resolve genuine ambiguity before changes that depend on it.

Keep project docs, decisions, logs, and execution state inside that project; use monorepo/subproject conventions for scoped ownership. Keep unrelated repositories' state separate. Do not create global project memory or parallel stores such as `docs/logs/` or `memory/` when canonical equivalents already exist.

## Markdown Responsibilities

The paths below are conventional roles. Existing equivalents are valid; use one canonical owner per fact. Applicable instructions and explicit reading requirements take precedence over the default read triggers.

| File / role | Owns and updates | Read when | Keep out |
| --- | --- | --- | --- |
| Root `AGENTS.md` | Concise scope, hard working constraints, essential commands, direct context routes. | Applicable at entry; reuse it when already supplied. | Complete architecture manuals, source copies, history, exhaustive reading lists. |
| Scoped `AGENTS.md` / equivalent | Additional instructions for files in its scope. | Before edits under that scope, even if a root index omits it. | Unrelated project rules or duplicated parent instructions. |
| `README.md` | Human-facing purpose, setup, common usage, and links. | Missing project orientation, setup, or usage knowledge. | Agent execution history and an assumed mandatory preflight for every edit. |
| `docs/index.md` or existing index | Question/topic → canonical path + heading/symbol + retrieval keys. | The next source is unknown and a direct root route is insufficient. | Copies of canonical facts, a full file listing, a second architecture document. |
| `docs/project-map.md` | Responsibility/owner → source entrypoints, contracts, tests, relevant scoped docs. | Locating an unknown owner or assessing affected modules. | Full architecture explanations or every file in the tree. |
| `docs/architecture.md` / architecture area | Current boundaries, dependency directions, flows, and cross-module invariants. | A change touches those boundaries or a map alone cannot explain the contract. | Work chronology, detailed source inventory, or the history of every rejected design. |
| `specs/` / contract documentation | Intended behavior, API/schema contracts, acceptance, compatibility constraints. | The affected intended contract is needed. | Assertions that current implementation already matches without evidence. |
| `docs/testing.md` / verification guide | Supported verification commands, scopes, fixtures, prerequisites. | The right check or its prerequisites are unknown. | Historical pass/fail output for individual runs. |
| `docs/runbook.md` / operations guide | Operational procedures, diagnosis, recovery constraints. | Runtime/operational work requires those procedures. | General implementation history or authorization to deploy. |
| `DECISIONS.md` or `docs/adr/*.md` | Durable choice, rationale, alternatives, consequences, supersession. | The relevant rationale constrains the current decision. | Every small implementation step; duplicated decisions in both formats. |
| `CHANGELOG.md` when used | User-visible released changes. | Release work or a compatibility question requires it. | Internal agent progress or a requirement to add a changelog to every repo. |
| `logs/YYYY-MM-DD.md` | Project process history: discoveries, verification, risks, commit/result pointers. | A specific previous task/date/result needs reconstruction. | Canonical stable facts, full transcripts, or an always-read recent-log bundle. |
| Task document / run `PLAN.md` | Current objective, scope, acceptance, slices, verification and rollback plan. | Starting that planned work or resolving missing scope on resume. | Permanent architecture facts or copies of all inspected documents. |
| Run `HANDOFF.md` | Current continuation entry: next action, blockers, evidence/commit state, retrieval pointers. | Resuming or handing off that active run. | Complete chronology, copied manuals, or a second durable fact store. |
| Run `LOG.md` | Append-only execution events and command/result pointers for that run. | A precise chronology/error/checkpoint gap remains after the handoff. | Current-status duplication or durable facts with no canonical promotion. |

`STATE.json` is the helper's structured run state, not another mandatory human reading file. Query its relevant fields/history only when the handoff lacks the needed detail. Source comments/docstrings own code-local intent and invariants; code/config/tests remain necessary evidence for affected behavior.

AGENTS answers **how to work here**; an index answers **where to ask**; a project map answers **which code owns this**; architecture answers **how components relate**. README serves users, specs define intended contracts, decisions explain choices, logs preserve history, and handoffs identify the next step. A small project may combine roles in clearly named sections of existing files instead of creating every path above.

## Canonical Fact Placement

- **Stable facts:** README/AGENTS/docs, according to their distinct roles above.
- **Decision facts:** DECISIONS or ADRs; choose the repository's format, link rather than duplicate.
- **Process facts:** dated project logs or the existing equivalent.
- **Agent execution state:** the active run's PLAN/LOG/HANDOFF/STATE only when recovery is needed.

When a log or run discovers a durable fact, update its canonical owner and leave a short link/pointer in the process record. Do not make the owner depend on reading execution history. Do not record secrets or unrelated projects' details.

## Index Contract

Use a small route table in AGENTS or an existing README/index first. Add `docs/index.md` only when the documentation set actually needs another routing level, and make it discoverable from the existing entry. Keep frequent routes direct; avoid obligatory AGENTS → README → index → map chains.

A useful route has:

| Field | Meaning |
| --- | --- |
| Question / read trigger | The uncertainty this target resolves, in task language. |
| Canonical target | Actual path plus stable heading or code symbol when useful. |
| Query | Narrow directory/file scope and useful symbol, keyword, or example command. |
| Update trigger | Change of path, heading, responsibility, command, or contract that affects this route. |

Only index useful entrypoints and important boundaries. A route is not an instruction to open all targets. Avoid summaries that duplicate canonical content, exhaustive tree dumps, invented paths, and speculative future documents. Validate targets against the actual checkout. Optional owner tags are useful only if the project maintains real ownership data.

The task that changes a routed path/heading/ownership repairs that row. Query by current heading/symbol rather than frozen line numbers. If an index is missing/stale, use scoped search and continue with evidence; do not make a complete index a prerequisite for an unrelated edit.

Use the [context index and project-map skeletons](templates.md#template-index) only when those artifacts are needed. For whole-project source/test/config/doc structure and code-comment standards, query the corresponding section of [stewardship standards](stewardship-standards.md).

## Change Propagation

Update the canonical owner of each changed fact, then repair affected navigation. Do not touch every Markdown on every task.

| Change | Canonical update | Navigation follow-up |
| --- | --- | --- |
| A working constraint or essential command | AGENTS; detailed setup/testing procedure in its owning guide. | Repair the route if the detailed target changes. |
| Module/entrypoint ownership | Project map or existing equivalent. | Fix affected root/index routes; architecture only if boundaries also change. |
| Boundary, flow, or cross-module invariant | Architecture or the relevant contract. | Repair its section route; record a decision when rationale is durable. |
| Public behavior/API/schema | Owning spec/API docs and relevant tests. | Update index keys only when discoverability changes. |
| Durable design choice | DECISIONS/ADR. | Link from the relevant contract/map where needed. |
| Task progress or observed verification result | Project log; active run state if in use. | Handoff points at the next action/evidence without copying the history. |
| Only a typo or local implementation detail | The affected file/code-local comment. | No global documentation/index refresh unless a route actually broke. |

## Small Projects And Existing Layouts

Keep the root entry sufficient for its scale. No index, map, architecture document, ADR directory, or run-state area is mandatory merely because the skill is active. Create or repair a missing contract only when the current work exposes a real continuity need. Preserve established equivalents such as `architecture/`, `docs/decisions/`, `.claude/specs/`, or package-local documentation rather than creating parallel stores.

For multi-project work, maintain separate roots and fact owners; a coordination note may link them without becoming their shared fact store. For monorepos, root routes point to package ownership and applicable scoped instructions; open only the package context relevant to the task.
