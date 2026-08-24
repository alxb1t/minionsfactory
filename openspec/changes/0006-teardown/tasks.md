# Tasks — 0006-teardown

Ordered phases for v0.6. **Build mode: by hand** (Claude Code + human; no orchestrator automation — a loop-built
prose change has no tests to bind, so its gate would be vacuously green; self-hosting starts at v0.9). **Doc-only
change** — ships prose (a rubric, a skill, two reconciled vault notes, README lines). Read `proposal.md` +
`design.md` (this dir) and the vault PRD (`prd/v0.6_teardown.md`, R1–R12) first.

**Per-phase ritual (every phase).**
- Author the phase's deliverable → confirm the **repo gate stays green** (markdown-only, so
  `uv run ruff format --check .` · `uv run ruff check .` · `uv run ty check` · `uv run pytest -q` ·
  `uv run python -m orchestrator specs check --strict` are unaffected) → confirm the deliverable exists as the PRD
  specifies.
- **Commit** in the code repo with a `Change: 0006-teardown` trailer, **contiguous** with `Co-Authored-By:` (no
  blank line between — git parses the trailer block as the last paragraph). Vault edits (`log.md`, `backlog.md`,
  `overview.md`) are separate from the code commit.
- Append the phase's changes under `## [Unreleased]` in `CHANGELOG.md`.
- Tick the phase's box in `## Progress` below, then continue to the next phase.

**Finish each phase completely before starting the next** — deliverable → gate → commit → CHANGELOG → vault
bookkeeping. Never interleave phases, and never tick a box whose acceptance is not met. The run continues
phase-to-phase without pausing **unless a halt condition fires** (below), in which case stop and report rather
than guessing.

**Halt and ask the human** when: the work would need a new dependency, code in `orchestrator/`, or anything the
PRD's Constraints forbid · a PRD requirement turns out to be self-contradictory or unsatisfiable · a change to
**MF's own gate array** is required (it is declared in four places and policed by two criteria — see phase 6 C1/C4)
· a proving-run disagreement resolves to none of R11's three causes · the gate goes red for a reason the phase's
own scope cannot fix · the fix would mean editing the PRD.

**Spec delta is N-A** — see `specs/README.md`. No scenarios to bind, nothing to fold at release.

**This change must satisfy its own criteria.** `sdd:active-change-contract` currently passes vacuously because MF
has no active change; creating this directory makes it live. Keep all four artifacts present, this `## Progress`
checklist intact, and `version: v0.6` in `proposal.md` frontmatter — phase 6 measures the repo these phases changed
(`design.md` §9, C3).

## Progress

- [x] 1 — Rubric skeleton + Tier 1 groups A–B (loop wiring, SDD layout)
- [x] 2 — Tier 1 group C + Tier 2 `python-uv` profile + the D–G forward note
- [x] 3 — Source reconciliation (`bootstrap_steps.md`, `generic_root_claude.md`)
- [x] 4 — The report contract (frontmatter, verdict rule, gap shape, merge + status machine)
- [x] 5 — The `mf-teardown` skill
- [ ] 6 — Proving runs + contract exercises + ship

---

## Phase 1 — Rubric skeleton + Tier 1 groups A–B

Create `skills/rubrics/compliance.md`: the file, its verdict convention, and the per-criterion convention — a
**stable id**, an **(M)/(J) tag**, a **severity** (`blocking` · `required` · `advisory`), a **what-is-checked** line
naming the exact path or key, and a **fix pointer**. Add the row to `skills/rubrics/README.md`'s *Which skill uses
which rubric* table, naming `mf-retrofit` (v0.7) and `mf-stamp` (v0.8) as forthcoming producers and `mf-teardown` as
the checker (`design.md` §1).

**Also extend that README's *Verdict + severity conventions* section**, which otherwise describes 3 of the 4
rubrics it indexes: compliance emits `compliant | gaps-found` over **three** severities (`blocking` · `required` ·
`advisory`), not the `clean | changes-requested` + `blocking | nit` the other three share. Same staleness class as
the `README.md:88` three→four rubric count phase 6 fixes.

