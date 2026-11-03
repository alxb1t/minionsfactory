# Run fixes — design

Four corrections to what the run does around its stations, each from isekai's first real `/mf-ship`. Verdict at the end:
ready to build.

## Context

Read at `f33a6b3` (v0.47.0). `conduct.py` is `skills/mf-ship/scripts/conduct.py`.

- **F1.** In a Codex worker on this Mac `uname -m` prints `x86_64` and `/usr/bin/arch` `i386`, while every process outside
  Codex is `arm64`; `/usr/bin/arch -arm64 /usr/bin/uname -m` prints `arm64` inside. The probe's gate (`probe_gate`, `:1244`)
  checks a refused write alone, so it passed.
- **F2.** `0090` and `0091` were cut from `ab956e1`; `main` then moved to `7064ae6`, changing `Makefile` and `AGENTS.md`. The
  run built both on the old gate. A dependent already gets the default branch merged in with no agent: `ready` → `merge_in`
  (`:2011-2050`), behind `integrate.py`'s delta check.
- **F3.** `mf-release` Step 4.1 writes `CI none` when `gh` fails (`skills/mf-release/SKILL.md:182`); under the sandbox it always
  fails, `~/.config/gh` being in `SECRETS`. The `Gate:` line is in the tagged release commit.
- **F4.** `mf-release` Step 5.6 runs `git -C <primary> worktree remove <tree>` (`:266`), and the sandbox refuses it,
  "Operation not permitted". A version's tree comes from git's worktree list (`_worktrees`, `:382`), which a worker can write.

## Goals / Non-Goals

**Goals:** a run halts at its probe on a translated shell; a cut-only version builds on today's `main`; a released worktree is
removed; the `Gate:` line says why CI is missing.

**Non-Goals:** CI times under `mf-ship`; changing a started build's base without the person.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The probe's gate checks `uname -m` against the host's native architecture | the conductor's Python can itself run translated | comparing with `platform.machine()` |
| [D2](#d2) | A cut-only version behind `main` gets `main` merged in at the start; a started one behind a gate change halts | `merge_in` exists; the first case alone would have saved `0090` and `0091` | merging into a started build |
| [D3](#d3) | `conduct.py` removes a released worktree, at the cut's path | the release cannot; a worktree entry is worker-writable | trusting the entry |
| [D4](#d4) | Under `merge=yes`, `CI not read under mf-ship` | the line is in the tagged commit; `gh` from the conductor adds an endpoint D51 keeps out | the conductor calling `gh` |

### D1

`_native()` returns `arm64` when `sysctl -n hw.optional.arm64` prints `1`, else `os.uname().machine`. `probe_gate(mark,
native)` adds first recipe lines `uname -m > .arch` and `test "$$(cat .arch)" = <native>`, so a translated shell fails the gate
before `touch .gated`. `check_probe`, finding no `.gated` and an `.arch` that is not `<native>`, fails with
`"<executor>'s shell runs as <arch> on a <native> host"`, so the run halts at the probe as on any failed probe. `.arch` joins
the scratch `.gitignore`.

### D2

`Run.take`, before `ready`'s dependency wait:

- the branch holds only its cut commit (`git rev-list --count <base>..<change>` is `1`) and the default branch is not an
  ancestor → `merge_in(tree, change, default)`, as for a dependent;
- the branch holds more, `_unticked(tree, change)` names a phase, no merge is open in the tree, and `git diff --name-only
  <base> <default> -- Makefile '*.mk' AGENTS.md CODING_STANDARDS.md CONTRIBUTING.md` prints a path → `Stop(1, "conduct:
  halt — <default> changed <paths> since <change>'s base: git -C <tree> merge <default>, then re-run")`;
- else nothing: a built version, or one with a merge open, goes on from its stage, and integrate merges the default
  branch in under D45's rules.

`<base>` is `git merge-base <default> <change>`. Only at a version's first `take` in a run.

### D3

`Run.advance`, after a release's `check` passes: `tree = version.tree`; when `tree.resolve()` equals the `Worktrees:` path
joined with the change id, resolved, list its ignored paths with `git ls-files --others --ignored --exclude-standard
--directory` in the tree, then `_git(primary, *NO_HOOKS, "worktree", "remove", str(tree))` and log
`self.log.event(change, "removed", "<tree>: ignored <paths>")`; else, on a failed listing, or on a refusal, log
`self.log.event(change, "kept", "<tree>: <why>")`. The branch stays. `EVENTS` gains `kept` and `removed`.

`skills/mf-release/SKILL.md` Step 5.6 opens "Under `merge=yes`, skip this: `conduct.py` removes it." and Step 6's close-out
says so.

### D4

`skills/mf-release/SKILL.md` Step 4.1: "`gh` failing, no `origin`, or no run → `CI none`" → "`gh` failing, no `origin`, or no
run → `CI none`; under `merge=yes`, `CI not read under mf-ship`".

`skills/mf-ship/SKILL.md` Step 4 gains: "A version still building, halted because `main` changed its gate since its
base, needs `git -C <tree> merge <default>` before a re-run; a built one goes on to integrate."

## Tests

Counted at `f33a6b3`: `uv run pytest --collect-only -q | tail -1` prints `101 tests collected`. All integration tests in
`tests/test_conduct.py`, through `tests/fake_worker.py`; none is end-to-end.

| test | change | holds |
|---|---|---|
| `test_a_probe_halts_on_a_write_out` | edited | D1: a fake probe whose `uname -m` differs from the native halts the run, naming the executor; the default passes |
| `test_after_waits_for_its_dependency` | edited | D2: a cut-only version behind `main` gets `main` merged in with no halt; a started version behind a `main` that changed `Makefile` halts naming it; one behind a `main` that changed neither builds; a built one, or one with a merge open, behind a `Makefile` change reaches integrate |
| `test_a_ready_version_ships_past_a_slow_one` | edited | D3: after each release, its worktree is gone and its branch kept; a worktree entry pointing elsewhere is kept and logged; a tree whose ignored paths cannot be listed is kept and logged, and a removed one logs its ignored paths |
| `test_no_worker_pushes` | edited | D3: the release's log ends with the tree's `removed` line |

`tests/fake_worker.py`'s probe gains a mode whose `uname -m` reports another architecture, through a `uname` on its `PATH`.
None is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **A merge at the start can stop on the delta check**, as a dependent's does, leaving an `integrating` halt for the person.
- **`hw.optional.arm64`** is macOS's; elsewhere `os.uname().machine` is the native.

## Verdict

Ready to build.
