# Debt paydown 3b — tasks

Build the settled [design](design.md), one phase at a time; each fix's test step goes red before its fix.

## Progress

- [x] 1 — The security and link cards · hard
- [x] 2 — The stacking, tool, probe, rejoin and converge cards · hard
- [x] 3 — The test-cost reasons and the docstrings · moderate
- [ ] 4 — The archived design lines the fixes made stale · moderate

## 1 — The security and link cards

- [x] 1.1 Add a step to `test_a_rescue_amends_at_amend_needed` in `tests/test_conduct.py` with an adversarial card whose Priority category is `security (exposure of secrets)`, then add `NON_SECURITY` beside `BLOCKS` in `skills/mf-ship/scripts/conduct.py` and change `_security_card` to read `_category(card) not in NON_SECURITY`, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_conduct.py -k a_rescue_amends_at_amend_needed` exits 0.
- [x] 1.2 Add a step to `test_a_run_moves_an_old_layout` in `tests/test_conduct.py` that swaps an old `review.md` for a link to a file outside `.minions` between the link check and the move (patch `_folder_fd` in the method's globals to do the swap), and asserts the method returns the `became a link` reason and the target file keeps one name. Then change `Run.migrate_layout` in `skills/mf-ship/scripts/conduct.py` per [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_conduct.py -k a_run_moves_an_old_layout` exits 0.
- [x] 1.3 Add `test_a_link_planted_after_the_removal_truncates_no_models_file` to `tests/test_conduct.py`: patch `_remove_in` in `_write_models`'s globals to remove the file and plant a hard link to a victim file, call `_write_models`, and assert it stops with 2 and the victim keeps its text. Then add `fresh` to `_write_in_change` and pass it from `_write_models` in `skills/mf-ship/scripts/conduct.py`, per [D5](design.md#d5).
  Verify: `uv run pytest -q tests/test_conduct.py -k a_link_planted_after_the_removal_truncates_no_models_file` exits 0.
