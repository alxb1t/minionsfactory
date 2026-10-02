---
version: v0.21
---

# 0021-model-suggestion — proposal

**In one line:** after its commit, `mf-cut-change` suggests in chat a model and an effort for the build, the
check loop and the release.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | the decisions (`D1`…`D6`) and the text the skill gains |
| [tasks.md](tasks.md) | the build: the suggestion |

## Why

Each station can run on a cheaper or a stronger model, and the right one depends on the change. Today the
operator picks from memory. The cut has just read the whole scope, so it is the station that can say.

## What Changes

```
  … ──▶ Step 10 · Commit ──▶ Step 11 · Report
                               branch · commit · clean tree
                               + Suggested models     ◀── new, chat only
                               next: /mf-build
```

- **A section, `## Suggesting models`,** in `skills/mf-cut-change/SKILL.md`: the rubric and the lines to print.
  See [D1](design.md#d1), [D2](design.md#d2), [D3](design.md#d3).
- **A sentence in Step 11** that runs it. See [D1](design.md#d1).
- **A line in `## Never`:** the suggestion is written to no file. See [D1](design.md#d1).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

_None._ No requirement changes, and no scan holds the new text ([D6](design.md#d6)); the change declares
`skip_specs`.

## Impact

| area | files |
|---|---|
| skills | `skills/mf-cut-change/SKILL.md` |
| tests | none |
| dependencies | none |
| target repos | none to change; the next cut in any repo prints the suggestion |

## Not in this change

- **A suggestion per phase.** One per station, for the whole change ([D2](design.md#d2)).
- **A model named in the skill.** The rubric speaks in tiers ([D3](design.md#d3)).
- **`mf-build`, `mf-converge`, `mf-release`.** They read no suggestion and are unchanged.
- **A model for the grilling.** The cut runs after it.
- **`docs/decisions.md`.** No decision in force is added or overturned: this is how a station reports.
