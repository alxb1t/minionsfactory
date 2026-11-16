# Test cost — tasks

One round for ten, one compile, the slow marks, the duplicates merged, and waits that assert. Decisions: [design](design.md).

## Progress

- [x] 1 — One round · moderate
- [x] 2 — One compile · moderate
- [x] 3 — The slow marks · moderate
- [ ] 4 — The duplicates · moderate
- [ ] 5 — Waits that assert · moderate

## 1 — One round

- [x] 1.1 In `tests/test_conduct.py`, drop `@pytest.mark.parametrize("attempt", range(10))` and the `attempt` parameter from `test_three_versions_cut_built_converged_and_closed_at_once`, and end its assert as `assert call in made, call` ([D1](design.md#d1)). Keep `@pytest.mark.slow`.
  Verify: `git grep -n attempt -- tests/test_conduct.py` prints no line.
- [x] 1.2 Check the test collects once.
  Verify: `uv run pytest tests/test_conduct.py -q --collect-only -k three_versions` prints one test id, with no `[` in it.
- [x] 1.3 In `openspec/changes/archive/0112-uv-race/design.md`, correct the fifth decision as [D6](design.md#d6) says. In its row, "is parametrized over ten rounds, each in its own `tmp_path`" → "runs one round in its own `tmp_path`", and the whole *because* cell becomes "the three versions share every resource of [the audit](#the-shared-state-audit) at once; the autouse `_uv_sync` fixture fakes every `uv sync --script`, so a second round repeats the first". In the `## Tests` table, "[D5](#d5), ten rounds" → "[D5](#d5), one round".
  Verify: `git grep -n "ten rounds" -- openspec/changes/archive/0112-uv-race/design.md` prints no line.

## 2 — One compile

- [x] 2.1 Add `tests/conduct_load.py`: a docstring, `_SCRIPT` the path of `skills/mf-ship/scripts/conduct.py`, `_CODE = compile(_SCRIPT.read_text(), str(_SCRIPT), "exec")`, and `def conduct() -> dict[str, Any]` as [D2](design.md#d2) sets out: a `types.ModuleType("<run_path>")` with `__file__`, entered in `sys.modules` for the call and the old entry restored in a `finally`, `exec(_CODE, module.__dict__)` with `# noqa: S102` on its line and `# why: the conductor's compiled source, run as `runpy` runs it` above it, a copy of the dict returned.
  Verify: `uv run ruff check tests/conduct_load.py` exits 0.
- [x] 2.2 In `tests/test_conduct.py`, replace the `_conduct` definition, whose body is `return runpy.run_path(str(_SCRIPT))`, with `from conduct_load import conduct as _conduct` in the import block, before `from fake_worker import (…)`, where ruff sorts it; keep `_SCRIPT` and `runpy`, which other tests read.
  Verify: `git grep -nF "runpy.run_path(str(_SCRIPT))" -- tests/test_conduct.py` prints no line.
- [x] 2.3 In `tests/test_sandboxed.py`, replace its `_conduct`, whose body is `return runpy.run_path(str(_SCRIPT))`, the same way, and drop the `runpy` import, `_SCRIPT` and `from typing import Any` when no other line reads them.
  Verify: `git grep -nF "runpy.run_path(str(_SCRIPT))" -- tests/test_sandboxed.py` prints no line.
- [x] 2.4 Add `test_each_conduct_load_is_a_fresh_module` to `tests/test_conduct.py`, after `_main`: two `_conduct()` loads hold different `Run` classes, each holds `__file__` equal to `str(_SCRIPT)`, and `"<run_path>"` is not in `sys.modules` after them. Its red run with `conduct()` returning one cached dict goes in the phase's commit body (`T6`).
  Verify: `uv run pytest tests/test_conduct.py -q -k fresh_module` exits 0.
- [x] 2.5 Run both files whole.
  Verify: `uv run pytest tests/test_conduct.py tests/test_sandboxed.py -q -n auto` exits 0.

## 3 — The slow marks

- [x] 3.1 Run the build's durations run and mark what it lists ([D3](design.md#d3)): above the `def` of each test its `slowest durations` block names, add `@pytest.mark.slow`, the other decorators kept; a test listed for setup or teardown only is marked too.
  Verify: `uv run pytest -q -n auto -m "not slow" --durations=0 --durations-min=5 tests/test_*.py` exits 0.
- [x] 3.2 Run it again; mark each test it still lists, and run it again until it lists none.
  Verify: `uv run pytest -q -n auto -m "not slow" --durations=0 --durations-min=5 tests/test_*.py` prints `hidden` under `slowest durations`, and no line holding `s call`, `s setup` or `s teardown`.

## 4 — The duplicates

- [ ] 4.1 **HALT CHECK** Every test the table of [design](design.md#tests) removes or edits stands at `HEAD` by its name, once.
  Verify: `git grep -n -E "def test_(a_lone_dependent_is_blocked_by_its_halt|a_later_version_ships_past_a_halted_one|a_forged_release_is_not_pushed|another_branch_moving_ends_the_reuse_of_a_result|a_git_grep_of_another_branch_is_not_reused_once_it_moves|a_dash_prefix_halts|an_ignore_target_halts|makeflags_ignore_halts|a_codex_fixers_prompt_names_its_attribution)\(" -- tests` prints each definition.
- [ ] 4.2 In `tests/test_conduct.py`, delete `test_a_lone_dependent_is_blocked_by_its_halt`. In the `lone` case of `test_run_halts_on_a_human_phase`, add its `_version` lines (`0002-marks` after `0001-todo`, `0003-more` after `0002-marks`) before the run, and after it the log assertions: a `0003-more · blocked — by 0002-marks` line, and a last line ending `halted 0001-todo · blocked 0002-marks 0003-more · released none · needs 0001-todo its **HUMAN phase`.
  Verify: `uv run pytest tests/test_conduct.py -q -k run_halts_on_a_human_phase` exits 0.
- [ ] 4.3 Delete `test_a_later_version_ships_past_a_halted_one` from `tests/test_conduct.py`; `test_a_later_version_halts_and_the_earlier_ships` and the first case of `test_run_halts_on_a_human_phase` carry it.
  Verify: `git grep -n test_a_later_version_ships_past_a_halted_one -- tests/test_conduct.py` prints no line.
- [ ] 4.4 Delete `test_a_forged_release_is_not_pushed` from `tests/test_conduct.py`. In `test_a_plain_commit_on_main_is_not_pushed`, after its `halts_on`, set `refs/remotes/origin/main` to `main` with `_git(root, "update-ref", …)` and call `halts_on` again.
  Verify: `git grep -n test_a_forged_release_is_not_pushed -- tests/test_conduct.py` prints no line.
- [ ] 4.5 Run the merged push test.
  Verify: `uv run pytest tests/test_conduct.py -q -k plain_commit_on_main` exits 0.
- [ ] 4.6 In `tests/test_plan_check.py`, delete `test_another_branch_moving_ends_the_reuse_of_a_result` and `test_a_git_grep_of_another_branch_is_not_reused_once_it_moves`. Add `git diff --quiet other HEAD` and `git grep -q LEGACY other -- src/legacy.py` to `commands` of `test_a_wrapped_git_command_is_not_reused_once_a_branch_moves`, and move `other` there onto the commit of the empty tree, as the deleted grep test did, so every command exits 1.
  Verify: `uv run pytest tests/test_plan_check.py -q -k wrapped_git_command` exits 0.
- [ ] 4.7 In `tests/test_gate_check.py`, delete `test_a_dash_prefix_halts`, `test_an_ignore_target_halts` and `test_makeflags_ignore_halts`. Add `.IGNORE:` and `MAKEFLAGS += -i` to `lines` of `test_a_planned_dash_the_task_does_not_quote_halts`.
  Verify: `uv run pytest tests/test_gate_check.py -q -k planned_dash` exits 0.
- [ ] 4.8 In `tests/test_stamp.py`, delete the step of `test_a_log_out_of_shape_is_not_stamped` that opens "A link swapped in after any check by name", through the `log.unlink()` that ends it.
  Verify: `git grep -n "swapped in after any check by name" -- tests/test_stamp.py` prints no line.
- [ ] 4.9 In `tests/test_converge.py`, add to the first run of `test_a_codex_fixer_runs_through_host_fix_and_halts_at_a_limit` the assert that `"Co-Authored-By: Codex gpt-6.1-sol <noreply@openai.com>"` is in `host.codexed[0][2]`. Cut the Codex run from `test_a_codex_fixers_prompt_names_its_attribution`, rename it `test_a_claude_fixers_prompt_names_its_attribution`, and end it on `host.codexed == []`.
  Verify: `git grep -n test_a_claude_fixers_prompt_names_its_attribution -- tests/test_converge.py` prints the definition.
- [ ] 4.10 Run the files the merges touched.
  Verify: `uv run pytest tests/test_converge.py tests/test_stamp.py tests/test_gate_check.py tests/test_plan_check.py -q -n auto` exits 0.
- [ ] 4.11 Run the durations run of 3.2 again; mark each merged survivor it lists.
  Verify: `uv run pytest -q -n auto -m "not slow" --durations=0 --durations-min=5 tests/test_*.py` prints `hidden` under `slowest durations`, and no line holding `s call`, `s setup` or `s teardown`.

## 5 — Waits that assert

- [ ] 5.1 In `_when_logged` of `tests/test_conduct.py`, add the keyword `seconds: float = 60.0`, the deadline's length. When its line is still missing at the deadline, `act` does not run, `hold` is made, and `join()` raises `TimeoutError` naming `said` ([D5](design.md#d5)).
  Verify: `git grep -n TimeoutError -- tests/test_conduct.py` prints the raise.
- [ ] 5.2 Add `test_a_log_line_that_never_comes_fails_the_wait` to `tests/test_conduct.py`, after `_when_logged`: `seconds=0.2`, a `said` no log holds, an `act` that records a call; `join()` raises `TimeoutError`, the recorder holds no call, and `hold` exists.
  Verify: `uv run pytest tests/test_conduct.py -q -k line_that_never_comes` exits 0.
- [ ] 5.3 In `test_a_dependent_waits_while_its_dependency_works`, add `assert waiting()` after the 30 s loop. Its red run with the `wait` log line dropped from `conduct.py`, undone after, goes in the phase's commit body (`T6`).
  Verify: `git grep -n "assert waiting()" -- tests/test_conduct.py` prints the line.
- [ ] 5.4 **HALT CHECK** The whole file passes with `_when_logged` raising: a test red here named a line that never came.
  Verify: `uv run pytest tests/test_conduct.py -q -n auto` exits 0.
- [ ] 5.5 Count the suite.
  Verify: `uv run pytest --collect-only -q tests/test_*.py` prints `694 tests collected`.
