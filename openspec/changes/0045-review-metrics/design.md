# Review metrics — design

A stdlib script reads every repo's findings and status logs leniently and draws one page through `mf-build`'s chart; a
thin skill runs it; the principle gains the station's exception. Verdict: ready to build. Scope is
[the proposal](proposal.md); behaviour is [the delta](specs/sdd/spec.md).

## Context

Premises were re-checked on `main` at `bb8d8c0` (v0.37.0) before the cut.

| evidence at the cut | implication |
|---|---|
| `skills/mf-build/scripts/metrics.py` (643 lines, stdlib PEP 723): `Metric = dict[str, Any]` `:47`, `Number = int \| float` `:49`, `chart(metric, points)` `:416` — `points` of `(label, value, is_this_one)`, a gap for `None`, using only `title` and `watch`; `_STYLE` `:476` | [D3](#d3) loads both by path |
| `tests/test_metrics.py:20-26` loads a script with `importlib.util.spec_from_file_location` | the new tests do the same |
| `skills/mf-converge/SKILL.md`: the frontmatter's fourteen keys `:248-266` (`tier`, `mode`, `workers`, `model`, `packet` since v0.37); the card's `Evidence:`, `Verdict:` and `<severity> · <role> · <category>`; `## Refuted`; the status log's `## Run N — <date> <time>`, `HH:MM:SS · round N · <event> — <detail>`, `verdicts … tokens <n>` or `tokens unavailable` `:81`, `done — converged in N rounds · M cards to backlog` | [D4](#d4)'s fields |
| Older files: the same nine frontmatter keys since v0.10 (isekai's oldest, `0008-one-path_review.md`); cards since v0.14; status logs since v0.18 | [D4](#d4) parses each field on its own |
| This machine's findings, at planning: isekai 74 review files, tropicsamui.rent 21, gpunit 15, minionsfactory 11, kitchen_scheduler_archived 8, agent-iac 4, synthetic_portraits 3 | [D7](#d7)'s live run |
| `docs/principles.md:127-143` *The repo reaches nothing outside itself* — three exceptions | [D5](#d5) adds the station's |
| D43 (`docs/decisions.md:232-245`): every number from a command; no analysis platform; the page never tracked | [D5](#d5)'s D50 sits after it |
| `README.md`'s skills table ends with `mf-ship`'s row; `AGENTS.md:30-33`'s skill list is edited by simplify in the same run | [D6](#d6) adds a README row only |
| `uv run pytest --collect-only -q \| tail -1` prints `68 tests collected` | [Tests](#tests) |

## Goals / Non-Goals

**Goal:** one page that shows, per tier and model, what review found and what it cost, across every repo on the
machine.

**Non-goals:** see [the exclusions](proposal.md#not-in-this-change).

## Decisions

The grilling settled these choices (the brief's method Q37, Q39 and Q1–Q12); the build does not reopen them.

### D1

| id | decision | because | rejected |
|---|---|---|---|
| D1 | The config is `$XDG_CONFIG_HOME/minionsfactory/review-metrics.toml`, else `~/.config/minionsfactory/review-metrics.toml`: `repos = [<paths>]`, `out = "<page path>"`; `--config`, `--repo` (repeatable) and `--out` override; no repo from either → exit 2 naming the path looked for | The person's infra-as-config rule; flags only override (Q2) | The vault; a repo |

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | `skills/mf-review-metrics/scripts/review_metrics.py`, stdlib PEP 723 (`requires-python = ">=3.12"`, `dependencies = []`); exits `0` written · `2` cannot run | MF's script rule | A dependency |

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | It loads `chart` and `_STYLE` from `../../mf-build/scripts/metrics.py`, resolved from its own file (`Path(__file__)`), with `importlib`; no chart code copied | One chart in MF (Q3) | A copy; a shared module |

### D4

| id | decision | because | rejected |
|---|---|---|---|
| D4 | **A record per change per repo**, each field parsed on its own and `None` when unreadable | Every era stays usable; a gap is never a zero (Q4, Q5) | An era detector |

| field | read from |
|---|---|
| `repo`, `change`, `reviewed` | the repo's directory name; the file name before `_review.md`; the frontmatter's `reviewed` |
| `tier`, `mode`, `model`, `packet_skipped` | the frontmatter, both files; `packet`'s `skipped:` count |
| `workers` | the review and security files' `workers` summed |
| `rounds`, `clean` | the review file's `round`; both `verdict: clean` |
| `findings`, `blocking`, by severity and category | every card's `Priority:` — severity its first word, category its third when present |
| `confirmed`, `plausible`, `refuted` | the cards' `Verdict:`; the `## Refuted` list's entries |
| `reopened` | the `## Resolution log` lines naming `reopen` |
| `inconclusive` | the Summary lines holding `inconclusive` |
| `duration`, `tokens`, `capped`, `to_backlog` | the status log: each run's first to last event, summed; the `tokens <n>` of `verdicts` lines, summed; a `halt` naming the cap; the `done` line's `N cards to backlog` |

### D5

| id | decision | because | rejected |
|---|---|---|---|
| D5 | The principle gains a fourth exception; D50 records the station, after D43 | Operator tooling, shaped like the brief's exception (Q1) | A repo reporting outward |

`docs/principles.md:131-134`'s list: the metrics bullet's closing `).` becomes `);`, and after it add:

```markdown
- the review-metrics station's read-only reads of the `.minions/findings/` of repos the operator names, and its page
  written to the path the operator gives — neither named in any repo
  ([D50](decisions.md#d50--review-metrics-are-read-across-repos-and-drawn-on-one-page)).
```

`docs/decisions.md`, after D43:

```markdown
### D50 · Review metrics are read across repos and drawn on one page

**`mf-review-metrics` reads the findings files and status logs of the repos the operator's config names, leniently —
every unreadable field a gap — and writes one self-contained page: tables per repo and per tier × model, charts over
changes through `mf-build`'s chart. Numbers only; it writes into no repo and is no station of the line.**

- **Why:** choosing a review tier, and seeing what it costs, needs the record of every past converge in one place.
- **Rejected:** a recommendation on the page · reading inside a run · a copy of the chart code.
```

### D6

| id | decision | because | rejected |
|---|---|---|---|
| D6 | `skills/mf-review-metrics/SKILL.md` is a thin operator skill; `README.md`'s skills table gains its row after `mf-ship`'s; `AGENTS.md` is left alone | Simplify edits `AGENTS.md`'s skill list in the same run — one line, two edits, a halt at integrate (Q11) | Listing it in `AGENTS.md` |

`skills/mf-review-metrics/SKILL.md`, whole:

```markdown
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
```

`README.md`, after `mf-ship`'s row, one line:

```markdown
| [`mf-review-metrics`](skills/mf-review-metrics/SKILL.md) | draw one page of review metrics across repos — per tier and model — from past findings; an operator tool |
```

### D7

| id | decision | because | rejected |
|---|---|---|---|
| D7 | **The page**: a header (repos and changes read); per repo a `<section class="repo">` opening its own line — its table (changes, median rounds, findings and blocking per change) and its charts over changes by `reviewed` (rounds, findings, blocking, duration, tokens); a table per tier × model (median rounds, findings and blocking per change, refuted share, median duration, median tokens); "what each repo lacked" — per field, the count of records with a gap. Text escaped; no script | Q4, Q6; D43's page rules | A JavaScript chart library |

The live run, from this worktree: a `python3` one-liner using `pathlib.Path.home()` writes the operator's two named repos —
`Path.home() / "Developer/tropicsamui.rent"` and `Path.home() / "Developer/AI_Engineering/isekai"`, the two with the
most findings — as `repos`, and `out = "../mf_metrics_probe/page.html"` to
`../mf_metrics_probe/review-metrics.toml`; the script runs with `--config` on it (Q12). The worker's shell is confined to the container; Python is not.

## Tests

`tests/test_review_metrics.py` is new, loading the script by path (`T1`: the reader and the page are unit-testable);
no test is removed.

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 68 | 5 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `68 tests collected` at the cut, `73 tests collected` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

| test | holds |
|---|---|
| `test_no_config_exits_2_naming_the_path` | D1's halt, nothing written |
| `test_each_era_parses_with_gaps` | a no-card file, a carded file with no tier, a v0.37 file with `Evidence:`, `Verdict:` and `## Refuted`: each record's fields, `None` where absent |
| `test_the_status_log_gives_duration_tokens_and_the_cap` | runs summed, `tokens unavailable` a gap, a cap halt, `cards to backlog` |
| `test_the_page_draws_charts_and_lists_gaps` | `<section class="repo">` per repo, the tier × model table, an `<svg` from the loaded `chart`, the gaps list, escaped text, no `<script` |
| `test_overrides_win_over_the_config` | `--repo` and `--out` over the config's |

## Dependencies

None.

## Risks / Trade-offs

- **A free-text field reads wrong in an old file** → that field is a gap, and the page lists it; no number is invented.
- **Medians over few changes mislead** → the tables show the count beside each median.
- **The live run reads repos outside the container** → read-only, by Python, never written; its config lives in the
  probe, not the person's `~/.config`.

## Migration Plan

```
1 the reader ─▶ 2 the page ─▶ 3 the station and the record ─▶ 4 the live run ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible; the probe is deleted at its end.

## Verdict

Ready to build. Acceptance: the script reads every era with gaps, draws the page through `chart()`, halts without a
config; the principle and D50 record it; the live run's page holds a section for each of its two repos.
