# Build per phase — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code, save the guards its
`## Tests` names.

## Progress

- [x] 1 — A build worker per phase
- [x] 2 — The phase handoff
- [ ] 3 — The moderate model
- [ ] 4 — The record

## 1 — A build worker per phase

- [x] 1.1 **HALT CHECK** Confirm 0099-stacked-builds' reset stands in `skills/mf-ship/scripts/conduct.py`, as
  [D3](design.md#d3)'s last bullet needs; missing, the plan is wrong.
  Verify: `git grep -n "def reset_stack" HEAD -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 1.2 Make the build of `tests/fake_worker.py` act as the design's *The fake host* paragraph says, save the modes
  `notes-<id>` and `notes-link-<id>`, which 2.1 adds.
  Verify: `grep -n "idle-phase-" tests/fake_worker.py` prints a line.
- [x] 1.3 Add `test_a_build_runs_a_worker_per_phase`, its phase spawns alone, and `test_a_halt_in_a_phase_resumes_there`
  to `tests/test_conduct.py`, per the design's `## Tests` rows; then build [D1](design.md#d1) and [D2](design.md#d2) in
  `skills/mf-ship/scripts/conduct.py`, each new why line citing `0102-build-per-phase design D1, D2`.
  Verify: `uv run pytest -q tests/test_conduct.py -k "worker_per_phase or resumes_there"` reports `2 passed`.
- [x] 1.4 In `tests/test_conduct.py`, make `_calls` drop each ` with phase=<digits>` clause, and edit each exact `_calls`
  list the run turns red, as the design's *The fake host* paragraph says.
  Verify: `uv run pytest -q tests/test_conduct.py -k dead_in_simplify` reports `1 passed`.
- [x] 1.5 In `tests/test_conduct.py`, edit `test_run_halts_on_a_human_phase`, `test_a_codex_worker_starts_on_mf_settings_alone`,
  `test_a_station_runs_on_its_executor`, `test_each_check_passes_only_on_disk_evidence` and
  `test_an_amend_past_the_judged_head_gets_one_round`, per their `## Tests` rows.
  Verify: `uv run pytest -q tests/test_conduct.py` exits 0.

## 2 — The phase handoff

- [x] 2.1 Add modes `notes-<id>` and `notes-link-<id>` to `tests/fake_worker.py`, and the notes step and the link roots to
  `test_a_build_runs_a_worker_per_phase` in `tests/test_conduct.py`, per the design's `## Tests` row.
  Verify: `grep -n "notes-" tests/fake_worker.py` prints a line.
- [x] 2.2 In `skills/mf-ship/scripts/conduct.py`, add `NOTES`, `Run.trim_notes`, the `notes` event in `EVENTS`, the line
  count before each phase spawn and the link halt, per [D3](design.md#d3), the why line citing
  `0102-build-per-phase design D3`.
  Verify: `uv run pytest -q tests/test_conduct.py -k worker_per_phase` reports `1 passed`.
- [x] 2.3 Add the reset step to `test_a_stacked_dependent_resets_and_merges_back` in `tests/test_conduct.py`, then make
  `reset_stack` in `skills/mf-ship/scripts/conduct.py` unlink `build-notes.md`, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_conduct.py -k stacked_dependent_resets` reports `1 passed`.
- [x] 2.4 In `skills/mf-build/SKILL.md`, add the `phase=` table to the change-id section, Step 1's fourth read, Step 2's
  item 7 and Step 4's phase report, per [D4](design.md#d4); the opening diagram's step 2 line gains `─▶ notes`.
  Verify: `grep -n "build-notes.md" skills/mf-build/SKILL.md` prints a line.

## 3 — The moderate model

- [ ] 3.1 Add the `_models` steps to `test_rescue_skip_runs_none`, and the moderate step and the second root to
  `test_a_build_runs_a_worker_per_phase`, in `tests/test_conduct.py`, per the design's `## Tests` rows.
  Verify: `grep -n "build.moderate names an executor" tests/test_conduct.py` prints a line.
- [ ] 3.2 In `skills/mf-ship/scripts/conduct.py`, add `MODERATE` to `PLANNED`, `_rating`, `_models`' `MODERATE` branch and
  `advance`'s pick, per [D5](design.md#d5), the why lines citing `0102-build-per-phase design D5`.
  Verify: `uv run pytest -q tests/test_conduct.py -k "worker_per_phase or rescue_skip"` reports `2 passed`.
- [ ] 3.3 Add the `build-moderate` steps to `test_a_hard_brief_is_ready_for_the_cut` and `test_a_brief_out_of_shape_halts`
  in `tests/test_brief_check.py`, and reword the latter's pinned `MODELS` text, per the design's `## Tests` rows.
  Verify: `grep -n "build-moderate" tests/test_brief_check.py` prints a line.
- [ ] 3.4 In `skills/mf-plan/scripts/brief_check.py`, add `PARTS`, take it in `models()`, add `build-moderate` to
  `HOSTLESS` and reword `MODELS`, per [D6](design.md#d6).
  Verify: `grep -n "^PARTS = " skills/mf-plan/scripts/brief_check.py` prints a line.
- [ ] 3.5 In `skills/mf-cut-change/SKILL.md`, add Step 6's rating bullet per [D5](design.md#d5), and edit *Suggesting
  models* per [D6](design.md#d6), keeping its row whose build cell opens `Sonnet 5.5 · high`.
  Verify: `grep -n "build.moderate" skills/mf-cut-change/SKILL.md` prints a line.
- [ ] 3.6 Edit the `I4` row of `skills/mf-cut-change/SKILL.md`'s and `skills/mf-build/SKILL.md`'s input contract, per
  [D5](design.md#d5).
  Verify: `grep -l "no part of the title" skills/mf-cut-change/SKILL.md skills/mf-build/SKILL.md` prints both paths.
- [ ] 3.7 In `skills/mf-plan/SKILL.md`, add the `build-moderate` part to the template's models line and to the parts
  paragraph, per [D6](design.md#d6).
  Verify: `grep -n "build-moderate" skills/mf-plan/SKILL.md` prints a line.

## 4 — The record

- [ ] 4.1 Run `grep -n "^### D[0-9]" docs/decisions.md`; add the decision [D7](design.md#d7) quotes to the group *The
  check loop and the release* in `docs/decisions.md`, `<n>` one above the highest id it printed, and `D<n>` to that group's
  list in the map.
  Verify: `grep -n "· A build runs a fresh worker per phase$" docs/decisions.md` prints a line.
- [ ] 4.2 Edit D65, D64, D57 and D13 in `docs/decisions.md`, per [D7](design.md#d7).
  Verify: `grep -n "build.{done,halt,closing,discarded.patch}., .build-notes.md." docs/decisions.md` prints a line.
- [ ] 4.3 Add the `build-notes.md` sentence to `THREAT_MODEL.md`'s *Entry points*, per [D7](design.md#d7).
  Verify: `grep -n "build-notes.md" THREAT_MODEL.md` prints a line.
- [ ] 4.4 In the flow diagram of `skills/mf-ship/SKILL.md`, replace `build, stacked on it` with `build, stacked on it, a
  worker a phase, then its close`, per [D7](design.md#d7).
  Verify: `grep -n "a worker a phase" skills/mf-ship/SKILL.md` prints a line.
