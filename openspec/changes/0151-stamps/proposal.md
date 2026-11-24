---
bump: minor
---

# Stamps

Converge stamps each findings file's counts, a halted version keeps its slot while its thread lives, and small checks stop the halts a hand-step caused.

Reading map: [design](design.md) holds the decisions and the test cost, [tasks](tasks.md) holds the phases: the stamp, the slot, and the row, the tag and `status`.

## Why

Some halts of 2026-11-20 to 2026-11-24 came from a worker's hand-step, not from the plan. A verify worker wrote `files: 3` for a freeze of more files, which halted 0144 and 0148, and the rescope sent the same checker out with a prompt that carried no count.

An unquoted `exits 5` in a `Verify:` read as exit 0, so 0149's halt check never ran at the cut. A halt freed 0148's slot while its supervisor was still to run, so the cap was passed, and 0149 took `v0.119.1` over a local `v0.119.0` that `main` never held.

Converge holds each value its workers kept getting wrong. A script writes it, and the check that read it is removed.

## What Changes

- Converge sets `head`, `round`, `files` and `commits` in each findings file after its checker returns and before it reads the file. A pickup check leaves `round`; a stub and a by-rule file stay as written.
- The scope comparison, `SCOPE_MISSED`, `rescoped` and the branch of `held` that called it are removed. [D88](../../../docs/decisions.md) loses its rescope sentence.
- The references stop telling a worker to write `head`, `round`, `files` and `commits`.
- `in_flight` counts a version whose thread is live whether a halt names it or not. A run-wide halt frees what it freed before. [D84](../../../docs/decisions.md) is reworded.
- A new cut-check row `V9` fails a `Verify:` whose word `exits` is not followed by a backticked integer.
- `next_tag.py` reads the tags the default branch holds merged.
- `status` prints a halting stage's reason after the stage.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd` ADDED: *Converge stamps a findings file's counts*, *Row V9 reads the token after exits*, *Status prints a halting stage's reason*.
- `sdd` MODIFIED: *A queued cut waits while the line is at its cap* (a halted version keeps its slot while its thread lives), *The release assigns the version* (the tags the default branch holds), *Converge's conductor is a script* (`head`, `round`, `files` and `commits` are stamped, not read as written).
- `sdd` REMOVED: *A verdict that misses the freeze's scope is sent out once more*.

## Impact

- Code: `skills/mflib/findings.py`, `skills/mf-converge/scripts/converge.py`, `skills/mf-ship/scripts/conduct.py`, `skills/mf-cut-change/scripts/cut_check.py`, `skills/mf-release/scripts/next_tag.py`.
- Skill text: `skills/mf-converge/references/worker.md`, `skills/mf-converge/references/verify.md`, `skills/mf-converge/references/generic-conformance.md`, `skills/mf-converge/references/generic-adversarial.md`, `skills/mf-cut-change/SKILL.md` and `skills/mf-release/SKILL.md`.
- Records: `docs/decisions.md` (D84, D88), `THREAT_MODEL.md`.
- Tests: `tests/test_findings.py`, `tests/test_converge.py`, `tests/test_conduct.py`, `tests/test_cut_check.py`, `tests/test_next_tag.py`.

## Not in this change

- A plan halt of any class; the build's box tick, commit subjects and trailers, a card's `Amend:`, the fixer's `plan check left:` and the `Plan-text:` trailer.
- A stamp of `passes`: it stays the worker's report, checked as before.
- The release script, which is the next version's: this change leaves `mf-release`'s steps as they are, save the tag's source.
- A new metric for versions in flight over the cap.
- The debt card `0138·S2`, which stays with the refactoring's `roots`.
