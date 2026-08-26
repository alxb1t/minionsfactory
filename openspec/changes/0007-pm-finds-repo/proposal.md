---
version: v0.7
---

# Proposal — 0007-pm-finds-repo

**Change:** `0007-pm-finds-repo` · **Version:** v0.7 · **PRD:** vault `planning/v0.7/v0.7_pm_finds_repo.md` (R1–R5)
**Build mode:** hand-authored (Claude Code + human; **no orchestrator automation**). **Doc-only change** — ships
prose (six skills, three rubrics, a worked example, README lines) and one vault convention, not test-backed
Python, so its **spec delta is N-A** (see `specs/README.md`, the `0004-planning-skills` precedent).

## Why

The `mf-*` planning line points the wrong way, and it is already broken.

The standing rule is *the vault reaches the repo; the repo never reaches the vault.* The planning line is the PM
side — the half of the product that lives in the vault — and it violates that rule directly: `mf-blueprint`,
`mf-forge` and `mf-inspect` each run with **cwd = the target repo** and resolve the vault out of **that repo's
`.env`**, via `VAULT_PROJECT_DIR`. The PM side finds itself by asking the repo where it is.

**And the line is broken now, not prospectively.** All six line skills resolve their artifacts under
`$VAULT_PROJECT_DIR/prd/…`; the vault restructured `prd/` → `planning/vX.Y/`. Every stage after `mf-order`
resolves a path that no longer exists.

**Why now — two reasons, the second forcing.** v0.8 deletes `VAULT_PROJECT_DIR` from `.env`, so fixing these
skills afterwards would leave the authoring line dead for the length of a version. And v0.8 **cannot be authored**
until this ships: `mf-forge` pointed at the v0.8 PRD looks for `prd/v0.8_decoupling.md` and finds nothing. A
prerequisite that blocks the authoring of the version it belongs to is a precursor, which is why this was split
out of v0.8 and why everything behind it renumbered one slot.

## What (scope)

1. **R1 — the vault project page declares its repo.** `overview.md` frontmatter gains `repo:`, an absolute path to
   the local clone; recorded in the vault's operating manual and in `template/vault-pm/`.
2. **R2 — the three repo-touching skills resolve their target from the vault**, run from the vault project dir,
   re-root their paths against **two** roots, correct `mf-line`'s stage annotations, and derive the change id from
   the version instead of scanning.
3. **R3 — the line's artifacts live at `planning/vX.Y/`** — all six `SKILL.md` files, the three shared rubrics,
   and the worked example with its inbound links.
4. **R5 — the repo's own docs describe the corrected line**, including two stale strings in files this change
   already opens.
5. **R4 — the corrected line proves itself** by rendering v0.8's change directory, recorded under `proving/`.

## Approach

Prose across twelve files, one directory move, roughly forty edited lines. No code, no tests, no spec delta; the
architecture is untouched because these are instruction files consumed by an LLM — the "resolution" being changed
is a sentence, not a function.

Two consequences follow from the **working directory** moving rather than from anything being rewritten. The
harness loads the vault's root `CLAUDE.md` instead of the repo's, which incidentally makes a target repo's
`CLAUDE.md` *data the skill reads* rather than *instructions the harness obeys*. And every relative path in the
retargeted skills must be re-rooted — to one of **two** roots, not one (see `design.md` §1).

## Out of scope

- **`mf-teardown`.** The one skill left reading `.env`. Its fix is written down rather than done — swap the
  preflight for `repo:` (six conditions → five) and settle how a target with no vault page behaves — and is
  **owned by v0.11's retarget**. It keeps working through this version because the key is still present; v0.8
  empties it and records the break.
- **The repo-side decoupling** — the five code reaches, the preflight deletion, the findings home, the rubric
  criteria. All of it is v0.8. This change touches no `orchestrator/` code.
- **A committed guard on the `prd/` string.** The convention scan does not cover `skills/`; widening it belongs to
  v0.8, which is already rewriting that test.
- **Reworking any rubric's criteria, or `mf-order`'s interview.** This is a path-and-resolution change.

## Success criteria

- `grep -rn 'prd/' skills/ template/` returns nothing.
- `grep -rln 'VAULT_PROJECT_DIR\|\.env' skills/mf-blueprint skills/mf-forge skills/mf-inspect` returns nothing.
- `mf-line`'s stage list annotates no stage `cwd = repo`.
- The corrected line, run from the vault, renders `openspec/changes/0008-decoupling/` into the repo resolved from
  `repo:` — proved by doing it, recorded under `proving/`.
- Gate green at **163 tests, unchanged**. A doc-only version that moves the count has touched something it should
  not have.
