---
bump: minor
after: [0100-worker-diet]
debt: [0095·R3, 0095·S5]
---

# Cut and converge diet

The cut's reviews and helpers read less, a pickup is checked by one verify pass instead of a round, the bundle carries
requirement diffs and the debt cards apart, and the release reads the findings files' frontmatter and card lines alone.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

On 0097 the cut's Opus plan reviews re-read everything, the second as much as the first, and most of the cut's reads
repeated files another worker of the cut had read. Converge's last round on 0096 only verified non-blocking pickups; the
bundle repeats the spec delta; checkers paged `diff.patch` again and again; the release read both findings files whole for
their verdicts; and 0098 and 0100 each paid a round and a rescue for a `design.md` drift line the fixer could not touch
([measured](design.md#context)). This version is the token diet's second,
after worker diet, `0100-worker-diet`.

## What Changes

- **Plan reviews** — each review gets a packet: the change directory, `HEAD`, the cut's notes file and the question, and a
  budget of 40 turns, reaching which it returns its doubts under `budget reached`. A second review judges only the change
  directory's diff since the first.
- **The cut's helpers** — run on Sonnet 5.5 · medium where the host offers it; the cut writes their answers to
  `.minions/changes/<change-id>/cut-notes.md`, which it and the reviewers read in place of the files again.
- **The pickup check** — once no blocker is open, a pickup's fix is checked by one fresh verify worker at `medium`
  effort over the pickup's own diff; it is no round, so no round 3 runs for a pickup.
- **The bundle** — each requirement the delta modifies or removes as an old→new diff; the debt cards on the diff's files
  in their own file, `debt-cards.md`, which adversarial reads in place of the bundle; each checker reads `diff.patch` once,
  in slices, never a slice again.
- **The release** — reads each findings file's frontmatter and, by one `grep`, its cards' title, Priority and Status lines.
- **The fixer** — corrects the `design.md` prose a `drift` card names, never a decision: the `## Decisions` section, its
  rows and D-ids, stays an amend.
- **Debt** — `worker.md`'s amend-round sentence names conformance alone (`0095·R3`); `references/verify.md` joins
  `THREAT_MODEL.md`'s `## Surfaces` (`0095·S5`).
- **The record** — D71; D16, D40, D53, D57, D64 and D66 amended; the principles *Every edit opens a round* and *`fixed` is
  a claim*, and the *Checker* term.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *A fresh worker reviews the plan before the cut commits* — MODIFIED: the packet, the 40-turn budget, the second
    review on the diff since the first, the helpers on Sonnet 5.5 · medium and the cut's notes file.
  - *Converge keeps deferred work in one repository debt file* — MODIFIED: a pickup is checked by one verify pass, no
    round.
  - *The converge fixer leaves the plan to the person* — MODIFIED: the pickup check keeps an amend card's `wontfix` and
    runs `gate_check.py`; the fixer corrects the `design.md` prose a `drift` card names, never a decision.
  - *Converge hands each worker a bundle of what the change cites* — MODIFIED: requirements as old→new diffs; adversarial
    reads `debt-cards.md`.
  - *Converge bundles the debt cards on the diff's files* — MODIFIED: `debt_match.py` writes `debt-cards.md` whole.
  - *Converge's checkers are conformance and adversarial* — MODIFIED: the packets name `debt-cards.md`; `diff.patch` read
    in slices, once.
  - *A repeated finding escalates* — MODIFIED: the repeat rule reads `debt-cards.md`.
  - *The release reads the findings files' frontmatter and card lines* — ADDED.

## Impact

Changes `skills/mf-cut-change/SKILL.md`, `skills/mf-converge/SKILL.md`, `skills/mf-converge/references/verify.md`,
`skills/mf-converge/references/worker.md`, `skills/mf-converge/references/generic-conformance.md`,
`skills/mf-converge/references/generic-adversarial.md`, `skills/mf-converge/scripts/bundle.py`,
`skills/mf-converge/scripts/debt_match.py`, `skills/mf-release/SKILL.md`, `docs/decisions.md`, `docs/principles.md`,
`THREAT_MODEL.md`, `tests/test_bundle.py`, `tests/test_debt_match.py` and `tests/test_skills.py`.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

- One build worker per phase, and a model per phase: the build-per-phase version.
- A scripted spec fold for the release; dropping the skills listing; splitting `conduct.py`; the Codex usage-limit
  fallback; local models.
- `0095·R6`, D63's matching sentence: a card this change does not list.
- Judging the savings: the ledger over the three versions after each diet ships, against $43.7 a version.
