---
version: v0.31
backlog: [0030·R3]
---

# mf-plan

The line's first station becomes an MF skill: `mf-plan` grills a version to settled decisions and writes the brief
`mf-cut-change` reads.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

The line plans with an adopted Claude plugin, `grilling`, which other executors do not carry and whose text moves
upstream. MF's own planning practice — facts at a commit, triggered backlog cards, the brief's shape — lives only
in one executor's memory. On 2026-10-26 a planning session switched a target's checkout to `main` to read facts
while a build ran in it, carrying the build's uncommitted edits along; no rule said a session that only reads must
not move the checkout.

## What Changes

- **`skills/mf-plan/SKILL.md`**, a new station: parameters `<what>`, `brief=` (required), `depth=light|hard` and
  `from=`; reads the target read-only at a named commit, by fresh helpers where the host can; runs MF's checks
  before its first round; asks the frontier in numbered rounds with a recommendation each; writes the brief after
  every round; ends on a settled table the person confirms.
- **The brief's contract**: fixed sections the cut can rely on, and a depth in its title.
- **`mf-cut-change`** names `mf-plan` as the station before it and halts on a light brief.
- **D5** is overturned for planning: a change is planned with `mf-plan`; the adopted skill is credited for its
  frontier.
- **The boundary principle** names the operator's brief, and the bundled metrics script's git reads of its own
  package, as its exceptions — closing `0030·R3`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`, each an ADDED requirement:
  - *The plan station reads the target without moving it* — the read-only commands, at a named commit.
  - *The plan station checks the line's rules before its first round* — triggered cards, the paydown line, the
    release's version form, decisions in force, metrics over their watch.
  - *The plan station writes the brief after every round* — its sections, `## Open`, `from=`.
  - *The cut halts on a light brief*.

## Impact

Adds `skills/mf-plan/SKILL.md` and its structural tests in `tests/test_skills.py`. Changes
`skills/mf-cut-change/SKILL.md`, `docs/decisions.md`, `docs/principles.md`, `AGENTS.md`, `README.md` and
`docs/README.md`. `make install-skills` links `mf-plan` with the others. The [delta](specs/sdd/spec.md) is folded
by release.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

No patch-release fix — a version of its own follows. No roadmap file or ritual: what the planning side does with a
brief stays the operator's. The `plan:` findings key stays as it is. No self-answered grilling for an unattended
line. No phrase scan over the new skill's text.
