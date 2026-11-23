# Cut catches — tasks

Phases: the conductor checks the cut, the rows, a person's phase refused, the declared checks, the build's unplanned file, the records.

## Progress

- [x] 1 — The conductor checks the cut · hard
- [x] 2 — The rows · moderate
- [x] 3 — A person's phase refused · moderate
- [ ] 4 — The declared cut checks · moderate
- [ ] 5 — The build's unplanned file · moderate
- [ ] 6 — The records · moderate

## 1 — The conductor checks the cut

- [x] 1.1 **HALT CHECK** `_check_cut` and `_boxed` stand in `skills/mf-ship/scripts/conduct.py`.
  Verify: `git grep -q -e "def _boxed" -- skills/mf-ship/scripts/conduct.py` exits `0`.
- [x] 1.2 In `tests/test_conduct.py` add `test_cutcheck_passes`, `test_cutcheck_fails_once_then_passes`, `test_cutcheck_fails_twice_halts`, `test_cutcheck_cannot_run_halts` and `test_cutcheck_never_resets_a_rejoin` per [D2](design.md#d2); an autouse fixture there points `CUT_CHECK` at a stub that exits 0, which the new tests override.
  Verify: `uv run pytest tests/test_conduct.py -q -k cutcheck` exits `0`.
- [x] 1.3 In `skills/mf-ship/scripts/conduct.py` add `CUT_CHECK` beside `GATE_RUN` and `_cut_checked`, which runs the checker through `_boxed` in the cut's tree per [D1](design.md#d1).
  Verify: `git grep -q -e "_cut_checked" -- skills/mf-ship/scripts/conduct.py` exits `0`.
- [x] 1.4 In `Run.cutting` of `skills/mf-ship/scripts/conduct.py`, route a failure per [D2](design.md#d2): write `cut.red`, reset and clean the tree, start the cutter again; `PROMPTS["cut"]` gains the tail.
  Verify: `git grep -q -F -e "cut.red" -- skills/mf-ship/scripts/conduct.py` exits `0`.
- [x] 1.5 In `skills/mf-cut-change/SKILL.md` Step 2, add: unattended, a standing `cut.red` holds the failing lines of an earlier cut of this id; read it with the brief.
  Verify: `git grep -q -F -e "cut.red" -- skills/mf-cut-change/SKILL.md` exits `0`.
- [x] 1.6 In `skills/mf-ship/SKILL.md` add that the run checks each cut with the cut's checker and cuts again once, handing the failing lines in `cut.red`.
  Verify: `git grep -q -F -e "cut.red" -- skills/mf-ship/SKILL.md` exits `0`.
- [x] 1.7 In `docs/modules.md` add `cut_check.py` to the names of the `skills/mf-ship/scripts/conduct.py` row, sorted.
  Verify: `uv run pytest tests/test_structure.py -q` exits `0`.

## 2 — The rows

- [x] 2.1 In `tests/test_cut_check.py` add `test_removed_name_in_design_is_refused`, `test_removed_name_with_a_removal_word_holds` and `test_removed_name_in_a_diff_block_is_refused` per [D3](design.md#d3).
  Verify: `uv run pytest tests/test_cut_check.py -q -k removed_name` exits `0`.
- [x] 2.2 In `skills/mf-cut-change/scripts/cut_check.py` add `row_k7` and its id `K7` to `ROWS` and to the rows `check` runs, per [D3](design.md#d3).
  Verify: `git grep -q -e "row_k7" -- skills/mf-cut-change/scripts/cut_check.py` exits `0`.
- [x] 2.3 In `tests/test_cut_check.py` add `test_first_word_on_path_holds`, `test_first_word_of_the_tree_holds` and `test_first_word_naming_nothing_is_refused` per [D3](design.md#d3).
  Verify: `uv run pytest tests/test_cut_check.py -q -k first_word` exits `0`.
- [x] 2.4 In `skills/mf-cut-change/scripts/cut_check.py` add `row_v7` and its id `V7`, in `ROWS` after `V6` and in the rows `check` runs.
  Verify: `git grep -q -e "row_v7" -- skills/mf-cut-change/scripts/cut_check.py` exits `0`.
- [x] 2.5 In `tests/test_cut_check.py` add `test_kexpr_naming_a_head_test_holds`, `test_kexpr_naming_a_planned_test_holds` and `test_kexpr_naming_nothing_is_refused` per [D3](design.md#d3).
  Verify: `uv run pytest tests/test_cut_check.py -q -k kexpr` exits `0`.
- [x] 2.6 In `skills/mf-cut-change/scripts/cut_check.py` add `row_v8` and its id `V8`, in `ROWS` after `V7` and in the rows `check` runs; it skips a command naming no test file, which `V5` owns.
  Verify: `git grep -q -e "row_v8" -- skills/mf-cut-change/scripts/cut_check.py` exits `0`.
- [x] 2.7 In `tests/test_verify_check.py` add `test_searched_range_is_no_range` and `test_oxford_comma_and_e_g_are_refused` per [D4](design.md#d4).
  Verify: `uv run pytest tests/test_verify_check.py -q -k "searched_range or oxford"` exits `0`.
- [x] 2.8 In `skills/mf-cut-change/scripts/verify_check.py` make `unplain` skip a search's patterns in the range test and `after_verb` read a clause and an `e.g.` per [D4](design.md#d4).
  Verify: `uv run pytest tests/test_verify_check.py -q` exits `0`.
- [x] 2.9 In `skills/mf-cut-change/SKILL.md` Step 8, write the ids as `V1`–`V8` and `K1`–`K7`, and name `V8` beside the `-k` rows.
  Verify: `git grep -q -F -e "V8" -- skills/mf-cut-change/SKILL.md` exits `0`.

## 3 — A person's phase refused

- [x] 3.1 In `tests/test_cut_check.py` replace the `I14` defect with `test_person_phase_is_refused`, which finds `I14` among the rows printed; the clean fixture's phase 2 becomes an ordinary rated phase editing `a.py`, and each defect that rewrote its old text follows.
  Verify: `uv run pytest tests/test_cut_check.py -q` exits `0`.
- [x] 3.2 In `skills/mf-cut-change/scripts/cut_check.py` add `PERSON_PHASE`, which `row_i14` fails for each such line, and drop the exemptions of `row_i4` and `row_i12` per [D5](design.md#d5).
  Verify: `git grep -q -e "PERSON_PHASE" -- skills/mf-cut-change/scripts/cut_check.py` exits `0`.
- [x] 3.3 In `skills/mf-cut-change/scripts/verify_check.py` drop the `phases` exemption of `check`; in `tests/test_verify_check.py` flip the `**HUMAN` step to hold the refusal.
  Verify: `uv run pytest tests/test_verify_check.py -q` exits `0`.
- [x] 3.4 In `tests/test_brief_check.py` add `test_brief_phase_marked_for_a_person_halts` and `test_brief_phases_without_one_are_ready` per [D5](design.md#d5).
  Verify: `uv run pytest tests/test_brief_check.py -q -k brief_phase` exits `0`.
- [x] 3.5 In `skills/mf-plan/scripts/brief_check.py` add `person_steps`, which reads `## Phases` and halts each line holding `**HUMAN`, run beside `headings`.
  Verify: `git grep -q -e "person_steps" -- skills/mf-plan/scripts/brief_check.py` exits `0`.
- [x] 3.6 In `skills/mf-build/SKILL.md` and `skills/mf-cut-change/SKILL.md` reword the `I14` row to one sentence: a person's step is no phase, and a `**HUMAN` line fails the cut; its id stays.
  Verify: `git grep -q -F -e "person's step" -- skills/mf-build/SKILL.md` exits `0`, and `git grep -q -F -e "person's step" -- skills/mf-cut-change/SKILL.md` exits `0`.
- [x] 3.7 In `skills/mf-cut-change/SKILL.md` word the rating rule so each `## Progress` line ends with its rating, no exemption, and drop the person's phase from the strongest-tier row.
  Verify: `git grep -q -F -e "line ends" -- skills/mf-cut-change/SKILL.md` exits `0`.
- [x] 3.8 In `skills/mf-plan/SKILL.md` add to the `hard` depth line that a `**HUMAN` phase is refused: a person's step comes after the release.
  Verify: `git grep -q -F -e "**HUMAN" -- skills/mf-plan/SKILL.md` exits `0`.

## 4 — The declared cut checks

- [ ] 4.1 In `tests/test_conduct.py` add `test_cutdeclared_command_passes`, `test_cutdeclared_command_fails_the_cut_check` and `test_cutdeclared_none_runs_nothing` per [D6](design.md#d6).
  Verify: `uv run pytest tests/test_conduct.py -q -k cutdeclared` exits `0`.
- [ ] 4.2 In `skills/mf-ship/scripts/conduct.py` add `_declared_checks`, which reads `Cut checks` from the primary's AGENTS.md, and run each after the checker per [D6](design.md#d6).
  Verify: `git grep -q -F -e "Cut checks" -- skills/mf-ship/scripts/conduct.py` exits `0`.
- [ ] 4.3 In `THREAT_MODEL.md` add `Cut checks:` to the entry points and the surfaces lines that name `Ship tools:`.
  Verify: `git grep -q -F -e "Cut checks" -- THREAT_MODEL.md` exits `0`.
- [ ] 4.4 In `skills/mf-cut-change/SKILL.md` Step 8, say the conductor runs a repository's `**Cut checks:**` after the cut commit, and the cut runs none.
  Verify: `git grep -q -F -e "Cut checks" -- skills/mf-cut-change/SKILL.md` exits `0`.
- [ ] 4.5 In `skills/mf-bootstrap/templates/AGENTS.md.tmpl` add a `**Cut checks:**` line reading `none`, with a note that backticked commands there run over a cut's worktree.
  Verify: `git grep -q -F -e "Cut checks" -- skills/mf-bootstrap/templates/AGENTS.md.tmpl` exits `0`.
- [ ] 4.6 In `docs/decisions.md` edit the decision `The cut writes to the build's input contract`: the conductor runs the cut's checker and each `Cut checks` command; the cut still runs no gate.
  Verify: `git grep -q -F -e "Cut checks" -- docs/decisions.md` exits `0`.

## 5 — The build's unplanned file

- [ ] 5.1 In `skills/mf-build/SKILL.md` Step 2, answer a red `make check` that needs a file no task names by the edit, the file on an `Unplanned:` line of the commit body per [D7](design.md#d7).
  Verify: `git grep -q -F -e "Unplanned:" -- skills/mf-build/SKILL.md` exits `0`.
- [ ] 5.2 In `skills/mf-build/SKILL.md` and `skills/mf-cut-change/SKILL.md` add to the `I6` and `I7` rows that a file a task leaves unnamed is the build's to answer; the ids stay.
  Verify: `git grep -q -F -e "unnamed" -- skills/mf-build/SKILL.md` exits `0`, and `git grep -q -F -e "unnamed" -- skills/mf-cut-change/SKILL.md` exits `0`.
- [ ] 5.3 In `skills/mf-converge/references/worker.md` add the `unplanned-file` pass to conformance's table, graded per [D7](design.md#d7).
  Verify: `git grep -q -F -e "unplanned-file" -- skills/mf-converge/references/worker.md` exits `0`.

## 6 — The records

- [ ] 6.1 In `docs/decisions.md` add `### D89 · The conductor checks the cut` after the decision on closing the halts a line can, and its line in the group index.
  Verify: `git grep -q -F -e "D89" -- docs/decisions.md` exits `0`.
- [ ] 6.2 In `docs/decisions.md` edit the decision `A mechanical step is a script`: the conductor runs the checker, and the new rows `V7`, `V8` and `K7`.
  Verify: `git grep -q -F -e "V7" -- docs/decisions.md` exits `0`.
- [ ] 6.3 In `docs/decisions.md` edit the decision `A run heals its own halts`: the cut refuses a person's phase, and the conductor still reads one of a version cut before.
  Verify: `git grep -q -F -e "cut before" -- docs/decisions.md` exits `0`.
