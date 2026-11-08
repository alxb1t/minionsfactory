## ADDED Requirements

### Requirement: A Codex usage limit halts only what runs on Codex

A probe worker or probe checker on Codex that exits on a usage limit SHALL be no refusal: `conduct.py` SHALL log
`run · limited — codex limited until <time>`, SHALL leave Codex unprobed, and the run SHALL go on. The reset SHALL be read, in
order, from Codex's rollout file named by the worker log's `thread.started` `thread_id` — the latest `resets_at` of the
`rate_limits` windows at 100% or more, else of the window most used — then from the failed turn's `try again at <time>` text,
taken as its next occurrence; a reset neither names SHALL hold the limit to the run's end. While the limit holds, each open
version and each queued cut with a station on Codex — any table save conformance's and adversarial's, the fixer and the
cutter included — SHALL halt alone, naming the limit, and SHALL get no rescue; every other version SHALL go on. A version
whose only Codex tables are checkers SHALL go on, its checkers falling back. Past the reset, Codex SHALL be probed again
before its first worker. A converge halt whose line names a usage limit SHALL get no rescue and no supervisor.

#### Scenario: The probe meets the limit
- **WHEN** a run's Codex probe exits on a usage limit, its rollout's 5-hour window at 100% with a reset two hours away, and the
  run holds a Claude-only version, a version whose `[converge.adversarial]` names Codex and a version whose `[build]` names Codex
- **THEN** the run log holds `codex limited until <time>`, the Claude-only version and the checker version are taken and
  released, and the version with the Codex build halts alone, naming the limit

#### Scenario: A reset only the text names
- **WHEN** a limited Codex log names a `thread_id` with no rollout file, and its failed turn says `Try again at 5:50 PM.`
- **THEN** the limit holds until the next 5:50 PM

#### Scenario: A converge halt names a usage limit
- **WHEN** a version's converge halts on a line naming `stopped by a usage limit`
- **THEN** no rescue and no supervisor starts for it, and the version stays halted for the person

### Requirement: A Codex checker falls back to Claude while Codex is limited

Before a mailbox checker on Codex spawns, `conduct.py` SHALL count Codex limited while a recorded limit holds, or while the
newest rollout file's last `rate_limits` shows the primary window at 90% or more with its `resets_at` still ahead. A limit whose
reset is at most 15 minutes away and before converge's deadline SHALL be waited for, then Codex probed if it is unprobed, and
the checker run on Codex; any other limit SHALL run the checker on Claude with converge's model and effort, starting no Codex
worker. A Codex checker that exits on a usage limit SHALL record the limit and go through the same rule once more, ending on
Claude when it does not wait. A fallen-back checker's answer SHALL end its executor, model and effort part with
`· fallback: codex usage limit`, and the converge conductor SHALL copy that into the role's `verdicts` line. A shadow checker
on Codex SHALL not fall back: while Codex is limited it SHALL answer exit 1 naming the limit, start no worker and halt nothing.

#### Scenario: A checker meets the limit
- **WHEN** a mailbox conformance checker on Codex exits on a usage limit whose reset is two hours away
- **THEN** `conduct.py` runs it again on Claude with converge's model and effort, its answer names
  `executor claude` and `fallback: codex usage limit`, and the version does not halt

#### Scenario: The window is nearly spent
- **WHEN** the newest rollout shows the primary window at 92% with its reset two hours away, and a Codex checker is requested
- **THEN** the checker runs on Claude, and no Codex worker starts
- **AND WHEN** that reset is ten minutes away
- **THEN** `conduct.py` waits for it, then runs the checker on Codex

#### Scenario: A shadow while Codex is limited
- **WHEN** a shadow checker on Codex is requested while Codex is limited
- **THEN** it answers exit 1 naming the limit, no worker starts, and converge goes on

### Requirement: A Codex spawn records its share of the plan's windows

