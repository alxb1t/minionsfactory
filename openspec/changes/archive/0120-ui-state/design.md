# ui · state — design

A read-only server projects each project's ship line into one state tree and streams it to a plain page. Verdict: ready to
build, in the phases of [tasks](tasks.md).

## Context

`conduct.py status` prints `<id> · <stage>` with no why, no worker, no converge round and nothing of the other repos. Every
fact a person wants is on disk: the stage readers of `conduct.py`, the run log, the claim, each change's folder and the
home queue. The readers write nothing, run no network git call and need no package, so a viewer can call them by path.

A reader can raise `Stop` on a version with no worktree or no `## Progress` list, and can block on a pipe planted where a
file is read, so each project is read in a child process the server can kill. A pinned install exports `skills/` alone, so
the viewer lives in a skill; no worker may bind loopback, so no test opens a socket.

The series decisions (series Q1…Q56) and the board's (board Q1…Q21) are inputs; this design settles what they leave open.
The Vue board that replaces the plain page, `ui · prepare` and the designed panes are later versions.

## Goals / Non-Goals

- **Goals:** one state tree for every project; stage and its why per version; phases, converge, workers and liveness;
  what needs the person; the queue; a stream of whole numbered states; a page that shows it as text.
- **Non-Goals:** [the proposal's list](proposal.md#not-in-this-change). Also: control of a run, history, the impact page, a
  login, a port other than loopback.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | One stdlib script, `skills/mf-ui/scripts/viewer.py`, runs the commands `project`, `serve`, `start` and `stop`, and loads `conduct.py` and `converge.py` by path | a pinned install exports `skills/` alone (series Q1, board Q18 amended); viewer and line stay one release | a root `ui/` · a copy of the readers · an import as a package |
| [D2](#d2) | A project is read by `viewer.py project <primary>` in a child process the server kills past 10 s | the readers raise and can block on a pipe; a child can be killed, a thread cannot | a thread · a signal alarm · no bound |
| [D3](#d3) | The state tree has the shape below, one whole value per frame | a page that renders whole states has no merge to get wrong | a diff protocol · a page that reads files |
| [D4](#d4) | A version's state is the first matching rule of a fixed table, and **for you** is a fixed list of rows | no file records a state, so the rules make it reproducible | a state stored by the run · a state the page computes |
| [D5](#d5) | Converge, workers and liveness are read from the status log, the findings files' frontmatter, the newest run log and mtimes | each is written to a contract; none needs a station change | a pid on the spawn line (`ui · worker`) |
| [D6](#d6) | The projects are the recorded repos with a `.minions/` folder, named, ordered and hidden by an optional `ui.toml` | a new project appears with no chore; review metrics reads the same record | a required config · a list kept in the repo |
| [D7](#d7) | The server polls every 2 s, serves `/`, `/events` and `/state`, refuses a foreign `Host` and numbers each changed whole state | with no login, the `Host` check stops another site's page reading the stream by DNS rebinding | a wildcard bind · a CORS header · a websocket |
| [D8](#d8) | `start` runs the server detached and prints its URL, a second `start` finds it, `stop` ends it; its pid, port and log are files in its own state folder | stop needs the pid, and no launchd (D22) | launchd · a file in a repo |
| [D9](#d9) | The page is one HTML file with an inline script and style, no build, every string set as text | the Vue board replaces it; worker-written text must never become markup | a framework · `innerHTML` |
| [D10](#d10) | D82 records the viewer as an operator tool; the principle, the threat model, the README, `AGENTS.md` and the docs map name it | the viewer reads what the sandbox keeps workers from | an exemption in prose alone |
| [D11](#d11) | A corpus case `viewer` runs the projector over this checkout's run directory | `make corpus` holds each reader of run data against real files | a fixture-only proof |

### D1

`skills/mf-ui/` holds `SKILL.md`, `scripts/viewer.py` and `page/index.html`. `viewer.py` is a `uv` script,
`requires-python = ">=3.12"` and `dependencies = []`: standard library alone.

It finds the packages beside it, `Path(__file__).resolve().parents[2]`, as `conduct.py` finds `converge.py`:
`mf-ship/scripts/conduct.py` and `mf-converge/scripts/converge.py`. `load(path)` is `runpy.run_path(str(path))`, which runs
definitions only, since `conduct.py` has its `__main__` guard and `converge.py` has none. So the viewer follows the
machine's pin: the installed viewer reads the installed `conduct.py`, and a checkout's viewer reads the checkout's.

| command | does |
|---|---|
| `project <primary> [--only liveness\|fingerprint]` | prints one project's tree, or its liveness, or its fingerprint, as JSON; exit 0 |
| `serve` | the server, in the foreground; what `start` detaches |
| `start` | starts `serve` detached, or finds it; prints the URL |
| `stop` | ends the server `start` started |

No argument, or another command, prints a usage line and exits 2.

### D2

The server runs `[sys.executable, <viewer.py>, "project", <primary>]` in its own session, with the environment plus
`GIT_OPTIONAL_LOCKS=0`, so a `git status` the readers run takes no optional lock. It waits at most `BOUND = 10` s. Past
that it kills the child's process group and shows the project `unread` with the reason `read past 10 s`.

A child that exits non-zero, or prints no JSON object, shows the project unread with the first line of its stderr. The
child calls `primary_of(<primary>)` first, which refuses a repo whose git names a folder outside it; a `Stop` there is the
project's unread reason. A version whose projection raises any `Exception` — `stage_of`'s `Stop` included — is
`unread` alone, with the error text, and its project's other versions are read.

The projector reads each file through `read_part(path, tail=False)`: a regular file, opened `O_NOFOLLOW | O_NONBLOCK`,
its first or last `PART = 262144` bytes, `None` for anything else. The readers of `conduct.py` keep their own reads; a pipe
there is what the kill is for.

### D3

One frame is `{"seq": <n>, "projects": [<project>, …]}`. The shape, every key always present, an absent value `null`:

```
project   name · unread · run · for_you[] · versions[] · queue[]
run       claim (none|live|stale|unread) · log (a stamp) · last (the newest event line)
version   id · state · stage · why · unread · phases[] · converge · workers[] · liveness · notes[]
phase     number · title · rating · box · done · total
converge  run · mark · round · cap · fixing · roles { conformance, adversarial }
role      verdict · open_blocking · executor · model · effort · tokens · fallback
worker    station · model · effort · executor · started
liveness  level (active|recent|quiet) · last
note      text
row       kind · id · why
cut       id · state (cut|cut halted) · halt
```

`unread` is `null` or the reason. `name` is the `ui.toml` name, else the primary's folder name; no path is in a frame.
`started` and `last` are epoch seconds, so the page counts elapsed time itself and a frame changes only when a fact does.

### D4

`stage_of(primary, version)` gives `(stage, why)`. The state is the first row that holds:

| row | state | holds when |
|---|---|---|
| 1 | `unread` | a read of the version raised |
| 2 | `needs you` | the stage is `human`, `integrating` or `released` |
| 3 | `halted` | the stage is `converge-halted`; or the stage is `build` and `_build_halt` names `HEAD`; or a halt stands in the newest run log |
| 4 | `blocked` | the stage is `waiting`, and a version its `why` (`after <id> …`) names is `halted` or `needs you` |
| 5 | `waiting` | the stage is `waiting` |
| 6 | `stacked` | the stage is `stacked` |
| 7 | `running` | a station stage, the claim `live`, and an unfinished spawn of the version |
| 8 | `idle` | a station stage otherwise |

A **station stage** is one of `build`, `converge`, `integrate` and `release`. A **halt stands in the newest run log** when
the version's last line there is a `halt — …` line with `<id>` as its who: a worker's exit (`halt — build worker exit 1`), a
check's failure or a rescue's diagnosis alike. The version's lines are those with `<id>` as their who and the run's
`run · rejoin — <id>: …` lines but a refused `still …` or `skipped …` one; any later line of the version, a `spawn` or a
taken `rejoin`, ends the halt. The state's `why` stays the stage's. A halt in an older run log is not shown: a newer log with
no line of the version ends it, as the workers of [D5](#d5) end with their log, and what carries a halt across runs is the
stage, `converge-halted` or a `build.halt` that names `HEAD`. A version the home queue holds as a queued cut is no version: it
is a `cut` row of the queue, as `status` prints it.

**For you** holds these rows, in this order of kind and by id within one, each with its `why`:

| kind | row | `why` |
|---|---|---|
| `needs you` | each version in that state | the stage's why |
| `halted` | each version in that state | the stage's why |
| `cut halted` | each queued cut with a `halt` | the halt |
| `stale run` | the claim is `stale` | `a run clears it, or stops naming why` |
| `usage limit` | the newest run log's last `run · limited — <executor> limited until <time>` while `<time>` is ahead of now, or names no time | that line's detail |
| `unpushed` | the default branch is ahead of `refs/remotes/origin/<default>` by `git rev-list --count`, no network | `<default> is ahead of origin` |

A rescue's or a supervisor's decision — a `run · rescue — <id>: decided|fixed · …` or `run · supervise — <id>: …` line of the
newest run log — is a `note` on its version, shown dim, and no row.

### D5

**Converge** is `null` when the change's folder has no `status_log.md`. Else:

- `cap` is `CAP` of `converge.py`.
- `run` and `mark` are the number and the mark of the newest `## Run <n> — <date> <time>[ · amend|catch-up|grant]` heading.
- `fixing` is true while the status log's top line after that heading holds `fix — sent`.
- Each role's `verdict` and `open_blocking` are the frontmatter of its findings file, `conformance.md` or `adversarial.md`;
  `round` is the larger of the roles' `round`.
- Its `executor`, `model`, `effort`, `tokens` and `fallback` come from the newest `verdicts — <role> …` line of the status
  log, `fallback` true when the line holds `FALLBACK` of `converge.py`. A field the files lack is `null`.

**Workers** are the spawns of the version in the newest run log, `.minions/runs/<stamp>.md`, that no later `finish` pairs.

- A spawn line is `<HH:MM:SS> · <id> · spawn — <station>`, then parts joined by ` · `: `model <m>`, `effort <e>` and
  `executor <x>`, each read when present and `null` when not; any other part is ignored. The conductor's own converge spawn,
  `spawn — converge · script`, is a worker with station `converge` and every other field `null`.
- A spawn is paired by station with the next `<id> · finish — <station> · …` line; a `finish` with no spawn pairs nothing.
- `started` is the stamp's date at the line's time, a day later each time a line's time is earlier than the line before it.
- Rescue, supervise and converge's checkers and fixer are workers by their spawns.

**Liveness** is read for a version with a worker. `last` is the newest of: the last `timestamp` of the worker's log, the log's
mtime, and the newest mtime under the version's worktree and its change folder, a walk that follows no link and skips `.git`.
The worker's log is the newest `.minions/changes/<id>/logs/<stamp>-<station>*.log` of the run's stamp. The `level` is `active`
under 60 s, `quiet` from 300 s, else `recent`.

**Phases** are `_progress`'s lines at `HEAD`. `box` is the `HEAD` tick, `rating` is `_rating` of the raw title, and `title` is
that title without its ` · hard` or ` · moderate` suffix. `done` and `total` count the lines `- [ ] N.M …` and `- [x] N.M …`
of the worktree's `tasks.md` whose number `N` is the phase's, `null` when the file cannot be read.

**The run** is the claim (`_claim`), the newest run log's stamp (`last_log`) and its last event line, `null` with none.
The claim is read once per project. A `Stop` from it, as when `ps` cannot read a running conductor's pid, makes it
`unread`, a value and no failure: no version is `running`, no `stale run` row shows, and the rest of the project is read.

### D6

The projects are the lines of `~/.mf-ship-origin/repos`, each kept when `<path>/.minions` is a folder. `ui.toml`, found in
`$XDG_CONFIG_HOME/minionsfactory/`, else `~/.config/minionsfactory/`, is optional: `port` (an integer, default `8737`) and
`[[container]]` rows with `path`, `name` and `hide`. A row's `path` adds its project when it holds `.minions/`; `hide = true`
drops it; `name` names it. The rows' order comes first, the record's order after, each path once, resolved.

A missing file halts nothing. A file that is no TOML, a `port` that is not an integer from 1 to 65535, or a row with no
string `path` exits 2 naming the file. An empty list of projects is a frame with no projects.

### D7

A tick runs every `POLL = 2` s, over the projects in parallel, so one slow project stalls no other. For each project:

- it runs `project --only fingerprint`;
- a changed fingerprint, or `REREAD = 10` s since the project's last full read, runs the full read;
- else `LIVENESS = 5` s since its last liveness runs `--only liveness` and merges it.

The fingerprint is a hash of the `(path, mtime, size)` of the newest run log, `.minions/runs/active`, each change folder's
entries, the refs under `.git`, each worktree's `tasks.md` and the home queue's `cuts/`: stat calls only.

`State.publish(projects)` takes the tick's projects and raises `seq` by 1 when their JSON differs from the last, else
nothing; it returns whether it did. `State.latest()` returns `(seq, projects)`, and `State.wait(after, timeout)` blocks until
`seq` is above `after` or the timeout passes, and returns whether it is. `frame(seq, projects)` is
`id: <seq>\nevent: state\ndata: <JSON>\n\n`, the JSON compact and one line.

Time and waiting are arguments, so a test sleeps nowhere. `tick(now, entries, memory, read)` takes the clock's seconds, the
`Entry(path, name)` list of [D6](#d6), the dict `memory` the caller keeps (`memory[path]` is a list of the last fingerprint, full
read time, liveness time and project), and `read(path, only)`, which returns a child's JSON object; it returns the projects in
order. `stream(state, keepalive=KEEPALIVE)` is the `/events` generator: it yields each frame and, when `State.wait` times out,
the comment `: keep-alive\n\n`.

`route(path, host, port, state)` returns a status, headers and a body, and touches no socket:

| request | answer |
|---|---|
| `Host` not `127.0.0.1:<port>` or `localhost:<port>`, or no `Host` | 403, on every path |
| `/` | 200 `text/html`, `page/index.html` |
| `/state` | 200 `application/json`, `{"seq", "projects"}` of the newest frame |
| `/events` | 200 `text/event-stream`, a generator: the newest frame at once, each newer one when `seq` rises, a `: keep-alive` comment every 15 s |
| any other path | 404 |

The query is dropped before the match. Every answer carries `Cache-Control: no-store`, `X-Content-Type-Options: nosniff` and
`Referrer-Policy: no-referrer`; `/` also carries `Content-Security-Policy: default-src 'none'; script-src 'unsafe-inline';
style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'`.

The server binds `127.0.0.1` and no other address. The lines that bind, accept and write a response are `serve` and the
handler's `do_GET`, each marked `# pragma: no cover`.

### D8

The state folder is `$XDG_STATE_HOME/minionsfactory/`, else `~/.local/state/minionsfactory/`, made mode `0o700`. It holds
`viewer.pid`, `viewer.port` and `viewer.log`, each mode `0o600`: the only files the viewer writes.

`start` reads the config first (a bad one exits 2), then the pid file:

- A pid that `serves(pid)` — `ps -o command= -p <pid>` names `viewer.py` and `serve` — is a running server. `start` prints
  `http://127.0.0.1:<port>/` from the port file and exits 0.
- Else it starts `[sys.executable, <viewer.py>, "serve"]` in a new session, output to the log, writes the pid and port
  files, waits `START_WAIT = 2` s for it to stay alive, and prints the URL.
- A server that exits in that time has its files removed; `start` prints `viewer: the server exited — see <log>` and exits 1.

`stop` signals a pid with `SIGTERM` only while `serves(pid)` holds and the pid is above 1, then removes the files and prints
`viewer: stopped`. Any other pid file is stale: `stop` removes the files, signals nothing and prints `viewer: not running`.
`start(folder, config, spawn, ps, wait=START_WAIT)` and `stop(folder, ps, kill)` take their spawn, `ps`, signal and wait as
arguments, so a test starts nothing and sleeps nowhere.

### D9

`page/index.html` is one file: an inline `<style>` and `<script>`, no framework and no build, one column. The tokens are CSS
variables, the Catppuccin Macchiato palette:

| token | value | token | value |
|---|---|---|---|
| `--base` | `#24273a` | `--text` | `#cad3f5` |
| `--mantle` | `#1e2030` | `--subtext` | `#a5adcb` |
| `--surface` | `#363a4f` | `--overlay` | `#6e738d` |
| `--blue` | `#8aadf4` | `--red` | `#ed8796` |
| `--peach` | `#f5a97f` | `--yellow` | `#eed49f` |
| `--green` | `#a6da95` | `--mauve` | `#c6a0f6` |

A state's colour: `running` blue, `idle` overlay, `waiting` and `stacked` subtext, `blocked` yellow, `halted` red, `needs you`
peach, `unread` overlay and faint, `cut` mauve, `cut halted` red.

Per project, the page shows:

- a heading with its name and run line, then **for you**;
- one text block per version: id, state, stage and why, station · model · effort · elapsed, liveness, the phases with
  their ticks, converge's lines, the notes dim;
- then the queue. A project that is `unread` shows its name, faint, and the reason.

The script opens `new EventSource("/events")`, renders each `state` event's whole value, and counts elapsed time each second
from `started`. It builds nodes with `createElement` and `textContent`; it holds none of `innerHTML`, `outerHTML`,
`insertAdjacentHTML`, `document.write`, `eval` or `Function(`.

### D10

D82 is added to `docs/decisions.md` beside D50, in the group of the check loop and the release, and to the page's index
lines:

> **D82 · The viewer is an operator tool.** `mf-ui` reads the recorded and configured projects' run directories, worktrees
> and queue entries, writes only its own state files in the operator's state folder, binds loopback and shows worker-written
> text as text. **Why:** a person who conducts several versions needs one page of them, and the sandbox that keeps workers
> from loopback and the home folder does not bind the operator's own tool. **Rejected:** a root `ui/` · a station of the
> line · a write to a repo. **Accepts:** an unsandboxed server reads files a worker wrote, so a read runs in a child the
> server kills, and the stream is a read of the machine's own projects that any local process can open.

The principle *The repo reaches nothing outside itself* gains a bullet for the viewer's reads and its state folder, linking
D82. `THREAT_MODEL.md` gains one *Trust boundaries* bullet: the viewer runs outside the sandbox, reads worker-written files,
kills a read past its bound, binds `127.0.0.1`, refuses a foreign `Host` and sets text only. `README.md`'s skill table, the
`skills/` entry of `AGENTS.md`'s layout and `docs/README.md`'s `skills/` row name `mf-ui`. The `CHANGELOG.md` entries are the
build's own, one a phase.

### D11

`scripts/corpus.toml` gains the case `viewer`, with `reads` = `the run directory, worktrees and queue of a project, read to its
state tree` and `argv` = `uv run --script skills/mf-ui/scripts/viewer.py project {primary}`, no `each`. It reads this checkout's
run directory, worktrees and queue as a person's run holds them, and must exit 0 whatever the data is, an unread version or an
unread claim ([D5](#d5)) being a value and no failure: a session that refuses `ps` reads the claim `unread`.

No sub-task carries the corpus mark: the plan check reads `scripts/corpus.toml` at the cut, where the case `viewer` does not
yet stand, and sub-task 1.11 adds it. That sub-task then runs `make corpus`, which prints `corpus: viewer · 1 runs · pass`, and
a red case there is the projector's reading of real data failing.

## Tests

`tests/test_viewer.py` is new. It builds a scratch repository with linked worktrees, run directories and a home folder under
`tmp_path`, as the conduct tests do, with the git helpers of the fake worker; it loads `viewer.py` with `runpy.run_path`. It
opens no socket, and starts no server: the routes, the frame and the stream's generator are called, and `start` and `stop`
take a fake spawn, `ps` and signal.

| layer | test | proves |
|---|---|---|
| unit | `test_main_dispatches_its_commands` | `project` prints JSON, an unknown command exits 2 |
| unit | `test_read_part_reads_a_regular_file_only` | a pipe, a link and a missing file read `None`; the head and the tail are bounded |
| integration | `test_a_version_shows_its_phases_with_the_trees_ticks` | `box` at `HEAD`, `done` and `total` from the worktree's `tasks.md`, `null` when it cannot be read |
| integration | `test_the_projector_gives_each_state_its_why` | each state of [D4](#d4) on one repository, with the stage's why |
| integration | `test_a_halt_stands_in_the_newest_log_until_the_version_rejoins` | a halt in an older log ends with a newer sibling-only log; a taken rejoin ends it, a refused one does not |
| integration | `test_a_version_that_raises_is_unread_alone` | a version whose `tasks.md` at `HEAD` has no `## Progress` list is `unread` with the reason, the rest of its project read |
| integration | `test_converge_shows_its_round_cap_blockers_and_each_role` | the run's mark, `fixing`, `CAP`, each role's verdict and verdicts-line fields, the fallback |
| integration | `test_workers_are_the_unfinished_spawns` | pairing by station, several in converge, a stale claim gives `idle` |
| unit | `test_a_claim_ps_cannot_read_is_unread` | a claim whose read raises `Stop` is `unread`, its station versions `idle`, no `stale run` row, the tree printed |
| integration | `test_liveness_is_active_then_quiet` | the levels of [D5](#d5) from set mtimes and a log timestamp |
| integration | `test_for_you_holds_what_needs_a_person` | each kind of [D4](#d4), a dim note in none, a limit past its reset in none, the queue's `cut` and `cut halted` rows |
| integration | `test_the_only_options_print_liveness_and_the_fingerprint` | `--only` prints one JSON object each; the fingerprint moves with a new run log line |
| integration | `test_the_projector_writes_nothing` | the file tree and each mtime are the same after a read |
| integration | `test_a_project_read_past_its_bound_is_killed` | a pipe at the claim's `pid` blocks the child; the read is killed and shows `unread` |
| unit | `test_the_projects_come_from_the_record_and_the_config` | record order, `ui.toml` names, order, hide and a missing `.minions/` |
| unit | `test_a_bad_config_exits_2_naming_it` | a bad TOML, a bad port and a row with no path |
| unit | `test_a_frame_numbers_the_whole_state` | `publish` raises `seq` on a change only; `frame`'s text |
| unit | `test_the_routes_answer_and_refuse` | `/`, `/state`, `/events`, 404 and a foreign or missing `Host` on every path |
| unit | `test_the_stream_sends_each_new_state_once` | the generator's first frame, a newer one, and the keep-alive |
| unit | `test_a_tick_reads_on_a_change_and_on_time` | a fake read: the fingerprint, the 10 s re-read and the 5 s liveness |
| unit | `test_start_finds_and_stop_removes_the_pid_file` | the files under a temporary state folder, the second `start`, `stop`, and a server that exits within the wait: files removed, exit 1 |
| unit | `test_stop_signals_only_the_servers_pid` | a pid that is not the server, a pid at or below 1, no pid file |
| unit | `test_main_runs_serve_start_and_stop` | `main` hands each command to a fake and returns its exit code |
| unit | `test_the_page_sets_text_only` | no file under `skills/mf-ui/` holds a markup sink named in [D9](#d9) |

Evidence, counted at the cut:

| what | command | at the cut |
|---|---|---|
| tests the change adds, by layer | `uv run pytest tests/test_viewer.py --collect-only -q` | none: the file is new |
| tests the change removes | `git diff --stat HEAD -- tests` | none |
| end-to-end runs the change adds | the engines each browser test runs on | none: no browser, no socket |

Each test sits at the lowest layer that can fail for it (`T1`): the state rules, the frame, the routes and the commands are
calls, and the integration tests run the real child on a real repository, since the readers' behaviour is the thing proved.
No test removes or merges another, so there is no table for `I16`. The child's bound is a parameter, and the test that kills
a read sets it to 1 s. The worker, halt, state and liveness tests carry the `slow` marker: each builds a repository and runs
the projector several times, over 5 s, which the child's bound does not cover.

## Dependencies

None.

## Risks / Trade-offs

- **The state rules are the viewer's own reading** of the stages and events of this release. A later station change that
  moves an event moves a state; the corpus case reads real data, the tests hold the rules.
- **The page's script has no test run** under a browser: the person's check against a live run after the release is its proof, and `test_the_page_sets_text_only`
  holds the markup sinks out.
- **Any local process can open the stream.** Loopback and the `Host` check stop other sites, not other processes of the same
  operator; D82 accepts it.
- **A read costs a process per project every tick** for the fingerprint. The full read waits for a change or 10 s.
- **`unpushed` is a local read**, so it shows what the last fetch or push left, never what `origin` holds now.
- **A repo still on the old run layout** is read as the readers read it; no old-layout mark is shown.

## Verdict

Ready to build in the phases of [tasks](tasks.md): the projector, the server, the page, the record, then a person's check
against a live run.
