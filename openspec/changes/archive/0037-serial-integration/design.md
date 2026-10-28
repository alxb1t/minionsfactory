# Serial integration — design

One station merges the default branch into the next version, by fixed rules for what is exact and a hand-over for
what is not, and converge judges the merge by what it decided. Verdict: ready to build. Scope is
[the proposal](proposal.md); behaviour is [the delta](specs/sdd/spec.md).

## Context

Premises were re-checked on `main` at `6e5dcc5` (v0.32.0) before the cut.

| evidence at the cut | implication |
|---|---|
| Release precondition 9 halts on a moved base and names a hand merge (`skills/mf-release/SKILL.md:109-114`); precondition 10 halts while a lower-id `v*` branch is open (`:116-119`) | the queue order is already enforced; precondition 9 names the station ([D1](#d1)) |
| Converge's catch-up round freezes `<judged head>..HEAD` (`skills/mf-converge/SKILL.md:146-147`) | it would re-read `main`'s changes ([D3](#d3)) |
| `git show --remerge-diff <merge>` prints only a merge's own resolution (git 2.54, scratch experiment) | [D3](#d3) |
| Build appends under `## [Unreleased]`; release renames it and copies the previous `Gate:` line (`skills/mf-build/SKILL.md:151-152`; `skills/mf-release/SKILL.md:152-166`); a plain merge conflicts; `merge=union` drops the blank line | [D2](#d2) |
| `docs/decisions.md:8`: *an id is never reused or renumbered*; the highest id is D44 (`:368`); the group map is at `:10-16` | [D2](#d2), [D5](#d5) |
| The fold replaces a MODIFIED requirement by title (`skills/mf-release/SKILL.md:128`) | the delta check ([D2](#d2)) |
| `_METRICS_SCRIPTS` pairs a station with its script (`tests/test_skills.py:405-409`) | [Tests](#tests) |
| No open `v*` branch; `uv run pytest --collect-only -q \| tail -1` prints `53 tests collected` | [Tests](#tests) |

## Goals / Non-Goals

**Goal:** a finished version reaches the default branch on the latest base, in cut order, with nothing the merge
decided left unread.

**Non-goals:** see [the exclusions](proposal.md#not-in-this-change).

## Decisions

The grilling settled these choices (the brief's Q2–Q12); the build does not reopen them.

### D1

| id | decision | because | rejected |
|---|---|---|---|
| D1 | `mf-integrate`, run in the primary, one version per run; precondition 9 names it | One owner of the merge-in; the release stays its own station (D17) | Merging inside the release |

```
next version (lowest open id) ─▶ ready? ─ no ─▶ halt, naming it
       │ yes
git -C <worktree> merge <default-branch> ─▶ the rules (D2) ─▶ a semantic conflict? ─ yes ─▶ halt, merge open (D4)
       │ no
make gate in the worktree ─▶ commit the merge, `Change: <id>` ─▶ Next: /mf-converge, then /mf-release
```

**Ready** is every `## Progress` box ticked and clean findings files, or converge skipped by the findings' absence.
The skill's sections: *Parameters* (none; the cwd is the primary), *Step 1 — Preconditions*, *Step 2 — Pick the
version*, *Step 3 — Merge and apply the rules*, *Step 4 — Gate and commit*, *Step 5 — Report*, *Never*.

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | `integrate.py` holds the exact rules: the queue, the CHANGELOG order, decision renumbering, the delta check | Exact rules drift in prose | `merge=union`; judgement for the CHANGELOG |

`uv run --script <this package>/scripts/integrate.py <command> …`, standard library, PEP 723 header `>=3.12`:

| command | does |
|---|---|
| `next` | prints the lowest-id unmerged `v*` branch, its worktree and whether it is ready; exit 1 when none is ready |
| `changelog <worktree>` | after a merge, keeps the branch's `## [Unreleased]` entries above the default branch's released sections, blank lines intact |
| `decisions <worktree>` | renumbers the branch's new decision to the next id free on the default branch, its citations with it, and the group map |
| `delta <worktree>` | prints each MODIFIED or REMOVED title of the branch's delta that the default branch changed since the merge-base; exit 1 when any |

`docs/decisions.md:8` becomes *An id in force is never reused or renumbered. A new decision takes the next number,
in the group it belongs to.* No `.gitattributes` `merge=union`.

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | Converge's catch-up judges a merge of the default branch by its `git show --remerge-diff`, plus the range's other commits | A clean merge adds nothing to read; the gate checks the combined tree | Re-reading `main`'s changes |

Catch-up step 3, after: *freeze `<judged head>..HEAD`; when the range holds a merge of the default branch, its patch is
that merge's `git show --remerge-diff` plus the diff of the range's other commits.*

### D4

| id | decision | because | rejected |
|---|---|---|---|
| D4 | A semantic conflict halts with the merge in progress and `.minions/integrate/<change-id>.md` | State on disk; the next run continues from `MERGE_HEAD` | Resolving silently against either design |

The note holds each design's decisions on the conflicting file or requirement, and a proposed resolution. The person
resolves or accepts it; `/mf-integrate` again sees `MERGE_HEAD`, runs the rules and the gate, and commits.

### D5

| id | decision | because | rejected |
|---|---|---|---|
| D5 | D45 records integration; `decisions.md:8`, release precondition 9 and `AGENTS.md` follow; README's runbook gains the move's steps | `A7`; `W6` | — |

```markdown
### D45 · One station merges the default branch into the next version

**`mf-integrate`, run in the primary, merges the default branch into the lowest-id open version's worktree,
applies fixed rules to the CHANGELOG, decision ids and spec delta, hands a semantic conflict to the person with the
merge open, gates, and commits the merge; converge's catch-up judges the merge by its remerge-diff.**

- **Why:** the merge-in a moved base needs conflicts on the same files every time; a clean merge adds nothing to
  read, and what the merge decided is exactly what review must see.
- **Rejected:** `merge=union` — it drops a blank line and hides the result from the remerge-diff · rebasing a judged
  branch · resolving silently against either design.
```

The overview's repo conventions end `…D44, D45`. README's runbook gains: the move through a temporary name, `rm -rf
.venv && uv sync --locked`, and `make install-skills SKILLS_DIR=$HOME/.claude/skills`.

## Tests

The gate stays offline: each test builds a `tmp_path` repository with a linked worktree and real merges.

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 53 | 5 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `53 tests collected` at the cut, `58 tests collected` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

| test, added | file | holds |
|---|---|---|
| `test_next_picks_the_lowest_open_id_and_halts_on_an_unready_one` | `tests/test_integrate.py` | the queue, readiness, never skipping ahead |
| `test_changelog_keeps_the_branch_entries_above_the_released_sections` | the same | a real conflicting merge, resolved; blank lines intact |
| `test_decisions_renumbers_a_colliding_decision_and_its_citations` | the same | D45 against D45, the group map |
| `test_delta_reports_a_requirement_main_changed` | the same | exit 1 and the title |
| `test_mf_integrate_runs_its_script` | `tests/test_skills.py` | a `_METRICS_SCRIPTS` pair: `mf-integrate` names `scripts/integrate.py`, which exists |

Planned addition count: ``grep -cE '^\| `test_[a-z0-9_]+` \| `tests/|^\| `test_[a-z0-9_]+` \| the same' openspec/changes/0037-serial-integration/design.md`` prints `5`.

## Dependencies

None.

## Risks / Trade-offs

- **A resolution that is wrong** → the catch-up reads it through the remerge-diff, and the gate runs on the combined
  tree.
- **A conflict the rules do not name** halts as semantic → by design.
- **The first use is the pilot** → the two versions after this one prove it.

## Migration Plan

```
1 integrate.py + its tests ─▶ 2 the station · converge's catch-up · release's precondition 9 ─▶ 3 the records
  ─▶ simplify ─▶ converge ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible.

## Verdict

Ready to build. Acceptance: the script's tests, the station and the two corrected stations, the records.
