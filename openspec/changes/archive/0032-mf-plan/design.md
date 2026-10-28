# mf-plan — design

A new station, `mf-plan`, grills a version to settled decisions and writes the brief the cut reads — reading the
target without moving it, on any executor. Verdict: ready to build. Scope is [the proposal](proposal.md); behaviour
is [the delta](specs/sdd/spec.md).

## Context

Premises were re-checked on `main` at `cb52d5b` (v0.30.1) before the cut.

| evidence at the cut | implication |
|---|---|
| D5 (`docs/decisions.md:59-66`): *grilled with the `grilling` skill … MinionsFactory adds only the conducting* | overturned for planning ([D6](#d6)) |
| The line diagrams label the first station `` `grilling` ``: `README.md:15`, `docs/README.md:9`; `mf-cut-change`'s diagram (`skills/mf-cut-change/SKILL.md:13`) starts at `grilling` | each names `mf-plan` ([D6](#d6)) |
| `mf-cut-change` Step 2 (`:48-54`) reads the source and halts when it settles no decision; it already takes `brief=` (`:27`) and never writes its path (Never) | the light-brief halt joins Step 2 ([D5](#d5)) |
| *The repo reaches nothing outside itself* (`docs/principles.md:126-131`) names the CI lookup and the collector's `git describe` — not the brief, and not the collector's `git ls-files --error-unmatch` (`skills/mf-build/scripts/metrics.py:243`) | one rewritten list of exceptions; closes `0030·R3` ([D6](#d6)) |
| `0030·R3`'s **Still true?** is `grep -n "save \`mf-release\`'s read-only remote CI lookup" docs/principles.md` | the rewrite leaves that phrase gone |
| `AGENTS.md:29` lists the skills as *bootstrap, cut, build, converge, release*; `README.md:23-29` has a row per skill | each gains `mf-plan` |
| `make install-skills` links every `skills/mf-*` | `mf-plan` installs with no recipe change |
| `uv run pytest --collect-only -q \| tail -1` prints `36 tests collected` | the count before ([Tests](#tests)) |

## Goals / Non-Goals

**Goal:** a version is planned the same way on every executor, from a brief on disk that any session can continue,
and no planning session moves a checkout another session is using.

**Non-goals:** see [the exclusions](proposal.md#not-in-this-change).

## Decisions

The grilling settled these choices; the build does not reopen them.

### D1

| id | decision | because | rejected |
|---|---|---|---|
| D1 | One skill, `skills/mf-plan/SKILL.md`, its parameters `<what>`, `brief=<path>` (required), `depth=light\|hard` (default `hard`), `from=<brief>`; the target is the cwd's repository | One output path, given by the operator; one skill for both depths | Wrapping the adopted skill — a plugin other hosts lack, text that moves |

Its sections, in order:

```
## Parameters                    the table above; no `brief=` → halt and ask; a `from=` that does not resolve → halt
## Step 1 — Preconditions        a git repository; root `AGENTS.md` and its mandatory context read; the default
                                 branch and its commit named: `<ref>` = that branch, `<sha>` = its short commit
## Step 2 — Read the target, read-only     D2
## Step 3 — The checks           D3, reported as facts before the first round
## Step 4 — The rounds           D4
## Step 5 — Write the brief      after every round, D5
## Step 6 — Close                frontier empty → the settled table, the person confirms, `## For the cut` filled;
                                 the close-out, then the last line
## The brief                     D5's template
## Never                         D2's forbidden commands, and: write the brief's path into the target · cut
```

The close-out follows every station's: at most three sentences, then `Next: /mf-cut-change <id> <version>
brief=<path>` — or, for a light brief, `Next: /mf-plan <what> depth=hard from=<path>`.

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | Read the target only at `<ref>`; helpers by default, held to the same rule | The 2026-10-26 collision; a long thread keeps facts, not file dumps | Reading the working tree, which may be a build's half-done state |

| allowed | never |
|---|---|
| `git show <ref>:<path>` · `git grep <pattern> <ref>` · `git log <ref>` · `git ls-tree <ref>` · `git diff <a> <b>` · `git rev-parse` · reading `.minions/backlog.md` from disk | `switch` · `checkout` · `stash` · `reset` · `commit` · `branch` · `merge` · `rebase` · editing a file in the target · `make gate` · a metric collection |

**Helpers.** Where the host can start fresh workers, fact-finding goes to read-only helpers by default, each given
`<ref>`, the question, and the allowed list; each returns conclusions with `path:line` at `<sha>`, not file contents.
Without helpers, the station looks facts up itself, by the same list.

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | Before the first round, report as facts: triggered cards, the paydown line, the release's version form, decisions touched, a split, re-measured facts, metrics past their watch | MF's practice, portable; the checks a cut otherwise finds late | Leaving them to the operator's memory |

| check | how |
|---|---|
| triggered cards | each card's **Trigger** in `.minions/backlog.md` against the version; matches proposed as `backlog: [<ids>]` |
| the paydown line | more than ten `- **<4 digits>·` lines → recommend a paydown version first |
| the release can ship it | the version's form against what `skills/mf-release/SKILL.md` at `<ref>` writes for a tag; a mismatch goes to the person |
| decisions touched | `docs/decisions.md` at `<ref>`, when present: each decision the version adds or overturns, named |
| a split | a version whose one diff would be too large for review is proposed as two |
| re-measure | with `from=`: a fact citing a commit other than `<sha>` is checked again at `<sha>` |
| metrics | with `metrics/catalogue.toml` at `<ref>`: the metrics past their `watch` in the tracked data file of the highest version, read with `git show`, no collection run |

### D4

| id | decision | because | rejected |
|---|---|---|---|
| D4 | Rounds over the frontier: a design tree; each round asks every question whose prerequisites are settled, `❓ Qn` with `➡️` a recommendation, numbered on from the brief's last; facts are the station's, decisions the person's; a premise conflict goes to the person with its evidence, and waits | The adopted skill's frontier, credited; MF's practice | One question at a time; asking what can be looked up |

```
facts (D3) ─▶ round: the frontier, each with a recommendation ─▶ the person answers ─▶ write the brief (D5)
                 ▲                                                                      │
                 └──────────────── the frontier recomputed ◀───────────────────────────┘
                                         empty ─▶ the settled table ─▶ confirmed ─▶ close
```

**Depth.** `light` stops once the direction is settled — no phases — and its title says `light`. `hard` walks the
frontier to empty: phases, and Acceptance as commands in `## Decisions` and `## For the cut`.

### D5

| id | decision | because | rejected |
|---|---|---|---|
| D5 | The brief is written after every round, in fixed sections; the cut halts on a light one | A thread can end anywhere and a new one continue with `from=`; the cut relies on fixed places | A brief written only at the end; a free-form brief |

```markdown
# <version name> · a minor | a patch · light | hard · <YYYY-MM-DD>

**<what the version does, in one line>**

## Facts
- <a fact> (`path:line` at `<sha>`)

## Decisions
| # | decision | the reason that settled it |
|---|---|---|

## Phases
<a small diagram, one line a phase — hard only>

## Not in this
- <what is out>

## Open
- <a question still on the frontier — removed when it is empty>

## For the cut
<the change id and version proposed · `backlog: [ids]` · the conditions — filled when the frontier is empty>
```

The cut's Step 2 gains: *A `brief` whose title declares `light` → **halt**: it is not hard-grilled; name
`/mf-plan <what> depth=hard from=<brief>`.*

### D6

| id | decision | because | rejected |
|---|---|---|---|
| D6 | Record it where it lives: D5 overturned for planning; the boundary principle's exceptions rewritten; the diagrams and lists name `mf-plan` | `A7`; `W6`; `0030·R3` | A design-only record |

**D5**, after:

```markdown
### D5 · A change is planned with `mf-plan` and written with the OpenSpec CLI

**`mf-plan` grills a version to settled decisions and writes the brief; the OpenSpec CLI's `instructions` shape
each artifact, and its `validate --strict` is the check on a change. `mf-plan` takes its frontier rounds from the
adopted `grilling` skill it replaces.**

- **Why:** the line's practice must run on every executor, and a plugin one host carries cannot; the OpenSpec CLI
  is maintained elsewhere and stays adopted.
- **Rejected:** wrapping `grilling` — a plugin other hosts lack, text that moves upstream · `to-spec`, which
  collides with `openspec instructions` · `to-tickets`, which is redundant · a `docs/agents/` adapter, which has no
  reader.
```

**The boundary principle**'s bold paragraph, the exceptions as a list:

```markdown
**Project inputs and outputs stay inside the target repository, save:**

- **the operator's brief**, read and written at the path the operator gives, never named in the repo;
- `mf-release`'s read-only remote CI lookup for its `Gate:` line;
- the bundled metrics script's read-only git reads of its own package — `git ls-files` and `git describe`
  ([D43](decisions.md#d43--project-health-is-measured-per-change-from-the-repos-own-catalogue)).

**Installed skills, bundled references and bundled scripts are instruction-package material, not permission to
read arbitrary outside files. Run output goes to the gitignored `.minions/`; the repo names no path, token or tool
of the place its plan is kept.**
```

**The diagrams**: `README.md` and `docs/README.md` put `mf-plan` under *grill*; `mf-cut-change`'s starts
`mf-plan ──▶ mf-cut-change`. **The lists**: `AGENTS.md`'s skills line reads *plan, bootstrap, cut, build, converge,
release*; `README.md`'s skill table gains a `mf-plan` row first.

### D7

| id | decision | because | rejected |
|---|---|---|---|
| D7 | Structural tests only: `mf-plan` holds `## Parameters`, whose table names `brief`, and `## Never`; a twin shows the check fails on a skill missing either | D42: structure, not phrases | A phrase scan of the read-only list |

The proof of the station is the next version's grilling, run with `mf-plan` once the links are reinstalled.

## Tests

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 36 | 2 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `36 tests collected` at the cut, `38 tests collected` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

| test, added | file | holds |
|---|---|---|
| `test_mf_plan_holds_its_parameters_and_never` | `tests/test_skills.py` | the `## Parameters` table names `brief`; a `## Never` section exists |
| `test_the_plan_scan_reports_a_missing_section` | the same | its twin (`W5`, `T6`) |

Planned addition count: ``grep -cE '^\| `test_[a-z0-9_]+` \| `?(tests/|the same)' openspec/changes/0032-mf-plan/design.md`` prints `2`.

## Dependencies

None.

## Risks / Trade-offs

- **A host without helpers grills inline** → the thread grows; the brief on disk lets a new session continue.
- **The read-only rule is instruction, not enforcement** → the forbidden list is explicit, and a build that finds
  its checkout moved already halts and asks.
- **The skills are live-linked while this builds** → the build edits `mf-cut-change`; other projects see that edit
  through the links until release, unless the operator freezes them as for v0.30.

## Migration Plan

```
1 the station ─▶ 2 the cut's halt ─▶ 3 the records ─▶ simplify ─▶ converge ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible.

## Verdict

Ready to build. Acceptance: `mf-plan` with its parameters, checks, rounds, brief and `## Never`; the cut halting on
a light brief; D5 and the principle rewritten; the structural tests green.
