---
version: v0.7
---

# Proposal — 0007-pm-side-process-standard

**Change:** `0007-pm-side-process-standard` · **Version:** v0.7 · **PRD:** vault `planning/v0.7/v0.7_pm_side_process_standard.md`
**Class:** `migration` — three stages, one version, one tag. **Build mode:** hand-authored (Claude Code + human;
**no orchestrator automation**). **Renamed** from `0007-pm-finds-repo` when the version absorbed two further
stages; the five stage-A commits' trailers are rewritten to match, so one id traces the whole version.

## Why

**The vault and the repo reach into each other, and the standard allows only one direction:** the vault reaches
the repo; the repo never reaches the vault. Neither side obeyed it.

The repo reaches the vault in **five** places, all shipped code — findings at `<vault>/findings/`
(`orchestrator/findings.py:12`), the vault resolved from `.env` with its write-grant asserted pre-spawn
(`orchestrator/state.py:81,129`), the coder's HALT report (`orchestrator/driver.py:82`), the release gate's
no-tech-debt predicate reading the vault backlog (`orchestrator/__main__.py:234`), and the release stage
prepending to a vault release log (`orchestrator/release.py:350`). Around them sit a `.env` key, a tracked
`.env.example` mirroring it, a settings grant over the vault, an Inputs block handing every role two vault paths,
six role prompts writing vault files, and a root `CLAUDE.md` documenting the arrangement as load-bearing.

The PM side reached back the wrong way round: four `mf-*` skills ran with **cwd = the target repo** and resolved
the vault out of *that repo's* `.env` — the planning line asking the repo where it lived — and all six resolved
their artifacts under a `prd/` directory the vault had already restructured, so **the line could not read the PRD
describing its own repair.** Stage A fixed that first, by necessity.

**Why it matters now.** The claim this repo makes is that it is self-contained: installable, handable to any agent
on any machine, with no vault concept. That claim is false while five code paths, six wiring artifacts and four
skills name a private Obsidian folder — and the next version's execution line targets repos that have no vault at
all. Meanwhile findings have **two live homes**, the drift the previous version spent itself deleting, and the
compliance rubric *certifies the coupling as compliant*: three group-A criteria, one of them `blocking`, require
the vault grant, so a correctly decoupled repo measures **non-compliant** against its own standard.

It also closes a backlogged containment hole by deletion: `read_vault_dir` reads an arbitrary absolute path out of
an untrusted target's `.env` and hands it to code that writes there. The reader is removed rather than guarded.

## What (scope)

**Stage A — the PM side finds the repo** *(phases 1–5; 1–4 committed)*

1. **A1** — the vault project page declares its repo (`repo:`), documented in the vault schema and the worked example.
2. **A2** — `mf-blueprint`, `mf-forge`, `mf-inspect` run from the vault and resolve the repo from `repo:`; every
   relative path re-rooted to one of two roots; the change id derived from the version, never scanned for.
3. **A3** — the line's artifacts live at `planning/vX.Y/` across six skills, three rubrics and the worked example.
4. **A4** — the corrected line proves itself by rendering **this** change; the change dir is renamed to
   `0007-pm-side-process-standard` and the five stage-A trailers rewritten to match.
5. **A5** — the repo's docs describe the corrected line.

**Stage B — the repo stops reaching the vault** *(phases 6–14)*

6. **B1** — findings resolve at `.minions/findings/<change-id>_<role>.md`, one resolution site, directory created
   before the first spawn.
7. **B2** — the coder's HALT report resolves at `.minions/HALT.md`.
8. **B3** — deferred work goes to `.minions/<version>_backlog.md`; **any list line blocks the release**, checkbox
   state irrelevant, reversing today's fail-closed-on-absence behaviour deliberately.
9. **B4** — the vault release-record is deprecated: `_release_log_entry` and `_prepend_release_log` deleted,
   `prepare_release` drops its `vault_dir` argument.
10. **B5** — every role's Inputs block is repo-only; `build_inputs_block` drops `vault_dir` and the `Context:` line.
11. **B6** — the vault preflight is **deleted, not guarded**: `read_vault_dir`, `verify_vault_access`, the
    `change-state` requirement and its eleven scenarios, with their tests. `.env` / `.env.example` keep their shape
    as empty scaffolding.
