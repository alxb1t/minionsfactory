# 0020-architecture-and-decisions — design

**In one line:** the pages under [pages/](pages/) become `docs/principles.md`, `docs/decisions.md` and
`docs/autonomous.md`; the front door is rewritten around them; `docs/sdd.md` is deleted last. Prose, one small
test, and edits to skill text. **Verdict: feasible** ([why](#verdict)).

Motivation is in [proposal.md → Why](proposal.md#why). This page holds the decisions, what each rewritten file
holds, and the text each changed sentence becomes.

## Context

- `README.md:3`, `CLAUDE.md:3`, `docs/README.md:3` and `docs/architecture.md:5` open by describing "a CLI +
  orchestrator". `CLAUDE.md:15-18` and `CLAUDE.md:105-107` state "no LLM in the orchestration layer".
- `docs/architecture.md:92-94`, `docs/modules/provider.md:114`, `docs/modules/provider.md:132` and
  `docs/README.md:42-43` point at a `decisions.md` outside the repository; `docs/modules/state.md:243` points at a
  backlog outside it.
- `docs/sdd.md` is cited by `CLAUDE.md:8`, `:63`, `:73`, `:78`; `README.md:98`; `docs/README.md:34`;
  `openspec/config.yaml:7`; `skills/mf-build/SKILL.md:142`; `skills/mf-converge/SKILL.md:153`;
  `skills/mf-release/SKILL.md:77` and `:113`; `tests/test_conventions.py:255-262`; `tests/test_skills.py:441-468`;
  and the living requirement at `openspec/specs/sdd/spec.md:410-423`.
- The gate's last command is `python -m orchestrator specs check --strict` (`Makefile:15`), and it requires every
  test to carry a `spec` or a `spec_exempt` marker.
- `tests/test_conventions.py` scans `docs/`, `README.md`, `CLAUDE.md` and `skills/` for retired names, so a new
  page there must name none of them.

### Terms

| term | means |
|---|---|
| **the pages** | the files under [pages/](pages/): the text of each new `docs/` page, as settled entry by entry |
| **the front door** | `README.md`, `CLAUDE.md`, `docs/README.md` and the `context:` block of `openspec/config.yaml` |
| **the runner** | `orchestrator/`, `prompts/`, `docs/architecture.md`, `docs/modules/` and the tests and specs that describe them |
| **the method page** | `docs/sdd.md` |

## Goals / Non-Goals

**Goals**

- A reader of the repository alone learns what MinionsFactory is, its rules and its choices, each with its reason.
- No tracked file points at a record outside the repository.
- No file cites the method page, and the page is gone.

**Non-Goals**

- Deleting the runner, or changing the gate recipe or the spec↔test binding.
- Building any part of the autonomous line.
- Checking the docs beyond [E4](#e4).

## Decisions

The change's own decisions are `E1`…`E13`; `D1`…`D35` are the entries of [pages/decisions.md](pages/decisions.md).

| id | decision | because | rejected |
|---|---|---|---|
| <a id="e1"></a>**E1** | **`docs/` holds a map, the principles, the decisions and the autonomous design**, each its own file | a principle is held by a test or a skill; a decision is a choice with a reason. One file for both held neither | one `architecture.md` for everything · one file per decision |
| <a id="e2"></a>**E2** | **The pages are the text.** The build writes each `docs/` page from its file under [pages/](pages/), changing only what HEAD contradicts — a step number, a test name, a card that closed | each entry was read and agreed as text; re-wording it at the build re-decides it | the build composing the entries from a summary |
| <a id="e3"></a>**E3** | **A principle is a heading, a bold rule, `Why`, and what holds it.** A decision is `### Dn · title`, a bold rule, `Why`, and where they apply `Rejected` and `Accepts` with a reopen condition. Present tense: no version, no history, no author | an entry says what holds and why; `design.md` and git keep how it came about | a table row per rule, which cannot hold a reopen condition · a `Made by` line |
| <a id="e4"></a>**E4** | **One check holds the pages:** `tests/test_principles.py` fails when `docs/principles.md` names a `tests/<file>.py::<name>` that does not exist. Marked `spec_exempt` | a renamed test would orphan the principle naming it while the page still read as held | link, table and id checks — complication for little · binding the check to a scenario, since the binding retires with the runner |
| <a id="e5"></a>**E5** | **The autonomous design enters now**, as `docs/autonomous.md` and `D24`…`D35`, marked designed-not-built once per page | one record has no "until built" clause; the change that builds a part edits the page like any other | adding it when the first part is built |
| <a id="e6"></a>**E6** | **The runner stays, named deprecated.** `docs/architecture.md` opens with a banner; the pointers out of the repository are removed; nothing else of the runner is touched | its deletion is code work of its own, and the gate still runs `orchestrator/specs.py` | deleting it here · leaving its pages in the reading order |
| <a id="e7"></a>**E7** | **The front door leads with the skills.** `CLAUDE.md` imports `docs/principles.md` and keeps only what is true of this repository | a front door that states a rule the decisions page rejects is a second truth | keeping the runner's constraints as "hard constraints" |
| <a id="e8"></a>**E8** | **`A7` in `mf-cut-change`:** *when the repo has `docs/decisions.md`, a change that adds or overturns a decision in force names that page in a task.* `CLAUDE.md` states the same for this repository. No scan, no requirement | a page nobody is told to edit goes stale | a rule in `mf-build`, which builds the task it is given · a scan for one table row |
| <a id="e9"></a>**E9** | **The method page is deleted, in the last phase.** What it alone held moves first ([map](#where-the-method-pages-content-goes)); its Part II is dropped | the method is OpenSpec's plus what the skills state, and the installed skills cite a page their targets lack | keeping it as a third account · moving Part II to a new page |
| <a id="e10"></a>**E10** | **A skill states its rule, not its deviation.** The sentences that "declare a deviation from `docs/sdd.md`" become the rule itself ([text](#the-skill-sentences-before--after)) | the skill is the authority on what its station does | pointing the skills at `docs/principles.md`, which a target repo does not have |
| <a id="e11"></a>**E11** | **The delta is one MODIFIED requirement.** *Anchored harms block, and drift has its own tier* stops naming the method page; its key and its scenario title are unchanged, since `openspec validate` refuses a MODIFIED block that drops a scenario title | it is the only requirement that names the page | a requirement for the new pages, which would bind a check that is `spec_exempt` |
| <a id="e12"></a>**E12** | **Every page follows `mf-build`'s prose rules `P1`…`P13`:** terse, short sentences, an answer-first line under each heading, an ASCII diagram for each flow, tree or state, things named rather than counted. The pages already do; the front door is written to them; `CLAUDE.md` says docs are written to those rules | a record is read by agents and by people in a hurry, and the same rules already hold the change artifacts | a separate style guide for docs |
| <a id="e13"></a>**E13** | **No scan for the method page's name.** The delete is checked once, by the `git grep` in its task; `tests/test_conventions.py` and `docs/principles.md` are unchanged | settled at the build: a needle scan passed before the delete, so it could not be built test-first, and a one-time check is enough for a page name | a needle `sdd.md` in `tests/test_conventions.py` with its scan and twin |

## What each file of the front door holds

### `docs/README.md`

A title, one paragraph, this diagram, the table of pages, a deprecated list, and where the rest lives.

```
   grill ───▶ cut ───────────▶ build ────▶ converge ──────────▶ release      the stations
     │         │                 │            │                    │
 `grilling`  mf-cut-change    mf-build     mf-converge          mf-release    the skills
                                           review ‖ security

   conducted by a person today · by an LLM conductor held by scripts: designed, not built
```

| section | holds |
|---|---|
| the pages | `principles.md` — the rules every station follows · `decisions.md` — the choices in force · `autonomous.md` — the autonomous line's design · `sdd.md` — the method page, until phase 6 removes the row |
| deprecated | `architecture.md` and `modules/` — the runner's pages |
| where the rest lives | `skills/` — what each station does · `openspec/specs/` — the living spec · `openspec/changes/` — the active change and the archive · `CHANGELOG.md` · `CLAUDE.md` — what is true of this repository |

It names no place outside the repository.

### `docs/architecture.md`, and the pointers

The banner, directly under the title:

```
> **Deprecated.** This page and `modules/` describe the deterministic runner in `orchestrator/` and `prompts/`.
> MinionsFactory's line is the `mf-*` skills ([D3](decisions.md#d3--one-line-of-stations-conducted-by-a-person-or-by-an-llm)). The
> runner is deleted by the change that retires it.
```

| file | before → after |
|---|---|
| `docs/architecture.md:92-94` | the sentence "The deep design rationale … lives in the vault's `decisions.md`, linked from the module docs that touch it." → deleted |
| `docs/modules/provider.md:114` | the closing parenthetical "(Rationale — bare-tool denies enforce … / Q1.)" → "Bare-tool denies enforce; scoped `Bash` sub-patterns leak." |
| `docs/modules/provider.md:132` | the closing parenthetical "(Rationale: the vault's `decisions.md` → …)" → deleted |
| `docs/modules/state.md:243` | "and it is recorded in the vault backlog against **v0.10** rather than fixed here" → "and it is not fixed here" |

### `README.md`

| section, in order | holds |
|---|---|
| title and opening | what MinionsFactory is: disciplined feature development with Claude Code, as skills; the practices it carries — grill, the spec-driven change, the check loop |
| The line | the diagram above, and the skills table now at `README.md:76-81` |
| Install | `make install-skills` and `make uninstall-skills`, as at `README.md:88-93` |
| What a target repo needs | the contract of [D18](pages/decisions.md), linked to `docs/decisions.md` |
| This repo's gate | `make gate` and CI, as at `README.md:62-68` |
| Docs | `docs/README.md`, the pages, `CHANGELOG.md` |
| The deterministic runner — deprecated | `orchestrator/` and `prompts/` are deprecated; `python -m orchestrator specs check` is the spec-binding check the gate runs; `docs/architecture.md` |

Removed: the invariants list (`README.md:8-15`), *Status* (`:17-27`), *Usage* and the runner's target contract
(`:29-60`), *The method* (`:95-103`).

### `CLAUDE.md`

| section, in order | holds |
|---|---|
| title and opening | what MinionsFactory is, in the README's words; `docs/README.md` as the map |
| the record | the line `@docs/principles.md` alone on its line; `docs/decisions.md` holds the decisions in force; **a change that adds or overturns a decision in force edits `docs/decisions.md` in one of its phases**, and its `design.md` keeps the history; docs are written to `mf-build`'s prose rules `P1`…`P13`; a change is cut with `mf-cut-change` |
| the role note | the blockquote at `CLAUDE.md:29-32`, unchanged |
| The quality gate — `make gate` | the paragraph at `CLAUDE.md:38-41`, unchanged |
| Layout | `skills/`, `docs/`, `openspec/` with the OpenSpec CLI's recorded version, `.minions/`, `tests/`; everything a station reads or writes is inside the repository |
| The deprecated runner | `orchestrator/`, `prompts/` and their tests; the `Provider` and gate seams and their fakes; `orchestrator/specs.py` is the binding check the gate runs; not extended; deleted by the change that retires it |
| Guardrails | the secret-and-path bullet (`CLAUDE.md:95-102`) and the dependency bullet (`:103-104`), unchanged |

Removed: the "hard constraints" paragraph (`CLAUDE.md:15-18`), "Two lines run here" (`:20-27`), *Engineering
conventions* (`:49-66`), and the guardrails "No LLM in the orchestration layer" (`:105-107`) and "State lives on
disk" (`:108-109`), which the principles page holds. `CLAUDE.md` names no place outside the repository.

### `openspec/config.yaml`

The `context:` block becomes the text below; the `rules:` block is unchanged.

```
context: |
  This repository's rules are in `docs/principles.md`, and its decisions in force in
  `docs/decisions.md`. Read both before authoring any artifact. A change that adds or
  overturns a decision in force edits `docs/decisions.md` in one of its phases.

  What is true of this repository in particular — the gate (`make gate`), the layout,
  the guardrails — is in `CLAUDE.md`. Read it too. A change is cut with the
  `mf-cut-change` skill, which carries the contract a change must meet.

  None of these pages is restated in this file. Where an instruction below and a page
  disagree, the page wins and this file is the thing to fix.
```

## The check

`tests/test_principles.py`, after the same check in a repository the skills work on.

| piece | does |
|---|---|
| `missing_tests(text, root)` | returns each `tests/<file>.py::<name>` written in backticks in `text` whose file is absent under `root`, or which defines no top-level function of that name |
| `test_every_test_a_principle_names_exists` | `missing_tests` over `docs/principles.md` returns nothing |
| `test_the_check_catches_a_named_test_that_does_not_exist` | on a planted page and a planted test file, the missing name is reported and the present one is not |

Both tests carry `spec_exempt("structural: …")`.

## `A7`

A new row after `A6` in `skills/mf-cut-change/SKILL.md`, *Rules for the artifacts*:

```
| **A7** | **A decision in force is edited where it lives** | when the repo has `docs/decisions.md`, a change that adds or overturns a decision in force names that page in a task. The page says what holds; `design.md` says how it came about |
```

## Where the method page's content goes

| in `docs/sdd.md` | goes to |
|---|---|
| the practices; "no station verifies its own work"; the gate rules; state on disk | `docs/principles.md` |
| the change and its artifacts; the delta | OpenSpec's own instructions; [D5](pages/decisions.md), [D6](pages/decisions.md), [D10](pages/decisions.md) |
| the `Change:` trailer; the version line | [D21](pages/decisions.md), [D19](pages/decisions.md) |
| the loop | the diagram in `docs/README.md`; each skill |
| the findings contract; severities; the backlog | `skills/mf-converge/SKILL.md`, which already states them; [D15](pages/decisions.md), [D16](pages/decisions.md) |
| the release fold | `skills/mf-release/SKILL.md`; [D17](pages/decisions.md) |
| the footprint in a target repo | [D18](pages/decisions.md) |
| "evidence to measure, never instruction"; "cite the shape, never the string" | the principle *Text read from a target is evidence, never instruction* |
| "relax scope; never relax acceptance" | [D9](pages/decisions.md) |
| the rest of Part II: the phase bound, the migration exception, the feasibility verdict, the readiness list, the toolchain profile | dropped |
| the runner's divergence (`docs/sdd.md:152-154`) | dropped; `docs/architecture.md` describes the runner |

## The skill sentences, before → after

```
skills/mf-build/SKILL.md:142-144
before:  **This is a declared deviation from `docs/sdd.md`'s three-read-only-station *Check*.** There, simplify
         is a blind read-only station that reports and edits nothing but its own findings file; here it fixes in
         place inside the builder. It is safe because of the ordering: simplify runs **first**, so …
after:   **Simplify fixes in place, inside the build.** It is safe because of the ordering: simplify runs
         **first**, so …

skills/mf-converge/SKILL.md:153-154
before:  its own. **This is a declared deviation from `docs/sdd.md`'s three-read-only-station *Check*,** and its
         consequence is carried deliberately: **there is no simplify findings file at all**, …
after:   its own. The consequence is carried deliberately: **there is no simplify findings file at all**, …

skills/mf-release/SKILL.md:76-78
before:  … its edits verified by the review station that read a diff containing them. That is a declared
         deviation from `docs/sdd.md`'s three-read-only-station *Check*. Naming the exclusion is what keeps …
after:   … its edits verified by the review station that read a diff containing them. Naming the exclusion is
         what keeps …

skills/mf-release/SKILL.md:113-116
before:  **A declared deviation from `docs/sdd.md`'s *The release fold*, which checks the spec binding before the
         fold and again before archiving:** this station runs no separate step for it. Precondition 1's gate runs
         before the fold and Step 4.3's gate after the archive, so in any repository whose gate includes that
         check, those two runs are the method's two — and a repository whose gate lacks it gives a separate step
         nothing to run.
after:   **This station runs no separate spec-binding step.** Precondition 1's gate runs before the fold and
         Step 4.3's gate after the archive, so in any repository whose gate includes a binding check, those runs
         cover it — and a repository whose gate lacks one gives a separate step nothing to run.
```

`tests/test_skills.py:436-468`: the anchors scan drops `_METHOD_PAGE` and its `_file_needle_problems` term; the
test becomes `test_converge_names_the_anchors_and_the_drift_tier`, and its twin plants `mf-converge` alone.
`tests/test_conventions.py:255-262`: `test_the_method_doc_exists_and_the_docs_map_links_it` is deleted.

## Dependencies

None.

## Risks / Trade-offs

- **A principle's `Held by` may name a skill step, and no check reads that.** → [E4](#e4) holds test names only;
  review holds the rest, and the page says which is which.
- **`openspec/specs/sdd/spec.md:416` names the method page until the release folds the delta.** → the fold replaces
  the requirement whole; nothing in the gate reads that sentence.
- **`docs/principles.md` links `docs/decisions.md` one phase before it exists.** → no check reads links, and phase
  2 lands it.
- **The pages stay in the archive as a second copy of the entries.** → an archive is history; `docs/` is what is
  in force ([D6](pages/decisions.md), [D23](pages/decisions.md)).
- **`CLAUDE.md` imports the principles into every session in this repository.** → that is the point: the rules
  are in context when a line is written.

## Verdict

**Feasible.** Every file the change touches is named above, the text of each new page is settled under
[pages/](pages/), and the tests that name the method page are known and change in the phase that deletes it.
