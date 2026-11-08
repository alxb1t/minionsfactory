---
bump: minor
after: [0098-beside]
debt: [0050·R5, 0095·R6]
---

# Stacked builds

A dependent builds on its dependency's built head once that build check passes, waits as `stacked`, and converges only
after the dependency released and its release was merged in.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

`after:` holds a dependent's build until its dependency releases: through a converge of about 45 minutes, which rarely
changes the code the dependent needs, and changes it less since the amend round. The dependent can build meanwhile, on the
built head, and still be judged only against the released dependency.

## What Changes

- **The stack** — once a version's one unreleased `after:` dependency passes its build check, `conduct.py` merges that
  dependency's built head into the version, with no agent, writes its sha to `.minions/changes/<id>/stacked-on`, and the
  version builds. Built, it waits in a new stage, `stacked`, shown by `conduct.py status`.
- **The merge back** — once the dependency releases, the run merges the default branch in, as for any dependent, removes
  `stacked-on`, and converge runs a normal round 1. `integrate.py`'s `changelog` rule keeps only the entries the branch added
  past a stacked base's, so the dependency's entries are not carried twice.
- **The base** — while `stacked-on` stands, the build's gate check and metrics, `mf-simplify`'s range and the gate's diff
  coverage take its sha as their base. `I17` also passes on that head holding the dependency's change; integrate's Ready and
  release precondition 10 still need the dependency released.
- **The reset** — an amend of the dependency's change directory past the stacked-on head that changes a decision resets the
  dependent to its cut commit and removes `stacked-on`; it stacks again on the dependency's next build.
- **The metric** — `after-wait-minutes`, the time a dependent waits on its `after:` ids, from the run log's new `wait` events.
- **The debt** — `merge_in` compares the git config again right before its commit (`0050·R5`); D63 says conformance alone
  keeps the full plan (`0095·R6`).
- **The record** — D72; D44, D45, D47 and D57 amended; the threat model names the stacked build; `mf-ship`'s flow.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A dependent builds on its dependency's built head* — ADDED: the trigger, the merge of a ref, `stacked`, `stacked-on` and
    its bases, the merge back, the reset.
  - *A version declares what it builds on* — MODIFIED: a dependent starts once its dependency released, or as the stack says;
    `I17` takes the stacked-on head at the build.
  - *A halt stops only its version, and a re-run resumes* — MODIFIED: a dependent stacked before its dependency halted builds
    on, then blocks.
  - *The ship station takes cut versions to the default branch* — MODIFIED: a stacked version gets no gate merge of the default
    branch while it stands stacked.
  - *The integrate station resolves mechanical conflicts by fixed rules* — MODIFIED: the `changelog` rule keeps the branch's
    entries past a stacked base's, and runs on a stacked branch's merge, clean or not.
  - *Each release records its run* — MODIFIED: `after-wait-minutes`.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `skills/mf-integrate/scripts/integrate.py`, `scripts/metrics/run.py`,
`metrics/catalogue.toml`, `Makefile`, `skills/mf-build/SKILL.md`, `skills/mf-cut-change/SKILL.md`,
`skills/mf-simplify/SKILL.md`, `skills/mf-ship/SKILL.md`, `docs/decisions.md`, `THREAT_MODEL.md`, `tests/test_conduct.py`,
`tests/fake_worker.py`, `tests/test_integrate.py`, `tests/test_gate_run.py` and `tests/test_metric_scripts.py`.

Dependencies: none. The gate recipe changes one line: diff coverage reads its base from `stacked-on`.

## Not in this change

- Stacking on two unreleased dependencies at once, or on a built head that lacks the dependent's base: such a dependent
  waits as before ([D1](design.md#d1)).
- Stopping a dependent's running build at its dependency's re-plan: the reset is read between stations
  ([D6](design.md#d6)).
- A `beside:` reader: `0098-beside`'s design D4 keeps none.
- A separate catch-up round for what the dependency's converge changed: round 1 judges against the default branch, which
  holds the release ([D3](design.md#d3)).
