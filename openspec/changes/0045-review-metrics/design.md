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
| Older files: the same nine frontmatter keys since v0.10 (the oldest on the machine, a `0008-*_review.md`), findings as `- **severity:** <grade>` bullets; cards since v0.14, `Priority:` sometimes in backticks, old security categories in brackets (`medium · security (integrity)`); status logs `<change-id>_status_log.md` since v0.18; no file on the machine has `tier:` yet | [D4](#d4) parses each field on its own |
| `skills/mf-converge/SKILL.md:276-277`: security blocks on `critical` and `high`, review on `blocking`; `:290-292` the `## Resolution log`'s transitions, `<from> → <to>` — the largest repo's hold `fixed → verified` 241 times, `fixed → open` 4 | [D4](#d4)'s `blocking`, `verified` and `reopened` |
| Status logs' `start` lines name the engine as `engine generic` or `engine: generic`; `done` lines say `N cards to backlog` or `1 card to backlog`, some none; a `halt` at the cap names `cap` | [D4](#d4)'s `engine`, `to_backlog` and `capped` |
| The operator's two named repos, at the cut: 280 and 100 files in `.minions/findings/` | [D7](#d7)'s live run |
| `docs/principles.md:127-144` *The repo reaches nothing outside itself* — three exceptions | [D5](#d5) adds the station's |
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
| D1 | The config is `$XDG_CONFIG_HOME/minionsfactory/review-metrics.toml`, else `~/.config/minionsfactory/review-metrics.toml`: `repos = [<paths>]`, `out = "<page path>"`, a relative path resolved against the config's directory; `--config`, `--repo` (repeatable) and `--out` override, `--out` resolved against the cwd; no repo from either → exit 2 naming the path looked for | The person's infra-as-config rule; flags only override (Q2) | The vault; a repo |

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | `skills/mf-review-metrics/scripts/review_metrics.py`, stdlib PEP 723 (`requires-python = ">=3.12"`, `dependencies = []`); exits `0` written · `2` cannot run; on `0` it prints the page's path, `repos: <n> · changes: <n>`, the tier × model table as markdown, and `lacked:` with each gap field and its count | MF's script rule | A dependency |

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | It loads `chart` and `_STYLE` from `../../mf-build/scripts/metrics.py`, resolved from its own file (`Path(__file__)`), with `importlib`; no chart code copied | One chart in MF (Q3) | A copy; a shared module |

### D4

| id | decision | because | rejected |
|---|---|---|---|
| D4 | **A record per change per repo**, each field parsed on its own and `None` when unreadable | Every era stays usable; a gap is never a zero (Q4, Q5) | An era detector |

A change's files are `.minions/findings/<change-id>_review.md`, `_security.md` and `_status_log.md`; a change with
any of them is a record. **Clean** means a file's `verdict: clean`.

| field | read from |
|---|---|
| `repo`, `change`, `reviewed` | the repo's directory name; the file name before `_review.md`, `_security.md` or `_status_log.md`; the frontmatter's `reviewed`, the review file's first |
| `tier`, `model`, `mode` | the review file's frontmatter, else the security file's; `tier` absent → `unknown` in the tables |
| `engine` | a status log `start` line's `engine <word>` or `engine: <word>` |
| `workers` | the review and security files' `workers`, summed |
| `packet_included`, `packet_skipped` | `packet`'s entries before `skipped:`, and after it, counted |
| `rounds` | the review file's `round`, else the security file's |
| `findings`, by severity and category | every card's `Priority:`, backticks stripped: severity the first `·` field, category the third, else the bracketed word after the role; a file with no card, its `- **severity:** <grade>` bullets; a file with neither, `0` when clean, else a gap |
| `blocking` | the findings graded `blocking` in review and `critical` or `high` in security |
| `confirmed`, `plausible`, `plausible_verified`, `refuted` | the cards' `Verdict:` first word; the `plausible` cards whose **Status** is `verified`; the `## Refuted` list's entries — each a gap in a file with no card carrying `Verdict:` |
| `verified`, `reopened` | the `## Resolution log`'s `→ verified` transitions; its `→ open` transitions from `fixed`, `wontfix` or `accepted` |
| `inconclusive` | the lines holding `inconclusive`, outside the cards — a gap in a file with no `tier:` |
| `duration`, `tokens`, `capped`, `to_backlog` | the status log: each `## Run` heading's first to last event time, summed; the `tokens <n>` of `verdicts` lines, summed, a gap when none has one; `1` for a `halt` line naming `cap`, else `0`; the `done` line's `N card(s) to backlog`, a gap when it names none |

**Plausible, verified** stands in for the brief's "plausible later confirmed": a card's `Verdict:` is never rewritten,
so a fix verified against it is the record there is.

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
| D7 | **The page**, every chart drawn by the loaded `chart` over the repo's changes in `reviewed` order: see the layout below. Text escaped; no script | Q4, Q6, method Q37 and Q39; D43's page rules | A JavaScript chart library; a recommendation |

```
header         repos read · changes read
per repo       <section class="repo">, opening its own line
  table        changes · median rounds · findings, blocking, verified, reopened per change · capped · to backlog
  severity     findings per grade, a row per grade the repo used
  charts       rounds · findings · blocking · verified · reopened · capped · to_backlog · duration · tokens
tier × model   a row per tier, model and engine, `unknown` for a gap: changes · median rounds · findings and
               blocking per change · median workers · confirmed, plausible, plausible verified, refuted ·
               inconclusive · packet included and skipped · top categories · median duration · median tokens
lacked         per repo, each field and the count of records with a gap
```

Each median shows its count beside it.

The live run reads the operator's config, written beside the container before the run, so no repo names the repos it
reads (Q1): `../mf_metrics_probe/review-metrics.toml`, holding the operator's two named repos as `repos` and
`out = "page.html"`. The script runs with `--config` on it (Q12). The worker's shell is confined to the container;
Python is not.

## Tests

`tests/test_review_metrics.py` is new, loading the script by path (`T1`: the reader and the page are unit-testable);
no test is removed.

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 68 | 6 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `68 tests collected` at the cut, `74 tests collected` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

| test | holds |
|---|---|
| `test_no_config_exits_2_naming_the_path` | D1's halt, nothing written |
| `test_each_era_parses_with_gaps` | a pre-card file with `- **severity:**` bullets, a clean file with no finding, a carded file with no tier and a backticked `Priority:`, a v0.37 file with `Evidence:`, `Verdict:` and `## Refuted`: each record's fields, `0` for the clean file, `None` where absent |
| `test_the_resolution_log_counts_verified_and_reopened` | `fixed → verified`, `fixed → open` and `wontfix → open` counted; a sentence saying "nothing reopened" counts nothing |
| `test_the_status_log_gives_duration_tokens_and_the_cap` | runs summed, `tokens unavailable` a gap, a cap halt, `1 card to backlog` and `3 cards to backlog`, `engine: generic` |
| `test_the_page_draws_charts_and_lists_gaps` | `<section class="repo">` per repo, the severity table, the tier × model table with an `unknown` row, an `<svg` from the loaded `chart`, the gaps list, escaped text, no `<script`; the printed summary |
| `test_overrides_win_over_the_config` | `--repo` and `--out` over the config's; a relative `out` resolved against the config's directory |

## Dependencies

None.

## Risks / Trade-offs

- **A free-text field reads wrong in an old file** → that field is a gap, and the page lists it; no number is invented.
- **Medians over few changes mislead** → the tables show the count beside each median.
- **The live run reads repos outside the container** → read-only, by Python, never written; its config is the
  operator's, in the probe, not the person's `~/.config`.
- **A free-text status line reads as a number it is not** → each status-log field is a fixed pattern from
  [D4](#d4), and the test feeds it real lines.

## Migration Plan

```
1 the reader ─▶ 2 the page ─▶ 3 the station and the record ─▶ 4 the live run ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible; the probe is deleted at its end.

## Verdict

Ready to build. Acceptance: the script reads every era with gaps, draws the page through `chart()`, halts without a
config; the principle and D50 record it; the live run's page holds a section for each repo its config names.
