# Ship speed — tasks

The green gate vouches for more pytest `Verify:` lines, the check judges in groups and has a quick mode, the conductor and the fixer run the quick mode, a clean file with a blocking card not closed is read as malformed, then the record says so.

## Progress

- [x] 1 — The green gate vouches more · hard
- [x] 2 — Cheap first, and `--quick` · hard
- [ ] 3 — The phase check collects · hard
- [ ] 4 — The fixer's check, and a clean file with a card not closed · hard
- [ ] 5 — The words · moderate

## 1 — The green gate vouches more

With the gate green at the tree, `plan_check.py` leaves a pytest `Verify:` that expects exit 0 unrun also with `-n` or `--numprocesses` and `-k` and their values ([D1](design.md#d1)).

- [x] 1.1 **HALT CHECK** `skills/mf-converge/scripts/plan_check.py` still holds its quiet options in `QUIET_OPTIONS`, the only words it vouches beside test modules.
  Verify: `git grep -q -e "^QUIET_OPTIONS" -- skills/mf-converge/scripts/plan_check.py` exits `0`.
- [x] 1.2 In `skills/mf-converge/scripts/plan_check.py` add `_vouched_words(words, root)` and call it from `bare_pytest` in place of the per-word `_vouched` loop: `-n` and `--numprocesses` take a value of digits, `auto` or `logical`, glued or apart; `-k` takes the next word; every other word goes to `_vouched`.
  Verify: `git grep -n -e "^def _vouched_words" -- skills/mf-converge/scripts/plan_check.py` prints a line.
- [x] 1.3 In `tests/test_plan_check.py` add `test_a_green_record_vouches_n_and_k_options`, over a stub `pytest` of its own that answers `--collect-only` with the real one and exits 3 otherwise: on a green record `pytest -q <file> -k test_a`, `pytest -q -n 2 <file>`, `pytest -q --numprocesses=2 <file>` and a case of `<file>` and `<other>`, both test files, with `-n auto` pass unrun; `-k gone`, `-m gone` and `-c other.ini <file>` run and exit 3.
  Verify: `uv run pytest tests/test_plan_check.py -q -k test_a_green_record_vouches_n_and_k_options` exits `0`.

## 2 — Cheap first, and `--quick`

The check judges in the groups of [D2](design.md#d2), a failed group ends it, and `--quick` runs the quick group alone ([D3](design.md#d3)).

- [x] 2.1 **HALT CHECK** `plan_check.py` still collects a bare pytest through `collecting`, called only on a green record.
  Verify: `git grep -q -e "^def collecting" -- skills/mf-converge/scripts/plan_check.py` exits `0`.
- [x] 2.2 In `skills/mf-converge/scripts/plan_check.py` add `is_make(argv)`, `runs_tests(argv)` for a pytest with no `--collect-only`, `wants_collection(command)` for a pytest run whose `Verify:` expects exit 0 and no more, and `collected_none(name, command)` returning `plan: <sub-task> — `<command>` collected no test`.
  Verify: `git grep -n -e "^def wants_collection" -- skills/mf-converge/scripts/plan_check.py` prints a line.
- [x] 2.3 In `skills/mf-converge/scripts/plan_check.py` make `check_verifies` take the keyword `quick: bool = False` and run the quick group, then the long group. The quick group is one `schedule` of the commands that are no pytest run and no `make`, then the collections, results kept by tree but the collections not; a failed collection is the line of `collected_none`, any line ends the check, and `quick` returns there. The long group runs the pytest runs and the `make` commands, the vouched left unrun. `collecting` no longer waits for `gate_green()`.
  Verify: `git grep -n -e "quick: bool" -- skills/mf-converge/scripts/plan_check.py` prints a line.
- [x] 2.4 In `skills/mf-converge/scripts/plan_check.py` make `check` return the lines of `check_boxes`, `check_names`, `check_tests` and `check_corpus` alone, the reads group, when it holds any, before `check_verifies`; with `only` it calls `check_verifies` alone. Make `main` take `--quick`, pass it to `check`, and refuse it beside `--only`: print `plan: cannot check — --quick and --only are alone`, exit 2.
  Verify: `git grep -n -e "--quick" -- skills/mf-converge/scripts/plan_check.py` prints a line.
- [x] 2.5 In `tests/test_plan_check.py` add `test_a_failed_group_ends_the_check_before_the_next`, `test_a_quick_check_runs_no_pytest_and_no_make` and `test_a_collection_that_finds_no_test_is_a_line`, each over a stub `pytest` that logs its calls, and `test_quick_and_only_exit_2`. Turn each pin of `test_a_green_gate_record_passes_a_bare_pytest` whose command collects no test, a missing path or node, a `[` id, `-k gone`, `-m gone`, `-c other.ini <file>` and a file holding no test among them: it now prints `collected no test` and runs no `pytest`.
  Verify: `uv run pytest tests/test_plan_check.py -q` exits `0`.

## 3 — The phase check collects

The conductor runs `--quick` after each phase but the last, beside `gate_built`, and a failure is that phase's check failing ([D4](design.md#d4)).

- [ ] 3.1 **HALT CHECK** The conductor holds no quick run yet.
  Verify: `git grep -q -e "^def _quick_plan" -- skills/mf-ship/scripts/conduct.py` exits `1`.
- [ ] 3.2 In `skills/mf-ship/scripts/conduct.py` add `_quick_plan(primary, change, tree)`, which runs `plan_check.py --quick` through `_boxed` with `_close_base`'s base and returns `plan_check.py --quick exit <code> · <last line>`, or None, and `Run.quick_built(version, tree, phase)`, which on a failure calls `_halt_build` with `phase <N>` and `plan check` and returns `plan check: ` and the evidence. In `Run.advance`, beside the call of `gate_built`, call it once a numbered phase's check passed and a later phase is unticked. `_check_phase` stays as it is.
  Verify: `git grep -n -e "--quick" -- skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 3.3 In `tests/test_conduct.py` add `test_quick_built_fails_a_phase_whose_earlier_search_no_longer_holds`, over a fixture with phases 1, 2 and 3, a ticked task holding a `git grep` that exits 1: after phase 2 it returns `plan check: …` and `build.halt` names `phase 2`; with every check holding it returns None. Add `test_a_build_runs_the_quick_plan_check_after_every_phase_but_the_last`, `_quick_plan` stubbed to log its calls.
  Verify: `uv run pytest tests/test_conduct.py -n auto -q -k quick` exits `0`.

## 4 — The fixer's check, and a clean file with a card not closed

The fixer runs `--quick` ([D5](design.md#d5)), and a clean file beside a blocking card not closed gets one rewrite worker, then a halt ([D6](design.md#d6)).

- [ ] 4.1 **HALT CHECK** The fixer's reference still tells it to run the whole plan check.
  Verify: `git grep -q -e "Run the plan check" -- skills/mf-converge/references/fix.md` exits `0`.
- [ ] 4.2 In `skills/mf-converge/references/fix.md` make the bullet *Run the plan check* run `plan_check.py --change <change-id> --base <base> --quick` before the commit, name what it runs, and say the whole check follows the gate. Keep its lines as blocking cards, its `timed out` rule and the `plan check left:` line.
  Verify: `git grep -n -e "--quick" -- skills/mf-converge/references/fix.md` prints a line.
- [ ] 4.3 In `skills/mf-converge/scripts/converge.py` add `CLEAN_OPEN` beside `NO_OPEN_CARD`, and make `read_findings` return malformed, the reason holding the card's id and Status word, for a file whose `verdict` is `clean`, whose `open_blocking` is `0` and which holds a blocking card whose status is neither `verified` nor `accepted`, judged after the passes of conformance.
  Verify: `git grep -n -e "^CLEAN_OPEN" -- skills/mf-converge/scripts/converge.py` prints a line.
- [ ] 4.4 In `skills/mf-converge/scripts/converge.py` add `REWRITE_CLOSE`, the rewrite worker's prompt for `CLEAN_OPEN`, which lets it set the card's Status or the file's verdict; make `rewrite` send it for that reason and raise `Halt` naming the role, the card and the word of the first read when the rewritten file is malformed for any reason. The mismatch itself sends no card to a fixer and counts no round; the file the worker leaves is read as any file.
  Verify: `git grep -n -e "^REWRITE_CLOSE" -- skills/mf-converge/scripts/converge.py` prints a line.
- [ ] 4.5 In `tests/test_converge.py` add `test_a_clean_file_with_a_card_not_closed_gets_a_rewrite` and `test_a_clean_file_still_mismatched_halts`, the first over a verify file clean with `open_blocking: 0` and R1 `fixed` that the rewrite worker sets `verified`: no fixer runs and the round stays; the second over a worker that leaves it and one that breaks the file another way, each halting with the role, R1 and `fixed`, not `cap reached`.
  Verify: `uv run pytest tests/test_converge.py -n auto -q -k clean_file` exits `0`.

## 5 — The words

The record says what the code now does ([D1](design.md#d1) to [D6](design.md#d6)).

- [ ] 5.1 In `docs/decisions.md` edit D74 where it lives: a green record vouches a pytest with `-n` and `-k`, the check judges in groups and has `--quick`, the conductor runs it after each phase but the last, and the fixer runs it. Edit D78: a clean file beside a blocking card not closed gets its one rewrite worker, then a halt.
  Verify: `git grep -n -e "plan_check.py --quick" -- docs/decisions.md` prints a line.
- [ ] 5.2 In `skills/mf-converge/references/verify.md` say a card's Status is the first word of its Status line, as `verified — <note>`, and a worker sets that word.
  Verify: `git grep -n -e "first word" -- skills/mf-converge/references/verify.md` prints a line.
