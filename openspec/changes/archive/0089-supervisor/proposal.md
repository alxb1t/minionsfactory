---
bump: minor
version: 0.72
after: [0088-paydown-2]
debt: [0085·S1, 0087·S1]
---

# Supervisor

A second-tier station, `mf-supervise`, answers a build or converge halt the rescue diagnosed or was spent on, under the
version's `decide = "recommended"`, with one amend of the change directory the run checks and takes in the same thread.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

In 0087's run a supervising chat answered what the rescue could not — an amend needing the spec delta, a sub-task already
rescued, a verified box to tick, an integrate conflict — each also a restart; in 0085's, an integrate flag and a decision id
taken while it waited. None of it was code: each was a judgment the rescue may not make by design (D53, D60). D60 rejected a
supervisor role; the 2026-11-07 evidence reopens it.

## What Changes

- **A new station, `mf-supervise`** — the conductor starts it in the version's thread when the rescue diagnoses a build or
  converge halt, or is spent on it, under the version's switch alone. It amends anything under the change directory, the spec
  delta included, ticks a sub-task whose `Verify:` it ran green, and adds work as a new phase; never code, a test, a blocking
  security card, a gate approval, a threat-model risk, an integrate halt, a release, merge or push.
- **Its check** — one commit, the amend's subject, `Supervisor:` and `Decided-by: supervisor` trailers, paths under
  `openspec/changes/<id>/` alone; taken in-thread, logged `supervise — <id>: decided · <halt> · <sha7>`; anything else halts
  the version for the person.
- **Its cap** — one try a halt, at most `SUPERVISES = 2` a version a run.
- **Its models** — `[supervise]` in the models file, else `claude-opus-5-5` at `high` effort on Claude.
- **No worker amend is the person's** — the person's-amends route takes no commit carrying a `Rescue:` or `Supervisor:`
  trailer, and the catch-up reads a `Supervisor:` amend in a round, never by rule; the trailer-less route is recorded as
  accepted (`0085·S1`, `0087·S1`).
- **New work goes in a new phase** — a sub-task an amend adds, the supervisor's, the rescue's or the person's, goes in a new
  unticked phase after the last, never under a ticked one.
- **The record** — `report`, the close's ` · supervised <ids>`, the `supervisor-decided` metric; D61, with D15, D47, D53 and
  D60 edited; `THREAT_MODEL.md`; README and `AGENTS.md`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A supervisor answers what the rescue leaves* — ADDED: the trigger, the switch, what it may amend, the check, the
    in-thread resume, the cap, the models, the record.
  - *A halted version is rescued in its run* — MODIFIED: a commit carrying a `Rescue:` or `Supervisor:` trailer is no
    person's amend; a sub-task an amend adds goes in a new unticked phase.
  - *The release ships only a reviewed head* — MODIFIED: an amend carrying a `Supervisor:` trailer is a merges-and-amends
    commit, and no round over it is by rule.
  - *A converge halt answered by the person converges afresh* — MODIFIED: the catch-up reads a `Supervisor:` amend in one Step 7
    round, as a `Rescue:` one.
  - *A catch-up over a merge the fixed rules reproduce is clean by recomputation* — MODIFIED: by rule passes no amend carrying
    a `Supervisor:` trailer.
  - *A halt stops only its version, and a re-run resumes* — MODIFIED: a halted version starts no new worker but its rescue
    and, under its switch, its supervisor.
  - *A verify halt is diagnosed by the run* — MODIFIED: the version stays halted with no switch.

## Impact

Adds `skills/mf-supervise/SKILL.md`. Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-rescue/SKILL.md`,
`skills/mf-ship/SKILL.md`, `skills/mf-converge/SKILL.md`, `scripts/metrics/run.py`, `metrics/catalogue.toml`,
`docs/decisions.md`, `docs/principles.md`, `THREAT_MODEL.md`, `README.md`, `AGENTS.md`, `tests/test_conduct.py`, `tests/fake_worker.py` and
`tests/test_metric_scripts.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- The supervisor at an integrate halt, settling a text conflict for integrate to commit, and D45's edit — supervisor-merge.
- The brief's path kept at a passed cut and named in the supervisor's prompt — supervisor-merge.
- A supervisor for a halt older than the run, met at its start with no rescue in the run.
- A watcher running all night (D47), and a push notification.
- The supervisor's cost on the review-metrics page (`skills/mf-review-metrics/scripts/review_metrics.py`'s `STATIONS`) —
  when a run's supervisor spend needs comparing across models.
