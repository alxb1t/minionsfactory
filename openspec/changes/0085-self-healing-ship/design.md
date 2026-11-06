# Self-healing ship — design

A stronger rescue and conductor, no supervisor: the rescue amends at `amend needed`, decides under the version's switch, and the
run takes back every halt answered on disk until nothing can move. Verdict at the end: ready to build.

## Context

Read at `95dcad0` (v0.67.0). The brief's facts were read at `f349aa8`; `git diff --name-only f349aa8..HEAD` names
`docs/decisions.md` and `openspec/specs/sdd/spec.md` of the paths they cite, so D47, D53, D56 and the spec were re-read; the rest
stand. `C` is `skills/mf-ship/scripts/conduct.py`, `R` is `skills/mf-rescue/SKILL.md`, `T` is `tests/test_conduct.py`.

- **F1. Rescue today.** `RESCUED` (`C:82`), `RESCUES = 3` (`C:83`), `AMENDS = ("tasks.md", "design.md")` (`C:84`). `Run.held`
  (`C:2840-2857`) picks what a failed check is rescued on; `advance` spawns the rescue on a halt met on entry with `()`
  (`C:2933-2940`) and after a failed check with `AMENDS` at a build alone (`C:2984-2997`). `_amend` (`C:1978-2002`) takes one commit,
  its subject the amend's, a `Rescue:` trailer, `amends` paths alone. R's kind table (`R:53-63`) has no `amend needed` row; a fix
  needing a decisions row is a diagnosis (`R:68-70`).
- **F2. The `amend needed` gap.** With `()`, a rescue's amend at `amend needed` is refused, `rescue touched …` (`C:1993-1994`);
  `rescue`'s `finally` calls `hold` (`C:2796-2797`), which reads `AMENDED` and freezes the version in `self.answered`
  (`C:2821-2838`); `take_back` then refuses it (`C:3323-3328`). The person's own amend during a rescue freezes it the same way.
- **F3. The loop.** `join` (`C:3498-3511`) polls `take_requests` and `_unblock`, joining each live thread for up to `REJOIN_POLL`
  in turn; a halt answered on disk is re-read only by a request or a new run. `closing` (`C:2657-2664`); `report`'s rescue lines
  map `fixed` to `rescued` and print any other kind as it is (`C:4129-4131`); `EVENTS` (`C:68-72`).
- **F4. Models.** `_table` (`C:1881-1893`) reads named tables alone; `read_plan` (`C:3204-3226`) reads `[rescue] skip` and
  `[converge] auto_grant` once a run, beside the plan. `PROMPTS["rescue"]` (`C:172`).
- **F5. Cards.** A card's **Fix** holds its suggested fix and size (`skills/mf-converge/references/worker.md:135-150`); at
  `amend needed` the fixer marks it `wontfix`, naming the amend, and the halt reads `amend needed — <card ids>`
  (`skills/mf-converge/SKILL.md:338`). Security blocks at `critical` and `high` (`BLOCKS`, `C:109`).
- **F6. The record.** D47 (`docs/decisions.md:466-498`) and D53 (`:521-546`) hold the freeze; D53 rejects "a rescue that changes a
  decision". `THREAT_MODEL.md:52-59` (the mailbox, the freeze) and `:64-75` (worker steering, a rescue writing the plan).
  `scripts/metrics/run.py:324-328` counts `fixed` and `diagnosed`; `metrics/catalogue.toml:383-399`.
