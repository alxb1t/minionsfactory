---
bump: minor
debt: [0146·S10, 0146·S15, 0147·S3, 0090·S1, 0145·S5, 0112·S1, 0114·S3, 0146·S8, 0120·S3, 0140·S1, 0147·S1, 0116·S2, 0118·S2, 0104·S3, 0060·S6, 0062·S1, 0068·S3, 0108·S1, 0111·R3, 0112·S2, 0118·S3, 0119·S1, 0120·R4, 0120·R9, 0120·S4, 0121·S3, 0121·S4, 0129·R1, 0131·S3, 0132·S3, 0134·S2, 0136·S4, 0137·S5, 0139·S2, 0144·S3, 0145·S6, 0145·S7, 0146·S9, 0146·S14, 0065·R8, 0085·R3, 0143·S2, 0146·S12]
---

# Debt paydown 5

Empties the debt list but for the refactoring's riders: the cards paid by small fixes, and the cards settled closed as won't-fix, struck by the release with no task.

Reading map: [design](design.md) holds the decisions, the tests and the reach of each fix, [tasks](tasks.md) holds the phases, from the cut's rows to the texts.

## Why

The debt file holds cards of small defects, each a bounded fix, and cards whose accepted risk the threat model or a decision already states. A person's sort of the cards chose which to pay and which to close with no fix. A close with no fix is a card listed under `debt:` with no task: the release deletes every listed id and reports one it does not find ([D3](design.md#d3)).

## What Changes

- **Row `V2`** reads a negated `-k` word the test's name does not hold as unknown, and stays silent ([D7](design.md#d7), [D14](design.md#d14); 0116·S2).
- **Row `V6`** compares the removed and added lines of the searched file's diff block, by its header; a block with no header takes no part ([D7](design.md#d7), [D14](design.md#d14); 0118·S2).
- **The cut's kept output** keeps the newline of a line cut at 4000 characters, and the cut's halt marker is matched at a line's start (0146·S10, 0146·S15; [D5](design.md#d5)).
- **A worker's environment** drops every `UV_` and `PIP_` variable of the operator's, as preparation and the fetch do (0112·S1; [D13](design.md#d13)).
- **The run log's write** failing in the run's halt handler and in `stop_run` ends in a named stop, exit 2 (0140·S1; [D13](design.md#d13)).
- **`sandboxed()`** bounds its read after the deadline and closes the pipe, for every caller (0114·S3, 0146·S8; [D13](design.md#d13)).
- **A `Plan-text:` trailer** must name a card of the findings files (0147·S1; [D13](design.md#d13)).
- **The viewer's failed start** forgets the record only while it holds its own child's pid (0120·S3; [D13](design.md#d13)).
- **Integrate's Step 4.3 row** names every path the index changed (0090·S1, 0145·S5; [D6](design.md#d6)).
- **D76's accepts and the two Codex window titles** name the share's limit (0104·S3; [D8](design.md#d8)).
- **Requirement `Row V2 evaluates a -k expression`** — MODIFIED: an identifier negated by `not` that the name does not hold makes the row silent.
- **Requirement `A cut's mechanical steps are scripts`** — MODIFIED: row `V6` reads the removed and added lines of the searched file's diff block, and a block with no header takes no part.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements named above.

## Impact

- `skills/mf-cut-change/scripts/cut_check.py` and `tests/test_cut_check.py`: rows `V2` and `V6`.
- `skills/mf-ship/scripts/conduct.py`: the kept output, the halt marker, the environments, the run log's stops and `sandboxed()`.
- `tests/test_conduct.py`, `tests/test_sandboxed.py` and `tests/test_runlog.py`: the tests of those fixes.
- `skills/mf-converge/scripts/converge.py`, `skills/mf-converge/references/fix.md` and `tests/test_converge.py`: the trailer's card.
- `skills/mf-ui/scripts/viewer.py` and `tests/test_viewer.py`: the failed start's record.
- `skills/mf-integrate/SKILL.md`: Step 4.3's row.
- `docs/decisions.md` and `metrics/catalogue.toml`: D76's accepts and the titles of the Codex window metrics.

## Not in this change

- The riders of 5c3 `marks`: 0136·S3, 0138·S2, 0140·S3, 0142·S2 ([D1](design.md#d1)).
- Any edit of the debt file by a task; any change to how converge files a card of an accepted class ([D11](design.md#d11)).
- Attribution of a Codex share by tokens ([D8](design.md#d8)); a bound of the settle's paths in code ([D6](design.md#d6)); the verify pass's new question on a reworded delta, which D53 leaves to its judgment.
- A retry or a card for a timed-out plan check; a narrower unplanned-file exemption ([D9](design.md#d9)); a plan-text check of a fresh run after a fixer's halt ([D12](design.md#d12)).
