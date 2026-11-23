---
bump: minor
version: 0.117
debt: [0143·S6, 0143·S9]
---

# Cut catches

The conductor runs the cut's checker, the checker learns more faults of a plan's own text, and a person's phase is refused at the cut.

Reading map: [design](design.md) holds the decisions and the test cost, [tasks](tasks.md) the phases, the conductor's first.

## Why

A plan's own text halts versions the cut could have stopped: a design line that names code a task removes, a `Verify:` whose first word is no program, a `-k` that selects nothing, a phase only a person can do. The conductor reads the cut's commit subject, tree and models file alone, so a self-check row binds only as far as the cutter obeys its skill.

## What Changes

- The conductor runs `cut_check.py` after the cut commit. A failure starts the cutter once more, handed the failing lines in `cut.red`; a second failure halts the cut.
- A repository may declare `**Cut checks:**` in its root `AGENTS.md`; the conductor runs each command over the cut's worktree under the sandbox, on the same route.
- `cut_check.py` gains the rows `K7`, `V7` and `V8`; `verify_check.py` stops refusing a search for a range's text and stops passing an Oxford comma or an `e.g.`.
- A `**HUMAN` phase is refused by the cut's `I14` and by the brief check; the conductor, the plan check and the build keep reading one for a version cut before.
- The build edits a file no task names when a red `make check` needs it, and lists it on an `Unplanned:` line of its commit; conformance judges it.
- Requirement lines of the delta:
  - ADDED: A run checks each cut with the cut's checker.
  - ADDED: A repository declares the checks a cut passes.
  - ADDED: A plan holds no phase a person does.
  - ADDED: The build edits a file no task names when its check needs it.
  - REMOVED: A HUMAN phase is handed over as a checklist of commands, into the requirement above.
  - MODIFIED: A cut's mechanical steps are scripts, for the new rows.
  - MODIFIED: A Verify: is one plain command and counts honestly, for the search script's fixes.
  - MODIFIED: A moderate phase builds on its own model, which ends each phase's line with a rating.

## Capabilities

### New Capabilities

None. Every requirement joins `sdd`.

### Modified Capabilities

- `sdd` — the cut, its checker, the brief check, the build's check step and conformance's passes.

## Impact

- The conductor and its skill: `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md`, `docs/modules.md`.
- The cut: `skills/mf-cut-change/SKILL.md`, `skills/mf-cut-change/scripts/cut_check.py`, `skills/mf-cut-change/scripts/verify_check.py`.
- The plan: `skills/mf-plan/scripts/brief_check.py`, `skills/mf-plan/SKILL.md`.
- The build and converge: `skills/mf-build/SKILL.md`, `skills/mf-converge/references/worker.md`.
- Bootstrap and the model of threats: `skills/mf-bootstrap/templates/AGENTS.md.tmpl`, `THREAT_MODEL.md`.
- The record: `docs/decisions.md`.
- Tests: `tests/test_conduct.py`, `tests/test_cut_check.py`, `tests/test_verify_check.py`, `tests/test_brief_check.py`, `tests/test_structure.py`.

## Not in this change

- The Codex side's dollars, and a price for a Codex window share.
- A change to what the release's gate runs are.
- isekai's own mutation tool and its cut.
- A paydown version: it follows the token line.
- The workspace setup at the cut and a worker's worktree left behind: they stay with the rescue routes.
- The run log's new fields: they wait for the token line's last version.
