# Build resume — design

How a run tells a finished build from one that died in its closing steps, and how the build resumes there. Verdict at the
end: ready to build.

## Context

Read at `f33a6b3` (v0.47.0).

- `mf-build` closes with simplify, Step 3 (`skills/mf-build/SKILL.md:175`), then the metrics, Step 3.5 (`:191`). Simplify makes
  one commit at its end, or reports `lean already` or `nothing kept`, which leave none.
- `mf-build`'s start table: a dirty tree with `tasks.md` tracked continues an interrupted phase (`:104`); every box ticked
  reports the change built and stops (`:106`).
- `stage_of` returns `build` only for an unticked phase (`skills/mf-ship/scripts/conduct.py:669`, `_unticked` `:459`); every
  phase ticked goes on to converge, whose first precondition is a clean tree (`skills/mf-converge/SKILL.md:208`).
- isekai, run `20261102-211122`: `0091`'s build died on a usage limit mid-simplify, every phase committed, an edit to
  `ui/src/views/Hub.vue` uncommitted; simplify's pass never finished.

## Goals / Non-Goals

**Goals:** a build that dies after its last phase resumes at simplify, under a run and by hand; disk tells done from not done.

**Non-Goals:** resuming inside a simplify angle; a second writer of the marker.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `.minions/build/<change-id>.done`, written by `mf-build` alone after Step 3.5 | the one way to tell `lean already` from "never ran" | the simplify commit as the marker: `lean already` makes none |
| [D2](#d2) | `stage_of` reads its absence as stage `build` | a run resumes by itself | a halt for the person |
| [D3](#d3) | `mf-build` resumes at Step 3, restoring a dirty tree in the range | simplify's edits are cleanups; a half-done angle's edit was never gated | continuing the angle |
| [D4](#d4) | A version whose converge has begun reads as before | no migration for versions built before this | a migration step |

### D1

After Step 3.5, `mf-build` writes `.minions/build/<change-id>.done`, the run directory's, two lines:

```
head: <the full sha of HEAD>
simplify: <the simplify commit's sha> | lean already | nothing kept
```

It writes it only once Step 3 and Step 3.5 are done; `metrics: none — no catalogue` counts as done. Step 4's report names it.

### D2

`stage_of`, after the unticked-phase check and before the converge checks: `_run_end(runs, change)` is `None` and
`_closed(runs, tree, change)` is false → `("build", "closing steps left")`. `_closed` reads the file's `head:` line and compares
it with the tree's `HEAD`, resolved; a missing or unreadable file is not closed.

### D3

`mf-build`'s start table:

- the row "every `## Progress` box is ticked" → "every box ticked, and `.minions/build/<change-id>.done` names `HEAD` → the
  change is built: report that and stop; invent no scope".
- a new row: "every box ticked, and no `.done` names `HEAD` → the closing steps were interrupted: go to Step 3. A dirty tree
  then holds a pass that never finished: when every dirty path is one the change's commits touch
  (`git diff --name-only <base>..HEAD`), restore them with `git restore --staged --worktree` and remove the untracked ones,
  and say so; a path outside them → **halt**, naming it."

### D4

`_run_end` is checked first in D2, so a version whose converge status log has a run is past its build whatever the marker
says. A version built before this change and not yet converging runs simplify again, which ends `lean already` when nothing
is left.

`skills/mf-ship/SKILL.md` Step 4 gains: "A build that died in its closing steps resumes at simplify on a re-run."

## Tests

Counted at `f33a6b3`: `uv run pytest --collect-only -q | tail -1` prints `101 tests collected`. Both below are integration
tests in `tests/test_conduct.py`, through `tests/fake_worker.py`; none is end-to-end.

| test | change | holds |
|---|---|---|
| `test_a_build_dead_in_simplify_resumes_at_it` | added | D2: a fake build in mode `dies-simplify` ticks and commits every phase, writes no `.done` and exits 1; `stage_of` reads `build`, "closing steps left"; a re-run's build writes `.done` and the version converges. Its twin, in the same test: a `.done` naming an older head reads `build`; one naming `HEAD` reads converge; D4: a converge status log with no `.done` reads converge |

`tests/fake_worker.py`'s `build` writes `.minions/build/<change>.done` after its commit, and gains mode `dies-simplify`. Tests
that tick a version's phases by hand and expect converge or release get a `.done` from a helper. None is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **A worker writes the marker**, like the status logs: a confused worker could write it early. The accepted class; converge
  still judges the head.
- **A version built before this, not yet converging,** simplifies once more.

## Verdict

Ready to build.
