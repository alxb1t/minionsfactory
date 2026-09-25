---
version: v0.14
---

# 0014-backlog-cards — proposal

**In one line:** every finding becomes a **card** — a plain title and short labelled fields — that the stations
write, `mf-converge` carries into the backlog, and `mf-backlog-export` keeps whole.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | the decisions (`D1`…`D7`), the card, and the before → after text |
| [tasks.md](tasks.md) | the build: one phase, one commit |
| [specs/sdd/spec.md](specs/sdd/spec.md) | one new requirement, held by a test |

## Why

The human opened the exported backlog to decide what to fix, and could not read it. Each item is one table row,
and its *defect* cell is a paragraph: why it matters, when it bites and what it touches are folded into one run
of prose ([evidence](design.md#evidence)). Deferred work nobody can read is deferred work nobody does.

## What Changes

```
  review ─┐                     non-blocking cards                       cards, whole
          ├─▶ findings files ───────────────────▶ <version>_backlog.md ───────────▶ the human's backlog
 security ┘   every finding       mf-converge          mf-backlog-export
              is a card           carries whole        carries whole
```

- **The card** — a plain-words title, then labelled fields: why it's a problem · when you'd hit it · what it
  affects · priority · fix · trigger · still true? · related · status. See [D1](design.md#d1).
- **The stations write it.** Review and security write every finding as a card; `mf-converge` carries the
  deferred ones verbatim and judges nothing. See [D2](design.md#d2), [D3](design.md#d3).
- **The export keeps it.** `mf-backlog-export` carries each card whole instead of flattening it into table fields, and uses its
  *still true?* check to decide what is moot. See [D4](design.md#d4).
- **A card stays a list item** — one top-level item, fields as nested bullets — so `mf-release`'s deferred-work
  check keeps blocking. See [D5](design.md#d5).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `sdd`: one ADDED requirement.

| requirement | what changes |
|---|---|
| Converge and the export share one card shape | new: the field labels in `mf-converge`'s and `mf-backlog-export`'s `## The card` sections are the same set |

## Impact

| area | files |
|---|---|
| skills | `skills/mf-converge/SKILL.md` · `skills/mf-backlog-export/SKILL.md` |
| tests | `tests/test_skills.py` |
| dependencies | none |
| target repos | none to change; the next converge writes cards |

## Not in this change

- **`mf-release`.** Its deferred-work check already counts any list line, and a card is one.
- **Existing backlog blocks** in the human's backlog. They convert when next touched.
- **The review and security engines.** They are adopted unmodified; the card is part of the findings-file
  contract the stations are given, not a change to the engines.
- **Qualifying ids** (`0012·S1`). The export already does it by hand; writing that rule down is not settled.
