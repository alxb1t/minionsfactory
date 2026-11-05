# Run metrics — design

Converge names each role's executor, model and effort; every spawn keeps its log; `scripts/metrics/run.py` records a release's run
into its data file; the review metrics read tokens per role and Codex's sessions into `review-metrics.json`. Verdict at the end:
ready to build.

## Context

Read at `61daff7` (v0.62.0); the brief carries no `At` line, so every fact was re-read.

- **F1. The verdicts line:** the events table's row (`skills/mf-converge/SKILL.md:82`), "each file's `verdict` and `open_blocking`,
  ending `tokens <n>` … or `tokens unavailable`"; in practice one line per role. The conductor's `tokens` is the Task result's
  final turn (`totalTokens`): no all-turn figure reaches it. The station's run log does hold every subagent `assistant` event, by
  `parent_tool_use_id`, its `task_started` mapping each to its Task — review r1 of `0076`: 8,367,892 tokens against 192,099.
- **F2. The models and the spawn line:** `_models` returns `(executor, model, effort)` (`skills/mf-ship/scripts/conduct.py:1781-1801`);
  the spawn line is `{station} · model {model or 'default'}{other}` (`:2561`), `other` ` · executor <x>` only when it differs.
  `test_a_station_runs_on_its_executor` (`tests/test_conduct.py:1918`) reads spawn lines.
- **F3. The station logs:** `work()` opens each with `"w"` (`conduct.py:2122`) at `<who>_<station>.log` (`:2562`, `:3247`): a second
  spawn in one stamp truncates the first. `0071`'s converge was spawned four times and two logs remain; its cost reads $2.10.
- **F4. The card:** `skills/mf-converge/references/worker.md:129-166`, the rows Title … Status at `:137-148`, "every field, in this
  order" (`:150`); no test pins the field list (`tests/test_skills.py:181-225`).
- **F5. The collector:** `run_metric` runs `uv run --script <script> <args>` with `cwd` the worktree and `MF_METRICS_CHANGE`,
  `_BASE`, `_HEAD` in its env (`skills/mf-build/scripts/metrics.py:170-194`, `:315-319`); the last stdout line is the value; a
  non-zero exit is `unavailable`, its first stderr line the reason. `_derived` fills `diff-lines`, `diff-files` for a `source =
  "station"` entry (`:231-245`, `:328-330`). A script finds `.minions/` as `scripts/metrics/backlog.py:21-28` does.
- **F6. The sources:** run logs `HH:MM:SS · <who> · <event> — <detail>`, the date only in the stamp name (`conduct.py:63`,
  `:1740-1764`); a catch-up is a converge spawned after the version's first integrate spawn; status logs, findings cards
  (`Verdict`, `Status`, `Related`), `.minions/backlog.md`'s `## <id>` headings, the proposal's `backlog:`. Build commits include
  `fix(<id>)` subjects, so the split is at `.minions/build/<id>.done`'s `head:`, along `--first-parent --no-merges`.
- **F7. Measured** with a scratch script over `0071`, `0072`, `0074`, `0076`: lead 111.6, 33.8, 40.2, 52.2 minutes; build 37.4,
  11.0, 12.6, 19.4; converge 59.3, 22.7, 27.6, 32.7; `0071`'s waits 6.6; rounds 4, 2, 3, 2; cost without the release $12.85 (a
  floor, F3), $10.28, $12.01, $18.39. `0072`'s two "escapes" repeat cards `0072` itself pays.
- **F8. The token forms** over 711 `verdicts` lines in MF, isekai and gpunit: no `token` word 445 · `tokens N` on a one-role line
  173 · `tokens N` on a both-role line 27 · `tokens unavailable` 45 · `tokens review N, security M` 13 · `tokens N + M` 7 ·
  `tokens Nk (review Ak, security Bk)` 2 · `tokens N review, M security` 1. Today's regex
  (`skills/mf-review-metrics/scripts/review_metrics.py:287`) takes each line's first `tokens N` and sums every line.
- **F9. Codex sessions:** `~/.codex/sessions/**/*.jsonl`; a worker's `session_meta.payload.source.subagent.thread_spawn` names its
  `parent_thread_id` and `agent_path` (`/root/review_round1`, `security_r2`); `turn_context` its model and effort; the last
  `token_count` event's `info.total_token_usage` its cumulative tokens. `git.repository_url` names the repo, the parent's `cwd` its
  worktree; the 62 guardian sessions (`codex-auto-review`) are no worker. Matched by URL or worktree and the round's freeze-to-
  verdicts window, summing every session in it: 73 of 73 Codex review and security workers. Status-log times are local; the
  offset changed on 2026-10-25.
