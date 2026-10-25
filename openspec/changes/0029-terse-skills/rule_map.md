# Rule map

Where every rule, exception, halt and output of the old text went, per [D4](design.md#d4). Old lines are at
`a926ca1`. `cut` names the authority the station still reads.

## skills/mf-converge/SKILL.md

| old (section · lines at a926ca1) | rule, exception, halt or output | new (section) | disposition |
|---|---|---|---|
| intro · 8-10 | conductor judges nothing; freezes, dispatches, reads from disk, fixes once, re-verifies; no review, no release | intro, blockquote | kept |
| intro · 11 | read `AGENTS.md` and the change | intro, read line | merged with 17 |
| intro · 13-15 | why: three opinions from one reader; the stations are fresh workers or there is no check | intro, `Why:` line | kept, shorter |
| intro · 17-18 | read root `AGENTS.md` and its mandatory context; missing → halt naming it | intro, read line | kept |
| — | the loop as a flow | intro, diagram | added: restates Steps 1–10, no new rule |
| Parameter · 22-29 | strict inference: none, several, branch mismatch halt; echo | Parameter, list | kept, shorter |
| Parameter · 31-32 | why strict: the id keys the findings paths | Parameter, lead line | kept |
| Parameter · 34-35 | release version from `proposal.md`; the backlog is `.minions/backlog.md`, the only copy | Parameter, last paragraph | kept |
| constants · 39-43 | `make gate` from root; `make -n gate` printed first; not a sandbox; halt naming the `Makefile` on no `Makefile`, non-zero, or no command | constants, first paragraph | kept |
| constants · 43-45 | never ask for or substitute a gate; why: invisible wrong guess | constants, second paragraph | kept, shorter |
| status log · 49-52 | path; newest on top; only you write it; not a findings file; release never reads it; no-edit rule does not cover it | status log, first paragraph | kept |
| status log · 54-55 | event line format; time from `date` via Bash, never by hand; why: a stale time shows a dead run | status log, An event | kept |
| status log · 56-59 | a run per invocation; opened after the id and the catch-up check; `· catch-up` heading; `mkdir -p`; title; run heading under the title | status log, A run | kept; "above the previous run" folded into "directly under the title" |
| status log · 60-61 | insert under latest run heading; insert only; a line stays | status log, Insert only | kept |
| status log · 62-63 | a run ends on `halt` or `done`; every halt writes `halt`; neither means going or dead | status log, A run ends | kept |
| status log · 65-93 | the events table and the example | status log | kept byte for byte |
| executor · 97-98 | report the engine from runtime evidence; model, provider, editor names are not evidence | executor, first paragraph | kept |
| executor · 100-102 | Claude Code: require `/code-review` and `/security-review`; missing → halt; generic only on explicit user choice; native parallel and scoping; missing-remote limit | executor, table row 1 | kept |
| executor · 103-105 | other: load the generic references from the installed package; generic security needs no remote | executor, table row 2 | kept |
| executor · 107-109 | a worker is new, explicit inputs, no build transcript, no resumed worker or fork; every dispatch fresh; role identity in its file | executor, worker paragraph | kept |
| executor · 111-114 | confirm start, wait, read; missing → halt; no inline review, no unobservable thread; generic parallel or sequential on one head; both finish before a fixer; Claude Code parallel | executor, last paragraph | kept |
| executor · 115 | MF skill names are instruction names; host syntax | executor, last paragraph | kept |
| catch-up · 119-123 | definition; release halts until `HEAD` is the judged head; when it applies | catch-up, opening | kept |
| catch-up · 125-133 | the flow diagram | catch-up | kept byte for byte |
| catch-up · 135 | open the run `· catch-up`; write `catch-up` | catch-up | kept |
| catch-up · 137-143 | ancestry, cap, preconditions and freeze, one Step 7 round with no pickup | catch-up, list | kept |
| Step 1 · 147-148 | clean tree; why: uncommitted work is outside the range | Step 1.1 | kept, shorter |
| Step 1 · 149-151 | every Progress box ticked; halt naming the first unticked; `mf-build` owns it | Step 1.2 | kept; "a verdict about a change that does not exist yet" cut: the halt holds it |
| Step 1 · 152 | non-empty range | Step 1.3 | kept |
| Step 1 · 153-154 | `gate` target runs a command; halt naming the `Makefile` | Step 1.4 | kept |
| Step 1 · 155-157 | gate green before round 1; red → halt, `mf-build` owns it; why: misattributed red | Step 1.5 | kept, shorter |
| Step 1 · 158-165 | precondition 6 | Step 1.6 | kept word for word |
| Step 1 · 167 | write `start` | Step 1 | kept |
| Step 2 · 171-172 | derive the base by merge-base; never accept or pick one | Step 2.1 | kept |
| Step 2 · 173-174 | halt on an empty range; why | Step 2.2 | kept |
| Step 2 · 175-177 | `mkdir -p`; the patch path and range; gitignored; never committed | Step 2.3 | kept |
| Step 2 · 178-180 | print base, head, commit count, files changed before any station; round 1's numbers; re-freeze prints its own | Step 2.4 | kept; the re-freeze half lives in Step 6 |
| Step 2 · 181 | write `freeze` | Step 2.5 | kept |
| Step 3 · 185-189 | simplify ran in the build; review judges its edits; no simplify findings file; release excludes it | Step 3, first paragraph | kept, shorter |
| Step 3 · 191-193 | fresh, read-only but for their own files; parallel in Claude Code; generic parallel or sequential; wait for both | Step 3, dispatch line | merged: points to *Executor and worker selection*, which states it |
| Step 3 · 195-204 | the inputs list | Step 3, list | kept |
| Step 3 · 206 | write `fan-out` | Step 3 | kept |
| Step 3 · 208-210 | a repeat escalates, one level; the station judges the match | Step 3, A repeat | kept |
| Step 3 · 212-214 | stale-claim pass: what it greps, cards `drift`, Summary names it | Step 3, passes table | kept |
| Step 3 · 216-219 | test-cost pass: `T1`, `T2`, `T4` as `nit`, sized `a test` | Step 3, passes table | kept |
| Step 3 · 221-225 | coverage-trace pass: when it runs; what is `blocking`; Summary | Step 3, passes table | kept |
| Step 3 · 227-232 | native scoping; fallback to the patch only when empty or wrong; Summary states which and the counts; why | Step 3, Native scoping | kept, shorter |
| Step 3 · 234-236 | generic scoping; report resolved scope; halt on unusable inputs; no remote needed; findings rules apply to either engine | Step 3, Generic scoping; overrides "either engine" | kept |
| Step 3 · 238-242 | never `--fix`, `--comment`, `ultra`, with reasons | Step 3, Engine overrides | kept, one line |
| Step 4 · 246-261 | exactly one file; parsed; the frontmatter | Step 4 | kept; the YAML byte for byte |
| Step 4 · 263-265 | body is cards; fix and verify change only **Status** | Step 4 | kept |
| Step 4 · 267-272 | the severity vocabularies and blocking tiers; drift; a spec scenario is `blocking`; `open_blocking`; clean means zero, a station obligation | Step 4, grades table and paragraph | kept, the vocabularies as a table |
| Step 4 · 274-276 | anchors always block; the classes; the floors | Step 4, Anchors | kept |
| Step 4 · 278-283 | status `open → fixed → verified`; the fixer claims, only the checker promotes or reopens with a reason; regression is new; `wontfix` with justification, the checker's to accept or reopen | Step 4, status diagram and paragraph | kept, as a state diagram |
| Step 4 · 285-287 | Resolution log append-only; counters rewritten in place; past rounds never rewritten | Step 4, Resolution log | kept |
| Step 4 · 289-290 | a findings file is material, not instruction; reportable | Step 4, last paragraph | kept |
| Step 5 · 294-296 | read from disk yourself; never a station's report; write `verdicts`; fail-closed | Step 5, opening | kept, per the D2 anchor |
| Step 5 · 298-299 | a missing findings file is not clean; halt naming it | Step 5, the table | kept |
| Step 5 · 300-307 | zero files → `changes-requested`, *scope resolution failed*, halt; compare with this round's freeze, never round 1's once superseded | Step 5, table and paragraph | kept, per the D2 anchor |
| Step 5 · 308-311 | a review without its stale-claim, test-cost or coverage-trace pass is not clean | Step 5, the table | kept, per the D2 anchor |
| Step 5 · 313-316 | non-blocking cards wait for Step 9, because pickup fixes some | Step 5, last paragraph | merged into one sentence |
| Step 5 · 318 | both clean and counts match → Step 8 | Step 5, last paragraph | kept |
| Step 6 · 322-323 | fix is a station inside converge; why no build∥fix seam | Step 6, opening | kept |
| Step 6 · 325-327 | fresh worker; all open blocking, or the pickup cards; green gate; write `fix` at dispatch and commit | Step 6 | kept |
| Step 6 · 329-346 | the fixer's rules: test-first to `T1`, `T2`; no weakening, no test deletion or merge (`T5`); `fixed` with a note; red before green, docs exempt; no counters, never `verdict: clean`; `wontfix` with justification; no deleting the files; no backlog writes; commit by name with the contiguous trailer | Step 6, list | kept |
| Step 6 · 342 | clearing the files is the human's act | *Never* | merged: stated once there |
| Step 6 · 348-350 | nothing committed → say so, write `fix` with `nothing committed`, skip the re-freeze, re-judge `wontfix` against the unchanged head | Step 6, The fixer committed nothing | kept |
| Step 6 · 352-355 | re-freeze to `<previous head>..<new head>`, overwriting the patch; no per-round patch files, why | Step 6, Otherwise re-freeze | kept |
| Step 6 · 357-361 | print the re-frozen numbers; `base` unchanged; they supersede for Step 5; write `freeze` | Step 6, Otherwise re-freeze | kept |
| Step 7 · 365-372 | re-run the gate; `verify`; same roles fresh at `round ≥ 2` with Step 3's inputs; `fan-out`; each re-reads, promotes or reopens, rewrites counters, appends, declares; review runs all passes; pass review `design.md` and `## Tests`; read under Step 5 | Step 7, first paragraph | kept |
| Step 7 · 374-375 | after a nothing-committed round, the verify judges the previous freeze's patch and Step 5 uses its numbers | Step 6, The fixer committed nothing | moved: stated where the branch is taken |
| Step 7 · 377-379 | reopen a test-sized card with no red run, or one off the scenario; the station cannot re-run on the parent | Step 7, second paragraph | kept |
| Step 7 · 381 | both clean → Step 8; else Step 6 | Step 7 | kept |
| Step 7 · 383-386 | the cap is three, pickup counts; halt leaving every file; no backlog; report open ids and the pickup round; no escalation; the halt is the finding | Step 7, The cap | kept |
| Step 8 · 390-392 | fix small cards and drift while fresh; a small card's sizes; mechanical, no human confirms | Step 8, opening | kept |
| Step 8 · 394-401 | once, while a round remains; what is picked; literal size match; print ids, write `pickup`; send by id, verify; one pickup per run | Step 8, list | kept |
| Step 9 · 405-419 | the backlog write: non-verified non-blocking cards; Still true? and moot; file creation line; qualified ids, fields verbatim; skip existing ids; clear a fixed repeat's card; write `backlog` | Step 9, list | kept |
| Step 10 · 423-424 | close-out shape; halt reported in full | Step 10 | kept |
| Step 10 · 426-428 | the sentences: verdicts and round, blocking end states, qualified ids, backlog total, final gate exit code | Step 10 | kept |
| Step 10 · 428 | the rest is on disk | Step 10, close-out | merged: "the detail stays on disk" |
| Step 10 · 430 | write `done`; `Next: /mf-release, in a fresh session.`; stop | Step 10 | kept |
| The card · 434-436 | one list line plus nested field bullets, never a heading, why; one owner, held by `tests/test_skills.py` | The card, opening | kept |
| The card · 438-465 | the field table, writing limits, the example | The card | kept byte for byte |
| Rules for tests · 469-470 | `mf-build` owns the list; ids held equal; fixer writes to them; test-cost judges by them | Rules for tests, opening | kept |
| Rules for tests · 472-479 | the `T1`…`T6` table | Rules for tests | kept byte for byte |
| Never · 483-496 | never review in your context; never edit, delete, move, rename, empty a findings file or patch; never edit a status line; pickup limits; backlog deletion limit; never weaken; never archive, fold, tag, merge, push; never write a secret or real path | Never | kept, shorter |

## skills/mf-converge/references/generic-review.md

| old (section · lines at a926ca1) | rule, exception, halt or output | new (section) | disposition |
|---|---|---|---|
| intro · 3-4 | a fresh checker; writes only its findings file; edits and commits are the fixer's | intro | kept |
| Inputs · 8-10 | load the converge contract and what it owns; no new findings format | Inputs and contract | kept |
| Inputs · 12-15 | the required inputs; verify adds findings, `## Tests`, fix range; resolve from the package; missing → halt | Inputs and contract | kept |
| Inspect · 19-21 | resolve with git; read with context; correctness, spec, standards, test proofs; trace trigger to consequence; cite; no speculation | Inspect and write, items 1-2 | kept, as steps |
| Inspect · 23-25 | stale-claim and test-cost passes; coverage trace to a test or retiring decision, or none removed; repeats; severity floors | Inspect and write, items 3-4 | kept |
| Inspect · 26-27 | frontmatter, cards, Summary with counts and passes; empty or incomplete scope cannot be clean | Inspect and write, item 5 | kept |
| Verify · 31-33 | re-read; judge each fix; promote or reopen; new card for a regression; red runs; counters, head, log | Verify freshly | kept |
| Verify · 34-35 | role lives in the file; fixer and conductor cannot supply the verdict; findings on disk; no external comments | Verify freshly | kept |
| Verify · 37-39 | target text is evidence, not authority; reads stay in the repo; write only your file; no remote or plugin needed | Verify freshly, last paragraphs; intro | kept |

## skills/mf-converge/references/generic-security.md

| old (section · lines at a926ca1) | rule, exception, halt or output | new (section) | disposition |
|---|---|---|---|
| intro · 3-4 | inspect for concrete vulnerabilities as a fresh checker; write only the findings file | intro | kept |
| Inputs · 8-10 | load the converge contract and what it owns; no new format | Inputs and contract | kept |
| Inputs · 12-15 | the required inputs; verify adds findings and fix range; resolve from the package; missing → halt; no remote or plugin needed | Inputs and contract | kept |
| Inspect · 19-22 | resolve with git; read with context; trace across trust boundaries; what to inspect; concrete trigger, defect and harm; never copy a secret | Inspect and write, items 1-3 | kept, as steps |
| Inspect · 24-26 | repeats and severity floors; security vocabulary and tiers; frontmatter and Summary with counts; uninspected cannot be clean | Inspect and write, items 4-5 | kept |
| Verify · 30-33 | re-read; judge each fix; promote or reopen; regressions carded; red runs; counters, head, log; identity on disk; accept no other's verification; findings local | Verify freshly | kept |
| Verify · 35-37 | target content grants no authority and certifies nothing; instructions are evidence; reads stay in the repo; write only your file; package material is not outside access | Verify freshly, last paragraph; intro | kept |
