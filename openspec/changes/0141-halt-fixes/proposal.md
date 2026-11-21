---
bump: patch
---

# Halt fixes

Fixes the few-line defects that halted isekai's runs and MF's own: a check read wrong, a decision compared by its bytes, a queue that strands its dependents.

Reading map: [design](design.md) holds each fix as a decision and the test cost, [tasks](tasks.md) builds them phase by phase: the plan check, the conductor, the queue, integrate and converge, then the rule.

## Why

A run halts today on defects the line already has the words for: a rescue that dedents a code block in a decision is refused as if it had decided, a `Verify:` that says `exits 2` passes only on exit 0, and a cut halts on an `after` that released while it waited. Each fix is a few lines, so one patch holds them, and no decision changes.

## What Changes

- **The plan check** reads every span after an output verb as output until `then`, `;` or the sentence's end, judges `` exits `<N>` `` by the exit, drops `VIRTUAL_ENV` from a command's environment, and `verify_check.py` loads that parser in place of its copy.
- **The conductor** compares a design's decisions with each run of whitespace as one space, removes `build.halt` when it spawns a build, and reads `origin` once more when the read after its own push fails.
- **The queue** drops a released `after` from what it hands the cutter, `cut_pre.py` passes a released id, and `rejoin` of a cut clears and requests each dependent halted `after <id> is cut-halted`, down the chain.
- **Integrate** renumbers the changelog first, skips and names a conflicted path, and halts once after every file.
- **Converge** counts a role whose verdict is `changes-requested` with no open card that blocks as clean, writing `clean` into its file, and reads a `changes-requested` file with no open card as malformed.
- **The rule** in `mf-rescue` and `mf-supervise`: a `Verify:` that cannot pass is retargeted or split, never replaced by one that proves less.

Requirements, one line each, all MODIFIED in `sdd`:

- A plan check holds the plan to the built tree: the span rule, `exits`, the environment, the one parser.
- A rescue decides by the version's switch: whitespace reads as one space.
- A run goes on while origin cannot be reached: one more read after the run's own push.
- A version declares what it builds on: a released id is met.
- A cut halt is the plan's, answered by a re-plan and a rejoin: the cascade.
- The integrate station resolves mechanical conflicts by fixed rules: the order, the skip, the one halt.
- The integrate station renumbers the branch's changelog entries: before any recital.
- Converge's conductor is a script: a verdict read against its cards.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements above.

## Impact

- Code: `skills/mf-converge/scripts/plan_check.py`, `skills/mf-converge/scripts/converge.py`, `skills/mf-cut-change/scripts/verify_check.py`, `skills/mf-cut-change/scripts/cut_pre.py`, `skills/mf-ship/scripts/conduct.py`, `skills/mf-integrate/scripts/integrate.py`.
- Text: `skills/mf-integrate/SKILL.md`, `skills/mf-rescue/SKILL.md`, `skills/mf-supervise/SKILL.md`, `docs/modules.md`.
- Tests: `tests/test_plan_check.py`, `tests/test_verify_check.py`, `tests/test_structure.py`, `tests/test_conduct.py`, `tests/test_cut_pre.py`, `tests/test_integrate.py`, `tests/test_converge.py`.

## Not in this change

- isekai's `tools/mutate.py` and its derivers' step: isekai's line.
- The stack's reset on a dependency's re-plan: D72 stands as written; the whitespace rule removes the reformat case.
- `_settle_kept`, and the supervisor's settle paths: they open D61, which a later version takes.
- The probe, and the rest of the debt.
