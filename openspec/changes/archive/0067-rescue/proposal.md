---
bump: minor
version: 0.56
backlog: [0063·S5]
---

# Rescue

A halted version is rescued in its run: a fresh worker fixes a simple plan halt and the version goes on, or writes a diagnosis
for a halt that needs the person.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

isekai, 2026-11-02 to -04: the cut-side halts (`720px`, `"stock_wait"`, `(D25)`, `flows`, the `$(seq)` loop) each waited for a
person to write an amend a fresh reader could have written, and `0095`'s caps waited for a grant, then a re-plan. The person wants an
`mf-ship` run that carries on through the simple halts unattended, with isekai's next batch as its test.

## What Changes

- **The halt file** — `mf-build` writes `.minions/build/<id>.halt` on a halt: the sub-task, the stop condition, the evidence.
- **`mf-rescue`** — a new station: it fixes a plan halt with one amend commit to `tasks.md` and `design.md`, or diagnoses.
- **The conductor** — spawns it in the halted version's thread, checks the commit's paths, clears the halt and goes on; at most
  three rescues a version, none for a sub-task rescued before; `[rescue]` in the models file, `skip = true` to turn it off.
- **`0063·S5`** — the rejoin and grants folders read and emptied through a directory file descriptor, no link followed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A halted version is rescued in its run* — ADDED: the halt file, the station, the path check, the limits, the record, the
    folders read by descriptor.
  - *A halt stops only its version, and a re-run resumes* — MODIFIED: a halted version starts no worker but its rescue.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-rescue/SKILL.md` (new), `skills/mf-build/SKILL.md`, `skills/mf-ship/SKILL.md`,
`AGENTS.md`, `docs/decisions.md` (D47, a new D53), `THREAT_MODEL.md`, `tests/test_conduct.py`, `tests/fake_worker.py` and
`tests/test_skills.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

A rescue that changes a settled decision; re-plan at the cap's own halt; the UI's "Help me" button; a rescue for a timeout, a usage
limit or D47's person-only halts.
