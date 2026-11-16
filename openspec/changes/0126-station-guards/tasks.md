# Station guards — tasks

A phase for each station: the case each guard lacks, seen red under its break per [D2](design.md#d2), then green. Each row `G` is in [the guards](design.md#the-guards).

## Progress

- [x] 1 — The gate's guards · moderate
- [ ] 2 — Verify:'s shell refusals · moderate
- [ ] 3 — The cut's contract · moderate
- [ ] 4 — Converge's cards, cap and verdict · moderate
- [ ] 5 — Integrate's merge and git failure · moderate
- [ ] 6 — The viewer's bind · moderate

## 1 — The gate's guards

- [x] 1.1 Add row G1's two-task case, keyed `"second"`, to `tests/test_gate_check.py`'s `test_a_bare_makefile_task_fails_the_plan_check`.
  Verify: `git grep -n '"second"' -- tests/test_gate_check.py` prints a line, then `uv run pytest tests/test_gate_check.py::test_a_bare_makefile_task_fails_the_plan_check -q` exits 0.
- [x] 1.2 Add the new `test_a_makefile_outside_the_tree_hides_none_inside` to `tests/test_gate_check.py`, built to row G2 and [D3](design.md#d3).
  Verify: `uv run pytest tests/test_gate_check.py::test_a_makefile_outside_the_tree_hides_none_inside -q` exits 0.
- [x] 1.3 Add the new `test_a_gate_that_changes_what_it_ran_on_records_nothing` to `tests/test_gate_run.py`: row G3's case, then row G4's, per [D4](design.md#d4).
  Verify: `uv run pytest tests/test_gate_run.py::test_a_gate_that_changes_what_it_ran_on_records_nothing -q` exits 0.
- [x] 1.4 Add row G5's `false` case, a sub-task titled `Silent`, to `tests/test_plan_check.py`'s `test_a_plan_check_finds_what_the_plan_left`.
  Verify: `git grep -n Silent -- tests/test_plan_check.py` prints a line, then `uv run pytest tests/test_plan_check.py::test_a_plan_check_finds_what_the_plan_left -q` exits 0.
- [x] 1.5 Leave every line broken for a red run as it was.
  Verify: `git diff --quiet HEAD -- skills` exits 0.

## 2 — Verify:'s shell refusals

- [ ] 2.1 Add rows G6 to G10 as refusals, starting `grep -eo`, `grep -n -f`, `grep -n -e x`, `grep -n x a.md; cd /` and `if grep`, to the table of `tests/test_verify_check.py`'s `test_a_check_out_of_shape_breaks_and_is_not_run`, each expecting the line the script prints for it.
  Verify: `git grep -n -F -e 'grep -eo' -- tests/test_verify_check.py` prints a line, then `uv run pytest tests/test_verify_check.py::test_a_check_out_of_shape_breaks_and_is_not_run -q` exits 0.
- [ ] 2.2 Add row G11's passing check, `grep -n cd app/states.py`, to the `fits` list of `tests/test_verify_check.py`'s `test_a_search_prints_the_lines_it_matches_at_head`.
  Verify: `git grep -n -F -e 'grep -n cd app/states.py' -- tests/test_verify_check.py` prints a line, then `uv run pytest tests/test_verify_check.py::test_a_search_prints_the_lines_it_matches_at_head -q` exits 0.
- [ ] 2.3 Leave every line broken for a red run as it was.
  Verify: `git diff --quiet HEAD -- skills` exits 0.

## 3 — The cut's contract

- [ ] 3.1 Add rows G12 and G13 to `tests/test_cut_check.py`'s `test_i4_names_each_defect_of_the_tasks_shape`, each asserting its message, `listed twice` and `lists no phase`, in the halt.
  Verify: `git grep -n -e 'listed twice' -- tests/test_cut_check.py` prints a line, then `uv run pytest tests/test_cut_check.py::test_i4_names_each_defect_of_the_tasks_shape -q` exits 0.
- [ ] 3.2 Add row G14's case to the same test, asserting `sits outside its` in the halt, and delete its assert on the absent `sits in section 1` message.
  Verify: `git grep -n -e 'sits outside its' -- tests/test_cut_check.py` prints a line, then `uv run pytest tests/test_cut_check.py::test_i4_names_each_defect_of_the_tasks_shape -q` exits 0.
- [ ] 3.3 Leave every line broken for a red run as it was.
  Verify: `git diff --quiet HEAD -- skills` exits 0.

## 4 — Converge's cards, cap and verdict

- [ ] 4.1 Add row G15's second card, held in a variable `sibling`, to `tests/test_converge.py`'s `test_a_fixed_repeats_old_card_is_cleared`, the debt compared byte for byte.
  Verify: `git grep -n sibling -- tests/test_converge.py` prints a line, then `uv run pytest tests/test_converge.py::test_a_fixed_repeats_old_card_is_cleared -q` exits 0.
- [ ] 4.2 Add the new `test_round_three_is_the_cap_of_a_pickup_and_a_catch_up` to `tests/test_converge.py`: row G16's case, then row G17's.
  Verify: `uv run pytest tests/test_converge.py::test_round_three_is_the_cap_of_a_pickup_and_a_catch_up -q` exits 0.
- [ ] 4.3 Add row G18's case as the `_RESUMED` row `"catch-up at round three"` and a branch of `_resumed` that plants it, in `tests/test_converge.py`.
  Verify: `git grep -n -F -e '"catch-up at round three"' -- tests/test_converge.py` prints a line, then `uv run pytest tests/test_converge.py::test_a_run_resumes_from_its_status_log -q` exits 0.
- [ ] 4.4 Add the new `test_an_accepted_blocker_converges_and_a_critical_one_blocks` to `tests/test_converge.py`: row G19's case, then row G20's.
  Verify: `uv run pytest tests/test_converge.py::test_an_accepted_blocker_converges_and_a_critical_one_blocks -q` exits 0.
- [ ] 4.5 Leave every line broken for a red run as it was.
  Verify: `git diff --quiet HEAD -- skills` exits 0.

## 5 — Integrate's merge and git failure

- [ ] 5.1 Add the new `test_merge3_resolves_by_its_table` to `tests/test_integrate.py`: a table of `merge3(base, ours, theirs)` rows, among them row G21's, run through `runpy` as the file's other tests do.
  Verify: `uv run pytest tests/test_integrate.py::test_merge3_resolves_by_its_table -q` exits 0.
- [ ] 5.2 Add the new `test_a_git_failure_after_the_tree_names_its_command` to `tests/test_integrate.py`, built to row G22 beside `test_a_git_failure_names_its_line`.
  Verify: `uv run pytest tests/test_integrate.py::test_a_git_failure_after_the_tree_names_its_command -q` exits 0.
- [ ] 5.3 Leave every line broken for a red run as it was.
  Verify: `git diff --quiet HEAD -- skills` exits 0.

## 6 — The viewer's bind

- [ ] 6.1 Add `HOST` and `server(port)` to `skills/mf-ui/scripts/viewer.py` per [D6](design.md#d6), and have `serve` call `server(port).serve_forever()`.
  Verify: `git grep -n 'ThreadingHTTPServer((HOST, port), Handler)' -- skills/mf-ui/scripts/viewer.py` prints a line.
- [ ] 6.2 Add the new `test_the_viewer_binds_loopback_alone` to `tests/test_viewer.py`, built to row G23. Change the module docstring's `no socket is opened` to say the one test binds port 0 on loopback and closes it.
  Verify: `uv run pytest tests/test_viewer.py::test_the_viewer_binds_loopback_alone -q` exits 0.
- [ ] 6.3 **HALT CHECK** Confirm [D5](design.md#d5): each test of debt card `0120·R3` carries `pytest.mark.slow`. Edit nothing.
  Verify: `git grep -c 'pytest.mark.slow' -- tests/test_viewer.py` prints `4`.
- [ ] 6.4 Leave every line broken for a red run as it was, and `viewer.py` the only source edited.
  Verify: `git diff --quiet HEAD -- skills/mf-converge skills/mf-cut-change skills/mf-integrate skills/mf-ship` exits 0.