Each Codex worker's log SHALL end, once the worker exits, with one `mf.quota` line `conduct.py` appends, following no link:
the share of the 5-hour and the weekly window the spawn used, in percent, read from the newest rollout file before the spawn
and the spawn's own rollout after it, a window whose reset moved counting its whole use after. A spawn with no rollout SHALL
get no line. A mailbox checker's findings file SHALL have its `model:` stamped with the model it ran on and a `tokens:` key
with its log's tokens, written by `conduct.py` following no link. `run.py` SHALL sum a version's Codex shares as
`codex-window-5h` and `codex-window-week`, a gap when no Codex spawn of the version holds the line, and SHALL count a Codex log
with no `turn.completed` as no tokens and no dollars. `skills/mf-review-metrics/prices.toml` SHALL hold rows for
`claude-opus-5-5` and `claude-sonnet-5-5`, and a Claude converge worker SHALL be priced from them.

#### Scenario: A Codex checker's spawn
- **WHEN** a mailbox checker on Codex runs, the primary window at 40% before it and 43% after, the weekly at 10% and 11%
- **THEN** its log ends with an `mf.quota` line naming 3 and 1, its findings file names the plan's model and the log's tokens,
  and `codex-window-5h` reads 3 at the release

#### Scenario: A Claude worker priced
- **WHEN** a converge subagent on `claude-sonnet-5-5` reads one million input tokens and writes one million output tokens
- **THEN** the review metrics price it at 12 dollars from `prices.toml`

## MODIFIED Requirements

### Requirement: The ship station judges every station from disk

`skills/mf-ship/scripts/conduct.py` SHALL decide each version's stage from git and the run directory alone, and SHALL
pass a station only when the worker exits 0 and its check on disk passes — never on the worker's report. The converge
check SHALL need `done` as the newest run's latest status-log event. Before the
first station it SHALL run a probe worker that must edit, commit and run `make gate` in a scratch repo, or halt, save a usage
limit, which halts only what runs on its executor. The scratch
gate's recipe SHALL try a write to a file `conduct.py` made outside the worker's reach, and SHALL pass only when that write is
refused; `conduct.py` SHALL halt the run when the file changed, and SHALL remove it. The recipe SHALL also pass only
when the shell's `uname -m` is the host's native architecture, so a worker whose shell runs translated halts the run, naming
its executor. A Codex probe worker SHALL also run `git write-tree` in a linked worktree of its scratch repo, and SHALL pass only
when it wrote the tree that command prints there. A Codex probe that passes SHALL then run one conformance checker over a
fixture change in a second scratch
repo, and SHALL pass only when the checker leaves `.minions/changes/0001-probe/conformance.md`, a file and no link, whose
frontmatter holds every key of the findings file contract, `type: conformance` and `plan: 0001-probe`, and when its log holds
a usage event; the checker's verdict SHALL be logged and never judged.
It SHALL log every worker's start, end and check to `.minions/runs/<stamp>.md`, and `conduct.py log --verify` SHALL
fail on a worker with no end, a run that ends on neither `halt` nor `done`, or an unknown event.

#### Scenario: A worker reports success that disk does not show
- **WHEN** a build worker exits 0 and a `## Progress` box is still unticked
- **THEN** the build check fails and the version halts

#### Scenario: A run's log is complete
- **WHEN** a run ends
- **THEN** `conduct.py log --verify` exits 0 on its log

#### Scenario: A worker dies after clean findings
- **WHEN** a converge worker exits 1 with both findings files clean at `HEAD` and no `done` in its status log
- **THEN** the version halts, naming the exit, and nothing is released

#### Scenario: A probe worker runs unsandboxed
- **WHEN** the probe worker's write outside its reach lands
- **THEN** the run halts naming the probe's executor, no version starts a worker, and the file is gone

#### Scenario: A worker's shell runs translated
- **WHEN** the probe worker's shell reports `x86_64` on an `arm64` host
- **THEN** the run halts, naming the executor and both architectures, and no version starts a worker

#### Scenario: A Codex checker probe writes no findings file
- **WHEN** a Codex probe passes its scratch edit, and its checker exits 0 leaving no `conformance.md`
- **THEN** the probe fails, naming the missing file, and no station runs on Codex
- **AND WHEN** the checker leaves a findings file with every contract key and `verdict: clean` over the fixture's defect
- **THEN** the probe passes, and its check line names the verdict

#### Scenario: A Codex probe cannot write a linked worktree's index
- **WHEN** a Codex probe worker edits, commits and gates its scratch repo, and leaves no tree written in the linked worktree
- **THEN** the probe fails, naming `git write-tree`, and no station runs on Codex

### Requirement: A halt stops only its version, and a re-run resumes

