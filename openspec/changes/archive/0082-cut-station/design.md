# Cut station — design

`conduct.py cut` queues a settled brief under one lock; the run cuts it in a sandboxed worker of its own, checks the cut on
disk and builds it; `mf-cut-change unattended=yes` decides by the brief's switch or halts in one line. Verdict at the end:
ready to build.

## Context

The brief's `At` sha is `f349aa8` (v0.66.0). `git diff --name-only f349aa8..HEAD --no-renames` prints the 0081-cut-awake
release's files: `skills/mf-cut-change/SKILL.md`, `docs/decisions.md`, `tests/test_skills.py` among them. Every fact on
those paths was read again at HEAD `95dcad0` and stands, its line moved; the facts on `conduct.py`, `THREAT_MODEL.md`,
`docs/principles.md`, `skills/mf-ship/SKILL.md` and `skills/mf-plan/SKILL.md` stand unmoved.

- **F1. The claim:** `run()` (`skills/mf-ship/scripts/conduct.py:3690-3749`) detaches a child with `subprocess.Popen`
  into `.minions/runs/detached.log` and prints `run: started · pid <pid>` at once (`:3711-3723`); the child's
  `active.mkdir()` (`:3725`) is the only lock, and `shutil.rmtree(active)` (`:3749`) ends the claim after the pin move.
  **Gap A:** two callers that both see no claim both detach. **Gap B:** `join` (`:3498-3511`) reads the requests a last
  time, then `ship` pushes and `run()` removes the claim; a request in between is never read.
- **F2. The mailbox:** `_request(runs, name)` (`:3817-3820`) touches `.minions/runs/rejoin/<name>`; `_requests(runs)`
  (`:3788-3797`) reads and empties `runs / "rejoin"` through `_entries` (`:2014-2040`), one descriptor, no link followed.
  `rejoin` (`:3800-3814`) and `grant` (`:3841-3879`) write it; `take_requests` (`:3242-3267`) reads it each poll and
  `ship` (`:3606`) empties it at the start. A worker can write `.minions/` (`0063·S3`).
- **F3. The home folder:** `_digest(primary)` (`:1146-1148`) names a repo's files in `~/.mf-ship-origin/`
  (`KEPT_ORIGINS`, `:117`): the kept URLs, `<digest>.released`, `<digest>.gate`. `approve_gate` (`:3882-3910`) makes its
  folder `0o700` and its file `0o600` with `O_EXCL`, and a refusal exits 2, naming a sandbox.
- **F4. The worker:** `argv` (`:2151-2213`) gives a Claude worker `--add-dir` and `Edit(/<tree>/**)` for each of
  `reach(primary)` (`:2065-2078`) — the primary and every linked worktree — and `worker_settings` (`:2126-2148`) writes
  those and the common directory; a Codex worker takes them as `writable_roots`. `spawn` (`:2685-2729`) logs `spawn`,
  `finish` and a halt on a failed exit; `TOOLS` (`:122`) holds `Agent` and `Skill`.
- **F5. Joining a run:** `take_back` (`:3314-3362`) checks a requested version's stage, compares its models file, clears its
  halts, reads its plan, probes a new executor, then starts `take` (`:3185-3202`) in a thread it adds to `threads`.
  `open_versions` (`:460-480`) lists a branch only once it holds its change (`_holds`, `:447-451`).
