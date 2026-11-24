# Stamps — design

Converge writes the counts a worker kept getting wrong, `in_flight` keeps a halted version's slot while its thread lives, and small checks close the halts a hand-step caused. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Converge asks each checker to write `head`, `round`, `files` and `commits`, then reads them against its freeze. A count under the freeze's sent the checker out once more with the same prompt, which carried no count; a second miss halted. Converge already holds each value: the freeze's counts are git's, and the round is the one it counts.

The cap counts a version in flight while its thread runs and no halt names it. `Run.judge` names the halt before the thread runs its rescue and supervisor, so the slot frees while they are still to answer. `next_tag.py` reads every local tag. `plan_check.py` reads an exit only from a backticked number, and no cut row reads the word. `_status_line` prints the stage and drops the reason `stage_of` returns.

## Goals / Non-Goals

Goals: no halt from a worker's count; one slot per version until its halt is final; a cut that refuses `exits 5`; a tag from the default branch's history; a status line that names why a version halted.

Non-goals: a stamp of `passes`; any plan halt; the release script. See [proposal](proposal.md).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | Converge stamps `head`, `round`, `files` and `commits` into each findings file | it holds each value; the worker's count halted 0144 and 0148 | a count in the prompt; keeping the rescope; stamping `passes` |
| [D2](#d2) | The stamp runs after a checker returns and before its file is read, in `dispatch`, `check` and `rewrite` | those three start the workers that write a findings file | a stamp in `read_verdicts`; a stamp in `Run.checker` |
| [D3](#d3) | `skills/mflib/findings.py` gains `counted` and `count`, beside `stamped` and `stamp` | one module writes a findings file | a stamp in `converge.py` itself |
| [D4](#d4) | The scope comparison, `SCOPE_MISSED`, `rescoped` and `held`'s branch are removed; `read_findings` loses its `freeze` | nothing is left to compare | keeping the check as a guard |
| [D5](#d5) | `in_flight` counts a version whose thread is live, halted or not; a run-wide halt still counts none | the rescue and supervisor run in that thread, before `final` | a set of final halts; a count kept in `halts` |
| [D6](#d6) | Row `V9`: the token after `exits` in a `Verify:` is a backticked integer | the plan check reads the unquoted form as exit 0 | a rewrite of `plan_check.py`; a row that reads prose |
| [D7](#d7) | `next_tag.py` reads the tags the default branch holds merged | a stray local tag took a version number | the highest remote tag |
| [D8](#d8) | `status` prints a halting stage's reason after the stage | `released` was printed for a release the default branch did not hold | a second status command |
| [D9](#d9) | [D84](../../../docs/decisions.md) and [D88](../../../docs/decisions.md) are edited where they live; no decision is added | the page says what holds | a new decision for the stamp |

### D1

Converge sets `head` to the round's freeze head, `files` and `commits` to its counts, and `round` to the round it counts. A pickup check leaves `round`: it is no round. `verdict`, `open_blocking`, `inconclusive`, `passes` and the cards stay the worker's.

A scope that resolved no file stays the worker's *scope resolution failed* card, per [worker.md](../../../skills/mf-converge/references/worker.md). The references `worker.md`, `verify.md`, `generic-conformance.md` and `generic-adversarial.md` stop telling a worker to write the keys.

```
checker returns ──▶ converge stamps head, files, commits, round ──▶ read_findings ──▶ held
```

### D2

`dispatch` stamps each role it ran, `check` stamps each dispatched role with `round` left, and `rewrite` stamps its role, each before the read. A verify round's freeze is the fix diff's, so its file carries the fix's head and counts.

A file whose `mode` is `skipped` or `by-rule`, written whole by a script, is left. A file with no frontmatter is left, and `read_findings` reads it malformed as before.

### D3

`counted(text, values)` returns the text with each key of `values` set in the leading block, a missing key added before the closing `---`; it returns None for no frontmatter, `mode: skipped` or `mode: by-rule`. `count(folder, name, values)` writes it through the staged write `stamp` uses, at mode `0600`, following no link. The two share one staged-write helper.

A file `count` cannot stamp is left as `stamp` leaves it: `read_findings` reads it malformed, as it reads a file with no frontmatter. The probe's key list, `FINDINGS_KEYS` in `conduct.py`, holds only the keys a worker writes, so `head` and `round` leave it as `tokens` did.

### D4

`read_findings` keeps its `passes` and malformed checks. Its `freeze` parameter goes, with the `unscoped` freezes its callers built to turn the comparison off. [D88](../../../docs/decisions.md) loses its rescope sentence and the rescoped checker's accepted cost. The spec requirement of the rescope is removed in the delta.

### D5

`in_flight` skips a thread that is not live, and every thread once a halt names the run; it no longer skips a thread a halt names alone. A halt that stands ends its thread, so `live` is false by then and the slot frees.

A rejoin, a take-back and a version cut at the run's start run past the cap as before. The wait's reason, `<n> in flight, cap <N>`, counts a version at its rescue because `in_flight` does.

### D6

`row_v9` reads each sub-task's `Verify:` with its code spans blanked, finds each word `exits`, and requires a code span of whole digits right after it. A `**HALT CHECK**` sub-task is read like the rest: its `Verify:` runs first in the build, and an unquoted `exits 5` would pass for exit 0. The word outside a `Verify:` is no business of the row.

The living requirement of the sequencing rows `V1` to `V8` stands as it is: `V9` reads a form, not a sequence, and has its own requirement in the delta.

### D7

`next_tag.py` lists `git tag --list 'v*' --merged <default>`, `<default>` being `origin/HEAD`'s branch, else `main`. A default branch that does not exist exits 2, as a repository that cannot run does. The release script's own tag, when a dead release left it on an orphan commit, is read as none, so the next run takes the same number.

### D8

`_status_line` prints `<change-id> · <stage> — <reason>` when the stage is in `HALTS` and `stage_of` returned a reason. A broken models file's halt follows after a second ` — `, as before.

### D9

[D84](../../../docs/decisions.md) says a version is in flight while its thread runs, its rescue and supervisor included, and no halt names the run. [D88](../../../docs/decisions.md) says converge stamps a findings file's `head`, `round`, `files` and `commits`, in the sentence the rescope held. `THREAT_MODEL.md` says converge stamps through the same staged write as the conductor's `model:` and `tokens:`.

## Tests

Every new test is a unit test in a file that exists. The change adds no end-to-end run and merges no test. It deletes the tests of the rescope, named in the table.

| file | adds | layer |
|---|---|---|
| `tests/test_findings.py` | `counted` sets, adds and leaves a stub and a by-rule file; `count` follows no link | unit |
| `tests/test_converge.py` | a miscounted file stamped; a file with no count keys stamped; a verify round's head and round; a pickup check's round kept; a stub and a by-rule file left; the checker prompt holds `mode` and no `head` | unit |
| `tests/test_converge.py` | `test_a_scope_that_misses_once_is_sent_out_again` and `test_a_scope_missed_twice_halts_on_a_file_gone_or_malformed` deleted: `retired by removing A verdict that misses the freeze's scope is sent out once more` | unit |
| `tests/test_conduct.py` | a halted version at its rescue keeps the slot; a final halt frees it; a revived version finds no second; `status` prints a reason | unit |
| `tests/test_cut_check.py` | `V9` on `exits 5`, on `` exits `5` ``, on prose, on a halt check | unit |
| `tests/test_next_tag.py` | a stray local tag | unit |

Baseline `def test_` lines, from `git grep -c "def test_" -- <file>`: `tests/test_converge.py` 101, `tests/test_findings.py` 31, `tests/test_conduct.py` 336, `tests/test_cut_check.py` 45, `tests/test_next_tag.py` 1.

## Dependencies

None.

## Risks / Trade-offs

- A checker that wrote a wrong `head` is no longer read as stale: converge stamps the freeze's. The resume's `done` test reads the stamped head and round, which a worker that died before the stamp did not write; that role runs again.
- `count` follows the run directory's root as `stamp` does, so the debt cards `0136·S3` and `0138·S2` stand for it too.
- A halted version holds its slot for as long as its rescue and supervisor run, which can be long; a final halt frees it.
- `next_tag.py` needs the default branch as a local ref, named as the rest of the line names it: `origin/HEAD`'s branch, else `main`. A repository whose default branch lives only on `origin`, or is no `main` with no `origin/HEAD`, exits 2.
- `_answered` in `conduct.py` reads each role's stamped `head`. A halt before a checker returned finds a file no stamp reached, and reads as unanswered, as a stale file read before.

## Verdict

Ready to build in the phases of [tasks](tasks.md): the stamp first and hardest, the slot next, and the row, the tag and `status` last.
