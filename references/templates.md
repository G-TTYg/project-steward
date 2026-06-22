# Long-Work Templates

Use these templates only when they improve recoverability. Keep them short and factual.

## Run Plan

```markdown
# Plan: <task>

Project: `<absolute project root>`
Run state: `<path>`

## Goal

- User outcome:
- Acceptance criteria:
- Non-goals:

## Context

- Instructions read:
- Existing patterns:
- Affected modules/contracts:

## Slices

1. <slice>
   - Files/modules:
   - Verification:
   - Stop condition:

## Verification

- Targeted:
- Broad:
- Manual:

## Risks

- Risk:
- Rollback:
```

## Log Entry

```markdown
## <timestamp>

- Did:
- Learned:
- Changed files:
- Verification:
- Next:
- Risk/blocker:
```

## Handoff

```markdown
# Handoff: <task>

Updated: <timestamp>
Status: active | paused | blocked | verified | complete
Project: `<absolute project root>`

## Current Objective

<one paragraph>

## Completed

- <facts only>

## Current State

- Changed files:
- Important commands:
- Important decisions:

## Next Safest Step

<exact command, file, or action>

## Verification

- Run:
- Result:
- Still needed:

## Risks Or Blockers

- <risk or none>
```

## Blocker Note

```markdown
## Blocker: <short title>

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

## Final Summary

```markdown
Changed:
- <behavior or files>

Verified:
- `<command>` - <result>

Recorded:
- <run/log/ADR/spec path>

Remaining:
- <risk, TODO, or none>
```

