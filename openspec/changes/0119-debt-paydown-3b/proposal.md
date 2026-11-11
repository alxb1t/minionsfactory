---
bump: patch
after: [0118-debt-paydown-3a]
debt: [0090·S5, 0091·S6, 0095·S2, 0095·S4, 0099·S3, 0099·S4, 0100·S3, 0106·S4, 0111·S2, 0104·S7, 0097·R7, 0100·R5, 0112·R3, 0090·R4, 0111·R2, 0111·R4]
---

# Debt paydown 3b

The small `conduct.py` debt cards and the ideas of this line are paid, each fix behind a test that was red first.

Reading map: [design](design.md) holds one decision per fix and the test cost, [tasks](tasks.md) holds the phases.

## Why

The debt file holds one-line cards in `skills/mf-ship/scripts/conduct.py`. Each is a fail-open parse, a link the conductor follows, a wrong wait or a test that costs more than it says. `0118-debt-paydown-3a` takes every card outside `conduct.py`; this change takes the small ones inside it. The design-sized cards wait for a conductor-hardening version.

## What Changes

- A card whose category is not a non-security one bars the rescue and the supervisor (`0095·S2`).
- The run-start move links no link, and unlinks a name that turned into one (`0095·S4`).
- Restoring `models.toml` creates a fresh file and never truncates one (`0106·S4`).
- Cleanup of a temporary folder chmods no parent of its root (`0111·S2`).
- The settle check exempts a `test fixed` path under the test folders alone, and halts on a commit past integrate's merge (`0090·S5`).
- A rejoin stops on a brief row with a control character before it prints the row (`0091·S6`).
- A stacked version whose dependency is unreleased on the default branch stays `stacked`, whatever its own tree holds (`0099·S3`).
- A wait for a dependency stacks as soon as it is the one unreleased dependency left (`0099·S4`).
- A missing-tool halt reads a result that opens with the CLI's message, not one that holds it (`0100·S3`).
- A Codex probe starts only with a probe's worth of converge's time left (`0104·S7`).
- A rejoin written while its version's rescue runs is kept until the thread ends.
- `converge.py` prints a halt on an ended status log and stamps none.
- Reasons for the cost of run tests, a corrected docstring and docstrings cut to the comment limit (`0097·R7`, `0100·R5`, `0112·R3`, `0090·R4`, `0111·R2`, `0111·R4`).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Each fix makes the code meet a requirement already in force; [D10](design.md#d10) says why no delta is written.

## Impact

`skills/mf-ship/scripts/conduct.py`, `skills/mf-converge/scripts/converge.py`, `tests/test_conduct.py` and `tests/test_converge.py`. No dependency, no skill prose, no spec.

## Not in this change

- The design-sized cards: 0107·S1, 0114·S3, 0111·S1, 0112·S2, 0108·S1, 0109·S1, 0068·S3, 0060·S6, 0062·S1, 0089·S2, 0090·S1, 0104·S3, 0116·S2, 0065·R8, 0111·R3 — a conductor-hardening version.
- Any file outside `conduct.py`, `converge.py` and their tests: `0118-debt-paydown-3a` holds them.
- A threat-model line for `0090·S5`'s tighter bound: the model's sentence stays as it reads.
