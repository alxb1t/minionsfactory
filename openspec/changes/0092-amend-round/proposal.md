---
bump: minor
after: [0090-supervisor-merge]
debt: [0071·S2]
---

# Amend round

An answered converge halt — the person's amend, the rescue's or the supervisor's — gets one review round over its own range,
never a reopen of converge from round 1 over the whole change.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

A halt answered past its head opens a run marked `· amended` that restarts at round 1 over the whole change with a fresh cap of
three. Those runs cost $55.2, 24% of converge's spend: 0087's two-line amend bought a 13-file round, and 0087 and 0088 looped on
it. The only reason recorded is a backstop for worker-written amends; the stale-claim pass and a re-run of each amended `Verify:`
catch what a scoped round would miss. The conductor and the skill also disagree on a halt past the judged head (0088 Run 4).

## What Changes

- **The amend round** — an answered halt opens a catch-up run marked `· amend` over `<judged head>..HEAD`, whatever the findings
  files' verdicts: the amend, the build's code for a phase it added, and converge's own unverified fix. One judge round, at most
  one fix round; a blocker left is `cap reached`. No run marked `· amended`, and no new round 1.
- **Amended `Verify:` lines re-run** — before the round's `start`, each `Verify:` line the range adds to `tasks.md`, ticked tasks
  included; one that fails halts `verify failed — <sub-task ids>`.
- **One answer rule** — a halt is answered by any commit when both findings files judged its head, else by an amend of the change
  directory past it, in `conduct.py`'s `_answered` and the skill alike.
- **No amend passes by rule** — By rule takes merges alone; the person's amend takes the round as the rescue's and the
  supervisor's do (`0071·S2`).
- **The worker's amend scope** — the full plan stays in the reading set, the stale-claim pass greps the whole tree for each claim
  the amend changes, and an amend card the amend settled goes `verified`.
- **The mark and its metrics** — `_amendable` reads `· amend` as `· catch-up`; `converge-rounds` skips amend runs, and
  `amend-rounds` counts them.
- **Shorter** — the converge skill and its worker reference end with fewer words than at `bb4cf51`.
- **The record** — D63; D15, D47, D53 and D60 edited; the principles, `THREAT_MODEL.md`, and `mf-rescue`'s and
  `mf-supervise`'s role lines.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *An answered converge halt gets one amend round* — ADDED: the answer rule, the `· amend` run over the files' head, the
    `Verify:` re-run, its own count.
  - *A converge halt answered by the person converges afresh* — REMOVED: the amend round replaces the reopen from round 1.
  - *The release ships only a reviewed head* — MODIFIED: by rule takes merges alone; an answered halt counts its own rounds.
  - *A catch-up over a merge the fixed rules reproduce is clean by recomputation* — MODIFIED: a selection holding an amend never
    passes by rule.
  - *A halted version is rescued in its run* — MODIFIED: the rescue's amend goes on to its amend round, not a `· amended` run.
  - *The converge fixer leaves the plan to the person* — MODIFIED: an amend card the amend settled goes `verified`.
  - *Each release records its run* — MODIFIED: converge's rounds skip amend runs; the amend rounds are counted.

## Impact

Changes `skills/mf-converge/SKILL.md`, `skills/mf-converge/references/worker.md`, `skills/mf-ship/scripts/conduct.py`,
`scripts/metrics/run.py`, `metrics/catalogue.toml`, `tests/fake_worker.py`, `tests/test_conduct.py`,
`tests/test_metric_scripts.py`, `skills/mf-rescue/SKILL.md`, `skills/mf-supervise/SKILL.md` (0089's), `docs/decisions.md`, `docs/principles.md` and `THREAT_MODEL.md`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- The rest of the token diet — `lighter-converge` and `lighter-build-cut`.
- A rescue amend at a `verify failed` halt: it is a halt before round 1, the person's to answer, until a run shows the rescue
  could.
- Changing `gate_check.py`, which adopts an amended `Verify:` without running it: the amend round runs it.
