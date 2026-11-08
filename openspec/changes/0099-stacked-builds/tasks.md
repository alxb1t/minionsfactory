# Stacked builds — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code. Keep each phrase a
`Verify:` searches for on one line of its file.

## Progress

- [x] 1 — The stack
- [x] 2 — The base
- [x] 3 — The reset and the merge back
- [x] 4 — The record
- [x] 5 — The reset past a release

## 1 — The stack

- [x] 1.1 **HALT CHECK** Confirm `merge_in` in `skills/mf-ship/scripts/conduct.py` still takes the default branch as its third
  argument, per [D2](design.md#d2); missing, the plan is wrong.
  Verify: `grep -n 'def merge_in(self, tree: Path, change: str, default: str) -> None:' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 1.2 Add `hold-converge-<change>` to the converge of `tests/fake_worker.py`, then extend
  `test_after_waits_for_its_dependency` in `tests/test_conduct.py` as the design's `## Tests` row says.
  Verify: `grep -n 'hold-converge-0001-todo' tests/test_conduct.py` prints a line.
- [x] 1.3 Add `STACKED_ON`, `_built_head`, `_replanned`, `_stacked_on` and `_merged_back`, and their reads in `stage_of`,
  to `skills/mf-ship/scripts/conduct.py`, per [D1](design.md#d1), [D3](design.md#d3) and [D6](design.md#d6).
  Verify: `grep -n 'waits for its release' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 1.4 Give `merge_in` its `ref` and `stacked` arguments and the `chore(stack)` subject, and add `Run.stack`, in
  `skills/mf-ship/scripts/conduct.py`, per [D2](design.md#d2).
  Verify: `grep -n 'chore(stack): merge' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 1.5 Add `self.built`, `notify_built`, `stackable` and `until` to `Run`, and rewrite `ready` on them, in
  `skills/mf-ship/scripts/conduct.py`, per [D1](design.md#d1) and [D3](design.md#d3).
  Verify: `grep -n '    def stackable(' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 1.6 Extend `test_delta_reports_a_requirement_main_changed` in `tests/test_integrate.py`, as the design's `## Tests` row
  says, then make `delta` in `skills/mf-integrate/scripts/integrate.py` drop each id whose archive `MERGE_HEAD` holds, per
  [D2](design.md#d2).
  Verify: `uv run pytest -q tests/test_integrate.py -k requirement_main_changed` reports `1 passed`.
- [x] 1.7 Add `advance`'s return and its `stacked-on` removal, `Run.landed`, `take`'s loop, `catch_up`'s skip and the `wait`
  and `stacked` events in `skills/mf-ship/scripts/conduct.py`, per [D3](design.md#d3).
  Verify: `uv run pytest -q tests/test_conduct.py -k after_waits_for_its_dependency` reports `1 passed`.
- [x] 1.8 Make the edits the design's `## Tests` names for `test_a_dependents_delta_halts_as_integrating`,
  `test_a_crashed_integrate_script_halts_and_a_rerun_merges` (its commits alone), `_delta_noted`,
  `test_a_changed_git_config_halts_a_merge_in` and `test_a_run_goes_on_while_origin_is_down` in `tests/test_conduct.py`.
  Verify: `grep -n 'the dependent waits unstacked' tests/test_conduct.py` prints a line.
- [x] 1.9 Add the config step to `test_a_merge_in_refuses_a_planted_hook` in `tests/test_conduct.py`, as the design's
  `## Tests` row says, then `merge_in`'s second config check, its docstring naming `0050·R5`, per [D2](design.md#d2).
  Verify: `grep -n '0050·R5' skills/mf-ship/scripts/conduct.py` prints a line.

## 2 — The base

- [x] 2.1 Add `test_diff_coverage_takes_the_stacked_base` to `tests/test_gate_run.py`, as the design's `## Tests` row says, then
  make this `gate` edit to `Makefile`, per [D5](design.md#d5):
  ```diff
  - DIFF_BASE ?= main
  + # A stacked build's base is its dependency's built head: 0099-stacked-builds design D5.
  + STACKED_ON = $(shell git rev-parse --verify --quiet "$$(grep -sxE '[0-9a-f]{40}' "$$(git rev-parse --path-format=absolute --git-common-dir)/../.minions/changes/$$(git branch --show-current)/stacked-on")^{commit}")
  + DIFF_BASE ?= $(or $(STACKED_ON),main)
  ```
  Verify: `uv run pytest -q tests/test_gate_run.py -k stacked_base` reports `1 passed`.
- [x] 2.2 Edit Step 3.5's `<base>` in `skills/mf-build/SKILL.md`, as [D5](design.md#d5) quotes it.
  Verify: `grep -n 'names while it stands — a stacked build' skills/mf-build/SKILL.md` prints a line.
- [x] 2.3 Edit the `I17` row and Step 1's `I17` bullet in `skills/mf-build/SKILL.md`, as [D5](design.md#d5) quotes them.
  Verify: `grep -n 'or its change in the head .stacked-on. names' skills/mf-build/SKILL.md` prints a line.
- [x] 2.4 Edit the `I17` row in `skills/mf-cut-change/SKILL.md`, as [D5](design.md#d5) quotes it.
  Verify: `grep -n 'or its change in the head .stacked-on. names' skills/mf-cut-change/SKILL.md` prints a line.
- [x] 2.5 Edit the range in Step 1 of `skills/mf-simplify/SKILL.md`, as [D5](design.md#d5) quotes it.
  Verify: `grep -n 'is .<base>..HEAD., .<base>. the sha' skills/mf-simplify/SKILL.md` prints a line.

## 3 — The reset and the merge back

- [x] 3.1 Add `test_a_stacked_dependent_resets_and_merges_back` to `tests/test_conduct.py`, as the design's `## Tests` row
  says.
  Verify: `grep -n '^def test_a_stacked_dependent_resets_and_merges_back' tests/test_conduct.py` prints a line.
- [x] 3.2 Add `_cut_commit`, `Run.reset_stack`, its reads in `advance` and `landed`, and the `reset` event to
  `skills/mf-ship/scripts/conduct.py`, per [D6](design.md#d6).
  Verify: `grep -n '    def reset_stack(' skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 3.3 Extend `test_changelog_keeps_the_branch_entries_above_the_released_sections` and
  `test_replay_reproduces_a_rule_settled_merge` in `tests/test_integrate.py`, as the design's `## Tests` rows say, then
  `changelog`'s base entries, `unreleased` and `replay`'s condition in `skills/mf-integrate/scripts/integrate.py`, per
  [D4](design.md#d4).
  Verify: `grep -n '^def unreleased' skills/mf-integrate/scripts/integrate.py` prints a line.
- [x] 3.4 Add `self.unreleased` to `Run` and its read in `settle` in `skills/mf-ship/scripts/conduct.py`, and `unreleased` to
  the `crash.py` of `test_a_crashed_integrate_script_halts_and_a_rerun_merges` in `tests/test_conduct.py`, per
  [D4](design.md#d4).
  Verify: `uv run pytest -q tests/test_conduct.py -k resets_and_merges_back` reports `1 passed`.

## 4 — The record

- [x] 4.1 Extend `test_run_metrics_read_the_run_logs` in `tests/test_metric_scripts.py`, as the design's `## Tests` row says,
  then `Version.after_waits` and its `METRICS` entry in `scripts/metrics/run.py`, per [D7](design.md#d7).
  Verify: `grep -n '"after-wait-minutes": Version.after_waits' scripts/metrics/run.py` prints a line.
- [x] 4.2 Add the `after-wait-minutes` metric after `wait-minutes` in `metrics/catalogue.toml`, as [D7](design.md#d7) quotes it.
  Verify: `grep -n 'id = "after-wait-minutes"' metrics/catalogue.toml` prints a line.
- [x] 4.3 Add D70 after D47 in `docs/decisions.md`, as [D8](design.md#d8) quotes it.
  Verify: `grep -n '^### D70 · A dependent builds on its dependency.s built head$' docs/decisions.md` prints a line.
- [x] 4.4 Add `, D70` after `D67` in the Repo conventions list of the map at the top of `docs/decisions.md`, per
  [D8](design.md#d8).
  Verify: `grep -n 'D60, D61, D67, D70' docs/decisions.md` prints a line.
- [x] 4.5 Add D44's sentence in `docs/decisions.md`, as [D8](design.md#d8) quotes it.
  Verify: `grep -n 'A stacked dependent takes its dependency.s built head by a' docs/decisions.md` prints a line.
- [x] 4.6 Make D45's edits in `docs/decisions.md`, as [D8](design.md#d8) quotes them.
  Verify: `grep -n 'a stacked branch.s .CHANGELOG.md. on any merge' docs/decisions.md` prints a line.
- [x] 4.7 Make D47's edit in `docs/decisions.md`, as [D8](design.md#d8) quotes it.
  Verify: `grep -n 'a dependent building on its dependency.s built head' docs/decisions.md` prints a line.
- [x] 4.8 Add `stacked-on` to D57's list in `docs/decisions.md`, per [D8](design.md#d8).
  Verify: `grep -n 'discarded.patch}., .stacked-on.' docs/decisions.md` prints a line.
- [x] 4.9 Make D63's edit in `docs/decisions.md`, per [D8](design.md#d8) (`0095·R6`).
  Verify: `grep -n 'Conformance keeps the full plan' docs/decisions.md` prints a line.
- [x] 4.10 Add the stacked-build bullet to *Trust boundaries* in `THREAT_MODEL.md`, as [D8](design.md#d8) quotes it.
  Verify: `grep -n 'A stacked build runs on code no converge has judged' THREAT_MODEL.md` prints a line.
- [x] 4.11 Drop `0050·R5` from *Known gaps* in `THREAT_MODEL.md` and rewrite its config-race gap, as [D8](design.md#d8)
  quotes it.
  Verify: `grep -n 'compares the config again right before its commit' THREAT_MODEL.md` prints a line.
- [x] 4.12 Edit the flow's version line in `skills/mf-ship/SKILL.md`, as [D8](design.md#d8) quotes it.
  Verify: `grep -n 'build, stacked on it' skills/mf-ship/SKILL.md` prints a line.

## 5 — The reset past a release

- [x] 5.1 Extend `test_a_stacked_dependent_resets_and_merges_back` in `tests/test_conduct.py` with the `0005-redo` and
  `0006-race` step, as the design's `## Tests` row says.
  Verify: `grep -n '0006-race' tests/test_conduct.py` prints a line.
- [x] 5.2 Give `Run.reset_stack` its released read, and add its read in `ready` before the merge back, in
  `skills/mf-ship/scripts/conduct.py`, per [D6](design.md#d6).
  Verify: `uv run pytest -q tests/test_conduct.py -k resets_and_merges_back` reports `1 passed`.
- [x] 5.3 Edit D70's reset sentence in `docs/decisions.md`, as [D8](design.md#d8) quotes it.
  Verify: `grep -n 'once the dependency released; it stacks again on the dependency' docs/decisions.md` prints a line.
