---
name: mf-build
description: Build the active in-repo change phase by phase — one phase at a time, each verification run rather than summarized, each phase ending on a green gate, a CHANGELOG entry, a ticked box and one trailered commit; closes with a /simplify pass. Use when a change under openspec/changes/ has been cut and its phases need building.
---

# mf-build — build the active change, one phase at a time

> **Your role is BUILD.** You build the phases of one change, in order, to a green gate, and you commit each
> phase on its own. You do **not** review your own work, and you do **not** converge or release: `mf-converge`
> conducts the end-of-change loop and `mf-release` finalizes. Read the repo's `CLAUDE.md` as shared context —
> it is what is *true* of the repository, not a script — and read the change itself, which is authoritative.

## Parameter — the change id, required

`change-id` is an **explicit, required parameter**. Without it, **halt** and ask for it.

Never infer it: not from the highest-numbered directory under `openspec/changes/`, not from "there is only one
active change so it must be that". The id keys both the phase state you read and the `Change:` trailer you
write, so a wrong id builds one change's phases and files them under another's name.

Echo the change id and the phase you are about to build before you build anything.

## Input contract

What a change must meet before you build it. This skill owns the list; `mf-cut-change` writes to it and carries
the same ids. Step 1 checks the four marked **yes** itself; the rest surface through the stop-conditions.

| id | the change must | Step 1 checks it |
|---|---|---|
| **I1** | be committed, on its own branch `v<version>_<slug>` cut from the default branch; the tree is clean after the cut commit | yes — `tasks.md` is tracked, and the branch is not the default |
| **I2** | have all four artifacts and pass `openspec validate <id> --strict`. A change with no delta has both `skip_specs: true` in `.openspec.yaml` and `specs/.gitkeep` | — |
| **I3** | leave `make gate` green on the cut commit | — |
| **I4** | open `tasks.md` with `## Progress`, one line per phase: `- [ ] N — Title`. Each phase has a `## N — Title` section of `- [ ] N.M` sub-tasks, and each sub-task states its check after `Verify:` | yes — at least one Progress line parses |
| **I5** | make every `Verify:` a command that runs on this machine, or a fact visible on disk | — (stop-condition 1) |
| **I6** | give every task one reading: it names its files, offers no "or", and names things rather than counting them (`P12`) | — (stop-condition 3) |
| **I7** | name, in some task, every existing file the change will turn red | — |
| **I8** | let each phase end on a green gate by itself; steps that cannot be green apart are one phase | — (stop-condition 5) |
| **I9** | have a delta for every behaviour change. A MODIFIED title matches an existing requirement exactly. A rename is REMOVED (old title, with **Reason** and **Migration**) plus ADDED (new title) | — |
| **I10** | agree with HEAD: every file and symbol `design.md` names exists, and every line number was re-checked at the cut | — (stop-condition 2) |
| **I11** | need no dependency beyond the `## Dependencies` section of `design.md`, which always exists and says `None.` when empty | — (stop-condition 4) |
| **I12** | hold no task for a step another station owns: a gate run, a CHANGELOG entry, a tick, a commit, `/simplify`, review, converge, release, archive, tag. `tasks.md` does not copy this skill's per-phase ritual | — |
| **I13** | open `proposal.md` with `version:` frontmatter — `vX.Y`, or `vX.Y.Z` for a patch | yes — the key is in the leading frontmatter |
| **I14** | mark a phase a person must do with `**HUMAN` on its `## Progress` line (qualifiers may follow: `**HUMAN · METERED**`), and give it at least one `Verify:` naming the evidence that closes it | yes — every `**HUMAN` phase has at least one `Verify:` |
| **I15** | mark `**HALT CHECK**` on a sub-task whose failure means the plan is wrong | — (Step 2 halts on it) |

## Step 1 — Lift the context

**First, check the four input-contract items marked yes** — a failure halts, naming the id:

- **`I1`** — `git ls-files --error-unmatch openspec/changes/<change-id>/tasks.md` exits 0, and
  `git branch --show-current` is not the default branch.
- **`I4`** — `tasks.md` has a `## Progress` list with at least one line of the form `- [ ] N — Title`
  (ticked or not).
- **`I13`** — `proposal.md` opens with frontmatter holding a `version:` key.
- **`I14`** — every `## Progress` line containing `**HUMAN` has a `## N — Title` section with at least one
  `Verify:`.

Then lift the context:

