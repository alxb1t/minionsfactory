# Conflict resolve — design

What the integrator may resolve when both sides of a merge add, how it records each resolution, and what still goes to the
person. Verdict at the end: ready to build.

## Context

Read at `22c1af8` (v0.47.4).

- `skills/mf-integrate/SKILL.md` Step 3 applies `integrate.py`'s rules — `changelog`, `decisions`, `delta` — then treats a
  rule's exit 1 or any unmerged path as a **semantic conflict** (`:96-98`), writes `.minions/integrate/<change-id>.md` and halts
  with the merge open (`:99-112`), and never resolves one "silently against either design" (`:143`). Step 4 gates and commits
  the merge as `chore(integrate): merge <default-branch> into <branch>` (`:114-128`).
- D45 (`docs/decisions.md:429-439`) holds the station; its *Rejected* names "resolving silently against either design".
- Converge's catch-up round judges a merge by its remerge-diff (`skills/mf-converge/SKILL.md:176`, `:189`), and the gate judges
  the merged tree.
- `conduct.py`'s own `merge_in`, for a cut-only branch, runs with no agent and leaves any conflict open with its note.
- MF's own parallel run, 2026-11-03 (run `20261103-123305`): `0057-run-fixes`' integrate halted at 14:25:01 after 42 seconds,
  on two hunks whose note proposed the right resolution, settled by hand as proposed:

  | file | the branch | the default branch | resolved as |
  |---|---|---|---|
  | `skills/mf-ship/scripts/conduct.py`, the `EVENTS` tuple | adds `kept`, `removed` (`0057` D3) | drops `loopback` (`0056`, `7a04500`) | `*("push", "ledger", "unlock", "unkept", "kept", "removed")` |
  | `skills/mf-ship/SKILL.md`, Step 4's halt paragraph | adds the gate-moved and open-merge halt text (`0057` D2) | adds "A build that died in its closing steps resumes at simplify on a re-run." (`0055`, `73abb9b`) | the branch's paragraph, then the default branch's sentence before "The last line:" |

  Each overlapped on a line, so git could not merge them; each separated as list items and sentences.
- The `0050-codex-review` merge, 2026-11-01: a test needed a choice of which guard runs first — a choice of behaviour.
- D42 (`docs/decisions.md:409-417`): a test over skill text checks structure, never that a sentence exists.
- `0057·R4`: D45 (`:434`) and `mf-integrate` (`:69`, `:97-98`, `:138`) say `conduct.py` merges only into a dependent's cut-only
  branch; since v0.47.4 it also merges into one the default branch passed before its first worker.

## Goals / Non-Goals

**Goals:** an additive conflict merges with no person, and its resolution is on the record; every other conflict still halts.

**Non-Goals:** `conduct.py`'s `merge_in` resolving; a deterministic resolver; a wording test.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The integrator resolves an additive hunk, at the level its edits separate | `0057`'s hunks overlapped on a line, yet each side only added | a line-level rule: it halts both · `merge=union`, which D45 rejects |
| [D2](#d2) | Every other conflict halts as today | a choice is the person's (Q2) | resolving by judgement |
| [D3](#d3) | The merge commit names each resolved hunk; the note is still written | the catch-up round and the person read it; nothing is silent | the note alone, which Step 4 deletes |
| [D4](#d4) | `:143` and D45 say so; `0057·R4`'s wording | A7 | — |
| [D5](#d5) | No wording test: a `grep` `Verify:` at the build, and the proof after the release | D42; a real integrator is an agent | a test that a sentence exists |

### D1

`skills/mf-integrate/SKILL.md` Step 3 gains an item between today's items 2 and 3, **Resolve what both sides add**: for each
path git leaves unmerged, compare the base with each side. A hunk is **additive** when the union keeps every line, list item
or sentence each side added and every one each side removed, and changes nothing else. Resolve it to the union and stage the
path by name. A merged test the union breaks is fixed when the fix keeps both sides' intent. Every path left unmerged after it
is a semantic conflict, as today.

### D2

Today's item 3 names what is not additive: one side editing what the other removed, two values for one thing, designs that
disagree, a choice between behaviours, a requirement both sides changed (the `delta` rule). Each goes to item 4's note and halt,
unchanged.

### D3

Item 4's note is still written, its resolved hunks under `## Resolved`, each with **The branch**, **The default branch** and
**The union**. Step 4's commit gains a body, one line per resolved hunk, before the trailer block:

    chore(integrate): merge <default-branch> into <branch>

    <path>: the branch <its intent>; <default-branch> <its intent>; union
    <path>: …

    Co-Authored-By: <the attribution line this session uses>
    Change: <change-id>

e.g. `skills/mf-ship/scripts/conduct.py EVENTS: the branch adds kept, removed; main drops loopback; union`.

### D4

- `:143` → "**Never resolve a semantic conflict silently**: name each resolved hunk in the merge commit; a choice between
  behaviours halts. Never abort the person's open merge."
- D45's bold rule gains, after "applies fixed rules to the CHANGELOG, decision ids and spec delta,", "resolves a hunk both
  sides only add, naming it in the merge commit,"; *Rejected*'s "resolving silently against either design" stays.
- `0057·R4`, in D45 (`:434`) and `mf-integrate` (`:69`, `:97-98`, `:138`): "a dependent's cut-only branch" → "a cut-only branch —
  a dependent's, or one the default branch passed before its first worker", each sentence kept grammatical.

### D5

The build proves the wording once, by the tasks' `grep` checks. After the release, the next parallel `/mf-ship` whose integrate
meets additive hunks commits the merge with no halt, its body names each hunk, and its catch-up round is clean.

## Tests

Counted at `22c1af8`: `uv run pytest --collect-only -q | tail -1` prints `102 tests collected`. No test is added, deleted or
merged: the change is skill and decision text, held by review (D42).

## Dependencies

None.

## Risks / Trade-offs

- **A wrong union.** The catch-up round reads the merge by its remerge-diff and its body, and the gate runs on the merged tree;
  a union that drops an intent is caught there, not shipped.
- **"Additive" is the integrator's judgement.** The rule names its test, and each resolution is on the record for the catch-up.

## Verdict

Ready to build.
