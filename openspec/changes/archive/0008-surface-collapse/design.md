---
version: v0.8
---

# Design — 0008-surface-collapse

Technical decisions for v0.8. The *what* and *why* are in `proposal.md`; the intent record is the vault's
`planning/v0.8/v0.8_grilling.md`, which this design implements and does not restate.

## 1 — What `docs/sdd.md` is, and what it is not

**It is a method document, not a developer doc about this codebase.** `docs/` is otherwise the orchestrator's own
map — `architecture.md` plus one page per module. `docs/README.md` gains one line declaring `sdd.md` the single
page that is *about the method rather than about this repository*, so the map stays honest.

**It is written above the tool layer.** It names stations and the disk artifacts they produce; *who* runs a
station — a human pasting a prompt, a skill, an orchestrator — is left unfixed. Three reasons: none of v0.9's or
v0.10's tooling exists yet, so any tool-level claim ships false; those versions' skills must *reference* this page
rather than restate it, which is only possible if it sits above them; and status that changes every version
belongs in `README.md` and `CHANGELOG.md`.

**It assumes no orchestrator.** `skills/rubrics/compliance.md:55` frames its first criteria group as *"Loop
wiring — can the orchestrator start at all?"*. The readiness checklist re-frames that as *can the loop be run
here*: a **declared** gate command list, a change directory, a spec tree. Most criteria survive re-worded, because
a skill needs the same facts a driver does. What drops is the part assuming an installed package is pointed at
you.

**It is self-sufficient.** The travelling footprint is `openspec/specs/` + `openspec/changes/` +
`.minions/minions.toml` + a repo `CLAUDE.md`. That is empirical, not aspirational: isekai runs the standard with
exactly that and no `prompts/`, no `docs/`. Role prompts are **not** part of the kit — v0.10 turns them into
skills installed globally, and per-repo copies would make a fifth copy of the findings contract.

**It names the intent record abstractly.** *Grilling produces a written record of what was settled; the change is
cut from it and checked against it.* No path, no vault. Naming a location outside the repository would break the
invariant v0.7 spent seventeen phases establishing.

### Outline

*Part I — the method:* what this is and the three practices · the unit of work (`openspec/specs/` +
`changes/<id>/`: proposal · design · tasks · delta) · traceability (the `Change:` trailer, scenario keys bound to
proving tests, `change vX.Y = CHANGELOG = tag`) · the gate (declared on disk, **run, never summarized**) · the
loop (grill → cut → build → review ‖ security ‖ simplify → converge → release; builder interactive, checkers
blind) · the findings contract · the release fold.
*Part II — adoption:* what must be settled before a change is cut · the readiness checklist, with `python-uv` as a
worked toolchain profile.

Target **220–260 lines**. The four rubrics total ~350 lines of surviving content — `compliance.md:266-586` is the
teardown report contract, which dies with the runner and is distilled into nothing.

## 2 — The split with `CLAUDE.md`, and why the line falls where it does

| moves to `docs/sdd.md` | stays in `CLAUDE.md` |
|---|---|
| *Where the work is defined* — the change contract, the `Change:` trailer | this repo's six actual gate commands |
| *The findings contract* — path, frontmatter, the two severity vocabularies, the producer/checker asymmetry, the append-only resolution log | the seams: `Provider` Protocol, `run_gate`, the deterministic driver |
| the CHANGELOG/version-line rule (`change vX.Y = CHANGELOG = pyproject = tag`) | the no-LLM-in-orchestration invariant |
| the release fold | the secrets/deps guardrails, the layout facts |
| "the gate is run, never summarized" | |

**The constraint that fixes this line:** all six role prompts open with *"read the repo's `CLAUDE.md` as shared
context"*, and `prompts/coder.md:29` enumerates its contents as **"the quality gate, the engineering
conventions/seams, the guardrails."** All three stay, so that sentence remains true and **no role prompt is
edited**. A more aggressive split would put six more files in scope for no gain.

**Moving the findings contract costs nothing operationally.** It is already restated in full inside
`prompts/reviewer.md:73-116`, `prompts/security.md:48-102` and `prompts/simplify.md:44-113`, and enforced by
`orchestrator/findings.py`. `CLAUDE.md`'s copy is the fourth, and the one no role reads.

`CLAUDE.md` gains a pointer to `docs/sdd.md` in place of what it gives up.

