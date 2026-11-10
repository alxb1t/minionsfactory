# Converge script — design

`skills/mf-converge/scripts/converge.py` conducts converge; `conduct.py` loads it in-process and calls it in a version's thread.
Verdict: build the fields first, the script in three phases, then the wiring and the record. Each phase ends green.

Read [proposal](proposal.md) for why, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the requirements.

## Context

Facts at `ccfa6a1`, the brief's sha: `git diff --name-only ccfa6a1..HEAD --no-renames` prints nothing, so every fact that cites
a path stands. Lines are `ccfa6a1`'s, from the cut's notes. `C` is `skills/mf-ship/scripts/conduct.py`, `K`
`skills/mf-converge/SKILL.md`, `W` `skills/mf-converge/references/worker.md`, `T` `tests/test_conduct.py`.

| id | fact | where |
|---|---|---|
| F1 | the conductor costs $2.91 of 0105's $12.04 converge (24%) and $2.34 of 0104's $14.13 (17%), on Opus high | the efficiency ledger, outside the repository |
| F2 | `C` starts converge as one LLM station: `Run the mf-converge skill for change …`; its prompt and mailbox are built in `Run.advance`, then `self.spawn` | `C:257-259`, `C:5213-5266` |
| F3 | `C` judges converge from disk: `stage_of`, `_check_converge`, and byte-for-byte matches of `cap reached`, `amend needed —`, `verify: halt` and ` · head <sha>` | `C:1421-1494`, `C:1531`, `C:120`, `C:1484`, `C:2747`, `C:1132` |
| F4 | `K` holds many rules and halt sites; these places judge: Step 5's scope and Summary checks, the amend card's drift exception, **Still true?**, `plan check left:` read from free text, each worker's prompt composed free, Step 10's `inconclusive` sections | `K:355-362`, `W:166-170`, `K:502-529`, `K:389`, `K:334-338`, `K:531-542` |
| F5 | the converge scripts stand, each `main(argv=None) -> int`; not scripted: the loop and resume, the verdict read, the pickup pick, amend detection, the debt write, By rule's frontmatter edit, catch-up enumeration, the report | `skills/mf-converge/scripts/` |
| F6 | the spawner is reusable: module-level `argv`, `work`, `_free_log`, `tokens_of`; `Run.worker(who, station, cwd, prompt, models, …) -> (exit, killed, log, denials)` names its log `<stamp>-<station>` | `C:3390-3594`, `C:4680-4749`, `C:4717` |
| F7 | `Run.checker(change, role, cwd, prompt, deadline, request) -> str` runs one checker, holds the Codex fallback and returns a mailbox answer; the mailbox — request and answer files, `serve_requests`, `checker()`, its subparser, `_mailbox`, `_open_mailbox`, `Run.server`, the constants `CHECKERS`, `MAILBOX_POLL`, `CHECKER_WAIT`, `REQUEST_BYTES`, `REQUEST_ID`, `CHECKER_SPAWNS` — exists for a sandboxed LLM conductor; [D8](#d8) removes it | `C:4613-4661`, `C:2989-3160`, `C:6812`, `C:7446`, `C:7717-7720`, `C:73-80` |
| F8 | `C` runs outside any sandbox; the gate, `gate_check.py` and `plan_check.py` run inside the LLM conductor's. [0107-sandbox-runner](../0107-sandbox-runner/design.md) adds `sandboxed(argv, cwd, trees) -> int`, which tees to `sys.stdout` and takes no file | `K:290`, `K:431-433`, the design of 0107 |
| F9 | `Run.__init__` loads `integrate.py` by `runpy.run_path(str(INTEGRATE))`; `INTEGRATE` is a module constant | `C:86`, `C:4305` |
| F10 | `_clear` kills a claim group only when its leader is an executor name, else raises `Stop(2)` | `C:4154` |
| F11 | `CONDUCTOR`, which [D8](#d8) renames, has one reader, `_models`; the converge row of `STATION_TOOLS` is read by `tools_for` alone; `CACHE_HOUR` by `argv` alone | `C:153`, `C:2577`, `C:202`, `C:3306`, `C:207`, `C:3435` |
| F12 | the fixer runs on adversarial's model when a card is blocking and adversarial is no mailbox role; no test asserts it | `K:374-377`, `openspec/specs/sdd/spec.md:3743-3749` |
| F13 | H5 is `surfaces.py`, the adversarial head by rule: never fired, 0 of 25 | `K:439-452`, `openspec/specs/sdd/spec.md:3925-3951` |
| F14 | `stage_of` and `_unjudged` read a converge skip from `models.toml` at every poll, while the checker skips and the `decide` switch are read once into `Run.skipped` | `C:1250`, `C:1476`, `C:4342`, `C:5867-5873` |
| F15 | `tests/fake_worker.py` plays a whole converge from one prompt, by modes; `T` drives it in many tests | `tests/fake_worker.py:712-847`, `T:687`, `T:5525`, `T:8308-9105` |
| F16 | `review_metrics.py` books a converge worker by its Agent description, `WORKER`; `converge-reading-set` counts AGENTS.md, `K` and `W` | `skills/mf-review-metrics/scripts/review_metrics.py:96`, `metrics/catalogue.toml:5-15` |
| F17 | the highest decision is D76, and D77 is 0106-cut-scripts' own; this change's decision is D78 | `docs/decisions.md:821`, the design of 0106 |
| F18 | `stamp.py`, `bundle.py`, `debt_match.py`, `open_cards.py`, `skip_stub.py`, `overlap.py`, `gate_run.py`, `gate_check.py`, `plan_check.py` each have `main(argv)`; `tests/test_skills.py` requires each script a skill names to exist | `skills/mf-converge/scripts/`, `tests/test_skills.py:507-531` |

## Goals / Non-Goals

**Goals:** the brief's acceptance — `make gate` exits 0; with the fake hosts a version converges through `conduct.py` with no
converge LLM spawn, one log per worker; a malformed findings file gets one rewrite worker, then a debt card; a worker's exit 1
gets one retry; the fixer runs on `fix=`'s model with a blocking card open; `surfaces.py` is deleted; `serve_requests` is removed;
D78 stands. Also the debt of [D11](#d11).

**Non-Goals:** tool evidence before the checkers; Linux; a change to what a checker judges or how it grades; H15 and H16 of the
efficiency ledger, which the person records outside the repository.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `converge.py` holds the whole conductor; `conduct.py` loads it by `runpy` and calls `converge(host, change, tree, …)` in the version's thread; `conduct.py converge` runs it by hand | Q1 | a runner inside `conduct.py`, already the largest module · a python claim leader (F10) |
| [D2](#d2) | the six judgments become fields: `files`, `commits`, `passes`, `inconclusive`, `Amend:`, `fix.md`'s `plan check left:`, and a `## Prompt` per reference | Q4 | a script reading prose |
| [D3](#d3) | each Step of `K` is one function, and `K` as it stands at the build's start is the behaviour save where [D3](#d3)'s table changes it | Q1, Q14 | a rewrite of the rules |
| [D4](#d4) | workers are fresh processes through `Run.worker` and `Run.checker`, one log each, named `<stamp>-converge-<role>-r<N>.log`; the fixer always on `fix=` | Q1, Q6, Q8, Q10 | an Agent subagent · the fixer by grade |
| [D5](#d5) | no halt a script can go on from: one retry, one rewrite, one more fix pass, an empty `debt-cards.md`, a 10-minute lock wait | Q5 | halting at each |
| [D6](#d6) | the gate, `gate_check.py`, `plan_check.py` and each **Still true?** command run under `sandboxed()` | Q2, Q12, Q13 | running them bare |
| [D7](#d7) | the debt write: a prose **Still true?** goes to the debt unchecked; a command that exits 1 is moot | Q4 | a worker reading the check |
| [D8](#d8) | `conduct.py` changes: the in-process call, the mailbox retired, `Run.checker` returns a result, the converge rows gone, a skip read once, H5 deleted, `conduct.py converge` | Q1, Q6, Q7, Q8 | keeping the mailbox for a hand converge |
| [D9](#d9) | the record: D78, and D3, D40, D47, D51, D53, D64, D68, D70, D71 and D76 amended where they live | Q17 | a new decision per amendment |
| [D10](#d10) | the prose and the metrics: a thin `K`, the reading set, review metrics by log name, the skill test's rows | Q10, Q15 | keeping `K` whole |
| [D11](#d11) | the debt: the frontmatter's cards closed, the mailbox's cleared as moot | Q9 | leaving them |

### C rows

| id | decision | reason |
|---|---|---|
| C1 | the new decision is D78, not the brief's unnumbered one: D77 is 0106-cut-scripts' | F17; an id in force is never reused |
| C2 | `0105·R7` is closed in the delta's *A converge conductor stubs a skipped checker*, which this change modifies anyway; no task edits a spec | the delta is the spec's change; the release folds it |
| C3 | the spec's *Converge keeps a status log* and the rest of the delta keep the word "conductor" for the script | the script conducts; only the LLM conductor goes |
| C5 | the conduct-level converge tests run `converge.py` under a fake `sandbox-exec` on `PATH` that runs its command unconfined, the fixture moved from `tests/test_sandboxed.py` to `tests/conftest.py`, and each fake repo holds a `gate` recipe that succeeds | a nested Seatbelt cannot apply a profile ([0107](../0107-sandbox-runner/design.md), F8), and the gate is the repository's own; brief decision C1 |
| C6 | `converge()` meets exceptions as [D1](#d1) says: only `host.sandboxed`'s code 2 is "cannot run"; a worker's failure is a `halt` event and exit 1; a thread's exception propagates | brief decision C2 |
| C7 | `replay` failing, which `K` halts on, is a worker round, as the brief's Q5 says | brief decision C3 |
| C4 | the phrases "mailbox" in the living *The review-metrics station charts past findings, read-only* and *A halt stops only its version, and a re-run resumes* stay: they name older logs and a retired path that the release's fold cannot reword without copying two long requirements | the delta's *A converge worker is booked by its log name* carries the new rule |
| C8 | `plan_check.py` skips a line of `openspec/specs/<capability>/spec.md` that stands in a requirement the change's `specs/<capability>/spec.md` lists under `## REMOVED Requirements`, from its `### Requirement:` heading to the next `### Requirement:` or `## ` heading; the delta's *A plan check holds the plan to the built tree* says so | the delta removes *A converge checker on another host runs through the mailbox*, whose living text names `CHECKER_WAIT` and `REQUEST_BYTES`, and the release folds a removal only after the build's close: without the skip, every change that removes a requirement naming the code it deletes halts its close (the build's close halt, answered by the supervisor) |

### D1

**Where it lives.** `skills/mf-converge/scripts/converge.py`, a `uv` script with `dependencies = []`, loaded by `Run.__init__` beside
`INTEGRATE` ([F9](#context)): `CONVERGE = Path(__file__).resolve().parents[2] / "mf-converge/scripts/converge.py"`, and
`self.converge = runpy.run_path(str(CONVERGE))["converge"]`.

```
converge(host, change, tree, *, workers, grant=False, deadline) -> int     0 done · 1 halted · 2 cannot run
host.primary       the primary checkout            host.trees()   reach(primary), the sandbox's trees      a new Run method
host.plan[change, "converge.<role>"]   (executor, model, effort), read once with the run's plan
host.worker(who, station, cwd, prompt, models, timeout=…)   Run.worker's           (F6)
host.checker(change, station, table, cwd, prompt, deadline, effort=None) -> Checked   Run.checker's, D8
host.sandboxed(argv, cwd, trees, out=None) -> int    a new Run method calling conduct.py's module function, from 0107, D6
workers            {"conformance": (executor, model, effort) | "skip", "adversarial": …, "fix": …} the hand command's or the plan's
```

- A halt writes its `halt` event to the status log, ending ` · head <sha>`, and returns 1; `conduct.py` then judges the version
  from disk as it does now, through `check` and `judge` ([F3](#context)). Nothing in `stage_of` or `_check_converge` changes
  but [D8](#d8)'s skip read.
- The script writes the status log through `stamp.py`'s own `main`, loaded by `runpy`: its text is byte for byte as before.
- `host` is a plain object: the tests pass a fake, and `Run` is the real one, given the two methods `trees` and `sandboxed` that
  call `reach(self.primary)` and the module-level `sandboxed`.
- `converge.py` cannot name `conduct.py`'s `Stop`. It catches `Exception` around each `host.sandboxed` call alone, reads the
  exception's `code` attribute, and treats `2` as "cannot run": it prints the message and returns 2. Any other exception, a
  checker thread's included (`future.result()` re-raises), propagates to `Run.advance`, which meets a `Stop` as it meets one now.
  The fake host raises an exception with `code = 2`.
- A worker that fails twice, is killed, or asks for a tool its station lacks is not an exception: `converge` writes the `halt`
  event with `Run.spawn`'s words — `<station> timed out after <s>s; its group was killed`, `<station> asked for a tool its station
  lacks: <names>`, `<station> worker exit <code><limit>` — and returns 1; `Run.advance` then judges the version from disk.
- `replay` is called as a function: `converge.py` loads `integrate.py` by `runpy`, as `conduct.py` does, and calls
  `replay(tree, merge)` with the version's tree; `integrate.py`'s `main` (`integrate.py:810-835`) shows what it returns and raises.
  A line `replay: by rule — <paths>` or `no conflict` is by rule; a merge it does not reproduce goes on as `K` says, to the round;
  an exception, which `K` halts on as exit 2, is a worker round ([C7](#c-rows)). Nothing changes the process's directory.
- By hand, `conduct.py converge <change-id> [conformance=…] [adversarial=…] [fix=…] [grant=yes]` builds `Run(primary, executor)`
  as `agent` builds its worker, fills `host.plan` from the arguments, and calls `converge` in the version's worktree; its exit is
  `converge`'s.

### D2

**The fields.** A script reads fields, not prose ([F4](#context)).

| field | where | set by | read by `converge.py` as |
|---|---|---|---|
| `files: <int>` and `commits: <int>` | a findings file's frontmatter | the checker: the files and commits it resolved | the scope check: zero files outside a catch-up's empty-resolution case, or fewer than this round's freeze, is not clean |
| `passes: [<name>, …]` | conformance's frontmatter | conformance: `stale-claim`, `test-cost`, and `coverage-trace` or `no-removed-test` | not clean when `stale-claim` or `test-cost` is missing, or neither of the last two stands |
| `inconclusive: [<document>, …]` | either file's frontmatter | the checker: each section it judged `inconclusive` | the report's `inconclusive` sentence |
| `Amend: yes \| no` | each card, after **Fix** | the checker: `yes` when its **Fix** names `tasks.md` or `design.md` by path, save a `drift` card naming prose outside `## Decisions`, `## Tests` and `## Dependencies`, and a fix note | amend detection, at the halt and the debt write |
| `fix.md` | `.minions/changes/<change-id>/fix.md` | the fixer: its report, ending `plan check left: <subjects>` or `plan check left: none` | the plan-check halt |
| `## Prompt` | `generic-conformance.md`, `generic-adversarial.md`, `verify.md`, `fix.md` | the cut of this change | the prompt of each worker |

- A **malformed** file lacks a key above, holds a key of the wrong type, or holds a card with no `Amend:` line. A stub
  (`mode: skipped`) is exempt from `files`, `commits`, `passes` and `inconclusive`.
- `## Prompt` holds one fenced block; its placeholders are `{change}`, `{role}`, `{round}`, `{base}`, `{head}`, `{range}`,
  `{findings}`, `{patch}`, `{bundle}`, `{debt_cards}`, `{open}`, `{ids}`, `{models}` and `{mode}`, each replaced by
  `str.replace`; a `{name}` left, or a name the script does not know, is an error the tests catch.
- A new reference, `skills/mf-converge/references/fix.md`, holds the fixer's rules moved from `K`'s Step 6 bullets, and its `## Prompt`.
- `W` is edited where the fields live: the frontmatter block, the card table, the amend-card paragraph. That paragraph also gains
  the closing fix-note exception (card `0103·R3`'s kin, `0103·R2`) and `## Tests` and `## Dependencies` among the sections the
  fixer never edits (`0101·S4`).

### D3

**Each Step of `K` is a function.** `K` as it stands when the build starts is the behaviour; the table lists what changes.

| `K` | function | change |
|---|---|---|
| the run, resume and the status log | `resume`, `open_run` | the resume table, each row, is a test case |
| Step 1 preconditions | `preconditions` | the gate runs through [D6](#d6); `uv` is not a precondition; no `sandbox-exec` exits 2, `no OS sandbox` |
| Step 2 freeze | `freeze` | the bundle and `debt_match.py` run as functions of their scripts; `debt_match.py` exit 2 → an empty `debt-cards.md` |
| Step 3 dispatch | `dispatch` | the prompt filled from the reference's `## Prompt`; checkers in parallel, in threads |
| Step 5 read the verdicts | `read_verdicts` | [D2](#d2)'s fields; one `verdicts` line per role |
| Step 6 fix | `fix` | `fix=`'s model always; the round-1 pickup with the blockers; `fix.md`'s `plan check left:` |
| Step 7 verify and the cap | `verify`, `cap` | the adversarial head by rule is gone; each verify worker through `host.checker` on its role's table |
| Step 8 pickup | `pickup` | the pickup check on adversarial's model when a picked card is adversarial's, else conformance's |
| granted round, catch-up, By rule | `grant`, `catch_up`, `by_rule` | `replay` exit 2 → a worker round |
| Step 9 debt | `debt` | [D7](#d7) |
| Step 10 report | `report` | the close-out text from disk; each `inconclusive` from the field |
| shadow round 1, a skipped checker | `shadow`, `stubs` | shadow through `host.checker`; `skip_stub.py` as a function |

- The old status log's lines are the interface to `conduct.py` ([F3](#context)); the events table of `K` is the list.
- A worker that must be told a changed range gets it through `{range}` and `{patch}`; the script writes `diff.patch` as before.

### D4

**The workers.**

| role | station, the log's `<station>` | models | what |
|---|---|---|---|
| conformance, adversarial | `converge-<role>-r<N>` | the plan's table of the role, else `[converge]`'s | the packet's judge round |
| verify | `converge-verify-<role>-r<N>`, or `converge-verify-pickup-r<N>` | the role's table, effort `medium` | a round after a fix, or the pickup check |
| fixer | `converge-fix-r<N>` | `[converge.fix]` always, effort `medium` when it names none | the fix pass, no matter which card |
| shadow | `converge-shadow-<role>-r1` | the other host's, `_shadow` | round 1, driving nothing |

- `<N>` is the round the worker judges, or the round that found the cards for the fixer. A retry or a rewrite worker repeats the
  station: `_free_log` appends `-2`, so its log is `<stamp>-converge-<role>-r<N>-2.log`.
- A checker or a verify worker runs through `host.checker(change, station, table, cwd, prompt, deadline, effort)`; `table` is
  `conformance`, `adversarial`, `shadow-conformance` or `shadow-adversarial`. The fixer runs through `host.worker`, on converge's
  host: `[converge.fix]` names no executor ([F7](#context)).
- `Run.checker` stops reading a mailbox and returns `Checked(code, killed, models, limit, fallback, tokens)`, a frozen
  dataclass: the Codex fallback of D76 is the code it already holds, the answer string is gone. Past `deadline` it starts nothing
  and returns `Checked(1, False, models, "converge's time is spent", False, None)`; a timeout kill is `killed`.
- A round's checkers run in threads; the threads share nothing but `host`, whose `worker` already runs from the version threads.
- `tools_for` gives each `converge-…` station `WORKER_TOOLS`, so a worker has no `Agent`. `CACHE_HOUR` is the cut alone.
- A fixer's model never depends on a card's grade: the scenario *The fixer by grade* is rewritten to say so ([F12](#context)); the
  validator keeps a scenario's title across a MODIFIED requirement, so the titles with "mailbox" and "conductor" in the delta stay.
- The **pickup check** runs through `host.checker` on the needed role's table, as a normal Step 7 round when that role's table
  names another host: the mailbox's reason for that row is gone, so one rule holds: the needed role's table, at `medium`.

### D5

**The halts a script goes on from** ([brief](proposal.md) Q5):

| event | the script does | then |
|---|---|---|
| a worker exits non-zero, or leaves no file | one fresh worker for that role, its prompt unchanged | a second failure halts, naming the role and its log |
| a findings file is malformed ([D2](#d2)) | one rewrite worker, given the file and the contract | still malformed: one debt card naming the file, and the round goes on as the role clean at `HEAD` with no cards |
| the fixer's gate is red, or its tree dirty | one more fix pass, with the red lines as the cards | still red or dirty: `cap reached` |
| `debt_match.py` exits 2 | an empty `debt-cards.md` | the round goes on |
| `replay` exits 2 | a worker round over the merge, as an ordinary catch-up | |
| `.minions/debt.lock` held | waits, 5 seconds a poll, 10 minutes | then halts, naming the lock |
| a worker timed out, a usage limit, a tool its station lacks | `Run.worker`'s existing halt | stays |
| a gate red before round 1, a gate changed, a security `critical` or `high` card open at the cap, an amend, an old layout, no `sandbox-exec`, no worktree | halts as `K` does | stays |

- The debt card for a malformed file is written at the debt write, as a `Q<n>` card of the run: `- **<change>·M<n> — <role>'s
  findings file was malformed after a rewrite**`, its fields as the card's table needs, **Priority** `medium · conformance ·
  maintainability`.
- A retry's first failure is logged `retry — <role>: <why>` as a `fan-out` event's detail, never as a new event.

### D6

**The commands run sandboxed.** `converge.py` runs, each as one `host.sandboxed(["uv", "run", "--script", <script>, …], cwd,
host.trees(), out)`, `out` the round's open file: `gate_run.py`, `gate_check.py` and `plan_check.py`, which re-runs the `Verify:`
lines itself inside that one call.

- This change adds the parameter `out=None` to `sandboxed` of [0107](../0107-sandbox-runner/design.md): given a file object, each
  output line, and the `sandboxed: denied —` line after a refusal, is written to it in place of `sys.stdout` and `sys.stderr`. A process-wide `redirect_stdout` is no answer: versions and a round's
  checkers run in threads.
- The exit is the command's own; `no OS sandbox` is `Stop(2)`, which `converge` meets as [D1](#d1) says and returns as 2.
- `UV_OFFLINE=1`: a gate that needs the network fails red with the denial line. The gate's warm cache is the operator's.
- The `**Still true?**` commands of [D7](#d7) run the same way, one argv each, never a shell.

### D7

**The debt write.** Its order is `K`'s Step 9, with these rules:

- Take each non-blocking card whose Status is not `verified`. Amend cards first, as `K` does, with `Amend: yes` in place of the
  path test.
- A card's **Still true?** value holds a command when it opens with a backtick-quoted span: the span, `shlex`-split, is the argv.
  Exit 0 → still true: write the card. Exit 1 → gone: moot, named in the report with the command. Any other exit, or no command in
  the value → write the card unchecked.
- The lock is `mkdir .minions/debt.lock`; held → wait ([D5](#d5)). A fixed repeat's old card is cleared by the same exit rule.
- The qualified id, the heading and the skip of an id already in the debt are as `K` has them.

### D8

**What changes in `conduct.py`.**

- `Run.advance`: for the converge stage, no prompt, mailbox or spawn. It logs `spawn converge · script` and, on return,
  `finish converge · exit <n> · <s>s` — so the run log's minutes and `log verify` keep their pairs — then runs `check` and `judge`
  as now. `PROMPTS` loses its converge entry; `_worker_clause`, `WORKERS`'s clause use and `shadowed` clause are removed.
- The mailbox is removed: the constants `CHECKERS`, `MAILBOX_POLL`, `CHECKER_WAIT`, `REQUEST_BYTES`, `REQUEST_ID` and `CHECKER_SPAWNS`, `_mailbox`, `_open_mailbox`, `_take_request`, `_reply`, `serve_requests`, `_answer`,
  `_answer_refused`, `Run.server`, `checker()` and the `checker` subparser, removed with their tests. `_entries`, `_bounded` and `_place`
  stay: other code reads them ([F7](#context)).
- `Run.checker` takes the [D4](#d4) arguments and returns `Checked`; the `mailbox` parameters of `argv`, `Run.spawn` and `Run.worker`
  go with their last reader, and so does the `between` parameter of `work`, `Run.worker` and `Run.spawn`, whose only reader was
  `Run.server`.
- Converge's row of `STATION_TOOLS` and `CACHE_HOUR`'s `"converge"` are removed. `[converge] model` stays the checkers' default: `CONDUCTOR`
  is renamed `CHECKER_DEFAULT` and its branch in `_models` stays, so `[converge]` on Claude naming no model and no effort plans
  `claude-sonnet-5-5` · `high`, and `Run.checker` runs a checker whose table names no model on the plan's `converge` model, and
  on its effort when the table names none either — the delta's *The conductor's default*.
- `stage_of` and `_unjudged` take a `skips` argument, the run's read-once `Run.skipped` for the version; given, it replaces the
  `_skips(runs, change)` read, so a skip planted after the plan was read binds at the next run (card `0105·S2`). Called with none,
  by `status` and `check` by hand, they read the file as before. `Run.advance` and the stage poll pass it.
- `main` gains the `converge` subparser ([D1](#d1)); the module docstring's command list gains it.
- `tests/fake_worker.py` plays one worker per role — checker, fixer, verify — from the prompt's role line; the whole-converge
  modes become per-role modes the converge tests set; `plant-executor` and `dies-converge` keep their cases.
- `surfaces.py` and `tests/test_surfaces.py` are deleted; `THREAT_MODEL.md`'s `## Surfaces` stays for the cut's warning.

### D9

**The record.** D78 · *The converge conductor is a script* is added to `docs/decisions.md`'s check-loop group, after D76 in that
group's index line, and the D3, D40, D47, D51, D53, D64, D68, D70, D71 and D76 texts are edited where they live (`A7`).

```markdown
### D78 · The converge conductor is a script

**Converge's conductor is `skills/mf-converge/scripts/converge.py`, which `conduct.py` loads in-process and calls in a version's
thread; `conduct.py converge` runs it by hand, and `skills/mf-converge/SKILL.md` is its front. The checkers, the fixer and the
verify workers are the only LLMs, each a fresh process the run starts, one log each; the gate, the check scripts and a card's
**Still true?** command run under the sandbox runner. A script goes on where it can: one retry, one rewrite worker, one more fix
pass; only the environment, a loop outcome, a red gate and a security card halt. The fixer runs on `fix=`'s model always.**

- **Why:** the conductor was 17–24% of a converge and judged six things; a script reads fields.
- **Accepts:** one implementation with two fronts · a card's **Still true?** prose is never checked · a command that exits 1 is
  moot · a macOS-only converge until Linux has a runner.
- **Rejected:** a runner that reimplements stations inside `conduct.py` · a python claim leader · a conducting LLM for a hand converge.
- **Amends:** D3, D40, D47, D51, D53, D64, D68, D70, D71 and D76, each edited where it lives.
```

The edits, before → after:

- `### D3`: "No station is reimplemented: there is no third way to run the line." → "No station is reimplemented: converge's
  conductor is one script with two fronts, `mf-ship` and the skill ([D78](#d78--the-converge-conductor-is-a-script)); there is no
  third way to run the line."
- `### D40`: "The conductor dispatches, waits and reads findings from shared disk" gains "— converge's conductor is a script —", and
  "A checker on another host than its conductor's is a fresh agent process `conduct.py` starts on the conductor's request
  ([D68](#d68--…))" → "A checker on another host than converge's is a fresh agent process the script starts through the run's
  checker call."
- `### D47`: its "a converge worker its checker mailbox" and "An LLM conductor waiting on the workers" rows are reworded: the
  converge conductor is a script `conduct.py` calls, and the workers are the stations.
- `### D51`: gains "The converge script runs at the conductor's rights and runs each command of a builder's code under the sandbox
  runner."
- `### D53`: "The converge fixer edits no plan" keeps; gains "`## Tests` and `## Dependencies` among the sections it never edits".
- `### D64`: "Converge's conductor runs on Sonnet 5.5 · high" → "Converge's checkers default to `[converge]`'s model, Sonnet 5.5 ·
  high"; "and its fixer on the mid tier · medium, on adversarial's model,
  adversarial running on converge's host and not skipped, when a card it is sent blocks" → "and its fixer on the mid tier · medium
  always"; "A fix that touches no `## Surfaces` path … takes its adversarial head by recomputation" goes, with **Rejected**'s
  "an adversarial verify skipped by the conductor's judgment".
- `### D68`: "runs through the checker mailbox, in the home folder's queue: the conductor writes the request, `conduct.py` spawns the
  checker" → "is started by the converge script through the run's checker call, on the plan's model and effort"; **Accepts** and
  **Rejected** lose the mailbox lines.
- `### D70`: "the cut and converge `Agent` too" → "the cut `Agent` too"; "The cut and converge ask for the 1-hour cache" → "The cut asks for
  the 1-hour cache"; "the converge conductor reads no mandatory context" goes.
- `### D71`: **Accepts** loses "a pickup check on conformance's model moves adversarial's head when `surfaces.py` exits 0 and no
  adversarial card was picked, as the head by rule does" and "a pickup whose check needs a mailbox role verifies in a counted
  round"; its headline gains "on adversarial's model when a card it picked is adversarial's, else conformance's".
- `### D76`: "A mailbox checker on Codex that is limited" → "A converge checker on Codex that is limited"; **Why**'s "a wait in the
  mailbox blocks its thread and costs conductor turns" → "a wait costs a version's thread"; **Rejected**'s "`conduct.py` falls back
  inside the mailbox" → "`conduct.py` falls back inside the run's checker call".

### D10

**The prose and the metrics.**

- `K` becomes a front of ~40 lines: the parameters, `conduct.py converge <id> [conformance=…] [adversarial=…] [fix=…] [grant=yes]`,
  what it prints, and a pointer to `converge.py`'s docstring. `tests/test_skills.py`'s converge rows name `converge.py` and no
  longer `surfaces.py`, `stamp.py` and the rest, which the script's docstring names.
- `metrics/catalogue.toml`'s `converge-reading-set` becomes the fixer's set: `AGENTS.md`, `W` and `fix.md`; `reading_set.py`'s
  `converge` kind and its test follow.
- `review_metrics.py` books a worker by its log name ([the delta](specs/sdd/spec.md)); the Agent-description path stays for old logs.
- `scripts/metrics/run.py` counts each `converge-…` worker log in the converge stage's cost and tokens, and its minutes stay the run
  log's `converge` spawn and finish.
- `THREAT_MODEL.md`: `## Surfaces` intro says the cut's warning reads it, no converge fix does; *Out of scope* names the converge
  fixer's design-prose write beside the rescue's, bounded by the sections it never edits (card `0101·S4`); its mailbox lines go.

### D11

**The debt.**

| card | closed by |
|---|---|
| `0095·S1` — `open_cards.py` drops a Status not spelled `open`, `fixed` or `wontfix` | phase 1: it fails closed, as `surfaces.py` did, exit 2 naming the card |
| `0101·S4` — the fixer may rewrite `design.md`'s `## Tests` | `W`'s amend-card paragraph, `fix.md` and `THREAT_MODEL.md` |
| `0103·R2` — `W` still forbids the decision edit fix notes allow | the same paragraph, qualified |
| `0105·R7` — `skip_stub.py`'s refusal, absent from the spec | the delta's *A converge conductor stubs a skipped checker* |
| `0105·S2` — a planted `[converge] skip` binds in the run it is written in | [D8](#d8): `stage_of` and `_unjudged` read the skip once |

The mailbox cards `0097·R1`, `0097·R5`, `0097·R6`, `0097·R7`, `0097·S4`, `0097·S5`, `0100·R2`, `0100·S4` and `0101·S8` are moot: their
code is opened or deleted. The release deletes the five; the person clears the rest from `.minions/debt.md`.

## Tests

The new test file is `tests/test_converge.py`: the script at the lowest layer, a fake `host`, no process, no git remote (`T1`).
The conduct-level tests take [C5](#c-rows)'s fake `sandbox-exec` and a fake repo with a `gate` recipe.
`tests/test_conduct.py` gains the integration tests that drive a version through `conduct.py` over the fake hosts (`T2`: each
extends a test that already reaches converge). No end-to-end browser test: the repository has none.

Counts at `HEAD`: `git grep -c '^def test_' -- tests/test_conduct.py tests/test_surfaces.py tests/test_skills.py tests/test_open_cards.py
tests/test_review_metrics.py tests/test_metric_scripts.py` prints 160, 2, 21, 2, 15 and 15 for the six files in that order.

| test | layer | proves | `T` |
|---|---|---|---|
| `test_open_cards_refuse_what_they_cannot_read` (extended) | unit | [D11](#d11): a Status in another case is judged as its folded word; a word outside `open`, `fixed`, `wontfix`, `verified` and `accepted`, or a Status line under no title, exits 2 naming the card | T2 |
| `test_the_output_goes_to_the_file_given` (new, `tests/test_sandboxed.py`) | unit | [D6](#d6): `out` receives each line and the denial line, and `sys.stdout` and `sys.stderr` none; with none given the output goes to `sys.stdout` as before | T1 |
| `test_the_run_hands_converge_its_trees_and_sandbox` (new, `tests/test_conduct.py`) | unit | [D1](#d1): `Run.trees` is `reach(primary)`; `Run.sandboxed` runs the module function with `out` | T1 |
| `test_a_converge_refuses_what_it_cannot_start` (new) | unit | [D3](#d3): a dirty tree, an unticked box, an empty range, a red gate, a changed gate, an old layout; no OS sandbox exits 2 | T1 |
| `test_the_freeze_writes_the_patch_the_bundle_and_the_debt_cards` (new) | unit | the files, the counts, `debt_match.py` exit 2 → an empty file | T1 |
| `test_each_worker_prompt_is_filled_from_its_reference` (new) | unit | [D2](#d2): each `## Prompt`, every placeholder filled, none left | T1 |
| `test_a_findings_file_is_read_by_its_fields` (new) | unit | scope, `passes`, `inconclusive`, `Amend:`; each malformed form | T1 |
| `test_a_clean_round_converges_with_no_fix` (new) | unit | `fan-out`, `verdicts`, `done`; the status log's text | T1 |
| `test_a_skipped_checker_is_a_stub` (new) | unit | `skip_stub.py` after each freeze; the role not skipped alone is dispatched | T1 |
| `test_a_blocker_is_fixed_verified_and_cleared` (new) | unit | [D4](#d4): the fixer on `fix=` with a blocking card open; the re-freeze; a verify round | T1 |
| `test_a_red_gate_after_a_fix_gets_one_more_pass_then_the_cap` (new) | unit | [D5](#d5) | T1 |
| `test_the_cap_halts_with_the_open_blockers` (new) | unit | `cap reached`, the ids, a security card named | T1 |
| `test_plan_check_left_halts_amend_needed` (new) | unit | `fix.md`'s line; a repeat is `amend needed — plan check: …` | T1 |
| `test_round_one_pickup_rides_with_the_fix` (new) | unit | `pickup … with the fix`; a fixer that commits nothing runs no check | T1 |
| `test_a_pickup_check_runs_on_the_needed_role` (new) | unit | adversarial's model for an adversarial card, else conformance's | T1 |
| `test_a_granted_round_goes_one_past_the_cap` (new) | unit | `· grant`, the fixer, one verify round, no pickup | T1 |
| `test_a_catch_up_judges_the_new_commits` (new) | unit | ancestry, the cap and its own count, a merge's remerge scope | T1 |
| `test_a_merge_only_catch_up_is_by_rule` (new) | unit | `replay`, the files' frontmatter, `by rule`; exit 2 → a worker round | T1 |
| `test_a_run_resumes_from_its_status_log` (new) | unit | parametrized by the latest event, as `K`'s resume table | T1 |
| `test_a_shadow_round_runs_the_other_host_and_drives_nothing` (new) | unit | round 1 only, `overlap.py`'s line, a failed shadow halts nothing | T1 |
| `test_the_debt_is_written_once_under_its_lock` (new) | unit | the lock, a 10-minute wait, qualified ids, a held id skipped | T1 |
| `test_a_still_true_command_runs_sandboxed_and_a_prose_card_goes_unchecked` (new) | unit | [D7](#d7): exit 0, exit 1, another exit, no command | T1 |
| `test_an_amend_card_halts_the_debt` (new) | unit | `Amend: yes`, a moot one, an answered one | T1 |
| `test_a_fixed_repeats_old_card_is_cleared` (new) | unit | the old card deleted, its heading when empty | T1 |
| `test_a_failed_worker_gets_one_retry` (new) | unit | [D5](#d5): exit 1, no file, a second failure | T1 |
| `test_a_malformed_file_gets_a_rewrite_then_a_debt_card` (new) | unit | the rewrite worker, then the card, the run on | T1 |
| `test_the_report_names_the_verdicts` (new) | unit | the close-out sentences from disk | T1 |
| `test_a_version_converges_with_no_conducting_worker` (new, `tests/test_conduct.py`, slow) | integration | the acceptance: the fakes see no converge station, one log per worker named `converge-<role>-r<N>` | T2 |
| `test_a_skip_is_read_once` (new, same) | unit | [D8](#d8): `stage_of` with `skips` ignores a planted file; with none reads it; a run's poll of a version with no planned skip passes an empty set, never none, and ignores the planted file | T1 |
| `test_the_converge_command_runs_by_hand` (new, same) | integration | `conduct.py converge`, its arguments, its exit | T2 |
| `test_a_codex_checker_is_stamped_and_counted` (renamed from `test_a_mailbox_checker_is_stamped_and_counted`) | integration | the checker's `model:` and `tokens:` stamp | T2 |
| `test_a_codex_checker_runs_through_run_checker` (renamed from `test_a_codex_checker_runs_through_the_mailbox`) | integration | the Codex spawn, its models, no mailbox | T2 |
| `test_a_limited_checker_falls_back_to_claude`, `test_a_shadow_round_drives_no_fix`, `test_a_small_cap_is_granted_automatically` and the other converge tests of [F15](#context) (extended) | integration | each keeps its name and its assertion, over `converge.py` and the per-role fake | T2 |
| `test_review_metrics_books_a_worker_by_its_log_name` (new, `tests/test_review_metrics.py`) | unit | the delta's scenarios | T1 |
| `test_a_plan_check_finds_what_the_plan_left` (extended, `tests/test_plan_check.py`) | unit | [C8](#c-rows): a removed name in a living requirement the delta removes halts nothing; the same name in the next requirement, which the delta keeps, exits 1 naming its line | T1 |

**Removed.** Each test below is deleted and named here, as T5 asks.

| removed test | carried by, or retired by |
|---|---|
| `test_a_fix_that_reaches_no_surface_is_by_rule` and `test_a_fix_that_reaches_security_is_verified` (`tests/test_surfaces.py`, whole file) | no live behaviour to carry: they prove only *A fix that reaches no surface takes its adversarial head by recomputation*, which this change's delta removes ([specs/sdd/spec.md:604](specs/sdd/spec.md)), with `surfaces.py`; the person retired it at the plan (brief Q7, H5 never fired) |
| `test_a_fix_reaching_no_surface_takes_adversarial_by_rule` (`tests/test_conduct.py`) | the same |
| `test_a_worker_clause_names_its_model_and_effort` (`tests/test_conduct.py`) | carried by `test_a_blocker_is_fixed_verified_and_cleared`, which reads each worker's model from the plan; the prompt clause it also proved goes with the LLM conductor (brief Q1, Q8) |
| `test_a_checker_request_is_bounded` (`tests/test_conduct.py`) | the request, answer and `work`-`between` assertions prove only *A converge checker on another host runs through the mailbox*, which this change's delta removes ([specs/sdd/spec.md:612](specs/sdd/spec.md)), the person's call at the plan (brief Q6); the spent-deadline refusal and the timeout kill of `Run.checker` are carried by `test_a_codex_checker_runs_through_run_checker`, extended with each |
| `test_the_checker_command_sends_and_waits` (`tests/test_conduct.py`) | no live behaviour to carry: it proves only the mailbox's `checker` command, under *A converge checker on another host runs through the mailbox*, which this change's delta removes ([specs/sdd/spec.md:612](specs/sdd/spec.md)), brief Q6 |

- The end-to-end runs it adds are none beyond the one slow integration test, which runs on the fake hosts.
- After the build, `tests/test_surfaces.py` is gone and `tests/test_conduct.py` loses the tests of the table above and gains its new ones.
- The by-grade scenario of the living spec had no test ([F12](#context)); the new fixer rule is tested by `test_a_blocker_is_fixed_verified_and_cleared`.
- **Guards.** The retry's twin is the step of `test_a_failed_worker_gets_one_retry` with the retry removed, the red run in the
  commit body (`T6`); the sandbox's twin is `test_a_still_true_command_runs_sandboxed_and_a_prose_card_goes_unchecked` with the call
  made bare.

## Dependencies

None.

## Risks / Trade-offs

| risk | mitigation |
|---|---|
| the script is ~2k lines and its tests more; the status log's text drifts from what `conduct.py` matches | the status log is byte for byte ([D3](#d3)); `test_a_clean_round_converges_with_no_fix` and the resume cases assert each event; the slow test drives `check` |
| `0106-cut-scripts` and this change both open `_models_file`, `_table`, `_models`, `PROMPTS` and `main` | a text merge for `mf-integrate`; this change deletes the converge entry of `PROMPTS` and adds one subparser |
| this change's own converge runs the pinned `plan_check.py`, which lacks [C8](#c-rows)'s skip, so it flags the living lines of the requirement the delta removes | for this change's converge alone, the person put this branch's `plan_check.py` into the pinned tree, its original kept and restored after the release (2026-11-10) |
| a pinned skill (D55) keeps a live run on its tree across the switch | a findings file without the new fields is malformed, one rewrite worker fills it ([D5](#d5)); the status log's format is unchanged |
| a Still true? command that exits 1 for another reason drops a debt card as moot | the report names the command; the cost is a re-found card, as the old check's |
| the real Seatbelt gate may fail a step the fakes pass (`/dev`, `uv` cache) | [0107](../0107-sandbox-runner/design.md#risks--trade-offs) keeps its list of paths to widen; the first run is the person's |
| a malformed file the rewrite cannot mend reads as no cards, so a blocker in it goes unfixed this run | the debt card names the file and the report says so; the person chose a script that goes on (brief Q5), and the release's precondition reads the file's own verdict |
| a macOS-only converge | exit 2 `no OS sandbox`; Linux is a later version |
| checkers in threads share `host` | `Run.worker` already runs from each version's thread; the claim is per call |
| the living spec's phrases C4 stay stale until a later change | named in C4 |

## Migration Plan

None beyond the pin: a run on an old skill tree keeps its tree until it ends.

## Verdict

Build as written: the fields first, the script in three steps, the wiring and the record last.
