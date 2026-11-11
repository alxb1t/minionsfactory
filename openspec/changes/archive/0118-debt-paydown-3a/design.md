# Debt paydown 3a — design

The debt cards that no conductor code decides: what later versions made moot is closed with its evidence, the prose and archive cards are corrected in place, and four small ideas of this line are built. Verdict at the end: ready to build.

## Context

Read at `8fd7364` (v0.97.0), the brief's own `At` commit: every fact it cites stands. This version touches no `skills/mf-ship/scripts/conduct.py`; version 3b ([D1](#d1)) touches that file alone and builds after this one.

| measure | value | command |
|---|---|---|
| numbered cards in the debt at the brief | 75 | `grep -c '^- \*\*[0-9][0-9][0-9][0-9]·' <primary>/.minions/debt.md` |
| tests in the files this change extends | 3, 34 and 24 | `git grep -c '^def test_' -- tests/test_corpus.py tests/test_review_metrics.py tests/test_cut_check.py` |

**The cards closed without code.** Each Still true? was run at `8fd7364`; a card whose premise is gone, or whose class an earlier card closed, is listed in `debt:` and its release deletes it. Phase 1 re-checks each row.

| card | closes as | its Still true? at `8fd7364` |
|---|---|---|
| 0097·R1 | moot: the mailbox it gave D51 is retired | `git grep -n 'writes to the repo and its worktrees alone' -- docs/decisions.md` prints the D51 line; `git grep -n 'def _open_mailbox' -- skills/mf-ship/scripts/conduct.py` prints nothing |
| 0097·R5 | moot | `git grep -n '_place(fd, f"{role}.answer"' -- skills/mf-ship/scripts/conduct.py` prints nothing |
| 0097·R6 | moot | `git grep -n 'mailbox.parent.mkdir' -- skills/mf-ship/scripts/conduct.py` prints nothing |
| 0097·S4 | moot: `_bounded` stays, no served request feeds a spawn | `git grep -n 'serve_requests' -- skills/mf-ship/scripts/conduct.py` prints nothing |
| 0097·S5 | moot | `git grep -n 'the checker mailbox' -- skills/mf-ship/scripts/conduct.py` prints nothing |
| 0101·S8 | moot: converge is a script | `git grep -n 'Resuming a run' -- skills/mf-converge/SKILL.md` prints nothing |
| 0100·R2 | moot | `git grep -n 'round <N>' -- skills/mf-converge/SKILL.md` prints nothing |
| 0094·S7, 0094·S8 | moot: the surface matcher is retired | `git ls-files skills/mf-converge/scripts/surfaces.py` prints nothing |
| 0114·R3, 0114·R5 | moot: fixed in place | `git grep -n -F '# A selection or another option is no quiet flag' -- tests/test_plan_check.py` prints nothing; the same for the `COLLECTED` comment in `skills/mf-converge/scripts/plan_check.py` |
| 0114·R4, 0114·R6 | moot: fixed in place by later amends | `git grep -n 'an operand whose file or folder exists' -- openspec` and `git grep -n 'came back three times' -- openspec` print nothing |
| 0100·R1, 0117·R1 | wontfix by the class of 0098·R1 | `git grep -n '28.6k' -- docs/decisions.md` prints the D69 line; the archived proposal of 0117 holds the figure |
| 0098·R1, 0114·R2 | wontfix, text gone | `git grep -n -e 'sums to 278' -e 'about 330 s' -- openspec` prints nothing |
| 0113·R1, 0116·R1 | wontfix | the archived design of 0113 holds the range; `openspec/specs/sdd/spec.md` holds the scaffold requirement's wording |
| 0089·R4, 0102·R2, 0105·R6, 0108·R10 | accepted | each test stands in `tests/test_conduct.py` |

0114·R4 and 0114·R6 were fixed after their cards were written, so the brief's prose fixes lose them and the table closes them.

## Goals / Non-Goals

**Goals:** every card of `debt:` leaves the debt at the release; each code fix has its test red before it; each archived claim a card names reads as the code does.

