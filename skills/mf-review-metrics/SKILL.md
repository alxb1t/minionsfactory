---
name: mf-review-metrics
description: Draw one HTML page of review metrics — rounds, findings, verdicts, workers, duration and tokens, per role, executor and model, the headline numbers, and each station's cost, turns and tokens per change — and its data, review-metrics.json, from the .minions/changes — in a repo no run has moved, the .minions/findings and .minions/runs — of the repos ~/.config/minionsfactory/review-metrics.toml names and every repo a run started in, and the operator's Codex sessions. Use to compare review models on data; an operator tool, never part of a run.
---

# mf-review-metrics — what review found, and what it cost

> **Your role is REPORT.** You run the script and pass on its numbers. You recommend nothing, and you write into no
> repo.

## Parameters

None: the repos and the page's path are in `$XDG_CONFIG_HOME/minionsfactory/review-metrics.toml`, else
`~/.config/minionsfactory/review-metrics.toml`, and the run's repo list, `~/.mf-ship-origin/repos`, which `conduct.py run`
keeps, adds every repo a run started in that holds `.minions/`. A person may pass `--config`, `--repo` or `--out` to
override; `--repo` reads no repo list.

## Run

`uv run --script <this package>/scripts/review_metrics.py [overrides]`. Exit 2 → **halt**, copying what it printed:
neither the config nor the run's repo list names a repo, or the config names no page.

Beside the page it writes `review-metrics.json`: one record per round and role — its executor, model, effort, tokens,
dollars and source, a gap as `null`; `workers`, the cost per worker — each converge subagent and mailbox checker, with
its role, round, model, tokens, first-turn context and dollars, priced by `prices.toml`; and `stations`, each change's
stations, the cut and the supervisor among them, with their dollars, turns, tokens, seconds and first-turn context. The
first-turn context is what a log's first turn read: its input, cache-read and cache-write tokens. A record's dollars are
its round and role's workers'. A Codex worker's tokens come from its session in `$CODEX_HOME/sessions`, else
`~/.codex/sessions`, matched to its round by the round's window and where its parent ran: the change's worktree, or the
primary when no other version's round overlaps. A round its line names `executor claude` is never filled from a session.

The data also holds `roles`, one per change and role with its executor; `shadow`, `overlap.py`'s counts per shadow
round 1; `escapes`, each traced to the round 1 that missed it; and `headline`. The page opens with the four headline
numbers: each executor's share of the shadow rounds' distinct blockers it alone caught; escapes per version; converge's
dollars per confirmed blocker, by the checkers' executors; and, per executor of the checker that raised it, the share of
cards whose first verify after `fixed` read `verified`.

## Report

**Close-out:** at most three sentences — the page's path, the repos and changes read, and the fields some repos lack;
then the role, executor and model table it printed, with each group's median duration and tokens. The cost per station,
with its first-turn context, is on the page, and the cost per worker in the data, at list price: it ranks, it does not
bill. No advice: the choice of model is the person's.
