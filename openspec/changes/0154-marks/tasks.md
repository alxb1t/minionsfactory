# Marks — tasks

The phases: pin the marks as they are, add the module, move the callers, give each disagreement one answer, then hold the rule and the record.

## Progress

- [x] 1 — The pin · moderate
- [x] 2 — The module · hard
- [x] 3 — The stations · hard
- [ ] 4 — The fix · hard
- [ ] 5 — The rule and the record · moderate

## 1 — The pin

- [x] 1.1 **HALT CHECK** The conductor still holds the readers [design](design.md#context) says it does.
  Verify: `git grep -q -e '^def _stacked_on' -e '^def _build_halt' -- skills/mf-ship/scripts/conduct.py` exits `0`.
- [x] 1.2 Create `tests/test_mark_pins.py`: the conductor loader of the tests, a planted change folder, a helper that reads a blocking path in a thread, and the cases `c`, `d` and `g` of [D8](design.md#d8), each a test named as [D8](design.md#d8) says.
  Verify: `grep -n -e '^def test_case_c' -e '^def test_case_d' -e '^def test_case_g' tests/test_mark_pins.py` prints a line of each.
- [x] 1.3 Add the cases `h`, `m` and `n` to `tests/test_mark_pins.py`, each as the table of [D8](design.md#d8) says, no worker started.
  Verify: `grep -n -e '^def test_case_h' -e '^def test_case_m' -e '^def test_case_n' tests/test_mark_pins.py` prints a line of each.
- [x] 1.4 Add the cases `r`, `s`, `t` and `w` to `tests/test_mark_pins.py`.
  Verify: `grep -n -e '^def test_case_r' -e '^def test_case_s' -e '^def test_case_t' -e '^def test_case_w' tests/test_mark_pins.py` prints a line of each.
- [x] 1.5 Add the cases `x`, `p`, `a` and `l` to `tests/test_mark_pins.py`: the marks the conductor gained since the models file, `build.simplified`, `plan-check.txt` with the plan-output reader of the converge script, `gate.red` and `replan.mark`.
  Verify: `grep -n -e '^def test_case_x' -e '^def test_case_p' -e '^def test_case_a' -e '^def test_case_l' tests/test_mark_pins.py` prints a line of each.
- [x] 1.6 Add the cases `b`, `e` and `o` to `tests/test_mark_pins.py`: the writers and the removers, the release script's marks through its commands, and the conductor's reads of `release.held`, `release.flag` and `release.pre`.
  Verify: `grep -n -e '^def test_case_b' -e '^def test_case_e' -e '^def test_case_o' tests/test_mark_pins.py` prints a line of each.
- [x] 1.7 Add the pins of the readers, the stand tests, the build's notes, `cut.halt`, the writers, the failed writes and the marks the conductor gained since the models file, `cut.red` among them, as the pin table of [D8](design.md#d8) lists them.
  Verify: `grep -n -e '^def test_pin_readers' -e '^def test_pin_stands' -e '^def test_pin_notes' -e '^def test_pin_cut_halt' -e '^def test_pin_writers' -e '^def test_pin_failed_write' -e '^def test_pin_new_marks' tests/test_mark_pins.py` prints a line of each.
- [x] 1.8 Add the head forms of [D8](design.md#d8) for each mark that holds a `head:`, and the cases of the run's loop: a dependent's `stacked-on` goes before converge and before the release, and a closed build is not closed again.
  Verify: `grep -n -e '^def test_pin_head' -e '^def test_loop_' tests/test_mark_pins.py` prints a line of each.

## 2 — The module

- [x] 2.1 Create `skills/mflib/marks.py` with the names of [D2](design.md#d2), the bounds, the builder of a saved patch's name, and the errors `Broken` and `Unwritten`. It imports `layout` and `statefile` alone.
  Verify: `grep -n -e '^BUILD_DONE = "build.done"' -e '^RELEASE_PRE = "release.pre"' skills/mflib/marks.py` prints a line of each.
- [x] 2.2 Add the parsers of [D2](design.md#d2), each as its copy behaves today ([D3](design.md#d3)): a path read, its own pattern, its own answer to a bad byte.
  Verify: `grep -n -e '^def done_head' -e '^def release_pre' -e '^def plan_check_text' skills/mflib/marks.py` prints a line of each.
- [x] 2.3 Add the stand tests, the time and the notes functions of [D2](design.md#d2), each as the conductor's copy is today.
  Verify: `grep -n -e '^def stands' -e '^def present' -e '^def mtime' -e '^def open_notes' skills/mflib/marks.py` prints a line of each.
- [x] 2.4 Add the text writers, the staged write, the in-place write and the remover of [D2](design.md#d2), each as the conductor's copy is today.
  A function that raises a conductor `Stop` today raises `Broken` or `Unwritten` with the same words ([D3](design.md#d3)).
  Verify: `grep -n -e '^def write_in_place' -e '^def remove' -e '^def halt_text' skills/mflib/marks.py` prints a line of each.
- [x] 2.5 Create `tests/test_marks.py`: a unit case for each function of the module on a planted change folder, holding the copy's behaviour of today, every line of the module covered.
  Verify: `uv run pytest tests/test_marks.py -q` exits `0`.
- [x] 2.6 Add the module's row to `docs/modules.md`: `skills/mflib/marks.py`, layer `home`, naming `layout.py` and `statefile.py`.
  Verify: `uv run pytest tests/test_structure.py -q` exits `0`.

## 3 — The stations

- [x] 3.1 In `skills/mf-ship/scripts/conduct.py` read `build.done`, `build.simplified`, `stacked-on`, `build.halt` and the build's notes through the module; the readers that add git logic keep their names.
  Delete `_done_head`, `_simplified_head`, `_open_notes` and `_note_lines`.
  Verify: `git grep -c -e '^def _done_head' -e '^def _simplified_head' -e '^def _open_notes' -e '^def _note_lines' -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 3.2 In `skills/mf-ship/scripts/conduct.py` read `cut.halt`, `integrate.red`, `integrate.md`, `integrate.settled`, `release.held`, `release.flag`, `release.pre`, `gate.red` and the time of `rescue.md` through the module, the stand test that builds `integrate{end}` among them.
  Delete `_cutter_halt` and `_mtime`; the readers that add meaning keep their names.
  Verify: `git grep -c -e '^def _cutter_halt' -e '^def _mtime' -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 3.3 In `skills/mf-ship/scripts/conduct.py` write each mark through the module: the callers of the in-place writer call the module's, the text writers serve the halt, the close, the plan check and the supervisor, and each mark's unlink calls the module's remover.
  Delete `_write_in_change`. Each caller keeps its answer to a failed write ([D6](design.md#d6)); the remover for the cut's reservation stays.
  Verify: `git grep -c -e '^def _write_in_change' -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 3.4 Give the module's names to each other bare mark name of the conductor, `Run._needs`' action word among them, to the settling test of `skills/mf-integrate/scripts/integrate.py`, and to the reads of `plan-check.txt` and `build.done` in `skills/mf-converge/scripts/converge.py`.
  Name `../../mflib/marks.py` in the line of `skills/mf-converge/SKILL.md` that lists what `converge.py` loads, for those two reads.
  Verify: `git grep -c -E '"(build\.(done|halt|closing|simplified)|build-notes\.md|stacked-on|cut\.(halt|red)|integrate\.(md|red|settled)|release\.(held|flag|pre)|rescue\.md|replan\.mark|plan-check\.txt|gate\.red)"' -- skills/mf-ship/scripts/conduct.py skills/mf-integrate/scripts/integrate.py skills/mf-converge/scripts/converge.py` prints nothing.
- [x] 3.5 In `skills/mf-release/scripts/release.py` name `release.pre`, `release.flag` and the saved patches through the module, the mark's reader calling `release_pre`; its writes and its unlinks keep their path form.
  Verify: `git grep -c -e '^MARK = ' -e '^FLAG = ' -- skills/mf-release/scripts/release.py` prints nothing.
- [x] 3.6 Change the lines by which `tests/test_conduct.py` and `tests/test_mark_pins.py` reach a name the conductor no longer holds: no assert changes. Take from `tests/test_structure.py` each listed exception its rules name as gone, and make `docs/modules.md` name `marks.py` in each row that now loads it.
  Verify: `uv run pytest tests/test_conduct.py tests/test_mark_pins.py tests/test_release.py tests/test_structure.py -n auto -q` exits `0`.

## 4 — The fix

- [ ] 4.1 In `skills/mflib/marks.py` write `head_of` of [D4](design.md#d4), and let each head reader take it in place of its own pattern; the plan-output reader of the converge script compares `done_head` in place of a line.
  Outside a merge the integrate reader reads no head as a red gate on another head; inside an open merge today's reading stands. Delete `done_lines`; its unit case is carried as [design](design.md#tests) says.
  Verify: `grep -n -e '^def head_of' skills/mflib/marks.py` prints a line.
- [ ] 4.2 Write the one `read` of [D5](design.md#d5) and make each parser and `stands` go through it, the time through `lstat`: a stop mark that cannot be read raises `Broken` and the conductor halts its version naming the mark, `conduct.py status` names it and goes on, a pass mark that cannot be read is absent, the stop marks' stand tests call `standing`, `gate_red_text` answers `''` for a file that cannot be read, and the notes keep their own open under the larger bound. The viewer's borrowed reader of `build.halt`, the settling test of the integrate script and the conductor's test of a stranded tip take `Broken` as [D5](design.md#d5) says.
  Verify: `grep -n -e '^def read' skills/mflib/marks.py` prints a line.
- [ ] 4.3 Make `write` the one write: `Run.diagnose`, `Run.merge_in` and `Run.stack` call it. A failed write of `stacked-on` halts its version and not the run; the others keep their answers ([D6](design.md#d6)).
  Delete the in-place write of the module.
  Verify: `git grep -c -e 'def write_in_place(' -- skills/mflib/marks.py` prints nothing.
- [ ] 4.4 Take the release script's writes and unlinks under the change folder's descriptor ([D7](design.md#d7)): the mark and the saved patches through `write`, the drop and the restore through `remove` in place of their `(folder / name).unlink(missing_ok=True)` loops, an `OSError` a halt naming the mark, a patch's free name the first at which nothing stands.
  Verify: `git grep -c -F -e 'name).unlink(' -- skills/mf-release/scripts/release.py` prints nothing.
- [ ] 4.5 Turn each case and pin of the table of [D11](design.md#d11) in `tests/test_mark_pins.py`, `tests/test_marks.py` and `tests/test_conduct.py` to the one side, its name and its fixture kept.
  Verify: `uv run pytest tests/test_mark_pins.py tests/test_marks.py tests/test_conduct.py tests/test_release.py -n auto -q` exits `0`.

## 5 — The rule and the record

- [ ] 5.1 In `tests/test_structure.py` extend the format rule by the marks' names of [D9](design.md#d9): equality with a name of the module, its list `run.py` alone, a planted-breach twin `test_check_formats_fails_on_a_planted_mark_name` and a stale-entry case `test_check_formats_fails_on_a_listed_mark_name_that_is_gone`, the twins taking their own list.
  Verify: `git grep -n -e 'test_check_formats_fails_on_a_planted_mark_name' -e 'test_check_formats_fails_on_a_listed_mark_name_that_is_gone' -- tests/test_structure.py` prints a line of each.
- [ ] 5.2 In `docs/decisions.md` edit D57 where it lives: add `replan.mark`, `cut.red` and `release.discarded.<n>.patch` to its list of marks and name `skills/mflib/marks.py` as the module that writes and parses them, found through `change_dir`.
  Verify: `git grep -n -e 'skills/mflib/marks.py' -- docs/decisions.md` prints a line.
- [ ] 5.3 In `THREAT_MODEL.md` make true the sentences on the change folder: the marks' module reads each mark through no link and its staged write follows none, and the home's surface line lists it.
  Verify: `git grep -n -e 'skills/mflib/marks.py' -- THREAT_MODEL.md` prints a line.
