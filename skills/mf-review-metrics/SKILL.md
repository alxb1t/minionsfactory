---
name: mf-review-metrics
description: Draw one HTML page of review metrics — rounds, findings, verdicts, workers, duration and tokens, per model, and each station's cost, turns and tokens per change — and its data, review-metrics.json, from the .minions/changes — in a repo no run has moved, the .minions/findings and .minions/runs — of the repos ~/.config/minionsfactory/review-metrics.toml names and the operator's Codex sessions. Use to compare review models on data; an operator tool, never part of a run.
---

# mf-review-metrics — what review found, and what it cost

> **Your role is REPORT.** You run the script and pass on its numbers. You recommend nothing, and you write into no
> repo.

## Parameters

None: the repos and the page's path are in `$XDG_CONFIG_HOME/minionsfactory/review-metrics.toml`, else
`~/.config/minionsfactory/review-metrics.toml`. A person may pass `--config`, `--repo` or `--out` to override.

## Run

`uv run --script <this package>/scripts/review_metrics.py [overrides]`. Exit 2 → **halt**, copying what it printed:
the config is missing or names no repo.

Beside the page it writes `review-metrics.json`: one record per round and role — its executor, model, effort, tokens
and source, a gap as `null`. A Codex worker's tokens come from its session in `$CODEX_HOME/sessions`, else
`~/.codex/sessions`, matched to its round by the round's window and where its parent ran: the change's worktree, or the
primary when no other version's round overlaps. A round its line names `executor claude` is never filled from a session.

## Report

**Close-out:** at most three sentences — the page's path, the repos and changes read, and the fields some repos lack;
then the per model table it printed. The cost per station is on the page, at list price: it ranks, it does not bill. No
advice: the choice of model is the person's.
