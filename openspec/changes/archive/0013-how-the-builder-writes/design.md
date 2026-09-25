# 0013-how-the-builder-writes — design

**In one line:** three rule lists land in `mf-build` — `W` (truth), `P` (prose, shared with `mf-cut-change` by
id) and `C` (comments) — and `mf-cut-change` keeps its artifact-only rules plus the planning rules as `A`.
**Verdict: feasible** ([why](#verdict)).

Motivation is in [proposal.md → Why](proposal.md#why). This page holds 9 decisions and the full text of every
list, so the build copies rules rather than composing them.

## Context

- `mf-build` states how to build, test and commit. It says nothing about how to write a claim, a doc or a comment,
  except that a CHANGELOG entry is "1–3 short lines" (`skills/mf-build/SKILL.md:102-103`).
- `mf-cut-change` has a 16-row style table, `## How the artifacts read`, numbered `1`…`16`
  (`skills/mf-cut-change/SKILL.md:138-159`). Most of it is about any prose; three rows are about change artifacts
  only.
- `tests/test_skills.py` already holds one shared list by id — the input contract — with a scan and a twin.

### Terms

| term | means |
|---|---|
| **rule list** | a `##` section whose table rows each start with a bold id: `\| **P1** \|` |
| **W** | the truth rules — `mf-build`'s `## Rules for what you write` |
| **P** | the prose rules — `## Prose rules`, in both skills |
| **C** | the comment rules — `mf-build`'s `## Rules for code comments` |
| **A** | the artifact rules — `mf-cut-change`'s `## Rules for the artifacts` |
| **retirement** | removing or renaming a thing other text refers to: a module, a file, a term, a rule |

## Goals / Non-Goals

**Goals**

- Every rule the grilling settled is in a skill, under a stable id.
- `P` has one owner, and a copy that cannot drift silently.

**Non-Goals**

- Checking prose mechanically ([D8](#d8)).
- Changing `mf-converge`.
- Rewriting text a change does not touch ([D6](#d6)).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `mf-build` gets `## Rules for what you write`, `W1`…`W6` — FR-3's rules 1–5 and 8, text below | FR-3's evidence: false claims across isekai's tree ([E1](#evidence)) | putting them in `mf-converge`'s review — optional since v0.12, and its engines are adopted |
| <a id="d2"></a>**D2** | A retirement's search results (`W2`) go in the phase's commit body, one line per hit | the commit is on disk and travels with the change | the report (read once); a file (a new artifact) |
| <a id="d3"></a>**D3** | The 16 style rows split: 13 general rows become `P1`…`P13`, **owned by `mf-build`**, carried by `mf-cut-change` under the same ids; 3 artifact-only rows become `A1`…`A3` in `mf-cut-change`. A scan holds the `P` ids equal | one owner and a guarded copy — the input contract's pattern, already tested | copying all 16 into `mf-build` unguarded |
| <a id="d4"></a>**D4** | **Counts become names** (`P12`). Only a change's evidence and measurement tables keep counts, each with its command. `I6` changes to match, in both skills, and `mf-cut-change`'s example task stops saying "the seven criteria" | FR-3 rule 4 — counts drift; the grilling settled evidence tables as the one exception | keeping v0.11's "counts show their command" everywhere |
| <a id="d5"></a>**D5** | `mf-build` gets `## Rules for code comments`, `C1`…`C12`, text below | only the builder writes code | a shared copy in `mf-cut-change` (it writes no code) |
| <a id="d6"></a>**D6** | `P` covers the markdown docs `mf-build` creates or rewrites — `README.md`, `docs/`, `CLAUDE.md` — and its CHANGELOG entries. `C` covers comments and docstrings. Both apply only to text the phase writes or changes, and comments next to it — never a whole file unasked | unasked rewrites make a diff nobody asked to review; a task that says "rewrite X" rewrites X | a sweep of every touched file |
| <a id="d7"></a>**D7** | `mf-cut-change` gets `## Rules for the artifacts`, `A1`…`A6`: the three artifact-only rows, and FR-3's planning rules 6, 7, 9. Its Step 8 checks `P9`, `P12`, `P13`, `A2` | planning rules are decided at the cut, not during the build | putting them in `mf-build` |
| <a id="d8"></a>**D8** | Nothing checks prose mechanically | v0.12 made converge optional because it loops on prose; a prose check at every phase would bring that back | a per-phase check of size, counts and links |
| <a id="d9"></a>**D9** | Phase order: `P` first, then `W` and `C`, then `A4`…`A6` | `W4`, `C4` and `C10` cite `P` rules, so `P` must exist first | one phase (too large to review) |

### D1 — the `W` table, as `mf-build` carries it

| id | rule |
|---|---|
| **W1** | **Check a claim against the code's body** — never its name, its signature, or another document's word for it |
| **W2** | **A retirement searches the whole tree** — code, tests, docs, specs, `README.md`, `CLAUDE.md` — and lists every hit as fixed or kept, with the reason, in the phase's commit body ([D2](#d2)) |
| **W3** | **No *only*, *never* or *nothing else* without a named test** that fails when the claim stops being true |
| **W4** | **No counts in prose or comments** — name the things. The full rule and its one exception are `P12` |
| **W5** | **A test that holds a guard ships with a twin** showing the test fails when the guard is gone |
| **W6** | **The change that makes the docs false corrects them**, in the same change |

`W` applies to everything `mf-build` writes: code, comments, docs, CHANGELOG, specs.

### D2 — the retirement list, in the commit body

One line per hit, as its own paragraph before the trailer block:

```
refactor(0099-example): phase 2 — the reader is renamed

retired: read_change_state → load_change
  orchestrator/state.py — fixed
  docs/modules/state.md — fixed
  openspec/specs/sdd/spec.md — kept: a spec names the old term until the fold

Co-Authored-By: <the attribution line this session uses>
Change: 0099-example
```

### D3 — the split of the 16 rows

| old row | rule | new id |
|---|---|---|
| 1 | Terse | `P1` |
| 2 | Short sentences | `P2` |
| 3 | Simple English | `P3` |
| 4 | Examples | `P4` |
| 5 | Links | `P5` |
| 6 | ASCII diagrams | `P6` |
| 7 | Answer first | `P7` |
| 8 | Same headings every time | `A1` |
| 9 | Choices in tables | `P8` |
| 10 | Stable ids, cited as links | `P9` |
| 11 | One word per thing | `P10` |
| 12 | Concrete names | `P11` |
| 13 | Say what is out | `A2` |
| 14 | Counts show their command | `P12`, rewritten ([D4](#d4)) |
| 15 | Size limits | `P13` |
| 16 | A what-changes line per requirement | `A3` |

The `P` table both skills carry, row for row — `id · rule · example / why`:

| id | rule | example / why |
|---|---|---|
| **P1** | **Terse** | cut every word that carries nothing |
| **P2** | **Short sentences** | one idea each |
| **P3** | **Simple English** | "use", not "leverage" |
| **P4** | **Examples** | a rule with an example is read one way |
| **P5** | **Links** | link related files by relative path: `[design](design.md)` |
| **P6** | **ASCII diagrams** | for any flow, tree or state |
| **P7** | **Answer first** | each file and section opens with 1–2 lines saying what it is for or what it decides |
| **P8** | **Choices in tables** | `id · decision · because · rejected` |
| **P9** | **Stable ids, cited as links** | `per [D3](design.md#d3)` — agents grep `D3`, people click it |
| **P10** | **One word per thing** | define a term once, in bold; never swap in a synonym |
| **P11** | **Concrete names** | files, commands, symbols in backticks; a text change as before → after |
| **P12** | **No counts — name the things** | "the review and security files", not "the two files". The one exception: a change's evidence and measurement tables in `design.md`, each count with the command that produced it. A `Verify:`'s expected output is a check, not prose |
| **P13** | **Size limits** | a paragraph fits in 3 sentences, a task in 3 lines; anything longer is a decision or a doc section, linked |

### D4 — the text that changes with the counts rule

| where | before | after |
|---|---|---|
| `I6`, in both skills | "…offers no "or", and any count shows the command that produced it" | "…offers no "or", and names things rather than counting them (`P12`)" |
| `mf-cut-change`'s example task, *after* line | "Seed the seven criteria in `seeds/criteria.toml`, listed in [D6](design.md#d6)." | "Seed the criteria listed in [D6](design.md#d6) into `seeds/criteria.toml`." — its `Verify:` line is unchanged |

### D5 — the `C` table, as `mf-build` carries it

| id | rule | example / why |
|---|---|---|
| **C1** | **Say why, not what** — the code says what; the comment says why it is this way | `# run before the fold: archiving first leaves markers pointing at nothing` |
| **C2** | **Comment the surprise only** — a workaround, an ordering constraint, a non-obvious invariant; never restate the line | delete `# increment the counter` |
| **C3** | **A docstring's first line is one imperative sentence** saying what the caller gets | `"""Return the ids in the contract section, in order."""` |
| **C4** | **Short, simple, terse** — `P1`…`P3` apply | "use", not "leverage" |
| **C5** | **No history** — no "used to", "was changed in v0.8", "previously"; history is git and CHANGELOG | isekai: *"the comment above `PINNED` states the rule, never its history"* |
| **C6** | **Cite where the reason lives; do not copy it** — a reason past 3 lines goes to a doc or `design.md`, and the comment links | `# why: 0011 design D1` |
| **C7** | **3 lines at most**; longer is a doc, and `C6` applies | a comment is read beside the code, not instead of a doc |
| **C8** | **A workaround names when it can go** — a trigger, never a version; no bare `TODO` | `# remove when the runner runs make gate` |
| **C9** | **Show the shape when it is not obvious** — one input → output line in the docstring | `e.g. "0011-cut-and-gate" → 11` |
| **C10** | **One word per thing** — the term the docs and specs use (`P10`) | *change*, never also *plan* |
| **C11** | **No diagrams or tables in comments** — they belong in docs; link to them | keeps `C7` true |
| **C12** | **The `W` rules apply** — no counts, no *only* without a test, and a comment the change makes false is fixed in the same change | stated once in `W` |

The section closes with this before → after, from this repo's `tests/test_conventions.py`:

```
before:  # v0.8 widened it to nine: `.github/`, `Makefile` and `pyproject.toml` were outside
         # the scan and free of all fourteen needles, a future-regression gap rather than a
         # live hole, and they are now inside it. v0.10 makes it ten by re-adding `skills/`…

after:   # Every tracked root outside the history and the specs is scanned.
         # Why each root is in or out: 0005-change-cutover design §5.
```

### D6 — where `mf-build` states the scope

| where in `mf-build` | text |
|---|---|
| Step 2, item 1 | ends: "Write to `W`, `P` and `C` below." |
| Step 2, item 4 (CHANGELOG) | "1–3 short lines: what the phase changed and why" + ", following `P`" |
| Step 2, item 6 (commit) | one sentence: a phase that retires something carries `W2`'s list in its commit body ([D2](#d2)) |
| under the `## Prose rules` table | the scope of `P` and `C`, and *no sweeps* — [D6](#d6)'s decision, in 2–3 sentences |

The three rule sections go after *Stop-conditions* and before *What you must NOT do*, in the order `W`, `P`,
`C`.

### D7 — the `A` table, as `mf-cut-change` carries it

| id | rule | example / why |
|---|---|---|
| **A1** | **Same headings every time** | old row 8's text, unchanged |
| **A2** | **Say what is out** | proposal ends with `## Not in this change` |
| **A3** | **A what-changes line per requirement** | old row 16's text, unchanged |
| **A4** | **Keep the old thing declared until the new one is proven** — the irreversible act is the change's last phase | a delete, a removal, a migration that cannot be undone |
| **A5** | **Unbuilt work names its trigger, never a version** | "when the runner resumes", not "in v0.15" |
| **A6** | **A minor version delivers one feature; a patch delivers none.** The repo's `CLAUDE.md` states what a patch may hold; a patch cut in a repo that states nothing is put to the human | why v0.12 and v0.13 are two versions |

In `mf-cut-change`: `## How the artifacts read` becomes `## Prose rules` (the `P` table, then the example task)
followed by `## Rules for the artifacts`. Step 6's link and Step 8's check list — "style rules 10, 13, 14 and 15"
→ "`P9`, `P12`, `P13` and `A2`" — follow.

## Seams — what the test holds

The seam is the skill text on disk, as in v0.11 and v0.12. `tests/test_skills.py` already reads the input
contract's ids from a named section; the same reader serves `P` when it takes the section heading and the id
letter as parameters.

| scenario key | the scan | the twin plants |
|---|---|---|
| `sdd:prose-rules:ids-agree` | the ids in the first cell of each row (`\| **P<n>** \|`) of each skill's `## Prose rules` section are equal, non-empty, and run `P1`…`Pn` with no gap | two files differing by one id; one file with a gap — both reported |

The existing contract scan (`sdd:input-contract:ids-agree`) must stay green through the reader's change.

## Evidence

| id | observation | check |
|---|---|---|
| **E1** | isekai's architecture review: 28 false claims at `2ccda2f` — mostly a retired mechanism still described, an *only*, or a count | vault FR-3 |
| **E2** | `mf-cut-change`'s style table has 16 rows | command K1 below |
| **E3** | `mf-build` has no rule list for prose or comments | command K2 below |
| **E4** | this repo's comments carry history — the `C5` / `C7` example | `sed -n '48,51p' tests/test_conventions.py` |

```
K1  sed -n '/^## How the artifacts read/,/^## Never/p' skills/mf-cut-change/SKILL.md | grep -c '^| [0-9]* |'   → 16
K2  grep -c -e '^## Prose rules' -e '^## Rules for code comments' skills/mf-build/SKILL.md          → 0
```

## Dependencies

None.

## Risks / Trade-offs

- **Two copies of `P`'s text can drift while their ids agree.** → The scan guards ids only, as it does for the
  input contract; the owner is named in both, and `mf-build`'s wins.
- **Rules nobody checks are rules nobody follows.** → Accepted ([D8](#d8)). The human's read is the check, and
  isekai's docs versions are the first test.
- **`W2`'s list makes commit bodies long.** → Only phases that retire something carry it.

## Verdict

**feasible.** Two skills, one test module. No dependency. Three phases, each green alone.
