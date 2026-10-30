---
version: v0.37
---

# The review method

MF owns its review and security method on every host and model: one checklist and finding bar, run at two depths —
`standard`, one fresh worker per role file, and `high`, finders, verifiers and a gap sweep per role — and converge's
native engines leave.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the requirements.

## Why

Native Claude review is excellent and expensive, and runs only on Claude Code; most changes need a cheaper review
that still catches the obvious correctness and security defects, and the method must run on Claude, Codex, Qwen,
Kimi or any capable host. Today's generic references are a one-paragraph instruction each, with no finding bar, no
packet and no record a metrics station could read. The research behind this change is in the vault's review research
note, borrowed from Claude Code, Codex, Matt Pocock, gstack and CodeRabbit.

## What Changes

- **Both generic references are rewritten** as MF's method: a checklist per file, the finding bar, a do-not-flag list
  the target's threat model overrides, the standard packet, the size cap, `inconclusive` sections and a `## Refuted`
  list.
- **Converge takes `tier=standard|high`**, `standard` by default; `high` runs finders, a verifier per candidate, a gap
  sweep and a role writer per role, described in a new reference read only at `high`.
- **The card gains `Evidence:` and `Verdict:`**, and its Priority a category; the findings frontmatter gains `tier`,
  `mode`, `workers`, `model` and `packet`.
- **Native `/code-review` and `/security-review` leave converge**; native `/simplify` stays in the build.
- **The cut suggests the tier**, `mf-ship` passes it, the release reports it with any `inconclusive` section.
- **Decisions:** D11 rewritten, D40 and D47 amended, D49 added.
- **A calibration** on seeded and clean fixtures, run by the build.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *Engine selection follows the executor* — MODIFIED: review and security run MF's method on every executor;
    native `/simplify` stays.
  - *Independent workers have fresh contexts* — MODIFIED: no Claude Code exception; `high` dispatches more workers.
  - *Generic passes preserve the station boundaries* — MODIFIED: the checklists, the finding bar and the packet.
  - *Converge runs at a tier* — ADDED.
  - *A finding carries its evidence and verdict* — ADDED.

## Impact

Changes `skills/mf-converge/SKILL.md` and both its references, adds `skills/mf-converge/references/high-tier.md`;
changes `skills/mf-cut-change/SKILL.md`, `skills/mf-release/SKILL.md`, `skills/mf-ship/SKILL.md`,
`skills/mf-ship/scripts/conduct.py`, `skills/mf-bootstrap/SKILL.md`, `tests/test_conduct.py`, `tests/test_skills.py`,
`docs/decisions.md`, `docs/README.md` and `README.md`. The [delta](specs/sdd/spec.md) is folded by release.

Dependencies: none. The gate recipe stays unchanged.

## Not in this change

Charting the new fields is the next version's, review metrics. Native review stays the person's manual comparison,
never a converge mode. Native `/simplify` is unchanged. Different models inside one converge run, whole-repo audits,
automatic large-diff splitting and a runtime findings validator stay out.