- **F6. The cut:** `skills/mf-cut-change/SKILL.md` holds the id free at Step 1 (`:60-62`), makes the branch at Step 4
  (`:107-115`), waits at Steps 3, 8.5 and 9 (`:101-102`, `:182-184`, `:193-198`), and writes `models.toml` as "a
  suggestion … the human chooses" (`:316-318`, `:353`). Step 2 checks the `At` value with `git rev-parse --verify --quiet
  '<sha>^{commit}'` and then diffs from `<sha>` as written (`:75-77`): `':/fix|$(touch pwn)^{commit}'` passes that check
  (`0074·S2`).
- **F7. Models:** `_table` (`:1881-1893`) reads only named tables, so a top-level `decide = "recommended"` reaches no reader
  in this version; self-healing ship reads it later.
- **F8. Tests:** `git grep -c '^def test_' HEAD -- tests/` totals 221, 106 in `tests/test_conduct.py`. `fake_worker.py`
  reads the station from `Run the mf-(\w+) skill` (`tests/fake_worker.py:208`), which no `mf-cut-change` prompt matches.

## Goals / Non-Goals

**Goals:** the person's chat holds no cut; no two cuts take one number or start two runs; no cut or request lost at a run's
end; no worker-written file names what the run cuts or takes back; a cut halt that reads as the plan's.

**Non-Goals:** `mf-plan`'s close calling `cut` and `brief_check.py` (`0083-plan-queues`); the roadmap row (P10); a rescue
for a cut halt (P17); the cut station in the run and review metrics; `run --detach` waiting for its claim.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `conduct.py cut` takes the next free number under the queue lock, writes `.minions/cuts/<id>` and the queue entry in the home folder | P13, P18, C1 | the id given at dispatch (P3); the parameters in `.minions/` |
| [D2](#d2) | One lock, `~/.mf-ship-origin/<digest>.queue/lock`, `fcntl.flock`; with none live, the holder starts the run and waits for its claim; a run's close re-checks under it | P14 | a `mkdir` lock with a stale age; the run's claim as the lock |
| [D3](#d3) | The rejoin mailbox moves to `<digest>.queue/rejoin/`, written by the person's session alone | P14, `0063·S3` | the repo's `.minions/runs/rejoin/` |
| [D4](#d4) | The run reads the queue at its start and each poll; the conductor makes the branch and worktree; the cutter runs as the station `cut`; a check on disk, then `take` | P7, P15, P20 | a background subagent in the person's session (P4); the cutter making its own branch |
| [D5](#d5) | The cutter's reach: its worktree, the run directory, the common directory and the brief | P15 | the primary and every worktree, as other stations |
| [D6](#d6) | `cut-halted`: one line in the queue entry, no rescue; `status` and `report` show it; `rejoin <id>` clears it, and the run drops the half-done branch and cuts again | P17 | a rescue; a halt kept in a worker-written file alone |
| [D7](#d7) | `mf-cut-change unattended=yes`: P16's waits, `cut.halt`, the brief's `C` rows and `Cut` line, `models.toml` from the brief | P2, P8, P10, P16, P18, P20 | an `AGENTS.md` switch (D56) |
| [D8](#d8) | Step 2 takes an `At` value only as 7 to 40 hex digits, and diffs from the full sha | `0074·S2` | the `rev-parse` check alone |
| [D9](#d9) | D58 added; D20, D38, D41, D44, D47, D51, D57 amended; the threat model, the principles, `mf-ship`'s skill and the README | P9, P21 | — |

### D1

**`cut`** — `conduct.py cut <slug> <bump> brief=<path> [after=<id>[,<id>]] --executor claude|codex [--model <m>]
[--effort <e>]`, in `main`'s parser: `slug`; `bump`, choices `minor` and `patch`; `brief` and an optional `after`, each a
positional that must start with its `brief=` or `after=`; `--executor` required; `--model` and `--effort` optional. The
function `cut(cwd, slug, bump, brief, after, executor, model, effort) -> str` returns its line, and a `Stop` exits as the
others do. The cut station's own model is the person's, given here by `mf-plan`'s close (P18); no model name is written in
code (D41).

**Refusals, each `Stop(2)`, nothing written:** a slug `SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")` does not fully match
→ `cut: cannot run — not a slug: <slug>`; a missing prefix → `cut: cannot run — expected brief=<path>` (or `after=<ids>`); a
`brief=` value that is not an absolute path to a file → `cut: cannot run — brief=<path> is not an absolute path to a file`;
an `after` id that names no open version (`open_versions`) and no queued cut → `cut: cannot run — after=<id> names no open
version or queued cut`.

