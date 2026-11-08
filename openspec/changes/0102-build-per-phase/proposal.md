---
bump: minor
after: [0101-cut-converge-diet, 0099-stacked-builds]
---

# Build per phase

Under `mf-ship`, the build runs one fresh worker per phase and one more for its close — simplify, the metrics and
`build.done` — each starting from the change directory, `build-notes.md` and the change's `git log`. The cut rates each
phase `moderate` or `hard`, and an optional models-line part builds the moderate ones on their own model.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

One build session carries every phase's reads and output to its end: 0097's ran 206 turns, its context 28.6k at the start
and 547k at the most, its last phase at a 522k median. A fresh worker per phase, re-reading a ~100k base, simulates −$4.3 on
0097 and +$0.2 on 0096 ([evidence](design.md#evidence)). Per-phase workers also make a per-phase model possible.

## What Changes

- **The build station** — `conduct.py` spawns one build worker per unticked phase, `phase=<N>` in its prompt, then one for
  the close, `phase=close`. A phase worker passes only when its phase is ticked at `HEAD` on a clean tree, so no phase is
  spawned twice without a rescue's amend between.
- **The handoff** — each phase appends what the next must know to `.minions/changes/<change-id>/build-notes.md`; the
  conductor keeps at most 40 lines of each phase's append. A stacked dependent's amend reset removes the file.
- **`mf-build`** — takes `phase=<N>` and `phase=close`; bare, it builds every phase and closes, as today. It reads
  `build-notes.md` as evidence and appends its phase's notes.
- **The rating** — the cut ends each `## Progress` line but a `**HUMAN` one with ` · moderate` or ` · hard`. A phase rated
  `moderate` builds on the models file's `[build.moderate]` when it stands; every other phase, and every phase without that
  table, on `[build]`.
- **The models line** — `brief_check.py` takes an optional `build-moderate <model> <effort>` part after `cut`, with no host;
  the cut writes it as `[build.moderate]`.
- **The record** — a new decision; D65, D64, D57 and D13 edited; the threat model's entry points; `mf-ship`'s and
  `mf-plan`'s text.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The build runs a fresh worker per phase* — ADDED: a worker per phase and one for the close, the per-spawn check,
    `build-notes.md` and its 40-line bound, the reset removing it.
  - *A moderate phase builds on its own model* — ADDED: the ` · moderate` / ` · hard` rating and `[build.moderate]`.
  - *Model suggestions use exposed capabilities* — MODIFIED: one suggested build model, and a brief's `build-moderate`
    written as `[build.moderate]`.
  - *A hard brief is checked before it is queued* — MODIFIED: the optional `build-moderate` part.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-build/SKILL.md`, `skills/mf-cut-change/SKILL.md`,
`skills/mf-plan/scripts/brief_check.py`, `skills/mf-plan/SKILL.md`, `skills/mf-ship/SKILL.md`, `docs/decisions.md`,
`THREAT_MODEL.md`, `tests/test_conduct.py`, `tests/fake_worker.py` and `tests/test_brief_check.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- A worker per phase for a build run by hand: bare `/mf-build` keeps one session; `phase=` is there for a person who wants it.
- A model per phase beyond `moderate` and `hard`, and a host of its own for `[build.moderate]`.
- Per-phase rows in the review metrics: every build spawn stays the station `build`.
- Setting `build-moderate` in a brief: the trials of 0101 and debt paydown 3 decide it (brief T21, T23).
