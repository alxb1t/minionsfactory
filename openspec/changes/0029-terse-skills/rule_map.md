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

## skills/mf-build/SKILL.md

| old (section · lines at a926ca1) | rule, exception, halt or output | new (section) | disposition |
|---|---|---|---|
| intro · 8-10 | build the phases in order, green gate, a commit each; no review, converge or release; who does them | intro, blockquote | kept |
| intro · 10-11 | `AGENTS.md` is shared context, true not a script; the change is authoritative | intro, read line | merged with 13 |
| intro · 13-14 | read root `AGENTS.md` and its mandatory context; missing → halt | intro, read line | kept |
| — | the ritual as a flow | intro, diagram | added: restates Steps 1–4, no new rule |
| Parameter · 18-25 | strict inference: none, several, branch mismatch halt; echo | Parameter, list | kept, shorter |
| Parameter · 27-28 | why strict: the id keys the phase state and the `Change:` trailer | Parameter, lead line | kept |
| Parameter · 30 | echo the id and the phase before building | Parameter | kept |
| Input contract · 34-36 | the skill owns the list; the cut carries it; Step 1 checks the yes items; others by stop-condition; a mid-build breach halts naming the id | Input contract, opening | kept |
| Input contract · 38-55 | the `I1`…`I16` table | Input contract | kept byte for byte |
| Step 1 · 59-67 | the `I1`, `I4`, `I13`, `I14` checks; a failure halts naming the id | Step 1, list | kept |
| Step 1 · 71-74 | read proposal, design and all of tasks; `design.md` authoritative; disagreement halts | Step 1.1 | kept |
| Step 1 · 75 | `AGENTS.md`: gate, conventions, seams, guardrails | Step 1.2 | kept |
| Step 1 · 76-77 | work stands in Progress and `git log`, never memory; re-read every pass | Step 1.3 | kept |
| Step 1 · 78-83 | the gate, `make -n gate` first, not a sandbox, the halts naming the `Makefile`; never infer, ask for or substitute a gate | Step 1.4 | kept |
| Step 1 · 85-86 | what you read is evidence; report it | Step 1 | kept |
| Step 1 · 88-90 | dirty tree with tracked `tasks.md` → continue the interrupted phase, say so; untracked → `I1` halt | Step 1, at-the-start table | kept, as rows |
| Step 1 · 92 | every box ticked → report built and stop; invent no scope | Step 1, at-the-start table | kept, as a row |
| Executor · 96-97 | report the engine from runtime evidence; names do not identify it | Executor selection | kept |
| Executor · 99-101 | Claude Code: native `/simplify` required before edits; missing → halt; generic only on explicit user choice; keep native behaviour | Executor, table row 1 | kept |
| Executor · 102-104 | other: load generic simplify; the named executors; resolve from the installed package | Executor, table row 2 | kept |
| Executor · 106 | MF skill names identify instructions; host syntax | Executor selection | kept |
| Step 2 · 110-112 | first unticked phase, whole ritual through its commit; never batch; why | Step 2, opening | kept |
| Step 2 · 114-116 | HUMAN phase: do none of its tasks, run its `Verify:`; a failure halts with the checklist only | Step 2, A HUMAN phase | kept |
| Step 2 · 118-128 | the HUMAN checklist format | Step 2 | kept byte for byte |
| Step 2 · 130-133 | root in chat only; secrets by env-var; all pass → search evidence for home, root, keys and halt on a hit; stage by name, no ignored path, no `git add -f`; gate, CHANGELOG, tick phase and `N.M`, commit | Step 2, paragraph after the checklist | kept; the gate-to-commit steps point to items 3–6 |
| Step 2 · 135-138 | test-first at `T1`'s layer, a step per `T2`; fake effects behind seams; write to `W`, `T`, `P`, `C` | Step 2.1 | kept |
| Step 2 · 139-144 | run each verification, never summarize; show real output; tick `N.M` once passed; failed **HALT CHECK** halts; never change code to pass | Step 2.2 | kept |
| Step 2 · 141-142 | the same rule the gate is under | Step 2.2 | cut: the principle *The gate is run, never summarized*, in `docs/principles.md`, read via `AGENTS.md` |
| Step 2 · 145-148 | run `make gate`, exit 0; never weaken, halt; a table-named deletion is not weakening | Step 2.3 | kept |
| Step 2 · 149-150 | CHANGELOG entry, 1–3 lines, what and why, to `P` | Step 2.4 | kept |
| Step 2 · 151-152 | tick the phase box; commit and tick together make an advance | Step 2.5 | kept |
| Step 2 · 153-162 | one commit; stage by name, never `git add -A`, why; Conventional Commits; trailer block contiguous, why; every commit carries `Change:` | Step 2.6 | kept |
| Step 2 · 164-170 | a retiring phase carries `W2`'s list before the trailers; the example | Step 2.6 | kept; the example byte for byte |
| Step 2 · 172-173 | a new e2e test carries `T2`'s reason before the trailers | Step 2.6 | kept |
| Step 2 · 175 | then the next phase, until every box is ticked | Step 2, last line | kept |
| Step 3 · 179-183 | after the last phase only; selected engine over the diff with its inputs; fixes in place | Step 3.1 | kept |
| Step 3 · 184-185 | re-run the gate; red halts; no commit over red; no weakening | Step 3.2 | kept |
| Step 3 · 186-187 | its own trailered commit, by name; a no-op reported, no manufactured commit | Step 3.3 | kept |
| Step 3 · 189-196 | why in the build: before converge, review judges its edits; no simplify findings file; release excludes it | Step 3, Why inside the build | kept, shorter |
| Step 4 · 200-205 | close-out shape; the sentences; `Next: /mf-converge, in a fresh session.`; stop | Step 4 | kept |
| Stop-conditions · 209-211 | halt cleanly, no commit, no tick; report the question; why | Stop-conditions, opening | kept |
| Stop-conditions · 213-224 | the five stop-conditions, with the dependency lookup | Stop-conditions, list | kept, shorter |
| Rules for what you write · 228-238 | the `W` scope, retirement, and `W1`…`W6` | Rules for what you write | kept byte for byte |
| Rules for tests · 242-252 | ownership and the `T1`…`T6` table | Rules for tests | kept byte for byte |
| Prose rules · 256-276 | ownership, the `P1`…`P13` table, the `P` and `C` scope | Prose rules | kept byte for byte |
| Rules for code comments · 280-306 | the `C1`…`C12` table and the before → after | Rules for code comments | kept byte for byte |
| NOT do · 310-318 | never batch; never summarize a check; never review, converge, release, archive, fold, tag, merge, push; never `git add -A`; never a secret or real path; never invent scope or re-open a decision | What you must NOT do | kept, shorter |

