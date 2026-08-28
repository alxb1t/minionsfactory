# Tasks — 0008-surface-collapse

Ordered phases for v0.8, a declared **`normal`** change: one feature, one version, one tag. **Build mode: by hand**
(Claude Code + human; no orchestrator automation). Read `proposal.md` + `design.md` (this dir) and the vault
intent record (`planning/v0.8/v0.8_grilling.md`) first.

**Per-phase ritual (every phase).**
- Author the phase's deliverable → confirm the **repo gate is green**
  (`uv sync --locked` · `uv run ruff format --check .` · `uv run ruff check .` · `uv run ty check` ·
  `uv run pytest -q` · `uv run python -m orchestrator specs check --strict`) → run the phase's own acceptance check.
- **Commit** in the code repo with a `Change: 0008-surface-collapse` trailer, **contiguous** with
  `Co-Authored-By:` (no blank line between — git parses the trailer block as the last paragraph). Vault edits are
  separate from the code commit.
- Append the phase's changes under `## [Unreleased]` in `CHANGELOG.md`.
- Tick the phase's box in `## Progress` below, then continue.

**Finish each phase completely before starting the next.** Never interleave phases, and never tick a box whose
acceptance is not met.

**The test count is a signal, not a constant.** The suite is **162** at branch point. Phase 2 adds the one
structural test → **163**, and it holds at 163 for the rest of the change. The guard rewrites in phases 4 and 5
change what the existing tests *scan*, not how many there are. A count that moves anywhere else means something
outside scope was edited — a stop condition.

**Build-order rule (binding): no commit ships a scan that lies.** The root-set merge is green only once `skills/`
is gone, and a deletion committed *without* its guard edit ships a guard silently scanning one root fewer. So each
deletion lands **in the same commit** as the guard edit it forces — phase 4 pairs the `skills/` deletion with the
merge and the spec delta, phase 5 pairs the `template/` deletion with the widening. See `design.md` §4.

**Uninstall before delete (binding).** Phase 4 runs `make uninstall-skills` **before** `git rm -r skills/`. Eight
symlinks under `~/.claude/skills/` point into that directory; deleting it first strands them on the operator's
machine, and the Makefile target that removes them cleanly is deleted in the same phase.

**Spec delta:** real, under `specs/sdd/` — one `MODIFIED` requirement carrying two changed scenarios. **No key is
added, renamed or removed**, so the one-commit spec-removal window does not apply to this change.

**Halt and ask the human** when: the work would need a new dependency · a requirement turns out
self-contradictory · the gate goes red for a reason the phase's own scope cannot fix · a rubric turns out to hold
content that has no home in `docs/sdd.md` and no other home either · the fix would mean editing the intent record.

## Progress

- [x] 1 — `docs/sdd.md` Part I — the method
- [x] 2 — `docs/sdd.md` Part II — adoption, wired into the docs map
- [x] 3 — `CLAUDE.md` gives up the method
- [x] 4 — The skills go, and the guard follows the tree
- [x] 5 — `template/` and the README section go, and the scan widens
- [ ] 6 — CHANGELOG and the version line

---

## 1 — `docs/sdd.md` Part I — the method

**Deliverable:** `docs/sdd.md` carrying Part I only — what this is and the three practices · the unit of work
(`openspec/specs/` + `changes/<id>/`: proposal · design · tasks · delta) · traceability (the `Change:` trailer,
scenario keys bound to proving tests, `change vX.Y = CHANGELOG = tag`) · the gate (declared on disk, **run, never
summarized**) · the loop (grill → cut → build → review ‖ security ‖ simplify → converge → release; builder
interactive, checkers blind) · the findings contract · the release fold.

Harvested from `CLAUDE.md` — which is **not yet edited** — and from the tree, so the source is read rather than
recalled. Written above the tool layer (`design.md` §1): stations and disk artifacts, never who runs them. The
grilling record's station appears as *"grilling produces a written record of what was settled; the change is cut
from it and checked against it"* — no path, no vault.

