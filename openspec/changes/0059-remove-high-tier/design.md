# Remove the high tier — design

What leaves with the high tier, and what the one depth keeps. Verdict at the end: ready to build.

## Context

Read at `22c1af8` (v0.47.4).

- **The measure:** v0.37's calibration (`0042-review-method`'s `evidence/calibration.md`): seeded-high found 5 of 5 with 89
  workers and 55.6 M tokens; seeded-standard found 5 of 5 with 2 workers and 4.2 M.
- **`skills/mf-converge/SKILL.md`:** the tier in the `start` and `fan-out` events (`:76`, `:78`) and their examples (`:94-95`);
  *The tier and the workers* (`:102-108`), linking `references/high-tier.md` (`:107`); the dispatch (`:244`) and each
  worker's inputs (`:257`); the frontmatter's `tier: standard | high` (`:295`); Step 7's "Step 3's tier" (`:401`); the
  close-out (`:459`). `:315` and `:422` name severity, not the tier.
- **`references/high-tier.md`** (`:1-37`) is the whole high depth.
- **`references/generic-review.md`** `:4`, `:16`, `:65` and **`generic-security.md`** `:4`, `:47`: "the tier changes who runs
  it", the tier among the inputs, the cap's "consider tier=high or a split".
- **`skills/mf-ship/scripts/conduct.py`:** `TIERS` (`:65`); the converge prompt's `{tier}` (`:119`); `_tier` (`:1424-1437`);
  the grant clause appended to it (`:1976-1981`). `skills/mf-ship/SKILL.md:96`: "at the tier the cut chose".
- **`skills/mf-cut-change/SKILL.md`:** the **Tier** bullet (`:266-267`) and the TOML's `tier =` line (`:284`).
- **`skills/mf-review-metrics/scripts/review_metrics.py`:** `IDENTITY` (`:50`); `inconclusive` counted when `"tier" in front`
  (`:245`); the record's `tier` (`:351`); `tier_table` (`:452-461`) and its heading (`:553`), its printer (`:561`, `:568`).
  `skills/mf-review-metrics/SKILL.md:3`, `:24`.
- **Docs:** D49 (`docs/decisions.md:221-230`), D47's "Converge runs at the tier the cut chose." (`:451`), D50's "per tier ×
  model" and "choosing a review tier" (`:250`, `:253`); `README.md:34`, `:47`; `skills/mf-release/SKILL.md:280`.
- **Tests:** `tests/test_conduct.py:3339-3354`, `:3387` in `test_a_worker_carries_the_allowlist_and_a_denial_is_named`;
  `:2765` in `test_a_grant_buys_one_round`; `tests/fake_worker.py:73`; `tests/drill_resume.py:147`;
  `tests/test_review_metrics.py` in `test_each_era_parses_with_gaps` (`:66-210`) and `test_the_page_draws_charts_and_lists_gaps`
  (`:279-333`).

## Goals / Non-Goals

**Goals:** one review depth, nothing left that names the other; past data still parses.

**Non-Goals:** the large-diff split; rewriting old findings or models files.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | Converge runs one depth; `high-tier.md` goes; a `tier=` halts | the person, 2026-11-03: one way to run the review | keeping `standard` as a parameter's only value |
| [D2](#d2) | The run passes no tier; the cut writes none; an old one is ignored | the person: new records carry none, old ones are ignored | halting on an old `tier` key: churn in every repo |
| [D3](#d3) | No tier in the findings, the log or the metrics; `## Refuted` marks the era | the person: free to break | keeping `tier:` as an era mark |
| [D4](#d4) | D49, D47, D50, `README.md`, `mf-release` say one depth | A7 | — |

### D1

`skills/mf-converge/SKILL.md`:

- *The tier and the workers* → *The workers — before checker dispatch*: "**Every host runs MF's method:** each worker loads
  [review](references/generic-review.md) or [security](references/generic-security.md), resolved from the installed package.
  Each role is one fresh worker. A `tier=` given → **halt**: the `tier` parameter was removed." Its worker paragraphs stay.
- `:76` and `:78` drop "the tier"; `:94-95`'s examples drop `· standard`; `:244` cites *The workers*; `:257` → "its mode and
  reference"; `:295`'s frontmatter line goes; `:401` → "with Step 3's inputs and dispatch rules"; `:459` drops "the tier, and".
- `references/high-tier.md` is deleted.
- `generic-review.md:4` and `generic-security.md:4`: "This is MF's method on every host; the tier changes who runs it, never
  what it checks." → "This is MF's method on every host."; `generic-review.md:16` "tier and mode" → "mode"; the cap line in both →
  "`over the standard cap — consider a split`".

### D2

`conduct.py`: `TIERS` and `_tier` go. `PROMPTS["converge"]` → `"Run the mf-converge skill for change {change}{grant}."`;
`Run.advance` formats it with `grant=" and grant=yes"` for a granted round, else `""`. No `[converge].tier` is read.
`tests/fake_worker.py:73`'s pattern → `r" (?:with|and) (?!merge=yes\b)\w+=\w+"`, so a returned clause changes the call; `tests/drill_resume.py:147` writes no `tier`.

`skills/mf-ship/SKILL.md:96` → "Converge runs MF's method." `skills/mf-cut-change/SKILL.md`: the **Tier** bullet and the TOML's
`tier =` line go.

### D3

`review_metrics.py`: the record's `tier` goes; `IDENTITY` becomes 2; `tier_table` → `model_table`, a row per model and engine;
the heading `<h2>model</h2>`; `inconclusive` is counted when the file holds a `## Refuted` section, else a gap.
`skills/mf-review-metrics/SKILL.md:3` and `:24` → "per model". Old `tier:` lines are read as nothing.

### D4

- **D49** → "### D49 · One review method, one depth"; its rule: "**Converge runs MF's method at one depth — one fresh worker per
  role, from a packet given up front. The review and security files are the same for every change.**" *Rejected* gains "· a
  high tier: 5 of 5 at both depths, 89 workers and 55.6 M tokens against 2 and 4.2 M".
- **D47** `:451`: "Converge runs at the tier the cut chose." goes.
- **D50** `:250` "per tier × model" → "per model"; `:253` "choosing a review tier" → "choosing a review model".
- `README.md:34` "per tier and model" → "per model"; `:47` "at the `standard` or `high` tier" → "at one depth".
- `skills/mf-release/SKILL.md:280`: "the converge tier and each `inconclusive` section" → "each `inconclusive` section".

## Tests

Counted at `22c1af8`: `uv run pytest --collect-only -q | tail -1` prints `102 tests collected`. All unit or integration;
none end-to-end. None is added, deleted or merged.

| test | change | holds |
|---|---|---|
| `test_a_worker_carries_the_allowlist_and_a_denial_is_named` | edited | D2: the converge prompt has no tier clause; an old models file's `tier = "high"` changes nothing; `_tier`'s cases go |
| `test_a_grant_buys_one_round` | kept | D2: the prompt still ends `and grant=yes` |
| `test_each_era_parses_with_gaps` | edited | D3: no record carries a tier; `inconclusive` counts only with `## Refuted` |
| `test_the_page_draws_charts_and_lists_gaps` | edited | D3: the printed table opens `| model | engine | changes |` |

## Dependencies

None.

## Risks / Trade-offs

- **Past `tier: high` data merges into its model's row** on the metrics page. The person accepted the break.
- **A change once flagged for high** (auth, the gate, CI, the review machinery) gets the one depth; the calibration showed
  the same findings.

## Verdict

Ready to build.
