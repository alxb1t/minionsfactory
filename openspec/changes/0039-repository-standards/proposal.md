---
version: v0.34
---

# Repository standards

A new repo gets `CODING_STANDARDS.md` and `CONTRIBUTING.md`, named mandatory context by its `AGENTS.md`; the build
and converge read them in any repo that has them; MF adopts both; the comment rules default to no explanatory
comment.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

A repo's coding and contribution rules have no home: an agent reads `AGENTS.md`, finds neither, and invents
conventions. The bootstrap writes no such file, and the review checks "the target's standards" without naming one.
The comment rules allow explanatory comments that go stale and mislead the next agent.

## What Changes

- **The bootstrap writes `CODING_STANDARDS.md` and `CONTRIBUTING.md`**, small and language-neutral, and its
  `AGENTS.md` names both mandatory context. It halts on an existing `CODING_STANDARDS.md`, `CODE_STANDARDS.md` or
  `CONTRIBUTING.md`.
- **The build and converge read the standards files** at the root when present, named or not; a contradiction
  between them is the person's.
- **The comment rules change:** `C1` is no explanatory comment, `C2` its exceptions; a project rule that names a
  `C` rule replaces it.
- **MF adopts both files**, its `AGENTS.md` naming them; the metric scripts count and check them.
- **D46** records where a repo's own rules live; **D18** names the two files the bootstrap also writes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *The bootstrap writes the target layout* — MODIFIED: the templates also hold `CODING_STANDARDS.md` and
    `CONTRIBUTING.md`.
  - *The stations use AGENTS.md as target context* — MODIFIED: the template names the standards files; the build
    and converge read them when present; the bootstrap halts on any of them.
  - *The build's comment rules default to no explanatory comment* — ADDED.

## Impact

Changes `skills/mf-bootstrap/` (the skill and its templates), `skills/mf-build/SKILL.md`,
`skills/mf-converge/SKILL.md` and its generic references, `tests/test_skills.py`, `tests/test_metric_scripts.py`,
`scripts/metrics/reading_set.py`, `scripts/metrics/references.py`, `docs/decisions.md`, `docs/README.md`,
`README.md` and `AGENTS.md`; adds `CODING_STANDARDS.md` and `CONTRIBUTING.md`. The [delta](specs/sdd/spec.md) is
folded by release.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

Adopting an existing target repo is the person's, by hand. MF's existing comments stay, the `Makefile`'s long ones
included: the rules apply to the text a phase writes. The review method and the native engines are unchanged. The
`converge-reading-set` watch stays breached until a change cuts converge's reading load.
