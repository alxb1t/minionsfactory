---
bump: minor
version: 0.111
---

# The debt file module

`.minions/debt.md` gets one module that writes and parses it, `skills/mflib/debtfile.py`, and the copies of its rules in converge, `debt_match.py`, the cut's context script and the conductor go through it.

Reading map: [design](design.md) holds the module, each copy's right side and the test cost, [tasks](tasks.md) its phases: the pin, the module, the stations, the fix, the record.

## Why

The debt file is read and written by converge, `debt_match.py`, the cut's context script and the conductor, each with its own title pattern, card extent, read and lock rule. They disagree: a bad byte stops `debt_match.py` and the freeze then writes `None.` with no halt; the release of the lock removes whatever stands at its name; a heading with trailing blanks gets a second heading.

This is the second half of the state-formats region: the findings module has landed, and the debt's parsers read a card through it. Later versions build on a debt that has one home.

## What Changes

- **A module.** `skills/mflib/debtfile.py` holds the read, a card's id, extent and count, the file and unfile of cards, the spoiled card's text, the lock, the patch's paths and the match, the page, and the release's clear.
- **The stations go through it.** Converge's debt functions and its spoiled card, `debt_match.py` as a thin command, `cut_context.py`, and the conductor's `_cards` and the migration's lock.
- **One side where the copies disagree.** One card, extent and count; one heading; one read, and the freeze halts on a debt it may not read; one lock that knows its holder; the debt write holds its folder; a `backlog.md` that is no file halts the migration; the writer's lookup of a heading is a read; `report` names a debt it may not read.
- **The record.** D16, D57, D66 and D83 amended; the module map, the recipe, the threat model and `mf-converge`'s text name the module.

Requirement lines, one per requirement the delta touches:

- MODIFIED *Every worktree shares the primary's run directory*: the lock is the module's, its wait the caller's, and a `backlog.md` that is no file halts the migration.
- MODIFIED *Converge keeps deferred work in one repository debt file*: the write goes through the module, holds its folder, and finds its heading as a read.
- MODIFIED *Converge bundles the debt cards on the diff's files*: `debt_match.py` is a command over the module, and a debt the freeze may not read halts it.
- MODIFIED *Converge's conductor is a script*: a debt card's title is read by the module's rule, and a debt the freeze may not read halts.
- ADDED *One module writes and parses the debt file*: the module, the card, the heading, the read, the lock and the holder's token.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements listed above, by [the delta](specs/sdd/spec.md).

## Impact

- **Code:** `skills/mflib/debtfile.py` is new; `skills/mf-converge/scripts/converge.py`, `skills/mf-converge/scripts/debt_match.py`, `skills/mf-cut-change/scripts/cut_context.py` and `skills/mf-ship/scripts/conduct.py` change; `skills/mf-converge/scripts/overlap.py` changes a comment.
- **Tests:** `tests/test_debtfile.py` is new; `tests/test_converge.py`, `tests/test_debt_match.py`, `tests/test_cut_context.py`, `tests/test_conduct.py`, `tests/test_staged_writes.py` and `tests/test_structure.py` gain cases or change the line by which they reach a name.
- **Record:** `docs/decisions.md`, `docs/modules.md`, `docs/recipes.md`, `THREAT_MODEL.md` and `skills/mf-converge/SKILL.md`; the release folds the delta into the living spec.
- **Behaviour:** none in the move; the fix phase changes the rights of the copies named in [design](design.md#d4).

## Not in this change

- `scripts/metrics/run.py` and `scripts/metrics/debt.py`, which count cards: they wait for the readers' version.
- The prose of `mf-plan`, `mf-cut-change` and `mf-release` that reads or deletes a card by hand: it waits for the version that turns prose into scripts.
- `migrate_debt`'s link-then-unlink by absolute path: it stays as it is, and its card is left to converge.
- Any edit of a debt card: `.minions/debt.md` is written under its lock by converge and the release alone.
- The stale break running anywhere but a run's start.
