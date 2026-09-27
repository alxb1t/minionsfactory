---
version: v0.17
---

# 0017-converge-audit-fixes — proposal

**In one line:** the check loop gets the fixes its own audit measured. No unreviewed commit ships, anchored harms
block, docs drift gets its own tier, repeats escalate, review searches for stale claims, and a fix's test must
fail without the fix.

| read | for |
|---|---|
| this page | why, and what changes |
| [design.md](design.md) | the decisions (`D1`…`D9`), the evidence, and each skill's before → after |
| [tasks.md](tasks.md) | the build: one phase per group of rules |
| [specs/sdd/spec.md](specs/sdd/spec.md) | the requirements, each held by a scan |

## Why

An audit of `mf-converge` over one target repository's 25 converged changes found the loop worth its cost. It
stopped 25 distinct medium-or-worse defects that no test would have caught. It also measured where the loop
leaks ([evidence](design.md#evidence)). Commits shipped unreviewed, severities were mis-set, one gap was deferred
four times, prose went stale outside the diff, and fixes were tested against the record instead of the failure.

## What Changes

```
  release ── HEAD = findings head? ── no ─▶ halt: run converge's catch-up round
  converge ── catch-up round: verify head..HEAD, counts against the cap
  stations ── anchors ─▶ blocking · drift tier ─▶ picked · repeat ─▶ one level up
  review   ── stale-claim pass after the engine ─▶ drift cards
  fixer    ── red run before the fix, pasted ─▶ verifier checks it
```

- **No unreviewed commit ships.** `mf-release` halts unless `HEAD` equals the findings files' `head:`, and
  `mf-converge` gains a **catch-up round** over the gap. See [D1](design.md#d1), [D2](design.md#d2).
- **Anchors.** Data loss, spend, exposure and silent wrong output always block. See [D3](design.md#d3).
- **A drift tier.** Review grades `blocking | drift | nit`; drift does not block and pickup always takes it. See
  [D4](design.md#d4).
- **Repeats escalate.** A finding already in the backlog goes up one level; a fixed repeat clears its old card.
  See [D5](design.md#d5), [D6](design.md#d6).
- **Stale-claim pass.** Review greps the tree for what the diff renamed, deleted or recounted. See
  [D7](design.md#d7).
- **Red before green.** A fix sized `a test` carries the failing run from before the fix. See [D8](design.md#d8).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `sdd`: the ADDED and MODIFIED requirements below.

| requirement | what changes |
|---|---|
| The release ships only a reviewed head | new: `mf-release` compares `HEAD` with `head:`; `mf-converge` names the catch-up round |
| Anchored harms block, and drift has its own tier | new: the anchor list and the `drift` tier in `mf-converge` and `docs/sdd.md` |
| A repeated finding escalates | new: stations read the backlog; a repeat names the backlog id and goes up one level |
| Review searches for stale claims | new: the stale-claim pass, named in `mf-converge` |
| A fix's test fails without the fix | new: the fixer's red run, and the verifier's check of it |
| Converge keeps deferred work in one repository backlog | modified: pickup also takes every `drift` card; a fixed repeat's old card is deleted |

## Impact

| area | files |
|---|---|
| skills | `skills/mf-converge/SKILL.md` · `skills/mf-release/SKILL.md` |
| docs | `docs/sdd.md` |
| tests | `tests/test_skills.py` |
| dependencies | none |
| target repos | none to change. Their next converge uses the new rules |

## Not in this change

- **The parked runner.** `prompts/reviewer.md` and `prompts/security.md` keep `blocking | nit`. This is a declared
  divergence ([D9](design.md#d9)). It closes when the runner resumes.
- **Splitting large diffs.** The audit's largest leak; its threshold and split rule need their own grilling.
- **A whole-system review station.** A new station, not a rule.
- **Re-grading existing backlog cards.** The anchors and tiers apply to findings written after this release.
