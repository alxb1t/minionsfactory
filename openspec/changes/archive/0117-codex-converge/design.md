# Codex converge — design

A Codex fixer is an option a brief names; it halts at a limit and never falls back, and `_headroom` reads both windows. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Converge's checkers run on Codex through `Run.checker`, which falls back to Claude per checker ([D76](../../../docs/decisions.md#d76--a-codex-usage-limit-falls-back-and-halts-only-what-runs-on-codex)). The fixer does not: `converge.fixer` starts it through `host.worker` on `fix=`'s model, with its own retry loop and no limit rule. `_models` makes a fixer inherit `[converge]`'s executor, `brief_check.py` keeps `fix` hostless, and `conduct.py` halts a `[converge.fix]` that names an executor.

A Codex worker commits and runs the gate in a linked worktree, with its own `TMPDIR`, but has no network: the gate's `uv sync --locked` works only from the warm `.minions/uv-cache`. A round-1 checker spends a large share of a 5-hour window, and a fixer runs a pass each round.

```
today                              after this change
  converge.fixer                     converge.fixer
    └─ host.worker (any host)          ├─ claude: host.worker            (unchanged)
                                       └─ codex:  host.fix ─ codex_ready ─┬─ no  → halt, the fixer
                                                                         └─ yes → worker ─ limit → halt
```

## Goals / Non-Goals