**Non-Goals:** the cards in *Not in this change*; any file `skills/mf-ship/scripts/conduct.py` or its tests hold; editing `.minions/debt.md`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | two versions split by file — **3a** touches no `conduct.py`, **3b** only `conduct.py` and its tests; the design-sized cards wait for a conductor-hardening version | reviewable diffs, no file in common, a trivial integrate | — |
| [D2](#d2) | 3a closes without code the moot cards, the wontfix by precedent and the accepted or wontfix; fixes the prose and archive cards and 0103·S2, 0100·S4, 0101·R7, 0114·R7; and takes four ideas: the corpus skips findings older than the card shape, plan metrics expands `$NAME` from the command's own words and books operator marks to the session's own repo, `cut_check.py` flags a `Verify:` needle a later task removes | about 45 cards, lowest risk | — |
| [D3](#d3) | C4 — the rescue and supervisor decide by card category — stands, recorded under the threat model's *Out of scope*; 0095·S3 closes | the person, 2026-11-11 | — |
| [D4](#d4) | 3b fixes 0090·S5, 0091·S6, 0095·S2, 0095·S4, 0099·S3, 0099·S4, 0100·S3, 0106·S4, 0111·S2, 0104·S7, 0097·R7, 0100·R5, 0112·R3, 0090·R4, 0111·R2, 0111·R4; and takes two ideas: a rejoin written while its version's rescue runs is kept until the thread ends, and `converge.py`'s halt on an ended log is printed, not stamped | one module, one build | — |
| [D5](#d5) | both: `fix codex/gpt-6.1-sol medium` and Codex checkers — converge fully on Codex; cut Sonnet medium (H21's second and third points); 3a builds on Sonnet medium (H11), 3b on Sonnet high | the person: prove Codex can converge; conductor code builds high | — |
| [D6](#d6) | 3a is queued once the gpunit run ends and v0.97.0 links; 3b `after:` 3a, its own run | the old pin halts a fixer naming a host | — |
| [D7](#d7) | 3a a minor (a new `cut_check.py` row, the corpus rule); 3b a patch | AGENTS.md's patch line | — |
| [D8](#d8) | each fix's test red before it; archived prose corrected in place; a card closed without code shows its Still true? output in the design | paydown 2's method | — |
| [D9](#d9) | a corpus case may hold `shape`, a regex an input must match; an input that does not is skipped and counted; a linked case folder stops the run | the old findings files fail the card reader, and a linked folder is deleted through | a skip list of paths; a date cut-off |
| [D10](#d10) | plan metrics reads `$NAME` from the command's own assignments, books an operator message only to marks of the session's own repo, and counts only agent tasks as workers | each is a card or idea of this line, each a few lines | reading the shell's environment |
| [D11](#d11) | `V6` flags a `Verify:` search whose needle a later sub-task, naming the same file, removes | 0117's close halted on a needle a later task removed | a check run at the build |

### D1

The split is by file, so the two builds share none and their integrate is trivial. This version's `debt:` and phases hold no `conduct.py` card.

### D2

The brief's scope, kept whole. Its prose fixes lose 0114·R4 and 0114·R6, which [the context table](#context) closes.

### D3

`THREAT_MODEL.md` gains one bullet in *Out of scope*, before *A planted skip*, naming C4 of `0095-converge-roles` and the person's yes of 2026-11-11. 0095·S3's Fix asked for this line and the person's confirmation; both are here.

### D4

Version 3b's scope, recorded here as the brief settled it. Nothing in this change builds it.

### D5

The models line is the brief's: Codex checkers and a Codex fixer, Sonnet medium for the build and the cut. Nothing in the artifacts names a model.

### D6

This version is queued once v0.97.0 links, as the old pin halts a fixer that names a host.

### D7

Minor, as the brief rates it: `V6` is a new row and the corpus rule is new behaviour.

### D8

Each code sub-task of phase 3 and 4 writes its test, runs it red, then fixes. A prose card has no test ([D37](../../../docs/decisions.md#d37--tests-hold-what-is-true-now-nothing-tests-an-absence), [D42](../../../docs/decisions.md#d42--skill-prose-is-held-by-review-not-by-phrase-scans)); its `Verify:` finds the new text or the lack of the old. The context table is the Still true? record.

### D9

`scripts/corpus.py` reads an optional `shape` of a case:

- A case whose `shape` is no string or no regex fails `broken`.
- `run_case` keeps an input when `re.search(shape, text, re.MULTILINE)` finds a match, and counts the others.
- The result line reads `corpus: <name> · <n> runs · <k> skipped · pass` when `k` is above zero, as before otherwise.
- A case whose inputs are all skipped prints `· no input`.

`scripts/corpus.toml` gives `open-cards` the shape `^[ \t]+- \*\*Status:\*\*`: a findings file with no card Status is older than the card shape, and `open_cards.py` refuses it by design. `run_case` raises `Stop` for a `minions / "corpus" / name` that is a link, before any `rmtree`, so `corpus.main` exits 2 and deletes nothing (0103·S2).

```
each glob ─▶ inputs ─▶ shape? ──no──▶ skipped, counted
                        │yes
                        ▼
           link at corpus/<name>? ──yes──▶ Stop, exit 2
                        │no
                        ▼
                     rmtree · run
```

### D10

- **`$NAME`.** `_token` reads a value that is `$NAME` or `${NAME}` as the value of an earlier word `NAME=<value>` of the same command, a trailing `;`, `&` or `|` dropped. A name no word assigns stays as written, as today.
- **The session's own repo.** `_sessions` keeps the first string `cwd` of a transcript. `_operator` takes the marks of the repo `cwd` names: the configured repo equal to it, holding it, or whose `.git/worktrees/<name>` a `gitdir:` line in `cwd`'s `.git` file names. A session whose `cwd` names none keeps every mark. The requirement's list of what a transcript gives gains `cwd`, and the page still writes numbers, ids and times, never a path.
- **Agent tasks.** `_log_workers` skips a `task_started` whose `task_type` is a string other than `local_agent`; an older log with no `task_type` still counts (0100·S4).

Fix note (2026-11-11, S1): `_own_repo` checks configured repositories from the deepest path outward, so an exact match or the nearest containing repository wins independently of configuration order.

### D11

`row_v6` is `row_v1`'s twin: for each search of a sub-task and each needle, a later sub-task that names the search's file and quotes the needle in a removed line returns `<task>: <needle> is removed in <later>`.

- A **removed line** is a line starting `-` inside a fenced `diff` block of that sub-task.
- A later sub-task whose diff also adds the needle back is silent.
- `V6` joins `ROWS` after `V5`, and `check` runs it after `V5`.

```
 task 1.1 Verify: grep x a.py ──┐
                                ├─ later task names a.py and removes "x" ─▶ V6
 task 2.3 diff:  -x             ┘
```

## Tests

No test is deleted or merged. Added at the lowest layer, each in a test file of its subject, none end-to-end:

| test | layer | the step it carries |
|---|---|---|
| `test_a_case_skips_an_input_its_shape_does_not_match` (new, `tests/test_corpus.py`) | unit | a skipped input is counted; all skipped prints `no input` |
| `test_a_linked_case_directory_is_refused` (new, `tests/test_corpus.py`) | unit | exit 2, the link's target kept |
| `test_a_span_is_bound_to_the_ids_a_cut_queued` (extended, `tests/test_review_metrics.py`) | unit | `$B` and `${B}` bind; an unassigned name binds none |
| `test_operator_work_is_booked_to_the_nearest_mark` (extended, `tests/test_review_metrics.py`) | unit | marks of the session's own repo only |
| `test_review_metrics_books_a_worker_by_its_log_name` (extended, `tests/test_review_metrics.py`) | unit | a `local_bash` task is no worker |
| `test_each_mechanical_row_fails_by_name` (extended, `tests/test_cut_check.py`) | unit | `V6` fails by name |
| `test_a_needle_a_later_task_adds_back_passes_v6` (new, `tests/test_cut_check.py`) | unit | a removed and re-added needle is silent |

The tests the card fixes touch by comment alone are `tests/test_bundle.py` and `tests/test_plan_check.py`; no assertion changes. The tests of the accepted cards, in `tests/test_conduct.py`, are read, not changed. The gate adds no end-to-end run.

## Dependencies

None.

## Risks / Trade-offs

- The seven old findings files the brief's acceptance names are not in this run directory, so the corpus rule is proved by its fixture; the person's `make corpus` with them back at their paths is the last check.
- A findings file with no cards at all has no Status and is skipped by `shape`; it holds nothing a verify judges.
- A session whose `cwd` names no configured repo books as today, against the nearest mark of any repo: the gap the idea closes stays open for those.
- An archived `debt:` line edited in place changes no card: only the change that lists the card at its release deletes it.
- `V6` reads fenced `diff` blocks alone, so a task that removes a needle in prose passes it; the plan check still fails that `Verify:` at the converge's close.

## Verdict

Ready to build.
