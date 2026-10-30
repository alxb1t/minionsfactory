---
version: v0.36
---

# Review inputs

A repo's architecture decisions and threat model get a known home; the cut, build and converge read them; the
bootstrap writes their starting files; MF writes its own threat model.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

A review can only judge a change against what is written down. Today a target's architecture decisions and its
threat model have no home the stations know: the cut designs without them, the build cannot halt on breaking one,
and security review falls back on generic categories. The review method that follows this version cites these
documents, so they must exist first.

## What Changes

- **The cut, build and converge read the architecture decisions and the threat model** — named in `AGENTS.md`, or
  found by name: `docs/decisions.md`, `ARCHITECTURE.md`, `docs/adr/*.md`, `THREAT_MODEL.md`.
- **The build halts** on a phase that contradicts a decision in force, unless the change amends it in a task.
- **The bootstrap writes `THREAT_MODEL.md` and an empty `docs/decisions.md`**, its `AGENTS.md` naming both; it halts
  on any of them, or `ARCHITECTURE.md`, already there.
- **MF writes its own `THREAT_MODEL.md`**, named for the cut, build and converge, and counted in converge's reading set.
- **D48** records where the documents live; **D18** names the two files the bootstrap also writes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The bootstrap writes the target layout* — MODIFIED: the templates also hold `THREAT_MODEL.md` and
    `docs/decisions.md`.
  - *The stations use AGENTS.md as target context* — MODIFIED: the cut, build and converge read the architecture
    decisions and the threat model; the build halts on a contradicted decision; the bootstrap halts on them.

## Impact

Changes `skills/mf-cut-change/SKILL.md`, `skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md` and its generic
references, `skills/mf-bootstrap/` (the skill and its templates), `tests/test_skills.py`,
`tests/test_metric_scripts.py`, `scripts/metrics/reading_set.py`, `scripts/metrics/references.py`,
`docs/decisions.md`, `docs/README.md` and `AGENTS.md`; adds `THREAT_MODEL.md`. The [delta](specs/sdd/spec.md) is
folded by release.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

The review method — the finding bar, the tiers, the packet's assembly, `inconclusive` — is the next version's.
Existing target repos adopt the documents by hand. No `ARCHITECTURE.md` template: decisions accumulate change by
change in `docs/decisions.md`.
