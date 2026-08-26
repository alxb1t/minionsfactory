# Tasks — 0007-pm-side-process-standard

Ordered phases for v0.7, a declared **`migration`**: three stages, one version, one tag. **Build mode: by hand**
(Claude Code + human; no orchestrator automation). Read `proposal.md` + `design.md` (this dir) and the vault PRD
(`planning/v0.7/v0.7_pm_side_process_standard.md`) first.

**Per-phase ritual (every phase).**
- Author the phase's deliverable → confirm the **repo gate is green**
  (`uv sync --locked` · `uv run ruff format --check .` · `uv run ruff check .` · `uv run ty check` ·
  `uv run pytest -q` · `uv run python -m orchestrator specs check --strict`) → run the phase's own acceptance check.
- **Commit** in the code repo with a `Change: 0007-pm-side-process-standard` trailer, **contiguous** with
  `Co-Authored-By:` (no blank line between — git parses the trailer block as the last paragraph). Vault edits are
  separate from the code commit.
- Append the phase's changes under `## [Unreleased]` in `CHANGELOG.md`.
- Tick the phase's box in `## Progress` below, then continue.

**Finish each phase completely before starting the next.** Never interleave phases, and never tick a box whose
acceptance is not met.

**The test count is a signal, not a constant.** Stage A is doc-only and must hold **163 tests exactly** — a moving
count there means something outside scope was edited. Stage B's count **falls**: the eleven preflight scenarios and
the vault-path scan take their tests with them, landing near **147**. A count that moves in stage A, or moves the
wrong way in stage B, is a stop condition.

**Build-order rule (binding).** No phase may delete a symbol, or assert the absence of a needle, while a live
dependent still names it. This is why the retired-vault scan is phase **17** and not the close of stage B — see
`design.md` §5.

**Spec-removal rule (binding, and it bites three times).** Removing a scenario key — or *renaming* one, which is
a removal plus an addition — must land **in one commit** with the test change it implies. `collect_spec_keys`
discards a REMOVED key from both the shipped and the resolvable sets the moment the delta block exists: author the
block **earlier** and the still-live test markers dangle; author it **later**, after the tests go, and the shipped
scenarios orphan. The window is exactly one commit wide. It applies to **phase 7** (one renamed key), **phase 10**
(eleven) and **phase 14** (two), and each commit does the same four things: change the code, change the tests,
author the live `## REMOVED Requirements` block in this change's delta, and hand-delete the matching block from
`openspec/specs/`. A MODIFIED requirement that merely stops mentioning a key does **not** remove it — MODIFIED
lands at the release fold, not at check time.

**Only the merge to `main` is deferred.** After stage B the audit skill halts at preflight on every target; only
stage C restores it. That state must never reach `main`, which is why these are one version.

**Halt and ask the human** when: the work would need a new dependency or anything the PRD's Constraints forbid ·
a requirement turns out self-contradictory · the gate goes red for a reason the phase's own scope cannot fix ·
phase 5's proving run disagrees with what the PRD predicts · the fix would mean editing the PRD.

**Spec delta:** real, under `specs/` — six capabilities touched. Stage A and the prose phases bind no scenario;
stages B and C carry the removals and modifications listed in each phase.

## Progress

- [x] 1 — The vault declares its repo
- [x] 2 — The path axis: `prd/` retires across `skills/` and `template/`
- [x] 3 — The resolution axis: three skills run from the vault
- [x] 4 — Docs, and the `mf-teardown` gap recorded
- [x] 5 — Prove it: rename the change, then render this version
- [x] 6 — Findings and the HALT report re-root under `.minions/`
- [x] 7 — The deferred-work backlog re-roots, and its predicate reverses
- [ ] 8 — The vault release-log writer is deleted
- [ ] 9 — The Inputs block drops the vault
- [ ] 10 — The vault preflight is deleted, not guarded
- [ ] 11 — All six role prompts stop writing the vault
- [ ] 12 — Root `CLAUDE.md` declares the findings contract
- [ ] 13 — The rubric sheds three criteria; nine docs describe a self-contained repo
- [ ] 14 — The `sdd` spec stops requiring the vault
- [ ] 15 — The audit report moves into the repo it measures
- [ ] 16 — The audit preflight resolves from `repo:`, and the file empties
- [ ] 17 — The retired-vault scan lands, over its full root set
- [ ] 18 — Re-measure: `mf-teardown` against this repo reports `compliant`

