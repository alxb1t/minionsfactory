# Design — 0009-planning-line

## Context

See `proposal.md` — *Why*. What this section adds is the state the approach has to fit.

**This document is the record.** v0.9 stops keeping a separate planning artifact outside the repository: the
grilling that settled this change was a conversation, and what survives of it is here, in `proposal.md`, and in
`tasks.md`. That makes the *rationale* load-bearing rather than optional — a decision recorded without the
measurement behind it is a decision the next version re-derives. Every claim below that could have been assumed
was instead measured against this tree with **`@fission-ai/openspec@1.11.0`** on 2026-08-29 and 2026-08-30, and the
measurement is written next to the decision it settled.

Three constraints shape everything here. The repository keeps **its own** scenario-to-test binding check
(`orchestrator/specs.py`) and **its own** release fold (`orchestrator/release.py`) — these are deliberate
deviations from any portable line and were not up for removal. The **gate array** in `.minions/minions.toml` is
mirrored in four places that must agree command-for-command, so touching it is never a one-file edit. And
`docs/sdd.md` is written **above the tool layer** — it names stations and disk artifacts, never who runs them, and
assumes no installed package.

## Goals / Non-Goals

**Goals**

- A planning line assembled entirely from tools maintained elsewhere: `grilling` for the decisions, the OpenSpec
  CLI for scaffolding, authoring instructions and validation.
- `openspec validate --all --strict` exits 0 over this tree, so the spec tree is legible to a checker that is not
  ours.
- The repo's contract stated where each reader will meet it, and stated **once** in each place.
- `docs/sdd.md` describing the line actually run.

**Non-Goals**

- **Writing any skill.** The version's premise is that a hand-maintained planning surface is the debt v0.8 paid off.
- **Putting `openspec validate` in the gate** — a v0.10 question (see *Decisions*).
- **Pinning or vendoring the CLI**, or introducing a second runtime manifest.
- **Adopting the wider community skill set** (`code-review`, `tdd`, `diagnosing-bugs`, `triage`) or writing the
  `docs/agents/` adapter they read. Whichever future version adopts one of them writes it then, for a reason it can
  name.
- **Changing the execution loop.** The fan-out's blindness, the producer/checker asymmetry and the findings
  contract are shipped, spec'd and tested; nothing here touches them.

## Decisions

### 1. The line is `grilling` → `openspec instructions <artifact>` → author

Three tools were on the table: `grilling`, `to-spec`, `to-tickets`. Only the first survives.

**`to-spec` is not adopted.** Read against the four-artifact contract it collides in four places, and the adapter
that would resolve them would consume most of the skill:

| `to-spec` says | this repo requires |
| --- | --- |
| a fixed template (Problem Statement · Solution · **a long list of user stories** · Implementation Decisions · Testing Decisions) | the structure `openspec instructions <artifact>` emits |
| *"do NOT include specific file paths"* | the approach names the actual files it touches (`docs/sdd.md`, Part II) |
| one `spec.md` | one `spec.md` per capability directory — a root one is a malformed change |
| publish to an issue tracker, apply `ready-for-agent` | write the four artifacts; there is no tracker and no label |

What is left after the overrides is a single instruction — *synthesize the conversation, do not re-interview* —
which costs nothing to give directly. Four overrides to salvage one instruction is negative value, and the adapter
would exist chiefly to disarm the skill it adapts.

**One idea in `to-spec` is not redundant** and is kept: *sketch the seams you will test at; prefer existing seams;
use the highest seam available.* `openspec instructions design` has no equivalent, and this repository lives on its
seams (the `Provider` Protocol, the `run_gate` seam). It survives as a `design`-artifact rule in `config.yaml` —
the idea kept, the skill dropped.

**`to-tickets` is not adopted**: `openspec instructions tasks` owns phase decomposition, and this repo's phases in
`tasks.md` *are* the tickets.

**No `docs/agents/` adapter.** Measured: `grilling` contains **zero** references to `docs/agents/`, `CONTEXT.md`
or an issue tracker — the adapter would do nothing for the only skill in the line. Its real consumers are
`code-review` (reads `issue-tracker.md`) and the `CONTEXT.md`/ADR vocabulary in `tdd`, `diagnosing-bugs`,
`codebase-design`, `triage` and others — none of which this version adopts. **Cost accepted:** running one of those
skills here will send you to `/setup-matt-pocock-skills`.

