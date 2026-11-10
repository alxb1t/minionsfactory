# Converge done order — design

How a converge's `done` or `halt` stays its run's top line, and how D39's rule gains a case for a feature a change removes.
Verdict: refuse the bad order in `stamp.py`, heal an old log in the converge check, and add one way to D39 and each copy of its rule.

Read [proposal](proposal.md) for why, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the requirements.

## Context

Facts at `56c6ab4`, `HEAD` at the cut. `S` is `skills/mf-converge/scripts/stamp.py`, `C` `skills/mf-ship/scripts/conduct.py`, `K`
`skills/mf-converge/SKILL.md`. Lines are `HEAD`'s, from the cut's notes.

| id | fact | where |
|---|---|---|
| F1 | 0107's conductor stamped `done` and `debt` in one call, `done` given first: `debt` landed on top, the check failed on "the status log has no done", and a rejoin's converge refused the log | `C:1559-1566` |
| F2 | `K`'s rule: events with no command between them go in one call, the last given on top; `debt` is Step 9's event, `done` Step 10's | `K:67`, `K:98-100` |
| F3 | `K`'s resume table sends a top `debt` to Step 10, and a top line that is neither `halt` nor `done` continues that run | `K:221`, `K:186` |
| F4 | `S` writes the events reversed under the newest `## Run` heading and checks no order | `S:58-62` |
| F5 | `C` reads only the newest run's top line: `_run_end`, `_converge_done`; `_check_converge` fails on it | `C:896-906`, `C:1268-1270`, `C:1559-1569` |
| F6 | D39 lets a removed test's proofs be carried by a remaining test or retired by a decision in force at the base: no case for a feature the change's delta removes, so 0108-converge-script's tests of the mailbox and of H5 meet conformance's R6 twice | `docs/decisions.md:643-648`, 0108's design on its branch, line 93 |
| F7 | the rule stands in the principle, the spec, the bootstrap template, `I16` and `T5` of `mf-build` and `mf-cut-change`, the worker reference; `tests/test_skills.py` holds the `I` and `T` ids and labels equal across the skills | `docs/principles.md:110-113`, `openspec/specs/sdd/spec.md:558-564`, `openspec/specs/sdd/spec.md:3943-3963`, `skills/mf-bootstrap/templates/AGENTS.md.tmpl:31-32`, `skills/mf-build/SKILL.md:78`, `skills/mf-build/SKILL.md:350`, `skills/mf-cut-change/SKILL.md:327`, `skills/mf-cut-change/SKILL.md:373`, `skills/mf-converge/references/worker.md:21`, `skills/mf-converge/references/worker.md:199` |

## Goals / Non-Goals

**Goals:** a finished converge never reads as unfinished through the order of one call; a log already out of order heals with no hand
step; D39 covers a removed feature's tests.

