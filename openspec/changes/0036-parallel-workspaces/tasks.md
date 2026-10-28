# Parallel workspaces — tasks

Build the settled [design](design.md), one phase at a time. The station text is the design's, word for word.

## Progress

- [x] 1 — Resolve one run directory in the scripts
- [ ] 2 — Make the cut work in worktrees
- [ ] 3 — Share the run directory and merge in the primary
- [ ] 4 — Record the workspaces

## 1 — Resolve one run directory in the scripts

- [x] 1.1 **HALT CHECK** `git rev-parse --path-format=absolute --git-common-dir` prints the primary's git directory from a linked worktree, the premise of [D3](design.md#d3).
  Verify: `git rev-parse --path-format=absolute --git-common-dir` prints a path ending in `/.git`.
- [x] 1.2 Resolve the run directory per [D3](design.md#d3) in `skills/mf-build/scripts/metrics.py`, `skills/mf-converge/scripts/gate_check.py` and `scripts/metrics/backlog.py`, and add the tests the [Tests](design.md#tests) table names.
  Verify: `uv run pytest -q -k primary_run_directory` reports `3 passed`.

## 2 — Make the cut work in worktrees

- [ ] 2.1 Rewrite the id and version preconditions in `skills/mf-cut-change/SKILL.md`, per [D2](design.md#d2).
  Verify: `grep -c 'every unmerged version branch' skills/mf-cut-change/SKILL.md` prints `1`, and `grep -c 'git tag -l' skills/mf-cut-change/SKILL.md` prints at least `1`.
- [ ] 2.2 Rewrite Step 4, Step 10 and the report in `skills/mf-cut-change/SKILL.md` for the declared worktree and setup, per [D1](design.md#d1).
  Verify: `grep -c 'git worktree add -b' skills/mf-cut-change/SKILL.md` prints `1`, and `grep -c 'Workspace setup:' skills/mf-cut-change/SKILL.md` prints at least `1`.

## 3 — Share the run directory and merge in the primary

- [ ] 3.1 Define the run directory in `skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md`, `skills/mf-release/SKILL.md`, `skills/mf-cut-change/SKILL.md` and `skills/mf-plan/SKILL.md`, per [D3](design.md#d3).
  Verify: `grep -l 'git-common-dir' skills/mf-build/SKILL.md skills/mf-converge/SKILL.md skills/mf-release/SKILL.md skills/mf-cut-change/SKILL.md skills/mf-plan/SKILL.md | wc -l` prints `5`.
- [ ] 3.2 Add the backlog lock to converge Step 9 and release Step 4.6, per [D3](design.md#d3).
  Verify: `grep -l 'backlog.lock' skills/mf-converge/SKILL.md skills/mf-release/SKILL.md | wc -l` prints `2`.
- [ ] 3.3 Rewrite release Step 5 and Step 6's no-merge commands for the primary, per [D4](design.md#d4).
  Verify: `grep -c 'git worktree list --porcelain' skills/mf-release/SKILL.md` prints `1`, and `grep -c 'worktree remove' skills/mf-release/SKILL.md` prints at least `1`.
- [ ] 3.4 Add the *parallel with* row to `skills/mf-plan/SKILL.md`'s checks, per [D5](design.md#d5).
  Verify: `grep -c '^| parallel with |' skills/mf-plan/SKILL.md` prints `1`.

## 4 — Record the workspaces

- [ ] 4.1 Add D44, amend D20, D16 and D18, and extend the overview line in `docs/decisions.md`, per [D6](design.md#d6).
  Verify: `grep -c '^### D44 · Versions run side by side in worktrees; one primary merges them$' docs/decisions.md` prints `1`, and `grep -c 'versions ship in cut order' docs/decisions.md` prints at least `1`.
- [ ] 4.2 Add the `## Workspaces` section to `AGENTS.md`, per [D1](design.md#d1).
  Verify: ``grep -c '^- \*\*Worktrees:\*\* `../`' AGENTS.md`` prints `1`.
- [ ] 4.3 Add the *Parallel workspaces* section, with the move's runbook, to `README.md`, per [D6](design.md#d6).
  Verify: `grep -c '^## Parallel workspaces$' README.md` prints `1`.
- [ ] 4.4 The suite has the planned tests.
  Verify: `uv run pytest --collect-only -q | tail -1` prints `53 tests collected`.
