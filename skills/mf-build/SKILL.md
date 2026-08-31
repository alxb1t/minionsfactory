---
name: mf-build
description: Build the active in-repo change phase by phase — one phase per pass, each verification run rather than summarized, each phase ending on a green gate, a CHANGELOG entry, a ticked box and one trailered commit; closes with a /simplify pass. Use when a change under openspec/changes/ has been cut and its phases need building.
---

# mf-build — build the active change, one phase per pass

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

## Step 1 — Lift the context

1. **The change** — `openspec/changes/<change-id>/`: `proposal.md` (scope), `design.md` and `tasks.md`
   (the whole file, and your phase's sub-tasks and their stated verifications in particular).
   **`design.md` is authoritative — do not re-derive it and do not re-litigate it.** Where the build disagrees
   with a decision it settled, that is a **halt**, not a quiet divergence.
2. **`CLAUDE.md`** at the repo root — the gate, the conventions and seams, the guardrails.
3. **Where the work stands** — the `## Progress` list in `tasks.md` plus `git log`, never memory. Resume is
   free: re-read both at the start of every pass.
4. **The gate** — the ordered command list in `.minions/minions.toml`'s `gate` array. That declaration is the
   source of truth; a `Makefile` target mirrors it. If the file is absent or its `gate` array is empty,
   **halt naming the file** — never infer a gate, never ask for one, never substitute a command you found.

If the tree is dirty when you start, a previous pass at this phase was interrupted. Read what is there against
the phase's acceptance and **continue** it rather than restarting; say so in your report.

If every `## Progress` box is already ticked, do not invent scope: the change is built. Report that and stop.

## Step 2 — The per-phase ritual

Build **only the first unticked `## Progress` phase**. Never batch phases, and never start the next one in the
same pass — the ordering exists so each phase is reviewable and revertible on its own.

1. **Do the phase's tasks.** Test-first where there is logic: write the failing test for the phase's acceptance,
   then implement to green. External effects are faked behind the repo's declared seams, so the suite stays
   offline and deterministic.
2. **Run each sub-task's stated verification — run it, never summarize it.** Paste the command's real output
   into your report. A verification you describe is a claim about the check; only the command that exited is the
   check. This is the same rule the gate is under, applied to the per-task acceptance.
3. **Run the full gate** — every command in the `gate` array, in order. It must exit 0. **Never weaken the gate
   to pass:** deleting or skipping a test, a blanket suppression, a loosened config — each is a plan problem, and
   the move is to halt (see *Stop-conditions*).
4. **Append that phase's entry under `## [Unreleased]` in `CHANGELOG.md`** — what the phase changed and why, in
   the style of the entries already there.
5. **Tick the phase's box** in the `## Progress` list in `tasks.md` (`- [ ] N` → `- [x] N`). A phase is finished
   by a commit **and** a ticked box; either alone is not an advance.
6. **One commit for that phase.** Stage the paths you changed **by name** — never `git add -A`, because
   `.minions/` holds gitignored run output and an un-ignored one would be swept into history. Write a
   Conventional-Commits subject, and end the message with the trailer block:

       Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
       Change: <change-id>

   **Every commit carries a `Change: <change-id>` git trailer**, and the two lines are **contiguous** — git
   parses the trailer block as the last paragraph of the message, so a blank line between them silently breaks
   it.

Then take the next unticked phase, from Step 2 again, until every box is ticked.

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
4. **A dependency that would need adding** — state the justification and stop for approval. Dependencies are the
   supply-chain surface and are human-gated.
5. **A gate that only goes green by weakening it** — halt. That is a plan problem, not a coding shortcut.

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