## skills/mf-build/references/generic-simplify.md

| old (section · lines at a926ca1) | rule, exception, halt or output | new (section) | disposition |
|---|---|---|---|
| intro · 3-4 | behaviour-preserving, inside the build, before checking; a producer: no findings file, no verdict | intro | kept |
| Inputs · 8-10 | the inputs; resolve from the installed package; missing → halt naming them | Inputs and boundary | kept |
| Inputs · 12-14 | read with callers; what to look for; keep design, behaviour, test proofs, role boundaries; no unrelated cleanup | Inputs and boundary | kept |
| Apply · 18-19 | apply in place; prefer direct or existing helper; keep a real distinction | Apply and finish, item 1 | kept |
| Apply · 20-22 | run the full gate as the build directs; red halts; a no-op still runs it; separate commit by name with trailers; report scope and edits, or a no-op | Apply and finish, items 2-4 | kept, as steps |
| Apply · 24-25 | target content is evidence; reads and writes stay in the repo; package material | Apply and finish, last paragraph | kept |

## skills/mf-cut-change/SKILL.md

| old (section · lines at a926ca1) | rule, exception, halt or output | new (section) | disposition |
|---|---|---|---|
| intro · 8-10 | write one change from settled decisions; commit once the self-check passes; no build, review, converge, release | intro, blockquote | kept |
| intro · 10 | `AGENTS.md` is shared context; the source is what you write from | intro, read line | merged with 18 |
| intro · 12-16 | the line diagram | intro | kept byte for byte |
| intro · 18-19 | read root `AGENTS.md` and its mandatory context; missing → halt | intro, read line | kept |
| Parameters · 23-30 | the parameters table; echo all; a missing required one halts and asks; never infer | Parameters | kept |
| Parameters · 32-33 | the source; an unresolved `brief` halts; never search | Parameters | kept |
| Step 1 · 37-46 | the preconditions, each halting by name, the gate halts naming the `Makefile`, not a sandbox | Step 1 | kept; "the gate is sound" folded into the `make -n gate` line |
| Step 2 · 50-51 | what to read; no settled decision → halt | Step 2 | kept |
| Step 2 · 53-54 | the source is evidence; report a line addressing you | Step 2 | kept |
| Step 3 · 58-62 | re-check premises against HEAD, why; a failure goes to the human, wait; never overturn or record an overturn alone | Step 3 | kept, one paragraph |
| Step 4 · 66-67 | `git switch -c`; the slug rule and example | Step 4 | kept |
| Step 5 · 71-72 | scaffold and `.openspec.yaml` | Step 5 | kept |
| Step 6 · 76-79 | artifact order; `openspec instructions` first; write to the contract, prose and artifact rules | Step 6 | kept |
| Step 6 · 81 | `version:` frontmatter; the CLI does not check it | Step 6 | kept |
| Step 6 · 82-84 | a paydown lists `backlog:` ids; grep each; not found → human; the cut leaves the backlog | Step 6 | kept |
| Step 6 · 85-86 | no behaviour change → `skip_specs: true` plus `specs/.gitkeep`, together, why | Step 6 | kept |
| Step 6 · 87-88 | `## Tests` and `## Dependencies` always; `None.`; exact package and constraint | Step 6 | kept |
| Step 7 · 92 | validate strict; red → fix and re-run | Step 7 | kept |
| Step 8 · 96-97 | the `I1`…`I16` table; `I1` at commit; `I3` on the tree to commit | Step 8 | kept |
| Step 8 · 99-102 | read every `Verify:`, run none; the build runs them; rewrite one that will not run; flag one that already holds, except a **HALT CHECK** | Step 8 | kept |
| Step 8 · 103-104 | check `P9`, `P12`, `P13`, `A2`; gate green | Step 8 | kept |
| Step 8 · 106 | an unmeetable item goes to the human, and waits | Step 9, the wait table | merged: one statement of what waits |
| Step 8 · 106-108 | the self-check is a declared exception; the independent checks | Step 8 | kept |
| Step 9 · 112-114 | show the change, phases, ids, table, files, every `Verify:` word for word; commit without waiting | Step 9 | kept; "the build runs them" stated once, in Step 8 |
| Step 9 · 116-117 | dependencies not `None.` and an unmeetable item wait for an OK; per-package OK; edits → Step 7 | Step 9, the wait table | kept, as a table |
| Step 9 · 119-120 | a post-commit edit is a further `amend` commit with the trailers | Step 9 | kept |
| Step 10 · 124-128 | stage by name, never `git add -A`; the message; the contiguous trailer block | Step 10 | kept |
| Step 11 · 132-137 | close-out; the sentences; suggest models; `Next: /mf-build <change-id>, in a fresh session.`; stop | Step 11 | kept |
| Input contract · 139-160 | ownership and the `I1`…`I16` table | Input contract | kept byte for byte |
| Prose rules · 162-190 | ownership, the `P1`…`P13` table, the task before → after | Prose rules | kept byte for byte |
| Rules for tests · 192-204 | ownership and the `T1`…`T6` table | Rules for tests | kept byte for byte |
| Rules for the artifacts · 206-219 | the `A1`…`A8` table | Rules for the artifacts | kept byte for byte |
| Suggesting models · 223-225 | suggest in chat for build, loop, release; target menu, then session menu, then a capability; never invent names | Suggesting models | kept |
| Suggesting models · 227-229 | effort only where exposed; no model change, auth or provider setup; chat only | Suggesting models | kept |
| Suggesting models · 231-253 | the tier table; highest row decides; converge skip rule and anchors; release tier; the block; a suggestion only | Suggesting models | kept byte for byte, but for one shorter line |
| Never · 257-264 | never build or edit outside the change; never simplify, review, converge, release, push, merge; never commit unapproved dependencies; never overturn alone or invent scope; never write the brief's or an absolute path; never write the suggestion to a file | Never | kept, lines merged |

