---
bump: minor
version: 0.116
debt: [0089·S2, 0090·S1]
---

# Halts alone

The line closes halts that today wait for a person: a rescue's decided amend, a gate red under load, a Codex checker that fails, a converge halt a worker's exit caused, a verdict that misses its scope, a hand converge that ignores its models file, a design-sized cap, a stacked base's changelog entries, and a `wait` that cannot end early.

Reading map: [design](design.md) holds the decisions and the test cost, [tasks](tasks.md) holds its phases: the rescue's amend, the gate under load, Codex's fallbacks, converge's ways back, the supervisor at the cap, and the changelog rule, the wait and the records.

## Why

In the runs of 2026-11-22 a watcher on Opus answered the halts the line had no route for (Q3). This version gives routes to the halts whose fix is a rule, not a judgment, so that no agent has to
watch a run. Cards `0089·S2` and `0090·S1` ride along: their trigger is the next change that opens D61 or the
supervisor's path rule, which this one does (Q50).

## What Changes

- **Rescue amend** — under the switch an amend that decides is taken with or without `Decided-by: rescue`; without the switch it is refused as before and its commit is reset off `HEAD`.
- **Gate under load** — a red conductor gate read under a load over the cores waits, at most 1,800 s, for the load to fall, then runs once more.
- **Codex fallbacks** — a Codex checker that fails twice before a completed turn runs on Claude; a failed checker probe marks Codex not ready for the version.
- **Converge's ways back** — a halt a worker's exit or timeout caused, with no verdict read, is run again once by the run, then read as a rerun; a verdict whose scope misses the freeze is sent out once more; a hand converge reads the models file.
- **Supervisor at the cap** — under the switch the supervisor may amend a design-sized cap's plan once a version.
- **Changelog rule** — a stacked branch's entries that the default branch released are dropped, not a halt.
- **`wait --halt`** — ends, exit 1, when a version halts with no rescue or supervisor left.
- **Records** — D60, D61, D76 and `THREAT_MODEL.md` are edited where they live; one decision is added.

Requirement lines, one each:

- MODIFIED `A rescue decides by the version's switch` — the trailer is no condition; a refused amend is reset.
- MODIFIED `The conductor runs the gate of a build` — the gate waits out a load.
- MODIFIED `A Codex checker falls back to Claude while Codex is limited` — a failure falls back too, as `fallback: codex failed`.
- MODIFIED `The integrate station resolves mechanical conflicts by fixed rules` — a stacked base's released entries are dropped.
- MODIFIED `` `conduct.py wait` blocks until the run ends `` — `--halt` ends it at a halt nothing answers.
- ADDED `A failed Codex checker probe leaves the checkers on Claude`.
- ADDED `A converge halt no verdict followed is run again`.
- ADDED `A verdict that misses the freeze's scope is sent out once more`.
- ADDED `A converge by hand reads the models file`.
- ADDED `A supervisor re-plans a design-sized cap once`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd` — each MODIFIED and ADDED requirement above.

## Impact

- `skills/mf-ship/scripts/conduct.py`, `skills/mf-converge/scripts/converge.py`, `skills/mflib/statuslog.py`, `skills/mf-integrate/scripts/integrate.py`.
- `skills/mf-rescue/SKILL.md`, `skills/mf-supervise/SKILL.md`, `skills/mf-converge/SKILL.md`, `skills/mf-ship/SKILL.md`, `skills/mf-integrate/SKILL.md`.
- `docs/decisions.md` (D60, D61, D76, D88), `THREAT_MODEL.md`; the paths the threat model names under `openspec/` and `docs/`.
- `tests/test_conduct.py`, `tests/test_converge.py`, `tests/test_integrate.py`, `tests/test_statuslog.py`.

## Not in this change

- The Codex side's dollars, and a price for a Codex window share.
- A change to the release's gate runs (D17).
- isekai's own mutation tool and its cut.
- A paydown version: it follows the token line.
- The refusal of a `**HUMAN` phase: it is `cut-catches`' row of the cut.
- New fields of the run log: they are `run-fields`.