A failed check SHALL halt its version alone: that version SHALL start no new worker but its rescue and, under its switch, its
supervisor, and every other version SHALL go on
to its release. A version whose `after:` names a halted or blocked version SHALL be blocked, starting no worker. A failed
probe, save one a usage limit stopped, and a conductor crash SHALL stop the run. A run with every open version at a halt stage
or `waiting` SHALL start
no worker, the probe included. A `**HUMAN` phase, a dependency waiting for approval,
converge's cap, an open integrate merge, a red gate, a release stopped before its merge, and a worker past its timeout
SHALL each halt their version.

Each halt SHALL be logged when it happens, and each block as `blocked — by <id>`. A run with a halt or a block SHALL
close on `run · halt — halted <ids> · blocked <ids> · released <tags>` and exit 1. `conduct.py report` SHALL print every
`halt` line, then the closing line, and SHALL end a blocked version's line with `blocked by <id>`. The run SHALL keep no state
outside git and the run directory, except the claim, `origin`'s URLs, the offline base, the release ledger and a person's gate approval
in the home folder: a re-run derives every stage again and continues. A halt SHALL need
the person only at a stage in `HALTS`, a `**HUMAN` phase, a merge with a note, a converge that halted on anything but
`.minions/debt.lock`, or an older `.minions/backlog.lock`, a release whose
base moved, a release stopped on purpose or refused, a repo git config key or local `origin` the run refuses, a git config that
changed during the run, an `origin` that left the kept URLs, an `origin` it cannot read with no offline base, an old
`.minions/backlog.md` beside `.minions/debt.md` or a file at `.minions/backlog.lock` or `.minions/debt.lock`, or one that is a
link, or a default-branch commit no ledger entry stands behind. A worker stopped by a usage limit SHALL be halted with its reset
time named, save a mailbox checker, which falls back.

#### Scenario: A HUMAN phase halts its version
- **WHEN** a version's first unticked phase is marked `**HUMAN`
- **THEN** that version halts, naming the phase, and every other version goes on

#### Scenario: A later version halts, and the earlier ships
- **WHEN** two versions run and the later one's build check fails
- **THEN** the earlier is released, merged and pushed
- **AND** the run closes naming the later as halted and the earlier's tag as released, and exits 1

#### Scenario: A later version ships past a halted one
- **WHEN** two versions run and the earlier one's build check fails
- **THEN** the later is released, merged and pushed
- **AND** the run closes naming the earlier as halted and the later's tag as released, and exits 1

#### Scenario: A halted dependency blocks a chain
- **WHEN** a version halts, a second has it in `after:`, and a third has the second in `after:`
- **THEN** neither starts a worker, each logs `blocked — by <id>`, and the closing line names both as blocked

#### Scenario: No open version can start
- **WHEN** one version sits at a `**HUMAN` phase, and every other is `waiting`
- **THEN** the run starts no worker, and closes naming the first as halted and the others as blocked

#### Scenario: A failed probe stops the run
- **WHEN** the probe's check fails
- **THEN** no version starts a worker, and the run closes naming `run` as halted

#### Scenario: The person re-runs after a halt
- **WHEN** the person handles the halt and runs `mf-ship` again
- **THEN** each version continues from its stage on disk, and the finished stations do not run again

#### Scenario: The person resolves a semantic conflict
- **WHEN** integrate halted on a semantic conflict, with the merge open and its note under `.minions/changes/<change-id>/`,
  and the run takes no supervisor settle — no switch, or a supervisor was spawned on that open merge before
- **THEN** a re-run of `mf-ship` halts again and integrates nothing, whatever the person staged
- **AND WHEN** the person settles it and `/mf-integrate <change-id>` commits the merge
- **THEN** a re-run of `mf-ship` runs the catch-up round, then the release

#### Scenario: The person fixes a red gate
- **WHEN** integrate halted on a red gate, with the merge committed and `.minions/changes/<change-id>/integrate.red` naming it
- **THEN** a re-run of `mf-ship` halts again and integrates nothing
- **AND WHEN** the person commits a fix past the merge
- **THEN** a re-run of `mf-ship` integrates again, gating the fix, then runs the catch-up round and the release

#### Scenario: Grant takes only the cap
- **WHEN** a person runs `/mf-ship grant <change-id>` on a version halted on anything but converge's cap
- **THEN** it exits 2, and records nothing