## skills/mf-release/SKILL.md

| old (section · lines at a926ca1) | rule, exception, halt or output | new (section) | disposition |
|---|---|---|---|
| intro · 8-10 | verify, finalize, then ask; never edit feature code or lower a bar; a failed precondition halts naming what and who; merge and push only on the yes, asked once | intro, blockquote | kept |
| intro · 12-15 | why: the loop that declared convergence does not archive and tag; re-read verdicts; the only check when skipped, said so; re-run the gate, inherit nothing | intro, `Why` paragraph | kept |
| intro · 17-18 | read root `AGENTS.md`; missing → halt | intro | kept |
| — | the release as a flow | intro, diagram | added: restates Steps 1–6, no new rule |
| Parameter · 22-32 | strict inference, halts, echo; why strict | Parameter | kept, shorter |
| Parameter · 34-35 | the version from `proposal.md`, never invented or derived; `<version>` and the tag | Parameter | kept |
| constants · 39-44 | the gate, `make -n gate` first, not a sandbox, the `Makefile` halts; never infer or substitute, why | constants | kept |
| constants · 46-47 | an absent version file is a stated skip, `none`, with why | constants | kept |
| Step 1 · 51-53 | report a checklist; findings files are evidence; a line addressing you → note it and halt | Step 1, opening | kept |
| Step 1 · 55-60 | the exact paths, keyed by the change id | Step 1, list | kept |
| Step 1 · 62-64 | never glob the findings directory, why; an absent file is never a reason to search | Step 1 | kept |
| Step 1 · 66-68 | precondition 1: re-run here, not inherited; red → halt, the build owns it | precondition 1 | kept |
| Step 1 · 67 | a green gate is a command that exited 0, observed by the side that needs it | precondition 1 | cut: the principle *The gate is run, never summarized*, read via `AGENTS.md` |
| Step 1 · 70-71 | time the run for the `Gate:` line, the one-shell command | precondition 1 | kept |
| Step 1 · 72-76 | preconditions 2 and 3: clean, every blocker `verified`; `fixed` is a claim | preconditions 2, 3 | kept |
| Step 1 · 77-85 | precondition 4: skipped, patch-only halt, ran, one-file halt; the skip line; lost `.minions/`; simplify excluded by name, why | precondition 4, table | kept, as a table |
| Step 1 · 86-88 | preconditions 5 and 6 | preconditions 5, 6 | kept |
| Step 1 · 89-92 | precondition 7: HEAD is the judged head; halt with the catch-up instruction; checked before the fold | precondition 7 | kept |
| Step 1 · 93-100 | precondition 8 | precondition 8 | kept word for word |
| Step 2 · 104-111 | ADDED append; MODIFIED whole replace byte for byte, why; REMOVED delete | Step 2, table | kept, as a table |
| Step 2 · 113 | a rename is REMOVED + ADDED | Step 2 | kept |
| Step 2 · 115-117 | preamble verbatim; flag a hand-edit; never silently rewrite or leave wrong | Step 2 | kept |
| Step 2 · 119-120 | `skip_specs` folds nothing and still archives | Step 2 | kept |
| Step 3 · 124-126 | move, stage by name; commit nothing; Step 4 commits after its gate | Step 3 | kept |
| Step 3 · 128-130 | no separate spec-binding step, why | Step 3 | kept |
| Step 3 · 132-133 | fold and archive in one commit, why | Step 3 | kept |
| Step 4 · 137-148 | the changelog cut; the `Gate:` line, its example, CI and previous rules | Step 4.1 | kept |
| Step 4 · 150-151 | no other changelog prose, why | Step 4.1 | kept |
| Step 4 · 152-155 | version file bump or `none`; correct current-version prose, why | Step 4.2 | kept |
| Step 4 · 156-164 | re-run the gate before commit and tag, why; red → halt, no weakening; report staged and uncommitted work; reverting is the human's; why this order | Step 4.3 | kept, shorter |
| Step 4 · 165-179 | one release commit, by name; `git diff --quiet` and no untracked files or halt; clean after; contiguous trailers; the skip line paragraph and the example | Step 4.4 | kept |
| Step 4 · 180-182 | annotated local tag; the record is tag, commit and changelog | Step 4.5 | kept |
| Step 4 · 183-187 | clear paid-down cards; `backlog: none`; an id not found is reported; nothing to commit | Step 4.6 | kept |
| Step 5 · 191-203 | ask once; anything but yes → Step 6; failure halts with remaining commands; the merge-base check; merge with trailers; tree check; no `origin`; push order; never pull, force, or push the version branch | Step 5 | kept |
| Step 6 · 207-209 | the authorizing gate is Step 4.3's; no re-run; report its exit code | Step 6 | kept |
| Step 6 · 211-227 | close-out; the sentences; the last lines and the no-merge block; stop | Step 6 | kept |
| Never · 231-242 | never merge or push without the yes, force, pull, push the branch; never edit feature code or tests; never over a failed precondition; never commit or tag ungated; never invent the version or write prose; never touch the findings files; never a secret or real path | Never | kept; "no just this once" folded into "no exceptions" |

