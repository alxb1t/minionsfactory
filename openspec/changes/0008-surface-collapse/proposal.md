---
version: v0.8
---

# Proposal — 0008-surface-collapse

**Change:** `0008-surface-collapse` · **Version:** v0.8 · **Intent record:** vault
`planning/v0.8/v0.8_grilling.md` (the grilling record — this version's PRD-substitute; the change is cut from it
and checked against it)
**Class:** `normal` — one feature, one version, one tag. **Build mode:** hand-authored (Claude Code + human;
**no orchestrator automation**). **Not doc-only** — see *Why it is not doc-only* below.

## Why

**Seven skills and four rubrics cost 1753 lines to maintain a planning line the project no longer runs.**
`mf-teardown` (462) plus `compliance.md` (586) are **1048 of that — 60% of the surface for one read-only
reader**. The line they implement takes days to get from an idea to a cut change, most of it spent producing
documents the change then restates.

`mf-teardown` is deleted **and not because it failed** — its v0.7 run returned `verdict: compliant`,
`criteria_total: 20`, zero gaps. It goes because the requirements move faster than a 586-line rubric can be kept
honest, and a runner whose rubric is a standing maintenance debt costs more than the measurement is worth. This
settles the fork the abandoned v0.8 was going to deliberate: **the document is the product, the runner is not.**

**Deletion is not discard.** The four rubrics carry real content, and it lands in one place instead of four:
`prd-readiness` and `feasibility` become *what must be settled before a change is cut*; `conformance` becomes
*how a change is checked*; `compliance`'s criteria become *the readiness checklist*. All of it in **`docs/sdd.md`**
— the SDD approach and conventions on one page, written **above the tool layer** so that v0.9's and v0.10's skills
*reference* it instead of restating it. That restating is precisely how the four rubrics drifted from the six role
prompts in the first place.

**`docs/sdd.md` is the artifact that travels.** The standard has already travelled once unassisted: isekai carries
`openspec/`, `.minions/minions.toml` and a repo `CLAUDE.md`, and **no `prompts/` and no `docs/`**. The page
describes that footprint and assumes no installed orchestrator, because the repos it is for do not have one.

### Why it is not doc-only

The roadmap called this *"mostly `git rm` plus one page."* Two shipped artifacts assert the surface being deleted:

- `tests/test_conventions.py:139` hard-codes `"skills"` in `_SCANNED_VAULT`, and `:147` asserts that tuple
  **verbatim** — deliberately, so narrowing it is a visible edit rather than a silent one.
- `openspec/specs/sdd/spec.md:206` names **`skills/`** in the THEN of the live scenario
  `sdd:vault-layout:no-retired-vault-vocabulary`.

Delete the directory and **nothing goes red**: `_text_files()` on a missing root calls `rglob` on a nonexistent
path, which yields nothing and raises nothing. The guard stays green while scanning one root fewer, and the living
spec keeps asserting a root set that no longer exists — a document asserting something the tree does not do, which
is the defect class v0.7's review found over and over.

The deletion also **unlocks a simplification**. The spec justifies the vault needles having their *own* root set
*"because a retired plan needle is live check text inside `skills/`"* (`openspec/specs/sdd/spec.md:207-208`) — and
that text is `skills/rubrics/compliance.md:68,564`, deleted here. With it gone the two needle sets share one root
set. And `tests/test_conventions.py:126-128` records `template/`, `.github/`, `Makefile` and `pyproject.toml` as
outside the scan, saying in as many words: *"Widening is recorded for v0.8."*

All fourteen needles were measured at **zero hits** across every affected root before either edit — both changes
are green before they are made.

## What (scope)

1. **`docs/sdd.md`** — two parts. *The method:* the change contract, traceability, the gate, the loop, the
   findings contract, the release fold. *Adoption:* what must be settled before a change is cut, then the
   readiness checklist. Generic: no module names, no vault paths, no assumed orchestrator. ~220–260 lines.
2. **`CLAUDE.md` shrinks by ~70 lines.** The method moves out — the change contract, the findings contract, the
   version-line rule, the release fold, "the gate is run, never summarized". What stays is what is true about
   **this repo**: its six gate commands, its seams, the no-LLM invariant, the guardrails. The split line is chosen
   so `prompts/coder.md:29`'s account of `CLAUDE.md`'s contents stays accurate and **no role prompt changes**.
3. **Delete** all seven `mf-*` skills, all four rubrics, the `skills/` directory, `template/`, both `Makefile`
   skill-install targets, and `README.md`'s planning-line section — replaced by a short **"The method"** section.
   `make uninstall-skills` runs **first**, so the eight `~/.claude/skills/` symlinks die cleanly.
4. **The guards follow the tree.** Drop `skills/` from the root set, merge the two needle sets onto one shared
   set, widen to `.github/`, `Makefile` and `pyproject.toml`. One `MODIFIED` requirement in the `sdd` delta
   carrying both affected scenarios. One new structural test — `docs/sdd.md` exists and `docs/README.md` links it
   — carrying `spec_exempt`, not a scenario.

## Non-goals

- **No new capability.** No Python under `orchestrator/` is touched; nothing the orchestrator does changes.
- **No `mf-change`, no role skills, no `mf-execute`** — v0.9 and v0.10. `docs/sdd.md` is written so they can
  reference it rather than forcing their design now.
- **No scaffolding command.** Stamping the footprint into a new repo is `mf-stamp`, and it stays on the backlog.
- **No replacement rubric.** The four are distilled into prose and deleted; nothing measures a repo automatically
  after this version.
- **No content guard over prose.** A needle set policing which file may say what is a new rubric-shaped
  maintenance debt in the version that exists to delete one.
- **Track B stays parked.** The 162-test suite it owns is left alone rather than trimmed.
