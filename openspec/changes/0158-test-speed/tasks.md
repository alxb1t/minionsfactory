# Test speed — tasks

The scheduling default, then the marks and their words. Each phase follows [design](design.md).

## Progress

- [ ] 1 — The scheduling default · moderate
- [ ] 2 — The marks · moderate

## 1 — The scheduling default

- [ ] 1.1 Add `"--dist=worksteal"` to the `addopts` list of `pyproject.toml`, after `"--tb=short"`, per [D1](design.md#d1). Edit no other line of it.
  Verify: `git grep -n -e "--dist=worksteal" -- pyproject.toml` exits `0`.
- [ ] 1.2 Run the small file `tests/test_next_tag.py` under `-n 2`, to show the default parses beside `-n`, per [D5](design.md#d5). No file changes.
  Verify: `uv run pytest tests/test_next_tag.py -q -n 2` exits `0`.

## 2 — The marks

Each task below adds `@pytest.mark.slow` on its own line directly above the `def` of each function [the marks](design.md#the-marks) lists for its file, below any other decorator, per [D2](design.md#d2). It edits no other line.

- [ ] 2.1 Mark the functions of `tests/test_release.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_release.py` prints `74`.
- [ ] 2.2 Mark the functions of `tests/test_conduct.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_conduct.py` prints `239`.
- [ ] 2.3 Mark the functions of `tests/test_converge.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_converge.py` prints `36`.
- [ ] 2.4 Mark the functions of `tests/test_mark_pins.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_mark_pins.py` prints `25`.
- [ ] 2.5 Mark the functions of `tests/test_cut_check.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_cut_check.py` prints `18`.
- [ ] 2.6 Mark the functions of `tests/test_plan_check.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_plan_check.py` prints `17`.
- [ ] 2.7 Mark the functions of `tests/test_gate_run.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_gate_run.py` prints `11`.
- [ ] 2.8 Mark the functions of `tests/test_gate_check.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_gate_check.py` prints `11`.
- [ ] 2.9 Mark the functions of `tests/test_integrate.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_integrate.py` prints `14`.
- [ ] 2.10 Mark the functions of `tests/test_viewer.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_viewer.py` prints `14`.
- [ ] 2.11 Mark the functions of `tests/test_cut_context.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_cut_context.py` prints `6`.
- [ ] 2.12 Mark the functions of `tests/test_pin.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_pin.py` prints `6`.
- [ ] 2.13 Mark the functions of `tests/test_modelsfile.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_modelsfile.py` prints `5`.
- [ ] 2.14 Mark the functions of `tests/test_queue_pins.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_queue_pins.py` prints `6`.
- [ ] 2.15 Mark the functions of `tests/test_metric_scripts.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_metric_scripts.py` prints `5`.
- [ ] 2.16 Mark the functions of `tests/test_sandboxed.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_sandboxed.py` prints `6`.
- [ ] 2.17 Mark the functions of `tests/test_brief_check.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_brief_check.py` prints `5`.
- [ ] 2.18 Mark the functions of `tests/test_next_tag.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_next_tag.py` prints `2`.
- [ ] 2.19 Mark the function of `tests/test_awake.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_awake.py` prints `1`.
- [ ] 2.20 Mark the function of `tests/test_corpus.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_corpus.py` prints `1`.
- [ ] 2.21 Mark the function of `tests/test_cut_pre.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_cut_pre.py` prints `1`.
- [ ] 2.22 Mark the function of `tests/test_facts.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_facts.py` prints `1`.
- [ ] 2.23 Mark the function of `tests/test_metrics.py`.
  Verify: `grep -c -e "^@pytest.mark.slow" tests/test_metrics.py` prints `2`.
- [ ] 2.24 In the marker line of `pyproject.toml`, change `over 5 s` to `over 1 s`, per [D2](design.md#d2). Leave the rest of the line.
  Verify: `git grep -n -e "over 1 s" -- pyproject.toml` exits `0`.
- [ ] 2.25 In `AGENTS.md`, after the sentence that says `make check` runs its fast steps, no `slow` test, between build phases, add `In this repository a test over 1 s is `slow`.` and re-wrap the paragraph, keeping `over 1 s` unbroken on one line.
  Verify: `git grep -n -e "over 1 s" -- AGENTS.md` exits `0`.
