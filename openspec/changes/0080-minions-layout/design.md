# Minions layout — design

One folder per change under `.minions/changes/`, one helper per script to find it, a start-of-run move, both layouts read by the
review metrics, a hand-run station or script halting on an old layout, as D4 lists. Verdict at the end: ready to build.

## Context

Read at `41de9b6` (v0.65.0); sites mapped at `0079-debt-rename`'s tip `73fb1c5` and re-checked by symbol — `0079`'s last commits
touched none of them. ~233 path lines in `skills/`, `scripts/` and `tests/`, 27 in the spec, ~12 in the docs.

- **F1. `conduct.py`** (`skills/mf-ship/scripts/conduct.py`), its `runs` parameter meaning `.minions/`: findings and status log —
  `_run_end`, `_run_marked` (through it `_granted_run`, `_converge_halt`, `_converge_done`), `_amendable`, `_answered`, `_unjudged`,
  `_open_blockers`, `report`; build — `_closed`, `_build_halt`, `_check_build`'s message; integrate — `_red`, `stage_of`,
  `_check_integrate`, `Run.merge_in`, `Run.catch_up`; release — `_release_tip`; models — `_table` (through it `_models`,
  `_skips_rescue`, `_auto_grants`), `planned_models`' message, `read_plan`; rescue — `Run.rescue`, `Run.diagnose` (an `O_NOFOLLOW`
  folder); worker logs — `_free_log(folder, who, station)`, called from `Run.spawn` with `self.runs / self.log.stamp`. Generic:
  `runs/active`, `runs/rejoin`, `runs/<stamp>.md`, `runs/agent-<stamp>.log`, `grants/`, `uv-cache`, `debt.md`.
- **F2. The scripts:** `integrate.py`'s `_run_dir` and its readers `unready` (findings, patch) and `_settling` (the note); `replay/`
  stays. `gate_check.py`'s `exports()`, read as `exports() / change`. `metrics.py`'s `_change_dir(root, change)` already means the
  openspec change directory (used three times) — a name clash with the helper; its `run_directory` serves `metrics/<id>.html`, which
  stays. `review_metrics.py`'s `FINDINGS`, `RUNS`, `FILES`, `_cost_logs`, `read_change`, `read_repo` (raises with no findings
  folder), `round_data`; it has no run-dir helper — repos come from the config. `scripts/metrics/run.py`'s `Version.__init__` (the
  run dir inline), `status_runs`, `commits` (`.done`), `log()` (feeding `spent`, `role_tokens`), `cards`.
  `scripts/metrics/codebase.py` reads only the generic `.minions/test-report.xml`.
- **F3. The prose:** mf-build (8 lines), mf-converge (6) and `references/worker.md` (1), mf-integrate (9), mf-release (7), mf-rescue
  (7, its build-log glob among them), mf-cut-change (the models file), mf-ship (1), mf-review-metrics' description;
  `docs/principles.md`, `CONTRIBUTING.md`, `docs/decisions.md`, `AGENTS.md`'s `.minions/` list, `THREAT_MODEL.md:47`.
- **F4. The tests:** `tests/test_conduct.py` (50 path lines, written inline), `tests/test_review_metrics.py` (41),
  `tests/test_metric_scripts.py` (27), `tests/fake_worker.py` (15), `tests/drill_resume.py` (5), `tests/test_integrate.py` (4),
  `tests/test_gate_check.py` (3).
- **F5. The pattern:** `Run.migrate_debt()` (`0079`) returns a halt reason or `None`, renames only when the target is absent, halts
  when both stand, logs `move`; `ship()` calls it under the claim, before `_clear_stale_lock`, `read_plan` and the probe.
- **F6. On disk:** MF 47 change ids (186 findings files, 38 models, 21 `.done`, 142 change logs); isekai 83 (its `0097` halted in
  flight: a `.done`, a `.halt` naming 1.2, findings, models, rescue, logs); gpunit 19. Strays to leave: MF `findings/0034-fix-red.txt`,
  `release/fold.py`, top-level `0027-smoke/`, `0029-reader/`; isekai `findings/superseded/`, `*_station_brief.md`, `00xx_*gate.log`,
  the slugless `0030_review.md` and kin, `release/fold_0102.py`; gpunit `*_review.run1.md` and kin.
- **F7. Worker logs:** `who` is a change id or `run`; a Codex probe may run under a change id (`probe-codex`). A stamp may itself carry
  `-2`, so "newest" parses the name, never sorts it.

## Goals / Non-Goals

**Goals:** one folder per change; every reader on the new paths; no repo misread before or after its move; no chore.

