# Stewardship Standards

Use this reference when judging maintainability, architecture drift, ADR need, or review risk.

## Quality Bar

A stewarded change should leave the project easier to continue:

- responsibilities are in the module that owns them;
- public contracts are explicit and tested;
- dependencies point inward toward stable abstractions when possible;
- data shapes, events, commands, and API behavior are documented where future readers will look;
- docs and diagrams describe the code that actually exists;
- tests cover the changed contract or explain the remaining gap;
- project-specific knowledge lives in project files, not only in chat.

## Anti-Sprawl Rules

Watch for:

- duplicate modules or parallel implementations;
- feature code hidden in utility files;
- framework or vendor details leaking into domain logic;
- global mutable state used as a shortcut;
- cross-layer imports that bypass application/domain boundaries;
- config, schema, and data model changes without docs or migration notes;
- broad rewrites when a narrow boundary fix would work;
- new dependencies without a clear reason and owner.

When sprawl appears, prefer a small boundary improvement over a sweeping cleanup unless the user asked for a refactor.

## ADR Triggers

Write an ADR or decision note for:

- new architecture layers or removal of existing layers;
- database/schema/event/API contract changes;
- authentication, authorization, privacy, or security posture changes;
- provider/vendor/framework selection;
- migration strategy or compatibility policy;
- public CLI/API behavior changes;
- long-lived feature flags or rollout mechanics;
- decisions that future maintainers may otherwise reverse by accident.

## Review Checklist

Before delivery, check:

- Project root and scope are correct.
- Existing instructions and similar code were read.
- The change belongs in the touched modules.
- Interfaces/contracts remain clear.
- Tests match the risk and behavior.
- Docs/logs/ADRs were updated or intentionally skipped.
- Handoff names remaining risks and next steps.