### 2. `config.yaml` `rules:`, not a forked schema

`openspec/config.yaml` supports `context:`, per-artifact `rules:` and `operations.guidance`; `openspec schema *` is
flagged **experimental** by the CLI. A fork buys template control and control of the artifact dependency graph.
Neither is needed: the `spec-driven` graph is already `proposal → {specs, design} → tasks`, exactly this repo's
four-artifact contract, and every override below is a *rule*, not a template. Take the fork only when a future
version needs a fifth artifact or a different graph.

### 3. Where the contract is taught — a strict split, so nothing is restated twice

Four restatements of one method is how the deleted rubrics drifted from the role prompts. The split is by *what
each file is for*, and it is the rule for anything added later:

- **`openspec/config.yaml`** — what must be **injected into artifact authoring**. `context:` is a **pointer** to
  `docs/sdd.md` and `CLAUDE.md`; `rules:` carry only the non-derivable overrides.
- **`CLAUDE.md`** — the **repo fact**: this is how a change is cut here, with which commands, against which CLI
  version. Read by every role, always.
- **`docs/sdd.md`** — the **method**, tool-neutral. It never names the OpenSpec CLI or `.openspec.yaml`.

### 4. `openspec validate` stays out of the gate array

Three shapes were weighed. **In the array:** it puts node in CI against a `python-uv` readiness profile that
describes no node toolchain, and moves four prose mirrors that `docs/sdd.md` makes a **required** readiness
criterion. **In the test suite:** a pytest shelling out to the CLI reaches the gate with no mirror churn, but makes
a deliberately hermetic suite depend on an external binary, and a test that skips when the binary is absent guards
nothing. **Out of the gate:** validation is phase acceptance and a release precondition, run and observed.

Out of the gate, chosen. Adopting an external CLI and making it blocking in the same version is the coupling the
method warns about; the repo's own `specs check --strict` remains the binding authority. Revisit at v0.10 with a
version of evidence.

### 5. The CLI is recorded, not pinned

Measured at `@fission-ai/openspec@1.11.0`, installed globally via npm and resolved on `PATH`. Because nothing in
CI runs it (decision 4), a moving CLI cannot turn anything red — it can only hand a future author different
authoring instructions. A `package.json` with a devDependency would buy reproducibility with no consumer, add a
second runtime manifest to a `python-uv` repository, and trip the dependency approval gate. The version is
therefore stated in `CLAUDE.md` as a measured fact and kept current by hand.

### 6. Zero-delta is `skip_specs: true`, and it retires the `specs/README.md` precedent

This is the collision that forced a convention change, and it was measured rather than reasoned:

- `specs/README.md` alone → `✗ [ERROR] file: Change must have at least one delta`, exit 1.
- `skip_specs: true` **plus** `specs/README.md` → `✗ [ERROR] file: skip_specs is set in .openspec.yaml but spec
  files exist under specs/`, exit 1.
- `skip_specs: true` plus `specs/.gitkeep` → **exit 0**, `Change '…' is valid`.

The two mechanisms are mutually exclusive. `orchestrator/state.py` requires only that `specs/` **exist**, so a
`.gitkeep` satisfies the four-artifact contract and keeps the directory tracked, which an empty directory cannot be.
`.openspec.yaml` therefore becomes a **tracked** fifth file in a change directory — a convention every future change
inherits, and the reason `docs/sdd.md` gains a clause admitting tooling metadata beside the four artifacts.

Manufacturing a requirement to produce a delta was rejected outright: forbidden by `docs/sdd.md` and by the artifact
instructions in the same words.

### 7. The tombstone is deleted, and the convention with it

`openspec/specs/change-state/spec.md` declared that it held no requirement and existed to record that its contents
had been deleted. `openspec validate --strict` refuses it — *"Spec must have at least one requirement"* — and while
it stands, `validate --all` can never be green, which forecloses decision 4's revisit entirely.

