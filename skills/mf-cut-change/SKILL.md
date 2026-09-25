---
name: mf-cut-change
description: Cut a new in-repo change from a settled grilling — create its version branch, write the four OpenSpec artifacts to mf-build's input contract, check them, show the human, and commit on their OK. Use when the decisions for the next change are settled, in the conversation or a brief file, and its change directory does not exist yet.
---

# mf-cut-change — write a change `mf-build` can run without guessing

> **Your role is CUT.** You write one change — `openspec/changes/<change-id>/` — from decisions a person has
> already settled, and you commit it only after they read it. You do **not** build, review, converge or
> release it. Read the repo's `CLAUDE.md` as shared context; the source you are given is what you write from.

```
  grilling ──▶ mf-cut-change ──▶ mf-build ──▶ mf-converge ──▶ mf-release
                  │                  ▲
                  └── I1 … I15 ──────┘   the input contract, owned by mf-build
```

## Parameters

| parameter | required | form |
|---|---|---|
| `change-id` | yes | `<digits>-<lowercase-slug>`, e.g. `0011-cut-and-gate` |
| `version` | yes | `vX.Y`, or `vX.Y.Z` for a patch |
| `brief` | no | a path to a grilling brief |

Echo all three before anything else. A required one missing → **halt** and ask for it. Never infer one: not the
id from the highest directory, not the version from the id.

The **source** is what you write from: the conversation, unless `brief` is given. A `brief` path that does not
resolve is a **halt** — never search for one.

## Step 1 — Preconditions

Every one holds, or **halt** naming the one that failed:

- you are on the default branch, and `git status --porcelain` prints nothing;
- `openspec --version` runs;
- the gate is sound: `make -n gate` exits 0 and prints at least one command. Paste its output. No root
  `Makefile`, no `gate` target, an empty recipe, or only `is up to date` / `Nothing to be done` → halt, naming
  the root `Makefile`;
- `change-id` is free, and its number is higher than every id under `openspec/changes/` and
  `openspec/changes/archive/`;
- the branch `v<version>_<slug>` does not exist (`git branch --list`).

## Step 2 — Gather

Read the source; `CLAUDE.md`; `openspec/config.yaml` if present; the list of `openspec/specs/*/`; and the code the
source names. The source settles no decision → **halt**: there is nothing to cut yet.

## Step 3 — Re-check premises

Check each file, symbol, line number and count the source names against HEAD. A source ages: a premise that was
true at the grilling may be false now.

A premise fails → put it to the human with the evidence, and **wait**. Never overturn a settled decision alone,
and never record an overturn the human did not make.

## Step 4 — Branch

`git switch -c v<version>_<slug>`. The slug is the id without its number, hyphens → underscores:
`0011-cut-and-gate` at `v0.11` → `v0.11_cut_and_gate`.

## Step 5 — Scaffold

`mkdir -p openspec/changes/<change-id>/specs`.

## Step 6 — Write

