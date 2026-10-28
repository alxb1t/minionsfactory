---
version: v0.31.2
backlog: [0023·S1, 0023·S5, 0023·R8]
---

# Gate-recipe hardening

A branch can no longer certify its own weakened gate: both sides' dry runs come from fresh exports, and every
route that silences a check halts.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the corrected requirement.

## Why

Converge and the release compare `make -n gate` with the base's `Makefile` piped to make — run in the branch's tree.
So the base side reads the branch's included makefiles and `$(MAKE)` sub-makes (`0023·S1`), and `make -n` prints
`-false` as `false` and ignores `.IGNORE` and `MAKEFLAGS += -i` (`0023·S5`, `0023·R8`). A branch can weaken its gate
and pass both stations.

## What Changes

- **A bundled check**, `skills/mf-converge/scripts/gate_check.py`, run as a `uv` script: it exports the base and
  `HEAD` with `git archive`, runs make in each with `MAKEFLAGS` and `MFLAGS` cleared, and removes the exports.
- **Unplanned:** a branch that changes any **gate makefile** — any file make reads for `gate` on either side — or
  the gate's dry run halts.
- **Planned** (a cut task names the recipe): a dropped command line, or an added `-` prefix, `.IGNORE` or `-i` in
  `MAKEFLAGS`, halts unless the task quotes it.
- **An export that lacks a path, or a dry run that fails in one, halts**, naming the side.
- Converge's precondition 6 and the release's precondition 8 call the check; the principle's *Held by:* names it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`, a MODIFIED requirement, corrected:
  - *Converge and the release halt on a gate the cut did not plan* — exports, gate makefiles, ignore marks, a
    failing export.

## Impact

Adds `skills/mf-converge/scripts/gate_check.py` and `tests/test_gate_check.py`. Changes
`skills/mf-converge/SKILL.md`, `skills/mf-release/SKILL.md`, `docs/principles.md` and `tests/test_skills.py`. The
[delta](specs/sdd/spec.md) is folded by release.

Dependencies: none — the standard library, git and make. The gate recipe stays unchanged.

## Not in this change

A weakening through a program the recipe calls — `./run-tests` edited to exit 0 — stays review's to read. No
worktree. The bootstrap templates' wording, which still holds. No new station, parameter, decision or requirement:
this is a patch.