### Requirement: A station's executor comes from the models file

`.minions/changes/<change-id>/models.toml` MAY name `executor = "claude"` or `"codex"` in any station's table; absent, the station
runs on the run's executor. Integrate SHALL use the `[release]` table. `conduct.py` SHALL halt a version, before its
worker starts, on an `executor` it does not know and on a `codex` station with a `claude-*` model. It SHALL run one probe
worker per distinct executor named across the open versions and the run's own — each station's, each checker table's, and
each shadow checker's under `shadow = true`; a failed probe at the start SHALL stop the run, and one for a joining version
SHALL halt only the versions on its executor; a probe a usage limit stopped SHALL halt only the versions with a station on its
executor.
A station on Codex SHALL report each denial, its usage limit with the reset time, its tokens and its priced cost from its JSON
event log, as a station on Claude does from its own; converge's per-role tokens SHALL read `unavailable` on Codex, save a
checker the mailbox started, whose own log holds them.

#### Scenario: Converge on Codex beside a build on Claude
- **WHEN** a version's models file names `executor = "codex"` under `[converge]`
- **THEN** its converge runs as `codex exec`, and its build and release as `claude -p`
- **AND** the run probes both executors before any station

#### Scenario: A checker's executor is probed
- **WHEN** a run's only Codex table is a version's `[converge.adversarial]`
- **THEN** the run probes Codex before any station

#### Scenario: A model the executor cannot run
- **WHEN** a table names `executor = "codex"` and `model = "claude-opus-5-5"`
- **THEN** that version halts naming the table, and no worker starts for it

#### Scenario: A Codex worker is refused a command
- **WHEN** a Codex worker's command fails with the sandbox's `Operation not permitted`
- **THEN** the run log holds a `denied` line naming the command, and the report lists it

#### Scenario: A Codex worker meets its usage limit
- **WHEN** a Codex station's worker exits 1 after a failed turn whose error names its usage limit and a time to try again
- **THEN** its version halts with `stopped by a usage limit · resets <time>`
- **AND WHEN** the worker is a mailbox checker
- **THEN** it runs again on Claude, and its version does not halt

### Requirement: A worker's reach stops at the repository

A Codex worker's writable roots and a Claude worker's `Edit` and `--add-dir` SHALL be the primary and each open worktree,
from `git worktree list`, and never the directory holding them. A Codex worker's writable roots SHALL also hold the common
directory and each folder directly under its `worktrees/`, a link left out, so a linked worktree's index, `HEAD` and logs are
written as the primary's are. An open worktree SHALL be the worktree of an open version —
a branch named by a change id, the default branch lacks, holding its change — or of a cut queued in the home folder's
queue; any other listed worktree SHALL be no reach. A listed worktree whose `.git` file does not point back to
an entry under the common directory SHALL be no worktree. `conduct.py` SHALL take the primary and its common directory once,
before the first worker, and SHALL never take a worker's reach from git's answer in a worktree. It SHALL refuse a run in a
checkout whose `.git` names another repository, and SHALL halt a Codex worker when the primary's `.git` no longer resolves to
that common directory. Directly before each Codex worker starts, `conduct.py` SHALL halt its version when any writable root
or its working directory is a link or no longer resolves to itself, naming the path. `conduct.py` SHALL load `integrate.py`
once, before the first worker, and SHALL halt a version's merge when the local git config or `info/attributes` changed since
then. The refusal of a git config key that could name a program SHALL read each linked worktree's `config.worktree` too.

#### Scenario: A sibling project
- **WHEN** a worker runs in a repository whose parent holds other projects
- **THEN** no writable root and no `--add-dir` names that parent

#### Scenario: A released version's worktree
- **WHEN** a version's branch is merged into the default branch and its worktree is kept
- **THEN** no writable root and no `--add-dir` of a later worker names that worktree
- **AND WHEN** a cut is queued and its worktree made
- **THEN** a later worker's `--add-dir` names it

#### Scenario: A worker forges a worktree entry
- **WHEN** a worker adds an entry under the common directory's `worktrees/` naming a directory outside the repository
- **THEN** no writable root and no `--add-dir` names that directory, and no version runs in it

#### Scenario: A worker repoints a worktree
- **WHEN** a worker rewrites a worktree's `.git` file or its entry's `commondir` to name another repository
- **THEN** no writable root and no `--add-dir` of the next worker names that repository

