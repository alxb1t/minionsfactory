# Tasks — 0010-execution-line-skills

**Change:** `0010-execution-line-skills` · **Version:** v0.10 · **Build mode:** hand-authored, one phase per commit.

Every commit carries a `Change: 0010-execution-line-skills` trailer, contiguous with any `Co-Authored-By:`. Every
phase ends on a green gate (`make gate`, or the six commands in `.minions/minions.toml`) and appends its entry
under `## [Unreleased]` in `CHANGELOG.md`. A phase is finished by a commit **and** a ticked box — either alone is
not an advance.

`## Progress` below is what `orchestrator/state.py` reads; the `N.M` checkboxes inside each phase section are
sub-tasks for the builder and are invisible to that parser.

**One rule binds every phase 1-4:** no `SKILL.md` may contain an absolute path, a `~/` expansion, or any path
outside the repository it is invoked in (`design.md` — D15). The check is the same for all four and is run in
phase 5.

## Progress

- [x] 1 — `mf-build` — the phase-by-phase builder
- [x] 2 — `mf-converge` — the conductor
- [x] 3 — `mf-backlog-export` — the human-invoked vault bridge
- [x] 4 — `mf-release` — verify, fold, archive, tag, stop
- [x] 5 — The install path, and the README catches up
- [x] 6 — `CLAUDE.md` declares the two lines
- [ ] 7 — `skills/` becomes the tenth scanned root

---

## 1 — `mf-build` — the phase-by-phase builder

Transcribed from the build hand-off. It is the one skill with no prior recorded run (`design.md` — D13), so it
carries the conventions an agent loses natively rather than the building an agent does natively.

- [x] 1.1 Create `skills/mf-build/SKILL.md` with YAML frontmatter carrying `name: mf-build` and a
  `description:` that names when to use it. *Verify:* `head -4 skills/mf-build/SKILL.md` shows both keys inside a
  `---` block.
- [x] 1.2 Write the per-phase ritual: build only the first unticked `## Progress` phase · **run each task's stated
  verification, never summarize it** · run the full gate read from `.minions/minions.toml` · append the
  `CHANGELOG.md` entry · tick the box · **one commit for that phase**, staged by name, with the
  `Change: <change-id>` trailer contiguous with `Co-Authored-By:` · never batch phases.
  *Verify:* `grep -c 'never summarize\|Change: <change-id>\|one commit' skills/mf-build/SKILL.md` is non-zero for
  each of the three literals.
- [x] 1.3 Write the closing simplify pass: after the last phase, run `/simplify` over the change diff and let it
  fix in place; **re-run the gate — red is a halt**; commit its edits as their own trailered commit. State that
  this is a declared deviation from `docs/sdd.md`'s three-read-only-station *Check*, and why it is safe (review
  verifies simplify's work). *Verify:* the section names `/simplify`, the re-run gate and the deviation.
- [x] 1.4 Write the five stop-conditions, each a halt with no guessing past it: an acceptance that cannot be a
  passing check · the design contradicting the code · a task ambiguous enough that two readings give different
  work · a dependency that would need adding · a gate that only goes green by weakening.
  *Verify:* five distinct halt conditions are enumerated in the file.
- [x] 1.5 State that the change id is a **required parameter** and that the skill halts without it — never
  inferred from the highest directory number (`design.md` — D12). *Verify:* the file names the parameter and the
  halt.

## 2 — `mf-converge` — the conductor

The largest file, and the one that carries the invariants. It conducts and judges nothing itself.

- [x] 2.1 Create `skills/mf-converge/SKILL.md` with `name` / `description` frontmatter and the required
  `change-id` parameter. *Verify:* `head -4` shows the frontmatter; the body names the halt on a missing id.
- [x] 2.2 Write the five preconditions, each halting and naming what is missing: tree clean · **every
  `## Progress` box ticked** · derived range non-empty · `.minions/minions.toml` present with a non-empty `gate`
  array · gate green before round 1. *Verify:* five preconditions are enumerated, each with its halt.
- [x] 2.3 Write the freeze step: derive `base` via `git merge-base` against the default branch, write
  `.minions/findings/<change-id>_diff.patch`, print base · head · commit count · files changed, and **halt if
  `base` equals `HEAD`**. *Verify:* the file names the patch path, the printed fields and the empty-range halt.
