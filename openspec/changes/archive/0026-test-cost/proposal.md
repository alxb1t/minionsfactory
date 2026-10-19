---
version: v0.26
---

# 0026-test-cost — proposal

**In one line:** the line places each test by its cost — the lowest layer, a step in an existing test before a new
one, engines only where they differ — consolidates only per the design's table, has review judge test cost and
traced coverage, and has the release print the gate's time.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | the evidence, the decisions (`B1`…`B13`) and the text, word for word |
| [tasks.md](tasks.md) | the build: the rules for tests, consolidation, the review passes, the clock, the record |

## Why

A target repo built under the line grew its browser suite from 64 to 1 002 runs and its CI from 6 to 54 minutes over
eleven releases, and nothing showed it. The skills push that way: the build writes a new test for every acceptance,
the fix station a new regression test for every finding, and *"never weaken the gate"* forbids merging a test as
firmly as dropping a proof.

## What Changes

```
  cut ── design.md `## Tests`: the cost line, the consolidation table
   │
   ▼
  build ── T1…T6: lowest layer · extend before adding · engines only where they differ
   │       deletes or merges only per the table (I16)
   ▼
  converge ── fix: T1…T6, never deletes · review: + test-cost pass, + coverage-trace pass
   │
   ▼
  release ── `Gate:` line in the CHANGELOG: local time, CI time, the previous release's
```

- **Rules for tests** `T1`…`T6`, owned by `mf-build`, carried by `mf-cut-change` and `mf-converge`, synced by a
  scan. `W5`'s twin follows `T6`. See [B1](design.md#b1)–[B3](design.md#b3).
- **Consolidation is not weakening** when `design.md`'s `## Tests` table names it: new contract item `I16`, artifact
  rule `A8`; the fix station never deletes or merges a test. See [B4](design.md#b4)–[B6](design.md#b6).
- **Review runs a test-cost pass and a coverage-trace pass**, each checked in its Summary, every round. See
  [B7](design.md#b7)–[B9](design.md#b9).
- **The release records the gate's time** — precondition 1's local run and CI's last green run on the default
  branch — in one `Gate:` line. See [B10](design.md#b10).
- **The record:** D39 added; D17 and two principles amended; the bootstrap's `CLAUDE.md` gets `## Tests`. See
  [B11](design.md#b11)–[B13](design.md#b13).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `sdd`: **ADDED** *The build owns the rules for tests, and the cut and converge carry them* — `T` ids equal in the
  three skills.
- `sdd`: **ADDED** *A test is deleted or merged only as the design's table names it* — the build halts outside it;
  the fix station never deletes or merges.
- `sdd`: **ADDED** *Review judges test cost and traced coverage* — the test-cost and coverage-trace passes, each
  checked in the Summary.
- `sdd`: **ADDED** *The release records the gate's time* — the `Gate:` line, from precondition 1's run and
  `gh run list`.
- `sdd`: **ADDED** *The bootstrap's `CLAUDE.md` states the rules for tests* — a `## Tests` section in the template.
- `sdd`: **MODIFIED** *A fix's test fails without the fix* — the red run may be an extended test's.

## Impact

| area | files |
|---|---|
| skills | `skills/mf-build/SKILL.md`, `skills/mf-cut-change/SKILL.md`, `skills/mf-converge/SKILL.md`, `skills/mf-release/SKILL.md`, `skills/mf-bootstrap/templates/CLAUDE.md.tmpl` |
| tests | `tests/test_skills.py` |
| docs | `docs/decisions.md` (D17, D39), `docs/principles.md` |
| dependencies | none; `gh` is operator tooling, read when present |
| target repos | none changed; their next change is cut and built under the rules |

## Not in this change

- **A fast phase gate.** When the gate runs is the next change's feature: an optional `make phase-gate` after each
  phase, the full `make gate` once per build, per round and at release.
- **A CI template in the bootstrap,** and a `timeout-minutes` on it. Trigger: when the bootstrap writes CI.
- **A time estimate at the cut.** The cost line counts tests and runs; no per-run cost is on disk.
- **A threshold on the gate's time.** The release prints it; nothing halts on it.
- **Binding scenarios to tests** — D36 stands; this is where a test goes and what it costs.
- **The vault's adoption template.** It lives outside this repo.
