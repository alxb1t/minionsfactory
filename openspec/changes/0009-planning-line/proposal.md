---
version: v0.9
---

# Proposal — 0009-planning-line

**Change:** `0009-planning-line` · **Version:** v0.9 · **Record:** grilled in-session; the decisions and the
evidence behind them are in `design.md`, which is the record this change was cut from.
**Class:** `normal` — one change, one version, one tag. **Build mode:** hand-authored (Claude Code + human;
**no orchestrator automation**). **Doc-only** — nothing under `orchestrator/` or `tests/` changes.

## Why

**v0.8 deleted the planning line and left the method without one.** Seven `mf-` skills and four rubrics — 1753
lines — went, and what they knew was distilled into `docs/sdd.md`, written above the tool layer so that tooling
could *reference* the method rather than restate it. That was the right trade, and it left a gap: the stations
exist on the page and nothing runs them. Cutting a change is now unaided prose discipline, and the one property
that made the old line worth its weight — a fresh checker contradicting the producer — has no mechanism at all.

**Rebuilding it would repeat the mistake.** The 1753 lines were not deleted because they were wrong; they were
deleted because requirements move faster than a hand-maintained rubric can be kept honest. Writing new skills
buys the same debt at a later date.

**So adopt rather than build.** Two community tools already do the two halves: the `grilling` skill stress-tests
an idea against a person until the decisions are settled, and the **OpenSpec CLI** scaffolds a change, supplies
each artifact's authoring instructions, and validates the result. Neither is maintained here. Nothing new is
written that must be kept current — the version is **wiring, one real run, and a record of what the tools got
wrong**.

**The adoption also exposes four things the method page now states falsely**, all of them consequences of
deletions this project already made. `docs/sdd.md` still ends its feasibility axis in a verdict that
`mf-blueprint` emitted, and still describes a cut-station conformance check that `mf-inspect` performed; both
skills are gone. `CLAUDE.md` still says PM-side tooling runs from a vault, which stops being true the moment
grilling runs in the repo. And the spec tree carries a deliberate tombstone that no portable validator can accept.
A version that adopts a checker and leaves the tree unable to pass it has adopted nothing.

## What Changes

- **`openspec/config.yaml` carries the repo's contract** — a `context:` **pointer** to `docs/sdd.md` and
  `CLAUDE.md` (never a restatement of either), plus per-artifact `rules:` holding only what a reader cannot derive
  from those two pages: four artifacts always; the approach names the files it touches; one `spec.md` per
  capability directory, never one at the root; a zero-delta change declares `skip_specs`; `tasks.md` opens with a
  `## Progress` checklist in `- [ ] N — Title` form; and the seams instruction on the `design` artifact.
- **`CLAUDE.md` gains a *How a change is cut here* section** — the CLI commands, the `version:` frontmatter this
  repo's reader requires, the `skip_specs` mechanism, and the CLI version measured. Three now-false vault
  sentences are corrected in the same pass; the v0.7 containment invariant is untouched.
- **The spec tree becomes legible to a portable validator** — ten `openspec/specs/*/spec.md` gain a `## Purpose`
  section, `sdd` also gains `## Requirements`, and `openspec/specs/change-state/` is **deleted**, its one
  forward-pointing sentence relocated into `sdd`'s new `## Purpose`.
- **`docs/sdd.md` describes the line actually run** — the feasibility verdict is emitted by the grill station and
  recorded in `design.md`; the N-A declaration names its mechanism tool-neutrally; a clause admits tooling metadata
  beside the four artifacts; and the Grill and Cut paragraphs are rewritten so the change artifacts *are* the
  record, checked internally rather than against a document this repository does not hold.
- **BREAKING (convention).** The N-A spec delta stops being a `specs/README.md` and becomes `skip_specs: true` in
  a tracked `.openspec.yaml` plus `specs/.gitkeep` — the two are mutually exclusive, measured. The
  `0004-planning-skills` / `0006-teardown` precedent is superseded for future changes; the archived changes
  themselves are untouched and out of the validator's scope.
- **BREAKING (convention).** The tombstone convention — a dead capability leaving an empty marker directory — is
  retired, not merely applied differently to one file.
- **Evaluated and not adopted, with reasons recorded** — `to-spec`, `to-tickets`, and the `docs/agents/` adapter.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

**This change declares `skip_specs: true`.** No requirement changes: the deleted capability held none, `## Purpose`
headings add none, and `docs/`, `CLAUDE.md` and `openspec/config.yaml` sit outside the spec tree. Inventing a
requirement to satisfy the validator is forbidden by `docs/sdd.md` and by the artifact instructions alike, so the
delta is declared absent rather than manufactured.

## Impact

**Files.** `openspec/config.yaml`; `CLAUDE.md`; ten `openspec/specs/*/spec.md`; `openspec/specs/change-state/`
deleted; `docs/sdd.md`; this change's own artifacts; `CHANGELOG.md`.

**Not touched.** `orchestrator/`, `tests/`, `.minions/minions.toml` and its four mirrors, `.github/workflows/ci.yml`,
`Makefile`, `README.md`, `pyproject.toml`, `uv.lock`.

**Dependencies.** None added. The OpenSpec CLI is operator tooling, installed globally and **recorded, not pinned**
— no `package.json`, no second runtime in the repository, and the approval gate is not tripped.

**The gate is unchanged.** `openspec validate` does **not** join the `gate` array: it would put node in CI against a
`python-uv` readiness profile that does not describe one, and an unproven external CLI does not belong in a blocking
gate on the version that first adopts it. Validation is phase acceptance and a release precondition here, and joining
the gate is a v0.10 question to be answered with a version of evidence behind it.

**Risk carried.** The capability deletion has no representation in any delta — `## REMOVED Requirements` removes
requirements and this capability holds none — so it is a hand-edit recorded in `tasks.md`, and the release fold is a
no-op over it. Its only machine-checkable trace is that `openspec validate --all --strict` goes green.