Then Tier 1 **group A · Loop wiring** (`wiring:git-repo`, `wiring:gate-config`, `wiring:vault-perms`,
`wiring:claude-md`, `wiring:env-example`, `wiring:gitignore`) and **group B · SDD layout** (`sdd:specs-tree`,
`sdd:changes-tree`, `sdd:active-change-contract`, `sdd:scenario-shape`, `sdd:test-binding`, `sdd:checker-in-gate`),
with the tags and severities the PRD's tables state. `sdd:checker-in-gate` ships **`advisory` with its reason
stated inline** — no `[build-system]`, so no target can install the orchestrator (`design.md` §6).

**Acceptance:** the rubric file exists; the rubrics README lists it with its producer/checker **and its verdict +
severity conventions**; every group A and B criterion named above is present, carrying the tag, severity and
fields the convention above requires, none empty, each matching what the PRD's tables state; ids unique; no
severity unset; `sdd:checker-in-gate` ships `advisory` with its reason stated inline; repo gate green.

## Phase 2 — Tier 1 group C + Tier 2 profile + the D–G forward note

**Group C · Gate quality** (`gate:covers-axes`, `gate:contract-agrees`, `gate:make-mirrors`, `gate:no-gaming`) —
note `gate:no-gaming`'s example must stay **tool-neutral** (Tier 1 names no Python tool, R3).

**Decide `gate:contract-agrees`' (M) boundary here, and write the decision into the criterion.** It requires the
gate written in `CLAUDE.md` / `README.md` to match the array *command-for-command*, but a declaration may be
**prose rather than a command list** — MF's own `CLAUDE.md:56–65` states axes in prose ("`pytest` — all tests
pass"; "`ruff format --check` + `ruff check`") while `README.md:66–69` is a literal `bash` block. State which
satisfies the criterion: a prose axis list counts, or the criterion measures only literal command blocks and a
prose section is out of its scope. Left silent, this is a judgment call handed to execution — and it decides
whether MF has one failing declaration or two (`design.md` §9 C4).

**Tier 2 — `python-uv`** (`py:manifest`, `py:lockfile`, `py:gate-commands`, `py:pinned-runtime`, `py:lint-select`,
`py:dev-deps-isolated`, `py:import-resolution`), its **detection rule** — `pyproject.toml` **plus** a uv signal
(`uv.lock` tracked, or a `[tool.uv]` table) — and the written **extension rule** for a future profile: a new Tier-2
section with its own detection rule, no change to Tier 1 and no change to the skill (`design.md` §3).

Then the **"planned — v0.8" forward note** for groups D–G, in **its own section after Tier 2**: group name, one
line each on what it would measure, and an explicit statement that no id in them is live — no ids, no severities,
no measurement. State plainly that a repo failing every D–G criterion is still `compliant` at v0.6
(`design.md` §2).

**Acceptance:** the rubric's live criteria are exactly those the PRD's A–C and profile tables enumerate, and no
other criterion id anywhere in the file is live; every criterion added here satisfies the same field convention
phase 1 gated, with the tag and severity the PRD states, ids unique file-wide and no severity unset (R1);
`gate:contract-agrees` states its prose-vs-command-block boundary; nothing in the profile tier restates a
universal criterion and no Python tool name appears in the Tier-1 tables (R3); the extension rule is written
down; the D–G list is present, explicitly marked not-measured, and assigns no severity; repo gate green.

## Phase 3 — Source reconciliation

R10's acceptance is absolute — **neither note may contain the string `implementation_plans`** — so work from the
occurrence list, not from the section headings. There are **five**, and two sit outside the sections an earlier
draft of this phase named:

| Site | What it is | Work |
|---|---|---|
| `bootstrap_steps.md:17` | inside the `[!warning]` block: "the vault `implementation_plans/` model this recipe was written against is **retired**" | remove with the banner (below) |
| `bootstrap_steps.md:28` | **a link into another project's vault** — `../../../Projects/LePalace/KitchenScheduler/implementation_plans/v0.1_engine_core_implementation_plan.md` | **re-point or drop the example.** Outside every section named below; the easiest occurrence to miss and it alone fails acceptance |
| `generic_root_claude.md:45` | inside its `[!warning]` block | remove with the banner |
| `generic_root_claude.md:51` | step 2 — "read the **latest implementation plan** in `$VAULT_PROJECT_DIR/implementation_plans/`" | rewrite onto `openspec/changes/<id>/` |
| `generic_root_claude.md:59` | **a separate paragraph** on where plans and research files live — *not* part of steps 2–3 | rewrite onto the in-tree contract |

**`notes/bootstrap_steps.md`** — add the missing **SDD section** (the plan-side steps were *removed rather than
rewritten* pending v0.5, which has shipped) and rewrite *Handoff* step 2 off the deleted vault-plan reader.

**`notes/generic_root_claude.md`** — rewrite steps 2–3 from `$VAULT_PROJECT_DIR/implementation_plans/` onto the
in-tree `openspec/changes/<id>/` contract, instructing a cold agent to read the active change's `tasks.md`
`## Progress` checklist. Then the `:59` paragraph, which the steps rewrite does not reach.

**The banners to remove are the `[!warning]` blocks at `bootstrap_steps.md:16` and `generic_root_claude.md:44`.**
(`bootstrap_steps.md:35` and `:249` are inline ⚠️ pointers *to* the banner, not the banner — they go too, but
clearing them alone leaves the acceptance clause unmet.)

Then verify rubric ↔ notes agree — where they disagree, **the rubric wins and the note is corrected**.

**Acceptance:** neither note contains the string `implementation_plans`; neither carries a "pending v0.5" banner;
`generic_root_claude` points a cold agent at the active change's `## Progress` checklist; no rubric criterion
contradicts either note; this closes the backlog item blocking `mf-stamp`; repo gate green.

## Phase 4 — The report contract

Document in the rubric: `<vault>/findings/teardown.md` frontmatter (`type` · `repo` · `head` · `profile` · `round` ·
`criteria_total` · `open_gaps` · `open_blocking` · `open_required` · `verdict`), the **verdict rule** (`compliant`
iff `open_blocking: 0` **and** `open_required: 0`; advisories listed and counted but never withholding it, with the
`sdd:checker-in-gate` reason stated), the gap-entry shape (criterion id · severity · status · evidence naming the
path checked and what was found · fix pointer), **severity ordering** (`blocking` → `required` → `advisory`, with
`verified` sorting below `open` within each), the **cross-round merge + status machine** (still failing → `open`, a
`fixed` gap that still fails returns to `open` with a rejected-fix note; no longer failing → `verified`; newly
failing → `open`; `verified` entries persist until the report goes `compliant`, then clear), and the append-only
`## Resolution log`. Record that **`fixed` is the producer's word** — teardown never writes it (`design.md` §4).

Document the **absent-subject rule** (`design.md` §5), so one defect is reported once and two runs are comparable:
existence criteria **fail**; universally-quantified criteria **vacuously pass** over an empty set (their emptiness
is already reported by the existence criterion); and criteria **whose subject is the unreadable gate array
itself** — `gate:covers-axes`, `gate:contract-agrees` and `sdd:checker-in-gate` — are **not measured**, each
naming the gap that gates them and excluded from both counts. Write down the two exclusions too:
**`gate:make-mirrors` fails outright when a `Makefile` gate target is absent** (isekai's case, which R11 requires
reported) and **`gate:no-gaming` is never gated**, its subject being tool config. The rule must name **every**
gate-array-subject criterion — an omission means a gap reported against a merely mis-located config that
evaporates the moment the file moves.

**Acceptance:** every frontmatter field listed above is defined, `criteria_total` by the formula in `design.md` §5
with its subtraction shown; the absent-subject rule is stated with each case and each exclusion named above; the verdict
rule is stated with its rationale; the severities are defined and ordered; the merge rules and the
`open → fixed → verified` machine are written down; the producer/checker status asymmetry is stated.

