# Tasks — 0009-planning-line

**Change:** `0009-planning-line` · **Version:** v0.9 · **Build mode:** hand-authored, one phase per commit.

Every commit carries a `Change: 0009-planning-line` trailer, contiguous with any `Co-Authored-By:`. Every phase
ends on a green gate (`make gate`, or the six commands in `.minions/minions.toml`) and appends its entry under
`## [Unreleased]` in `CHANGELOG.md`. A phase is finished by a commit **and** a ticked box — either alone is not an
advance.

`## Progress` below is what `orchestrator/state.py` reads; the `N.M` checkboxes inside each phase section are
sub-tasks for the builder and are invisible to that parser (`design.md` — Decisions 8).

## Progress

- [ ] 1 — `openspec/config.yaml` and `CLAUDE.md`: how a change is cut here
- [ ] 2 — The spec tree validates under a portable checker
- [ ] 3 — `docs/sdd.md` describes the line actually run

---

## 1 — `openspec/config.yaml` and `CLAUDE.md`: how a change is cut here

Two files, one subject: where the contract is taught. The vault corrections ride here because this phase already
opens `CLAUDE.md` and the sentences are false as of this version.

- [ ] 1.1 Write `openspec/config.yaml` — keep `schema: spec-driven`, add `context:` as a **pointer** to
  `docs/sdd.md` and `CLAUDE.md` (never a restatement of either). *Verify:* the file parses as YAML and
  `openspec status --change 0009-planning-line` still resolves the schema.
- [ ] 1.2 Add per-artifact `rules:` carrying only the non-derivable overrides: four artifacts always; the approach
  names the files it touches; one `spec.md` per capability directory, never one at the root; a zero-delta change
  declares `skip_specs: true` with `specs/.gitkeep`; `tasks.md` opens with a `## Progress` checklist in
  `- [ ] N — Title` form with `N.M` used only for sub-tasks inside phase sections; and on the `design` artifact,
  sketch the seams the work will be tested at, preferring existing seams and the highest one available.
  *Verify:* `openspec instructions proposal --change 0009-planning-line` and `… tasks --change …` each emit the
  rules for that artifact.
