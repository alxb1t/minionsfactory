# Codex converge — tasks

The models line, the fixer on Codex with the stage rule, then the windows, the prompt, the decisions and the spec. Decisions: [design](design.md).

## Progress

- [x] 1 — the models line: fix codex/<model> in brief_check.py and conduct.py's _models, no inherited executor · moderate
- [ ] 2 — converge.py's fixer on Codex: through the worker call, a limit halts it, no fallback; 0104·S4 · hard
- [ ] 3 — _headroom over both windows; fix.md's trailer and no-package line; D68, D76, D40; the spec · hard

## 1 — the models line: fix codex/<model> in brief_check.py and conduct.py's _models, no inherited executor

- [x] 1.1 In `skills/mf-plan/scripts/brief_check.py`, set `HOSTLESS = ("cut", "build-moderate")` ([D2](design.md#d2)).
  Verify: `git grep -n 'HOSTLESS = ("cut", "build-moderate")' -- skills/mf-plan/scripts/brief_check.py` prints a line.
- [x] 1.2 In `skills/mf-plan/SKILL.md`, write `fix <host/model> <effort>` in the `models:` grammar line, and replace "`cut`, `fix` and `build-moderate` take none" with "`cut` and `build-moderate` take none; `fix codex/<model> <effort>` runs the fixer on Codex, and a `fix` with no host runs on Claude".
  Verify: `git grep -n 'fix <host/model> <effort>' -- skills/mf-plan/SKILL.md` prints a line.
- [x] 1.3 In `tests/test_brief_check.py`, drop the `fix codex/x b` item and its `takes no host` line from `test_a_brief_out_of_shape_halts`, keeping the `cut` and `build-moderate` ones and every item's number as it stands. Add a `fix codex/gpt-6.1-sol medium` item to `test_models_prints_the_items_toml` and assert the `[converge.fix]` table holds `executor = "codex"`, `model = "gpt-6.1-sol"` and `effort = "medium"`.
  Verify: `uv run pytest tests/test_brief_check.py -q` exits 0.
- [x] 1.4 In `skills/mf-ship/scripts/conduct.py`'s `_models`, stop refusing `FIXER` an own `executor`: the refusal at `own and station in (FIXER, MODERATE)` keeps `MODERATE` alone. For a `FIXER` with no own `executor`, return `"claude"`, not `[converge]`'s ([D2](design.md#d2)). Update the docstring's `Why:` to name `0117-codex-converge design D2`.
  Verify: `git grep -n 'own and station in (FIXER, MODERATE)' -- skills/mf-ship/scripts/conduct.py` exits 1.
- [x] 1.5 In `tests/test_conduct.py`: in `test_a_checker_on_another_host_is_planned_and_probed`, replace the `converge.fix names an executor` row with `[converge.fix]` `executor = "codex"`, `model = "claude-sonnet-5-5"` halting `converge.fix on codex, model claude-sonnet-5-5`. In `test_a_station_runs_on_its_executor`, assert `models(minions, "0001-todo", "converge.fix", "claude")` is `("claude", …)` under a `[converge] executor = "codex"` file with no fixer table, and `("codex", "gpt-6.1-sol", "medium")` under `[converge.fix] executor = "codex"`.
  Verify: `uv run pytest tests/test_conduct.py -q -k "another_host or runs_on_its_executor"` exits 0.
- [x] 1.6 In `tests/test_conduct.py`, add `test_a_cut_queues_a_codex_fixer`: a brief item whose models line ends `fix codex/gpt-6.1-sol medium`, cut as `test_a_cut_queues_its_models_file` cuts its own, queues a `models.toml` holding `[converge.fix]` with `executor = "codex"`, which `_models` reads back as `("codex", "gpt-6.1-sol", "medium")`. Leave `_MODELS` and that test as they are.
  Verify: `uv run pytest tests/test_conduct.py -q -k queues_a_codex_fixer` exits 0.

## 2 — converge.py's fixer on Codex: through the worker call, a limit halts it, no fallback; 0104·S4

- [ ] 2.1 In `skills/mf-converge/scripts/converge.py`, add to the `Host` protocol a method `fix(change, station, cwd, prompt, models, deadline) -> Checked`, its docstring "Run the Codex fixer; return what it did" ([D7](design.md#d7)).
  Verify: `git grep -n 'Run the Codex fixer; return what it did' -- skills/mf-converge/scripts/converge.py` prints a line.
- [ ] 2.2 In `converge.py`'s `fixer`, when `executor == "codex"` start the worker through `context.host.fix(context.change, station, context.tree, told, models, context.deadline)` and take its `code`, `killed` and `limit`; a non-empty `limit` raises `Halt(limit)` at once, with no retry. A Claude fixer keeps `host.worker` and its retry. Update the docstring ([D3](design.md#d3), [D7](design.md#d7)).
  Verify: `git grep -n 'host.fix(' -- skills/mf-converge/scripts/converge.py` prints a line.
- [ ] 2.3 In `tests/test_converge.py`, add `fix` to the fake host and `test_a_codex_fixer_runs_through_host_fix_and_halts_at_a_limit`: a fixer with `("codex", "gpt-6.1-sol", "medium")` calls `fix` and never `worker`; a result whose `limit` is `codex usage limit — the fixer · resets 5:50 PM` halts with that text after one call; a result with exit 1 and no limit gets one retry.
  Verify: `uv run pytest tests/test_converge.py -q -k host_fix` exits 0.
- [ ] 2.4 In `skills/mf-ship/scripts/conduct.py`, add `Run.fix(change, station, cwd, prompt, models, deadline)` beside `Run.checker`, returning a `Checked`. `codex_ready(change, deadline)` false returns `limit` = `text` and starts no worker; else `self.worker(...)` runs, and its exit not 0 with `usage_limit(out)` returns `text`, any other result `limit` `""`. `text` is `codex usage limit — the fixer · resets <time>`, `<time>` `_until(reset)` for a recorded limit's `reset` from `self.limited_until("codex")`, else `unknown` ([D3](design.md#d3)).
  Verify: `git grep -n 'codex usage limit — the fixer' -- skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 2.5 In `tests/test_conduct.py`, add `test_a_codex_fixer_halts_at_a_limit_and_never_falls_back`. Codex limited, its reset hours away: `Run.fix` returns a `limit` holding `codex usage limit — the fixer · resets`, and starts no worker of any executor. Codex not ready with no limit recorded (a failed probe): `resets unknown`. Codex ready, a faked worker exiting 1 on a Codex usage limit: the same text, the limit recorded. A worker exiting 0: `limit` `""`.
  Verify: `uv run pytest tests/test_conduct.py -q -k never_falls_back` exits 0.
- [ ] 2.6 In `conduct.py`, give `Run.on_stations` a `stage: str | None = None` and `Run.hold_limited` a `stages: dict[str, str] | None = None`. With a stage, leave out the stations behind it, and `rescue` and `supervise`, as [D8](design.md#d8)'s table says; with none, return what it returns now. At `Run.run`'s call, pass `{change: stage for change, (stage, _) in stages.items()}`.
  Verify: `git grep -n 'stages: dict\[str, str\] | None' -- skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 2.7 In `tests/test_conduct.py`, add `test_a_limit_halts_only_the_stations_ahead`: with Codex limited, `hold_limited` given the stage `release` does not halt a version whose `[build]` names Codex, and given the stage `build` halts it; `on_stations` with no stage returns what it returns now.
  Verify: `uv run pytest tests/test_conduct.py -q -k stations_ahead` exits 0.

## 3 — _headroom over both windows; fix.md's trailer and no-package line; D68, D76, D40; the spec

- [ ] 3.1 In `conduct.py`, make `_headroom(now)` return `(reset, window)` or `None` as [D4](design.md#d4) says, `window` named by a constant `WINDOWS = {"primary": "5-hour", "secondary": "weekly"}`. Make `Run.codex_ready` take the reset from the pair, and `Run.fix` take its `<time>` from the pair when no limit is recorded and append ` · the <window> window` to its text. Update both docstrings.
  Verify: `git grep -n '"secondary": "weekly"' -- skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 3.2 In `tests/test_conduct.py`, rewrite the `headroom(...)` assertions of `test_the_codex_limit_data_is_read_from_its_rollout` to the pair `_headroom` returns (the `secondary` cases now return a pair, not `None`), and add a rollout with the weekly window at 98% and the 5-hour window at 10%. In `test_a_usage_limit_at_the_probe_is_no_refusal`, make the fake `headroom` return a pair. Add `test_a_checker_falls_back_when_the_weekly_window_is_spent`: `codex_ready` is false with that rollout, and `Run.fix` returns a `limit` ending ` · the weekly window`.
  Verify: `uv run pytest tests/test_conduct.py -q -k "weekly or read_from_its_rollout or no_refusal"` exits 0.
- [ ] 3.3 In `skills/mf-converge/scripts/converge.py`, add `"attribution"` to `PLACEHOLDERS`; in `fixer` fill it with `Co-Authored-By: Codex <model> <noreply@openai.com>` on Codex and `the attribution line your session names` on Claude ([D5](design.md#d5)).
  Verify: `git grep -n '"attribution"' -- skills/mf-converge/scripts/converge.py` prints a line.
- [ ] 3.4 In `skills/mf-converge/references/fix.md`, add `- The line your commit's trailer starts with: {attribution}` to the prompt's list, and to the rules `- **A fixer adds no package**: a dependency is the plan's, and a Codex fixer has no network.`
  Verify: `git grep -n 'adds no package' -- skills/mf-converge/references/fix.md` prints a line.
- [ ] 3.5 In `tests/test_converge.py`, add `test_a_codex_fixers_prompt_names_its_attribution`: the prompt `fixer` passes to `host.fix` for `("codex", "gpt-6.1-sol", "medium")` holds `Co-Authored-By: Codex gpt-6.1-sol <noreply@openai.com>`, and the one it passes to `host.worker` for a Claude fixer holds `the attribution line your session names`.
  Verify: `uv run pytest tests/test_converge.py -q -k fixers_prompt` exits 0.
- [ ] 3.6 In `skills/mf-converge/SKILL.md`'s `fix=` row and `skills/mf-ship/SKILL.md`'s converge row, state that the fixer runs on the executor its table names, Claude when it names none, and that a Codex fixer at a limit halts the version.
  Verify: `git grep -n 'Codex fixer' -- skills/mf-converge/SKILL.md skills/mf-ship/SKILL.md` prints a line.
- [ ] 3.7 In `docs/decisions.md`, edit where they live ([D6](design.md#d6)): D68, its `The fixer stays on converge's host` sentence → `A fixer table may name Codex; it halts at a limit and never falls back` and its `Rejected` `a fixer on another host` removed; D76, `a primary window at 90% or more` → `the 5-hour or weekly window at 90% or more`, and its `Accepts` gains `a Codex fixer halts its version at a limit, with no fallback`; D40's last sentence gains `, and a Codex fixer through the run's fixer call`.
  Verify: `git grep -n 'fixer stays on converge' -- docs/decisions.md` exits 1.
