---
bump: minor
backlog: [0055·S2, 0051·R8]
---

# Rejoin

A halted version rejoins the live run once it is fixed: `/mf-ship` during a run takes it back, with every newly cut version,
and the versions still running carry on.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

isekai, 2026-11-03 and -04: `0093` halted while `0092` ran, and its fix waited for the whole run to end; `0095`'s fix after a
cap halt still read `converge-halted`, so every fix cost a grant, and converge itself refused a run past the cap with no grant
(Run 6, 12:14); a second `grant`, its first still waiting, was refused naming nothing to run; and every sibling release that
touched `AGENTS.md` halted each started version at the next start.

## What Changes

- **A rejoin request** — `conduct.py rejoin [<id>]` writes `.minions/runs/rejoin/<id>`; `/mf-ship` sends it when a run is live;
  the live run polls the folder and takes back every version whose stage on disk is no longer a halt, newly cut ones included,
  but none whose models file changed since the run read it.
- **A new executor mid-run** — the live run probes it once, before its first worker; a failed probe halts only that
  executor's versions.
- **A fix voids a converge halt** — the halt's head the findings files' `head:`, and `HEAD` past it → the stage is `converge`,
  and converge opens a run marked `· amended`, from round 1.
- **`grant`** — names `/mf-ship` when it refuses; during a live run it writes the grant and a request; the run logs `grant`.
- **The base** — a started version behind a gate change gets the default branch merged in when the merge is clean or only the
  changelog and decisions rules' paths conflict.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A halted version rejoins a live run* — ADDED: the request, the poll, the versions taken, the probe, the close.
  - *A converge halt answered by the person converges afresh* — ADDED: the void halt, the `· amended` run, a resumed grant.
  - *The ship station takes cut versions to the default branch* — MODIFIED: a started version behind a gate change merged in.
  - *A run's plan is read once* — MODIFIED: a joining version's models read as it joins; one whose models file left the
    plan stays out.
  - *A station's executor comes from the models file* — MODIFIED: a failed probe at the start stops the run; one for a
    joining version halts only the versions on its executor.
  - *A person can grant one more round* — MODIFIED: the refusal names `/mf-ship`; a grant during a live run.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-ship/SKILL.md`, `skills/mf-converge/SKILL.md`, `docs/decisions.md`
(D47), `THREAT_MODEL.md`, `tests/test_conduct.py` and `tests/fake_worker.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

A rescue that fixes a halt itself; a request to a run that has ended; rejoin after a run-level halt; the viewer, which reads the
same log later.