- [x] 2.4 Write the fan-out: **two** fresh read-only subagents (review, security — simplify already ran in
  `mf-build`), dispatched in parallel, each given the range, the patch path and its own findings path; each scopes
  its skill to the range, falls back to reading the patch only if that scope was empty or wrong, and **states in
  its Summary which it did**. Include the three engine overrides: never `--fix`, never `--comment`, never `ultra`
  (user-triggered and billed, not agent-launchable). *Verify:* both roles, the fallback rule, the declare-scope
  rule and the three overrides are present.
- [x] 2.5 Write the findings-file contract: the exact frontmatter (`type` · `plan` · `project` · `branch` ·
  `head` · `reviewed` · `round` · `open_blocking` · `verdict`), the two severity vocabularies and which station
  owns which, `open → fixed → verified` with only the checker promoting, and the append-only `## Resolution log`.
  *Verify:* the frontmatter block in the file lists all nine keys.
- [x] 2.6 Write the two fail-closed rules as the conductor's own reads, from disk and never from a station's
  report: **a missing findings file is not clean**, and **an empty review is not clean** — a station reporting
  zero files reviewed writes `changes-requested` with a scope-resolution finding, and the conductor compares the
  reported count against the count it printed in 2.3. *Verify:* both rules are stated, and the count comparison
  is described as the conductor's action.
- [x] 2.7 Write the fix station: one subagent, clears open blocking findings to a green gate, flips per-finding
  status `open → fixed` with a note, touches **no** frontmatter counter and never writes `verdict: clean`, carries
  nits to `.minions/<version>_backlog.md`, commits staged by name with the trailer. Then re-freeze the patch to
  the **scoped** range `<previous head>..<new head>`. *Verify:* the file states the counter prohibition and the
  scoped re-freeze.
- [x] 2.8 Write the verify round (same two roles, fresh subagents, `round ≥ 2`), the **cap of 3** with a halt that
  leaves every findings file as it stands and names the still-open blockers by id, and the final report (verdicts
  quoted from disk · every blocking finding's end state · nits carried · the gate's exit code re-run at the end ·
  what it did **not** do: archive, fold, tag, merge, push). *Verify:* the cap, the halt contents and the five
  report items are present.
- [x] 2.9 Write the `Never` block: never review in your own context — if subagents cannot be dispatched, **halt**
  and say so; never edit a findings file yourself; never weaken the gate; never archive, fold, tag, merge or push.
  *Verify:* the block names all five.

## 3 — `mf-backlog-export` — the human-invoked vault bridge

The only skill that touches anything outside the repository, and the only one that commits nothing.

- [x] 3.1 Create `skills/mf-backlog-export/SKILL.md` with frontmatter, and declare the vault path an **explicit
  parameter with no default** — the skill resolves nothing, searches for nothing, and halts if either path does
  not resolve. *Verify:* the file names the parameter and the halt, and `grep -c '~/' skills/mf-backlog-export/SKILL.md`
  returns 0.
- [x] 3.2 Write the classification step — **moot** (subject deleted or superseded, closed with what removed it) ·
  **next release** · **future / unversioned** — with the rule that no item is silently dropped and no version
  commitment is invented. *Verify:* three classes, each with its stated reason requirement.
- [x] 3.3 Write the carry-whole rule (id · severity · source role · `path:line` · the defect · the suggested fix)
  and the no-duplicate rule (link, never restate — two copies drift). *Verify:* both rules are present with their
  reasons.
- [x] 3.4 Write the empty-the-file step: remove every list line, never delete the file, never leave a ticked list,
  and replace the list with a prose record of where each item went. *Verify:* the file states that a ticked item
  still blocks.
- [x] 3.5 Write the two verification greps (zero list lines in the repo-side file; the new block present in the
  vault) and the guardrails: never write a vault path into a tracked repository file, and **commit nothing**.
  *Verify:* both greps and both guardrails are present.

## 4 — `mf-release` — verify, fold, archive, tag, stop

The strongest prohibition in the set, and the step with the least prior evidence — `v0.9`'s fold was a no-op.

- [x] 4.1 Create `skills/mf-release/SKILL.md` with frontmatter and the required `change-id` parameter.
  *Verify:* `head -4` shows the frontmatter; the body names the halt on a missing id.
- [x] 4.2 Write the preconditions, each a halt naming what is missing and who owns it: gate **re-run** in this
  session · review and security `verdict: clean` with every blocking finding `verified`, not merely `fixed` · **a
  missing findings file is not clean**, and **simplify is declared out by name** (it produces no file by design,
  `design.md` — D6) · the deferred-work file holds no list line whatever its checkbox state, a missing file
  passing · the version line aligned (tag absent, `## [Unreleased]` has real entries) · tree clean · the spec
  binding green **before** the fold. *Verify:* seven preconditions enumerated; simplify named as excluded.