Three checks that are **not** restatements — they gate consequences of the above:
- **no criterion both fails and is counted not-measured** — the two categories are disjoint;
- **`gate:make-mirrors` is reportable as a gap on a repo with no `Makefile`**, whatever its gate config (the
  isekai case R11 requires reported);
- **every gate-array-subject criterion appears in the rule's covered set** — none left silent.

Repo gate green.

## Phase 5 — The `mf-teardown` skill

`skills/mf-teardown/SKILL.md` — cwd = the target repo. **Preflight** (R7): resolve `.env` → `VAULT_PROJECT_DIR`,
**mirroring the five conditions `read_vault_dir` (`orchestrator/state.py:81–126`) already enforces** — `.env`
unreadable · not valid UTF-8 · key missing or empty · value **not absolute** · value not an existing directory.
Each **halts with its own diagnostic**, before any subagent is spawned, writing nothing; the diagnostic tells the
human the one line to add to `.env`.

**The absolute-path condition is the security-relevant one** (`design.md` §7): a relative value such as
`VAULT_PROJECT_DIR=docs` resolves to a directory **inside the target repo**, and the outer step would write the
report there — breaking R6 and the never-write-to-the-repo constraint. Teardown must not accept an input the loop
rejects.

**The resolver strips surrounding double quotes and preserves spaces** — exactly `orchestrator/state.py:108`
(`raw.strip().strip('"')`), double only; stripping single quotes too would accept a value the loop rejects. Real
targets write the value double-quoted over a path containing spaces — `isekai/.env:6`, and MF's own `.env` — so a
naive read halts a correctly-wired repo with a false *"path does not resolve"*. Get this right here; it is the
exact bug phase 6's isekai run would otherwise hit.

Then **profile detection in the outer step, before the spawn** (R4, `design.md` §3): `pyproject.toml` **plus** a uv
signal → `python-uv`; no match → `profile: none` and the explicit not-assessed statement. Detection is a mechanical
file check and belongs to the deterministic half — R4 forbids *guessing* a profile, and a deterministic step naming
the profile to the judgment step is what makes that structural. The `profile:` frontmatter field is written by the
outer step, which owns the report.

Then the **fresh measuring subagent** given only the repo path, the rubric and **the detected profile name**,
**blind to the existing report**, returning failing criterion ids with evidence and **no status field, no
verdict**; the **outer step** that reads the prior report, increments `round`, merges per phase 4, and writes.
Instruct the subagent to work **group by group** (A → B → C, then the profile) rather than recalling 23 criteria
from one pass (`design.md` §11).

**The full sequence:** preflight → detect profile → spawn subagent → merge → write.

**Read-only must be stated in the skill's own instructions** (`design.md` §7): no writes in the target, no gate
command executed, no target code run — files and git metadata only.

**Acceptance:** the skill exists and is picked up by the `skills/mf-*` install glob (no Makefile edit needed); the
measurement runs in a fresh subagent receiving only the inputs listed above, and **not** the previous report; its
output names failing criteria only, with no status field and no verdict; profile detection runs in the outer step
before the spawn and the `profile:` field is written there; **each** preflight condition listed above halts with
its own diagnostic and no subagent spawned; the skill's instructions forbid running the target's tooling.

Two behavioural checks that are **not** restatements — run them against a real `.env`:
- **a relative `VAULT_PROJECT_DIR` is refused** even when it names an existing directory inside the target;
- **a double-quoted value over a path containing spaces resolves and does *not* halt** (both proving targets are
  written this way, so a regression here false-halts a correctly-wired repo).

Repo gate green.

## Phase 6 — Proving runs + contract exercises + ship

**The two proving runs (R11).** Run against **minionsfactory** and **isekai**; commit both reports as evidence.
Every expectation/result disagreement is recorded with which of the three causes it was — the rubric is wrong, the
skill is wrong, or MF is genuinely out of compliance — and what changed. **Never** resolved by relaxing the
expectation.