- **F7. The `after` versions.** `0082-cut-station` writes `decide = "recommended"` at the models file's top from the brief, and no
  reader takes it there (its design's F7); it moves the rejoin mailbox to the home folder's queue, reads queued cuts at each poll
  in `take_requests`, splits `admit` out of `take_back`, adds D58, and amends D47, D51 and the threat model's mailbox paragraph.
  `0084-ship-fixes-2` adds the halt before round 1: `RERUN`, `Run.reruns`, and a refusal in `take_back`.

## Goals / Non-Goals

**Goals:** a run of fake workers that meets each Acceptance line of the brief: an `amend needed` halt converges again in its run;
a decided amend is taken under the switch and refused without it; an amend during a rescue goes on; a halt answered on disk
mid-run comes back with no request.

**Non-Goals:** a supervisor role (S1); a push notification (S4); a rescue for a timeout, a usage limit, a failed worker, a
`**HUMAN` phase or a stopped release.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | The rescue gets `AMENDS` at an `amend needed` halt, on entry and after a check; an accepted amend goes on; no `hold` after it | S6 (gap 4), S7 | a rescue only at a halt met after a check |
| [D2](#d2) | A security `critical` or `high` card the halt names gets `()`: a diagnosis | S7 | trusting the rescue skill alone |
| [D3](#d3) | The switch is the models file's top-level `decide = "recommended"`, read once with the plan, passed in the prompt | S2, P8 | `[rescue] decide`; an `AGENTS.md` line (D56) |
| [D4](#d4) | `_amend` takes a decided amend only under the switch, with `Decided-by: rescue`; `decided` is a rescue event kind | S7, S8 | a new event name |
| [D5](#d5) | `hold` lets an amends-only answer go on, logged `amended`; every other answer freezes as before | S9 (gap 3) | dropping the freeze for grants and merges |
| [D6](#d6) | `Run.recheck` at each poll takes back a halted version whose stage or `HEAD` changed on disk; each poll waits one `REJOIN_POLL` at most | S3, S9 | a request the run writes itself |
| [D7](#d7) | The run ends when no thread is live and no request, cut or re-check starts one; the close names each halted version's need and the decisions | S8, S10 | a new closing format |
| [D8](#d8) | D47 and D53 amended, D59 added; the threat model, the skills and the metrics | S11, S8 | — |

### D1

`_rescue_amends(runs, change, station, decide) -> tuple[str, ...]` in `C`, `station` the halted station: `"build"` →
`AMENDS`; `"converge"` with `amend needed` in `_converge_halt(runs, change)` → `AMENDS`, save [D2](#d2); else `()`. With
`decide`, a non-empty answer gains `"proposal.md"` ([D4](#d4)). Both rescue calls in `advance` take it: the entry path
(`C:2938-2939`) passes `"converge"` for the stage `converge-halted` and the stage itself otherwise; the check path (`C:2988`)
passes its `stage`, `build`, `converge` or `integrate`, in place of `AMENDS if stage == "build" else ()`. The entry path goes on when the rescue returns True:
`if rescued and self.rescue(…): continue`, else `return`.

`rescue` calls `hold` in its `finally` only when no amend was taken: an accepted amend leaves the stage `converge`, `AMENDED`,
and converge opens its `· amended` run. The `Rescue:` trailer at `amend needed` names the card ids, `Rescue: R4`.

R's kind table gains a row after the `verify: halt` row: `| converge's \`amend needed\` | fix | the amend its \`wontfix\` cards
name, in \`tasks.md\` and \`design.md\`'s prose |`, and a line under the table: a card of security severity `critical` or `high` is a
diagnosis, whatever the switch.

### D2

`_security_blocks(runs, change, halt) -> bool`: the ids after `amend needed — ` (`re.findall(r"\b[RS]\d+\b", …)`), each read in
`security.md` as `_open_blockers` reads a card (`CARD`, `_field`), true when one's `Priority` severity is in `BLOCKS["security"]`.
An unreadable file is true. The rescue then gets `()`, and writes its diagnosis.

### D3

`_decides(runs, change) -> bool`: the models file parses, as `_table` reads it, and its top-level `decide` is `"recommended"`.
`read_plan` reads it beside `_skips_rescue` into `self.decides: set[str]`, once a run: a worker writing it later changes nothing.
`PROMPTS["rescue"]` becomes `Run the mf-rescue skill for change {change}{decide}.`, `{decide}` being ` with decide=recommended`
for a version in `self.decides`, else empty.

R's *Parameter* section gains `decide=recommended`, from the conductor alone, and each line that confines the rescue to
`tasks.md` and `design.md`'s prose names the switch's exception: the fix rule under the kind table (`R:68-70`), Step 3a's staging
(`R:77`), and *Never*'s path line (`R:120`) and decision line. Under it, at a build halt and an `amend needed`
halt, the rescue takes the fix a card's **Fix** or the plan proposes as its decision: it may edit `proposal.md` and `design.md`'s
`## Decisions` too, and its commit adds `Decided-by: rescue` to the trailer block. It never edits the spec delta, code or a test,
takes a security `critical` or `high` card, approves a gate makefile, settles an integrate conflict, releases, merges, pushes or
answers a run-wide halt.

### D4

`_amend(tree, change, before, amends)` returns `(sha, why, decided)`. A **decided amend** touches `proposal.md`, or changes the
`## Decisions` section of `design.md` — the text from that heading to the next `## ` heading, `_show(tree, before, …)` against
`_show(tree, sha, …)`, a missing file read as empty. Without `proposal.md` in `amends` — no switch — a decided amend is `None`, `rescue changed a decision:
<path>`. With it, a decided amend whose `%(trailers:key=Decided-by)` is not `rescue` is `None`, `rescue commit <sha7> decided
with no Decided-by: rescue trailer`.

`rescue` logs `rescue — <id>: decided · <held> · <sha7>` for a decided amend, else `fixed` as today, and appends the change to
`self.decided`. `_amend`'s readers take the third value: `rescue`, and `test_a_rescue_outside_the_plan_halts` (`T:1580`), whose
expected tuples (`T:1619-1622`) gain `False`. `report` prints it as `<id> · decided <held> · <sha7>` through its existing kind rule.
`scripts/metrics/run.py` gains `"rescues-decided": lambda v: v.rescues("decided")`, and `metrics/catalogue.toml` an entry after
`rescues-diagnosed`, `title = "Rescues that decided for the person"`, the same group, unit, `better` and script.

### D5

`hold` returns a bool, True when the version goes on. Before freezing, it reads the halt it rescued: the stage on disk is
`converge`, the halt is `_amendable`, `_amended_only` holds past its head, and no commit in `<before>..HEAD` carries a `Rescue:`
trailer — the person's amends carry none, and a rescue amend `_amend` refused carries one — → clear the version's halts, log
`rescue — <id>: amended · <HEAD7>`, return True. Any other answer freezes as today, D53's grant, commit, merge and note
included. `rescue` returns True when `hold` does.

```
  rescue ends ─▶ amend taken? ─ yes ─▶ go on (D1)
                    │ no
                    ▼
               hold: stage on disk a halt? ─ yes ─▶ halted
                    │ no
                    ▼
               amends alone past the halt? ─ yes ─▶ go on · amended (D5)
                    │ no
                    ▼
               frozen for the run (D53)
```

### D6

`Run.recheck(threads) -> bool`, called by `join` after `take_requests` and `_unblock`. For each open version that `self.halts`
names, with no live thread, not in `self.blocked`, not in `self.answered`, and not an id `0082-cut-station`'s queue holds — a
queued cut joins through its own check alone, as in its `take_requests`: read `stage_of`. The **baseline** is
`self.seen_halts[change] = (stage, why, HEAD)`, which `Run.halt` writes for a version each time it halts, read from disk then
through `find_version`; a read that raises stores `None`, and the first poll's read replaces a `None`, taking nothing. A read
whose stage is not in `STUCK` and whose `(stage, why, HEAD)` differs from the baseline is a **candidate**; the same candidate read
at the next poll too → `take_back_safely(version, threads)`, and the entry is dropped. A fix written in steps — a commit, then a
file — is so read once it stands. It raises nothing, as `take_requests` does not, and returns whether it started a thread.

`join` waits one `REJOIN_POLL` window a loop: `deadline = time.monotonic() + REJOIN_POLL`, each live thread joined with
`max(0, deadline - time.monotonic())`. A rescue's end is read within one poll.

Overlap: `0082-cut-station` rewrites `take_requests` and `join` for its queue, and moves part of `take_back` into `admit`;
`recheck` calls `take_back_safely` as it stands after that merge. `0084-ship-fixes-2`'s `take_back` refusal for `Run.reruns` stands:
a halt before round 1 re-run at the same head reads unchanged.

### D7

`join` returns when no thread is alive and none of `take_requests`, `recheck` and `0082-cut-station`'s queued cuts starts one.

`closing` keeps its line and appends, after `released <tags>` and before `unpushed`: ` · decided <ids>` when `self.decided`
holds any — the `done` line (`C:3686`) gains the same part after its tags, so a run that releases names its decisions too — then ` · needs <id> <action>, …` for each halted version, `run` skipped. `_needs(version) -> str`, the first that
fits:

| the version | its need |
|---|---|
| in `self.answered` | `a re-run` |
| in `Run.diagnosed`, which `rescue` and `diagnose` fill as they log `diagnosed` | `rescue.md` |
| stage on disk `converge-halted` with `cap reached` | `a grant or a re-plan` |
| stage on disk `integrating` | `the merge settled` |
| stage on disk `human` | `its **HUMAN phase` |
| any other, or a read that raises | `a fix` |

e.g. `run · halt — halted 0001-a 0002-b · blocked none · released v0.3.0 · needs 0001-a rescue.md, 0002-b a fix`.

### D8

- **`docs/decisions.md`** — **D59 · A run heals its own halts**, after D53, its id added to the diagram's *Repo conventions* list (`docs/decisions.md:15`): the rescue amends at `amend needed`; under
  a version's `decide = "recommended"` it takes a card's or the plan's proposed fix, `proposal.md` and `design.md`'s
  `## Decisions` included, with `Decided-by: rescue`, never S7's never-list; the person's amends during a rescue let the version
  go on; each poll takes back a halt answered on disk; the run ends when nothing can move, its close naming each need and
  decision. **Why:** a supervising chat answered every halt of 2026-11-05/06, ~70% of them the line's gaps. **Rejected:** a
  supervisor role · `[rescue] decide` · an `AGENTS.md` switch (D56) · a request the run writes itself · a push notification.
  **D53** — "It may fix a build halt" → "It may fix a build halt or an `amend needed` halt"; "never `design.md`'s decisions table"
  → "never `design.md`'s decisions table, save under D59's switch"; the freeze sentence gains "save the person's amends, which
  let the version go on"; *Rejected*'s "a rescue that changes a decision" → "a rescue that changes a decision with no switch".
  **D47** — "nor one whose converge or integrate halt was answered while its rescue ran, the person's own fix included" gains
  ", save by the person's amends alone", and "A live run takes a rejoin request" gains "and, at each poll, every halt answered
  on disk ([D59](#d59--a-run-heals-its-own-halts))". `0082-cut-station` amends D47 and D51 too: the build edits the text as it
  stands after that merge.
- **`THREAT_MODEL.md`** — the mailbox paragraph's freeze sentence gains the amends exception; the worker-steering paragraph
  gains: under a version's switch, a rescue commits a worker-written card's fix — the class accepted on 2026-11-01 — bounded by
  D59's paths, the `Decided-by:` check and the switch the plan reads once a run.
- **`skills/mf-ship/SKILL.md`** — the `rejoin` row (`:55`) and the `run · live` row (`:85`) gain the amends exception and the
  run's own re-check; the diagnosed row (`:90`) gains `<change-id> · decided <sub-task> · <sha>`; the frozen row (`:91`) names the
  amends exception; the closing sentence (`:123`) gains ` · decided <ids> · needs <id> <action>`.

## Tests

`git grep -c '^def test_' -- tests/` totals 221 at the cut, 106 in `tests/test_conduct.py`. Added: 4 integration tests of the
conductor, each a run of `tests/fake_worker.py`. No end-to-end test. Each is marked `slow` when it runs over 5 s (`T1`).
`T2`: the rescue tests (`T:1480-1688`) reach a build halt alone, and none reaches `amend needed` or a poll's re-check.

- `test_a_rescue_amends_at_amend_needed` — the fake's new `amend-halts` converge mode halts `amend needed — R1` with a
  `wontfix` review card, then converges clean once an amend stands; the new `rescue-prose` rescue mode commits a `design.md` prose
  amend with `Rescue: R1`. The version converges in a `· amended` run and releases in the same run; the log holds
  `rescue — <id>: fixed`. A run whose one version stands halted that way on disk at its start, beside a second version that
  builds, gets the same through the entry rescue. With the card in `security.md` at `high`, the rescue's prompt runs with no
  amend taken and the version stays halted.
- `test_a_rescue_decides_under_the_switch` — the new `rescue-decides` mode edits a row of `design.md`'s `## Decisions` with
  `Decided-by: rescue`. With `decide = "recommended"` atop the models file: taken, `rescue — <id>: decided`, the closing line's
  ` · decided <id>`, `report`'s `<id> · decided` line, and the rescue's prompt ends `with decide=recommended`; a run that releases ends its `done` line ` · decided <id>`. Without it: halted,
  `rescue changed a decision: openspec/changes/<id>/design.md`. With the switch and no trailer: halted, naming the trailer.
- `test_an_amend_during_a_rescue_goes_on` — the new `rescue-person-amends` mode commits the person's amend and no `Rescue:`
  trailer: the version goes on, `rescue — <id>: amended`. The `rescue-answers` grant in `test_a_grant_buys_one_round` still
  freezes.
- `test_a_halt_answered_on_disk_comes_back` — one version halts while a held one builds; `_when_logged`'s act commits a fix on
  its branch and writes no request: the run logs `rejoin — <id>: <stage>` and releases it. A second, halted on a timeout with
  nothing changed, stays out, and the closing line ends `needs <id> a fix`. `REJOIN_POLL` is set to 0.1 through
  `conduct["main"].__globals__`, as `T:1274` sets it.

Extended or edited:

- `tests/test_metric_scripts.py::test_run_metrics_read_the_run_logs` — a `rescue — 0001-x: decided · 2.2 · abc1235` line at the
  existing `fixed` line's time, so `wait-minutes` stays 516.5, and `"rescues-decided": 1`.
- `test_a_rejoined_dependency_brings_its_chain_back` (`T:1268`) and `test_a_fixed_version_rejoins_a_live_run` (`T:1785`) — each
  act resets the fake's modes first, then commits the fix and writes `_done`, then requests: a re-check between those steps takes
  nothing, as the candidate must read the same at two polls.
- `tests/test_conduct.py` — each closing-line assertion that ends on a version halted at the close gains its ` · needs …` part.
  `grep -n 'run · halt — halted ' tests/test_conduct.py` lists them.

No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- A decided amend that passes the path and trailer checks is a worker's decision: converge reads the whole change after it, and
  the close and `report` name it for the person (D59, the threat model).
- A re-check every poll reads each halted version's stage from disk: git calls bound by the halted versions' count, every 10 s.
- `_needs` reads the stage at the close: a stage changed after the last poll names what it needs then.
- The person's amend during a rescue at a cap answers nothing (`_amendable`), so it freezes as before.
- A rescue that commits an amend with no `Rescue:` trailer reads as the person's, and the version goes on: worker steering, in the
  class the threat model accepts; `_amended_only` still holds it to the change's folder, and converge judges it.

## Verdict

Ready to build.
