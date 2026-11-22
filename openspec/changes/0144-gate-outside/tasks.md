# Gate outside — tasks

Each phase ends on a green `make check`, the last on a green gate: the close's model key, the close command, the build loop, the skills and converge, the records. Decisions are in [design](design.md).

## Progress

- [x] 1 — The close's model key · moderate
- [x] 2 — The close command · hard
- [x] 3 — The build loop · hard
- [x] 4 — The skills and converge · moderate
- [ ] 5 — The records · moderate

## 1 — The close's model key

- [x] 1.1 In `skills/mf-plan/scripts/brief_check.py` make `PARTS` `("build-moderate", "build-close", *CHECKS)`, add `"build-close"` to `HOSTLESS`, and name `build-close` after `build-moderate` in `MODELS` ([D1](design.md#d1)). Update the `MODELS` assertions of `tests/test_brief_check.py`, and add `test_the_models_line_takes_build_close`: in order it passes, out of order it prints `MODELS`, with a host it says `build-close takes no host`.
  Verify: `uv run pytest tests/test_brief_check.py -k test_the_models_line_takes_build_close -q` exits `0`.
- [x] 1.2 In `skills/mflib/modelsfile.py` add `"build-close": "build.close"` to `TABLES` after `"build-moderate"`. In `tests/test_modelsfile.py` add `build-close claude-sonnet-5-5 high` after `build-moderate` in `_EVERY_PART` and its `[build.close]` table after `[build.moderate]` in `_EVERY_TABLE`, which the round-trip test over `TABLES` reads, and add `test_the_text_writes_a_build_close_table`: `text` writes `[build.close]` with `model` and `effort` and no `executor`, between `[build.moderate]` and `[converge]`, and `read` of an effort `a;b` there raises `Broken` naming `build.close`.
  Verify: `uv run pytest tests/test_modelsfile.py -k test_the_text_writes_a_build_close_table -q` exits `0`.
- [x] 1.3 In `skills/mf-ship/scripts/conduct.py` add `CLOSE = "build.close"` after `MODERATE`, put it in `PLANNED` and `_BUILT`, and make `_models` treat it as `MODERATE`: a table naming an `executor` stops with `conduct: halt — changes/<id>/models.toml: build.close names an executor`, else the executor is `[build]`'s. Add `test_a_build_close_table_names_no_executor` to `tests/test_conduct.py`, beside the `build.moderate` case.
  Verify: `uv run pytest tests/test_conduct.py -k test_a_build_close_table_names_no_executor -q` exits `0`.
- [x] 1.4 In the loop of `conduct.py` that builds the spawn's `models`, beside the moderate branch, give a spawn with `phase == "close"` the `model` and `effort` of the first of `[build.close]`, `[build.moderate]` and `[build]` that names each ([D1](design.md#d1)). Add `test_the_close_runs_on_the_close_table_then_moderate_then_build` to `tests/test_conduct.py`: a version for each table, each asserting the close's `spawn` line in the run log. This turns the close-spawn assertion of `test_a_build_runs_a_worker_per_phase`, whose `[build.moderate]` table now also serves the close: update it to the close on `[build.moderate]`.
  Verify: `uv run pytest tests/test_conduct.py -k "test_the_close_runs_on_the_close_table_then_moderate_then_build or test_a_build_runs_a_worker_per_phase" -q` exits `0`.
- [x] 1.5 In `skills/mf-plan/SKILL.md` add `build-close <model> <effort>` after `build-moderate` in the models line, and say the close's part takes no host as `build-moderate` takes none. In `skills/mf-cut-change/SKILL.md` add a `# [build.close]` entry to the models file block, one sentence saying the close runs on it, else on `[build.moderate]`, else on `[build]`, and a *Suggesting models* line for the close: Sonnet 5.5 · high.
  Verify: `git grep -n -e "build-close" -- skills/mf-plan/SKILL.md skills/mf-cut-change/SKILL.md` exits `0`.

## 2 — The close command

- [x] 2.1 In `skills/mf-converge/scripts/gate_run.py` make `gate()` read `subprocess.TimeoutExpired` as red: print `gate: red — past its limit · <seconds>s` and return `124` ([D3](design.md#d3)). Add `test_a_gate_past_its_limit_is_red` to `tests/test_gate_run.py`, with `GATE_SECONDS` patched to `1` and a `gate` target that runs `sleep 5`.
  Verify: `uv run pytest tests/test_gate_run.py -k test_a_gate_past_its_limit_is_red -q` exits `0`.
- [x] 2.2 In `conduct.py` add the `close` subcommand to `main`, `close <change-id>`, calling a new `close_command(cwd, change_id)` that takes the primary as `primary_of(cwd)`, finds the version with `find_version(primary, change_id)`, and prints `close: done`, `close: fail — <why>` or `close: cannot run — <why>` for exits `0`, `1` and `2` ([D2](design.md#d2)). A version not found exits `2`; an unticked `## Progress` box or a dirty tree fails. Add `test_close_of_a_version_that_is_not_there_exits_2` and `test_close_fails_on_an_unticked_phase` to `tests/test_conduct.py`.
  Verify: `uv run pytest tests/test_conduct.py -k "test_close_of_a_version_that_is_not_there_exits_2 or test_close_fails_on_an_unticked_phase" -q` exits `0`.
- [x] 2.3 In `conduct.py` add `_run_gate`, the gate step: `gate_run.py` (beside `CONVERGE`, in `mf-converge/scripts/`) through `sandboxed()` over `reach(primary)` in the version's tree. It prints `check — gate · pass · <n>s` or `check — gate · fail — red · <n>s`; on red it writes the output to `gate.red` in `.minions/changes/<change-id>/` through `mflib.statefile`, refusing a link, and on green it removes `gate.red`. `close` writes `build.halt` after a red `_run_gate`, with `sub-task: close`, `stop: gate`, `evidence:` and `head:` ([D2](design.md#d2), [D3](design.md#d3)). Add `test_close_on_a_green_gate_prints_the_gate_line` and `test_close_on_a_red_gate_writes_gate_red_and_build_halt` to `tests/test_conduct.py`, with the stand-in for `sandboxed` the suite already uses and a fixture whose `gate` target exits as the test says.
  Verify: `uv run pytest tests/test_conduct.py -k "test_close_on_a_green_gate_prints_the_gate_line or test_close_on_a_red_gate_writes_gate_red_and_build_halt" -q` exits `0`.
- [x] 2.4 In `conduct.py` add the close's metrics step after the gate: no `metrics/catalogue.toml` prints `metrics: none — no catalogue`; else `metrics.py collect --change <id> --base <base> --out <draft>` then `metrics.py page <id> --data <draft>`, `<base>` as `mf-build`'s Step 3.5 gives it. Exit `3` carries on, exit `2` or any other writes `build.halt` with `stop: metrics`. Add `test_close_skips_metrics_with_no_catalogue` and `test_close_halts_on_a_metrics_halt` to `tests/test_conduct.py`.
  Verify: `uv run pytest tests/test_conduct.py -k "test_close_skips_metrics_with_no_catalogue or test_close_halts_on_a_metrics_halt" -q` exits `0`.
- [x] 2.5 In `conduct.py` add the close's plan-check step and its end: `plan_check.py --change <id> --base <base>`, its printed lines kept in `plan-check.txt` beside `build.halt`; exit `1` writes `build.halt` with `stop: plan check`. On a pass write `build.done` as `head: <sha>` and `simplify: <sha>` or `simplify: none`, then remove `build.closing`, and print `close: done` ([D7](design.md#d7)). Add `test_close_halts_on_a_plan_check_failure` and `test_close_writes_build_done_with_head_and_simplify` to `tests/test_conduct.py`.
  Verify: `uv run pytest tests/test_conduct.py -k "test_close_halts_on_a_plan_check_failure or test_close_writes_build_done_with_head_and_simplify" -q` exits `0`.
- [x] 2.6 In `docs/modules.md` add `gate_run.py`, `metrics.py` and `plan_check.py` to the `skills/mf-ship/scripts/conduct.py` row, each in its place in the sorted list.
  Verify: `git grep -n -e "findings.py, gate_run.py, integrate.py" -- docs/modules.md` exits `0`.

## 3 — The build loop

- [x] 3.1 In `tests/fake_worker.py` make `_phase` answer `phase=repair` by committing a fix that removes the file `gate-red`, and commit a `refactor(<change-id>): simplify` commit at `phase=close` under a new mode `simplify-commit`; both leave the default close as it is, so no test turns yet. Give the fixture repos of `tests/test_conduct.py` a `gate` target `test ! -e gate-red`, so a test makes the gate red by committing `gate-red`.
  Verify: `git grep -n -e "simplify-commit" -- tests/fake_worker.py` exits `0`.
- [x] 3.2 In `conduct.py` make `check()` pass a `phase == "close"` spawn on every box ticked and a clean tree, with no `build.done` asked, through a new `_check_simplified`; the loop then writes `build.simplified` with `head: <sha>` and calls `close`, and `_check_build` stays the stage's check after it ([D5](design.md#d5)). A failed `close` hands its `<why>` to `judge` as the stage's reason, so `held` reads `build.halt` and the rescue keys as today. Make `_phase` of `tests/fake_worker.py` write no `build.done` at `phase=close`, and turn `test_each_check_passes_only_on_disk_evidence`, `test_the_stations_run_the_bundled_metrics_script` and each test of `tests/test_conduct.py` that reads the close's `build.done` from the fake worker. Add `test_the_simplify_worker_is_checked_on_a_clean_tree`.
  Verify: `uv run pytest tests/test_conduct.py tests/test_skills.py -q` exits `0`.
- [x] 3.3 In the build loop of `conduct.py`, after a phase's check passes with no `## Progress` box left unticked, call `_run_gate` ([D4](design.md#d4)). On red spawn one build worker with the prompt `Run the mf-build skill for change <id> with phase=repair.` on the last phase's models, once a run, its `build.halt` removed first as for any build spawn; run `_run_gate` again; a second red writes `build.halt` with `sub-task: repair` and hands `gate red after the repair` to `judge` as the reason. Add `test_a_red_gate_after_the_last_phase_is_repaired_once`, `test_a_second_red_gate_halts_after_the_repair` and `test_a_green_gate_after_the_last_phase_spawns_no_repair` to `tests/test_conduct.py`.
  Verify: `uv run pytest tests/test_conduct.py -k "test_a_red_gate_after_the_last_phase_is_repaired_once or test_a_second_red_gate_halts_after_the_repair or test_a_green_gate_after_the_last_phase_spawns_no_repair" -q` exits `0`.
- [x] 3.4 In `close`, when `_run_gate` is red and `HEAD`'s subject is `refactor(<change-id>): simplify`, reset the branch to the commit before it with `git reset --hard`, print `reset — simplify dropped`, write `build.simplified` at the new head and run the steps once more, at most once a call ([D5](design.md#d5)). Add `test_a_red_gate_after_simplify_drops_its_commit` and `test_a_red_gate_with_no_simplify_commit_fails_the_close` to `tests/test_conduct.py`.
  Verify: `uv run pytest tests/test_conduct.py -k "test_a_red_gate_after_simplify_drops_its_commit or test_a_red_gate_with_no_simplify_commit_fails_the_close" -q` exits `0`.
- [x] 3.5 In `conduct.py` make the loop run `close` with no worker when `build.simplified` names an ancestor of `HEAD` and each commit past it has the subject `docs(<change-id>): amend the change directory` and touches paths under the change directory alone; any other commit past it, or no file, spawns the simplify worker ([D6](design.md#d6)). Add `test_a_close_after_an_amend_of_the_change_directory_spawns_no_worker` and `test_a_close_after_a_commit_that_moves_code_spawns_the_simplify_worker` to `tests/test_conduct.py`.
  Verify: `uv run pytest tests/test_conduct.py -k "test_a_close_after_an_amend_of_the_change_directory_spawns_no_worker or test_a_close_after_a_commit_that_moves_code_spawns_the_simplify_worker" -q` exits `0`.

## 4 — The skills and converge

- [x] 4.1 In `skills/mf-build/SKILL.md` word `make check` after every phase where `make -n check` exits `0`, the last included, and the gate through `gate_run.py` where it does not; word `phase=close` as simplify alone with `make check` after each angle, and add `phase=repair`: read `gate.red` in the change's run folder, fix, run `make check` and the failed tests, commit. Move Steps 3.5 and 3.6 to `conduct.py close <change-id>`, which a build with no `phase=` runs once after simplify, and word `I8` as: each phase ends on a green `make check`, the build on a green gate.
  Verify: `git grep -n -e "conduct.py close" -- skills/mf-build/SKILL.md` exits `0`.
- [x] 4.2 In `skills/mf-cut-change/SKILL.md` word `I8` as in 4.1. In `skills/mf-simplify/SKILL.md` say its precondition is a green `make check`, it runs `make check` after each angle and not the gate, and its committed-tree re-run is the conductor's close: drop the re-run line.
  Verify: `git grep -n -e "make check" -- skills/mf-simplify/SKILL.md` exits `0`.
- [x] 4.3 In `skills/mf-converge/references/fix.md` say the fixer clears its cards to a green `make check` where `make -n check` exits `0`, runs the plan check as it does, and takes the gate through `gate_run.py` only where the repository has no `check` target ([D9](design.md#d9)).
  Verify: `git grep -n -e "make check" -- skills/mf-converge/references/fix.md` exits `0`.
- [x] 4.4 In `skills/mf-converge/scripts/converge.py` make `_evidence` read `plan-check.txt` from the change's run folder into the Plan check section, and run no `plan_check.py`, when `build.done` names the frozen head; at another head, or with no `plan-check.txt`, it runs the plan check as before ([D7](design.md#d7)). Add `test_a_freeze_at_the_head_build_done_names_runs_no_plan_check` and `test_a_freeze_at_another_head_runs_the_plan_check` to `tests/test_converge.py`.
  Verify: `uv run pytest tests/test_converge.py -k "test_a_freeze_at_the_head_build_done_names_runs_no_plan_check or test_a_freeze_at_another_head_runs_the_plan_check" -q` exits `0`.
- [x] 4.5 In the `Makefile`, in the `gate` target, add `--durations=20` to the pytest line, so `gate` names the twenty slowest tests ([D9](design.md#d9)). The diff:
  ```diff
  - uv run coverage run -m pytest -q -n auto --junitxml=.minions/test-report.xml
  + uv run coverage run -m pytest -q -n auto --durations=20 --junitxml=.minions/test-report.xml
  ```
  Verify: `git grep -n -e "--durations=20" -- Makefile` exits `0`.

## 5 — The records

- [ ] 5.1 In `docs/decisions.md` edit [D13](../../../docs/decisions.md): the build closes with a simplify worker alone that runs `make check` after each angle, and the conductor then runs the gate; edit D73: `phase=close` is simplify alone on `[build.close]`, the conductor's `close` runs the gate, the metrics, the plan check and writes `build.done`, and a gate red after the last phase gets one `phase=repair` worker.
  Verify: `git grep -n -e "phase=repair" -- docs/decisions.md` exits `0`.
- [ ] 5.2 In `docs/decisions.md` edit D70 so its *Why* no longer says no station's wait outlasts 5 minutes, and D74 so the plan check at the build's close is the conductor's `close` and not the build's own step.
  Verify: `git grep -c -e "no station's wait outlasts" -- docs/decisions.md` prints nothing.
- [ ] 5.3 In `docs/decisions.md` add `### D87 · The conductor runs the gate` after D86: the gate runs in the conductor after the last phase and in the close, under the sandbox runner, and a worker runs `make check`; *Rejected:* a gate in a worker's session.
  Verify: `git grep -n -e "### D87" -- docs/decisions.md` exits `0`.
- [ ] 5.4 In `CHANGELOG.md` rewrite the first bullet of the `[0.114.0]` section, the line debt card `0143·R3` names, to: "`plan_check.py` opens output only at a verb right before a span, and the `Verify:` label ends it, compares stdout alone and shows stderr on a failure, and starts a command only under the core count or when none runs (0143-verify-forms, phase 1)."
  Verify: `git grep -n -e "right before a span, and the" -- CHANGELOG.md` exits `0`.