**Non-Goals:** the converge conductor as a script ([0108-converge-script](../0108-converge-script/proposal.md)); a change to
`stage_of`; any new station, parameter or decision ([AGENTS.md](../../../AGENTS.md)'s patch line).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `S` exits 2, the log unchanged, on a call that gives `done` or `halt` before another event (`done goes last in a call`), and on any event for a run whose top line is `done` or `halt` (`the run ends on done: open a ## Run for a new event`), save a `halt` naming `.minions/debt.lock` or `.minions/backlog.lock` | 0107's mistake becomes impossible for the LLM conductor and for 0108's script, which writes through `S`'s `main`; a run halted on the lock resumes at Step 9 with no new `## Run` and stamps `debt` under that halt ([K:191](../../../skills/mf-converge/SKILL.md), `C:1506`), so the refusal spares it (C1 of the brief, decided by the cutter) | a check in `K` alone: prose a Sonnet-medium conductor missed once · a new `## Run` for a lock resume: `K:191` says otherwise, and D5 leaves `K` as it is |
| <a id="d2"></a>**D2** | `C`'s converge check, finding no `done` on top but one below it in the newest run, whose top line is no `halt`, passes after it stamps `done` again through `S`'s `main`, `round <N> · done — re-stamped by the run`, `<N>` the buried line's round | a log already in that state needs no hand step; both findings files clean at `HEAD` and a clean tree are what `done` claims, and the check reads both before it writes | a hand `stamp.py` of `done`, as 0107 took · re-running converge: it halts on the log |
| <a id="d3"></a>**D3** | the check logs the re-stamp: `check` and `_check_converge` take the keyword `notes: list[str] | None = None`, a list the re-stamp appends `re-stamped done` to; `Run` passes one and shows it after the pass, `check · converge · pass · re-stamped done`. A hand `conduct.py check converge` re-stamps too; `S`'s printed line, or its error, reaches stdout as it is | the run log is where a person reads what the run did; `check` has no log of its own | a new run-log event: `EVENTS` and `verify_log` change for one line |
| <a id="d4"></a>**D4** | D39 and each copy gain a third way: a removed test whose proofs cover only a requirement the change's delta removes, with the code under test, is retired by that removal; the `## Tests` table names the removed requirement | 0108's R6 is the rule's gap, not 0108's; a rule that misstates the behaviour is patch material | `retired by Dn` for a new decision: 0108 adds none for a removal · a coverage waiver: it weakens the gate |
| <a id="d5"></a>**D5** | `K` stays as it is | its rule, the last given on top, already puts `done` last; 0108 cuts `K` to a front, and `S`'s refusal teaches the order | a sentence in `K`'s Step 10: a merge conflict with 0108 for text that file is about to lose |

**The wording of D4**, the same phrase in each copy, so `tests/test_skills.py`'s equal rows stay equal:

```
before:  … or to a decision in force at the base that retires it
after:   … to a decision in force at the base that retires it, or, when its proofs cover only a requirement the
         change's delta removes, to that requirement removed with the code under test
```

`I16` keeps its `(retired by Dn)` and adds `(retired by removing <requirement title>)`. D39's page line holds
`a requirement the change's delta removes` whole, on one line.

## Tests

The change adds `test_a_done_under_the_top_line_is_stamped_again` and the fake mode `keep-log` of `tests/fake_worker.py`, and extends the tests of `tests/test_stamp.py`; it removes none.

| layer | file | test | does | why here |
|---|---|---|---|---|
| unit | `tests/test_stamp.py` | `test_a_stamp_writes_the_clock_time_under_the_latest_run`, extended | on a fresh log, `debt` then `done` in one call: both printed, `done` on top; an event under a top halt naming `.minions/debt.lock`, and one naming `.minions/backlog.lock`, stamps; a `--run` heading under a top `done` stamps | a step in the test that already writes several events (`T2`) |
| unit | `tests/test_stamp.py` | `test_a_log_out_of_shape_is_not_stamped`, extended | refusal cases of [D1](#d1): `done` before `debt`, `halt` before `debt`, an event under a top `done`, an event under a top `halt` that names no lock; each exit 2, its message, the log unchanged | the test of every refusal (`T1`) |
| integration | `tests/test_conduct.py` | `test_a_done_under_the_top_line_is_stamped_again`, new | `check` called direct on a log with `debt` over `done`, both findings files clean at `HEAD`, the tree clean: it passes, `done` is on top as `re-stamped by the run`, `notes` is `["re-stamped done"]`. A findings file not clean fails with `_unjudged`'s reason, a dirty tree with `the tree is not clean`, and an unanswered `halt` on top with `the status log halts: <the halt>`; each stamps nothing. `_buried_done` is None under a top `halt` and with no `done`. A `status_log.md.tmp` folder makes the stamp exit 2: the check fails `the status log has no done`, the log as it was. Then one `run`, the fake host in the new mode `keep-log`, which writes back the log its converge branch found after `_findings` has overwritten it, the log written after `_findings` in the test: it spawns converge and releases, its run log holding `check — converge · pass · re-stamped done` | no test reaches a log with `debt` above `done` and clean findings (`T2`); `check` is the lowest seam, the `run` closes the acceptance |

End-to-end runs added: one, in `test_a_done_under_the_top_line_is_stamped_again`, on the fake host, not slow. `I16` table: none removed.

`tests/test_skills.py` is not edited: it holds the `I` and `T` ids and labels equal across the skills, not their text, so the rows' wording is the build's to keep the same. Existing
tests that name "the status log has no done" (`tests/test_conduct.py`) hold logs with no `done` at all, and stay green.

## Dependencies

None.

## Risks / Trade-offs

| risk | mitigation |
|---|---|
| 0108-converge-script writes the log through `S`'s `main` and, in `K`, `conduct.py` and `worker.md`, edits what this change edits | `beside`: nothing waits; `mf-integrate` merges, and 0108's catch-up judges R6 under the new D39 |
| a legitimate flow stamps an event after a top `halt` | an answered halt opens a new `## Run` ([K:194-204](../../../skills/mf-converge/SKILL.md)); a lock halt resumes in place ([K:191](../../../skills/mf-converge/SKILL.md)), and [D1](#d1) spares it |
| the re-stamp writes through a worker-writable run directory | `S`'s `write` refuses a link and stages a `.tmp` with `O_NOFOLLOW`; the check reads both findings files and the tree first |
| a log with `debt` above `done` still reads as an unfinished run at `stage_of` | the converge that runs goes on at Step 10, writes `done` on top, and the check passes as it did |

## Verdict

Build in phases, each green on its own: `stamp.py` and its test; the converge check and its test; D39 and its copies.