- **F10. The record:** D50 (`docs/decisions.md:264`) names the findings files, status logs and run logs, and one page.

## Goals / Non-Goals

**Goals:** each release's run in its data file; each role's executor, model and effort recorded; Codex's tokens read.

**Non-Goals:** a page; the codebase's metrics; the release's own minutes and cost.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | A `verdicts` line per role ends `executor · model · effort · tokens`; a card's `**Round:**`; the spawn line's effort | Q2, Q4 | executor and effort in the findings frontmatter, which a worker cannot know |
| [D2](#d2) | A later spawn in a stamp writes `<who>_<station>-<n>.log`; readers glob `<who>_<station>.log` and `-[0-9]*.log` | Q2 | append mode, which breaks a log's cumulative cost |
| [D3](#d3) | `scripts/metrics/run.py <kind>`, the 37 script ids and the 2 station ids below | Q7, Q8 | one id per stage including the release, always a gap |
| [D4](#d4) | Per-role tokens, all turns, from the converge station log's subagent events | Q3 | the conductor's figure, the final turn |
| [D5](#d5) | `review_metrics.py` parses each token form per role, reads Codex sessions, writes `review-metrics.json` | Q2, Q11 | — |
| [D6](#d6) | The record: D50 | Q11 | — |

### D1

The events table's `verdicts` row reads "one line per role: its file's `verdict` and `open_blocking`, then `executor <x> · model
<m> · effort <e> · tokens <n>` — the executor, model and effort from the version's models file `[converge]`, else the run's; `tokens`
the worker's figure, or `unavailable`"; the example becomes two lines. `worker.md`'s card gains the row `| **Round** | the round the card
was found |` after `**Priority**`, in the table's own form, and its example a `**Round:** 1` line; a card without it reads as a gap.
The spawn line reads `{station} · model {model or 'default'}{effort}{other}`, `effort = f" · effort {effort}" if effort else ""`,
so a spawn with no effort reads as now. A
`verdicts` line with no model or effort known writes `default`, which the readers take as `null`. No living requirement pins the spawn line's format or the card's field list, so neither
takes a delta.

### D2

`spawn` (`conduct.py:2562`) takes the first free of `<who>_<station>.log`, `<who>_<station>-2.log`, … in the stamp — the n-th
spawn of a station in a stamp writes `.log` for n = 1 and `-n.log` after — and keeps the path it chose; the probe (`:3247`) reads that path, not a name of its own. `review_metrics.py`'s `_cost_logs` globs
`<change>_<station>.log` and `<change>_<station>-[0-9]*.log`, so `run_probe-codex.log` is no station's. `skills/mf-rescue/SKILL.md:40`
reads the newest `<change-id>_build*.log`.

### D3

`run.py` reads `MF_METRICS_CHANGE`, finds `.minions/` as `backlog.py` does, and prints one number or exits 1 naming what it lacked.
Its kinds, each a catalogue entry `script = "scripts/metrics/run.py"`, `args = ["<kind>"]`, `group = "run"`:

| kind | ids | unit · better |
|---|---|---|
| time | `lead-minutes`, `build-minutes`, `converge-minutes`, `catch-up-minutes`, `integrate-minutes`, `wait-minutes` | minutes · lower |
| loop | `converge-rounds`, `blockers-round-1`, `grants`, `halts-build`, `halts-converge`, `halts-integrate`, `halts-release`, `rescues-fixed`, `rescues-diagnosed`, `build-commits`, `fix-commits` | count · lower, but `build-commits` higher |
| cost | `cost-usd`, `cost-usd-build`, `cost-usd-converge`, `cost-usd-catch-up`, `cost-usd-integrate`, `tokens`, `tokens-build`, `tokens-converge`, `tokens-catch-up`, `tokens-integrate`, `cost-per-changed-line` | dollars, tokens · lower |
| review | `review-confirmed`, `security-confirmed`, `review-refuted`, `security-refuted`, `review-tokens-per-confirmed`, `security-tokens-per-confirmed`, `escapes`, `debt-added`, `debt-paid` | count, tokens · confirmed and `debt-paid` higher, the rest lower |

`diff-lines` and `diff-files` are `source = "station"` entries, `_derived`'s. Rules, from F6–F7: minutes from a stage's `spawn` to
its `finish` lines, summed over spawns, a catch-up a converge spawned after the first integrate; `lead-minutes` from the cut
commit — the change's first commit with the subject `docs(<id>): land the change directory` — its committer time, to the release's
`spawn`; a stage the run log never spawned for the version reads `0`, a spawned one whose log or lines are missing a gap; `wait-minutes` from a `halt` to the next `rejoin`, person's grant or run start
naming the version, a run's own spawn (rescue, automatic grant) counting none; cost and tokens by `_cost_logs`' rules, reimplemented in the standalone
script, a station whose spawns outnumber its logs a gap, a catch-up's logs those
of the converges spawned after the version's first integrate, by D2's n, `cost-usd` and `tokens` the stations' sum with rescue's, the release's
own log left out; `cost-per-changed-line` over `diff-lines`; escapes save the ids in the proposal's
`backlog:`; debt added from the backlog's `## <id>` heading, paid from `backlog:`; `blockers-round-1` from round 1's `verdicts`
lines' `open_blocking`. Times cross midnight by the stamp's date.

### D4

`run.py`'s `review-tokens-per-confirmed` and `security-tokens-per-confirmed` sum, per role, the `usage` of every subagent
`assistant` event in the version's converge logs whose `parent_tool_use_id` is a `tool_use_id` the log's `task_started` events map
to a `description` naming `review` or `security` — the conductor dispatches through `Agent`, e.g. "Converge review worker 0076" —
deduplicated by `message.id`; over the confirmed cards of that role. No log, no matching
subagent event, converge spawns outnumbering its logs, or no confirmed card, is a gap.

### D5

`_status_log`'s record keeps its `tokens`, the change's sum, for the chart, `median tokens` and `lacked`, and adds per-round,
per-role values for the JSON: the two-role forms first — `tokens review (\d+), security (\d+)`, `tokens (\d+) \+ (\d+)`,
`\(review (\d+)k, security (\d+)k\)` ×1000, `tokens (\d+) review, (\d+) security` — then `tokens (\d+)` on a line opening with
one role, credited to it; a both-role line's single figure is recorded under the role `both`, credited to neither; `unavailable` a
gap. D1's tail, `executor (\S+) · model (\S+) · effort (\S+)`, gives a Claude record its executor, model and effort, else `null`. `_codex_sessions(repo)`, reading `$CODEX_HOME/sessions`, else `~/.codex/sessions`: every session
with a `thread_spawn` source, its role from `agent_path`'s last segment when it opens with `review` or `security`, any other
(`fix_r1`, `sandbox_subagent`) left out, matched to a round by `git.repository_url` against the
repo's `origin` URL, else the parent's `cwd` among `git worktree list` — run without
failing on a repo that is no git repo — and the round's window — from the last `freeze` line before the round's `fan-out`, whatever round
it names (Step 6's re-freeze is logged under the round it closes), to its `verdicts` plus one minute —
local times to UTC by `zoneinfo`; every session in a window summed. A session is the change's only when its parent's `cwd` is
that change's worktree — its last path part the change id — or, for a session run in the primary, when no other version of the repo
has a round overlapping the window; any other is no round's. A record whose `verdicts` line names `executor claude` is never filled
from a session. `main` writes `out.with_name("review-metrics.json")` through `_write`:
`{"generated", "records": [{repo, change, run, round, role, executor, model, effort, tokens, sessions, source}]}`, `source`
`status-log` or `codex-session`, a gap `null`. `skills/mf-review-metrics/SKILL.md` names the file.

### D6

The delta's review-metrics requirement also drops "a Codex log SHALL be a gap", since Codex's tokens now come from its
sessions, and names `_cost_cell`'s `<read> of <spawns>`. D50 reads "…the findings files, status logs and run logs of the repos the operator's config names, and the operator's Codex
sessions, … writes one self-contained page and its data, `review-metrics.json`, beside it…".

## Tests

`git grep -c '^def test_' 61daff7 -- tests/test_conduct.py tests/test_metric_scripts.py tests/test_review_metrics.py` counts the
files at the cut. Added: `test_run_metrics_read_the_run_logs` and `test_run_metrics_read_cost_and_review_yield` (`tests/test_metric_scripts.py`)
over a fixture run directory, each metric a number or a gap — `T2`: no test reads a run for metrics; `test_tokens_are_read_per_role`
and `test_codex_sessions_fill_the_rounds` (`tests/test_review_metrics.py`). Extended: `test_a_station_runs_on_its_executor` with a
models file's effort in the spawn line; `test_a_small_cap_is_granted_automatically`, which spawns converge twice in one run, with
its `-2.log`; `test_run_logs_give_cost_turns_and_tokens_per_station`
with a `-2.log`; `test_the_status_log_gives_duration_tokens_and_the_cap` with the per-role figures. None deleted.

## Dependencies

None.

## Risks / Trade-offs

- **Free text:** the status log is the conductor's prose; a form not in F8 reads as a gap, never a wrong number.
- **Codex's tokens count cached input:**; the comparison reads like with like.

## Verdict

Ready to build.