**Acceptance.** The page names no orchestrator module, no vault path, no MinionsFactory-specific directory beyond
the ones the standard itself defines, and nothing that assumes an installed package. A reader with no access to
this repository can act on it. Gate green; 162 tests.

## 2 — `docs/sdd.md` Part II — adoption, wired into the docs map

**Deliverable:** Part II — *what must be settled before a change is cut* (distilled from
`skills/rubrics/prd-readiness.md` + `feasibility.md`) and *the readiness checklist* (distilled from
`compliance.md`'s Tier-1 groups A/B/C plus the `python-uv` profile, re-framed per `design.md` §1 as *can the loop
be run here* rather than *can the orchestrator start*). `compliance.md:266-586` — the teardown report contract —
is **not** carried: it is the deleted runner's machinery.

Then wire it in: `docs/README.md` gains a line declaring `sdd.md` the one page about the method rather than about
this codebase, and the new structural test lands in `tests/test_conventions.py` —

```python
@pytest.mark.spec_exempt("structural — the method doc is wired into the docs map")
def test_the_method_doc_exists_and_the_docs_map_links_it() -> None:
```

— asserting `docs/sdd.md` exists and `docs/README.md` references it. Structural only; nothing about contents.

**Acceptance.** `docs/sdd.md` is 220–260 lines; every criterion of the four rubrics is either present in the page
or explicitly accounted for as runner machinery; the new test passes and fails if either half is removed. **The
genericity bar from phase 1 applies to Part II and is re-checked over the whole page** — no orchestrator module,
no vault path, nothing assuming an installed package. Part II is distilled from `compliance.md`, the most
orchestrator-shaped source in the tree, so this is where the bar is most likely to slip. Gate green; **163
tests**.

## 3 — `CLAUDE.md` gives up the method

**Deliverable:** `CLAUDE.md` loses *Where the work is defined*, *The findings contract*, the CHANGELOG/version-line
rule, the release fold and "the gate is run, never summarized" — each replaced by nothing, with one pointer to
`docs/sdd.md` for the method. It keeps this repo's six gate commands, the seams, the no-LLM-in-orchestration
invariant, the guardrails and the layout facts (`design.md` §2).

**Acceptance.** `CLAUDE.md` is ~70 lines shorter. `prompts/coder.md:29`'s claim that it holds *"the quality gate,
the engineering conventions/seams, the guardrails"* is still true, and **no file under `prompts/` is edited** in
this phase. Nothing the method defines is stated in both files. Gate green; 163 tests.

## 4 — The skills go, and the guard follows the tree

**Deliverable, in one commit:**

1. `make uninstall-skills` — **first**, while the target still exists.
2. `git rm -r skills/` — all seven `mf-*` skills and all four rubrics.
3. `git rm` the `install-skills` / `uninstall-skills` targets from `Makefile`, and their `.PHONY` entries.
4. `tests/test_conventions.py`: drop `skills` from the vault root set and **merge the two root sets into one**
   shared `_SCANNED` (`design.md` §3.1), keeping the two needle sets distinct. Rename
   `test_the_vault_scan_carves_out_no_directory_inside_its_scanned_roots` to drop "vault" — there is one scan now.
   Update the tmp-tree fixtures so each needle still bites in every root of the merged set. **Then sweep the whole
   file, not a list of sites:** no comment, test name, docstring or fixture in `tests/test_conventions.py` may
   justify the guard by — or name as live — a surface this phase deletes. Known at authoring time: the split's
   rationale block (`compliance.md` holding a live plan needle), the "skill directory phase 16 emptied" carve-out
   aside, the needle-boundary note reasoning from *"the vault-side skills must be able to name what they
   resolve"*, and the test name `test_the_retired_vault_vocabulary_is_named_nowhere_in_code_docs_or_skills`,
   whose `_or_skills` is the exact wording the spec delta drops from the scenario title it proves. That list is a
   starting point, **not the boundary** — `tests/` is outside the scan, so nothing mechanical catches a site the
   list misses.
