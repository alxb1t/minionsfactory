---
name: mf-review-metrics
description: Draw one HTML page of review metrics — rounds, findings, verdicts, workers, duration and tokens, per role, executor and model, the headline numbers, and each station's cost, turns and tokens per change — and its data, review-metrics.json, from the .minions/changes — in a repo no run has moved, the .minions/findings and .minions/runs — of the repos ~/.config/minionsfactory/review-metrics.toml names and every repo a run started in, and the operator's Codex sessions, and the transcripts of the session folders its `sessions` key lists, booked as a `plan` and an `operator` station per change. Use to compare review models on data; an operator tool, never part of a run.
---

# mf-review-metrics — what review found, and what it cost

> **Your role is REPORT.** You run the script and pass on its numbers. You recommend nothing, and you write into no
> repo.

## Parameters

None: the repos and the page's path are in `$XDG_CONFIG_HOME/minionsfactory/review-metrics.toml`, else
`~/.config/minionsfactory/review-metrics.toml`, and the run's repo list, `~/.mf-ship-origin/repos`, which `conduct.py run`
keeps, adds every repo a run started in that holds `.minions/`. A person may pass `--config`, `--repo` or `--out` to
override; `--repo` reads no repo list.

The config's `sessions = [...]` lists the Claude Code project folders whose session transcripts to read, each resolved
against the config's folder. No key, no transcript read, and no `plan` or `operator` row.

## Run

`uv run --script <this package>/scripts/review_metrics.py [overrides]`. Exit 2 → **halt**, copying what it printed:
neither the config nor the run's repo list names a repo, or the config names no page.

Beside the page it writes `review-metrics.json`: one record per round and role — its executor, model, effort, tokens,
dollars and source, a gap as `null`; `workers`, the cost per worker — each converge worker, booked by its log name, or an older
log's subagent by its description, with its role, round, run, model, tokens, first-turn context and dollars, priced by `prices.toml`; and `stations`, each
change's stations, the cut and the supervisor among them, with their dollars, turns, tokens, seconds and first-turn
context. The first-turn context is what a log's first turn read: its input, cache-read and cache-write tokens. A
subagent's tokens and dollars are a gap: Claude's log holds no subagent's final output count. A record's dollars are its
run, round and role's workers'. A Codex worker's tokens come from its session in `$CODEX_HOME/sessions`, else
`~/.codex/sessions`, matched to its round by the round's window and where its parent ran: the change's worktree, or the
primary when no other version's round overlaps. A round its line names `executor claude` is never filled from a session.

The data also holds `roles`, one per change and role with its executor; `shadow`, `overlap.py`'s counts per shadow
round 1; `escapes`, each traced to the round 1 that missed it; and `headline`. The page opens with the four headline
numbers: each executor's share of the shadow rounds' distinct blockers it alone caught; escapes per version; converge's
dollars per confirmed blocker, by the checkers' executors; and, per executor of the checker that raised it, the share of
cards whose first verify after `fixed` read `verified`.

A transcript is read for numbers, ids and times alone: each message's id, time, model and usage, priced once by
`prices.toml`, and each call's marker, `brief=` and `from=` paths and the path it wrote, compared in memory and never
written. A session with no `mf-*` skill call or `conduct.py` command is not read, and a session a station log's `init`
names is skipped. The `plan` station is the messages from an `mf-plan` call to the last write of its brief, bound to
the ids a matched `conduct.py cut` queued and split equally between them, else `unbooked`. The `operator` station is
every other message, booked to the version the nearest earlier run-log line or queued id names, else `unbooked`. Both
are `stations` rows and columns of the page's cost table, and the rows with no change are its `unbooked` table. They
rank hand work, they do not bill it.

## Report

**Close-out:** at most three sentences — the page's path, the repos and changes read, and the fields some repos lack;
then the role, executor and model table it printed, with each group's median duration and tokens. The cost per station,
with its first-turn context, is on the page, and the cost per worker in the data, at list price: it ranks, it does not
bill. No advice: the choice of model is the person's.
