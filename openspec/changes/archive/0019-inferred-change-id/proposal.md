---
version: v0.19
---

# 0019-inferred-change-id — proposal

**In one line:** `mf-build`, `mf-converge` and `mf-release` start without a `change-id` when exactly one change is
ready — the one tracked active change, on its own branch — and echo the id they took.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | the decisions (`D1`…`D4`) and the text each skill's `## Parameter` section becomes |
| [tasks.md](tasks.md) | the build: one phase |
| [specs/sdd/spec.md](specs/sdd/spec.md) | one new requirement, held by a scan |

## Why

After a cut there is one change to build, converge and release, and the operator types its id for each of them. The id
is already on disk: the change's directory and the branch the cut made. Today each of these skills halts without
it, because they were written to never infer.

## What Changes

```
  change-id given? ── yes ─▶ use it (as today)
        │ no
        ▼
  tracked active changes on this branch:  none ─▶ halt · several ─▶ halt, listing them
        │ exactly one
        ▼
  branch = v<its version>_<its slug>?  no ─▶ halt, naming both
        │ yes
        ▼
  echo "change-id: <id> (inferred …)" ─▶ proceed
```

- **Inference, strictly.** Only a tracked, active change counts. See [D1](design.md#d1).
- **A branch cross-check.** The id must agree with the branch the cut made. See [D2](design.md#d2).
- **An echo, no wait.** See [D3](design.md#d3).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `sdd`: the ADDED requirement below.

| requirement | what changes |
|---|---|
| A skill infers the one active change | new: `mf-build`, `mf-converge` and `mf-release` name the inference rule, both halts and the echo, and no longer forbid inference |

## Impact

| area | files |
|---|---|
| skills | `skills/mf-build/SKILL.md` · `skills/mf-converge/SKILL.md` · `skills/mf-release/SKILL.md` |
| tests | `tests/test_skills.py` |
| dependencies | none |
| target repos | none to change |

## Not in this change

- **`mf-cut-change`.** It creates the change, so there is nothing to infer; its own "never infer" stays.
- **The autonomous `mfa-*` line.** It takes ids from its roadmap.
- **What a skill does once it has its id.** Unchanged.
- **A confirmation step.** The skill proceeds after the echo ([D3](design.md#d3)).
