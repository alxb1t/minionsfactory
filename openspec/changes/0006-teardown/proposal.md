---
version: v0.6
---

# Proposal — 0006-teardown

**Change:** `0006-teardown` · **Version:** v0.6 · **PRD:** vault `prd/v0.6_teardown.md` (R1–R12)
**Build mode:** hand-authored (Claude Code + human; **no orchestrator automation**). **Doc-only change** — ships
prose (a rubric, a skill, two reconciled notes, README lines), not test-backed Python, so its **spec delta is N-A**
(see `specs/README.md`, the `0004-planning-skills` precedent). Self-hosting still resumes at v0.9.

## Why

The framework has always claimed two entry points: **`mf-stamp`** for a new repo, and an audit for an **existing**
one — *"point it at an existing Python project and get a gap report."* The second has never been built. Onboarding
an existing repo today means a human reading four prose notes (`bootstrap_steps`, `generic_root_claude`,
`docs_standard`, `conventions`) and checking a repo against them by eye — no checklist, no severity, no record, and
no way to tell whether the same repo was measured the same way twice.

**Why now.** v0.5 shipped and **deleted** the vault-plan reader. Five live targets — isekai, KitchenScheduler,
Palimpsest, Apilogue, Tomten — **cannot run at all** until they carry an in-tree `openspec/changes/<id>/`. That is a
break, not a risk. And v0.9's remediation loop refuses at preflight any target with no gate config or vault wiring,
so an un-compliant repo cannot even reach the loop that would fix its code. isekai is the concrete case: measured
during planning, it keeps `minions.toml` at the repo **root** (the reader looks in `.minions/`, so its gate is
unreadable), has **no** `openspec/` tree at all, and ships no `Makefile` and no `.python-version`.

**What breaks without it.** The compliance standard exists only as prose scattered across four notes, two of which
are **knowingly stale** — both still describe the retired `implementation_plans/` model and carry ⚠️ banners
pending v0.5, which has now shipped. There is no single artifact that says what "compliant" means, so every
onboarding is a fresh act of judgment, gaps are found by tripping over them mid-run, and nothing downstream can
consume the result.

## What (scope)

A **compliance rubric** and its **read-only reader skill**, plus the reconciliation of the rubric's own stale
sources:

1. **`skills/rubrics/compliance.md` (R1)** — the **fourth shared rubric**, in the existing `skills/rubrics/` home,
   following the shape `skills/rubrics/README.md` establishes: an (M)/(J) tag on every criterion, a stated verdict
   convention, and a "which skill uses which rubric" row. Every criterion carries a **stable id**, a **severity**, a
   **what-is-checked** line naming the exact path or key, and a **fix pointer**.
2. **The criteria — 23, and no others (R2).** Tier 1 universal groups **A · Loop wiring** (6), **B · SDD layout**
   (6), **C · Gate quality** (4); Tier 2 profile **`python-uv`** (7). Groups **D–G** (product record, docs, vault
   side, CI) appear only as a **"planned — v0.8"** forward note in its own section after Tier 2: named, one line
   each, **no ids, no severities, no measurement**.
3. **Two tiers, so a second toolchain is a new file (R3).** Universal and toolchain criteria live in separately
   headed sections; nothing in Tier 1 names a Python tool, nothing in Tier 2 restates a universal criterion, and
   the rubric writes down how a future profile is added.
4. **Profile detection and honest degradation (R4).** Detected from `pyproject.toml` **plus a uv signal**
   (`uv.lock` tracked, or a `[tool.uv]` table), **in the outer step, before the measuring subagent is spawned**. No
   match — including a Python manifest with no uv signal — degrades to the universal tier with an explicit
   not-assessed statement. Never a guess, never an abort.
5. **`skills/mf-teardown/` (R5)** — a skill run with cwd = the target repo. The **outer step** detects the profile
   and owns the report; a **fresh measuring subagent**, given only the repo path, the rubric and the detected
   profile name and **blind to the existing report**, returns a pure current-state measurement — failing criterion
   ids with evidence, no status field, no verdict. Sequence: preflight → detect → spawn → merge → write.
6. **Read-only, enforced (R6).** Writes nothing in the target, runs **no** gate command, executes **no** target
   code. Files and git metadata only.
7. **Preflight halts on an unwired vault (R7)**, refusing exactly what the loop refuses — the **five** conditions
   `read_vault_dir` (`orchestrator/state.py:81–126`) already enforces and specs: `.env` unreadable · not valid
   UTF-8 · `VAULT_PROJECT_DIR` missing or empty · **value not absolute** · value not an existing directory. Each
   halts with its own diagnostic, before any subagent is spawned, writing nothing. The absolute check is
   security-relevant: a relative value resolves *inside the target repo*, where the report must never be written.
8. **The report — `<vault>/findings/teardown.md` (R8)** — the reserved id `teardown` in the v0.5 `findings/` home.
   Frontmatter `type` · `repo` · `head` · `profile` · `round` · `criteria_total` · `open_gaps` · `open_blocking` ·
   `open_required` · `verdict: compliant | gaps-found`. **Verdict rule:** `compliant` iff `open_blocking: 0` **and**
   `open_required: 0`; open `advisory` gaps are listed and counted but do not withhold the verdict.
9. **Severity ordering and the cross-round merge (R9).** Three severities — `blocking` · `required` · `advisory`.
   The **outer step** reads the prior report, increments `round`, and reconciles: still failing → stays `open` (a
   `fixed` gap that still fails returns to `open`); no longer failing → `verified`; newly failing → `open`.
   `fixed` is written by the **producer** (v0.7), never by teardown.