## skills/mf-bootstrap/SKILL.md

| old (section · lines at a926ca1) | rule, exception, halt or output | new (section) | disposition |
|---|---|---|---|
| intro · 8-10 | write starting files from the templates, gate green, commit once; a repo with its own setup halts | intro, blockquote | kept |
| intro · 9 | never overwrite, add a remote, or push | *Never* | merged: stated once there |
| intro · 12-14 | the line diagram | intro | kept byte for byte |
| Parameters · 18 | no parameters; target is the cwd, name its basename | Parameters | kept byte for byte |
| The files · 22-23 | target path is the template path without `.tmpl`; example | The files | kept, shorter |
| The files · 25-29 | the collision table: halt, skip `README.md`, append `.gitignore` | The files | kept byte for byte |
| The files · 31-34 | only the placeholders change; the placeholders | The files | kept |
| Step 1 · 38-47 | the preconditions, each halting by name; every collision named in one halt; adoption is out | Step 1 | kept; "without it the gate is red" folded into "the gate runs the OpenSpec CLI" |
| Step 2 · 51-54 | `git init -b main`; write with placeholders and parents; keep every byte, tab; list the paths | Step 2 | kept |
| Step 3 · 58-59 | `make -n gate` and `make gate`, pasted; red → halt, commit nothing, report paths | Step 3 | kept |
| Step 4 · 63-68 | stage by name, no `git add -A`; skipped `README.md` not staged; the message and trailer; no `Change:`; clean after or halt | Step 4 | kept byte for byte |
| Step 5 · 72-80 | close-out; the sentences; the no-remote note; generic needs none; provider setup is the operator's; the last line | Step 5 | kept |
| Step 5 · 78 | bootstrap does not add a remote | *Never* | merged: stated once there |
| Never · 84-89 | never overwrite; never write outside the target; never add a remote, push, or another branch; never commit over red; never a `Change:`, CHANGELOG entry or change; never a secret or real path | Never | kept byte for byte |