- [x] 1.4 Add a step to `test_a_codex_temp_folder_is_removed` in `tests/test_conduct.py` that leaves the folder's root at mode `000` and wraps `os.chmod` to raise `PermissionError` for the root's parent, and asserts the folder is removed. Then guard the parent `chmod` in `_remove_temp.unlock` of `skills/mf-ship/scripts/conduct.py` on `os.fspath(path)`, per [D6](design.md#d6).
  Verify: `uv run pytest -q tests/test_conduct.py -k a_codex_temp_folder_is_removed` exits 0.
- [x] 1.5 Add steps to `test_a_supervisor_settle_outside_the_text_halts` in `tests/test_conduct.py`: a merge whose body names `src.py: test fixed — kept` is reported as holding `src.py`, and a commit on top of a settled merge is reported as `integrate committed past its merge`. Then add `TEST_PATHS` beside `SETTLES` and change `_settle_kept` in `skills/mf-ship/scripts/conduct.py`, per [D7](design.md#d7).
  Verify: `uv run pytest -q tests/test_conduct.py -k a_supervisor_settle_outside_the_text_halts` exits 0.
- [x] 1.6 Add a step to `test_a_cut_halt_is_shown_and_rejoin_cuts_again` in `tests/test_conduct.py`: a brief whose new package row holds `\x1b[2K` in a cell makes `rejoin` raise `Stop` with code 2 naming the row by `repr`. Then add the check to `rejoin` in `skills/mf-ship/scripts/conduct.py`, per [D8](design.md#d8).
  Verify: `uv run pytest -q tests/test_conduct.py -k a_cut_halt_is_shown_and_rejoin_cuts_again` exits 0.

## 2 — The stacking, tool, probe, rejoin and converge cards

- [x] 2.1 Add a step to `test_a_stacked_dependent_resets_and_merges_back` in `tests/test_conduct.py` in which the dependent's tree holds an archive folder for its dependency while the default branch lacks it, and `stage_of` still returns `stacked`. Then change the `stacked` return in `stage_of` of `skills/mf-ship/scripts/conduct.py`, per [D9](design.md#d9).
  Verify: `uv run pytest -q tests/test_conduct.py -k a_stacked_dependent_resets_and_merges_back` exits 0.
- [x] 2.2 Add a step to `test_a_dependent_waits_while_its_dependency_works` in `tests/test_conduct.py` in which a dependent names unreleased dependencies A and B, A releases during the wait, and the dependent stacks on B while its thread lives. Then change `Run.until` and `Run.ready` in `skills/mf-ship/scripts/conduct.py`, per [D9](design.md#d9).
  Verify: `uv run pytest -q tests/test_conduct.py -k a_dependent_waits_while_its_dependency_works` exits 0.
- [x] 2.3 Add a step to `test_a_worker_asking_for_a_missing_tool_halts` in `tests/test_conduct.py` with an errored `Bash` result whose text is `Exit code 1` and a pytest line holding `No such tool available: Task`, asserting `lacked` returns `[]`, and add that test's `# T2: <reason>; 0119-debt-paydown-3b design D15.` line from [D15](design.md#d15)'s table. Then change `lacked` in `skills/mf-ship/scripts/conduct.py`, per [D11](design.md#d11).
  Verify: `uv run pytest -q tests/test_conduct.py -k a_worker_asking_for_a_missing_tool_halts` exits 0.
- [x] 2.4 Add a step to `test_a_checker_falls_back_when_the_weekly_window_is_spent` in `tests/test_conduct.py`: discard `"codex"` from `run.probed`, replace `run.probe_for` with a function that fails the test when called, and with a deadline under `PROBE_ROOM` ahead assert `codex_ready` returns False, `run.halts` stays empty and `run.refused` stays empty. Then add `PROBE_ROOM` beside `LIMIT_WAIT` and the early return in `Run.codex_ready` of `skills/mf-ship/scripts/conduct.py`, per [D12](design.md#d12).
  Verify: `uv run pytest -q tests/test_conduct.py -k a_checker_falls_back_when_the_weekly_window_is_spent` exits 0.
- [x] 2.5 Add a step to `test_a_fixed_version_rejoins_a_live_run` in `tests/test_conduct.py`: a request for a version whose thread lives and whose last log event is a `rescue` spawn is present again after `take_requests`, and a poll after the thread ends takes it. Then add `self.kept` beside `self.candidates` in `Run.__init__` and the write in `Run.take_requests` of `skills/mf-ship/scripts/conduct.py`, per [D13](design.md#d13).
  Verify: `uv run pytest -q tests/test_conduct.py -k a_fixed_version_rejoins_a_live_run` exits 0.
- [x] 2.6 Add `test_a_halt_on_an_ended_log_is_printed_not_stamped` to `tests/test_converge.py`: on a status log whose newest run ends on `done`, `converge["halt"](context, "git failed")` raises nothing and the log keeps its bytes. Then add the early return to `halt` in `skills/mf-converge/scripts/converge.py`, skipped when the top event is a `halt` whose detail `LOCKED` matches, per [D14](design.md#d14): `test_the_debt_is_written_once_under_its_lock` stamps a halt on top of a lock halt.
  Verify: `uv run pytest -q tests/test_converge.py -k "a_halt_on_an_ended_log_is_printed_not_stamped or the_debt_is_written_once_under_its_lock"` exits 0.

## 3 — The test-cost reasons and the docstrings

- [x] 3.1 Add the reason of [D15](design.md#d15)'s table as a `# T2: <reason>; 0119-debt-paydown-3b design D15.` line at the top of the body of `test_a_shadow_round_drives_no_fix` and `test_every_station_starts_lean` in `tests/test_conduct.py`; task 2.3 wrote the third.
  Verify: `grep -c -e 'no other run test reaches it' -e 'it writes the operator' tests/test_conduct.py` prints `2`.
- [x] 3.2 Cut the `_temp_folder` docstring and the `_remove_temp` docstring in `skills/mf-ship/scripts/conduct.py` to a summary line, a blank line and the `Why:` line, per [D15](design.md#d15).
  Verify: `grep -c -e 'a .000. subfolder' -e 'e.g. ._temp_folder' skills/mf-ship/scripts/conduct.py` prints `0`.
- [x] 3.3 Replace `Why: 0090-supervisor-merge security S2.` in the `_settle_kept` docstring of `skills/mf-ship/scripts/conduct.py` with `Why: 0090-supervisor-merge design D4, its delta's *A supervisor answers what the rescue leaves*.`.
  Verify: `grep -c 'security S2' skills/mf-ship/scripts/conduct.py` prints `0`.

## 4 — The archived design lines the fixes made stale

- [ ] 4.1 In the `### D1` entry of `openspec/changes/archive/0099-stacked-builds/design.md`, per [D17](design.md#d17): the `until` signature's `stack: bool,` becomes `still: Callable[[], list[str]],`; its docstring's first line becomes `"""Wait while the dependency's thread lives, until the version may stack.`; after the code block, the clause naming the flag true when one id is unreleased becomes `ready` passing `still`, a callable that returns the unreleased dependencies at each poll, and `until` asking `self.stackable(version, still())`, `per 0119-debt-paydown-3b design D9`.
  Verify: `grep -n -e 'stack: bool' -e 'true when one id is unreleased' openspec/changes/archive/0099-stacked-builds/design.md` exits 1.
- [ ] 4.2 In the `### D5` entry of `openspec/changes/archive/0100-worker-diet/design.md`, per [D17](design.md#d17): the `lacked` item's words that the result holds `MISSING` become that the result's text opens with `MISSING` once its `<tool_use_error>` prefix is removed and its leading whitespace stripped, `per 0119-debt-paydown-3b design D11`.
  Verify: `grep -n 'holds .MISSING.' openspec/changes/archive/0100-worker-diet/design.md` exits 1.
- [ ] 4.3 In the `### D3` entry of `openspec/changes/archive/0104-codex-limits/design.md`, per [D17](design.md#d17): the `Run.codex_ready` item, Codex unprobed, returns False when less than `PROBE_ROOM` is left before `deadline`, `per 0119-debt-paydown-3b design D12`, and calls `self.probe_for` otherwise.
  Verify: `grep -c 'PROBE_ROOM' openspec/changes/archive/0104-codex-limits/design.md` prints `1`.
