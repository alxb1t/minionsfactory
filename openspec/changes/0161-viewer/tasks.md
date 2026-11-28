# Viewer — tasks

The phases pin the viewer's reads on today's side, add the module parsers, move the viewer and converge onto them, turn the settled readings, and write the record.

## Progress

- [x] 1 — The pin · moderate
- [x] 2 — The module · moderate
- [x] 3 — The readers · moderate
- [ ] 4 — The fix · hard
- [ ] 5 — The record · moderate

## 1 — The pin

- [x] 1.1 Add `tests/test_viewer_pins.py` with its harness and the group A cases of [the cases](design.md#the-cases): `runpy` loaders of the viewer and converge, a real git repo with a linked worktree, a fake `ps` first on `PATH`, and writers of a run log, a status log, a findings file, a claim and a queue entry, as `tests/test_viewer.py` builds them.
  A case reaches the code through `project`, `projects` or `read_part`; start no worker, and mark a case over `1` s `slow` ([D27](design.md#d27)).
  Verify: `uv run pytest tests/test_viewer_pins.py -n auto -q` exits `0`.
- [x] 1.2 Add the group B cases of [the cases](design.md#the-cases) to `tests/test_viewer_pins.py`: the log's stem, the clock, the days and the lines kept, each through `project(primary)`, with a first event of `00:00:01` in a log stamped `23:59:00` pinned on the stem's day.
  Name the case of that first event `test_l6_the_first_event_is_on_the_stems_day` ([D40](design.md#d40)); every other stem holds its first event less than `12` hours before the stem's time.
  Verify: `uv run pytest tests/test_viewer_pins.py -n auto -q` exits `0`.
- [x] 1.3 Add the group H cases and the run log's shapes of [the cases](design.md#the-cases) to `tests/test_viewer_pins.py`: `runlog.events` and `runlog.newest` through their public functions, a log that is a link, a folder, empty or a FIFO, and a claim that is a file, a link or a FIFO.
  Name the case of `20261399-250000.md` `test_l1_a_name_that_is_no_date_is_listed`; run a FIFO in a child with a timeout, marked `slow`.
  Verify: `uv run pytest tests/test_viewer_pins.py -n auto -q` exits `0`.
- [x] 1.4 Add the groups C, D, E and G of [the cases](design.md#the-cases) to `tests/test_viewer_pins.py`: the spent fields, the heading, the mark, `fixing`, the round, the cause, and converge's `_spent` through `runpy`.
  Add a case whose top line is a `halt` holding ` · fix — sent`, shown `fixing` today, named `test_v4_a_halt_that_holds_the_words_shows_fixing`.
  Verify: `uv run pytest tests/test_viewer_pins.py -n auto -q` exits `0`.
- [x] 1.5 Add the group I cases and the heading shapes of [the cases](design.md#the-cases) to `tests/test_viewer_pins.py`: `statuslog.is_heading`, `newest`, `latest` and `parse_event`, and the viewer's reading of each heading shape.
  Name the viewer cases of a mark of several words, a trailing space, a missing date and CRLF `test_s1_…`, `test_s2_…` and `test_s5_…`, and the case of words before `verdicts` `test_v6_…`.
  Verify: `uv run pytest tests/test_viewer_pins.py -n auto -q` exits `0`.
- [x] 1.6 Add the shapes of the status log and the findings files of [the cases](design.md#the-cases) to `tests/test_viewer_pins.py`: a link, a dangling link, a folder, a FIFO in a child, a bad byte, an empty file, `262144` bytes before and after the text, CRLF and a missing file.
  Mark a FIFO case `slow`; add the frontmatter case of quoted values.
  Verify: `uv run pytest tests/test_viewer_pins.py -n auto -q` exits `0`.
- [x] 1.7 Add the slice P cases of [the cases](design.md#the-cases) to `tests/test_viewer_pins.py`: `projects` over rows and the record, the shapes of `repos`, a queue entry through `project(primary)["queue"]`, and the run log line of `Converge Skipped`.
  Name each case of a record that is a link, a dangling link, a folder or a FIFO `test_p1_…`, of a bad byte or a NUL byte, the record `x\x00y` among them, `test_p2_…` and of a file over the bound, the records of `262144` blank lines and of blanks up to `262141` bytes among them, `test_p3_…`, of a relative line `test_p4_…` and of a linked `.minions` `test_p6_…`; run a FIFO record in a child, marked `slow`.
  Verify: `uv run pytest tests/test_viewer_pins.py -n auto -q` exits `0`.

## 2 — The module

- [x] 2.1 Add `lines(path, cut)` to `skills/mflib/statefile.py`: the viewer's `read_lines` as it is, each line of a regular file cut at `cut` characters, nothing for a link, a FIFO, a folder or a missing file ([D4](design.md#d4), [D30](design.md#d30)).
  Add `test_lines_cut_a_long_line_and_drop_its_rest` and `test_lines_read_nothing_from_what_is_no_regular_file` to `tests/test_statefile.py`, the open-descriptor count held.
  Verify: `uv run pytest tests/test_statefile.py -k test_lines -q` exits `0`.
- [x] 2.2 Add `timed(stem, lines)` and `cause(detail)` to `skills/mflib/runlog.py` as the viewer reads them today: a step back of the clock between events is a day on, the first event is on the stem's day, the cause is any word of lower-case letters and hyphens at the end.
  Add `test_timed_a_step_back_is_a_day_on` and `test_cause_reads_a_word_off_the_list_too` to `tests/test_runlog.py`, each stem with its first event less than `12` hours before the stem's time.
  Verify: `uv run pytest tests/test_runlog.py -k "test_timed or test_cause" -n auto -q` exits `0`.
- [x] 2.3 Add `Section` and `runs(text)` to `skills/mflib/statuslog.py`: every run of a log's text, newest first, each its heading's number, mark and events, a line that starts `## Run` a heading as `is_heading` reads it, no date and no clock ([D41](design.md#d41)).
  Add `test_runs_give_each_run_newest_first` and `test_runs_read_running_as_a_heading_with_no_number` to `tests/test_statuslog.py`.
  Verify: `uv run pytest tests/test_statuslog.py -k test_runs -q` exits `0`.
- [x] 2.4 Add `FALLBACK`, `FAILED`, `spent`, `verdicts_line` and `Verdicts` to `skills/mflib/statuslog.py`, and `verdicts(line)`, which finds the `verdicts` text anywhere in a line as the viewer does ([D29](design.md#d29), [D34](design.md#d34)).
  Add `test_spent_words_a_string_fallback_as_failed` and `test_verdicts_read_a_line_the_writer_wrote` to `tests/test_statuslog.py`, the text of `spent` as converge writes it today.
  Verify: `uv run pytest tests/test_statuslog.py -k "test_spent or test_verdicts" -q` exits `0`.
- [x] 2.5 Add `repos(path)` to `skills/mflib/kept.py`, reading the record as the viewer's `projects` does today: the first `REPOS_BOUND` bytes, each line stripped, a blank one skipped, nothing for a link, a FIFO or a missing file ([D35](design.md#d35)).
  Add `test_repos_list_each_line_stripped`, `test_repos_list_is_empty_for_a_missing_file`, `test_repos_list_is_empty_for_a_link` and `test_repos_list_is_empty_for_a_fifo` to `tests/test_kept.py`, the FIFO in a child with a timeout, marked `slow`.
  Verify: `uv run pytest tests/test_kept.py -n auto -q` exits `0`.
- [x] 2.6 No script calls the new functions yet, and no row of the map changes.
  Verify: `git grep -c -e "statuslog.runs" -e "statefile.lines" -e "kept.repos" -e "runlog.timed" -- skills/mf-ui skills/mf-converge skills/mf-ship` prints nothing; `uv run pytest tests/test_statuslog.py tests/test_status_log_copies.py tests/test_runlog.py tests/test_kept.py tests/test_structure.py -n auto -q` exits `0`.

## 3 — The readers

- [x] 3.1 Re-point the lines by which a test reaches a moved name, and no assert: the `read_lines` lines of `tests/test_viewer.py` and the `read_lines` case of `tests/test_viewer_pins.py` take `statefile.lines` with `PART`, and the case of converge's `_spent` takes `statuslog.spent` ([D1](design.md#d1)).
  The case of `_spent` passes its models, tokens and fallback as plain values and asserts the same text.
  Verify: `uv run pytest tests/test_viewer.py tests/test_viewer_pins.py -n auto -q` exits `0`.
- [x] 3.2 In `skills/mf-ui/scripts/viewer.py` read the run log through `statefile.lines` with `PART`, `runlog.parse` and `runlog.timed`, and the newest log through `runlog.newest`; the viewer's `read_lines`, `EVENT` and `last_log` subscripts are removed ([D31](design.md#d31)).
  No assert changes: the midnight case and the long-line case pass as phase 1 wrote them; import each module the task calls under the seed line.
  Verify: `git grep -c -F -e "read_lines" -e "conduct[\"EVENT\"]" -- skills/mf-ui/scripts/viewer.py` prints nothing; `uv run pytest tests/test_viewer.py tests/test_viewer_pins.py -n auto -q` exits `0`.
- [x] 3.3 In `skills/mf-ui/scripts/viewer.py` read the status log through `layout.status_log`, a role's spent fields through `statuslog.verdicts` per line, the first line of a role winning, and a findings file's fields through `findings.frontmatter`; `VERDICT`, `SPENT` and the converge subscripts of `FALLBACK` and `FAILED` are removed.
  `RUN_HEADING` and `fixing` stay as they are until phase 4; import each module the task calls under the seed line.
  Verify: `git grep -c -e "VERDICT" -e "SPENT" -e "status_log.md" -- skills/mf-ui/scripts/viewer.py` prints nothing; `uv run pytest tests/test_viewer.py tests/test_viewer_pins.py -n auto -q` exits `0`.
- [x] 3.4 In `skills/mf-ui/scripts/viewer.py` read the queue through `queue.entries` and `queue.is_wait`, a halt's cause through `runlog.cause`, and the record through `kept.repos`, the `.minions` check through `layout.run_dir`; the `conduct["_cuts"]` and `conduct["_frontmatter"]` subscripts and `CAUSE` are removed ([D3](design.md#d3), [D8](design.md#d8)).
  Import each module the task calls under the seed line.
  Verify: `git grep -c -F -e "conduct[\"_cuts\"]" -e "conduct[\"_frontmatter\"]" -e "CAUSE" -- skills/mf-ui/scripts/viewer.py` prints nothing; `uv run pytest tests/test_viewer.py tests/test_viewer_pins.py tests/test_kept_pins.py -n auto -q` exits `0`.
- [x] 3.5 In `skills/mf-converge/scripts/converge.py` write the `verdicts` line through `statuslog.verdicts_line` and the `pickup` line through `statuslog.spent`; `_spent`, `FALLBACK` and `FAILED` are removed.
  The text of both lines is as it was.
  Verify: `git grep -c -e "_spent" -e "FALLBACK" -e "FAILED" -- skills/mf-converge/scripts/converge.py` prints nothing; `uv run pytest tests/test_converge.py -k "verdicts or fallback or findings_file or stamp or status or log" -n auto -q` exits `0`.
- [x] 3.6 In `tests/test_structure.py` drop the entries: the viewer's `status_log.md` of `FORMAT_SITES`, its `.minions` of `LAYOUT_SITES`, and its `_cuts` and `_frontmatter` of `PRIVATE_REACH`; keep both loads and its `## Run` ([D32](design.md#d32)).
  In `docs/modules.md` give the viewer's row `findings.py`, `kept.py`, `queue.py`, `runlog.py` and `statuslog.py` beside its names, in order.
  Verify: `uv run pytest tests/test_structure.py -q` exits `0`.
- [x] 3.7 Hold every assert of the conductor's and the pins' tests: converge's lines and the viewer's reads moved, `conduct.py` did not.
  Verify: `uv run pytest tests/test_conduct.py -k "frontmatter or log_verify or cut_halt or queued_cut or a_cut or cap_status or cap_writes or rejoin or halt_is or run_log or spent or status_log or newest" -n auto -q` exits `0`.

## 4 — The fix

- [ ] 4.1 In `skills/mflib/runlog.py` make a first event a day on when its clock is `12` hours or more earlier than the time in the log's stamp ([D25](design.md#d25)), and make a name that is no real date no log in the list and the newest ([D21](design.md#d21)); a `-N` suffix on a real stamp stays.
  Turn `test_l6_the_first_event_is_on_the_stems_day` and `test_l1_a_name_that_is_no_date_is_listed` in `tests/test_viewer_pins.py`, and write `test_first_event_late_in_the_day_is_a_day_on` and `test_a_name_that_is_no_date_is_passed_over_by_the_list` in `tests/test_runlog.py`.
  Verify: `uv run pytest tests/test_runlog.py tests/test_viewer_pins.py -n auto -q` exits `0`; `uv run pytest tests/test_mark_pins.py tests/test_queue_pins.py -k "case_n_the_trim or case_s_stack or take_requests_reads" -n auto -q` exits `0`.
- [ ] 4.2 In `skills/mflib/kept.py` read `repos` through the bounded read of `REPOS_BOUND` and raise `Broken` for a link, a FIFO, a folder, a bad byte, a file over the bound and a line holding a NUL byte; a missing file is no line ([D22](design.md#d22), [D35](design.md#d35)).
  Turn `test_repos_list_is_empty_for_a_link` and `test_repos_list_is_empty_for_a_fifo` in `tests/test_kept.py` to `…_raises_broken_for_a_link` and `…_for_a_fifo`, write `test_repos_list_raises_broken_for_a_nul_line`, turn `test_p1_…`, `test_p2_…` and `test_p3_…` in `tests/test_viewer_pins.py` to `projects` raising `Broken`, and split the viewer's cases out of the two `repos` readers' cases in `tests/test_kept_pins.py` to raise `Broken` ([D38](design.md#d38)).
  Verify: `uv run pytest tests/test_kept.py tests/test_kept_pins.py tests/test_viewer.py tests/test_viewer_pins.py -n auto -q` exits `0`.
- [ ] 4.3 In `skills/mf-ui/scripts/viewer.py` let `projects` take a record of None as no record, add `snapshot(now, record, rows, memory, read)`, which ticks `ui.toml`'s projects alone and puts the row named `repos` first, built as `_unread` builds a project's, when `projects` raises `Broken`, and have the poll of `serve` call it ([D35](design.md#d35)).
  Write `test_snapshot_shows_one_row_for_a_record_that_cannot_be_read` in `tests/test_viewer_pins.py`: a record holding `x`, a NUL byte and `y`, one `ui.toml` project, a stand-in `read`; the row is first, says `repos could not be read`, and the project follows.
  Verify: `uv run pytest tests/test_viewer.py tests/test_viewer_pins.py -n auto -q` exits `0`.
- [ ] 4.4 In `skills/mf-ui/scripts/viewer.py` list no project for a line of `repos` that is no absolute path and none whose `.minions` is a link, the record's paths and `ui.toml`'s alike; a path through a linked parent folder still lists ([D36](design.md#d36)).
  Turn `test_p4_…` and `test_p6_…` in `tests/test_viewer_pins.py`.
  Verify: `uv run pytest tests/test_viewer.py tests/test_viewer_pins.py -n auto -q` exits `0`.
- [ ] 4.5 In `skills/mflib/statuslog.py` make `verdicts` take an event of the module's form named `verdicts`, its fallback read from the detail's own fields, and in `skills/mf-ui/scripts/viewer.py` read the newest run, its number and mark, `fixing` and each role's spent fields from `statuslog.runs`; `RUN_HEADING` and its `heading[2]` read are removed ([D33](design.md#d33), [D34](design.md#d34)).
  Turn `test_s1_…`, `test_s2_…`, `test_s5_…`, `test_v4_…` and `test_v6_…` in `tests/test_viewer_pins.py`, and the phase 2 cases of `verdicts` in `tests/test_statuslog.py` to events.
  Verify: `git grep -c -F -e "heading[2]" -- skills/mf-ui/scripts/viewer.py` prints nothing; `uv run pytest tests/test_statuslog.py tests/test_viewer.py tests/test_viewer_pins.py -n auto -q` exits `0`.
- [ ] 4.6 In `tests/test_structure.py` drop the viewer's `## Run` entry of `FORMAT_SITES`.
  Verify: `uv run pytest tests/test_structure.py -q` exits `0`.
- [ ] 4.7 Hold every assert of the readings kept as today: a role's older `verdicts` line still shows ([D19](design.md#d19)), and no assert of `tests/test_viewer.py` changed; the conductor reads `runlog` too.
  Verify: `uv run pytest tests/test_conduct.py -k "frontmatter or log_verify or cut_halt or queued_cut or a_cut or cap_status or cap_writes or rejoin or halt_is or run_log or spent or status_log or newest" -n auto -q` exits `0`; `uv run pytest tests/test_mark_pins.py tests/test_queue_pins.py -k "case_n_the_trim or case_s_stack or take_requests_reads" -n auto -q` exits `0`.

## 5 — The record

- [ ] 5.1 In `docs/decisions.md` edit where a sentence is no longer true: D57 names `statuslog.runs`, the spent text and the `verdicts` line, `runlog`'s moment and cause and `kept.repos`; D82 says the viewer reads the formats through the home modules and shows a `repos` that cannot be read; D83's list of formats and its Accepts name this version's entries ([D32](design.md#d32)).
  D83's sentence that the lists only shrink is unchanged.
  Verify: `git grep -l -e "statuslog.runs" -- docs/decisions.md` prints `docs/decisions.md`.
- [ ] 5.2 In `THREAT_MODEL.md` say in the viewer's paragraph that it reads the status log, the run log, a findings file, the queue and `repos` through `skills/mflib/` modules, each bound kept, and that a `repos` that cannot be read shows one row and stops nothing.
  Verify: `git grep -l -e "kept.repos" -- THREAT_MODEL.md` prints `THREAT_MODEL.md`.
- [ ] 5.3 In `docs/recipes.md` add the recipe "A new fact on the board": the module's parser, the viewer's projector, the page and the test ([D24](design.md#d24)); in the state-file recipe name `statuslog.runs`, `runlog.timed` and `kept.repos` among what a reader takes.
  Verify: `git grep -l -e "new fact" -- docs/recipes.md` prints `docs/recipes.md`.
- [ ] 5.4 Read the delta `openspec/changes/0161-viewer/specs/sdd/spec.md` against the built code and edit each sentence that differs; the requirement that the viewer loads `conduct.py` and `converge.py` by path stands, and the run log's requirement still says `conduct.py` keeps `EVENT` and `last_log` bound.
  Verify: `openspec validate 0161-viewer --strict` exits `0`.