- [ ] 1.3 Add a **How a change is cut here** section to `CLAUDE.md`: `openspec new change <NN-slug>`; author
  `proposal.md` (with `version: vX.Y` frontmatter, which this repo's reader requires and the CLI does not),
  `design.md` and `tasks.md` against `openspec instructions <artifact>`; `skip_specs: true` + `specs/.gitkeep` for
  a zero-delta change; finish with `openspec validate <id> --strict`. Name the measured CLI version
  (`@fission-ai/openspec@1.11.0`) and point at `docs/sdd.md` for the method rather than restating it.
  *Verify:* the section exists, names all four commands, and `grep -n "/Users/\|/home/" CLAUDE.md` returns nothing.
- [ ] 1.4 Correct the three obsolete vault sentences in `CLAUDE.md` — the upstream decision record, *"any PM-side
  tooling runs from the vault, out of band"*, and the rationale attached to the absolute-path guardrail. **Keep**
  the guardrail rule itself and the v0.7 containment invariant (*everything a run reads or writes is inside the
  repository*). *Verify:* `grep -n -i vault CLAUDE.md` returns only the containment invariant and the guardrail
  rule; `uv run pytest -q tests/test_conventions.py` is green (no retired needle introduced).
- [ ] 1.5 Append the phase entry under `## [Unreleased]` in `CHANGELOG.md`. *Verify:* the entry names the change id
  and describes the split between `config.yaml`, `CLAUDE.md` and `docs/sdd.md`.
- [ ] 1.6 Run the gate and commit. *Verify:* all six commands in `.minions/minions.toml` exit 0; the commit carries
  the `Change: 0009-planning-line` trailer.

## 2 — The spec tree validates under a portable checker

One commit, deliberately whole: splitting it produces a first phase whose only honest acceptance is *"still red,
for one remaining reason"*, and the outcome this phase exists for is a single binary.

- [ ] 2.1 Add a `## Purpose` section to each of the ten living capability specs — `build-loop`, `cli`, `converge`,
  `diff`, `fanout`, `gate`, `provider`, `release`, `sdd`, `status`. Each must be **at least 50 characters** of real
  prose; `--strict` fails a shorter one with *"Purpose section is too brief"*. Most capabilities already open with a
  preamble paragraph that can become the Purpose. *Verify:* `openspec validate --specs --strict` reports no
  `overview` error or warning for any of the ten.
- [ ] 2.2 Add the `## Requirements` heading to `openspec/specs/sdd/spec.md`, which today jumps from its title
  straight to `### Requirement:`. *Verify:* the heading precedes the first requirement and `specs check --strict`
  still resolves every `sdd:` key.
- [ ] 2.3 Carry the tombstone's one load-bearing sentence into `sdd`'s new `## Purpose` — that the reader which
  reconstructs where-are-we is spec'd here — then delete `openspec/specs/change-state/` entirely. *Verify:* the
  sentence is present in `sdd`'s Purpose before the directory is removed, and the deletion lands in this same
  commit.
- [ ] 2.4 *Verify the phase:* `openspec validate --all --strict` exits **0** over 11 items (ten specs plus this
  change), **and** `uv run python -m orchestrator specs check --strict` exits **0**. Both, or the phase is not done.
- [ ] 2.5 Append the phase entry under `## [Unreleased]`, recording that the tombstone **convention** is retired
  and not merely applied differently to one file. *Verify:* the entry names both the deletion and the convention.
- [ ] 2.6 Run the gate and commit. *Verify:* all six commands exit 0; trailer present.

## 3 — `docs/sdd.md` describes the line actually run

Four edits, all consequences of deletions this project already made. The page stays **tool-neutral**: none of these
may name the OpenSpec CLI, `.openspec.yaml` or `skip_specs`.

- [ ] 3.1 Rewrite the **Grill** and **Cut** paragraphs together. Grilling settles decisions against a person; the
  change artifacts **are** the record; the check that follows the cut is internal — consistency across the four
  artifacts, every delta scenario tracing to an acceptance and back, and the design re-checked against the real
  code. Drop *"nothing asked for is dropped, nothing unauthorized is added"*, which needs an intent document this
  repository does not hold. *Verify:* neither paragraph refers to a record kept outside the repository, and the
  three surviving checks are each stated.
- [ ] 3.2 Part II — the feasibility axis now ends in a verdict emitted by the **grill station** and recorded in the
  change's `design.md`. Keep all four values; `needs-precursor` and `infeasible-as-specified` are halts and the
  vocabulary is why the axis can stop a change. *Verify:* the four values survive and no deleted stage is named.
- [ ] 3.3 Rewrite the N-A sentence so the absence of a delta is **declared in the change's metadata**, not by a
  placeholder file under `specs/`. *Verify:* the sentence names no tool and no filename.
- [ ] 3.4 Add one clause admitting that tooling may leave metadata beside the four artifacts without making the
  change malformed, and that such metadata is outside the contract. *Verify:* the clause is tool-neutral.
- [ ] 3.5 *Verify the page:* `grep -n -i "openspec cli\|\.openspec\.yaml\|skip_specs\|npm\|node" docs/sdd.md`
  returns nothing, and `uv run pytest -q tests/test_conventions.py` is green — `docs/` is inside the scanned roots
  and all fourteen retired needles must stay at zero hits.
- [ ] 3.6 Append the phase entry under `## [Unreleased]`. *Verify:* the entry states that all four edits correct
  claims about stages this project deleted, and that the execution loop's blindness was deliberately left alone.
- [ ] 3.7 Run the gate and commit. *Verify:* all six commands exit 0; trailer present; `openspec validate --all
  --strict` still exits 0.
