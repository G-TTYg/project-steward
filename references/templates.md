# Project Steward Templates

Copy and adapt these templates. Keep them short unless the project requires detail.

## `AGENTS.md` Template

```markdown
# AGENTS.md

## Project Scope

- Project root:
- Monorepo subproject, if any:

## Project Purpose

- What this project does:
- Non-goals:
- Primary users/systems:

## Required Reading Before Work

1. `README.md`
2. `docs/architecture.md` or `docs/architecture/overview.md`
3. Relevant files under `docs/`, `specs/`, or `.claude/specs/`
4. Nearby source code and tests for the area being changed
5. Recent project-local logs under `logs/` when continuing prior work

## Project Map

- `src/...` -
- `tests/...` -
- `docs/...` -

## Commands

- Install:
- Dev:
- Test:
- Lint/typecheck:
- Build:

## Architecture Rules

- Default to modern maintainable engineering: layered architecture, modularity, decoupling, explicit interfaces/contracts, and clear abstraction boundaries.
- Follow existing module boundaries; improve unclear boundaries when the change would otherwise spread across unrelated code.
- Search for similar implementations before adding new modules.
- Do not add dependencies/frameworks without a documented reason.
- Keep public APIs backward-compatible unless explicitly changing them.
- Keep domain/business logic independent from UI, framework, vendor, and infrastructure details where practical.

## Documentation Rules

- Update README/docs when commands, behavior, APIs, setup, or architecture change.
- Record significant decisions in `docs/adr/` or `DECISIONS.md`.
- Update diagrams when system boundaries or dependencies change.

## Logging Rules

- For non-trivial work, append this project's `logs/YYYY-MM-DD.md` with plan, discoveries, verification, and risks.
- Do not mix logs from other repos/projects managed by the same agent.
- Do not log secrets or sensitive personal data.

## Verification Rules

- Run the narrowest relevant test first.
- Run lint/typecheck/build when touching shared code or before handoff.
- If checks cannot run, explain why and what is unverified.

## Safety Rules

- Ask before destructive migrations, data deletion, deployments, or security posture changes.
```

## Work Plan Template

```markdown
## Plan: <task title>

Date: YYYY-MM-DD
Owner/agent:
Project root:
Subproject:

### Goal

### Context Read

- [ ] `AGENTS.md`
- [ ] `README.md`
- [ ] Relevant docs/specs
- [ ] Nearby code/tests
- [ ] Similar implementations searched

### Affected Areas

### Layering / Interfaces

- Existing layers/modules involved:
- Interfaces/contracts affected:
- New abstraction needed? Why/why not:

### Proposed Steps

1.
2.
3.

### Verification

### Docs/Logs/ADRs to Update

### Risks / Unknowns
```

## Daily Project Log Template

```markdown
# YYYY-MM-DD

## <task title>

Time:
Agent:
Project root:
Subproject:

### Intent

### Context / Discoveries

### Changes

-

### Decisions

-

### Architecture / Interface Notes

- Layers/modules affected:
- Contracts/docs updated:

### Verification

- Command/result:

### Risks / TODO

-

### Handoff Notes

-
```

## ADR Template

```markdown
# ADR YYYY-MM-DD: <decision title>

Status: Proposed | Accepted | Superseded
Date: YYYY-MM-DD

## Context

What problem or force led to this decision?

## Decision

What are we choosing?

## Alternatives Considered

1. Option A - pros/cons
2. Option B - pros/cons

## Consequences

### Positive

### Negative / Tradeoffs

### Follow-up

## References

- Related issue/spec/log:
```

## Architecture Overview Template

````markdown
# Architecture Overview

Last updated: YYYY-MM-DD

## System Purpose

## High-Level Diagram

```mermaid
flowchart LR
  User --> App["Application"]
  App --> Store[("Data Store")]
```

## Major Components

| Component | Layer | Responsibility | Public contracts/interfaces | Key files |
|---|---|---|---|---|
|  |  |  |  |  |

## Layering and Dependency Rules

- Presentation/entrypoints:
- Application/use cases:
- Domain/business logic:
- Infrastructure/adapters:
- Persistence/integration schemas:

## Data / Control Flow

## External Dependencies

## Important Invariants

## Known Risks / Tech Debt

## References

- ADRs:
- Specs:
- Runbooks:
````

## Handoff Template

```markdown
## Handoff: <task>

Project root:
Subproject:

### Current State

### What Was Done

### Files Touched

### Verification

### Open Questions

### Next Safe Step
```

## Blocker Note

```markdown
## Blocker: <short title>

Project root:
Subproject:
Impact:
Evidence:
Tried:
Safest next action:
Question for user:
```

## Verification Matrix

```markdown
| Area | Check | Result | Notes |
| --- | --- | --- | --- |
| Changed module | `<command>` | pass/fail/not run | |
| Contract/API | `<command or manual check>` | pass/fail/not run | |
| Build/lint/typecheck | `<command>` | pass/fail/not run | |
| UI/manual flow | `<steps>` | pass/fail/not run | |
```
