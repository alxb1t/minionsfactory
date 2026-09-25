---
version: v0.12
---

# 0012-converge-optional — proposal

**In one line:** `mf-release` releases a change that `mf-converge` never ran on, and says so; a converge that
did run still has to be clean.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | the decisions (`D1`…`D7`) and the before → after text |
| [tasks.md](tasks.md) | the build: one phase, one commit |
| [specs/sdd/spec.md](specs/sdd/spec.md) | one new requirement, held by a test |

## Why

On a change that is only docs and spec prose, `mf-converge` goes round in cycles and halts at its cap,
unconverged. `mf-release` then cannot release the change, because it requires two clean findings files. For a
prose change, the human would rather read the prose themselves ([evidence](design.md#evidence)).

## What Changes

```
  mf-build ──┬──▶ mf-converge ──▶ findings files ──▶ mf-release   both clean → release
             │                                                    any not clean → halt
             └───────────────────── no findings files ──▶ mf-release   release, and say
                                                                        "converge: skipped"
```

- **No findings files means converge was skipped.** When neither findings file exists for the change id,
  `mf-release` passes the converge preconditions and states `converge: skipped — no findings files`. See
  [D1](design.md#d1).
- **A converge that ran still binds.** If either findings file exists, both must exist and be clean, as today.
  See [D2](design.md#d2).
- **The skip is said out loud** — in the release report and in the release commit's body. The tag and the
  CHANGELOG entry do not change. See [D4](design.md#d4).
- **Deferred work still blocks.** Precondition 5 does not change. See [D3](design.md#d3).
- **The rule moves, it does not go.** *A missing findings file is not clean* stays in `mf-converge` and in
  `docs/sdd.md`'s account of the loop; it leaves `mf-release`. See [D5](design.md#d5).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `sdd`: one ADDED requirement.

| requirement | what changes |
|---|---|
| A release may skip the check loop, and says so | new: `mf-release` names the skip line and no longer carries the missing-file rule; `mf-converge` still does |

## Impact

| area | files |
|---|---|
| skills | `skills/mf-release/SKILL.md` |
| tests | `tests/test_skills.py` |
| docs | `docs/sdd.md` |
| dependencies | none |
| target repos | none to change. A repo that never runs converge can now release |

## Not in this change

- **`mf-converge`.** It keeps its rules; it is simply no longer required.
- **The parked runner.** `orchestrator/release.py` and the `release` capability keep requiring findings.
- **`mf-build`'s hand-off line** — *"`mf-converge` runs next"* (`skills/mf-build/SKILL.md:142`). It names the
  usual next step, which is still true; the grilling did not settle rewording it.
- **The builder rules (FR-3).** That is v0.13.
