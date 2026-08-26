# Design — 0007-pm-finds-repo

Technical decisions for v0.7. Doc-only: twelve files, one directory move, no code. Read with `proposal.md` and the
vault PRD (`planning/v0.7/v0.7_pm_finds_repo.md`).

## 1. Two root classes, not one

The single highest-risk decision in this change, because the obvious rule is wrong for exactly two paths.

Moving the working directory to the vault re-points every relative path in the retargeted skills. They carry
**two kinds**, which must not be treated alike:

| Class | Sites | Roots at |
|---|---|---|
| **Target-repo paths** | `mf-forge:20,25` (`openspec/changes/…`), `mf-inspect:16`, `mf-blueprint`'s codebase reads | the resolved `repo:` |
| **The skills' own rubrics** | `mf-blueprint:18`, `mf-inspect:26` (`skills/rubrics/<name>.md` *"(source repo)"*) | the **installed** absolute path |

The rubrics belong to **MinionsFactory**, not to the target. A target that is not MinionsFactory does not ship
them, so a blanket "root everything at `repo:`" rule fixes them **wrongly** — silently, by resolving to a path
that exists only when the target happens to be this repo.

**Decision.** Rubric reads resolve to `~/.claude/skills/rubrics/<name>.md`. The source-repo fallback is written
`<repo>/skills/rubrics/<name>.md` and carries an explicit *"only when the resolved repo ships them"* qualification.

## 2. The change id derives from the version

`mf-forge:20` computes `NNNN` as *"the next number after the highest existing dir under `openspec/changes/`
including `archive/`"*. Under this change that read crosses the seam: unrooted, it scans the **vault** and
restarts numbering at `0001`.

Re-rooting it would work. Deleting it is better, because the scan only ever implemented a coincidence: the
*one small feature = one change = one version* rule has made the id equal the version in every change shipped —
`v0.3`→`0003`, `v0.4`→`0004`, `v0.5`→`0005`, `v0.6`→`0006`.

**Decision.** `NNNN = (major × 100) + minor`, zero-padded to four digits. `v0.7`→`0007`, `v0.8`→`0008`,
`v1.0`→`0100`. Properties that were checked rather than assumed:

- **Reproduces every shipped id**, so no archived change is renamed.
- **Monotonic past the 1.0 boundary** (`v0.9`→0009 < `v0.10`→0010 < `v1.0`→0100), so `state.py::select_change`'s
  "highest numeric id wins" invariant survives and needs no revisiting at 1.0.
- **Shape satisfies `_CHANGE_ID_PATTERN`** and the `sdd:change-structure:malformed-change-id-refused` scenario.
- **Domain is closed** — undefined for patch versions, but `mf-forge` already refuses a non-`vX.Y` version.
- **No repo read at all**, so the id is knowable before the target is resolved.

**Collision halts.** If the derived directory already exists, two changes claim one version — a violation of the
one-change-one-version rule, and a question for the human. `mf-forge` stops rather than incrementing past it;
incrementing would silently restore the coincidence this decision removes.

## 3. The harness loads a different root `CLAUDE.md`

Running from the vault means the *vault's* operating manual is the project instruction set and the repo's is not
loaded. Each retargeted skill therefore names the repo files it needs rather than assuming repo context.

This is also a quiet security improvement: the target repo's `CLAUDE.md` becomes **data the skill reads** rather
than **instructions the harness obeys** — the posture `mf-teardown`'s untrusted-target clause argues for, now true
by construction for the whole line.

## 4. Write direction, and what is deliberately not specified

`mf-forge` now writes into the repo from a vault-rooted session, the opposite of today. The first such write
raises a **permission prompt**, which the supervising human approves — Track A is supervised by design, so a
prompt is the normal interaction.

**Deliberately not a requirement.** That grant is operator-local, untracked config in the human's own vault, not
part of the standard this repo ships. Specifying it would encode one machine's setup into the product — precisely
the coupling v0.8 removes when it deletes the repo's vault grant. The two are not symmetric: one is a tracked
coupling being removed, the other a local convenience that never needed specifying. R5 carries one line of
orientation prose instead, naming no path.

## 5. Carried caveat — `mf-teardown` stays transitional

This change leaves one skill of four on the old model, reading `.env` → `VAULT_PROJECT_DIR`. That is a deliberate
scope boundary, not an oversight: its fix carries an unsettled product question (what happens to a target repo
with **no vault project page**, which its *"point it at any existing project"* pitch promises), and settling that
would grow a twelve-file prose change into a design discussion.

**Consequence to state in the CHANGELOG** so the asymmetry reads as designed: three skills resolve from the vault,
one still reads the repo's `.env`. It keeps working through v0.7; **v0.8 empties the key and records the break;
v0.11 owns the fix.**

## 6. Proving, and the two-active-changes overlap

A doc-only change to instructions cannot be proved by a unit test. It is proved by use: all three retargeted
stages run against the v0.8 PRD, recorded under `proving/` following the v0.6 convention.

Two constraints on that record:

- **The vault's absolute path is elided**, written `<vault>/planning/v0.8/…`. `proving/` sits under `openspec/`,
  which `tests/test_conventions.py::test_the_operators_vault_path_is_named_nowhere_in_the_repo` scans for that
  literal string; writing it turns the gate red and breaks this change's own "163 tests, unchanged" constraint.
  v0.6's `proving/README.md` already states the convention.
- **The run leaves two active change directories** — `0007-pm-finds-repo`, still being built, beside the freshly
  forged `0008-decoupling` — so `select_change` begins answering `0008`. Harmless as planned: v0.7 is hand-built
  and Track B is parked, so nothing consults `select_change` during the overlap, and the hand-build reads `0007`
  explicitly. The overlap ends when v0.7's release archives `0007`.

**Ordering.** Phase 5 requires the v0.8 PRD to be gauge-`clean` first — forging from an ungated PRD would prove
the plumbing while breaking the discipline the line exists to enforce. It does not block phases 1–4.

## 7. Enforcement is by grep, and that is proportionate

Nothing machine-checks prose skills. R3's enforcement is `grep -rn 'prd/' skills/ template/`, run by hand at the
end of phases 2 and 3. The committed convention scan (`_SCANNED`) does not cover `skills/`, and v0.8 widens it
only for the five *vault* needles — `prd/` is not among them, so a regression here is silent.

**Accepted**, with a pointer: when v0.8 rewrites that test, `prd/` is worth adding to the needle set. Building the
guard here and again there would mean writing it twice.
