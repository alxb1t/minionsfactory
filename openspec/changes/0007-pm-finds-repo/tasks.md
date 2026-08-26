# Tasks — 0007-pm-finds-repo

Ordered phases for v0.7. **Build mode: by hand** (Claude Code + human; no orchestrator automation — a prose change
has no tests to bind, so a loop-built gate would be vacuously green). **Doc-only change** — ships prose (six
skills, three rubrics, a worked example, README lines) plus one vault convention. Read `proposal.md` + `design.md`
(this dir) and the vault PRD (`planning/v0.7/v0.7_pm_finds_repo.md`, R1–R5) first.

**Per-phase ritual (every phase).**
- Author the phase's deliverable → confirm the **repo gate stays green and unchanged at 163 tests**
  (`uv sync --locked` · `uv run ruff format --check .` · `uv run ruff check .` · `uv run ty check` ·
  `uv run pytest -q` · `uv run python -m orchestrator specs check --strict`) → run the phase's own acceptance grep.
- **Commit** in the code repo with a `Change: 0007-pm-finds-repo` trailer, **contiguous** with `Co-Authored-By:`
  (no blank line between — git parses the trailer block as the last paragraph). Vault edits are separate from the
  code commit.
- Append the phase's changes under `## [Unreleased]` in `CHANGELOG.md`.
- Tick the phase's box in `## Progress` below, then continue.

**Finish each phase completely before starting the next.** Never interleave phases, and never tick a box whose
acceptance is not met.

**A moving test count is a stop condition.** This change touches no code. If `pytest -q` reports anything other
than 163, something outside the declared scope was edited — stop and report rather than adjusting the count.

**Halt and ask the human** when: the work would need code in `orchestrator/`, a new dependency, or anything the
PRD's Constraints forbid · a PRD requirement turns out self-contradictory · the gate goes red for a reason the
phase's own scope cannot fix · phase 5's proving run disagrees with what the PRD predicts · the fix would mean
editing the PRD.

**Spec delta is N-A** — see `specs/README.md`. No scenarios to bind, nothing to fold at release.

## Progress

- [x] 1 — The vault declares its repo
- [x] 2 — The path axis: `prd/` retires across `skills/` and `template/`
- [x] 3 — The resolution axis: three skills run from the vault
- [x] 4 — Docs, and the `mf-teardown` gap recorded
- [ ] 5 — Prove it: the corrected line renders v0.8

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
- **Rubric fallbacks NOT rooted there** — `mf-blueprint:18`, `mf-inspect:26`. See `design.md` §1: the obvious rule
  is wrong for exactly these two.
- **The change id derives from the version** — `NNNN = (major × 100) + minor`, zero-padded; the scan at
  `mf-forge:20` is deleted, not re-rooted. Collision on an existing directory **halts**. See `design.md` §2.
- **Halt diagnostics** — a missing, relative, or non-git `repo:` halts naming the **field**; never a traceback,
  never a silent fall-back to cwd.
- **`mf-line:25,29`** — the two `(main session; cwd = repo)` stage annotations. They carry no `prd/` string, so
  phase 2's grep does not reach them.
- Each skill names the repo files it needs rather than assuming the repo's `CLAUDE.md` is loaded (`design.md` §3).

**Acceptance.** `grep -rln 'VAULT_PROJECT_DIR\|\.env' skills/mf-blueprint skills/mf-forge skills/mf-inspect`
returns nothing; every `openspec/` occurrence in the three is repo-rooted; every `skills/rubrics/` occurrence is
the installed absolute path or a qualified `<repo>/` fallback; `mf-line` annotates no stage `cwd = repo`.

## 4 — Docs, and the `mf-teardown` gap recorded

**Requirement:** R5. **Deliverable:** the repo's docs describe the corrected line; two stale strings corrected.

- `README.md` — the `mf-` line section: skills run **from the vault** and resolve from `repo:`; no `.env` /
  `VAULT_PROJECT_DIR` wiring bullet for the three. Add one line of orientation: the session will ask for access to
  the repo the first time (`design.md` §4) — orientation, naming no path.
- `README.md:125` — no longer names **`mf-retrofit`** as v0.7, a claim false the moment this ships.
- `template/vault-pm/README.md:5` — *"`minions bootstrap` (v0.8)"* → **`mf-stamp` (v0.12)**, matching the roadmap.
- Vault `backlog.md` — the `mf-teardown` item with its two-part fix (preflight → `repo:`, six conditions → five;
  and the no-vault-page question), owned by **v0.11**.
- `CHANGELOG.md` `[Unreleased]` — including the deliberate asymmetry from `design.md` §5: three skills on the new
  model, `mf-teardown` still on the old.

**Acceptance**, each clause a check rather than a read:
- `grep -c 'mf-retrofit' README.md` → `0`.
- `grep -n 'minions bootstrap' template/vault-pm/README.md` → nothing; the line names **`mf-stamp` (v0.12)**.
- `README.md`'s `mf-` line section names `repo:` as the resolution source and carries no `.env` /
  `VAULT_PROJECT_DIR` bullet for the three retargeted skills. *(Scoped to that section — the README's other `.env`
  mentions belong to v0.8's documentation sweep and must survive this phase untouched.)*
- `grep -n 'mf-teardown' <vault>/backlog.md` → the item, naming both halves of the fix and **v0.11**.
- `CHANGELOG.md` `[Unreleased]` names the version and the deliberate asymmetry (`design.md` §5).

## 5 — Prove it: the corrected line renders v0.8

**Requirement:** R4. **Deliverable:** `proving/`, and `openspec/changes/0008-decoupling/` in the repo.

**Precondition — do not start this phase until the v0.8 PRD is gauge-`clean`.** Its earlier `clean` was earned
under the pre-split numbering and is marked `stale`; forging from an ungated PRD would prove the plumbing while
breaking the discipline the line exists to enforce.

- Run **all three** retargeted stages from the vault against the v0.8 PRD, so none ships unexercised:
  `mf-blueprint` (**overwrites** the existing `planning/v0.8/v0.8_design.md`) → `mf-forge` → `mf-inspect`.
- `mf-forge` writes `<repo>/openspec/changes/0008-decoupling/` — id derived, not scanned. **No directory named
  `openspec/` appears in the vault.**
- Record each invocation, its resolved paths and its artifacts under `proving/`, **with the operator's absolute
  vault path elided** as `<vault>/…` (`design.md` §6 — the gate scans this directory for that literal string).
- Note the two-active-changes overlap (`design.md` §6): `select_change` begins answering `0008` until release
  archives `0007`.

**Acceptance.** The three runs complete with no `.env` read and no `VAULT_PROJECT_DIR` in any resolution;
`0008-decoupling/` exists in the repo with its four artifacts; `proving/` records all three and contains no
absolute vault path; gate green at 163 tests.