---

## 1 — The vault declares its repo

**Requirement:** R1. **Deliverable:** the `repo:` convention exists and is documented in all three places.

- Vault `Lab/minionsfactory/overview.md` — frontmatter gains `repo:`, an absolute path to the local clone.
  Verify its `current_phase` narrates the post-renumber sequence (corrected during planning; confirm, don't assume).
- Vault `Lab/CLAUDE.md` — the autonomous-build variant's frontmatter bullet, which lists `current_phase:` plus the
  per-phase flags, gains `repo:` as a required field.
- `template/vault-pm/overview.md` *(tracked)* — carries a `repo:` line, so the worked example teaches the new
  convention rather than the retired one.

**Acceptance.** `repo:` present, absolute, naming a directory that contains a `.git`; the variant's field list
names it; the template carries it. Only the template file is committed — the other two are vault edits.

## 2 — The path axis: `prd/` retires across `skills/` and `template/`

**Requirement:** R3. **Deliverable:** nothing under `skills/` or `template/` names `prd/`.

- Six `SKILL.md` files — `mf-order:3,33,37` · `mf-gauge:41` · `mf-blueprint:3,17,37` · `mf-forge:16,17` ·
  `mf-inspect:16,41,54` · `mf-line:21,25`. **Includes the `description:` frontmatter** of `mf-order` and
  `mf-blueprint`, which name the output path.
- Three shared rubrics — `prd-readiness.md:3` · `feasibility.md:3` · `conformance.md:20`. They *define* the
  artifacts by path and are read **first** by the skills that consume them; fixing only the skills would ship a
  skill saying `planning/` and a rubric saying `prd/`.
- `git mv template/vault-pm/prd template/vault-pm/planning/v0.1`, then repoint its **five** inbound references:
  `template/vault-pm/README.md:14` · `overview.md:17` · `overview.md:26` · `log.md:9` · `roadmap.md:11`.
  *(`overview.md`'s two refs sat at 16 and 25 before phase 1 inserted `repo:` into its frontmatter — cited
  post-shift. The grep below is the real acceptance either way.)*

**Acceptance.** `grep -rn 'prd/' skills/ template/` returns nothing; all five inbound links resolve; the PRD lands
at `planning/vX.Y/vX.Y_<short-name>.md` and each of `_gauge` · `_design` · `_inspect` beside it.

## 3 — The resolution axis: three skills run from the vault

**Requirement:** R2. **Deliverable:** `mf-blueprint`, `mf-forge`, `mf-inspect` resolve their target from the
vault; `mf-line` agrees with them.

- **Setup rewritten** in all three: run **from the vault project dir**; resolve the target repo from
  `overview.md` → `repo:`. Replaces *"Run with cwd = the target repo. Resolve the vault from `.env` →
  `VAULT_PROJECT_DIR`"* — replaced, not supplemented.
- **`mf-forge:3` `description:`** — currently *"Runs in the repo, reads the vault PRD/design via .env."*
- **Target-repo paths rooted at the resolved repo** — `mf-forge:20,25`, `mf-inspect:16`, `mf-blueprint`'s
  codebase reads.
- **Rubric fallbacks NOT rooted there** — `mf-blueprint:18`, `mf-inspect:26`. See the two-root-classes decision (stage-A design, since superseded by this dir's re-rendered `design.md`): the obvious rule
  is wrong for exactly these two.
- **The change id derives from the version** — `NNNN = (major × 100) + minor`, zero-padded; the scan at
  `mf-forge:20` is deleted, not re-rooted. Collision on an existing directory **halts**. (Stage-A design decision; the current `design.md` no longer carries it, and phase 5 records how the collision was actually resolved.)
- **Halt diagnostics** — a missing, relative, or non-git `repo:` halts naming the **field**; never a traceback,
  never a silent fall-back to cwd.
- **`mf-line:25,29`** — the two `(main session; cwd = repo)` stage annotations. They carry no `prd/` string, so
  phase 2's grep does not reach them.
- Each skill names the repo files it needs rather than assuming the repo's `CLAUDE.md` is loaded (stage-A design decision).

**Acceptance.** `grep -rln 'VAULT_PROJECT_DIR\|\.env' skills/mf-blueprint skills/mf-forge skills/mf-inspect`
returns nothing; every `openspec/` occurrence in the three is repo-rooted; every `skills/rubrics/` occurrence is
the installed absolute path or a qualified `<repo>/` fallback; `mf-line` annotates no stage `cwd = repo`.

## 4 — Docs, and the `mf-teardown` gap recorded

**Requirement:** R5. **Deliverable:** the repo's docs describe the corrected line; two stale strings corrected.

- `README.md` — the `mf-` line section: skills run **from the vault** and resolve from `repo:`; no `.env` /
  `VAULT_PROJECT_DIR` wiring bullet for the three. Add one line of orientation: the session will ask for access to
  the repo the first time (stage-A design decision) — orientation, naming no path.
- `README.md:125` — no longer names **`mf-retrofit`** as v0.7, a claim false the moment this ships.
- `template/vault-pm/README.md:5` — *"`minions bootstrap` (v0.8)"* → **`mf-stamp` (v0.12)**, matching the roadmap.
- Vault `backlog.md` — the `mf-teardown` item with its two-part fix (preflight → `repo:`, six conditions → five;
  and the no-vault-page question), owned by **v0.9**.
- `CHANGELOG.md` `[Unreleased]` — including the deliberate asymmetry recorded in the stage-A design: three skills on the new
  model, `mf-teardown` still on the old.

**Acceptance**, each clause a check rather than a read:
- `grep -c 'mf-retrofit' README.md` → `0`.
- `grep -n 'minions bootstrap' template/vault-pm/README.md` → nothing; the line names **`mf-stamp` (v0.12)**.
- `README.md`'s `mf-` line section names `repo:` as the resolution source and carries no `.env` /
  `VAULT_PROJECT_DIR` bullet for the three retargeted skills. *(Scoped to that section — the README's other `.env`
  mentions belong to v0.8's documentation sweep and must survive this phase untouched.)*
- `grep -n 'mf-teardown' <vault>/backlog.md` → the item, naming both halves of the fix and **v0.9**.
- `CHANGELOG.md` `[Unreleased]` names the version and the deliberate asymmetry (stage-A design decision).

## 5 — Prove it: rename the change, then render this version

**Requirement:** A4. **Deliverable:** the change dir carries the derived id, the trailers agree, and the corrected
line has rendered this version from the vault.

**Order inside this phase is load-bearing.** `mf-forge` derives `NNNN-<name>` from the PRD and HALTs on *some other
`NNNN-*`*. Rename first, or it halts on the directory it is about to write.

- ~~`git mv openspec/changes/0007-pm-finds-repo openspec/changes/0007-pm-side-process-standard`~~ — **done
  during planning**, together with the branch rename. `openspec/changes/` holds exactly one directory. The rest of
  this phase still bites.
- Rebase the branch to rewrite the **five** stage-A trailers to `Change: 0007-pm-side-process-standard`. The
  branch is local and unmerged, so this preserves the traceability the id rename would otherwise split.
- `CHANGELOG.md` — the **seven** `[Unreleased]` entries naming the old id, and the phase-3 entry's forward note
  (*"v0.8 empties the key and records the break, v0.11 owns the fix"*), which this version's own stages B and C
  now supersede. The changelog sits outside every scan root and outside `git log`; nothing else catches it.
- Run the line from the vault project dir against this PRD; record the run under `proving/`, including any gap it
  exposed.

**Acceptance.** `git log --grep "Change: 0007-pm-side-process-standard"` returns every commit of the version,
stage A included; `git log --grep "Change: 0007-pm-finds-repo"` returns nothing; exactly one directory under
`openspec/changes/` holds `0007`; `grep -c '0007-pm-finds-repo' CHANGELOG.md` → `0`; the `proving/` record exists.

---

## 6 — Findings and the HALT report re-root under `.minions/`

**Requirement:** B1, B2. **Spec:** MODIFIED `fanout` → *Findings location and key*; MODIFIED `build-loop` →
*Deterministic per-phase decision*.

- `orchestrator/findings.py` — `findings_path` takes the **repo** and resolves
  `.minions/findings/<change-id>_<role>.md`. The single-resolution-site property is preserved: fan-out, converge
  and release resolve the identical path for identical inputs.
- `orchestrator/driver.py` — `halt_report_exists` takes the **repo** and tests `.minions/HALT.md`.
- The orchestrator creates `.minions/findings/` **before the first spawn** — the read-only role is granted write
  to its own file only and has no shell with which to create a directory.
- Update every call site and the `_findings_map` helper.

**Acceptance.** The resolved findings path is `<repo>/.minions/findings/<change-id>_<role>.md` for all three
consumers; a fan-out against a repo with no `.minions/findings/` creates it before spawning; `decide` halts on
`.minions/HALT.md`. Gate green.

---

## 7 — The deferred-work backlog re-roots, and its predicate reverses

**Requirement:** B3. **Spec:** MODIFIED `release` → *Release-gate preconditions*, *Fail-closed document guards*.

- The gate reads `.minions/<version>_backlog.md`. **Any list line blocks the release** — checkbox state is
  irrelevant, since an item leaves the file by being removed or exported, not by being ticked.
- **The fail-closed behaviour reverses deliberately** (`design.md` §3): a missing file **passes**, because with a
  per-version file in ephemeral `.minions/`, absence means *nothing was deferred* — the common case. The
  changelog guard's fail-closed behaviour is untouched.

**A key is retired here, so this phase is one commit like phases 10 and 14.** The old scenario
`release:failclosed-guards:backlog-missing-section-blocks` names the behaviour being reversed — it asserted that a
missing section *blocks* — and is replaced by `…backlog-missing-file-passes`. A rename is a removal plus an
addition, and `collect_spec_keys` drops a shipped key from the orphan set **only** on a REMOVED block: the
MODIFIED requirement no longer mentioning it is not enough, since MODIFIED lands at the release fold, not at check
time. So in one commit: author the live `## REMOVED Requirements` block in `specs/release/spec.md`, hand-delete
that scenario from `openspec/specs/release/spec.md`, and re-bind the test to the new key.

**Acceptance.** A backlog file with any `- ` line blocks; an empty file passes; a **missing** file passes; the
changelog guard still fails closed on a missing `[Unreleased]`; `specs check --strict` reports no orphan and no
dangling key. Gate green.

---

## 8 — The vault release-log writer is deleted

**Requirement:** B4. **Spec:** MODIFIED `release` → *Prepare locally or refuse — never ship*.

- `orchestrator/release.py` — delete `_release_log_entry` and `_prepend_release_log`; `prepare_release` drops its
  `vault_dir` parameter and every call site with it.
- The durable release record is `git log` + `CHANGELOG.md` + the annotated tag. The vault's narrative record is
  deprecated as a **destination**; the vault file itself is not deleted and is no concern of this repo.

**Acceptance.** `prepare_release` writes nothing outside the repo; no symbol named `release_log` survives in
`orchestrator/`; a green verdict still cuts the changelog, bumps pyproject, commits and tags. Gate green.

---

## 9 — The Inputs block drops the vault

**Requirement:** B5. **Spec:** MODIFIED `fanout` → *Orchestrator-owned role inputs*.

- `orchestrator/fanout.py` — `build_inputs_block` drops the `vault_dir` parameter and the trailing `Context:`
  line naming two vault files. Every role's block is repo-only: the change directory, the findings paths, the git
  head, the declared version.
- Update the fan-out and the release handoff emitter.

**Acceptance.** The built block names no path outside the repo; an assembled prompt still leads with the block.
**And this phase is where `fanout:findings-path:no-external-root-argument` becomes true and is bound**: it sits
under phase 6's requirement because that is where the findings root moves, but it asserts a property of the whole
orchestrator — *no signature takes a parameter naming a directory outside the repository* — and `build_inputs_block`
is the last one holding it. Prove it here: `grep -rn 'vault_dir' orchestrator/` returns nothing. Gate green.

---

## 10 — The vault preflight is deleted, not guarded

**Requirement:** B6. **Closes the backlogged containment finding.** **Spec:** REMOVED `change-state` →
*Vault-write preflight* (all **eleven** scenarios); MODIFIED `cli` → *Zero-token preflight before spend*.

**This phase stays whole, and the window is one commit wide.** `collect_spec_keys` discards a REMOVED key from
both the shipped and the resolvable sets as soon as the delta block exists: author it earlier and eleven live test
markers dangle; author it after the tests go and eleven shipped scenarios orphan. So this one commit does all four
things — delete the code, delete the fourteen bound tests, author the live `## REMOVED Requirements` block in
`specs/change-state/spec.md`, and **hand-delete the same requirement block from
`openspec/specs/change-state/spec.md`**. This is the rule the previous version's own vault-plan deletion commit
recorded.

- `orchestrator/state.py` — delete `read_vault_dir` and `verify_vault_access`; delete both call sites in
  `orchestrator/__main__.py`. No module reads `.env`.
- `tests/test_state.py` — delete the fourteen `change-state:vault-preflight:*` bound tests.
- `.env` and `.env.example` keep their shape as **empty scaffolding**: the files stay, the key and its comment
  block go, `.env.example` declares zero keys.
- `.gitignore` — the comment above `.minions/*` stops claiming `events.jsonl` carries a vault path; the rules
  themselves are unchanged.
- **B7 — the operator removes the vault grant from `.claude/settings.local.json`**: the three `Read` / `Edit` /
  `Write` globs over the vault project dir, and the `additionalDirectories` entry naming it. **This is the one
  requirement in the change that no test can catch** — the file is untracked, so it is neither committed nor
  scanned, and every automated check would pass with the grant still live. It belongs here because this is the
  phase after which nothing in the repo needs it: once the preflight is gone, no code path resolves, reads or
  writes a path outside the repository, so a role would run without it.

**Acceptance.** `minions run` against a repo with no `.env`, no key and no settings grant proceeds to the
change-state read and spawns normally — no preflight error; neither deleted symbol survives; `specs check
--strict` is green with no orphaned marker. Test count falls by fourteen. **And, by hand:**
`.claude/settings.local.json` names no vault directory under `additionalDirectories` and no `Read`/`Edit`/`Write`
glob covers one — confirm by reading the file and say so in the phase's report, since nothing else will.

---

## 11 — All six role prompts stop writing the vault

**Requirement:** B9.

- `prompts/coder.md` · `fixer.md` · `reviewer.md` · `release.md` · `security.md` · `simplify.md` — none names a
  retired needle or a bookkeeping step outside the repo.
- **Deferral targets** in the reviewer's nit routing, `simplify.md`, `security.md`, `coder.md` and `fixer.md` each
  name `.minions/<version>_backlog.md`. *(A separate clause because these route to a bare `backlog.md` and hold no
  needle — a scan would pass them unchanged while they point at a filename that resolves nowhere.)*
- **No prompt describes the Inputs block as carrying vault context.** `fixer.md` and `release.md` describe it
  rather than performing a step, so a "no bookkeeping step" check alone would leave stale descriptions of
  machinery phase 9 deleted.

**Acceptance.** Each of the six names none of the six needles, no step outside the repo, the new backlog path
where it defers, and no description of vault context in the Inputs block. Gate green.

---

## 12 — Root `CLAUDE.md` declares the findings contract

**Requirement:** B10.

Declare, in one place: the findings **path**, the frontmatter shape, **both** severity vocabularies (security
`critical|high|medium|low`; review `blocking|nit`), the `open → fixed → verified` machine with its
**producer/checker asymmetry** (the producer writes `fixed`; only the checker promotes to `verified`), and the
append-only resolution log.

This is the contract the next version's execution line consumes. Measuring it against the rubric is deliberately
**out of scope** — it waits for the version that re-measures the groups.

**Acceptance.** `CLAUDE.md` states all five elements and names no retired needle. Gate green.

---

## 13 — The rubric sheds three criteria; nine docs describe a self-contained repo

**Requirement:** B11, B12.

- `skills/rubrics/compliance.md` — delete `wiring:vault-perms` (`blocking`), `wiring:env-example` and
  `wiring:gitignore` (`required`); drop the vault-path clause from `wiring:claude-md` **including its restatement
  outside the criterion body**. Group A **6 → 3**; both baselines shrink (`23 → 20`, `16 → 13`).
- **Forward references**, all of them: the producer mentions repoint to the human / `mf-execute` (**v0.9**); the
  *"D–G planned — v0.8"* note (four lines) to **v0.10**. The same note in `skills/mf-teardown/SKILL.md`, the
  **eleven** `v0.7`/`mf-retrofit` producer mentions in that file, `skills/rubrics/README.md`'s producer column,
  and `template/vault-pm/README.md`'s `mf-stamp` version — which **phase 4 of this change wrote stale**.
- **The redaction block keeps its rule.** Its two worked examples are built on criteria this phase deletes;
  rewrite the examples, leave the rule. See `design.md` §6 — the rule rests on **destination**, not on the target
  being untrusted, so it outlives both criteria.
- Nine docs: `README.md`, `docs/README.md`, `docs/architecture.md`, `docs/modules/{driver,fanout,main,provider,release,state}.md`.
  **The README's `mf-teardown` section is deliberately left alone here** — phases 15 and 16 own it, so the shipped
  README describes the post-stage-C skill rather than a skill that exists for two phases.

**Acceptance.** Group A counts 3; both baselines read 20 and 13; no forward note names a superseded version; the
redaction rule survives with live examples; the nine docs show findings paths under `.minions/` and name no
needle **except inside `README.md`'s `mf-teardown` section**, which phase 16 owns and empties. Stating the
exception here rather than claiming a clean sweep: the section still describes a skill that has not been
retargeted yet, and phase 17's scan — not this phase — is what proves the absence. Gate green.

---

## 14 — The `sdd` spec stops requiring the vault

**Requirement:** B8 (spec half). **Spec:** MODIFIED `sdd` → *Repository is the source of truth for change
progress*, with two scenarios REMOVED and one ADDED.

- Rewrite the requirement: the repository holds the change, its progress **and** the roles' working artifacts;
  nothing shipped names the retired plan vocabulary or the retired vault vocabulary.
- **Delete what the removed scenarios leave dead in `tests/test_conventions.py`:** `_VAULT_SCANNED` and
  `_declared_vault_dir`, whose only users are the two tests this phase removes. The second **parses `.env` for
  `VAULT_PROJECT_DIR`** — dead code reading a key this version deleted, and `tests/` is outside every scan root,
  so nothing else would ever flag it.
- REMOVE `sdd:vault-layout:vault-path-not-in-repo` — the guard cannot run once the repo no longer knows a vault
  path — and `sdd:vault-layout:findings-and-prd-in-vault`, which asserts the arrangement this version reverses.
  **Same one-commit rule as phase 10:** author the live `## REMOVED Requirements` block in `specs/sdd/spec.md`,
  delete the two bound tests, and hand-delete the two shipped scenario blocks, all together. The MODIFIED block
  omitting them is not enough — omission only lands at the release fold.
- ADD the retired-**vault**-vocabulary scenario the phase-17 scan binds to.
- `progress-in-repo` and `no-plan-path-references` survive unchanged.

**Acceptance.** `specs check --strict` green, no orphan and no dangling key; the two scenarios are gone with their
tests; the new scenario exists and is not yet bound (phase 17 binds it). Gate green.

---

## 15 — The audit report moves into the repo it measures

**Requirement:** C1.

- `skills/mf-teardown/SKILL.md` — the report lands at `.minions/findings/teardown.md`, the reserved id
  `teardown`, the same home as every other findings file.
- **Rewrite the prose that advertises the reversed property**, in three documents and beyond the obvious range:
  the README's read-only claim and its report home; the skill's frontmatter `description:`, its merge and write
  steps, and the **`Never`** rule forbidding any write in the target; and the compliance rubric's report section
  with its vault-file framing — **the copy that actually steers a run**, since the rubric is what the measuring
  subagent reads.
- They do **not** claim the target gitignores `.minions/` — phase 13 deletes the criterion that required it. The
  claim that survives is narrower and true: the skill makes no change to the target's **tracked** tree.

**Acceptance.** All three documents name `.minions/findings/teardown.md`; none asserts the skill writes nothing in
the target; the `Never` rule reads consistently with what the skill now does. Gate green.

---

## 16 — The audit preflight resolves from `repo:`, and the file empties

**Requirement:** C2, C5.

- The skill runs **from the vault project dir** and resolves the target repo from `overview.md` → `repo:`.
- The six-condition `.env` table becomes **four** conditions on `repo:`: missing · relative · names a directory
  with no `.git` · the target has no vault project page at all. The last halts naming `repo:` and what to create.
- **Condition 6 is retired by decision, not by moot-ness** — record which of its three outcomes is accepted and
  why (`design.md` §6), rather than claiming the condition became irrelevant.
- **The six paragraphs reasoning from *cwd is the target*** are corrected. Only one states the rule; the other
  five argue from it. Two are not cosmetic: the stated security residual (which the move to the vault resolves —
  state what is true after the move, without inflating it into a feature this version set out to build), and an
  instruction **inside the subagent's own prompt block** describing that agent's context to itself.
- **The two blocks naming criteria phase 13 deletes** — the untrusted-target paragraph and the redaction
  constraint. The redaction rule is kept and its examples rewritten, matching phase 13's treatment of the rubric's
  copy.

- **`README.md`'s `mf-teardown` section**, which C2 assigns to this phase and which phase 13 deliberately
  deferred here: the **cwd example** at `README.md:113–115` still reads
  `cd /path/to/the/target/repo  # cwd must be the target` — the arrangement this phase reverses — and the
  **preflight sentence** at `README.md:124–128` still describes the target's `.env`, a usable
  `VAULT_PROJECT_DIR` and *"five preflight conditions, plus a sixth"*. The live `VAULT_PROJECT_DIR` at
  `README.md:126` is inside phase 17's scan root, so leaving it here makes that scan unreachable and phase 13's
  *"nine docs name no needle"* acceptance self-contradictory.

**This phase empties two files** — all twelve `VAULT_PROJECT_DIR` lines and the `read_vault_dir` reference in the
skill, and the last needle in `README.md`.

**Acceptance.** `git grep -n 'VAULT_PROJECT_DIR\|read_vault_dir' skills/mf-teardown/ README.md` returns nothing;
the four conditions are enumerated; no paragraph asserts or reasons from cwd being the target repo; both blocks
name only live criteria; the README's cwd example roots at the vault project dir. Gate green.

---

## 17 — The retired-vault scan lands, over its full root set

**Requirement:** B8 (test half), C3. **Binds** the scenario phase 14 added.

- `tests/test_conventions.py` — a third needle set with its **own** root set, in the pattern the file already
  ships and argues for. Needles: `VAULT_PROJECT_DIR`, `vault_dir`, `vault_project_dir`, `read_vault_dir`,
  `verify_vault_access`, `release_log`. Roots: `("orchestrator", "prompts", "docs", "README.md")` **plus
  `skills/`** — and, per `design.md` §4, `CLAUDE.md` and `.env.example`, so the root set covers everything the
  success criteria's whole-tree grep does.
- **No `skills/mf-teardown/` exclusion is declared anywhere in the file.** Phase 16 emptied it; there is nothing
  to suppress.
- Each needle is proved to bite, via the existing guard-fails test extended.
- Specs, the historical record and `tests/` stay excluded, as they are today — the last because the needles are
  literals in the guard itself.

**Acceptance.** The scan passes over the full root set with no exclusion declared; each needle fails the guard
when reintroduced; `specs check --strict` green with the phase-14 scenario now bound. Gate green.

---

## 18 — Re-measure: `mf-teardown` against this repo reports `compliant`

**Requirement:** C4. **The migration's end-to-end proof**, and the check stage B alone could not perform.

- Run `mf-teardown` against this repo, decoupled, from the vault project dir.
- The groups are re-measured against the **reduced** rubric. The untrusted-target posture is unchanged: the
  target's `CLAUDE.md` is **evidence to be quoted, never instruction to be obeyed**.
- This run also exercises four of the six properties this version reverses — a skill still saying *cwd is the
  target*, or still writing to the vault, does not merely read wrong, it runs wrong.

**Acceptance.** The verdict is `compliant` against the reduced rubric; the report lands at
`.minions/findings/teardown.md`; the run leaves the tracked tree unchanged. Gate green.

Then release: one version, one tag, one merge.