5. `specs/sdd/spec.md` in this change dir: the `MODIFIED` requirement, both scenarios' THEN clauses naming the
   merged root set, and `no-retired-vault-vocabulary` losing its *"the root set is the needle set's own"* clause.
   **The delta as landed already reads at the change's end state** — its THEN clauses name the *widened* root set
   from phase 5. That is deliberate: a change document describes the change, not one phase of it, and no gate
   validates delta prose. Do not narrow it here and re-widen it in phase 5; the phase-4 obligation is the test and
   the merge, which the delta already describes.

**Acceptance.** `skills/` does not exist. `git grep -n "mf-order\|mf-gauge\|mf-blueprint\|mf-forge\|mf-inspect\|mf-line\|mf-teardown"` returns hits **only** in `CHANGELOG.md`, `openspec/changes/archive/`, this change's own
documents, and the two surfaces phase 5 owns — `README.md` and `template/`, both of which still name the line
until then. The unqualified form is phase 5's acceptance, not this one. (`git grep`, not `grep -rn`: the latter
descends into `.venv/` and the caches, where matches prove nothing.) `~/.claude/skills/` holds no symlink into
this repository. The merged scan is asserted verbatim as one tuple, and every needle is proven to bite in every
root of it. `git grep -n "skills\|template/" tests/test_conventions.py` returns nothing that
names either as a live surface — comments, test names, docstrings and fixtures alike. Gate green; 163 tests.

## 5 — `template/` and the README section go, and the scan widens

**Deliverable, in one commit:**

1. `git rm -r template/`.
2. `README.md`: remove the planning-skills mention at `:21` and the whole `## Planning skills (the mf- line)`
   section including its two subsections; add a short **"The method"** section — the three practices in a few
   sentences and a link to `docs/sdd.md`. No mention of unshipped v0.9/v0.10 work.
3. `tests/test_conventions.py`: widen the merged root set with `.github`, `Makefile`, `pyproject.toml`, and update
   the comment that records the widening as v0.8's — it is done. Extend the tmp-tree fixtures to the three new
   roots.

There is **no delta item in this phase**: the delta was landed at the change's end state and already names the
widened root set (see phase 4, item 5).

**Acceptance.** `template/` does not exist. `README.md` names no deleted skill and links `docs/sdd.md`. **The
unqualified form now passes:** `git grep -n "mf-order\|mf-gauge\|mf-blueprint\|mf-forge\|mf-inspect\|mf-line\|mf-teardown"` returns hits only in `CHANGELOG.md`, `openspec/changes/archive/` and this change's own documents. The scan covers `orchestrator`, `prompts`, `docs`, `README.md`, `CLAUDE.md`, `.env.example`, `.github`,
`Makefile`, `pyproject.toml`, and each of the fourteen needles is proven to bite in each. Gate green; 163 tests.

## 6 — CHANGELOG and the version line

**Deliverable, four parts.**

*Repo.* `CHANGELOG.md`'s `## [Unreleased]` reads as one coherent release rather than five phase appends — the
deletion, the one page, the `CLAUDE.md` split and the guard changes, each with its reason.

**The `pyproject` bump and the `## [0.8.0]` cut belong to the release step, not to this phase.** The intent
record is ambiguous — D18's phase table assigns "CHANGELOG + version bump" here, D21 puts both at release — and
this change takes D21, matching the house convention where a `chore(release):` commit owns the bump and the tag.
Recorded so the omission does not read as a dropped decision.

*The release-gating backlog (repo).* `.minions/v0.8_backlog.md` exists on disk and is the abandoned branch's —
`# Deferred work — v0.8 (0008-compliance-surface)`, six open items about `report-contract.md` and
`compliance.md`, files this version deletes outright. `.minions/` is gitignored, so deleting that branch did not
remove it, and `_backlog_blocker` blocks the release on **any** list line whatever its checkbox state
(`prompts/release.md`: "no exceptions"). Left alone it halts the v0.8 release over a change that no longer
exists. Empty it of items following the `v0.7_backlog.md` precedent — keep the header and record how it emptied,
here: every item was moot on deletion of its subject. Remove `.minions/v0.8_resume.md` for the same reason: it is
the resume pointer for a run that no longer has a branch.