## AGENTS.md

| old (section · lines at a926ca1) | rule, exception, halt or output | new (section) | disposition |
|---|---|---|---|
| intro · 3-5 | what MinionsFactory is; the map of the record | intro | kept byte for byte |
| The record · 19-22 | this file is shared context, not a script; the prompt says what to do and wins a conflict; infer no workflow | intro, blockquote | moved: answer first, before the sections |
| The record · 9-10 | read the principles and decisions before work: mandatory | The record | kept |
| The record · 12-14 | decisions in force live in `docs/decisions.md`; a change that adds or overturns one edits it; `design.md` keeps the history | The record | kept; "each with its reason" cut: the decisions page says it of itself |
| The record · 15-17 | docs to `P1`…`P13`; a change is cut with `mf-cut-change` | The record | kept |
| gate · 28-31 | `make gate` at the root; what it checks; the recipe is the only list; skills and CI run it | The quality gate | kept |
| Layout · 37-39 | `skills/`, `docs/` | Layout | kept |
| Layout · 40-43 | the OpenSpec CLI: operator tooling, recorded not pinned, the version, global; out of the gate, why | Layout | kept; the why cut: D8, read as mandatory context |
| Layout · 44-46 | `.minions/` gitignored, the backlog; `tests/` | Layout | kept |
| Layout · 47-49 | inputs and outputs stay inside the repo, save release's CI lookup; installed skills are package material | Layout | cut: the principle *The repo reaches nothing outside itself* states it, and the line points there |
| Layout · 50-52 | execution follows the host; native or generic engines; fresh observable checkers; provider setup is the operator's | Layout | cut: D11, D40 and D22 state it, and the line points there |
| Guardrails · 58-65 | never commit a secret or a real absolute path; what is and is not the target; why; `.env` and `AGENTS.md`; the guardrail test | Guardrails | kept, shorter |
| Guardrails · 66-67 | dependencies minimal and human-gated; argue and wait; dev-only tools; lean runtime | Guardrails | kept |