10. **The two stale sources are reconciled (R10).** `bootstrap_steps.md` gains its missing SDD section and a
    rewritten *Handoff* step 2; `generic_root_claude.md` steps 2–3 move from `implementation_plans/` onto the
    in-tree `openspec/changes/<id>/` contract.
11. **Proving runs on two real repos (R11)** — minionsfactory and isekai, with the closability rule for a genuine
    MF gap: closable by editing a tracked file → closed here; not closable → backlogged by criterion id.
12. **Tracked as this change (R12)** — four artifacts, `version: v0.6`, `Change: 0006-teardown` trailers, N-A spec
    delta. **`mf-line` is not modified:** teardown runs once per repo, not once per feature.

## Approach

- **The rubric is the deliverable; the skill is its reader.** v0.7 `mf-retrofit` and v0.8 `mf-stamp` are both
  *writers* against the same standard, which is why it lives in `skills/rubrics/` rather than inside the skill.
- **The measurement is blind; the merge is not — and they are different steps.** The subagent reports only what
  fails *now* and never sees the previous report; the outer step carries statuses forward. Handing the subagent the
  prior report would show the checker which gaps it was expected to find — exactly the anchoring the
  `mf-gauge` / `mf-inspect` discipline exists to prevent, and v0.7's producer→checker claim rests on it.
- **No orchestrator change.** `findings/teardown.md` is deliberately **not** loop-readable: every findings path in
  the orchestrator is built from an explicit role list (`orchestrator/findings.py:12`, `__main__.py:96`,
  `fanout.py:91`) and nothing globs `findings/`, so the file coexists with the role findings without being reachable
  by the converge loop or the release gate.
- **`skills/mf-teardown/` needs no install change** — `make install-skills` already globs `skills/mf-*`.

## Out of scope

- **Fixing anything** — teardown measures and reports; closing gaps is **v0.7 `mf-retrofit`**.
- **Emitting a versioned remediation plan** — split out at the interview; authoring PRDs is the `mf-order` line's job.
- **Measuring code quality** — no review, security or simplify pass; that is v0.9's remediation loop, a different
  subject with a different producer.
- **Measuring project shape — groups D–G.** Product record, docs, vault layout and CI are drafted but **not
  measured** here; they move to **v0.8 `mf-stamp`**, which writes those artifacts and so owns their criteria. A repo
  failing every D–G criterion is `compliant` at v0.6, and the rubric says so out loud.
- **Running the gate** — reporting whether a gate is genuinely green needs executing target tooling; v0.6 reports
  only that a gate is configured and well-formed. `--run-gate` is a later increment, decided against, not deferred.
- **A `js` (or any second) toolchain profile** — the rubric is structured to accept one; v0.6 ships `python-uv`.
- **Making the spec checker reachable from a target's gate** — MF ships no `[build-system]` and runs from source, so
  a target cannot install the orchestrator. Recorded `advisory` with its reason inline; backlogged.
- **Stamping a new repo** (`mf-stamp`, v0.8), **sequencing teardown into `mf-line`** (R12), and **migrating the five
  live targets** (v0.7's work — this change only names their gaps).

## Success criteria

- `skills/rubrics/compliance.md` exists with **exactly 23 live criteria** across groups A–C + the `python-uv`
  profile; every one carries a unique stable id, an (M)/(J) tag, a severity and a fix pointer, none empty; the
  D–G forward note carries no ids and no severities; `skills/rubrics/README.md` lists the rubric with its
  producer/checker.
- `skills/mf-teardown/` exists, is picked up by the `skills/mf-*` install glob, spawns a **fresh subagent given
  only the repo path, the rubric and the detected profile name — and not the previous report**, and that subagent
  returns a measurement with no status field and no verdict.
- **Profile detection runs in the outer step, before the spawn**, and the report's `profile:` field and
  not-assessed statement are written by that step — so no step in the skill has to guess a profile.
- A run writes `<vault>/findings/teardown.md` with every frontmatter field populated and `open_gaps` /
  `open_blocking` / `open_required` agreeing with the body; every gap entry cites a real criterion id and evidence
  naming a real path; a second run overwrites in place and leaves one file.
- After a run, `git status` in the target is byte-identical to before, no untracked file has appeared, and no gate
  command from `.minions/minions.toml` was executed.
- Each of the **five** preflight failures produces its own diagnostic and a halt, with no subagent spawned and no
  partial report left behind; a **relative** `VAULT_PROJECT_DIR` is refused even when it names an existing
  directory inside the target, and a **double-quoted value over a path containing spaces** resolves without
  halting.
- **Proving runs:** the minionsfactory run returns `verdict: compliant` — or every remaining `required` gap is
  demonstrably not closable by editing a tracked file, is backlogged by criterion id, and is named in the write-up;
  **no `blocking` gap against MF is left open.** The isekai run names the root-`minions.toml` placement, the absent
  `openspec/` tree and the missing `Makefile` / `.python-version`, and does **not** report its missing `CHANGELOG`
  or `docs/` (v0.8 criteria — reporting them would be a false gap).
- Neither `bootstrap_steps.md` nor `generic_root_claude.md` contains the string `implementation_plans` or a
  "pending v0.5" banner, and `generic_root_claude` instructs a cold agent to read the active change's `tasks.md`
  `## Progress` checklist.
- `mf-line` is unchanged; the README documents teardown as a per-repo sibling with a runnable invocation; the repo
  gate stays green throughout.
