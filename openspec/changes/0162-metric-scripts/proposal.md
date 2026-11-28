---
bump: minor
---

# Metric scripts

The metric scripts, `scripts/metrics/run.py` and `scripts/metrics/debt.py`, read the run log, the status log, the findings, `build.done` and the debt file through the home modules, and the `prices.toml` parsers become one module; the home gains the list of run logs, the count of a `verdicts` line, the refuted section, `prices.py` and `eras.py`.

Reading map: [design](design.md) holds the decisions, the test cost and the risks, [cases](cases.md) the pinned cases, the settled readings and the asserts that turn, [tasks](tasks.md) its phases.

## Why

Each metric script keeps its own parser of a format a home module owns: the run log's clock and file list, the status log's heading and mark, a findings card, the head of `build.done`, a debt card, and `prices.toml`, which `review_metrics.py` parses a second time. The two parsers of each format answer differently on today's files, so a metric and a station can disagree on one file. This is the version of 5e that moves the metric scripts onto the home ([D12](design.md#d12)).

## What Changes

- The home gains `runlog.logs`, `statuslog.blocking`, `findings.refuted`, the new `skills/mflib/prices.py` and the new `skills/mflib/eras.py`, each with unit cases, and `runlog.timed` passes by a clock that is no time of day ([D1](design.md#d1) to [D5](design.md#d5)).
- `scripts/metrics/run.py` reads the run log, the status log, the findings and `build.done`, and `scripts/metrics/debt.py` and `run.py` read the debt file, through the home; each format constant the home owns is removed from them ([D6](design.md#d6) to [D10](design.md#d10)).
- `run.py` and `review_metrics.py` read `prices.toml` through `prices.rows`; `review_metrics.py` changes in its prices lines alone ([D11](design.md#d11)).
- A phase 1 pin holds today's side of every case; phases 3 and 4 turn the listed asserts, and no other assert changes ([D12](design.md#d12)).
- The entries of `run.py` and `debt.py` leave the format list of `tests/test_structure.py`, and the module map gains the rows of the new modules and changes the rows of the scripts ([D13](design.md#d13)).
- The recipes, the threat model and decision D83 say what is true after ([D17](design.md#d17)).
- The spec's requirement *Each release records its run* changes to say how each metric reads its files; *One module writes and parses the run log*, *One module parses a status log's runs and its verdicts line* and *One module writes and parses a findings file* each gain what the home now gives; *One module reads the price table* and *One module reads the formats an old run left* are new.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements named under *What Changes*, in [the delta](specs/sdd/spec.md).

## Impact

- `skills/mflib/runlog.py`, `skills/mflib/statuslog.py` and `skills/mflib/findings.py` gain one function each; `skills/mflib/prices.py` and `skills/mflib/eras.py` are new.
- `scripts/metrics/run.py` and `scripts/metrics/debt.py` read the home's parsers; `skills/mf-review-metrics/scripts/review_metrics.py` changes in its prices lines.
- `tests/test_metric_pins.py`, `tests/test_prices.py` and `tests/test_eras.py` are new; `tests/test_runlog.py`, `tests/test_statuslog.py`, `tests/test_findings.py`, `tests/test_viewer.py`, `tests/test_metric_scripts.py`, `tests/test_review_metrics.py` and `tests/test_structure.py` change as [tasks](tasks.md) names.
- `docs/modules.md`, `docs/recipes.md`, `docs/decisions.md` and `THREAT_MODEL.md` say what is true after.

## Not in this change

- `review_metrics.py` but its prices lines: 5e3 `review-metrics`, which also gives `prices.Unreadable` its meaning there and takes `eras.py` for its own old forms ([D11](design.md#d11)).
- A worker log's JSON lines — `_json`, `_summed`, `_spawn_line`, `_spent`, `log`, `checkers`, `spent`, `quota`, `role_tokens` — and the price arithmetic: no module owns them. Phase 1 pins their survivors all the same.
- The proposal's `debt:` and `backlog:` list, `paid`, and the `start` line's `versions` detail, `_versions`: they stay in `run.py`.
- `run.py`'s git calls — `lead`, `lines`, `per_line`, `commits`' two — and `debt.py`'s.
- The status log's heading date and its events' clocks: `run.py` reads neither, so `statuslog.runs` gains none.
- `runlog.parse` and `runlog.events`, the conductor's: a clock of `25:00:00` stays an event there.
- The dated-note and `R-a` cards of isekai's changes: the module counts them as cards, no metric's value moves by it, and no `eras` reader reads them.
- Summer time: an event's moment is the local clock's, as the viewer's; no case sets a zone.
- The items [cases](cases.md#the-readings-settled) lists as left for a later round of the person's.
- A corpus case for `run.py` and `debt.py`: no case reads them today, and a new one is a scope the brief did not settle ([D16](design.md#d16)).
