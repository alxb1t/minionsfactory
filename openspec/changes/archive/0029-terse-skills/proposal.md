---
version: v0.29
backlog: [0028·R4]
---

# Terse skills

The skills, their bundled role references and MF's shared context are rewritten shorter, with their behaviour kept.

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and
[the delta](specs/sdd/spec.md) for the one requirement it touches.

## Why

Every station reads its skill and the shared context before it starts, and much of that text restates one rule
in several places. A rule buried in repetition is easier for an agent to miss and harder for a person to
review. v0.28 retired the phrase scans that froze this wording, so it can now be rewritten.

## What Changes

- **The skills, rewritten action-first:** `mf-converge`, `mf-build`, `mf-cut-change`, `mf-release` and
  `mf-bootstrap`, with the generic review, security and simplify references. Steps as short lists, conditions as
  tables, branches as small ASCII flows, an example where a format is ambiguous.
- **The shared context, rewritten the same way:** `AGENTS.md`, `docs/principles.md`, `docs/decisions.md`.
- **A rule map** records where every rule, exception, halt and output of the old text went.
- **The reading sets are measured** before and after, by the same commands.
- **A fresh-reader check:** Codex and Claude Code answer fixed questions from the old and the new text; the new
  text must read the same as the old.
- Close `0028·R4`: the backlog requirement's SHALL text names every pickup size and writes only cards still true.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`:
  - *Converge keeps deferred work in one repository backlog* — its SHALL text names the `one line and a test` size
    and writes only cards whose **Still true?** check still shows the defect, as the skill does already.

## Impact

Rewrites `skills/mf-converge/SKILL.md`, `skills/mf-build/SKILL.md`, `skills/mf-cut-change/SKILL.md`,
`skills/mf-release/SKILL.md`, `skills/mf-bootstrap/SKILL.md`, `skills/mf-converge/references/generic-review.md`,
`skills/mf-converge/references/generic-security.md`, `skills/mf-build/references/generic-simplify.md`,
`AGENTS.md`, `docs/principles.md` and `docs/decisions.md`. `README.md` and `docs/README.md` change only where a
link or a heading they cite moves. No station changes what it does. The [delta](specs/sdd/spec.md) is folded by
release.

Dependencies: none. The gate recipe and `tests/` stay unchanged.

## Not in this change

No new shared-reference file and no conditional loading: every station reads what it reads today. The skills'
`description:` frontmatter, the bootstrap templates, the headings and id tables the structural tests read, and
every path, event, key, status, severity and card field stay as they are. Converge precondition 6 and release
precondition 8 keep their substance word for word. No compression target, and no claim about tokens or cost.
No other backlog card is taken.
