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
| [D2](#d2) | `stage_of` reads its absence as stage `build`, and the build check fails on it | a run resumes by itself, and a build that exits without it halts rather than starting again | a halt for the person · a build check on the boxes and a clean tree alone: it re-spawns without end |
| [D3](#d3) | `mf-build` resumes at Step 3, restoring a dirty tree in the range only while its `.closing` mark names `HEAD`, saved to a patch first | simplify's edits are cleanups; a half-done angle's edit was never gated; the mark proves the dirt is the build's own | continuing the angle · restoring on the range alone: a person's uncommitted edit is lost |
| [D4](#d4) | A version whose converge has begun reads as before | no migration for versions built before this | a migration step |

### D1

After Step 3.5, `mf-build` writes `.minions/build/<change-id>.done`, the run directory's, two lines:

```
head: <the full sha of HEAD>
simplify: <the simplify commit's sha> | lean already | nothing kept
```

It writes it only once Step 3 and Step 3.5 are done; `metrics: none — no catalogue` counts as done. Step 4's report names it.
Then it removes `.minions/build/<change-id>.closing`, per [D3](#d3).

### D2

`stage_of`, after the unticked-phase check and before the converge checks: `_run_end(runs, change)` is `None` and
`_closed(runs, tree, change)` is false → `("build", "closing steps left")`. `_closed` reads the file's `head:` line and compares
it with the tree's `HEAD`, resolved; a missing or unreadable file is not closed.

`_check_build`, after the unticked-phase and clean-tree checks: `_closed` is false → `no .minions/build/<change>.done names
HEAD`, so a build that exits 0 without the file halts its version, as any failed check does (D47), and no second build starts.

### D3

Step 3 opens: "After the last phase, and only then, write `.minions/build/<change-id>.closing`, the run directory's, one line:
`head: <the full sha of HEAD>`. It marks what Step 3 leaves dirty as the build's own."

`mf-build`'s start table:

- the row "every `## Progress` box is ticked" → "every box ticked, and `.minions/build/<change-id>.done` names `HEAD` → the
  change is built: report that and stop; invent no scope".
- a new row: "every box ticked, and no `.done` names `HEAD` → the closing steps were interrupted: go to Step 3. A dirty tree
  holds a pass that never finished only while `.minions/build/<change-id>.closing` names `HEAD`: then, when every dirty path
  is one the change's commits touch (`git diff --name-only <base>..HEAD`, `<base>` as in Step 3.5), save them —
  `git add --intent-to-add` the untracked ones, then write `git diff --binary HEAD` to
  `.minions/build/<change-id>.discarded.patch` — restore them with `git restore --staged --worktree`, and say so, naming the
  patch. No such mark, or a path outside them → **halt**, naming the dirty paths, and restore nothing."

A dirty tree with no mark is not the build's: a person's edit, or a build closed before this rule. `git apply` of the patch
brings the restored paths back, untracked ones included.

### D4

`_run_end` is checked first in D2, so a version whose converge status log has a run is past its build whatever the marker
says. A version built before this change and not yet converging runs simplify again, which ends `lean already` when nothing
is left; on a dirty tree it has no `.closing`, so its build halts and restores nothing.

`skills/mf-ship/SKILL.md` Step 4 gains: "A build that died in its closing steps resumes at simplify on a re-run."

## Tests

Counted at `f33a6b3`: `uv run pytest --collect-only -q | tail -1` prints `101 tests collected`. Both below are integration
tests in `tests/test_conduct.py`, the added one through `tests/fake_worker.py`; none is end-to-end.

| test | change | holds |
|---|---|---|
| `test_a_build_dead_in_simplify_resumes_at_it` | added | D2: a fake build in mode `dies-simplify` ticks and commits every phase, writes no `.done` and exits 1; `stage_of` reads `build`, "closing steps left"; a re-run's build writes `.done` and the version converges. Its twin, in the same test: a `.done` naming an older head reads `build`; one naming `HEAD` reads converge; D4: a converge status log with no `.done` reads converge |
| `test_each_check_passes_only_on_disk_evidence` | extended | D2: on every box ticked and a clean tree, `check build` fails with no `.done` and with one naming an older head, and passes once one names `HEAD` |

`tests/fake_worker.py`'s `build` writes `.minions/build/<change>.done` after its commit, and gains mode `dies-simplify`. Tests
that tick a version's phases by hand and expect converge or release get a `.done` from a helper. None is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **A worker writes the marker**, like the status logs: a confused worker could write it early. The accepted class; converge
  still judges the head.
- **A version built before this, not yet converging,** simplifies once more, and halts for the person on a dirty tree.
- **A person's edit made after a build died in simplify**, while its `.closing` still names `HEAD`, reads as the build's and
  is restored with it. `.minions/build/<change-id>.discarded.patch` keeps it, and the report names the patch.
- **A worker writes the `.closing` mark**, as it writes the marker: the same accepted class.

## Verdict

Ready to build.