- **Goals:** a brief may put the fixer on Codex; a Codex fixer halts for the person at a limit; the weekly window is read; a limit halts no version for a station it is past.
- **Non-Goals:** a Claude fallback for a Codex fixer; a verify executor of its own; a Codex fixer in this version's own converge.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | a Codex fixer is an option a brief names; with none named the fixer stays on Claude | about −$1.4 a version where the quota allows | a Codex fixer by default |
| [D2](#d2) | `fix codex/<model> <effort>` is valid in a brief and in `models.toml` (`[converge.fix] executor = "codex"`); a fixer naming no host is Claude's, never inheriting `[converge]`'s executor | the plan names each worker's host | a fixer that follows `[converge]` |
| [D3](#d3) | a Codex fixer never falls back to Claude: `codex_ready` saying no, or a limit, halts the version `codex usage limit — the fixer · resets <time>`, for the person to reset the window or wait, then rejoin; the checkers keep their per-checker fallback; a limit no longer halts a version for a Codex station it no longer needs (0104·S4) | the person, 2026-11-11: this line proves Codex can converge alone; the person resets the weekly window when it runs out | a per-fixer Claude fallback |
| [D4](#d4) | `_headroom` reads the 5-hour and the weekly window; either at 90% or more makes a Codex checker fall back before its spawn, and a Codex fixer halt before its spawn, naming the window | the weekly window stood at 98% unseen | reading the 5-hour window alone |
| [D5](#d5) | a Codex fixer's prompt fills its `Co-Authored-By:` with its own model; `fix.md` says a fixer adds no package | Codex knows no session attribution and has no network; packages are the plan's | the trailer left to the worker |
| [D6](#d6) | this version's own fixer stays Claude — the pinned v0.96.0 halts a fixer naming a host; its cut runs Sonnet medium, the H21 trial and the first H22 measure on the cut diet; Codex checkers; a minor; D68, D76, D40 amended; `debt: [0104·S4]` | lesson 1; a Codex fixer from the next version | a Codex fixer in this version |
| [D7](#d7) | a Codex fixer starts through a new host call, `Host.fix`, which returns a `Checked`; a Claude fixer keeps `host.worker` | the readiness rule and the limit text live in `Run`, beside `codex_ready`; fakes that start a Claude fixer change nothing | one call for both hosts: every fake host changes |
| [D8](#d8) | `hold_limited` takes each version's stage and counts only the stations ahead of it, and neither rescue nor supervise: each halts itself when it meets the limit | the card 0104·S4 names both; a rescue or supervisor may never run | reading the stage inside `on_stations` alone: `admit` probes with no stage |

### D1

A brief's `fix` part names a host only when the person chose Codex. With none, `models.toml` holds no `executor` under `[converge.fix]` and the fixer runs on Claude, as it does at v0.96.0 under a Claude `[converge]`.

### D2

`brief_check.py` drops `fix` from `HOSTLESS`, which then holds `cut` and `build-moderate`. `models_toml` already writes `executor` for a part with a host, so `[converge.fix]` gets it with no change. `_models` stops refusing `FIXER` an own `executor`, and for a `FIXER` with none returns `"claude"`, not the run's or `[converge]`'s. The `codex` + `claude-*` model refusal already holds for a worker table with an own executor.

### D3

`Run.fix(change, station, cwd, prompt, models, deadline)` returns a `Checked`.

- **Not ready:** `codex_ready(change, deadline)` false → `Checked(1, False, models, <text>, False, None)`, no worker started.
- **Ready:** `self.worker(...)` runs; exit not 0 and `usage_limit(out)` → the same text, with the recorded reset.
- **The text:** `codex usage limit — the fixer · resets <time>`, `<time>` from `_until(self.limited_until("codex"))`, the headroom reset when none is recorded ([D4](#d4)), else `unknown`.

`converge.fixer` on Codex raises `Halt(result.limit)` for a non-empty `limit`, at once and with no retry. The text holds `usage limit`, so `Run.rescue` gives it no rescue and no supervisor, as it does a checker's. The person resets the window or waits, then `conduct.py rejoin`.

### D4

`_headroom(now)` returns `(reset, window)` for the latest-resetting window at `HEADROOM` or more with its reset ahead, `window` `5-hour` for `primary` and `weekly` for `secondary`, else `None`. `codex_ready` takes the reset as before, so a weekly reset more than `LIMIT_WAIT` ahead sends a checker to Claude with no wait. `Run.fix` appends ` · the <window> window` to its text when the headroom, not a recorded limit, held it.

### D5

`fix.md`'s prompt gains `{attribution}`, a name in `PLACEHOLDERS`. `converge.fixer` fills it with `Codex <model> <noreply@openai.com>` on Codex, and with `the attribution line your session names` on Claude. The rules list gains `A fixer adds no package: a dependency is the plan's, and a Codex fixer has no network.`

### D6

This version's own converge runs the pinned v0.96.0 `converge.py` and `_models`: a fixer table naming a host halts. Its brief therefore names `fix claude-sonnet-5-5 medium`, and its checkers are Codex. Its cut is the first on the cut diet and the first on Sonnet medium.

### D7

`Host` gains `fix`, a method of the same shape as `checker`'s result. `converge.fixer` calls it only when `executor == "codex"`. A hand converge run with `--executor codex` takes the same path.

### D8

`on_stations(change, stage=None)` and `hold_limited(changes, cuts, stages=None)` keep their output with no stage. With a stage, these are behind it and left out:

| stage | left out |
|---|---|
| `converge`, `converge-halted` | `build`, the moderate build |
| `integrate`, `integrating` | the above, `converge`, the fixer |
| `release` | the above, `integrate` |

With any stage given, `rescue` and `supervise` are left out too. `Run.run` passes the stages it already read.

## Tests

The change adds tests at the unit layer and no end-to-end run: each new case uses a fake host or a `Run` with a faked worker, and runs on no engine (`T1`). It extends before it adds (`T2`).

| layer | file | added or changed |
|---|---|---|
| unit | `tests/test_brief_check.py` | `test_models_prints_the_items_toml` gains a `fix codex/gpt-6.1-sol medium` item; `test_a_brief_out_of_shape_halts` drops its `fix codex/x` row |
| unit | `tests/test_conduct.py` | `test_a_checker_on_another_host_is_planned_and_probed`'s `converge.fix names an executor` row becomes the `codex` + `claude-*` row; `test_a_station_runs_on_its_executor` gains the fixer rows; `test_the_codex_limit_data_is_read_from_its_rollout` reads the pair `_headroom` returns; `test_a_usage_limit_at_the_probe_is_no_refusal` gets a fake `headroom` that returns a pair |
| unit | `tests/test_conduct.py` | new `test_a_cut_queues_a_codex_fixer`, `test_a_limit_halts_only_the_stations_ahead`, `test_a_codex_fixer_halts_at_a_limit_and_never_falls_back`, `test_a_checker_falls_back_when_the_weekly_window_is_spent` |
| unit | `tests/test_converge.py` | new `test_a_codex_fixer_runs_through_host_fix_and_halts_at_a_limit`, `test_a_codex_fixers_prompt_names_its_attribution` |

No test is deleted or merged. The changed rows above keep their tests' other assertions and scenario ids, so no removed test needs a row here.

## Dependencies

None.

## Risks / Trade-offs

- A fixer under a `[converge] executor = "codex"` with no `[converge.fix]` table, which ran on Codex at v0.96.0, now runs on Claude with no model named. A brief names the fixer's host.
- A weekly window at 90% halts a Codex fixer until the person resets it or the window turns; the checkers fall back and the version goes on to its fixer, so a run can reach the fixer and stop there. That is the person's choice (D3).
- `_headroom` counts any Codex use, the operator's too, as D76 accepts.
- A Codex fixer has no network: a card whose fix needs a package fails its gate, and the fixer reports it `wontfix` naming the amend.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the models line, the fixer on Codex with the stage rule, then the windows, the prompt, the decisions and the spec.