- [x] 4.3 Write the fold: `ADDED` appends · `MODIFIED` **replaces the whole requirement matched by title**, byte
  for byte · `REMOVED` deletes · capability preamble prose preserved verbatim and flagged for a hand-edit if the
  change invalidated it · a `skip_specs` change folds nothing but **still archives**. *Verify:* all three
  operations, the preamble caveat and the skip-specs branch are present.
- [x] 4.4 Write verify-after-fold then archive, and state that **fold, verify and archive land in the same
  commit** — the binding check ignores the archive, so an archived delta's keys stop resolving and every marker
  bound to them dangles. Red post-fold check → **do not archive, halt**. *Verify:* the ordering, the one-commit
  rule and its reason are stated.
- [x] 4.5 Write the version-line cut (changelog heading and a fresh empty `## [Unreleased]`; version file if the
  repo keeps one; no new changelog prose written here), the one release commit and the annotated tag.
  *Verify:* the file forbids writing new changelog prose at release.
- [x] 4.6 Write the closing: re-run the gate on the released tree, then **stop** — report each precondition and
  how it was verified, what the fold changed or that it was a no-op and why, the release commit and tag, and
  **what it did not do: merge, push** — naming both as the human's, with the squash-caveat note. *Verify:* the
  file names merge and push as the human's and performs neither.

## 5 — The install path, and the README catches up

- [x] 5.1 Add `install-skills` and `uninstall-skills` targets to `Makefile`, with their `.PHONY` entries,
  symlinking each `skills/mf-*` directory into the operator's personal skills directory. The `gate` target is not
  touched. *Verify:* `make install-skills` creates four live symlinks; `make uninstall-skills` removes exactly
  those and strands none; `git diff Makefile` shows no change inside the `gate` target.
- [x] 5.2 Run the portability check over all four skills: no absolute path, no `~/` expansion, no path outside the
  repository the skill is invoked in (`design.md` — D15). *Verify:* the grep returns zero hits across
  `skills/**/SKILL.md`.
- [x] 5.3 Add a short `README.md` section naming the four skills and the two install commands, pointing at the
  skills themselves rather than restating what they do. *Verify:* the section names all four skills and both
  targets.
- [x] 5.4 Correct `README.md`'s `## Status` section, which still says v0.7.0 is the current release and the v0.8
  line is in progress. *Verify:* `grep -n 'v0.7.0 is the current release' README.md` returns nothing.

## 6 — `CLAUDE.md` declares the two lines

Additive only. The gate section, the seams and the guardrails are untouched.

- [x] 6.1 Add one short paragraph naming the two lines: `orchestrator/` + `prompts/` implement the automated
  line; `skills/mf-*` is the human-invoked line that ships releases; the duplication (one review axis, two
  rubrics) is deliberate and declared, not resolved. *Verify:* the paragraph names both lines and the word
  *declared*.
- [x] 6.2 Add `skills/` to the **Layout** section. *Verify:* the layout section names `skills/` and what it
  holds.
- [x] 6.3 Confirm nothing else moved. *Verify:* `git diff CLAUDE.md` shows no change to the gate command list,
  the engineering conventions, *How a change is cut here*, or the guardrails.

## 7 — `skills/` becomes the tenth scanned root

The delta this change carries, and the only test edit in it.

- [ ] 7.1 Add `"skills"` to `_SCANNED` in `tests/test_conventions.py` and update the verbatim tuple asserted in
  **both** scan tests to the same ten entries. *Verify:* `uv run pytest -q tests/test_conventions.py` is green and
  both assertions name ten roots.
- [ ] 7.2 Update both reintroduction tests to plant every needle in **all ten** roots and assert the full
  ten-entry hit list, so no root is asserted that a needle cannot bite in. *Verify:* `uv run pytest -q
  tests/test_conventions.py` is green, and temporarily removing `"skills"` from the tuple turns it red.
- [ ] 7.3 Confirm the four shipped skills are clean under the widened scan — all fourteen retired needles at zero
  hits across `skills/`. *Verify:* `uv run pytest -q` is green with `skills/` inside the scan.
- [ ] 7.4 Run the full gate and the spec binding. *Verify:* `make gate` exits 0, and
  `uv run python -m orchestrator specs check --strict` is green with the delta in place (no scenario key changes,
  so no marker moves).