12. **B7** — `.claude/settings.local.json` grants no vault (untracked; an operator edit this change documents).
13. **B8** — no shipped code, prompt or doc names the retired vault vocabulary. Six needles
    (`VAULT_PROJECT_DIR`, `vault_dir`, `vault_project_dir`, `read_vault_dir`, `verify_vault_access`,
    `release_log`), each needle set with its **own root set**. The scan that asserts it lands in stage C.
14. **B9** — all six role prompts stop writing the vault, and their deferral targets name the new backlog path.
15. **B10** — root `CLAUDE.md` declares the **findings contract**: path, frontmatter shape, both severity
    vocabularies, the `open → fixed → verified` machine with its producer/checker asymmetry, and the append-only
    resolution log.
16. **B11** — `skills/rubrics/compliance.md` sheds the dead criteria; group A **6 → 3**, both `criteria_total`
    baselines drop (`23 → 20`, `16 → 13`); every stale forward reference repointed.
17. **B12** — nine docs describe a self-contained repo.

**Stage C — the audit rejoins the standard** *(phases 15–18)*

18. **C1** — `mf-teardown`'s report moves to `.minions/findings/teardown.md`, and every document advertising the
    old guarantee is rewritten.
19. **C2** — its preflight resolves the target from the vault's `repo:`; six `.env` conditions become four on
    `repo:`; a target with no vault project page halts; the paragraphs reasoning from *cwd is the target* are
    corrected.
20. **C5** — the skill's prose stops naming criteria B11 deletes, and the last needle goes with it.
21. **C3** — the retired-vault scan lands over its full root set, with **no carve-out ever declared**.
22. **C4** — the rubric is re-measured: `mf-teardown` against this repo reports **`compliant`**.

## Approach

The shape of the change is **subtraction**. `vault_dir: Path` is a parameter threaded from the entry point into
five modules, and every call site that has it already has `repo`. Replacing one root with another already in scope
removes arguments rather than adding indirection: `findings_path`, `halt_report_exists`, `build_inputs_block` and
`prepare_release` each lose one. No new module, no new component, no new dependency.

The scan pattern B8 needs is one `tests/test_conventions.py` already ships and argues for: `_SCANNED` at `:37` and
`_VAULT_SCANNED` at `:54`, with a comment explaining that a second needle gets its own roots because the first's
exclusions were argued for a different needle. B8 adds a third set in an established pattern.

**Stage ordering is forced.** A before B (B empties the key A's skills stop needing); B before C (C's scan asserts
the absence B's deletions create, and C1/C2/C5 clear the last file that would fail it). The scan is therefore the
**penultimate phase of the version**, not the closing phase of stage B — `skills/mf-teardown/` holds twelve
`VAULT_PROJECT_DIR` lines until phase 16, so a stage-B scan could not go green, and a temporary carve-out was
declined as a suppression the version would have to remember to remove.

**Only the merge to `main` is deferred.** Between stage B and stage C the audit skill halts at preflight on every
target — a state that must never be published, and the reason these are one version and not three.

## Out of scope

- **`mf-backlog-export` (v0.8).** B3 pre-settles its open question by naming the file; v0.8 ships the export half.
- **The execution line, `mf-execute` (v0.9).** B10's findings contract is what it consumes.
- **A new group-A criterion for the findings contract.** B10 makes it load-bearing; measuring it waits for the
  version that re-measures the groups.
- **Three deferred `low` security findings** carried from the previous version; they ride with v0.10.
- **The vault's own restructuring.** The vault release record is deprecated as a *destination*; the file is not
  deleted and the vault's narrative record keeps its shape.
- **Reviving the parked runner.** Its code is retargeted so there is one findings home, not because it resumes.

## Success criteria

1. No symbol in `orchestrator/` resolves, reads or writes a path outside the repo.
2. Every findings file, the HALT report and the deferred-work backlog resolve under `.minions/`.
3. All four vault-side `mf-*` skills resolve their target repo from the vault's `repo:`, and read no `.env`.
4. `.claude/settings.local.json` grants no vault directory.
5. The compliance rubric's group A counts **3** criteria; both `criteria_total` baselines drop by three.
6. `mf-teardown` runs against this repo, decoupled, and reports **`compliant`** — the migration's end-to-end proof.
7. The gate is green at every phase; the test count falls from **163** to roughly **147** as the eleven preflight
   scenarios and the vault-path scan take their tests with them.