1. **The change** — `openspec/changes/<change-id>/`: `proposal.md` (scope), `design.md` and `tasks.md`
   (the whole file, and your phase's sub-tasks and their stated verifications in particular).
   **`design.md` is authoritative — do not re-derive it and do not re-litigate it.** Where the build disagrees
   with a decision it settled, that is a **halt**, not a quiet divergence.
2. **`CLAUDE.md`** at the repo root — the gate, the conventions and seams, the guardrails.
3. **Where the work stands** — the `## Progress` list in `tasks.md` plus `git log`, never memory. Resume is
   free: re-read both at the start of every pass.
4. **The gate** — `make gate`, run from the repository root. Before the first gate run in a session, run
   `make -n gate` and paste its output: it shows what will run. **Halt, naming the root `Makefile`,** when
   there is no `Makefile` at the root, when `make -n gate` exits non-zero (there is no `gate` target), or when
   it prints no command — an empty recipe, or only a line saying `is up to date` or `Nothing to be done`.
   Never infer a gate, never ask for one, never run a command you found instead.

If the tree is dirty when you start **and `tasks.md` is tracked** (the `I1` check above), a previous pass at this
phase was interrupted. Read what is there against the phase's acceptance and **continue** it rather than
restarting; say so in your report. An untracked change is never a phase to continue: it fails `I1`, and halts.

If every `## Progress` box is already ticked, do not invent scope: the change is built. Report that and stop.

## Step 2 — The per-phase ritual

Take the **first unticked `## Progress` phase** and finish its whole ritual — through its own commit — before
you look at the next one. Never batch phases: the ordering exists so each phase is reviewable and revertible on
its own.

**A HUMAN phase is done by a person, not by you.** Its `## Progress` line contains `**HUMAN`. Do none of its
tasks; run its `Verify:` checks. If any fails, **halt**: print its sub-tasks as the person's checklist, and the
checks that will close it. If all pass, the person has done it: run the gate, write the CHANGELOG entry, tick the
phase and its `N.M` boxes, and commit — staging the person's evidence files by name.

1. **Do the phase's tasks.** Test-first where there is logic: write the failing test for the phase's acceptance,
   then implement to green. External effects are faked behind the repo's declared seams, so the suite stays
   offline and deterministic. Write to `W`, `P` and `C` below.
2. **Run each sub-task's stated verification — run it, never summarize it.** Paste the command's real output
   into your report. A verification you describe is a claim about the check; only the command that exited is the
   check. This is the same rule the gate is under, applied to the per-task acceptance. Tick each `- [ ] N.M` →
   `- [x] N.M` once its check has run and passed.
   A sub-task marked `**HALT CHECK**` whose check fails is a **halt**: the plan's premise broke. Never change
   code to make it pass.
3. **Run the full gate** — `make gate`. It must exit 0. **Never weaken the gate
   to pass:** deleting or skipping a test, a blanket suppression, a loosened config — each is a plan problem, and
   the move is to halt (see *Stop-conditions*).
4. **Append that phase's entry under `## [Unreleased]` in `CHANGELOG.md`** — 1–3 short lines: what the phase
   changed and why, following `P`.
5. **Tick the phase's box** in the `## Progress` list in `tasks.md` (`- [ ] N` → `- [x] N`). A phase is finished
   by a commit **and** a ticked box; either alone is not an advance.
6. **One commit for that phase.** Stage the paths you changed **by name** — never `git add -A`, because
   `.minions/` holds gitignored run output and an un-ignored one would be swept into history. Write a
   Conventional-Commits subject, and end the message with the trailer block:

       Co-Authored-By: <the attribution line this session uses>
       Change: <change-id>

   **Every commit carries a `Change: <change-id>` git trailer**, and it is **contiguous** with any
   `Co-Authored-By:` — git parses the trailer block as the last paragraph of the message, so a blank line
   between them silently breaks it.

   A phase that retires something carries `W2`'s list in its commit body, one line per hit, as its own
   paragraph before the trailer block:

       retired: read_change_state → load_change
         orchestrator/state.py — fixed
         docs/modules/state.md — fixed
         openspec/specs/sdd/spec.md — kept: a spec names the old term until the fold

Only then take the next unticked phase, from Step 2 again, until every box is ticked.

## Step 3 — Close with the `/simplify` pass

After the last phase, and only then:

1. Run **`/simplify`** over this change's diff and let it **apply its fixes in place**.
2. **Re-run the full gate. Red is a halt** — do not commit simplify's edits over a red gate, and do not repair
   them by weakening it.
3. Commit its edits as **their own trailered commit**, staged by name, separate from any phase commit.

**This is a declared deviation from `docs/sdd.md`'s three-read-only-station *Check*.** There, simplify is a
blind read-only station that reports and edits nothing but its own findings file; here it fixes in place inside
the builder. It is safe because of the ordering: simplify runs **first**, so the review and security stations
`mf-converge` fans out afterwards read a diff that **includes** these edits — review verifies simplify's work,
and no station verifies its own. Running simplify last, after convergence, would land unreviewed edits after the
final station had spoken.

Two consequences follow, and both are deliberate: there is **no simplify findings file at all**, and
`mf-release` therefore declares simplify out **by name** rather than tolerating an absent file — so that *a
missing findings file is not clean* never erodes into *a missing file is fine*.

## Step 4 — Report, then stop

Report the phases built, the gate's exit code, the output of each verification the tasks stated, and that the
simplify commit has landed. Then **stop** and hand back. `mf-converge` runs next, in a separate session.

## Stop-conditions — halt rather than guess

Halt by **stopping cleanly without committing and without ticking the box**, and report the specific question.
An unticked box plus a clean tree is a legible place to resume from; a half-finished phase committed as if it
were whole is not.

1. **An acceptance that cannot be made a passing check** — halt for human verification rather than fake one.
2. **`design.md` contradicting the code** — the decisions were settled against reality; where reality has moved,
   that is a finding, never a silent divergence.
3. **A task ambiguous enough that two readings give different work** — halt and state both readings.
4. **A dependency that would need adding** — a package listed under `design.md`'s `## Dependencies` was approved
   at the cut: add it as listed. Any other: state the justification and stop for approval. Dependencies are the
   supply-chain surface and are human-gated.
5. **A gate that only goes green by weakening it** — halt. That is a plan problem, not a coding shortcut.

## Rules for what you write

| id | rule |
|---|---|
| **W1** | **Check a claim against the code's body** — never its name, its signature, or another document's word for it |
| **W2** | **A retirement searches the whole tree** — code, tests, docs, specs, `README.md`, `CLAUDE.md` — and lists every hit as fixed or kept, with the reason, in the phase's commit body (Step 2, item 6) |
| **W3** | **No *only*, *never* or *nothing else* without a named test** that fails when the claim stops being true |
| **W4** | **No counts in prose or comments** — name the things. The full rule and its one exception are `P12` |
| **W5** | **A test that holds a guard ships with a twin** showing the test fails when the guard is gone |
| **W6** | **The change that makes the docs false corrects them**, in the same change |

`W` applies to everything you write: code, comments, docs, CHANGELOG, specs. A **retirement** is removing or
renaming a thing other text refers to: a module, a file, a term, a rule.

## Prose rules

This skill owns this list. `mf-cut-change` carries the same ids; `tests/test_skills.py` fails if they differ.

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

`P` covers the markdown docs you create or rewrite — `README.md`, `docs/`, `CLAUDE.md` — and your CHANGELOG
entries. `C` covers comments and docstrings. Both apply only to the text a phase writes or changes, and the
comments next to it — never a whole file unasked; a task that says "rewrite X" rewrites X.

## Rules for code comments

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

A comment, before → after, from this repo's `tests/test_conventions.py`:

```
before:  # v0.8 widened it to nine: `.github/`, `Makefile` and `pyproject.toml` were outside
         # the scan and free of all fourteen needles, a future-regression gap rather than a
         # live hole, and they are now inside it. v0.10 makes it ten by re-adding `skills/`…

after:   # Every tracked root outside the history and the specs is scanned.
         # Why each root is in or out: 0005-change-cutover design §5.
```

## What you must NOT do

- **Never batch phases into one commit**, and never continue past the phase you are on without its commit.
- **Never summarize a check you were told to run** — neither a task's verification nor the gate.
- **Never review, converge or release your own work** — no fan-out, no review pass, no security pass, no
  converge loop; and never archive, fold, tag, merge or push.
- **Never `git add -A`.** Stage by name.
- **Never commit a secret, or a real absolute path from the machine the run is on** — the operator's home
  directory or the repository's own root, least of all one transcribed out of a `.minions/` artefact into
  tracked prose. Cite repository-relative paths.
- **Never invent scope** beyond the change, and never re-open a decision `design.md` settled.
