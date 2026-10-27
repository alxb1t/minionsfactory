# Metrics baseline — design

v0.30.0's data file is collected in a worktree of the `v0.30.0` tag, then copied into the branch. Verdict: ready
to build. Scope is [the proposal](proposal.md).

## Context

Premises were re-checked on `main` at `d7a18b8`, the v0.30.0 merge, before the cut.

| evidence at the cut | implication |
|---|---|
| `git ls-files metrics` prints only `metrics/catalogue.toml` | no data file exists yet |
| `git diff --quiet v0.30.0 main` exits 0; `git rev-parse --short 'v0.30.0^{commit}'` prints `f0aba0a` | the tag holds the shipped tree, analyzed as `f0aba0a` |
| `CHANGELOG.md` under `## [0.30.0]`: `Gate: local 0m5s` | v0.30.0's gate took 5 seconds locally |
| `0030-change-impact` design, Context: premises re-checked at `8c88e90` | v0.30's base is `8c88e90` |
| `.minions/backlog.md` exists; `.minions/` is gitignored | the worktree needs the backlog copied in, or `open-backlog-cards` is `unavailable` |
| `grep -c '^\[\[metric\]\]' metrics/catalogue.toml` prints `12` | the data file holds a value per metric |

## Goals / Non-Goals

**Goal:** a tracked `metrics/changes/0030-change-impact.json` that records what v0.30.0 shipped.

**Non-goals:** see [the exclusions](proposal.md#not-in-this-change).

## Decisions

### D1

| id | decision | because | rejected |
|---|---|---|---|
| D1 | Collect in a detached worktree of `v0.30.0` at `.minions/v0.30.0`, with the tag's own collector, and copy the file out | The values are the tag's; the cut and build commits stay out of `commits-without-trailer` and `amends`; `mf_version` reads `v0.30.0`; `.minions/` keeps it inside the repo and untracked | Collecting on this branch: `analyzed` would be the build's head and its commits would count · waiting for the next release: v0.30 would never get a point |

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | `gate-seconds` is `5`, from v0.30.0's `Gate:` line; `executor` and `model` are the building station's own report | The release's own timing is the record; provenance is never guessed | Re-timing the gate now: another run on another day |

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | Converge is skipped | The change adds one generated data file and no code | Running the check loop over a data file |

## Tests

No test is added, removed or merged.

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 36 | 0 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `36 tests collected` |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

## Dependencies

None.

## Risks / Trade-offs

- **`tests-collected` runs pytest in the worktree** → `uv` builds the worktree's `.venv` from its cache; the
  worktree is removed after.
- **The backlog is today's, not v0.30.0's** → `.minions/backlog.md` keeps no history; its count at the cut is
  the nearest record of v0.30.0's.

## Verdict

Ready to build. Acceptance: the tracked data file, its values as [D1](#d1) and [D2](#d2) say, and its page.
