# Parallel workspaces — design

A primary checkout on the default branch, a linked worktree per version beside it, one run directory for all of
them, and the release merging in the primary. Verdict: ready to build. Scope is [the proposal](proposal.md);
behaviour is [the delta](specs/sdd/spec.md).

## Context

Premises were re-checked on `main` at `aa85c14` (v0.31.3) before the cut.

| evidence at the cut | implication |
|---|---|
| The cut checks an id only against `openspec/changes/` and `archive/` here and a version only against a branch name (`skills/mf-cut-change/SKILL.md:47-49`), and switches in place (`:70`) | [D1](#d1), [D2](#d2) |
| `.minions/` is a cwd path in `skills/mf-build/scripts/metrics.py:579`, `skills/mf-converge/scripts/gate_check.py:24` and `scripts/metrics/backlog.py:14`, and in every station's text (`skills/mf-converge/SKILL.md:41,56,174,189-195,227,330,373`; `skills/mf-release/SKILL.md:64-68,75,78,90,194`; `skills/mf-build/SKILL.md:193-196`; `skills/mf-cut-change/SKILL.md:86-87`; `skills/mf-plan/SKILL.md:65-73`) | [D3](#d3) |
| Converge Step 9 (`skills/mf-converge/SKILL.md:371`) and release Step 4.6 (`skills/mf-release/SKILL.md:192`) write `.minions/backlog.md` | the lock ([D3](#d3)) |
| Release Step 5 (`skills/mf-release/SKILL.md:198-217`) runs `git switch <default-branch>`; git refuses a branch held by another worktree | [D4](#d4) |
| `mf-plan`'s checks table ends at its `metrics` row (`skills/mf-plan/SKILL.md:71`) | [D5](#d5) |
| D16 (`docs/decisions.md:183`), D18 (`:237`), D20 (`:277`); the overview's repo conventions end at D42 (`:15`) | [D6](#d6) |
| No `v*` branch is open; no tag `v0.32*`; `uv run pytest --collect-only -q \| tail -1` prints `50 tests collected` | the id and version are free; [Tests](#tests) |

## Goals / Non-Goals

**Goal:** two versions built side by side in their own worktrees, neither reading the other's state as its own,
each released from the primary in cut order.

**Non-goals:** see [the exclusions](proposal.md#not-in-this-change).

## Decisions

The grilling settled these choices (the brief's Q9–Q18); the build does not reopen them.

### D1

| id | decision | because | rejected |
|---|---|---|---|
| D1 | The cut makes the version's worktree when `AGENTS.md` declares `Worktrees:`; it runs a declared `Workspace setup:` there | The primary stays on the default branch, where cuts and merges happen; single-checkout repos keep the switch | Host flags, which put worktrees where MF cannot name them |

The keys, in a `## Workspaces` section of `AGENTS.md`:

```markdown
## Workspaces

- **Worktrees:** `../` — a version's worktree is `<this path>/<branch>`, relative to the primary checkout.
- **Workspace setup:** none — the gate's first step is `uv sync --locked`.
```

The cut's Step 4, after: *`Worktrees:` declared → `git worktree add -b v<version>_<slug> <path>/v<version>_<slug>
<default-branch>`; `Workspace setup:` names a command → run it in the new worktree, halting on a failure, naming
it; every path in Steps 5–10 is in the new worktree, and the commit is made there (`git -C <worktree>`). No
`Worktrees:` → `git switch -c v<version>_<slug>`, as before.* Its report names the worktree and ends
`Next: cd <worktree> && /mf-build <change-id>, in a fresh session.`

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | Ids and versions are reserved against every open version branch; versions ship in cut order | The branches are the reservation; ids stay in ship order | A lock file; ids in release order |

The cut's preconditions, after:

```markdown
- `change-id` is free: its number is higher than every id under `openspec/changes/` and `openspec/changes/archive/`
  on the default branch and on every unmerged version branch — each `git branch --no-merged <default-branch> --list
  'v*'` names, read with `git ls-tree -r --name-only <branch> -- openspec/changes/`;
- the version is free: no branch `v<version>_*` (`git branch --list`) and no tag `<tag>` (`git tag -l`).
```

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | One run directory: `.minions/` beside the primary's git directory, from any worktree; the backlog written under a `mkdir` lock | Findings, logs, drafts and exports are keyed by change id; one backlog; a release elsewhere no longer reads converge as skipped | A `.minions/` per worktree |

Each station defines it once, as it defines the default branch:

```markdown
The **run directory** is `.minions/` beside the primary checkout: `$(git rev-parse --path-format=absolute
--git-common-dir)/../.minions`, the same from every worktree. Every `.minions/` path below is in it.
```

Each script gains the same resolution in Python — `git rev-parse --path-format=absolute --git-common-dir`, its
parent, `/ ".minions"` — for `metrics.py`'s default page path, `gate_check.py`'s `EXPORTS` and `backlog.py`'s
`BACKLOG`.

**The lock**, in converge Step 9 and release Step 4.6: *before writing `.minions/backlog.md`, `mkdir
.minions/backlog.lock`; it exists → wait 5 seconds and retry, for 2 minutes, then halt, naming the lock; `rmdir` it
when the write ends, written or halted.*

### D4

| id | decision | because | rejected |
|---|---|---|---|
| D4 | The release merges in the worktree holding the default branch, then removes the version's worktree | `git switch` fails in a linked worktree; the evidence lives in the shared run directory | Merging in the version's worktree; a ref-only update |

Release Step 5, after: the **primary** is the worktree `git worktree list --porcelain` shows on `branch
refs/heads/<default-branch>`, or this checkout when none does. Its tree must be clean (`git -C <primary> status
--porcelain` prints nothing), else halt. Then `git -C <primary> merge --no-ff <branch>`, `git -C <primary> diff
--quiet <branch> <default-branch>`, and the pushes from the primary. After the merge, when this checkout is a linked
worktree: `git -C <primary> worktree remove <this worktree>` — a refusal is reported, never forced — and the last
line names `cd <primary>`. Step 6's no-merge commands use `git -C <primary>`.

### D5

| id | decision | because | rejected |
|---|---|---|---|
| D5 | `mf-plan`'s checks gain *parallel with* | Semantic conflicts are prevented at planning | Finding them at integration |

```markdown
| parallel with | when the person names versions to run side by side: their briefs' `## Facts` paths and `## Phases` files compared; a pair touching a file in common is proposed in an order, naming the file |
```

### D6

| id | decision | because | rejected |
|---|---|---|---|
| D6 | The records: D44 added; D20, D16 and D18 amended; `AGENTS.md` declares MF's workspaces; README gets the move's runbook | `A7`; `W6` | — |

D44, in *Repo conventions* after D42, the overview's `D41, D42` becoming `D41, D42, D44`:

```markdown
### D44 · Versions run side by side in worktrees; one primary merges them

**A repo that declares `Worktrees:` in `AGENTS.md` gets a linked worktree per version, made by the cut from the
primary checkout, which stays on the default branch. Ids and versions are reserved at the cut against every open
version branch, and versions ship in cut order. Every worktree shares the primary's `.minions/`; the release merges
in the primary.**

- **Why:** two writers in one checkout collide; git holds a branch in one worktree only; open branches reserve ids
  without a lock file.
- **Rejected:** host-managed worktrees — places MF cannot name · rebasing a judged branch · a reservation file.
```

D20's bold rule, after: *The number is higher than every id on the default branch and on every open version
branch; the cut takes the id it is given; versions ship in cut order; a version is numbered at its cut, so planned
work carries a name, not a number.* D16 gains: *one file per repository, in the primary's `.minions/`, shared by
every worktree and written under `.minions/backlog.lock`.* D18 gains, under its tree: *`.minions/` is the primary
checkout's; `AGENTS.md` may declare `Worktrees:` and `Workspace setup:` (D44).*

README, a section *Parallel workspaces*: the container layout, and the move — move the checkout to
`<container>/main`, `make install-skills` from it, update the planning side's path to the repo — done before the
next cut, since MF's `Worktrees: ../` names the container's folder.

## Tests

The gate stays offline: each new test makes a `tmp_path` repository with a linked worktree (`git worktree add`).

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 50 | 3 | 0 | `uv run pytest --collect-only -q \| tail -1` prints `50 tests collected` at the cut, `53 tests collected` after |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |

| test, added | file | holds |
|---|---|---|
| `test_the_page_defaults_to_the_primary_run_directory` | `tests/test_metrics.py` | from a linked worktree, `page` writes under the primary's `.minions/metrics/` |
| `test_exports_go_under_the_primary_run_directory` | `tests/test_gate_check.py` | from a linked worktree, the exports are made and removed under the primary's `.minions/gate-check/` |
| `test_the_backlog_is_read_from_the_primary_run_directory` | `tests/test_metric_scripts.py` | from a linked worktree, `backlog.py` counts the primary's cards |

Planned addition count: ``grep -cE '^\| `test_[a-z0-9_]+` \| `tests/' openspec/changes/0036-parallel-workspaces/design.md`` prints `3`.

## Dependencies

None.

## Risks / Trade-offs

- **MF's `Worktrees: ../` before the move** names `Developer/` → the runbook says move before the next cut.
- **A lock left by a dead converge** halts the next writer after two minutes → it names the lock; removing it is
  the person's.
- **Two cuts at the same moment** can both see the same free id → cuts run in the primary, one at a time.
- **The stations' worktree rules are held by review** (D42); the scripts' resolution is tested.

## Migration Plan

```
1 one run directory: the scripts ─▶ 2 the cut: worktree, reservation, setup ─▶ 3 converge · release · build · plan
  ─▶ 4 the records ─▶ simplify ─▶ converge ─▶ release ─▶ the person moves MF into the container
```

Each phase ends on a green gate. Nothing is irreversible.

## Verdict

Ready to build. Acceptance: the scripts' tests, the stations' new rules, the records, and the runbook; the real
proof is two versions side by side after the move (v0.33's brief).
