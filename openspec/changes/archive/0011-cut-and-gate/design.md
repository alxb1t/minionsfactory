# 0011-cut-and-gate — design

**In one line:** `mf-build` gets a written input contract, a new `mf-cut-change` writes to it, the skills run
`make gate`, and `mf-release` drops its separate binding step. **Verdict: feasible** ([why](#verdict)).

Motivation is in [proposal.md → Why](proposal.md#why). This page is the how: 16 decisions, the contract, the
cut's steps, the style, the tests and the evidence.

## Context

The line after this change:

```
            ┌──────────── the input contract, I1 … I15 ─────────────┐
            │  owned by mf-build · copied by id into mf-cut-change   │
            │  tests/test_skills.py fails if the two id sets differ  │
            ▼                                                        │
  grilling ──▶ mf-cut-change ──▶ mf-build ──▶ mf-converge ──▶ mf-release
              writes + checks    checks I1 I4     runs          no separate
              I1 … I15 itself    I13 I14 itself   make gate     binding step
                                 runs make gate                 runs make gate
```

What stands today, in one line each:

- The three gate-running skills read `.minions/minions.toml`'s `gate` array. `mf-converge` even forbids using
  a `Makefile` target.
- The cut has no skill. Its steps live as prose in each repo's `CLAUDE.md` (*How a change is cut here*).
- `mf-build` states its stop-conditions but not what it needs from a change.
- `mf-release` reads a spec-binding command out of the gate array and runs it around the fold.

### Terms

One word per thing. These are used exactly this way in all four artifacts.

| term | means |
|---|---|
| **change** | `openspec/changes/<id>/` — proposal, design, tasks, specs delta |
| **cut** | writing a change. `mf-cut-change` is the cut station |
| **source** | what a cut is written from: the conversation, or a brief file |
| **gate** | `make gate`, run at the repository root |
| **input contract** | `I1`…`I15` — what a change must meet before `mf-build` runs it |
| **HUMAN phase** | a phase a person does; marked `**HUMAN` on its `## Progress` line |
| **HALT CHECK** | a sub-task whose failure means the plan is wrong, not the code |
| **runner** | the parked automated line under `orchestrator/` |
| **target repo** | any repository the skills run in |

## Goals / Non-Goals

**Goals**

- A change cut by `mf-cut-change` reaches `mf-build`'s first phase with no halt caused by how it was written.
- One list of gate commands per repo: the `Makefile` recipe.
- `mf-release` does less, and nothing it drops leaves a check unrun in this repo.

**Non-Goals**

- Changing the runner (D3).
- A fresh-reader check of the cut (D11 — rejected for cost).
- Rewriting existing specs, CHANGELOG entries or archived changes into the new style (D15).
- Editing any target repo.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | The skills run `make gate` at the repo root, print `make -n gate` first, and halt on no `Makefile`, no `gate` target, or a target that runs nothing | every known target has the target ([E13](#evidence)); the toml copy drifted, and in one repo cannot run ([E14](#evidence)) | a toml fallback — a second path nobody needs |
| <a id="d2"></a>**D2** | The `Makefile` recipe is this repo's only list of gate commands. CI runs `make gate`; docs name it and say what it checks | four copies drifted before (backlog `mirror`); isekai's CI moved to `make gate` for the same reason ([E15](#evidence)) | keep the copies, with the `Makefile` as source |
| <a id="d3"></a>**D3** | The runner keeps reading `.minions/minions.toml`. The file stays in this repo only, marked deprecated | the runner is parked; changing it is Track B work | switching the runner now |
| <a id="d4"></a>**D4** | `mf-release` drops its separate spec-binding step. Step 3 stages; Step 4 commits once; the staged tree must be the gated tree | simpler; Step 4.3's full gate runs the binding check in any repo that has one | a second target, `make specs` |
| <a id="d5"></a>**D5** | `mf-build` owns the input contract. `mf-cut-change` carries the same ids. A test holds the two id sets equal | one owner, and drift turns the gate red | a copy with no guard; reading the sibling skill at run time (a `SKILL.md` names no path outside the repo — `0010` D15) |
| <a id="d6"></a>**D6** | `mf-build` Step 1 checks `I1`, `I4`, `I13`, `I14` itself | git and grep only: cheap and mechanical | all fifteen — judgement, tokens, and the CLI |
| <a id="d7"></a>**D7** | `mf-build` learns HUMAN phases, HALT CHECK, `N.M` ticks, approved dependencies and short CHANGELOG entries | each one tripped a real repo ([E10](#evidence), [E11](#evidence), [E17](#evidence), [E18](#evidence)) | leaving them to stop-conditions 1–5 |
| <a id="d8"></a>**D8** | A new skill, `mf-cut-change`, holds the whole cut and runs the OpenSpec CLI. `CLAUDE.md` loses its cut section | the cut was the one station written as prose, and nobody read it | keeping the steps in `CLAUDE.md` too |
| <a id="d9"></a>**D9** | Parameters: `change-id` and `version` required, `brief` optional. The source is the conversation unless `brief` is given | the rule of every `mf-*` skill: nothing keyed is inferred | deriving the id from the version |
| <a id="d10"></a>**D10** | Premises are re-checked at HEAD. A failed one goes to the human; the cutter never overturns a decision alone | a brief ages: re-grilled at the cut, 9 of one brief's 21 decisions fell ([E12](#evidence)) | overturning silently and recording it |
| <a id="d11"></a>**D11** | The cutter checks its own work against the contract — a declared exception to *no station verifies its own work* | token cost. The human's read and `mf-build` Step 1 are the independent checks | a fresh subagent (cost); the human alone (missed [E1](#evidence)) |
| <a id="d12"></a>**D12** | The cut starts on the default branch with a clean tree, creates `v<version>_<slug>`, and commits only after the human's OK | `mf-converge` needs a branch; an uncommitted cut reads as an interrupted phase ([E1](#evidence)) | committing before the human reads |
| <a id="d13"></a>**D13** | The cutter runs every read-only `Verify:` at the cut | GNU-only greps and always-true checks reached the build ([E6](#evidence), [E17](#evidence)) | reading them only |
| <a id="d14"></a>**D14** | Backlog items closed here: `S3` (the echo half), `R6`, `R8`, `R16`, `R17`, `mirror` (except D3's copy) | each sits in text this change rewrites | folding `R13`, `R9`, or the two `sdd` items |
| <a id="d15"></a>**D15** | Artifacts follow [How the artifacts read](#how-the-artifacts-read). `mf-build`'s CHANGELOG entries follow rules 1–3 | the old prose was hard for a person to read | style for the cut only |
| <a id="d16"></a>**D16** | Phase order: `mf-release` first, then the gate, the contract, the skill | no commit ships a skill naming a check whose source is gone | gate first — phase 1 would leave `mf-release` running a binding command read from an array it no longer reads |

### D1 — the gate rule

Each of the three skills states the same rule in its own words. Skills are self-contained, so there is no
shared file.

- The gate is `make gate`, run from the repository root.
- Before the first gate run in a session, run `make -n gate` and paste its output. It shows what will run.
- Halt, naming the root `Makefile`, when:
  - there is no `Makefile` at the root;
  - `make -n gate` exits non-zero — there is no `gate` target;
  - `make -n gate` prints no command — an empty recipe, or only a line saying `is up to date` or
    `Nothing to be done`.
- Never infer a gate, never ask for one, never run a command you found instead.

The third halt is measured, not guessed. A `gate` target missing from `.PHONY`, beside a file named `gate`
(make 3.81):

```
$ make gate        make: `gate' is up to date.                   exit 0  — nothing ran
$ make -n gate     make: `gate' is up to date.                   exit 0
no Makefile        make: *** No rule to make target `gate'.      exit 2
no gate target     make: *** No rule to make target `gate'.      exit 2
```

Where it lands:

| skill | place |
|---|---|
| `mf-build` | Step 1 item 4; Step 2 item 3 — "every command in the `gate` array, in order" → "`make gate`" |
| `mf-converge` | *Where the constants come from*; preconditions 4 and 5; Step 2 item 3 creates `.minions/findings/` with `mkdir -p .minions/findings` before writing the patch (`R6`) |
| `mf-release` | *Where the constants come from* |

`mf-converge`'s "never infer one from a `Makefile` target you found" goes: the target **is** the gate now.

### D2 — this repo's copies of the gate

| file | change |
|---|---|
| `.github/workflows/ci.yml` | the six `run:` steps become one: `run: make gate`. Checkout and the uv setup stay |
| `Makefile` | a comment above `gate:` — the only list of gate commands; the skills and CI run it; the runner's toml mirrors it, deprecated |
| `.minions/minions.toml` | the comment is rewritten per D3. The array does not change |
| `CLAUDE.md` | the gate section names `make gate` and what it checks — lock sync, format, lint, strict types, tests, spec binding — with no command list. The runner-seam bullet says the skills run `make gate` |
| `README.md` | *The quality gate* names `make gate` and what it checks, with no command block. The runner's target-repo list marks the toml deprecated. The skills section says a target repo needs a root `Makefile` with a `gate` target |
| `openspec/config.yaml` | `context:` says "the gate (`make gate`)" instead of "the six gate commands" |
| `docs/sdd.md` | the footprint list at the top, practice 2, *The gate — declared on disk*, and Part II *Wiring*, *Layout* and *Gate quality*: the array becomes the recipe; "mirrors the array" and "prose declares the gate as commands" become "prose names `make gate` and never copies its commands" |
| `docs/architecture.md` | invariant 6: the gate is `make gate`; the runner reads a deprecated toml copy. The graph edge label says `deprecated` |

Unchanged on purpose, because they describe the runner (D3): `orchestrator/gate.py`,
`openspec/specs/gate/spec.md`, `docs/modules/gate.md`, `docs/modules/main.md`, `prompts/coder.md`.

### D3 — the toml's new comment

It says four things, in this order:

1. **Deprecated.** The gate is the root `Makefile`'s `gate` target; the skills and CI run `make gate`.
2. Only the parked runner (`orchestrator/gate.py`) reads this array.
3. It must match the `Makefile` recipe command for command until the runner moves.
4. When the runner runs `make gate`, delete this file.

### D4 — `mf-release`, before → after

| where | before | after |
|---|---|---|
| *Where the constants come from* | two constants may be absent: a version file and a spec-binding command read from the `gate` array | one constant may be absent: a version file |
| Step 1, item 7 | the tree is clean **and** the spec binding is green before the fold | the tree is clean (`git status --porcelain` prints nothing) |
| Step 2 | three operations | three operations, plus one line: a rename arrives as REMOVED (old title) + ADDED (new title) — the fold has no rename operation |
| Step 3 | *Verify after the fold, then archive — one commit* | *Archive — staged, not committed*: move the change to `openspec/changes/archive/<change-id>/`, stage the fold and the move by name, commit nothing. Step 4 makes the one commit (`R8`). Then a paragraph declaring the deviation from `docs/sdd.md` (below) |
| Step 4, item 3 | ends "Verify, *then* act, exactly as Step 3 does around the fold." | that sentence goes |
| Step 4, item 4 | stage by name, commit | stage by name, then `git diff --quiet` must exit 0 and `git ls-files --others --exclude-standard` must print nothing, else halt: the commit must hold exactly the tree item 3 gated (`R16`). After the commit, `git status --porcelain` prints nothing |
| *Never* | "Never archive a change whose post-fold binding check is red" | line removed |

After it, no step of `skills/mf-release/SKILL.md` runs a binding check; the one line that names one is Step 3's
declared deviation from `docs/sdd.md`. `R17` closes with `R8`: its fix was
"resolve `R8` and let it stand", and the archived `0010` design stays as history.

This skill now differs from the runner's *Release fold* requirement in `openspec/specs/sdd/spec.md`, which
still verifies after folding. That requirement specs `orchestrator/release.py`, which does not change.
`CLAUDE.md` already says it: neither line is the other's spec.

It also differs from `docs/sdd.md`'s *The release fold*, which checks the binding before the fold and again
before archiving. The skill declares that in Step 3, as it declares its simplify deviation: precondition 1's
gate and Step 4.3's gate run that check before the fold and after the archive in any repo whose gate includes
it, so no separate step is needed. `docs/sdd.md` keeps its text, since this change edits only its gate prose.

Step 4, item 4 checks the staged tree with `git diff --quiet` and `git ls-files --others --exclude-standard`,
not `git status --porcelain`: after staging, `git status --porcelain` prints the staged entries, so a rule that
it print nothing there would halt every release. It prints nothing only after the commit.

### D6 — `mf-build` Step 1

- Check `I1`, `I4`, `I13`, `I14` before anything else. A failure halts, naming the id.
- The dirty-tree rule narrows. A dirty tree means an interrupted phase **only if** `tasks.md` is tracked
  (`git ls-files --error-unmatch openspec/changes/<change-id>/tasks.md` exits 0). An untracked change is `I1`:
  a halt, never a phase to continue.

### D7 — `mf-build` Step 2 and the stop-conditions

| topic | rule |
|---|---|
| **HUMAN phase** | A phase whose `## Progress` line contains `**HUMAN` is done by a person. Do none of its tasks. Run its `Verify:` checks. Any fails → halt: print its sub-tasks as the person's checklist, and the checks that will close it. All pass → the person has done it: run the gate, write the CHANGELOG entry, tick the phase and its `N.M` boxes, commit — staging the person's evidence files by name |
| **HALT CHECK** | A sub-task marked `**HALT CHECK**` whose check fails is a halt. The plan's premise broke; never change code to make it pass |
| **`N.M` ticks** | Tick each `- [ ] N.M` → `- [x] N.M` once its check has run and passed |
| **dependencies** | Stop-condition 4 changes. A package listed under `design.md`'s `## Dependencies` is added as listed. Anything else still halts for approval |
| **CHANGELOG** | Each entry: 1–3 short lines, what changed and why, in plain words. This replaces "in the style of the entries already there" |

### D8 — a reversal, said out loud

v0.9 decided *the planning line is adopted, not built*, and dropped `to-spec` for having no consumer. This
change builds the cut station anyway. The difference is evidence: `mf-build` now consumes every cut, and cuts
failed it in two repos ([E1](#evidence)–[E9](#evidence)). The reversal covers the cut only — `grilling` and the
OpenSpec CLI stay adopted, and the skill runs the CLI rather than replacing it.

## The input contract

Phase 3 writes this table into `skills/mf-build/SKILL.md` as `## Input contract`, with the first two columns
and the Step 1 marks. Phase 4 writes the same ids into `skills/mf-cut-change/SKILL.md`, each with how the cutter
meets and checks it. In both files the first cell of each row is the id in bold, `**I1**`.

| id | the change must | `mf-build` Step 1 checks it | the cutter checks it by |
|---|---|---|---|
| **I1** | be committed, on its own branch `v<version>_<slug>` cut from the default branch; the tree is clean after the cut commit | yes — `tasks.md` is tracked, and the branch is not the default | `git status --porcelain` prints nothing after the commit |
| **I2** | have all four artifacts and pass `openspec validate <id> --strict`. A change with no delta has both `skip_specs: true` in `.openspec.yaml` and `specs/.gitkeep` | — | running the validator |
| **I3** | leave `make gate` green on the cut commit | — | running `make gate` |
| **I4** | open `tasks.md` with `## Progress`, one line per phase: `- [ ] N — Title`. Each phase has a `## N — Title` section of `- [ ] N.M` sub-tasks, and each sub-task states its check after `Verify:` | yes — at least one Progress line parses | reading `tasks.md` |
| **I5** | make every `Verify:` a command that runs on this machine, or a fact visible on disk | — (stop-condition 1 at build) | running each read-only check (D13) |
| **I6** | give every task one reading: it names its files, offers no "or", and any count shows the command that produced it | — (stop-condition 3) | reading each task |
| **I7** | name, in some task, every existing file the change will turn red | — | searching the tests and docs for what the change edits |
| **I8** | let each phase end on a green gate by itself; steps that cannot be green apart are one phase | — (stop-condition 5) | reading the phase order |
| **I9** | have a delta for every behaviour change. A MODIFIED title matches an existing requirement exactly. A rename is REMOVED (old title, with **Reason** and **Migration**) plus ADDED (new title) | — | comparing each MODIFIED title with `openspec/specs/` |
| **I10** | agree with HEAD: every file and symbol `design.md` names exists, and every line number was re-checked at the cut | — (stop-condition 2) | checking each one (D10) |
| **I11** | need no dependency beyond the `## Dependencies` section of `design.md`, which always exists and says `None.` when empty | — (stop-condition 4) | reading it |
| **I12** | hold no task for a step another station owns: a gate run, a CHANGELOG entry, a tick, a commit, `/simplify`, review, converge, release, archive, tag. `tasks.md` does not copy `mf-build`'s per-phase ritual | — | reading `tasks.md` |
| **I13** | open `proposal.md` with `version:` frontmatter — `vX.Y`, or `vX.Y.Z` for a patch | yes — the key is in the leading frontmatter | reading it |
| **I14** | mark a phase a person must do with `**HUMAN` on its `## Progress` line (qualifiers may follow: `**HUMAN · METERED**`), and give it at least one `Verify:` naming the evidence that closes it | yes — every `**HUMAN` phase has at least one `Verify:` | running its checks: none may pass yet, or `mf-build` would close the phase unworked |
| **I15** | mark `**HALT CHECK**` on a sub-task whose failure means the plan is wrong | — (Step 2 halts on it) | reading `tasks.md` |

## The cut, step by step

This is `mf-cut-change`'s body (D8–D13). Phase 4 writes one `## Step N` heading per row.

**Parameters.** `change-id` — required, `<digits>-<lowercase-slug>`. `version` — required, `vX.Y` or `vX.Y.Z`.
`brief` — optional, a path to a grilling brief. Echo all three before anything else; halt if a required one is
missing. A `brief` path that does not resolve is a halt; the skill never searches for one.

| step | does | stops when |
|---|---|---|
| **1 Preconditions** | on the default branch; `git status --porcelain` prints nothing; `openspec --version` runs; `make -n gate` passes D1; the id is free and higher than every id under `openspec/changes/` and `openspec/changes/archive/`; branch `v<version>_<slug>` does not exist | any fails — name it |
| **2 Gather** | the source; `CLAUDE.md`; `openspec/config.yaml` if present; the list `openspec/specs/*/`; the code the source names | the source settles no decision |
| **3 Re-check premises** | each file, symbol, line number and count the source names, against HEAD (D10) | a premise fails — put it to the human with the evidence, and wait |
| **4 Branch** | `git switch -c v<version>_<slug>` — the slug is the id without its number, hyphens → underscores | — |
| **5 Scaffold** | `mkdir -p openspec/changes/<change-id>/specs` | — |
| **6 Write** | proposal → specs + design → tasks. Before each: `openspec instructions <artifact> --change <change-id>`. Follow its structure, the style and the contract | — |
| **7 Validate** | `openspec validate <change-id> --strict` exits 0 | — (fix and re-run) |
| **8 Self-check** | a table: each of `I1`…`I15`, met or not, with its evidence; run the read-only checks (D13); style rules 10, 13, 14, 15; `make gate` green | an item cannot be met — put it to the human |
| **9 Show** | what the change does, its phases, its decision ids, the self-check table, the file list | always — wait for the human's OK; on edits, back to step 7 |
| **10 Commit** | stage `openspec/changes/<change-id>/` by name; message `docs(<change-id>): land the change directory`, ending with the trailer block — `Co-Authored-By:` and `Change: <change-id>`, contiguous | — |
| **11 Report** | the branch, the commit id, `git status --porcelain` printing nothing; next: `/mf-build <change-id>` in a fresh session | — |

Example of step 4's slug: `0011-cut-and-gate` at `v0.11` → branch `v0.11_cut_and_gate`.

**D13 in practice.** Read-only means `grep`, `test`, `ls`, `cat`, `wc`, `find`, `sed -n`, `head` and `git`
without a write. A check that errors because of the command itself — an unknown flag, bad syntax — cannot run:
rewrite it. An error only because the file it reads is one the change creates is expected. A check that already
passes is flagged to the human: true before the build, it may prove nothing — except a **HALT CHECK**, which
checks a premise and should pass. A check that writes, or runs the test suite, is read and not run.

<a id="never"></a>**Never** — seven bullets in the skill:

- build, or edit anything outside `openspec/changes/<change-id>/`;
- run `/simplify`, review, converge or release;
- commit before the human's OK;
- push, or merge;
- overturn a settled decision alone;
- write the brief's path, or any absolute path, into the change;
- invent scope the source did not settle.

## How the artifacts read

Phase 4 writes this as a numbered table in `mf-cut-change` — one row per rule, first cell the number — followed
by the example below. The self-check covers rules 10, 13, 14 and 15. `mf-build`'s CHANGELOG entries follow 1–3.

| # | rule | example / why |
|---|---|---|
| 1 | **Terse** | cut every word that carries nothing |
| 2 | **Short sentences** | one idea each |
| 3 | **Simple English** | "use", not "leverage" |
| 4 | **Examples** | a rule with an example is read one way |
| 5 | **Links** | between the artifacts, and to files, by relative path |
| 6 | **ASCII diagrams** | for any flow, tree or state |
| 7 | **Answer first** | each file and section opens with 1–2 lines saying what it decides |
| 8 | **Same headings every time** | proposal: frontmatter · title · one line · reading map · Why · What Changes · Capabilities · Impact · Not in this change. design: title · one line + verdict · Context · Goals / Non-Goals · Decisions · *extra sections* · Dependencies · Risks / Trade-offs · *Migration Plan, if any* · Verdict. tasks: title · one line · `## Progress` · `## N — Title` |
| 9 | **Choices in tables** | `id · decision · because · rejected` |
| 10 | **Stable ids, cited as links** | `per [D3](design.md#d3)` — agents grep `D3`, people click it |
| 11 | **One word per thing** | define a term once, in bold; never swap in a synonym |
| 12 | **Concrete names** | files, commands, symbols in backticks; text changes as before → after |
| 13 | **Say what is out** | proposal ends with `## Not in this change` |
| 14 | **Counts show their command** | "57 (`grep -c … file`)" |
| 15 | **Size limits** | a task fits in 3 lines, a paragraph in 3 sentences; anything longer is a decision the task links to |
| 16 | **A what-changes line per requirement** | proposal lists each requirement the delta touches, one line each — a MODIFIED block hides its own diff |

The example, for the skill:

```
before:  2.4 Seed the criteria appropriately, making sure the values are consistent with
         what the matcher expects, or delete the stale ones if they are no longer needed.

after:   2.4 Seed the seven criteria in `seeds/criteria.toml`, listed in [D6](design.md#d6).
         Verify: `grep -c '^\[\[criterion\]\]' seeds/criteria.toml` prints `7`.
```

## Seams — what the tests hold

The seam is the skill text on disk: skills are prose, so a scan is the highest check available. Both tests live
in a new `tests/test_skills.py`, built like `tests/test_conventions.py` — module-level helpers that take a base
path, a scan over the repo, and a test that plants a defect in `tmp_path` to prove the scan bites.

| scenario key | the scan | the bite test plants |
|---|---|---|
| `sdd:skills-gate:skills-run-make-gate` | every `skills/*/SKILL.md`: no line names `minions.toml`; `mf-build`, `mf-converge`, `mf-release` each name `make gate` and `make -n gate` | the toml named in one skill; `make -n gate` missing from another — both reported |
| `sdd:input-contract:ids-agree` | the ids in the first cell of each table row (`\| **I<n>** \|`) in each file's `## Input contract` section — from that heading to the next `## ` — are equal, non-empty, and run `I1`…`In` with no gap | two files differing by one id; one file with a gap — both reported |

Both keys are ADDED in [specs/sdd/spec.md](specs/sdd/spec.md). An active delta's keys resolve for the
binding checker before the fold, so the tests bind from their first commit.

## Evidence

Every row can be re-checked. isekai rows are commits or files in the isekai repo.

| id | observation | check |
|---|---|---|
| **E1** | KitchenScheduler `0005-mid-month-replan` passed `--strict` and was not ready: uncommitted, a task implying a new dependency, a `/simplify` task | field note, 2026-09-03 |
| **E2** | a code block in a cut's `design.md` turned `ruff format --check` red | isekai `b72cfc1` |
| **E3** | "close two halt risks found auditing the cut against mf-build" | isekai `48a2ef4` |
| **E4** | "add the model-provisioning delta the cut omitted" — mid-build | isekai `5d9f252` |
| **E5** | tasks with two readings; "2.3 asserted 63 under a matcher that gives 57" | isekai `a2f61b3`, `f6f0dda` |
| **E6** | "five places the cut would have made a builder guess" (GNU-only greps among them); "the one red test file the cut never named" | isekai `594cc74`, `aeb523e` |
| **E7** | a requirement renamed under MODIFIED passes `--strict` and fails the fold; `0025` hands it to `mf-release` in prose | isekai converge review `0024` R1 and `0025` R5; `0025` `tasks.md:31` |
| **E8** | `/simplify` written as a task | isekai `0023` `tasks.md:262`, `0024` `:283`, `0025` `:179` |
| **E9** | `mf-build`'s ritual copied into 19 archived `tasks.md` | isekai, command C1 below |
| **E10** | the human-phase marker spelled 6 ways | isekai, command C2 below |
| **E11** | HALT CHECK sub-tasks in use | isekai `0024` `tasks.md:186`, `0025` `:105` |
| **E12** | "The grilling overturned nine of the twenty-one decisions the brief carried" | isekai `0a6aafa` |
| **E13** | all five known target repos have a root `Makefile` `gate` target — this repo, isekai, synthetic_portraits, ergo_sonar, KitchenScheduler | in each: `grep -c '^gate:' Makefile` prints `1` |
| **E14** | 4 of 5 toml arrays equal their recipe. KitchenScheduler's runs `npm ci` at the root, which has no `package.json`; its recipe says `cd frontend && npm ci` | compare each array with its recipe |
| **E15** | isekai's CI runs `make gate` because its own steps had drifted | isekai `.github/workflows/ci.yml` |
| **E16** | a non-`.PHONY` `gate` beside a file named `gate` exits 0 and runs nothing | [D1](#d1) |
| **E17** | 25 `N.M` boxes left unticked in one archived change | isekai: `grep -c '^- \[ \] [0-9]*\.[0-9]' openspec/changes/archive/*0025*/tasks.md` |
| **E18** | a dependency change `design.md` decided was built with no halt | isekai `0025` phase 2 |

The two commands the table cannot hold, run from the isekai root:

```
C1  grep -l '^## The per-phase ritual' openspec/changes/archive/*/tasks.md | wc -l          → 19
C2  grep -h -o '\*\*[^*]*\(HUMAN\|GPU · HALT\)[^*]*\*\*' openspec/changes/archive/*/tasks.md \
      | sort -u | wc -l                                                                    → 6
```

## Dependencies

None.

## Risks / Trade-offs

- **This build edits the skills that run it.** → Each phase leaves every skill usable here: the toml stays for
  the runner, `make gate` exists, and this change meets the contract it adds (task 3.7 checks it).
- **The self-check misses what a fresh reader would catch.** → The human's read, `mf-build` Step 1, and the
  stop-conditions still stand behind it.
- **A target repo with no `gate` target now halts.** → All five known targets have one ([E13](#evidence)), and
  the halt names the `Makefile`.
- **This repo's toml drifts from the `Makefile`.** → Only the parked runner reads it, the comment says so, and a
  Track B backlog item deletes it.
- **A HUMAN phase closes without the person.** → `I14` requires a check, and the cutter flags a HUMAN check that
  already passes.
- **`mf-release` archives a bad fold.** → Step 4.3's gate runs the binding check here and in any repo that has
  one. Red halts before the commit and the tag, while the fold and the move are still uncommitted and can be
  reverted. Repos with no checker had `none` before and lose nothing.

## Migration Plan

For target repos, after this ships — not part of this change:

1. `make install-skills` — the `skills/mf-*` glob links `mf-cut-change` too.
2. In each target: delete `.minions/minions.toml`, gitignore all of `.minions/`, and drop the toml from its docs.
3. In each target: delete `CLAUDE.md`'s *How a change is cut here*, moving any fact that is not about cutting.

## Verdict

**feasible.** Every file this names exists (`tests/test_skills.py` and `skills/mf-cut-change/SKILL.md` are new).
No dependency. Four phases, each green alone. The one real risk — the build editing its own skills — is handled
by the phase order (D16).