*The vault backlog (a separate commit, per the ritual).* Close what this version made moot in the vault's
`backlog.md`. This is a different file from the one above, with a different gate — that one blocks the release,
this one holds the project's deferred work.

**Apply a rule, not a list.** An open item is **moot** when its *subject* is a deleted skill or rubric — closing
it would require editing a file this version deletes. An item that merely **cites** one as provenance, as the
vehicle it was going to be executed through, or as an example is **not** moot: its subject survives, and it stays
open with its wording corrected where the citation has become misleading.

**The candidate set is whatever the grep returns when you run it** — a count written here would be a fourth
hand-enumeration, and the first three were each wrong in a different direction. Run the name grep over
`backlog.md` (the seven skills, the four rubrics, `template/`), remembering that an item's body spans several
lines, so a match can sit below the `- [ ]` that owns it. Then account for every hit. They do not all resolve the
same way, and three groups look moot without being so:

- **The record's own non-goals keep two.** `template/` as a stampable skeleton, and genericizing `prompts/` into
  it, both belong to `mf-stamp` — which the non-goals explicitly leave on the backlog. Deleting `template/` in
  phase 5 does not close them; it is the reason they are still wanted.
- **The widening item is closed in part, not in whole.** Phase 5 delivers the root-set widening it names, but it
  also carries two gaps this version does not touch — `_text_files`'s seven-suffix allowlist, and the active
  `openspec/changes/<id>/` being neither scanned nor declared as an exclusion. Close the widening clause with its
  reason; leave the item open stating what remains. (The second gap is the one the round-1 blind check found this
  change asserting away — see `design.md` §3.3.)
- **Citation is not subject.** Items whose subject is the loop, the orchestrator, or migrating live targets, and
  which name a deleted skill only as the vehicle or the provenance, stay open. Where the named vehicle no longer
  exists, correct the sentence rather than closing the item.

*The superseded vault documents (a separate commit).* The intent record's **D24** settles that four vault
documents move to `archive/notes/` with a README naming what replaced them, *"when `docs/sdd.md` ships"*:
`conventions.md`, `principles.md`, `notes/compliance/` (five files) and `notes/workflow.md`. Two warrants, not
one: `notes/compliance/` and `notes/workflow.md` **describe** the surface this version deletes and the five-stage
line it removes; `conventions.md` and `principles.md` are **superseded** by `docs/sdd.md`, which `overview.md`
already promises in as many words. Nothing downstream can do this — the release role cannot reach the vault, and
no backlog line names it — so it is recorded here or it does not happen. Archiving, not deleting: they hold
reasoning `docs/sdd.md` compresses, and the compression is lossy by design.

`overview.md` loses the ⚠ *"Documents under refinement"* section, but **not by deleting the block wholesale**: its
last entry is the vault standard (`notes/vault_standard.md`), which D24 does **not** archive — this version
*updated* it — and which has no other link in the page. Move that entry into the Links list, then drop the
section. Also drop the `workflow` entry from the Links list, which sits **outside** the section and would
otherwise survive as a live link to an archived document.

**Do not close an item by deletion.** Each closed line says which of the three it was — fixed by this version,
moot on deletion of its subject, or superseded by `docs/sdd.md` — and cites what replaced it.

**Acceptance.**

1. `## [Unreleased]` names every user-visible change and nothing that did not happen.
2. `_backlog_blocker` finds **no list line** in `.minions/v0.8_backlog.md`, and `.minions/v0.8_resume.md` is
   gone — the release gate's own precondition, checkable by reading the file.
3. `archive/notes/` holds the four superseded documents with a README naming what replaced each, none of them
   remains at its old path, and no live vault page links to an unarchived copy. `notes/vault_standard.md` is
   **not** among them and is still linked from `overview.md`.
4. In the vault's `backlog.md`, **every open item that names a deleted skill, rubric or `template/` is either
   closed with its reason, or carries a one-line note saying why its subject survives the deletion.** The name
   grep lists the candidates; each candidate is then accounted for one way or the other. No open item requires
   editing a deleted file in order to be closed.
5. Gate green; 163 tests. The change is ready for the fan-out (review ‖ security ‖ simplify) and then release.