**Under the lock ([D2](#d2)):** with no run live, `preconditions(primary, executor)` runs first, and its `Stop` reaches the
caller with nothing reserved. Then `_next_id(primary)` is one above the highest number of: each change directory under
`openspec/changes/` and `openspec/changes/archive/` in the default branch's tree; each branch `git branch --list '[0-9]*'`
names, and each change directory in its tree; each name in `.minions/cuts/`; each queued cut. The id is
`f"{number:04d}-{slug}"`.

**The reservation** `.minions/cuts/<id>`, an empty file, is what the cut's Step 1 counts ([D7](#d7)). **The queue entry**
`<digest>.queue/cuts/<id>` holds the cut's parameters as one JSON object — `bump`, `brief` (the resolved path), `after` (a
list), `executor`, `model`, `effort`, `halt` (`null` while queued) — written whole to a temporary name in its folder and
moved in with `os.replace`. `_cuts(primary) -> dict[str, dict[str, Any]]` lists that folder through `_entries(…, empty=False)`,
each name `CHANGE_ID` fully matches; an entry that is no such object reads as one whose `halt` is `the queue entry is
unreadable`. `_write_cut(primary, id, entry)` writes one. **C1** (the brief's `## Decisions`): the parameters stand in the
home folder, where no worker writes, because the brief path widens the cutter's sandbox ([D5](#d5)): a worker writing
`.minions/` could otherwise name the file a cutter writes. P13's `.minions/cuts/<id>` stays, the id's mark alone.

**Its line:** a live run → `cut: queued <id> · the live run takes it`; else `_start_run` ([D2](#d2)) →
`cut: queued <id> · run started · pid <pid>`; a run that did not start → `Stop(2, "cut: queued <id> · <its reason>")`, the
entry left queued for the next run.

### D2

**The lock** — `_queue(primary) -> Path` is `Path.home() / KEPT_ORIGINS / f"{_digest(primary)}.queue"`.
`_queue_lock(primary)`, a context manager, makes `_queue(primary)` with `mode=0o700` and its parents, opens `lock` in it
with `os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW` and `0o600`, and holds `fcntl.flock(fd, fcntl.LOCK_EX)`, blocking, until its
block ends. An `OSError` there → `Stop(2, "conduct: cannot run — the home folder refuses the queue: <strerror>; run it
outside a sandbox")`. Held by `cut`, by `rejoin` and `grant` from their claim read to their request or start, and by a run's
close. A lock the kernel holds ends with its process, so it has no stale age.

**`_start_run(primary, executor) -> int`** — makes `.minions/runs/` with its parents, notes the size of
`.minions/runs/detached.log`, starts the child through
`_detach(primary, executor)`, the `Popen` that `run(…, detach=True)` holds today, moved into a helper `run` calls too; then
polls every 0.1 s, at most `CLAIM_SECONDS = 30`: the claim `live` → return the child's pid. The child exited, or the time
passed → read the log's lines past the noted size; any one starting `run: done` or `run: halt` → the run started and ended:
return the pid. A pin move prints its line after it, so the last line is not the one read. Else `Stop(2, "the run did not start — <that line, or: no line in .minions/runs/detached.log>")`.

**The close** — `run()`'s `finally`, after the pin move and `_unmark`, calls `_close(primary, active, executor, seen)` in place
of `shutil.rmtree(active)`. `seen` is `Run.seen`, `None` until `ship` sets it to a set as its first act, and `None` too when
`Run(…)` raised: a `None` starts no next run, so a run that fails before it reads the queue starts no chain. Under the lock
`_close` removes the claim, then, with `seen` a set, starts the next run with `_start_run` when the mailbox holds a request — a regular file, read through the folder's
descriptor with `os.lstat` and `S_ISREG`, the kind `_requests` deletes, so a folder planted there starts none — or, from [D4](#d4) on, a queued cut with no `halt` whose id is not in `seen`,
the ids the run read. It prints `run: next started · pid <pid>`, or the `Stop`'s line. A `Stop` from the lock removes the
claim with no lock and starts nothing. A run whose start halts reads every queued cut first, so its close starts none, and no
chain of runs follows a halt.

```
cut / rejoin / grant                    a run's close
  lock ─┬─ claim live? ── yes ─▶ queue ─┐     lock ─▶ remove claim ─▶ request or unread cut? ─ yes ─▶ _start_run
        └─ no ─▶ queue ─▶ _start_run    │                                        │ no
              (waits for the claim)     ▼                                        ▼
  unlock ◀──────────────────────────────┘                                     unlock
```

### D3

The mailbox is `_queue(primary) / "rejoin"`. `_request(primary, name)` makes it `0o700` and touches `name` there;
`_requests(queue)` reads and empties `queue / "rejoin"` as today, so its link and descriptor rules stand. `rejoin`,
`grant` and the `Run` (`self.queue`, its start and each poll) use it; `.minions/runs/rejoin/` is no longer read or written.
Under the lock, `rejoin` reads the claim and writes its request; `grant` takes the lock before its claim read and holds it to
its request, or, with none live, to `_start_run(primary, executor)` in place of `run(cwd, executor, True)`, printing
`grant: recorded · run started · pid <pid>`: a cut right after it then sees the run live.

### D4

**At the start** — `ship` reads `_cuts(self.primary)` beside `open_versions`; every id it reads goes into `self.seen`. A cut
with a `halt` is a **halted cut**; the others are **takeable**. An open version that is also a queued cut — a cut that
committed before its run ended — goes through its cut thread, not a `take` of its own. The `start` line gains ` · cuts <ids>`
after its versions when any cut is queued. With no version and no takeable cut, the run closes: `halt` when a cut is halted,
else `nothing to ship`. A takeable cut counts as no stuck version, so the run probes and starts; `executors()` also names each
takeable cut's entry executor, so a cutter's executor is probed before its first worker. Each takeable cut gets a thread,
`self.cut(id, threads)`, beside the versions'. Each halted cut is logged as a halt, `cut-halted — <halt>`: once the threads
have started, or, when no thread starts, before the close, so it starts no thread and stops no other.

**Each poll** — `take_requests` reads the queue before its requests: a cut with no `halt`, no live thread, and an id not in
`self.seen` or named by a request this poll, has its halts cleared, is logged `run · cut — <id>: taken`, and gets a thread;
its id goes into `self.seen`; its entry executor, when the run has not probed it, is probed first in this main thread, and a
refused probe halts it as `take_back` halts a version. The open-version loop skips every id the queue holds: a queued cut
joins through its own check alone. It returns `True` when it started one, so `join` does not close past a cut. `EVENTS` gains
`cut`.

**The station** — `Run.cut(id, threads)`:

0. **Its `after`:** while an `after` id is itself a queued cut with no `halt`, the thread waits, polling every
   `REJOIN_POLL`: the dependent's cutter reads its dependency's committed change (`I9`, `I10`). A dependency that halts
   halts the dependent, `after <id> is cut-halted`.
1. **The branch, as code** (P15): when `refs/heads/<id>` stands and `_holds` it, skip to the check. When it stands holding no
   change, `git worktree remove --force` its worktree, if `_worktrees` lists one, then `git branch -D <id>`. Then
   `git worktree add -b <id> <self.worktrees>/<id> <default branch>`. A stale `.minions/changes/<id>/cut.halt` is removed.
2. **The cutter:** `self.spawn(id, "cut", tree, prompt, (executor, model, effort), brief=<the entry's brief>)`, the prompt
   `PROMPTS["cut"]`: `Run the mf-cut-change skill for change {change} with arguments `{change} {bump} brief={brief}{after}
   unattended=yes`.`, `{after}` being ` after=<ids>` or empty. It runs under the run's own awake hold (P20).
3. **The check**, `_check_cut(primary, id, tree) -> str | None`, the first that holds: the cutter's
   `.minions/changes/<id>/cut.halt`, read through no link, its first line, at most 300 characters; the branch tip's subject is
   not `docs(<id>): land the change directory` → `<id>: no cut commit at the branch's tip`; `_holds` fails → `<id>: the
   branch holds no openspec/changes/<id>/`; `_dirty(tree)` → `the tree is not clean`; no
   `.minions/changes/<id>/models.toml` → `no .minions/changes/<id>/models.toml`. It is logged `check — cut · pass` or
   `· fail — <why>`.
4. **A pass:** under the lock, delete the queue entry and `.minions/cuts/<id>`; log `run · cut — <id>: cut at <sha7>`. Then
   `self.admit(version)` — the part of `take_back` from clearing the halts to the probes, moved into a method both call, its
   probes held under a new `self.probing` lock so two cut threads never probe one executor twice — and, when it admits,
   `self.take(version, threads)` in this same thread: no thread adds to `threads` but the main one.
5. **Anything else** sets the entry's `halt` ([D6](#d6)): every exit of `Run.cut` that does not delete the entry sets it, a
   `conduct.py failed` crash included, so a close never re-starts a cut its run took.

### D5

`argv` and `spawn` take `brief: Path | None = None`; `spawn` passes `brief=` to `argv` only when it is not `None`, so the
`argv` spies of `test_a_station_runs_on_its_executor` and `test_the_plan_is_read_once` stand. With it, `trees` is the cutter's worktree and `primary / ".minions"`,
not `reach(primary)`. A Claude cutter gets `--add-dir` for each, `allowlist(trees, tools)`'s rules plus `Edit(/<brief>)`, and
`worker_settings` writing those, the common directory and the brief. A Codex cutter's `writable_roots` are the common
directory, those trees and the brief's folder: Codex roots are folders. The cutter's plan reviewers are its own subagents
(`Agent` in `TOOLS`), inside its sandbox. The common directory must stay writable: a commit in a worktree writes it.

### D6

**The halt** — `Run.cut_halted(id, reason)`: under the lock, the entry's `halt` becomes `reason`; the run logs
`<id> · halt — cut-halted — <reason>`, save after a failed exit, whose halt `spawn` already logged, the entry taking that
reason. No rescue runs: a cut halt is a plan gap (P2), answered in the plan.

**`status`** — after the version lines, one line per queued cut in id order: `<id> · cut`, or
`<id> · cut-halted — <halt>`. An open version that is a queued cut prints its cut line alone. **`report`** reads the run log
as today: the cut's halt line is one of its halt lines, and a halted cut's branch gives its version line.

**`rejoin <id>`** naming a queued cut, under the lock: clear its `halt`; a live run → `_request(primary, id)` →
`rejoin: requested <id>`; none live → `preconditions(primary, the entry's executor)`, then `_start_run` →
`rejoin: requested <id> · run started · pid <pid>`. The run's poll then takes it, or the new run's start does, and the
station's step 1 drops the half-done branch.

### D7

`skills/mf-cut-change/SKILL.md`, each edit in its step:

- **Parameters** — a row `` | `unattended` | no | `unattended=yes` — set by the run's cut station alone, never by hand | ``,
  and after the table an **Unattended** paragraph: the cut never waits. Its **switch** is `decide: recommended` in the brief's
  `## For the cut` item for this change. Under it, a moved fact that fails (Step 3) and a plan-review doubt that changes a
  decision or survives the second review (Step 8.5) take the recommended option, and the cut adds
  `| C<n> | decided by the cutter: <what> | <reason> |` to the brief's `## Decisions` table, `<n>` one above its last `C` row,
  else 1. Without the switch, each is a halt. Always a halt: a `## Dependencies` that is not `None.`, a self-check item the
  cut cannot meet, a doubt with no clear recommendation, a `debt:` id not found, and every halt of the steps. **An
  unattended halt** writes one line to `.minions/changes/<change-id>/cut.halt` —
  `<change-id> waits on one doubt: <the doubt> · <path:line>`, or `<change-id> failed: <the check>` — commits nothing, and
  ends its turn.
- **Step 1** — unattended, no awake hold: the run holds the Mac (P20). Its first precondition becomes: a linked worktree on
  the branch `<change-id>`, `git merge-base --is-ancestor HEAD <default-branch>` exiting 0, and `git status --porcelain`
  printing nothing. The id-free rule gains "and than every reservation in `.minions/cuts/`". Unattended, the whole id-free
  rule is replaced by one: `.minions/cuts/<change-id>` stands — the run reserved the number under its lock — and the `after`
  rule by: each `after` id is an open version, its number lower than `change-id`'s.
- **Step 3** — the wait gains: unattended, the switch's rule.
- **Step 4** — unattended: the branch and worktree stand, made by the run; skip the step.
- **Step 6** — a `debt:` id not found goes to the human; unattended, it is a halt.
- **Step 8.5** — the table's waiting rows gain: unattended, the switch's rule.
- **Step 9** — unattended: show nothing; each waiting row is a halt.
- **Step 11** — unattended: no hold to stop. After the commit, write `.minions/changes/<change-id>/models.toml`
  (as *Suggesting models* says), then add `Cut <YYYY-MM-DD> as <change-id> at <short sha>.` on its own line after the brief's
  `## For the cut` list. The last line: `Next: the run builds it.`
- **Suggesting models** — when the brief's `## For the cut` item for the change names models, write exactly those — the
  person chose them at the plan's close (P18) — and `decide = "recommended"` before the tables when it says
  `decide: recommended` (P8); else suggest, as today. The closing "A suggestion, never an instruction: the human chooses."
  becomes "A suggestion, never an instruction: the human chooses — at the plan's close, where the brief names the models."
- **Never** — "Never build, or edit anything outside `openspec/changes/<change-id>/`." becomes "Never build, or edit anything
  outside `openspec/changes/<change-id>/` and `.minions/changes/<change-id>/`, save, unattended, the brief's `Cut` line and
  `decided by the cutter` rows."

### D8

Step 2's *Moved facts*: "A `brief` with an `At <sha>, <YYYY-MM-DD>.` line → first run `git rev-parse --verify --quiet
'<sha>^{commit}'`; it exits other than 0 → every fact is a moved fact. Else run `git diff --name-only <sha>..HEAD
--no-renames`" → "A `brief` with an `At <sha>, <YYYY-MM-DD>.` line → a `<sha>` that is not 7 to 40 characters of `0-9a-f`
makes every fact a moved fact, and no command takes it. Else first run `git rev-parse --verify --quiet '<sha>^{commit}'`; it
exits other than 0 → every fact is a moved fact. Else run `git diff --name-only <the full sha it printed>..HEAD
--no-renames`". The worked example below it stands.

### D9

- **`docs/decisions.md`** — **D58 · A settled brief is cut by a conductor station**, in *Planning*, its id added to the
  diagram's Planning list: `conduct.py cut` queues a brief under the queue lock, reserving its number; the run makes the
  branch and worktree, runs `mf-cut-change unattended=yes` sandboxed to its worktree, the run directory and the brief, checks
  it on disk and builds it; unattended, the switch `decide: recommended` takes the recommended option, logged in the brief,
  and every other doubt halts at `cut-halted`, no rescue, answered by a re-plan and `rejoin`; queuing a cut is the person's
  yes to cut, run, merge and push it. **Why:** the chat stayed busy with cuts, and two cutters raced for one id.
  **Rejected:** a background subagent in the person's session · the id given at dispatch · an `AGENTS.md` switch · a rescue
  for a cut halt · the parameters in `.minions/`. Amended: **D20** — the number is also above every reservation in
  `.minions/cuts/`, and `conduct.py cut` gives the next free one under its lock; **D38** — an unattended cut halts where this
  one waits; **D41** — models the brief names are the person's, written by the cut; **D44** — ids are reserved against every
  open branch and every reservation `cut` wrote under its lock, and its *Rejected* drops "a reservation file"; **D47** — the
  run takes each queued cut, its mailbox stands in the home folder's queue, and its close re-checks under the lock; **D51** —
  the cutter writes its worktree, the run directory and its brief alone; **D57** — `cuts/` generic, `cut.halt` the change's.
- **`THREAT_MODEL.md`** — *Unattended workers* (`:17-23`): the cutter's reach; *A person's yes* (`:40`): "or a cut the person
  queued"; *Entry points*: the brief (`:44`) read and written back by an unattended cutter; *Rejoin requests* (`:52-59`): in
  the home folder's queue, written by the person's session alone, a file in `.minions/runs/rejoin/` no request; a new line:
  `.minions/cuts/<id>` and `cut.halt` are worker-writable — a forged reservation burns a number, a forged `cut.halt` halts
  its cut — and no worker names the brief a cutter writes.
- **`docs/principles.md`** — *The repo reaches nothing outside itself* (`:137-152`): the operator's brief is also read and
  written by the cut station's sandboxed worker; `conduct.py`'s records gain the queue, `<digest>.queue/`.
- **`skills/mf-ship/SKILL.md`** — the role line: queuing a cut is the person's yes too; the diagram gains the queued cuts;
  the command table gains `cut`; `status` names `<id> · cut` and `<id> · cut-halted — <line>`; `rejoin` clears a queued cut's
  halt and, with none live, starts a run; Step 2's table gains a `cut-halted` row: report it in full, then stop — the person
  runs `/mf-plan <what> depth=hard from=<its brief>`, then `conduct.py rejoin <id>`.
- **`README.md`** — the `mf-ship` row (`:33`) gains "— and each brief queued with `conduct.py cut`"; *Parallel workspaces*
  (`:100`): "a version's worktree, made by mf-cut-change" → "a version's worktree, made by mf-cut-change, or by the run for a
  cut queued with `conduct.py cut`".

## Tests

`git grep -c '^def test_' HEAD -- tests/` totals 221 at the cut. Each new test runs in a scratch repository with the `fake`
fixture's home under `tmp_path`, as the other `tests/test_conduct.py` tests do (`T1`: the conductor's lowest layer with a
fake worker). A stub for `_start_run`, set through `conduct["cut"].__globals__`, writes a live claim — `active/pid` this
process's, `active/start` its `_ps` start — and returns `4242`.

Added, in `tests/test_conduct.py`:

- `test_parallel_cuts_reserve_apart_and_start_one_run` — beside an open `0001-todo` and an archived `0002-old`, two threads
  each call `cut(root, "a" or "b", "minor", "brief=<file>", None, "claude", None, None)` under the stub, which sleeps 0.2 s
  first: the ids are `0003-*` and `0004-*`, the stub ran once, one line says `run started · pid 4242` and the other `the live
  run takes it`; both reservations and both entries stand, the entries holding the parameters and `halt` `null`. Then each
  refusal of [D1](#d1) exits 2 through `main`, reserving nothing: a slug `A b`, no `brief=` prefix, a brief that is no file,
  `after=0009-none`, and, with no run live, a dirty primary naming `the primary's tree is not clean`. A stub raising
  `Stop(2, "the run did not start — x")` makes `cut` exit 2 with `cut: queued <id> · the run did not start — x`, its entry
  left queued.
- `test_a_started_run_is_seen_by_its_claim_or_its_end` — each branch of `_start_run` forced through `__globals__`: `_claim`
  stubbed `live` over a `_detach` stub starting `sleep 5` returns its pid, the child then killed; `_claim` stubbed `none`
  over the real `_detach`, in a fresh primary with no `.minions/runs/` and nothing to ship, returns once `run: done` is in
  `detached.log`, the test having written `~/.mf-ship-origin/source` and a `pending` that cannot resolve, so the child prints
  `pin: cannot move — …` after it; a `_detach` stub starting a child that prints nothing → `Stop` 2,
  `the run did not start — no line in .minions/runs/detached.log`; a dirty primary → `Stop` 2,
  `the run did not start — run: cannot run — the primary's tree is not clean`. `main(["run", "--executor", "claude",
  "--detach"])` prints `run: started · pid <pid>` through `_detach`, the test waiting, at most 30 s, for its `run: done`.
- `test_a_request_at_a_runs_close_starts_the_next_run` — `Run.ship` replaced to write `_request(root, "all")` and return 0:
  the replacement sets `self.seen = set()` first, as the real `ship` does;
  `run` exits 0, the stub ran once with `(root, "claude")`, and the claim is gone; with no request, the stub does not run;
  with `~/.mf-ship-origin` a file, the close removes the claim and starts none; a stub raising `Stop` prints its line; a
  `Run` that raises leaves `seen` `None`, and a standing request starts none. `grant` with none live calls the stub and prints
  `grant: recorded · run started · pid 4242`. Extended in phase 2 with a cut queued during
  `ship` (started, not seen) and one in `seen` (none started).
- `test_a_queued_cut_is_cut_then_built` (`slow`) — a queued `0001-a`: `status` prints `0001-a · cut`; a run spawns
  `cut-change 0001-a`, then `build`, `converge` and `release` of it, and logs `run · cut — 0001-a: cut at`; its reservation
  and entry go. A cut queued while a second run builds a held version is taken at a poll. A queued cut whose branch already
  holds its committed change is built with no `cut-change` call.
- `test_a_cut_halt_is_shown_and_rejoin_cuts_again` (`slow`) — `cut-halts`: the run closes `halt`, logs
  `0001-a · halt — cut-halted — 0001-a waits on one doubt: two readings · tasks.md:3`, spawns no rescue; `status` and
  `report` print the line; a second run takes no thread. `rejoin 0001-a` with none live clears the halt and starts a run
  (the stub); `liar-0001-a` halts on `0001-a: no cut commit at the branch's tip`; a second `rejoin`, the fake set to cut,
  drops the half-done branch, cuts and releases. With a live claim, `rejoin 0001-a` writes the home request. A queue entry
  that is no JSON object prints `cut-halted — the queue entry is unreadable` in `status`. The fake modes `cut-empty`,
  `cut-dirty`, `cut-bare` and `dies-cut` halt on the check's no-change, dirty-tree and no-models lines and on a failed exit,
  and `_check_cut` stubbed to raise sets `conduct.py failed` as the halt. A dependent queued `after=0001-a` waits for its cut,
  and halts `after 0001-a is cut-halted` when it halts. A cut with entry executor `codex` taken at a poll of a `claude` run is
  probed first, `codex` off `PATH` halting it with the probe's reason. A halted cut beside an open version is logged once that
  version's thread has started, and the version releases.

Extended:

- `test_a_worker_carries_the_allowlist_and_a_denial_is_named` (`T2`) — a cut `argv` with `brief=`: Claude's `--add-dir` are
  the worktree and `.minions` alone, `Edit(/<brief>)` is allowed, the settings write the brief; Codex's roots hold the
  brief's folder and no other worktree.
- `test_a_new_executor_is_probed_mid_run`, `test_the_plan_is_read_once` and `test_a_grant_buys_one_round` — the
  requests they plant or read move to `_queue(root) / "rejoin"`; `rescue-answers` writes `.minions/runs/rejoin/<id>` as before, which
  stands unread, and the home request stands in for the person's.
- `tests/fake_worker.py` — the station regex `Run the mf-([a-z-]+) skill`, a `cut-change` station and its modes
  ([tasks](tasks.md) 2.1), and `rescue-answers` writing the home request too.
- `test_a_grant_buys_one_round` — its `run` spy becomes a `_start_run` stub, and its expected `grant` line the new one.

No end-to-end test beyond these (`T1`); none deleted, so no `I16` table.

## Dependencies

None.

## Risks / Trade-offs

- **A cut blocks on the lock while a run closes** → the close holds it only to remove its claim and start the next run, at most
  `CLAIM_SECONDS`.
- **The close starts runs in a chain** → only for a request or a cut it never read; a run whose start halts reads every cut,
  so its close starts none.
- **A worker forges `.minions/cuts/<id>` or `cut.halt`** → a burnt number, or one halted cut: the worker-steering class
  *Out of scope* accepts. The queue entry, with the brief path, stands where no worker writes (C1).
- **The cutter writes the vault's brief** → one file, named by the person's queue entry; a Codex cutter reaches its folder.
- **A cut by hand in the same minute as `conduct.py cut`** → the hand cut counts the reservation at its Step 1; the station
  counts the hand cut's branch once it holds its change. A hand cut between those reads is the race D44 already accepts.
- **`fcntl` is Unix-only** → MF runs on macOS, and Linux is unproven (*Known gaps*).

## Verdict

Ready to build.