Expected from the blueprint's hand-measurement, to be confirmed or corrected by the real run:
- **C1 — `py:gate-commands` (blocking) against MF.** No `uv sync --locked` step in `.minions/minions.toml`. R11
  forbids leaving a blocking gap open: **decide it** — correct the criterion (drop `uv sync` from the required form,
  or re-tag it `advisory`) or add the step to the array. Record the cause.
- **C2 — `py:pinned-runtime` (required) against MF.** No `.python-version`; closable by editing a tracked file →
  close it here, with a pin consistent with `requires-python`.
- **C4 — `gate:contract-agrees` (required) against MF.** `README.md:66–69` declares four commands where
  `.minions/minions.toml` holds five (missing `specs check --strict`; `uv run pytest` vs `pytest -q`). Closable by
  editing a tracked file → close it here. **Treat C1 and C4 as one edit:** the gate is declared in **four** places
  (`.minions/minions.toml`, `Makefile:7–12`, `README.md:66–69`, `CLAUDE.md:56–65`) and two criteria police their
  agreement, so adding `uv sync --locked` to the array alone would newly break `gate:make-mirrors`, which passes
  today. Whatever phase 2 decided about prose-form declarations governs how `CLAUDE.md` counts here.
- **isekai:** the root-`minions.toml` placement, the absent `openspec/` tree, the missing `Makefile` and
  `.python-version`. Its missing `CHANGELOG` and `docs/` must **not** be reported — v0.8 criteria, and reporting
  them is a false gap.

**Two contract exercises**, so no acceptance clause ships unfalsified: a **degradation run** on a directory with no
Python manifest (proves R4's `profile: none` path and the not-assessed statement), and a **re-run against a
hand-seeded report** carrying one `fixed` entry that still fails and one that now passes (proves R9's
`fixed → open` and `fixed → verified` transitions, which nothing writes until v0.7).

**Ship:** README — document teardown as a **per-repo sibling, not a line stage**, with a copy-paste invocation;
leave the `mf-` line's six-skill list intact and `mf-line` **unmodified** (R12). Also fix `README.md:88`, *"They
share **three** rubrics"* → **four**: this change ships `compliance.md`, and that line is the README's only rubric
count. Update the vault roadmap and backlog.

**Acceptance — the report contract proven against real reports (R8, R9):** in each committed report, every
frontmatter field is populated and `open_gaps` / `open_blocking` / `open_required` **agree with the body**; every
gap entry cites a criterion id that exists in the rubric and evidence naming a **real path**; entries are ordered
`blocking` → `required` → `advisory`; `verdict: compliant` iff `open_blocking: 0` and `open_required: 0`,
regardless of open advisories; a first run on a repo with no existing report writes **`round: 1` with every gap at
`open`**; and a second run **overwrites in place, leaves one file, and increments `round`**.

**Acceptance — read-only proven against a real repo (R6):** for at least one proving run, `git status` in the
target is **byte-identical** before and after and **no untracked file has appeared**; **no gate command** from the
target's `.minions/minions.toml` was executed; and a repo whose gate is red still produces a complete report.

**Acceptance — the runs:** both proving runs performed and their reports committed; both contract exercises
performed; every expectation/result disagreement recorded with which of the three causes it was; the isekai run
names the gaps listed above with correct evidence and reports **no** v0.8 criterion; **no false gap against MF**.

The MF run returns `verdict: compliant` — **or** every remaining `required` gap is demonstrably not closable by
editing a tracked file, backlogged by criterion id and named in the write-up. **No `blocking` gap against MF is
left open**, with no exception.

**Determinism:** a repeat run on an unchanged repo produces the same verdict and the same `blocking` + `required`
gap-id set across every (M) criterion. A (J) criterion that flips pass/fail is a **rubric defect** — sharpen it
until it decides the same way twice, or drop it to `advisory`, recorded as the "rubric is wrong" cause.

**Ship:** `mf-line` unchanged; README documents the sibling with a runnable invocation and its rubric count reads
four; repo gate green.
