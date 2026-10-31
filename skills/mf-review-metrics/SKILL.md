---
name: mf-review-metrics
description: Draw one HTML page of review metrics — rounds, findings, verdicts, workers, duration and tokens, per tier and model — from the .minions/findings of the repos ~/.config/minionsfactory/review-metrics.toml names. Use to compare review tiers and models on data; an operator tool, never part of a run.
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

## Report

**Close-out:** at most three sentences — the page's path, the repos and changes read, and the fields some repos lack;
then the per tier × model table it printed. No advice: the default tier is the person's decision.