## 3 — The guard changes

### 3.1 The root sets merge

`tests/test_conventions.py` carries two needle sets, each with its own root set:

- `_RETIRED` (eight retired *plan* symbols) over `_SCANNED` = `orchestrator`, `prompts`, `docs`, `README.md`.
- `_RETIRED_VAULT` (six retired *vault-reach* symbols) over `_SCANNED_VAULT` = those four plus `skills`,
  `CLAUDE.md`, `.env.example`.

The spec states why they are separate: *"one root set crossed with both needle sets cannot pass, because a retired
plan needle is live check text inside `skills/`"* — namely `skills/rubrics/compliance.md:68,564`. **That file is
deleted here**, so the reason evaporates. Measured before the edit: all eight plan needles return **zero hits**
across the post-deletion root set. The two needle sets therefore share **one** root set.

The needle sets stay **distinct**. They record different retirements with different histories — the retired plan
model (v0.5) and the retired vault reach (v0.7) — and collapsing them would lose which regression a future failure
is.

### 3.2 The root set widens

`tests/test_conventions.py:126-128` names `template/`, `.github/`, `Makefile` and `pyproject.toml` as deliberately
outside the scan, and records the widening as v0.8's. `template/` is deleted by this change; the other three are
added. Measured: all fourteen needles return **zero hits** across them, so this closes a future-regression gap
rather than a live hole.

**The resulting single root set:** `orchestrator`, `prompts`, `docs`, `README.md`, `CLAUDE.md`, `.env.example`,
`.github`, `Makefile`, `pyproject.toml`. `docs/sdd.md` falls inside it, so the new page is scanned from the moment
it exists.

### 3.3 The spec delta

One `MODIFIED` requirement — *Repository is the source of truth for change progress* — carrying both affected
scenarios: `sdd:vault-layout:no-plan-path-references` and `sdd:vault-layout:no-retired-vault-vocabulary`. The
latter loses its *"the root set is the needle set's own, not the retired-plan needle's"* clause along with the
justification this change deletes. `sdd:vault-layout:progress-in-repo` is untouched and is restated in the
MODIFIED block unchanged, as the fold requires.

Nothing is `ADDED` and nothing is `REMOVED`: no scenario key changes, so the one-commit spec-removal window that
bit v0.7 three times does not apply here.

### 3.4 The one new test

`docs/sdd.md` exists and `docs/README.md` links it. Structural only — nothing about contents.

It carries `@pytest.mark.spec_exempt("structural — the method doc is wired into the docs map")` rather than a
scenario. A file existing and being linked is not a system behaviour, and an ADDED scenario here would be one
nobody could meaningfully re-verify; the exemption matches the existing idiom (`tests/test_main.py:127` *"wiring"*,
`tests/test_specs.py:70` *"mechanism/plumbing"*). A **content** guard — needles policing what `CLAUDE.md` may say
— is deliberately not written: that is how `compliance.md` reached 586 lines.

## 4 — Build order, and why deletions commit with their guards

**Binding rule: no commit ships a scan that lies.**

The merge in §3.1 is only green once `skills/` is gone, so it cannot precede the deletion. If it *follows* the
deletion as its own phase, the deletion's commit ships a guard silently scanning one root fewer — green, and
narrower than the tuple it asserts. So each deletion lands **in the same commit** as the guard edit it forces:
phase 4 pairs the `skills/` deletion with the merge and the spec delta; phase 5 pairs the `template/` deletion
with the widening.

v0.7 could land its scan last because the guard did not exist yet and nothing could lie. That is not the case
here.

**`make uninstall-skills` runs before the deletion** in phase 4 — eight `~/.claude/skills/` symlinks point into
`skills/`, and deleting the directory first strands them on the operator's machine.

**`docs/sdd.md` is written first** (phases 1–2), before anything is deleted, so the four rubrics can be harvested
from the tree rather than from memory. `CLAUDE.md` shrinks in phase 3, once the page it defers to exists.

## 5 — What this change does not touch

`orchestrator/` and its 162 tests; the six role prompts; `.minions/minions.toml`; `.github/` (which names none of
the deleted surface); `.claude/settings.local.json`, whose stale `compliance.md` permission entries are globally
gitignored — dead local config, not a tracked lie. No `proving/` directory: v0.6 and v0.7 carried them to hold
measurement evidence, and this change measures nothing.