#### Scenario: A worker plants git config
- **WHEN** a worker changes the common directory's config during a run
- **THEN** the conductor merges nothing for a dependent, and that version halts, naming the change
- **AND WHEN** a worker writes `core.fsmonitor` into a linked worktree's `config.worktree`
- **THEN** the refusal halts as it does for the common config, naming the key

#### Scenario: A worker swaps a writable root for a link
- **WHEN** a worker moves a listed worktree aside and puts a link to a sibling project in its place, and the next station of
  a version runs on Codex
- **THEN** that version halts naming the link, and no Codex worker starts with the sibling among its writable roots

#### Scenario: A Codex worker in a linked worktree
- **WHEN** a Codex worker runs in an open version's linked worktree
- **THEN** its writable roots name that worktree's folder under the common directory's `worktrees/`

### Requirement: A halted version rejoins a live run

`conduct.py rejoin [<change-id>]` SHALL write a request in the repository's queue in the home folder, where no worker writes,
under the queue lock, and `/mf-ship` SHALL send it when a run is live. The live run SHALL check that folder at most every 10
seconds and before its close, and SHALL take into the run every
open version the request names — every one for a request with no id — whose stage on disk is no longer a halt: a halted one,
a blocked one, and one cut after the run started. A version still at a halt SHALL stay out, logged with why. The poll SHALL
not end the run's loop while a version's thread runs: an entry it cannot delete SHALL be no request, and a version it fails
to take SHALL halt alone. A request folder that is a link SHALL hold no request, and the poll SHALL delete nothing through
it. A version the run's plan already holds SHALL stay out, logged, while its models file differs from what the run read, and
a version whose rescue answered its converge or integrate halt on disk SHALL stay out, logged, for the rest of the run, both
waiting for a re-run. Anything that answers that halt on disk while its rescue runs, or before the run reads the rescue's
outcome, SHALL count as the rescue's answer: the person's own commit past the halted head, settled merge or removed note, and
a grant landing after the rescue's `finish`, included. The person's `docs(<id>): amend the change directory` commits that
answer a halt by amends alone SHALL not: that version goes on in its run. Any other taken version
SHALL have its models file read as it joins, then go through the run's base check, its dependencies, its stations and the
merge lock, as at a run's start, with its halts and blocks cleared. Its executor's probe SHALL run once in the run, before
the first worker on it; a failed probe SHALL halt only the versions on that executor, each later one with that probe's
reason and no second probe. A probe a usage limit stopped, or a limit still holding, SHALL halt only the versions with a
station on that executor, naming the limit. The run SHALL log a `rejoin` event per
version taken, delete the requests it read, and a run's start SHALL delete every request it finds. A run-level halt SHALL
end the run, as before. A request that lands after a run's last poll and before it removes its claim SHALL start the next
run, which deletes it at its start and takes every open version.

#### Scenario: A fixed version rejoins
- **WHEN** a version halts while another builds, the person fixes it on disk once any rescue of it has ended, and runs
  `/mf-ship`
- **THEN** the live run logs `rejoin` for it, and it releases in the same run, the other version's stations untouched

#### Scenario: A version still halted
- **WHEN** a request names a version whose stage is still a halt
- **THEN** it stays out, and the run logs why

#### Scenario: A version its rescue answered
- **WHEN** a version's rescue answered its converge or integrate halt on disk, and a request names it
- **THEN** it stays out for the rest of the run, and the run logs it still halted, naming the answer
- **AND WHEN** the person's own commit, settled merge or removed note answered that halt while the rescue ran
- **THEN** it counts as the rescue's answer: the version stays out, logged the same, and a re-run goes on from it

- **AND WHEN** only the person's amends answered an `amend needed` halt while its rescue ran
- **THEN** the version goes on in the run, with no request

#### Scenario: A version cut during the run
- **WHEN** a version is cut while a run is live, and `/mf-ship` runs
- **THEN** the live run takes it, and builds it beside the others
- **AND WHEN** a folder stands in the queue's request folder beside the request
- **THEN** the poll skips it, and the run goes on
- **AND WHEN** the request folder is a link to another folder
- **THEN** the poll reads no request there, and deletes nothing in it