Nothing machine-checkable holds the file: it contributes zero scenario keys, so `specs check --strict` cannot see
it, and no test reads it. Its only load-bearing content is one forward pointer — the reader that reconstructs
where-are-we is spec'd under `sdd` — and that sentence lands in `sdd`'s new `## Purpose`, which is where the reader
it names actually lives. The deletion record it pointed at already exists in the `## REMOVED Requirements` blocks
of `changes/archive/0005-change-cutover/` and `changes/archive/0007-pm-side-process-standard/`, and in two
`CHANGELOG.md` entries.

The convention is retired rather than worked around: a directory that costs maintenance to say what the archive
says better is not worth the one thing standing between this tree and a portable validator.

### 8. `tasks.md` layers the two formats — the collision that would have shipped a broken change

`openspec instructions tasks` prescribes, in its words *"Follow the template below exactly"*, headings of the form
`## 1. Group` with items `- [ ] 1.1 Task description`. This repository's reader is stricter:

```python
_PROGRESS_ITEM = re.compile(r"^- \[([ xX])\]\s*(\d+)\s*[—–-]+\s*(.+?)\s*$")
```

It reads **only** the section under `## Progress`, closing at the next `## `, and requires `- [ ] N — Title`: a
single integer and a dash. `1.1` does not match. An author following the OpenSpec template exactly produces a
`tasks.md` that parses to **zero phases** — which `docs/sdd.md` calls malformed and the orchestrator refuses at
read time. This is the only collision found that would have shipped a change the build loop cannot read.

The resolution layers them, and works by design rather than by luck: `## Progress` carries this repo's phase list,
each phase then gets its own `## N — Title` section, and OpenSpec-style `- [ ] N.M` sub-tasks live **inside** those
sections, where `parse_progress` provably never sees them — its docstring names that exact defence. Two facts make
this safe rather than a fudge: OpenSpec's **validator does not enforce its own template** (`0008-surface-collapse`
validates clean unmodified in this format), and its "apply phase" progress tracking is machinery this repo does not
use. They agree on the part that matters — every task states how completion is verified.

Changing the parser instead was rejected: it is `orchestrator/` code plus tests, which forfeits doc-only, and it
would break the format every archived change is written in.

### 9. `docs/sdd.md` — four edits, all consequences of deletions already made

The page is tool-neutral and stays so; none of these names a tool.

1. **The feasibility verdict** — `feasible` / `feasible-with-caveats` / `needs-precursor` /
   `infeasible-as-specified` was emitted by `mf-blueprint`, deleted in v0.8. The vocabulary is kept, because
   `needs-precursor` and `infeasible-as-specified` are *halts* and a criteria list with no halt vocabulary cannot
   stop a bad change. The **grill station** now emits it, recorded in `design.md`.
2. **The N-A sentence** names its mechanism tool-neutrally: the absence is declared in the change's metadata, not
   by a placeholder file under `specs/`.
3. **A clause admits tooling metadata** beside the four artifacts, outside the contract — so a reader who finds a
   fifth file in a change directory does not read it as malformed.
4. **The Grill and Cut paragraphs are rewritten together.** They described a record kept outside the repository,
   and a cut change checked back against it by a reader who did not write it — the `mf-inspect` conformance pass,
   also deleted in v0.8. With the change artifacts themselves being the record, "checked back against the record"
   is circular. What survives is the part that works and has a receipt: **internal consistency across the four
   artifacts, every delta scenario tracing to an acceptance, and the design re-checked against the real code.**
   `0007`'s B7 — a `proposal.md` requirement reaching no phase in `tasks.md`, which nearly shipped a live vault
   grant — was caught by exactly that internal check, so the deletion loses no proven catch.

**Not touched:** the fan-out's blindness, *"no station verifies its own work"*, and the producer/checker asymmetry.
Those are shipped behaviour, spec'd under `fanout` / `converge` / `release` and encoded in six role prompts;
editing them out of the page would make it contradict the code, which is the defect class this project has already
paid to fix once.

### 10. `CLAUDE.md`'s three obsolete vault sentences are corrected in the same pass

Grilling now runs **in the repository**, which falsifies three statements: the upstream decision record the human
keeps in a vault, *"any PM-side tooling runs from the vault, out of band"*, and the rationale attached to the
absolute-path guardrail. The **rule** stays — never commit a real absolute path — and so does the v0.7 containment
invariant, *everything a run reads or writes is inside the repository*, which is about the orchestrator rather than
the vault and is bound by `fanout:findings-path:no-external-root-argument`.