In this order: `proposal.md` → the `specs/` delta and `design.md` → `tasks.md`. Before each, run
`openspec instructions <artifact> --change <change-id>` and follow its structure. Write to the
[input contract](#input-contract), the [prose rules](#prose-rules) and the
[rules for the artifacts](#rules-for-the-artifacts).

- `proposal.md` opens with `version: <version>` frontmatter. The CLI neither emits nor checks it.
- A change with no behaviour change declares it: `skip_specs: true` in the change's `.openspec.yaml`, plus
  `specs/.gitkeep`. The two go together; a spec file beside `skip_specs` fails validation.
- `design.md` always has `## Dependencies`, saying `None.` when empty.

## Step 7 — Validate

`openspec validate <change-id> --strict` exits 0. Red → fix and re-run.

## Step 8 — Self-check

Build a table: each of `I1`…`I15`, met or not, with its evidence. Then:

- **Run every read-only `Verify:`.** Read-only means `grep`, `test`, `ls`, `cat`, `wc`, `find`, `sed -n`,
  `head`, and `git` without a write. A check that writes, or runs the test suite, is read and not run.
- A check that errors because of the command itself — an unknown flag, bad syntax — cannot run: rewrite it. An
  error only because it reads a file the change creates is expected.
- A check that already passes is flagged to the human: true before the build, it may prove nothing. Except a
  `**HALT CHECK**` — it checks a premise, and should pass.
- Check `P9`, `P12`, `P13` and `A2`.
- `make gate` is green.

An item cannot be met → put it to the human, and wait. This self-check is a declared exception to *no station
verifies its own work*: the human's read in Step 9 and `mf-build`'s Step 1 are the independent checks.

## Step 9 — Show

Show the human: what the change does, its phases, its decision ids, the self-check table, and the file list.
Then **wait for their OK**. On edits, go back to Step 7.

## Step 10 — Commit

Stage `openspec/changes/<change-id>/` by name — never `git add -A`. The message is
`docs(<change-id>): land the change directory`, ending with the trailer block, contiguous:

    Co-Authored-By: <the attribution line this session uses>
    Change: <change-id>

## Step 11 — Report

Report the branch, the commit id, and `git status --porcelain` printing nothing. Next: `/mf-build <change-id>`,
in a fresh session. Then stop.

## Input contract

`mf-build` owns this list. The ids here are the same set; `tests/test_skills.py` fails if they differ.

| id | the change must | the cutter meets and checks it by |
|---|---|---|
| **I1** | be committed, on its own branch `v<version>_<slug>` cut from the default branch; the tree is clean after the cut commit | Steps 4 and 10; `git status --porcelain` prints nothing after the commit |
| **I2** | have all four artifacts and pass `openspec validate <id> --strict`. A change with no delta has both `skip_specs: true` in `.openspec.yaml` and `specs/.gitkeep` | Step 6; running the validator in Step 7 |
| **I3** | leave `make gate` green on the cut commit | running `make gate` in Step 8 |
| **I4** | open `tasks.md` with `## Progress`, one line per phase: `- [ ] N — Title`. Each phase has a `## N — Title` section of `- [ ] N.M` sub-tasks, and each sub-task states its check after `Verify:` | writing that shape; reading `tasks.md` |
| **I5** | make every `Verify:` a command that runs on this machine, or a fact visible on disk | running each read-only check in Step 8 |
| **I6** | give every task one reading: it names its files, offers no "or", and names things rather than counting them (`P12`) | reading each task |
| **I7** | name, in some task, every existing file the change will turn red | searching the tests and docs for what the change edits |
| **I8** | let each phase end on a green gate by itself; steps that cannot be green apart are one phase | reading the phase order |
| **I9** | have a delta for every behaviour change. A MODIFIED title matches an existing requirement exactly. A rename is REMOVED (old title, with **Reason** and **Migration**) plus ADDED (new title) | comparing each MODIFIED title with `openspec/specs/` |
| **I10** | agree with HEAD: every file and symbol `design.md` names exists, and every line number was re-checked at the cut | checking each one in Step 3 |
| **I11** | need no dependency beyond the `## Dependencies` section of `design.md`, which always exists and says `None.` when empty | writing the section; reading it |
| **I12** | hold no task for a step another station owns: a gate run, a CHANGELOG entry, a tick, a commit, `/simplify`, review, converge, release, archive, tag. `tasks.md` does not copy `mf-build`'s per-phase ritual | reading `tasks.md` |
| **I13** | open `proposal.md` with `version:` frontmatter — `vX.Y`, or `vX.Y.Z` for a patch | writing it from the `version` parameter; reading it |
| **I14** | mark a phase a person must do with `**HUMAN` on its `## Progress` line (qualifiers may follow: `**HUMAN · METERED**`), and give it at least one `Verify:` naming the evidence that closes it | running its checks: none may pass yet, or `mf-build` would close the phase unworked |
| **I15** | mark `**HALT CHECK**` on a sub-task whose failure means the plan is wrong | reading `tasks.md` |

## Prose rules

`mf-build` owns this list. The ids here are the same set; `tests/test_skills.py` fails if they differ. Every
artifact follows these rules, and the ones in [Rules for the artifacts](#rules-for-the-artifacts). The
self-check covers `P9`, `P12`, `P13` and `A2`.

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

A task, before → after:

```
before:  2.4 Seed the criteria appropriately, making sure the values are consistent with
         what the matcher expects, or delete the stale ones if they are no longer needed.

after:   2.4 Seed the criteria listed in [D6](design.md#d6) into `seeds/criteria.toml`.
         Verify: `grep -c '^\[\[criterion\]\]' seeds/criteria.toml` prints `7`.
```

## Rules for the artifacts

Rules for a change's artifacts only; `mf-build` does not carry them.

| id | rule | example / why |
|---|---|---|
| **A1** | **Same headings every time** | proposal: frontmatter · title · one line · reading map · Why · What Changes · Capabilities · Impact · Not in this change. design: title · one line + verdict · Context · Goals / Non-Goals · Decisions · *extra sections* · Dependencies · Risks / Trade-offs · *Migration Plan, if any* · Verdict. tasks: title · one line · `## Progress` · `## N — Title` |
| **A2** | **Say what is out** | proposal ends with `## Not in this change` |
| **A3** | **A what-changes line per requirement** | proposal lists each requirement the delta touches, one line each — a MODIFIED block hides its own diff |

## Never

- Never build, or edit anything outside `openspec/changes/<change-id>/`.
- Never run `/simplify`, review, converge or release.
- Never commit before the human's OK.
- Never push, or merge.
- Never overturn a settled decision alone.
- Never write the brief's path, or any absolute path, into the change.
- Never invent scope the source did not settle.