**Non-Goals:** the generic folders; the viewer.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | The names inside `changes/<id>/` | Q1, Q5 | keeping `<id>_` prefixes |
| [D2](#d2) | `_change_dir(primary, id)` per script; `metrics.py`'s own renamed `_spec_dir` | Q7 | a shared module |
| [D3](#d3) | Worker logs in `changes/<id>/logs/`, the run's probe in `runs/<stamp>/` | Q5 | the probe in a change |
| [D4](#d4) | `Run.migrate_layout()` at a run's start; the hand-run stations and scripts D4 lists halt on an old layout | Q6 | dual-read in the stage machine |
| [D5](#d5) | `review_metrics.py` reads both layouts | Q6 | a one-off migration of other repos |
| [D6](#d6) | Links refused; the record | Q5 | — |

### D1

`.minions/changes/<id>/`: `review.md`, `security.md`, `status_log.md`, `diff.patch` (from `findings/<id>_*`); `models.toml` (from
`models/<id>.toml`); `integrate.md`, `integrate.red`, `integrate.resolved` (from `integrate/<id>.*`); `build.done`, `build.halt`,
`build.closing`, `build.discarded.patch` (from `build/<id>.*`); `rescue.md`; `release.held`; `gate-check/` (from `gate-check/<id>/`);
`logs/`.

### D2

`_change_dir(primary: Path, change: str) -> Path` returns `primary / ".minions" / "changes" / change` in `conduct.py`, and its twin,
from each script's own run directory, in `integrate.py`, `gate_check.py`, `run.py` and `review_metrics.py` (from a repo root). Every
F1–F2 site reads through it. `metrics.py`'s `_change_dir` becomes `_spec_dir`, its three callers with it.

### D3

`_free_log(folder, who, station)` takes `folder` = `_change_dir(primary, who) / "logs"` for a change id, named
`<stamp>-<station>[-<n>].log`; for `who == "run"`, `runs/<stamp>/run_<station>[-<n>].log` as now. `run.py`'s `log()` names the spawn's
`<stamp>-<station>[-<n>].log`; `review_metrics.py`'s `_cost_logs` reads every `<stamp>-<station>*.log`; mf-rescue's build-log input
reads the newest, by parsing the stamp and `n`.

### D4

`Run.migrate_layout() -> str | None`, beside `migrate_debt` in `ship()`, under the claim, before `read_plan`: for each change id
(`<4 digits>-<slug>`) an old-layout file names — a D1-named file at its old path, never a prefix match, so a stray never counts —
each D1 file moved into `changes/<id>/` when absent there, the worker logs
`runs/<stamp>/<id>_<station>[-<n>].log` to `changes/<id>/logs/<stamp>-<station>[-<n>].log`, logging `move — <id>: <n> files`; a file
not named by D1 — F6's strays — stays; an old file beside its new one, or a link (D6), halts the run, as `migrate_debt` does, before
any worker. Idempotent: nothing old, nothing moved. `integrate.py`, `gate_check.py`, `run.py` and `conduct.py grant`, finding an
old-layout file for their change, exit 2 naming `/mf-ship` to move it; a hand-run mf-converge checks before it opens its status log,
and a hand-run mf-build before it writes `build.halt`, and each halts the same way, writing no new-path file; `conduct.py status` and `report` read no stage for such a change
and print `<id> · old layout — a run moves it`, so `/mf-ship`'s Step 2 goes on to the run that moves it; `skills/mf-release/SKILL.md`'s
preconditions and mf-integrate's Step 2 halt the same way, so a hand-run release never reads "no findings" as converge skipped.

### D5

`review_metrics.py`'s `read_repo` lists `changes/*/` and, for a repo no run has moved, the old `findings/` and `runs/<stamp>/` logs;
per change the new folder wins; a repo with neither halts, naming `.minions/changes` and `.minions/findings` — the message
`test_overrides_win_over_the_config` (`tests/test_review_metrics.py:733-738`) reads, updated.

### D6

Every new-path open — the move, `_free_log`, `diagnose`, the integrate note — refuses a link at `.minions/changes/` or
`changes/<id>/`, as `diagnose` refuses at its folder. `THREAT_MODEL.md` gains the line: a link a worker plants at `changes/` or a
change's folder halts the run. The record: a new decision, *One folder per change in `.minions/`*, in `docs/decisions.md`, and the
paths at its other sites; `docs/principles.md`, `CONTRIBUTING.md` and its bootstrap template, `AGENTS.md`'s `.minions/` list.

## Tests

`git grep -c '^def test_' 41de9b6 -- tests/` counts the suite at the cut. The F4 sites follow the paths, the assertions unchanged.
Added: `test_a_run_moves_an_old_layout` (`tests/test_conduct.py`) — an old-layout fixture with strays and an in-flight build halt:
each file moved, the stage the same before and after, a second start moving nothing, both-files and a link halting —
`test_a_hand_run_station_halts_on_an_old_layout` (`tests/test_integrate.py`), `test_gate_check_halts_on_an_old_layout`
(`tests/test_gate_check.py`), `test_run_metrics_halt_on_an_old_layout` (`tests/test_metric_scripts.py`), `test_status_names_an_old_layout`
(`tests/test_conduct.py`, `status`, `report` and `grant`), `test_both_layouts_are_read` (`tests/test_review_metrics.py`) — `T2`: no
test holds an old layout. `test_overrides_win_over_the_config`'s expected message names both folders. None deleted.

## Dependencies

None.

## Risks / Trade-offs

- **A missed site misreads a stage:** the move's test holds a stage equality over every kind.
- **A repo not run since:** its hand-run stations halt, naming `/mf-ship`; one run moves it.

## Verdict

Ready to build.
