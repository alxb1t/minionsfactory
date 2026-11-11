---
bump: minor
debt: [0113·S4]
---

# Cut diet

The cut reads its context once, waits on its reviews in the foreground on the 5-minute cache, and a script writes what the brief already says.

Reading map: [design](design.md) holds the decisions and the check tables, [tasks](tasks.md) its phases.

## Why

The cut is the largest station of the line. It gathers by many reads — the instructions of each artifact, archived changes read as examples, the decisions, the living spec, the brief again and again — so its context is large before the proposal is written, and every later turn re-reads it, then it writes again what the brief already says. Its reviews, run in the background, woke it and re-read the whole context at each wake, and the 1-hour cache it paid for was set for reviews that no longer take that long.

## What Changes

- `cut_context.py <brief> <change-id>` writes one **context pack** the cut reads once: the brief, each fact with its lines at `HEAD`, the cited decisions, the requirements the brief names, the debt on the cited files and a skeleton of each artifact.
- `cut_context.py <brief> <change-id> --scaffold` writes the parts of the artifacts the brief already says: the proposal's frontmatter, title, one line and `## Not in this change`; the design's `## Decisions` table and `## Dependencies`; `tasks.md`'s `## Progress` and phase headings.
- `brief_check.py` gains `--sections`, which prints the brief's sections as JSON, so the cut's script reads the brief without a Markdown dependency.
- Step 8.5 runs each plan review in the foreground and waits for it.
- The cut starts on the 5-minute cache, as every station does; `CACHE_HOUR` goes.
- Row `V2` of `cut_check.py` evaluates a `-k` expression against each changed test name (debt `0113·S4`).
- Requirement *A Claude worker starts with its station's tools and nothing of the operator's*: MODIFIED — every station on the 5-minute cache.
- Requirement *A cut reads one context pack*: ADDED.
- Requirement *A cut starts from a scaffold of what the brief says*: ADDED.
- Requirement *A plan review runs in the foreground*: ADDED.
- Requirement *Row V2 evaluates a `-k` expression*: ADDED.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the cache requirement above, and the requirements ADDED above.

## Impact

- `skills/mf-cut-change/scripts/cut_context.py` is new; `tests/test_cut_context.py` holds its tests.
- `skills/mf-plan/scripts/brief_check.py` gains `--sections`; `tests/test_brief_check.py` holds its test.
- `skills/mf-cut-change/scripts/cut_check.py` evaluates a `-k` expression; `tests/test_cut_check.py` holds its tests.
- `skills/mf-ship/scripts/conduct.py` drops `CACHE_HOUR`; `tests/test_conduct.py` expects the cut on the 5-minute cache.
- `skills/mf-cut-change/SKILL.md` changes Steps 2, 6 and 8.5 and its reading step; `tests/test_skills.py` requires it to name `cut_context.py`.
- `docs/decisions.md` amends D77, D80 and D70.
- No dependency.

## Not in this change

- The cut's model in code: the Sonnet · medium trial is a line in a brief's models, with no code.
- The plan-metrics defects — a `$B` brief and cross-repo operator marks: a later debt paydown.
