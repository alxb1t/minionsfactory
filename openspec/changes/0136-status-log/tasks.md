# Status log — tasks

The phases: pin the region, write the modules, move the stations, give the helpers their callers, fix each copy to one side, then the rule and the record. The cases are [the pin](design.md#the-pin); the arguments are [the differences](design.md#the-differences).

## Progress

- [x] 1 — The pin · hard
- [ ] 2 — The modules · hard
- [ ] 3 — The stations · hard
- [ ] 4 — The helpers · moderate
- [ ] 5 — The fix · hard
- [ ] 6 — The rule and the record · hard

## 1 — The pin

Tests only, each green on the code as it stands ([D2](design.md#d2)).

- [x] 1.1 **HALT CHECK** The FIFO cases need the guards' `O_NONBLOCK` to stand in converge's `_text` and the viewer's `read_part`.
  Verify: `git grep -n -e "O_NONBLOCK" -- skills/mf-converge/scripts/converge.py skills/mf-ui/scripts/viewer.py` prints a line of each file.
- [x] 1.2 Add `tests/test_staged_writes.py`: a table of the staged writes of `stamp.py`, `bundle.py`, `debt_match.py`, `open_cards.py`, `skip_stub.py`, `gate_run.py` and `plan_check.py`, each row an adapter, and cases A, B, C and D over it.
  Verify: `uv run pytest tests/test_staged_writes.py -q` exits 0.
- [x] 1.3 Add case E to `tests/test_gate_run.py` and case F to `tests/test_plan_check.py`.
  Verify: `uv run pytest tests/test_gate_run.py tests/test_plan_check.py -q -k "case_e or case_f"` exits 0.
- [x] 1.4 Add case G to `tests/test_skip_stub.py`. Add cases H and I, and one test with `fifo` in its name for each of converge's `_text` and the viewer's `read_part`, to a new `tests/test_log_reads.py`; each FIFO test runs its read in a thread it joins with a ten-second timeout.
  Verify: `uv run pytest tests/test_skip_stub.py tests/test_log_reads.py -q -k "case_g or case_h or case_i or fifo"` exits 0.
- [x] 1.5 Add cases K and L to `tests/test_stamp.py`, and cases M, N and P to `tests/test_converge.py`.
  Verify: `uv run pytest tests/test_stamp.py tests/test_converge.py -q -k "case_k or case_l or case_m or case_n or case_p"` exits 0.
- [x] 1.6 Add cases J, O, Q, R and S to `tests/test_conduct.py`; case O is a twin line of the existing `stage_of` lock test.
  Verify: `uv run pytest tests/test_conduct.py -q -k "case_j or case_o or case_q or case_r or case_s"` exits 0.
- [x] 1.7 Add `tests/test_status_log_copies.py`: a link at the log, an event outside the spec's form, a missing log, each in the stamp, converge and the conductor as they stand, and a halt whose detail holds a line break.
  Verify: `uv run pytest tests/test_status_log_copies.py -q` exits 0.

## 2 — The modules

The modules and the layout's name, beside no caller ([D1](design.md#d1), [D3](design.md#d3)).

- [ ] 2.1 In `skills/mflib/layout.py` add `STATUS_LOG = "status_log.md"` and `status_log(primary, change)`, which returns `change_dir(primary, change) / STATUS_LOG`, with its docstring example; add its case to `tests/test_layout.py`, named `test_the_layout_names_the_log_of_a_change`.
  Verify: `uv run pytest tests/test_layout.py -q -k names_the_log_of_a_change` exits 0.
- [ ] 2.2 Write `skills/mflib/statefile.py` as [the modules](design.md#the-modules) names it, with every value of [the differences](design.md#the-differences) and `os.open` called as `os.open`. Write `tests/test_statefile.py`: a case for each argument value, a FIFO and a link at a read, and a file made at `.tmp` between the clear and the create.
  Verify: `uv run pytest tests/test_statefile.py -q` exits 0.
- [ ] 2.3 Write `skills/mflib/statuslog.py` as [the modules](design.md#the-modules) names it, path-based, importing `layout` and `statefile` as `from . import …`, each difference as today's code has it, and its read of the log taking `guard=False` as the stamp's read does. Write `tests/test_statuslog.py`: `NAMES` as a literal list of the spec's event names, a case for each function, each `extent`, and `names_lock` on `.minions/debt.lock`, `.minions/backlog.lock` and a bare `debt.lock`.
  Verify: `uv run pytest tests/test_statuslog.py -q` exits 0.
- [ ] 2.4 Add the `home` row of `skills/mflib/statefile.py` to `docs/modules.md`, in path order, its `names` cell `—`.
  Verify: `git grep -c -e "statefile" -- docs/modules.md` exits 0.
- [ ] 2.5 Add the `home` row of `skills/mflib/statuslog.py` to `docs/modules.md`, in path order, its `names` cell `layout.py, statefile.py`.
  Verify: `git grep -c -e "statuslog" -- docs/modules.md` exits 0.

## 3 — The stations

The move: no assert changes, only the line by which a test reaches a name ([D3](design.md#d3), [D10](design.md#d10), [D13](design.md#d13)).

- [ ] 3.1 In `skills/mf-converge/scripts/stamp.py` add the seed line and make `main` check its usage and call `mflib.statuslog.command`: delete `stamp`, `read`, `write`, `_ends`, `_now`, `LOCKS` and `Stop`, and keep `USAGE`, the arguments, the printed lines and the exit codes.
  Verify: `git grep -n -e "^LOCKS" -- skills/mf-converge/scripts/stamp.py` prints nothing.
- [ ] 3.2 In `tests/test_stamp.py` reach the clock through `statuslog._now` and the swapped-folder seam, the loaded script's `stamp`, through `statuslog.insert`.
  Verify: `uv run pytest tests/test_stamp.py -q` exits 0.
- [ ] 3.3 In `skills/mf-converge/scripts/converge.py` delete `STAMP`, `EVENT`, `LOCKED`, `Event` and `Run`; make `stamp` call `statuslog.command`, `open_run` call `statuslog.open_run`, `latest` call `statuslog.latest`, `answered_amends` walk the log with `is_heading`, `mark_of` and `parse_event`, `Context.log` call `mflib.layout.status_log`, and every use of `Event`, `Run` and the lock test name the module's. Re-point the lines of `tests/test_converge.py` and the phase 1 files that reach `STAMP` or the stamp's `Stop` to `mflib.statuslog`.
  Verify: `git grep -n -e "STAMP\[" -- skills/mf-converge/scripts/converge.py` prints nothing.
- [ ] 3.4 In `skills/mf-ship/scripts/conduct.py` delete `STAMP_SCRIPT`; keep `_run_end`, `_run_marked`, `_run_started`, `_is_event`, `_buried_done` and `_restamp` as wrappers that read the log with `read_text` as today and call `mflib.statuslog`, `_restamp` through `command`, which prints as the stamp's `main` did; `stage_of` tests a halt with `names_lock`.
  Verify: `git grep -n -e "STAMP_SCRIPT" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 3.5 In `docs/modules.md` set the `names` cells: `stamp.py` names `statuslog.py`; `converge.py` and `conduct.py` lose `stamp.py` and gain `statuslog.py`. In `skills/mf-converge/SKILL.md` replace the mention of `stamp.py` among the scripts converge loads with `../../mflib/statuslog.py`.
  Verify: `uv run pytest tests/test_structure.py tests/test_skills.py -q` exits 0.
- [ ] 3.6 In `tests/test_structure.py` remove the pair `("stamp.py", ".minions/")` from `LAYOUT_SITES`.
  Verify: `git grep -n -F '"stamp.py", ".minions/"' -- tests/test_structure.py` prints nothing.

## 4 — The helpers

The writers and readers outside the log take `statefile`, each keeping its check before the write, its bound and its error text ([D3](design.md#d3)).

- [ ] 4.1 In `skills/mf-converge/scripts/bundle.py`, `debt_match.py` and `open_cards.py` add the seed line and make `write` call `statefile.write(refuse_link=True, remove="any")`, word each `WriteFailed` as its own `Stop` text, and drop the no-follow flag from the write's flags.
  Verify: `git grep -n -e "statefile.write" -- skills/mf-converge/scripts/bundle.py skills/mf-converge/scripts/debt_match.py skills/mf-converge/scripts/open_cards.py` prints a line of each file.
- [ ] 4.2 In `skills/mf-converge/scripts/skip_stub.py` add the seed line; make `write` call `statefile.write(remove="never")` after its own check, with its `could not be written` text, and its read of the file it replaces, still after `path.is_file()`, call `statefile.read` with `guard` left true.
  Verify: `git grep -n -e "statefile" -- skills/mf-converge/scripts/skip_stub.py` prints a line.
- [ ] 4.3 In `skills/mf-converge/scripts/gate_run.py` make `write_record` call `statefile.write(remove="never")`: a `create` failure keeps its `could not be created` text, a `replace` failure raises the `OSError` as today. In `skills/mf-converge/scripts/plan_check.py` add the seed line and make `keep` call it under its `suppress`.
  Verify: `git grep -n -e "statefile.write" -- skills/mf-converge/scripts/gate_run.py skills/mf-converge/scripts/plan_check.py` prints a line of each file.
- [ ] 4.4 In `skills/mf-converge/scripts/converge.py` make `_text` call `statefile.read`, a missing file `None`; in `skills/mf-ui/scripts/viewer.py`, which already carries the seed line, make `read_part` call `statefile.read(limit=PART, tail=tail)`, any `OSError` `None`.
  Verify: `git grep -n -e "statefile.read" -- skills/mf-converge/scripts/converge.py skills/mf-ui/scripts/viewer.py` prints a line of each file.
- [ ] 4.5 In `skills/mf-ship/scripts/conduct.py` make `_bounded` call `statefile.read_bytes(limit=READ_BYTES + 1, folder=fd)`, `None` over `READ_BYTES`, and `_folder_fd` call `statefile.folder`.
  Verify: `git grep -n -e "statefile" -- skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 4.6 In `docs/modules.md` add `statefile.py` to the `names` cell of each script that now imports it, and in `skills/mf-converge/SKILL.md` name `../../mflib/statefile.py` beside the module.
  Verify: `uv run pytest tests/test_structure.py tests/test_skills.py -q` exits 0.
- [ ] 4.7 In `skills/mf-converge/scripts/bundle.py`, `debt_match.py` and `open_cards.py` no `O_NOFOLLOW` stands.
  Verify: `git grep -n -e "O_NOFOLLOW" -- skills/mf-converge/scripts/bundle.py skills/mf-converge/scripts/debt_match.py skills/mf-converge/scripts/open_cards.py` prints nothing.

## 5 — The fix

Each copy to one side, in the order of [D4](design.md#d4) to [D8](design.md#d8); the phase 1 cases whose copies differed turn to the one side.

- [ ] 5.1 In `skills/mflib/statefile.py` delete `remove` and `guard`: the staged file is removed on any failure and every read is guarded. Pass `refuse_link=True` from `statuslog.stamp` and `skip_stub.py`. Turn the rows of `tests/test_staged_writes.py`, `tests/test_statefile.py` and `tests/test_log_reads.py` that held a second value.
  Verify: `uv run pytest tests/test_staged_writes.py tests/test_statefile.py tests/test_log_reads.py tests/test_skip_stub.py -q` exits 0.
- [ ] 5.2 In `skills/mf-converge/scripts/gate_run.py` make a failed record print `gate: green — unrecorded, <name>.tmp could not be created` for a create, or `gate: green — unrecorded, <name> could not be replaced` for a rename, `<name>` the record's file name, and exit 0. Turn case D's `gate_run.py` row and case E.
  Verify: `uv run pytest tests/test_gate_run.py tests/test_staged_writes.py -q` exits 0.
- [ ] 5.3 In `skills/mflib/statuslog.py` delete `extent`: a run is its heading to the next heading, blank lines skipped. `mark_of` strips and returns `None` with no mark, `marked` calls it; `parse_event` takes an optional detail, and `is_event` and `ends` call it. Turn cases M, Q and R and the copies' rows of `tests/test_status_log_copies.py`.
  Verify: `uv run pytest tests/test_statuslog.py tests/test_converge.py tests/test_status_log_copies.py -q` exits 0.
- [ ] 5.4 In `skills/mf-ship/scripts/conduct.py` make the readers of the log read through `statefile.read`: a bad byte is replaced, and a link or a FIFO raises `Stop(1, "conduct: halt — .minions/changes/<change-id>/status_log.md is a link")` naming the path. Add a test with `status_log_link` in its name: `stage_of` raises it, and `conduct.py status` prints it and exits 1; a missing log keeps its answer.
  Verify: `uv run pytest tests/test_conduct.py -q -k "case_q or case_r or case_s or status_log_link"` exits 0.
- [ ] 5.5 In `skills/mflib/statuslog.py` give `stamp`, `command` and `open_run` an optional `folder` descriptor, held across the read, the create and the rename; with none, they open the log's parent by pathname and make nothing, so a missing log keeps its text. The parser replaces a bad byte and the writer refuses one with exit 2. Converge and `_restamp` pass `statefile.folder(run_dir, CHANGES, change)`. Add `tests/test_statuslog.py`'s case for card 0109·S1: the change folder swapped for a link right after the read leaves the outside file untouched.
  Verify: `uv run pytest tests/test_statuslog.py tests/test_stamp.py tests/test_converge.py -q` exits 0.
- [ ] 5.6 In `skills/mflib/statuslog.py` make `stamp` flatten each run of line breaks in an event to one space. Turn the multi-line halt of `tests/test_status_log_copies.py`, and add a test with `line_break` in its name for the re-run of a halt that carried git's stderr.
  Verify: `uv run pytest tests/test_statuslog.py tests/test_status_log_copies.py -q -k "line_break or flatten"` exits 0.

## 6 — The rule and the record

The format rule, then the record where each fact lives ([D9](design.md#d9), [D12](design.md#d12)).

- [ ] 6.1 In `tests/test_structure.py` add `FORMAT_SITES`, holding `status_log.md` and `## Run` each for `viewer.py`, `review_metrics.py` and `run.py`, a `_format_name` that returns `status_log.md` for an equal string and `## Run` for a string that contains it, and `check_formats`, held by the structure test. Its cases, each with `format` in its name: a planted `status_log.md`; a planted `## Run` in a longer string; a listed site that is gone; the module passing; a docstring passing.
  Verify: `uv run pytest tests/test_structure.py -q -k format` exits 0.
- [ ] 6.2 In `docs/decisions.md` amend D78 to say its status log is written through `skills/mflib/statuslog.py`; D83 to count the format names spelled outside `skills/mflib/` among what the gate holds; D57 to say `status_log.md` is written and parsed by `statuslog.py`, found through `change_dir`.
  Verify: `git grep -n -e "statuslog" -- docs/decisions.md` prints a line.
- [ ] 6.3 In `THREAT_MODEL.md` make the sentence on a conductor's writes true to what remains: the status log is written by `skills/mflib/statuslog.py` through a descriptor held across its read and its write; the other in-process writes of a change's folder follow no link by their own checks until their formats move. Add the formats to the shared home's surface sentence.
  Verify: `git grep -n -e "statuslog" -- THREAT_MODEL.md` prints a line.
- [ ] 6.4 In `docs/recipes.md` add to the state-file recipe's rule line `check_formats` and `FORMAT_SITES`, and a paragraph on writing a staged file through `statefile` and the status log through `statuslog`.
  Verify: `git grep -n -e "check_formats" -- docs/recipes.md` prints a line.
- [ ] 6.5 In `docs/modules.md` say in the `home` layer's line that the home holds the formats of the state files.
  Verify: `git grep -n -e "formats of the state files" -- docs/modules.md` prints a line.
