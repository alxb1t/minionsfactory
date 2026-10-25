---
version: v0.28
---

# Prose guards retire

Skill prose stops being frozen by phrase scans, and the unbuilt autonomous design leaves the mandatory context.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

The phrase scans in `tests/test_skills.py` prove a sentence exists, not that a station obeys it. They also make
skill prose append-only: no sentence can be reworded without editing a test. The next version rewrites the skills
for length, and cannot do it under them.
D24–D35 and `docs/autonomous.md` describe a line that is not built, yet every station and worker reads
`docs/decisions.md` before work.

## What Changes

- **Retirement rule:** new decision D42, *skill prose is held by review, not by phrase scans*. `T5`, `I16` and
  review's coverage-trace pass accept a removed test mapped to the decision that retires it.
- **`W3` scoped:** it covers claims of fact about code. An instruction, or a principle held by a named skill step,
  is not such a claim.
- **The phrase scans retire:** every phrase scan and its twin leave `tests/test_skills.py`. The structural checks
  stay: the shared `I`, `P` and `T` ids, the card's one owner, the bootstrap templates, the bundled references.
- **The principles' *Held by:* lines** name the skill step that holds each rule instead of a retired test.
- **The sdd spec:** each requirement held by a retired scan keeps its SHALL text and gets a behavioural scenario.
  The Purpose line stops saying every rule is proved by a scan.
- **The autonomous line leaves the repo:** D24–D35, `docs/autonomous.md` and every live reference to them. The ids
  stay a gap.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: each requirement below gets a behavioural scenario in place of its scan; those marked † also change
  their SHALL text for D42.
  - *The skills run the repository's `make gate`* — a gate run and a missing gate.
  - *A release may skip the check loop, and says so* — a skip, a lone patch, a lone findings file.
  - *Converge keeps deferred work in one repository backlog* — pickup and the backlog write.
  - *The release does not read the backlog* — a paydown release.
  - *The release ships only a reviewed head* — a late commit, and the catch-up round.
  - *Anchored harms block, and drift has its own tier* — an anchored finding, and drift.
  - *A repeated finding escalates* — a finding that repeats a card.
  - *Review searches for stale claims* — a renamed path, and a review without the pass.
  - *A fix's test fails without the fix* — a fix with and without its red run.
  - *Converge keeps a status log* — a run's events and its end.
  - *A skill infers the one active change* — one, none and several candidates, and a branch mismatch.
  - *The cut runs no check before the human reads it* — the self-check.
  - *Converge and the release halt on a gate the cut did not plan* — a changed dry run.
  - *No station deletes a findings file or the diff patch* — a finished converge and release.
  - *Every station closes in a few sentences and names the next act* — a finished run, and a halt.
  - *The cut commits without waiting, unless it adds a dependency* — with and without dependencies.
  - *The release merges and pushes on the person's yes* — yes, no, and no `origin`.
  - *A HUMAN phase is handed over as a checklist of commands* — an unworked HUMAN phase.
  - *A test is deleted or merged only as the design's table names it* † — a removed test mapped to a decision.
  - *Review judges test cost and traced coverage* † — a removed test retired by a decision, and one carried by
    neither.
  - *The release records the gate's time* — the `Gate:` line.

## Impact

Changes `tests/test_skills.py`, `skills/mf-build/SKILL.md`, `skills/mf-cut-change/SKILL.md`,
`skills/mf-converge/SKILL.md`, `skills/mf-converge/references/generic-review.md`, `docs/decisions.md`,
`docs/principles.md`, `openspec/specs/sdd/spec.md`'s Purpose line, `AGENTS.md`, `README.md` and
`docs/README.md`. Deletes `docs/autonomous.md`. The [delta](specs/sdd/spec.md) is folded by release, not by the
build.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

No skill is shortened or rewritten beyond the named rows and sentences; that is the next version. The bootstrap
templates, the skills' `description:` frontmatter, the kept structural tests and decision D3 stay as they are. No
decision is renumbered, no backlog card is taken, and no autonomous skill or script is built. `CHANGELOG.md`
history and `openspec/changes/archive/` keep their references to the retired tests and the deleted page.
