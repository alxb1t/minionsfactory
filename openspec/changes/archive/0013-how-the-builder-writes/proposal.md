---
version: v0.13
---

# 0013-how-the-builder-writes — proposal

**In one line:** `mf-build` gets rules for what it writes — true claims (`W`), readable prose (`P`, shared with
`mf-cut-change`) and useful code comments (`C`) — and `mf-cut-change` gets the planning rules.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | the decisions (`D1`…`D8`) and the full text of every rule list |
| [tasks.md](tasks.md) | the build: 3 phases, one commit each |
| [specs/sdd/spec.md](specs/sdd/spec.md) | one new requirement, held by a test |

## Why

Two problems, one feature: how the builder writes.

**1. What the builder writes goes false.** isekai's architecture review found false claims across its tree: a
retired mechanism still described, an *only* no test holds, a count that drifted
([evidence](design.md#evidence)). Nothing in `mf-build` says how to write a claim.

**2. What the builder writes is hard to read.** `mf-cut-change`'s artifacts follow a style the human finds easy
to read. `mf-build` has none, and isekai's next versions are docs.

## What Changes

```
  mf-build writes ──┬── docs, CHANGELOG ──── W + P ─┐
                    └── code comments ────── W + C  │  P is shared: owned by mf-build,
                                                    │  carried by mf-cut-change,
  mf-cut-change writes ── change artifacts ── P + A ┘  ids held equal by a test
```

- **`W1`…`W6` — the truth rules**, in `mf-build`. FR-3's rules 1–5 and 8. A retirement's search results go in
  the phase's commit body. See [D1](design.md#d1), [D2](design.md#d2).
- **`P1`…`P13` — the prose rules.** Split out of `mf-cut-change`'s style list, owned by `mf-build`, carried by
  `mf-cut-change`. They apply to the docs and CHANGELOG entries `mf-build` writes. See [D3](design.md#d3),
  [D4](design.md#d4).
- **`C1`…`C12` — the comment rules**, in `mf-build` only. See [D5](design.md#d5).
- **No sweeps.** `P` and `C` cover text a phase writes or changes — never a whole file unasked. See
  [D6](design.md#d6).
- **Counts become names.** A count in prose is replaced by the things it counts; only a change's evidence tables
  keep counts. See [D4](design.md#d4).
- **`A1`…`A6` — the artifact rules**, in `mf-cut-change` only: the three artifact-only style rules, plus FR-3's
  planning rules 6, 7 and 9. See [D7](design.md#d7).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `sdd`: one ADDED requirement.

| requirement | what changes |
|---|---|
| The build and the cut share one list of prose rules | new: the `P` ids in `mf-build` and `mf-cut-change` are the same set, numbered from `P1` with no gap |

## Impact

| area | files |
|---|---|
| skills | `skills/mf-build/SKILL.md` · `skills/mf-cut-change/SKILL.md` |
| tests | `tests/test_skills.py` |
| dependencies | none |
| target repos | none to change; the next change built in any repo follows the rules |

## Not in this change

- **`mf-converge`.** Its engines are adopted unmodified, and it is optional since v0.12.
- **A mechanical prose check.** The human's read, and review when converge runs, are the checks
  ([D8](design.md#d8)).
- **Rewriting existing text** — this repo's long comment blocks, old CHANGELOG entries, living specs. They change
  when a change touches them.
- **This repo's patch conditions.** `A6` says each repo states them; `CLAUDE.md` states none yet. That waits
  for the first patch.
