---
bump: patch
version: 0.90.1
beside: [0108-converge-script]
---

# Converge done order

A converge's `done` or `halt` is always its run's top line: `stamp.py` refuses any other order, and the run re-stamps a `done`
buried under the top. A test of a feature a change removes may go with it ([D39](../../../docs/decisions.md#d39--a-test-is-placed-by-its-cost)).

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

0107-sandbox-runner halted twice on a converge that had converged: its conductor stamped `done` and `debt` in one call, `done`
given first, so `debt` landed on top and the run read the log as unfinished ([design](design.md#context), F1). `stamp.py` checks
no order, and `conduct.py` reads only the top line (F4, F5). Separately, D39's rule on a removed test has no case for a feature
the change removes, so conformance's R6 blocks 0108-converge-script for deleting the tests of the mailbox it removes (F6).
Both are defects of what the line already does: a patch ([AGENTS.md](../../../AGENTS.md)).

## What Changes

- **The stamp** — `stamp.py` exits 2 on a call that gives `done` or `halt` before another event, and on any event for a run
  whose top line is `done` or `halt`, save a `halt` naming `.minions/debt.lock` or `.minions/backlog.lock`, under which converge resumes.
- **The check** — `conduct.py`'s converge check, finding `done` under the newest run's top line with both findings files clean
  at `HEAD` and the tree clean, stamps `done` again, `re-stamped by the run`, logs it and passes.
- **The rule** — D39 and each copy of its rule gain a third way: a removed test whose proofs cover only a requirement the
  change's delta removes is retired by that removal, the `## Tests` table naming the requirement. The copies are the principle, `I16`
  and `T5` of `mf-build` and `mf-cut-change`, the coverage-trace pass and `T5` of the worker reference, and the bootstrap template.

Requirements, in [the delta](specs/sdd/spec.md), all MODIFIED:

- *Converge keeps a status log* — `stamp.py` refuses `done` or `halt` anywhere but last in a call, and an event after a top `done`
  or `halt`.
- *The ship station judges every station from disk* — the converge check re-stamps a `done` under the top line.
- *A test is deleted or merged only as the design's table names it* — a requirement the delta removes retires a test.
- *Conformance judges test cost and traced coverage* — the coverage-trace pass accepts that retirement.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements above.

## Impact

Changes `skills/mf-converge/scripts/stamp.py`, `skills/mf-ship/scripts/conduct.py`, `tests/test_stamp.py`,
`tests/test_conduct.py`, `tests/fake_worker.py`, `docs/decisions.md`, `docs/principles.md`, `skills/mf-build/SKILL.md`,
`skills/mf-cut-change/SKILL.md`, `skills/mf-converge/references/worker.md` and `skills/mf-bootstrap/templates/AGENTS.md.tmpl`.
Dependencies: none. The gate recipe stays unchanged.

`0108-converge-script` opens `conduct.py`, `tests/test_conduct.py`, `tests/fake_worker.py`, `skills/mf-converge/SKILL.md` and `worker.md` too, and writes
the status log through `stamp.py`'s `main`: this change is built beside it, and `mf-integrate` merges it ([design](design.md#risks--trade-offs)).

## Not in this change

- The converge conductor as a script — 0108-converge-script.
- An edit of `skills/mf-converge/SKILL.md`: its rule, the last event given on top, already says where `done` goes, and 0108 cuts the file to a front.
- A change to `stage_of`: a log with `debt` above `done` still reads as an unfinished run, and converge goes on at Step 10.