They are corrected in the phase that already opens the file: shipping a version that makes three of its own
sentences false, while editing that file, is precisely the drift this project keeps paying to remove.

## Risks / Trade-offs

- **The capability deletion has no delta representation** → `## REMOVED Requirements` removes requirements and
  `change-state` holds none. *Mitigation:* the deletion is a hand-edit recorded in `tasks.md`, landing in the same
  commit as the `## Purpose` additions, with `openspec validate --all --strict` exiting 0 as its only
  machine-checkable trace. The release fold is a no-op over it, which is correct.
- **`## Purpose` has a length floor** → `--strict` promotes `⚠ overview: Purpose section is too brief (less than 50
  characters)` to a failure. *Mitigation:* treated as authoring work across ten specs, not heading insertion; the
  phase's acceptance is the command, so a short one fails the phase.
- **`.openspec.yaml` is a new tracked file in every change directory** → a convention introduced here that all
  future changes inherit. *Mitigation:* named in `CLAUDE.md` and admitted by `docs/sdd.md`'s new clause, so it is a
  declared convention rather than residue.
- **An unpinned CLI can change its authoring instructions under us** → *Mitigation:* it is out of the gate, so it
  can never turn CI red; the measured version is recorded in `CLAUDE.md`, and a future divergence is visible as a
  changed instruction rather than a silent failure.
- **Community engineering skills will misfire here** → no `docs/agents/`, no `CONTEXT.md`. *Mitigation:* accepted
  deliberately; the exit ramp is cheap and belongs to whichever version adopts one of those skills.
- **The tools were evaluated by reading their sources, not only by running them** → a run might surface friction a
  read does not. *Mitigation:* this change is itself the first real run of the adopted line, and decision 8 — the
  one collision that would have shipped a broken change — was found precisely that way.

## Migration Plan

Three phases, each independently committable and each ending on a green gate; ordering is not forced by any
dependency, so it runs wiring → tree → method page, which is also the order the CHANGELOG reads best in.

1. `openspec/config.yaml` + `CLAUDE.md` — how a change is cut here, and the three vault corrections.
2. The spec tree, whole — ten `## Purpose`, `sdd`'s `## Requirements`, `change-state/` deleted.
3. `docs/sdd.md` — the four edits.

**Rollback** is a plain revert at any phase: nothing under `orchestrator/` or `tests/` changes, the gate array is
untouched, and no dependency is added. Reverting phase 2 restores a tree that fails `openspec validate --all
--strict` and passes everything this repo's own gate runs, which is exactly the state before this change.

## Verdict

**`feasible-with-caveats`** — three doc-only commits, no dependency, no CI change, no orchestrator or test edit.
Both unknowns that could have sunk it were measured rather than assumed, and both have verified green exits. The
caveats are the first three risks above, carried rather than resolved.

## What the run found

Recorded because it is the deliverable the version was cut for, and because a claim that the artifacts were
produced by the line is not something disk can prove.

- **Two of the three candidate tools do not fit** and are not adopted (decision 1), which is a cheaper finding than
  a hollowed-out adoption would have been.
- **The CLI tolerates every local extension** it was tested against — `version:` frontmatter, `- **Key:**` /
  `- **Layers:**` scenario bullets, prose `tasks.md`. `0008-surface-collapse` validates clean unmodified.
- **The CLI's fold and `orchestrator/release.py`'s fold agree** — run over a spec `release.py` had already folded,
  the CLI reported *"Specs already in sync; no files changed."*
- **`--all` covers the living specs and the active change, never the archive** — measured at 12 items in this tree.
  The historical record needs no backfill.
- **`skip_specs` does not stall the artifact graph** — `openspec status` reports `[~] specs (skipped)` and unblocks
  `tasks` normally.
- **The instructions are authority on structure and wrong on format** (decision 8). A tool that says *"follow the
  template exactly"* and is not enforced by its own validator is a tool whose instructions must be overridden in
  writing, which is what `config.yaml`'s `rules:` are for.
