---
bump: minor
version: v0.128
---

# Test speed

A version's tests take less of its time: pytest hands the gate's tests out by work stealing, and `make check` skips every test over 1 s.

Reading map: [design](design.md) holds the measure, the rules and the list of marks, [tasks](tasks.md) holds the phases.

## Why

Tests are most of a version's run time: its gates, its `make check` after each phase and the slow runs a worker chooses.
The [measure](design.md#context) shows the causes that are cheap to remove.

- The gate's tests are handed out in fixed chunks, so one worker holds the longest test while the others wait. Work stealing ran the same tests in less wall.
- `make check` runs after every phase, and only tests over 5 s are marked `slow`. The tests under 1 s are a fraction of its wall.

## What Changes

- `pyproject.toml`'s `addopts` gains `--dist=worksteal`: every pytest run that carries `-n` takes it, and a run with no `-n` is as before.
- Each test function that [design](design.md#the-marks) lists gains `@pytest.mark.slow`: its slowest case ran over 1 s in the measure, and the whole-repo scanners are not listed.
- The marker's text in `pyproject.toml` says `over 1 s`, and `AGENTS.md` says that in this repository a test over 1 s is `slow`.
- No requirement changes, so the change carries no spec delta (`skip_specs`).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change edits the repository's own test configuration and marks, which no requirement states; see [D10](../../../docs/decisions.md).

## Impact

- `pyproject.toml` and `AGENTS.md`.
- Test files, each gaining marks per [design](design.md#the-marks): `tests/test_release.py`, `tests/test_conduct.py`,
  `tests/test_converge.py`, `tests/test_mark_pins.py`, `tests/test_cut_check.py`, `tests/test_plan_check.py`,
  `tests/test_gate_run.py`, `tests/test_gate_check.py`, `tests/test_integrate.py`, `tests/test_viewer.py`,
  `tests/test_cut_context.py`, `tests/test_pin.py`, `tests/test_modelsfile.py`, `tests/test_queue_pins.py`,
  `tests/test_metric_scripts.py`, `tests/test_sandboxed.py`, `tests/test_brief_check.py`, `tests/test_next_tag.py`,
  `tests/test_awake.py`, `tests/test_corpus.py`, `tests/test_cut_pre.py`, `tests/test_facts.py` and `tests/test_metrics.py`.
- `make check` runs the tests under 1 s and the scanners; the gate runs every test, so no proof leaves the gate.
- A break in a slow test shows at the build's end gate, not at the phase that made it. The person accepted this risk at the plan.

## Not in this change

- The conductor's git calls: a later version, when a round of its own is planned.
- The rewrites of the long flow tests, a repository template and compile-once.
- A tool that picks impacted tests; `pytest-testmon` is not taken.
- T1's text, the bootstrap template, `SLOW_SECONDS` and the metric `slow-tests`.
- An edit of the root `Makefile`, a `conftest.py` hook, a second marker and a check of a measured time.
- CI's run time, and the tests audit's findings on proof.
