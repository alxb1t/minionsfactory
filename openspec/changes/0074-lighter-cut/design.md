# Lighter cut — design

The brief names the commit its facts were read at; the cut re-checks only the moved ones, with parallel helpers, and its review and
show-and-tell skip what `verify_check.py` already ran. Verdict at the end: ready to build.

## Context

Read at `1df4e7a` (v0.59.0).

- **F1. The brief:** `mf-plan`'s template has no commit of its own; each fact carries `path:line` at `<sha>`
  (`skills/mf-plan/SKILL.md:124-129`), and its re-measure check already re-reads a fact citing another commit (`:74`).
- **F2. The cut's re-check:** Step 2 reads "the code the source names" (`skills/mf-cut-change/SKILL.md:66-67`); Step 3 checks
  every file, symbol, line and count against `HEAD`, then greps each deleted name (`:72-79`).
- **F3. The review and the show:** Step 8.5 asks whether each `Verify:` passes after its task (`:147`), the searches among them
  already run by `verify_check.py` (`:130-136`); Step 9 shows every `Verify:` and match word for word (`:161-163`).
- **F4. Measured cuts**, from the session transcripts: `0062`–`0070` took 3.7–16.6 minutes of work, `0066` and `0070` longer on a
  stalled helper and on waits; `0071` and `0072`, 2026-11-05, ran three helpers in parallel, and their second reviews found a missing
  delta, `Verify:` lines true before the build and a `.red` loop.
- **F5. `0066·R12`:** `Head.outside()` exports `HEAD` for every path operand, a `git grep`'s included, and `export()`'s
  `extractall(…, filter="data")` raises on a link to an absolute path or out of the tree, uncaught
  (`skills/mf-cut-change/scripts/verify_check.py:312-326`); a crash exits 1, the code for an `I19` break.
- **F6. The record:** D7 (`docs/decisions.md:86`), D40 (`:225`); the spec's *The cut runs no check before the human reads it*
  and *A fresh worker reviews the plan before the cut commits* (`openspec/specs/sdd/spec.md:288`, `:2165`).
- **F7. The brief's requirement:** *The plan station writes the brief after every round* lists the brief's sections
  (`openspec/specs/sdd/spec.md:888-894`), with no `At` line.

## Goals / Non-Goals

**Goals:** a cut at the brief's commit re-checks almost nothing; a cut after moves re-checks only what moved, in parallel.

**Non-Goals:** a tasks-shaped brief; a conditional second review; a faster I-table.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | The brief carries `At <sha>` under its title | Q2 | a sha per fact alone |
| [D2](#d2) | The cut re-checks a fact only when its cited path moved, or it cites none | Q2 | re-checking every fact |
| [D3](#d3) | Up to four helpers, five minutes each, the cut reading itself as the fallback | Q3, Q5–Q7 | one helper at a time |
| [D4](#d4) | The reviewer skips the searches `verify_check.py` ran; the second review stays | Q2, Q10 | a conditional second review |
| [D5](#d5) | Step 9 points at `tasks.md` and quotes the matches | Q2 | echoing every `Verify:` |
| [D6](#d6) | `verify_check.py` judges a `git grep`'s paths without the export, and a failed export exits 2 | `0066·R12` | — |
| [D7](#d7) | The record: D7, D40 | Q7 | — |

### D1

`mf-plan`'s brief template, and the delta's *The plan station writes the brief after every round*, gain, after its one-line summary, `At <sha>, <YYYY-MM-DD>.` — the `<sha>` of Step 1, rewritten every
time Step 5 writes the brief, so it names the commit the newest round read.

### D2

Step 2 reads the brief's `At` line, and with one runs `git diff --name-only <sha>..HEAD`: a fact whose cited paths that command
prints none of stands, and each other fact — a moved path, or no path — is a **moved fact**. With no `At` line, or a source that is
the conversation, every fact is a moved fact. Step 2's own read of "the code the source names" is the moved facts' code, and the
code the phases name for the design. Step 3 re-checks each moved fact against `HEAD`, from the helpers' answers or its own read;
the deleted-name grep stays whole. In the I10 row's "how" cell of `skills/mf-cut-change/SKILL.md`, "checking each one in Step 3"
→ "re-checking each moved one in Step 3, an unmoved path's standing"; the cell's `after:` clause is kept.

### D3

Step 2, once it has the moved facts, dispatches, where the host starts fresh workers, at most four read-only helpers in all, the
areas grouped to fit: one per top-level directory of the
moved facts' paths, one per question the brief's phases raise for the design — the file a phase edits, a symbol it calls, a test it
extends. Each gets `<sha>`, `HEAD`, its facts or question, and `mf-plan`'s allowed list (`skills/mf-plan/SKILL.md` Step 2), and
answers each fact `stands`, `moved to <path:line>` or `wrong: <evidence>`, never file contents. A helper not back in five minutes:
the cut reads its facts itself, and a late answer is ignored. With no fresh workers, the cut reads every fact itself by the same
list.

### D4

Step 8.5's question reads "can each task be built as written, each `Verify:` pass after it, and each the search script did not run
— a test, a command — fail before it?": the searches' "before" is the script's, so the reviewer reads only their "after". Its table
and the second review stay as they are.

### D5

Step 9 shows what the change does, its phases, its decision ids, the self-check table, the file list, each match the search script
printed, word for word, each plan-review doubt and what the cut did with it, and each target test rule planned to over `T1`–`T6`;
for the `Verify:` lines it names `tasks.md`, in those words.

### D6

`Head.outside(path, git: bool)`, the caller at `verify_check.py:352` passing `query.argv[0] == "git"`: for a `git grep` operand,
absolute or holding `..` is enough — git refuses a path out of the tree — and no export runs; for a `grep` operand, the export as
now. `export()` catches `tarfile.TarError` and raises `Unparsed("HEAD's tree holds a link out of it: <the error>")`, which
`check()` re-raises naming the sub-task (`:386-387`), so the cut rewrites that check — as a `git grep` — and goes on. The delta's
*A Verify: is one plain command and counts honestly* names the exit.

### D7

D7: the cut re-checks the facts whose files moved since the brief's `At` line, and its helpers read them. D40: the cut's helpers are
fresh read-only workers, as its plan reviewer is, answering in the cut's thread and writing no file.

## Tests

`git grep -c '^def test_' 1df4e7a -- tests/test_verify_check.py` prints `5` at the cut. Extended, under `T2`:
`test_what_cannot_run_exits_2` with a repository tracking `link -> /usr/share`, where a `git grep -n one -- a.md` check exits 0 with
its match and a `grep -n one a.md` check exits 2 naming the link. The skill prose is held by review (D42). None added or deleted.

## Dependencies

None.

## Risks / Trade-offs

- **A fact on an unmoved path that was wrong at the grilling:** it was checked at the brief's commit by `mf-plan`'s helpers; the plan
  review still reads the change against `HEAD`.
- **A rename the diff shows as a delete:** the old path is printed, so its facts are re-checked.

## Verdict

Ready to build.
