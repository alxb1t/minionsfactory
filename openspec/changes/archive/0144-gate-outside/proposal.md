---
bump: minor
version: 0.115
debt: [0143·R3]
---

# Gate outside

The conductor runs the full gate, as a script, after the last phase and at the close, and a worker runs `make check` alone: no worker waits on a gate that outlasts its 5-minute cache.

Reading map: [design](design.md) holds the decisions and the test cost, [tasks](tasks.md) holds the phases: the close's model key, the close command, the build loop, the skills and converge, the records.

## Why

A build worker that waits on a gate longer than the 5-minute cache writes its context again, and the runs' measured cost of it is in dollars. The close asks for the gate many times and always runs on `[build]`.

A script's gate costs no tokens, can be timed and logged, and can be run again. A red gate after the last phase also has no worker behind it today, so it always needs a person.

## What Changes

- **A `build-close` part** of the brief's models line, after `build-moderate`, written as `[build.close]`; the close's spawn runs on it, else on `[build.moderate]`, else on `[build]`, key by key.
- **`conduct.py close <change-id>`** runs the gate through `gate_run.py`, the metrics, the plan check from the base, and writes `build.done`; it writes `gate.red` and `build.halt` on a failure. `gate_run.py` reads a gate past its limit as red.
- **The build loop** runs the gate after the last phase; a red gate starts one `phase=repair` worker, then the gate again, and a second red halts. `phase=close` is a simplify worker alone; the conductor then writes `build.simplified` and runs the close's steps, drops a simplify commit when the gate is red with it, and resumes at the steps with no worker after an amend of the change directory.
- **The skills** say `make check` at every phase where the target stands, the last included; the close is simplify alone; a hand build runs `conduct.py close` once; the fixer runs `make check`. `I8` reads the same in both skills.
- **Converge's freeze** reads the plan check from the close's result and runs none when `build.done` names the frozen head.
- **The gate's pytest** gains `--durations=20`.
- **The records**: D13, D70, D73 and D74 are edited where they live, D87 is added, and the CHANGELOG line debt card `0143·R3` names is rewritten.
- **Requirements** — one line each, as the delta holds them:
  - ADDED *The conductor runs the gate of a build*.
  - ADDED *A close command ends a build*.
  - MODIFIED *The build runs a fresh worker per phase*.
  - MODIFIED *A moderate phase builds on its own model*.
  - MODIFIED *The build runs a quick check between phases*.
  - MODIFIED *The build collects a draft of the metrics after simplify*.
  - MODIFIED *mf-simplify simplifies a change inside its oracles*.
  - MODIFIED *A re-run recovers what a dead station left*.
  - MODIFIED *A plan check holds the plan to the built tree*.
  - MODIFIED *Converge writes the evidence of each freeze*.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the build's close, the models file's `[build.close]`, the gate's runner and the freeze's evidence.

## Impact

- Code: `skills/mf-ship/scripts/conduct.py`, `skills/mf-converge/scripts/gate_run.py`, `skills/mf-converge/scripts/converge.py`, `skills/mf-plan/scripts/brief_check.py`, `skills/mflib/modelsfile.py`.
- Skills: `skills/mf-build/SKILL.md`, `skills/mf-simplify/SKILL.md`, `skills/mf-plan/SKILL.md`, `skills/mf-cut-change/SKILL.md`, and the fixer's reference, `skills/mf-converge/references/fix.md`.
- A repository's `metrics/catalogue.toml` stays as it is: the close reads it where it stands.
- Tests: `tests/test_conduct.py`, `tests/test_gate_run.py`, `tests/test_converge.py`, `tests/test_brief_check.py`, `tests/test_modelsfile.py`, `tests/fake_worker.py`.
- The gate: `Makefile` gains one pytest option, so the dry run's hash changes once.
- Docs: `docs/decisions.md`, `docs/modules.md`, `CHANGELOG.md`.

## Not in this change

- The Codex side's dollars, and a price for a Codex window share.
- A change to what the release's gate runs are ([D17](../../../docs/decisions.md)).
- isekai's own mutation tool and its cut.
- A paydown version: it follows the versions of this line.
- The run log's new fields — the phase on a spawn line, cause words, the load — which `run-fields` takes; this change logs a gate with the `check` event the log already has.
- The `build-close` part in this change's own models line: the pinned `brief_check.py` does not know it, so this change's close runs on `[build]`.