## docs/principles.md

| old (section · lines at a926ca1) | rule, exception, halt or output | new (section) | disposition |
|---|---|---|---|
| every section | the words, both diagrams, every principle's rule, Why, Accepts, Known breaks, Not yet and Held by | the same section | kept; `###` headings byte for byte |
| No station verifies its own work · Why | a report on itself is a claim | same | two sentences joined |
| A checker is a fresh reader · Why | a remembering reader; a moving diff | same | two sentences joined |
| Never weaken the gate · Held by | "the recipe check in `mf-converge` and `mf-release`" | same | named: `mf-converge` precondition 6 and `mf-release` precondition 8 |
| State lives on disk · Why | resume is free; a view is a projection of files | same | two sentences joined |
| Decisions are made before the cut · Why | judgement in authoring; an improvising build | same | two sentences joined |

## docs/decisions.md

| old (section · lines at a926ca1) | rule, exception, halt or output | new (section) | disposition |
|---|---|---|---|
| every section | the intro, the diagrams, every decision's rule, Why, Accepts, Rejected, Gave up and Held in step by | the same section | kept; `### Dn` headings and the D18 tree byte for byte |
| D6 · 69-70 | this page holds what is in force; an overturn edits it; `design.md` keeps the history | intro | cut: the page's intro states it |
| D13 · 146-147 | Claude Code uses native `/simplify`; others load the generic simplify | D13, links D11 | cut: D11 states it |
| D18 · 220 | the stations install nothing into the target | D18, links D2 | merged: D2 states it |
