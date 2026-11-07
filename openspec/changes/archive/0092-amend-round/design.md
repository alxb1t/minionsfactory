# Amend round — design

An answered converge halt opens one amend round, a catch-up run marked `· amend` over `<judged head>..HEAD`, in place of the
`· amended` reopen from round 1 and the person's by-rule amends. Skill text, conductor code, run metrics and decision text.
Verdict at the end: ready to build.

## Context

Read at `bb4cf51`, the brief's own sha and this cut's `HEAD`: every fact citing a path stands. `S` is
`skills/mf-converge/SKILL.md`, `W` is `skills/mf-converge/references/worker.md`, `C` is `skills/mf-ship/scripts/conduct.py`, `F`
is `tests/fake_worker.py`, `T` is `tests/test_conduct.py`, `M` is `scripts/metrics/run.py`. 0088's, 0089's and 0090's change
directories are read with `git show <id>:openspec/changes/<id>/…` (0088's under `archive/`) and cited as `0089 D<n>`. See
[the proposal](proposal.md) for why.

- **F1. The reopen.** `S:151-154` opens a run marked `· amended` at Step 1 over the whole change, writing `round: 1`, for a halt
  whose head both findings files judged. `S:156-163` sends the person's amends at a clean catch-up, `verify: halt` or clean
  `amend needed` halt to the catch-up round, a `Rescue:` amend there to one Step 7 round, and calls a halt past the judged head
  "no person's answer".
- **F2. The catch-up.** `S:185-220`: its own count for merges and amends (`S:205-209`), By rule for merges and amends alone save a
  `Rescue:` amend (`S:211-214`), and item 5 freezes `<judged head>..HEAD` (`S:215-218`). By rule skips each amend (`S:232`) and
  writes a line per amend (`S:237`). Step 7 names the own count (`S:377-378`).
- **F3. The workers.** `W:16` is the stale-claim pass over the tree outside the diff; `W:20-22` judges the explicit range;
  `W:106-107` keeps an amend card's `wontfix`, never `accepted`.
- **F4. The answer in the conductor.** `_answered` (`C:870-902`) takes a halt before round 1 by any commit (`C:890-891`), an
  `_amendable` halt by `_amended_only` with no judged-head check (`C:892`), and else wants both files' `head:` to be the halt's.
  `_amendable` (`C:828-842`) reads `_run_marked(…, "catch-up")` (`C:836`); its other reader is `Run._amended_alone`
  (`C:3224`). `_amended_only` (`C:845-867`) lists `rev-list --parents <halted>..HEAD`. `stage_of` returns `AMENDED` on an
  answered halt (`C:1131-1132`), and `_check_converge` reads `_answered` too (`C:1163`).
- **F5. The metrics.** `Version.rounds` skips a heading ending `· catch-up` (`M:342-352`); `Version.grants` counts `· grant`
  headings (`M:371-373`); `METRICS` lists `grants` (`M:527`); `metrics/catalogue.toml:338-345` is the `grants` entry.
- **F6. The fake.** `_findings` writes `round: 1` (`F:43-50`); `_by_rule` passes merges and the person's amends (`F:133-167`),
  through `_person_amends` (`F:123-130`); the `amends` and `amend-halts` modes insert `## Run 2 — d · amended` (`F:463-465`).
- **F7. The tests that read it.** `T:1646` and `T:6265` assert `· amended`; `T:6287-6313` asserts a commit after the person's
  amend answers nothing; `T:6314-6320` asserts a catch-up halt over a findings file no longer clean stands; `T:6324-6331` runs
  the person's amend by rule; `T:1839` is `test_a_drift_amend_goes_on_by_rule`; `T:6181` is
  `test_a_fix_after_a_cap_halt_converges_afresh`, named at `T:6397` and `T:6419`. `test_run_metrics_read_the_run_logs`
  (`tests/test_metric_scripts.py:470-498`) reads `_STATUS` (`:382-394`).
- **F8. The overlap.** 0088 rewrites S's event line (`S:64-69`) for `stamp.py`; 0089 D9 writes `Supervisor:` into `S:160`,
  `S:196` and `S:212`, and "the supervisor's" into `S:206`; 0089 adds `skills/mf-supervise/SKILL.md`, whose role line ends
  "and converge reads the whole change in a round."; D6 edits `_amended_alone`'s trailer line, D10 edits D15, D47, D53, D60, the principles' *A merge*
  bullet and adds a `THREAT_MODEL.md` paragraph ending "and a catch-up passes it by rule."; 0089 extends
  `test_run_metrics_read_the_run_logs` and adds D61, which 0090 edits. Every S passage 0089 edits is one this change replaces whole.
- **F9. The words.** `wc -w skills/mf-converge/SKILL.md skills/mf-converge/references/worker.md` prints `5155`, `2253`, total
  `7408`; `converge-reading-set` is 19,667 against a watch of 10,500.

## Goals / Non-Goals

**Goals:** the brief's Acceptance with the fake worker — a halt answered by a two-line amend ends in one judge round over its
range and the version goes on, no run restarting at `round: 1`; an amend adding a phase brings the build's code into the range;
an amended `Verify:` that fails halts naming it; the converge skill and its worker reference hold fewer than 7,408 words;
`make gate` green.

**Non-Goals:** the rest of the token diet; a rescue amend at a `verify failed` halt; `gate_check.py`.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | An answered halt opens a catch-up run marked `· amend` over the files' `head:`, whatever their verdicts | A1, A3, A7 | a full reopen, a decision amend included; a new section beside the catch-up, which already freezes the range and counts its own rounds |
| [D2](#d2) | A halt is answered by any commit when both files judged its head, else by an amend among the commits past it, in `_answered` and the skill alike | A5, A6 | amends alone, which leaves an added phase's build code halted; `_amendable`'s list of kinds |
| [D3](#d3) | Each `Verify:` line the range adds to `tasks.md` runs before the round's `start`; one that fails halts `verify failed — <ids>` | A2 | after `start`, where a person's code fix answers nothing; every `Verify:` |
| [D4](#d4) | The amend round has the catch-up's own count: one judge round, at most one fix round, a blocker left `cap reached` under D56 | A4 | a fresh cap of three per amend |
| [D5](#d5) | By rule takes merges alone; no amend passes by rule | A6 | by rule for the person's amends (`0071·S2`) |
| [D6](#d6) | The worker reference's amend scope: the whole range, the full plan, each changed claim searched, a settled amend card `verified` | A1, A3 | reopening a settled amend card, as any `wontfix` whose justification no longer holds |
| [D7](#d7) | The mark `· amend`: `_amendable` reads it as `· catch-up`, `converge-rounds` skips it, `amend-rounds` counts it | A8 | keeping `· amended`, whose runs restarted at round 1, in one series |
| [D8](#d8) | The record: D63; D15, D47, D53, D60; the principles; `THREAT_MODEL.md`; `mf-rescue`'s and `mf-supervise`'s role lines | A3, A8 | a decision edited outside `docs/decisions.md` |

### D1

S's *Resuming a run* loses F1's two paragraphs, and the catch-up takes the answered halt. Each passage below replaces the one
named, whole; 0089's `Supervisor:` words go with them (F8).

- **The answered halt** — the paragraphs from "The top line is any other `halt`" through "is no person's answer." become:

> **An answered halt:** the top line is any other `halt`, `HEAD` descends from its `· head <sha>` and is not it, and both
> findings files' `head:` is `<sha>`, or `git rev-list <sha>..HEAD` names an **amend**: one parent, the subject
> `docs(<change-id>): amend the change directory`, paths under `openspec/changes/<change-id>/` alone. Open a catch-up run marked
> `· amend`, naming the halt in its first event, and run the [Catch-up round](#catch-up-round) from the files' `head:`, whatever
> their verdicts; no grant is needed. Files missing, or naming two heads → a plain new run. Any other halt is no answer.

- **A halt before round 1** — its last sentence, "A catch-up run halted before its `start` … so the commits since are judged.",
  becomes "A catch-up run halted before its `start` — in its catch-up check or Step 1 — is one too: a new run of its mark runs the
  [Catch-up round](#catch-up-round) again, so the commits since are judged."
- **The catch-up's check** — "and their `head:` is not `HEAD`:" → "and their `head:` is not `HEAD` — or in a run marked
  `· amend`, whatever the files say:". So the new run D1's halt-before-round-1 sentence opens, at the same head, runs the round
  too.
- **The status log's run** — "so a catch-up run's heading ends `· catch-up`" → "so a catch-up run's heading ends `· catch-up`,
  or `· amend` after an answered halt".
- **The diagram** — the five lines from `merges and amends?` through the `freeze <head>..HEAD` line become these four, the
  `freeze` line's `─` run before `┐` padded so the `┐` stands over the `│` below it:

```
  merges, amends or · amend? ── no ─▶ round < 3 ? ── no ─▶ halt: revert the late commits, or re-converge from round 1
               │ yes, its own count          │ yes
               ▼                             ▼
  merges only, replay? ── no ─▶ freeze <head>..HEAD ─▶ Step 7 verify ─┐
```

- **The run's mark** — "Open the run marked `· catch-up`, and write" → "Open the run marked `· catch-up`, or `· amend` after an
  answered halt, and write".
- **Step 7** — "A catch-up over merges and amends has [its own count](#catch-up-round)." → "A catch-up over merges and amends,
  or an answered halt's, has [its own count](#catch-up-round)."

**Words.** The passages D1, D3, D4 and D5 replace are longer than their replacements and D6's sentences, by more than 0088's
longer event line adds back. The measure is F9's command, run at sub-task 1.8 against F9's total.

### D2

One rule answers a halt with a head, past its head: the files judged that head, so any commit is an answer; or an amend follows
it, whatever its kind and whoever wrote it. Converge's range starts at the files' `head:` either way, so a person's further
commit, the build's code for an added phase and converge's own unverified fix are all judged. A halt before round 1 keeps its
own rule (any commit), and the rescue's hold keeps `_amended_alone`'s stricter one (0085 D5).

In C, beside `_amended_only`:

```python
def _amends(tree: Path, change: str, halted: str) -> list[bool]:
    """Return, per commit past `halted`, whether it is an amend of the change directory.

    An amend has one parent, the amend's subject, and paths under
    `openspec/changes/<change>/` alone. None is listed unless `halted` is an ancestor
    of `HEAD` and not it. Why: 0071-ship-fixes design D5; 0092-amend-round design D2.
    """
```

It holds `_amended_only`'s head check, listing and per-commit test, appending one bool per `rev-list --parents` line.
`_amended_only` becomes `amends = _amends(tree, change, halted)` and `return bool(amends) and all(amends)`, its docstring
"Return whether only amends of the change directory follow `halted`." and its `Why:` line. In `_answered`,
`if _amendable(runs, change, halt) and _amended_only(tree, change, halted):` becomes `if any(_amends(tree, change, halted)):`.
In `Run.advance`, the comment "An answered halt converges afresh or catches up:" (`C:3357`) becomes "An answered halt gets one
amend round:". `_answered`'s docstring reads:

```
Return whether a commit answered a converge halt.

The halt names the head it stopped at, `HEAD` descends from it and is not it,
and both findings files judged that head, or an amend of the change directory
follows it: converge judges the range from the files' head in one amend round. A
rewritten history leaves no descendant, and a halt before round 1 is answered
by any commit. Why: 0071-ship-fixes design D5; 0084-ship-fixes-2 design D1;
0092-amend-round design D2.
e.g. "… · halt — cap reached · head 7ee2179", `HEAD` a fix past 7ee2179 → True
```

### D3

S's catch-up item 3, "**Run Step 1's preconditions.**", becomes:

> 3. **Run Step 1's preconditions**, and before `start` each `Verify:` line the range adds to `tasks.md`, ticked or not: one that
>    fails → halt `verify failed — <sub-task ids>`.

The range's lines are `git diff <judged head>..HEAD -- openspec/changes/<change-id>/tasks.md`'s added lines holding `Verify:`;
converge's conductor runs each through Bash, as the build does, and `conduct.py` runs none. A halt there has no `start`, so it is a halt before round 1: `conduct.py` re-runs it once
at its head and takes any commit past it, the person's code fix or an amend of the `Verify:`, with no rescue (F4). A new run of
the `· amend` mark runs the round again, per D1. `gate_check.py`, which adopts an amended `Verify:` without running it, stays.

### D4

S's catch-up item 2, the sentence from "**Merges and amends** — merges," through "carries on past three.", becomes "**Its own
count** — an `· amend` run, and a selection of merges and [amends](#resuming-a-run), have one judge round and at most one fix
round, and `round:` carries on past three." Item 6's `cap reached` stands, and with it D56's grant of small cards.

### D5

- S's catch-up item 4 becomes "4. **Merges alone → try [By rule](#by-rule).** Every merge replays → Step 9, never Step 8: no
  freeze, no worker. A selection holding an amend, and an `· amend` run, never pass by rule." An answered halt's open blockers
  stay for its round to judge, never a clean by-rule write over them.
- By rule item 1 loses "Skip each amend: Step 1's gate and `gate_check.py` judged it."; item 3 loses "and one per amend —
  `- <sha>: the person's amend` — ".
- F's `_by_rule` takes merges alone: a selection holding any other commit returns None, and `_person_amends` goes.

### D6

W's edits:

- **Scoping** gains, after its first sentence: "An **amend round** judges its whole range with the full plan in its reading set."
- **The stale-claim row**: "for every path, symbol, verb, route or count the diff renames, deletes or changes" → "for every path,
  symbol, verb, route or count the diff renames, deletes or changes, and in an amend round each claim the amend changes".
- **The verify pass** gains, after "A justification that does not hold reopens it, as any `wontfix`.": "In an amend round, an
  amend card the amend settled goes `verified`, naming it."
- **The Status diagram**: its line "an amend card's wontfix stays wontfix" → "an amend card's wontfix stays, till an amend
  settles it".

A settled amend card's justification no longer holds, so without the sentence it would reopen, and the fixer would have nothing to
fix.

### D7

- **C** — `_amendable` reads `_run_marked(runs, change, "catch-up") or _run_marked(runs, change, "amend")`; its docstring's first
  line becomes "Return whether the person's amend during a rescue answers a converge halt of this kind.", its kinds "a halt in a
  catch-up or amend run with both findings files still clean", and its `Why:` line gains `0092-amend-round design D7`.
- **M** — `Version.rounds` skips a heading ending `· catch-up` or `· amend` (`str.endswith` with both), its docstring "Return the
  highest round a run that is no catch-up or amend run reached."; `Version.amends(self) -> int`, beside `grants`, counts headings
  ending `· amend`, its docstring "Return the converge runs marked as an answered halt's amend round."; `METRICS` gains
  `"amend-rounds": Version.amends` after `"grants"`.
- **`metrics/catalogue.toml`**, after the `grants` entry: `id = "amend-rounds"`, `title = "Amend rounds after an answered halt"`,
  `group = "run"`, `unit = "rounds"`, `better = "lower"`, `script = "scripts/metrics/run.py"`, `args = ["amend-rounds"]`.

### D8

- **D63**, at the end of *The check loop and the release* in `docs/decisions.md`, after D50, and its id after D50 in the map's
  `D11…D17, D40, D43, D49, D50` list:

> ### D63 · An answered amend gets one round over its range
>
> **A converge halt answered past its head — by any commit when both findings files judged that head, else by an amend of the
> change directory, the person's, the rescue's or the supervisor's — opens one amend round: a catch-up run marked `· amend` over
> `<judged head>..HEAD`, holding the amend, the build's code for a phase it added and converge's own unverified fix. Before its
> `start` it runs each `Verify:` the range adds to `tasks.md`; then one judge round and at most one fix round, a blocker left
> `cap reached` ([D56](#d56--the-cap-policy)). No amend passes by rule. The checkers keep the full plan, and the stale-claim pass
> searches the whole tree for each claim the amend changes.**
>
> - **Why:** an amended run restarted at round 1 over the whole change with a fresh cap of three: 24% of converge's spend, a
>   two-line amend buying a 13-file round, and 0087's and 0088's loops. A scoped round would have missed one nit; the
>   stale-claim pass and the `Verify:` re-run catch what an amend breaks outside its diff.
> - **Accepts:** code an amend contradicts outside the range, which only the stale-claim pass searches · a decision or
>   spec-delta amend judged in one round.
> - **Rejected:** a full reopen after a decision amend · a fresh cap of three per amend · by rule for the person's amends.

- **D15**, its drift line as 0089 leaves it, "… answers it." → "… answers it, in one amend round
  ([D63](#d63--an-answered-amend-gets-one-round-over-its-range))."
- **D47**: "A clean catch-up, verify or `amend needed` halt followed only by the person's `docs(<id>): amend the change
  directory` commits is answered." → "A converge halt followed by an amend of the change directory, or by any commit when the
  findings files judged its head, is answered, and gets one amend round
  ([D63](#d63--an-answered-amend-gets-one-round-over-its-range))."
- **D53**, its Why: "and converge judges the whole change after it." → "and converge judges the amend and every claim it changes
  ([D63](#d63--an-answered-amend-gets-one-round-over-its-range))."
- **D60**, its Accepts: "converge reads the whole change after it" → "converge judges the amend and every claim it changes".
- **`docs/principles.md`**: *Nothing reads as clean by being absent*, "a catch-up over merges and the person's amends, whose every
  merge" → "a catch-up over merges alone, whose every merge"; *Every edit opens a round*, the *A merge* bullet as 0089 leaves it
  becomes "- **A merge or an amend:** a catch-up over merges and amends, and an answered halt, counts its own rounds: one judge
  round, at most one fix round ([D63](decisions.md#d63--an-answered-amend-gets-one-round-over-its-range))."
- **`THREAT_MODEL.md`**, *Out of scope*: "and converge reviews the whole change after it." → "and converge judges the amend and
  every claim it changes."; in 0089's supervisor paragraph, "and a catch-up passes it by rule." → "and converge judges it in an
  amend round, as every amend."
- **`skills/mf-rescue/SKILL.md`**, its role line: "and converge judges the whole change." → "and converge judges your amend in
  one round."
- **`skills/mf-supervise/SKILL.md`**, 0089's role line: "and converge reads the whole change in a round." → "and converge judges
  your amend in one round."

## Tests

`git grep -c '^def test_' HEAD -- tests/test_conduct.py` prints 119 at the cut; 0088 adds none there, 0089 six and 0090 three
(their `## Tests`), so the build starts from 128. Added: one conductor test, at the lowest layer that holds its behaviour (`T1`):
its full runs use `tests/fake_worker.py`, as the rescue tests do, and it carries `slow` only if it runs over 5 s. Extended and
edited: the conductor tests F7 names, and `test_run_metrics_read_the_run_logs`. No end-to-end test: the repo has no browser
layer. `T2`: `test_a_fix_after_a_cap_halt_converges_afresh` reaches an answered cap halt, and the new test's halt past the judged
head, added phase and failed `Verify:` are states no existing test reaches.

| test | layer | asserts |
|---|---|---|
| `test_an_amend_past_the_judged_head_gets_one_round` | fake run, then unit | `0001-todo` ticked, `_findings` at `judged` with `"blocking"`, a `fix(0001-todo): R1` commit `fixed` on `src.txt`, `_done` at `fixed`, the log `## Run 1 — d` with `10:00:01 · round 1 · halt — amend needed — R1 · head <fixed>` over a round 1 `start`: the stage is `("converge-halted", <the halt>)`. A two-line amend of `tasks.md` (`Amended.` and `Twice.`), its subject the amend's: the stage is `("converge", AMENDED)`; with `fake("amends")` the run exits 0, the calls are `probe`, `converge 0001-todo`, `release 0001-todo`, the status log starts `# t\n\n## Run 2 — d · amend\n` and holds `· round 2 · freeze — <judged>..<amend>`, no line of that run holds `· round 1 ·`, and `review.md` holds `round: 2`. Then, in `_primary(tmp_path / "phase")`, the same halt answered by an amend adding `- [ ] 2 — Two` to `## Progress`: the stage is `("build", "phase 2 unticked")`; the run exits 0, the calls are `probe`, `build 0001-todo`, `converge 0001-todo`, `release 0001-todo`, and the log holds `· round 2 · freeze — <judged>..<the fake build's commit>`. Then, in `_primary(tmp_path / "verify")`, the first setup and amend with `fake("verify-fails")`: the run exits 1, its calls start `probe`, `converge 0001-todo` and hold no `release` or `rescue`, and a run-log halt line holds `verify failed — 1.1`; the stage is `("converge", RERUN)`, and after a person's commit on `src.txt` `("converge", AMENDED)`. Then `_findings` clean at `HEAD` and the log `## Run 3 — d · amend` over `10:00:00 · round 2 · halt — red · head <HEAD>`: `_amendable` is True; with the heading `## Run 3 — d` it is False |
| `test_a_fix_after_a_cap_halt_converges_afresh` → `test_a_fix_after_a_cap_halt_gets_one_round` | edited | renamed; `· amended` → `· amend` at `T:6265`; the halts loop at `T:6292-6313` keeps `stage_of == amended` at `amended_head`, adds that a person's commit past `amended_head` still reads `amended`, makes its refused commits, the `src.txt` commit and the amend touching `src.txt`, from `merged` (`git reset -q --hard <merged>` first), so neither follows an amend, and drops the side-merge case; the comment above the loop, "The person's amends answer a clean catch-up halt, a verify halt and an `amend needed` halt; any other commit past the halt does not.", becomes "An amend answers a halt past the judged head, and a commit after it is judged in its round; a commit with no amend before it answers none."; `T:6314-6320` asserts `amended` for the catch-up halt over a findings file no longer clean, its comment "A catch-up halt over a findings file no longer clean is answered too: the amend round re-judges it."; `T:6324-6331` runs `fake("amends")` and asserts the status log starts `# t\n\n## Run 2 — d · amend\n` in place of the by-rule line |
| `test_a_drift_amend_goes_on_by_rule` → `test_a_drift_amend_answers_its_halt` | edited | renamed, its assertions kept |
| `test_a_rescue_amends_at_amend_needed` | edited | `· amended` → `· amend` at `T:1646` |
| `test_a_verify_halt_is_diagnosed_without_a_worker`, `test_a_halt_before_round_1_runs_again_at_the_same_head` | edited | their comments at `T:6396-6397` and `T:6419` name `test_a_fix_after_a_cap_halt_gets_one_round`; `T:6396`'s "the version converges afresh, as" → "the version converges again, as": with no findings file, that run is a plain new one ([D1](#d1)) |
| `test_run_metrics_read_the_run_logs` (`tests/test_metric_scripts.py`) | extended | `_STATUS` gains, above `## Run 3`, `## Run 4 — 2026-11-02 10:00 · amend` over `10:30:00 · round 8 · done — converged in one amend round`; `expected` gains `"amend-rounds": 1`, `converge-rounds` staying 4 |

The fake's edits:

| where | what |
|---|---|
| `_findings` | a `round: int = 1` parameter, written as `round: <round>` |
| `_by_rule` | merges alone, per [D5](#d5); `_person_amends` deleted, and with it `_by_rule`'s `change` parameter and its argument at the call; its docstring "Return a line per merge when a catch-up selects merges alone, each replaying." |
| the converge branch, `amends` and `amend-halts` modes | before `_findings`, read review's `head:` as `judged` (else `HEAD`); `_findings(…, round=2)`; insert `## Run 2 — d · amend\n10:00:01 · round 2 · done — ok\n10:00:00 · round 2 · freeze — <judged>..<HEAD>\n\n` above the held log's first `## Run` |
| the converge branch, mode `verify-fails` | before the `before` table: insert `## Run 2 — d · amend\n10:00:00 · round 2 · halt — verify failed — 1.1 · head <HEAD>\n\n` above the held log's first `## Run`, and return |

The new test and the edits cover every line the change adds, as the gate's diff coverage requires; a line they leave uncovered
gets a case in the test of its phase.

**Renamed tests** — no assertion is lost, and no scenario id moves to another code path (`I16`):

| removed name | carried by |
|---|---|
| `test_a_fix_after_a_cap_halt_converges_afresh` | `test_a_fix_after_a_cap_halt_gets_one_round`, the same body edited as the table above says |
| `test_a_drift_amend_goes_on_by_rule` | `test_a_drift_amend_answers_its_halt`, the same body |

After: 129 in `tests/test_conduct.py`. No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **A defect an amend causes outside its range** → the stale-claim pass searches the whole tree for each claim the amend changes,
  and the `Verify:` re-run catches an amended check gone red; 0087 Run 5's cards sat outside the amend's diff and are of that
  kind. One nit (0088 Run 2's R4) would have been missed.
- **A decision or spec-delta amend judged in one round** → the person accepted it (A3): the delta is in the range, and review reads
  the living specs it touches.
- **A failed amended `Verify:` gets no rescue** → it is a halt before round 1, re-run once at its head and answered by any commit;
  the person fixes the code or amends the check.
- **A person's commit after an amend is judged, not refused** → the range starts at the files' head, so it is read in the round;
  the rescue's hold stays on `_amended_alone`'s amends-alone rule.
- **The word budget is thin** → sub-task 1.8 measures it; a total at or above F9's halts the build, the plan's budget wrong.
- **The integrate merges with 0089 and 0090** → each S passage 0089 edits is replaced whole here; D15, D47, the *A merge* bullet,
  and 0089's threat-model sentence are edited as 0089 leaves them, per `after:`.

## Verdict

Ready to build.