#### Scenario: A worker writes a request
- **WHEN** a worker writes a file in `.minions/runs/rejoin/`
- **THEN** no run reads it as a request

#### Scenario: A new executor
- **WHEN** a taken version's models file names an executor the run has not probed
- **THEN** the run probes it before that version's first worker, and the version goes on
- **AND WHEN** that probe fails
- **THEN** only the versions on that executor halt, the probe run once for them all, and the others release

#### Scenario: A joining version while Codex is limited
- **WHEN** a taken version's `[build]` names Codex while a Codex limit holds, and another's only Codex table is a checker
- **THEN** the first halts naming the limit, with no probe, and the second goes on

#### Scenario: A request at the close
- **WHEN** a request lands after the last version's thread ends
- **THEN** the run reads it before its close
- **AND WHEN** a request lands after the run's last poll and before it removes its claim
- **THEN** the run's close starts the next run, whose start deletes it and takes every open version

### Requirement: A converge checker on another host runs through the mailbox

When a version's conformance or adversarial table names an executor other than converge's, or `[converge] shadow = true`,
`conduct.py` SHALL give that version's converge worker one **checker mailbox**, `~/.mf-ship-origin/<digest>.queue/checkers/<change-id>/`,
made a folder and emptied before the worker starts, among its writable paths, and no other worker's; a mailbox that is a link
SHALL halt the version. The converge conductor SHALL send such a checker by writing its prompt to
`.minions/changes/<change-id>/<role>.prompt.md` and running `conduct.py checker <change-id> <role>` in the foreground, which
removes any `<role>.answer`, copies the prompt into the mailbox as `<role>.request` under a first line `request <id>`, 16 hex
digits of its own, and waits for `<role>.answer`, exiting with its exit code, or exiting 3
after `CHECKER_WAIT` seconds, so a re-run with `--wait` waits on. An answer that names no request, or another than the one
sent, SHALL be refused: removed, and waited past. While that converge worker runs, `conduct.py` SHALL take each
request of a role of `conformance`, `adversarial`, `shadow-conformance` and `shadow-adversarial`, read through one descriptor
following no link and refused past `REQUEST_BYTES` or with no `request <id>` line; spawn its checker as `converge-<role>`,
logged as any station, with the executor, model and effort its plan holds, never the request's, and with no more time than
converge's own spawn has left; and answer
`exit <n> · executor <x> · model <m> · effort <e>`, then ` · tokens <n>` when its log holds them, then ` · request <id>`. It
SHALL refuse a request past `CHECKER_SPAWNS` in one converge spawn, or once converge's time is spent, answering exit 1. A
checker's exit SHALL never halt the version itself. Each findings file SHALL name its checker's `executor:` in its
frontmatter. The fixer SHALL run on converge's host.

#### Scenario: A Codex checker under a Claude conductor
- **WHEN** a version's `[converge]` runs on Claude and `[converge.conformance]` names `executor = "codex"`, `model =
  "gpt-6.1-sol"` and `effort = "high"`
- **THEN** its converge prompt holds `and conformance=mailbox`, the converge worker's sandbox may write its mailbox, and its
  request makes `conduct.py` spawn `codex exec` with `-m gpt-6.1-sol` and `-c model_reasoning_effort=high`
- **AND** the conductor reads `conformance.md` from disk, its frontmatter naming `executor: codex`, and the fixer runs on Claude

#### Scenario: A forged request
- **WHEN** a request names a role outside the four, is a link, holds more than `REQUEST_BYTES` or no `request <id>` line, or a
  ninth request comes in one converge spawn
- **THEN** no checker starts for it, and a link's, a long request's, an unnamed request's and a ninth request's answer reads
  exit 1

#### Scenario: A checker outlasts the wait
- **WHEN** a checker runs past `CHECKER_WAIT` seconds
- **THEN** `conduct.py checker` exits 3, and `conduct.py checker <change-id> <role> --wait` prints the answer once it lands

#### Scenario: A leftover answer
- **WHEN** an earlier request's answer still stands in the mailbox and the conductor sends a new request for that role
- **THEN** `conduct.py checker` reads no answer but the one naming its new request

#### Scenario: A checker late in converge's time
- **WHEN** a request comes with ten minutes left of converge's spawn
- **THEN** its checker is killed past those ten minutes, and a request after them is refused with exit 1
