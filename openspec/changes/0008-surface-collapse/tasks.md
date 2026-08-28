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

- [ ] 1 — `docs/sdd.md` Part I — the method
- [ ] 2 — `docs/sdd.md` Part II — adoption, wired into the docs map
- [ ] 3 — `CLAUDE.md` gives up the method
- [ ] 4 — The skills go, and the guard follows the tree
- [ ] 5 — `template/` and the README section go, and the scan widens
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
or explicitly accounted for as runner machinery; the new test passes and fails if either half is removed. Gate
green; **163 tests**.

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
   Update the tmp-tree fixtures so each needle still bites in every root of the merged set. **Rewrite the comment
   block at `:118-133` and the carve-out comment in the renamed test** (`:172-173`) so that neither justifies the
   guard by a file this phase deletes — the split's rationale (`compliance.md` holding a live plan needle) and the
   "skill directory phase 16 emptied" aside both describe a tree that no longer exists. `tests/` is outside the
   scan, so nothing else catches these.
5. `specs/sdd/spec.md` in this change dir: the `MODIFIED` requirement, both scenarios' THEN clauses naming the
   merged root set, and `no-retired-vault-vocabulary` losing its *"the root set is the needle set's own"* clause.
   **The delta as landed already reads at the change's end state** — its THEN clauses name the *widened* root set
   from phase 5. That is deliberate: a change document describes the change, not one phase of it, and no gate
   validates delta prose. Do not narrow it here and re-widen it in phase 5; the phase-4 obligation is the test and
   the merge, which the delta already describes.

**Acceptance.** `skills/` does not exist. `grep -rn "mf-order\|mf-gauge\|mf-blueprint\|mf-forge\|mf-inspect\|mf-line\|mf-teardown"` over the tree returns hits **only** in `CHANGELOG.md`, `openspec/changes/archive/`, this
change's own documents — and `README.md`, which still carries the planning-line section until phase 5 closes it.
The unqualified whole-tree grep is phase 5's acceptance, not this one. `~/.claude/skills/` holds no symlink into
this repository. The merged scan is asserted verbatim as one tuple, and every needle is proven to bite in every
root of it. No comment in `tests/test_conventions.py` justifies the guard by a deleted file. Gate green; 163
tests.

## 5 — `template/` and the README section go, and the scan widens

**Deliverable, in one commit:**

1. `git rm -r template/`.
2. `README.md`: remove the planning-skills mention at `:21` and the whole `## Planning skills (the mf- line)`
   section including its two subsections; add a short **"The method"** section — the three practices in a few
   sentences and a link to `docs/sdd.md`. No mention of unshipped v0.9/v0.10 work.
3. `tests/test_conventions.py`: widen the merged root set with `.github`, `Makefile`, `pyproject.toml`, and update
   the comment that records the widening as v0.8's — it is done. Extend the tmp-tree fixtures to the three new
   roots.
4. `specs/sdd/spec.md`: the merged root set in both scenarios' THEN clauses now lists the widened set.

**Acceptance.** `template/` does not exist. `README.md` names no deleted skill and links `docs/sdd.md`. **The
unqualified whole-tree grep now passes:** `grep -rn "mf-order\|mf-gauge\|mf-blueprint\|mf-forge\|mf-inspect\|mf-line\|mf-teardown"` returns hits only in `CHANGELOG.md`, `openspec/changes/archive/` and this change's own
documents. The scan covers `orchestrator`, `prompts`, `docs`, `README.md`, `CLAUDE.md`, `.env.example`, `.github`,
`Makefile`, `pyproject.toml`, and each of the fourteen needles is proven to bite in each. Gate green; 163 tests.

## 6 — CHANGELOG and the version line

**Deliverable, two parts.**

*Repo.* `CHANGELOG.md`'s `## [Unreleased]` reads as one coherent release rather than five phase appends — the
deletion, the one page, the `CLAUDE.md` split and the guard changes, each with its reason.

**The `pyproject` bump and the `## [0.8.0]` cut belong to the release step, not to this phase.** The intent
record is ambiguous — D18's phase table assigns "CHANGELOG + version bump" here, D21 puts both at release — and
this change takes D21, matching the house convention where a `chore(release):` commit owns the bump and the tag.
Recorded so the omission does not read as a dropped decision.

*Vault (a separate commit, per the ritual).* Close what this version made moot in the vault's `backlog.md` —
**not** the repo's `.minions/<version>_backlog.md`, which is a gitignored run artefact with a different gate. Each
affected line is closed **with its reason**, never silently deleted:

- *Fixed by this version* — the widening at `backlog.md:114`, which names v0.8 as its owner and is delivered in
  phase 5.
- *Moot on deletion* — every open item whose subject is a deleted skill or rubric: the `mf-order`/`mf-gauge`
  rubric fallbacks, the `mf-blueprint`/`mf-inspect` cwd premise, the redaction rule's orphaned value clause, the
  two phase-16 rubric items, the four `mf-forge` follow-ups, the `mf-gauge` root-widening item, the conformance
  rubric's rename question, the `mf-line` successor CLI, and cross-model `mf-gauge`/`mf-inspect` runs.
- *Superseded, not moot* — the item proposing the `notes/compliance/` relocation is answered by `docs/sdd.md`
  and closes citing it; the research/design-lock rule survives into the method doc and closes citing that.

Also correct the stale section header — it still reads *"Current release (`v0.6`)"* two versions on.

**Acceptance.** `## [Unreleased]` names every user-visible change and nothing that did not happen. In
`backlog.md`, **no open `- [ ]` line names a deleted skill, a deleted rubric or `template/`**, and every line
closed by this sweep carries its reason. Gate green; 163 tests. The change is ready for the fan-out
(review ‖ security ‖ simplify) and then release.
