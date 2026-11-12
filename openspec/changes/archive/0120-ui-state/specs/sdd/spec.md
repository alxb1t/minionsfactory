## ADDED Requirements

### Requirement: The viewer projects every ship line, read-only

`skills/mf-ui/scripts/viewer.py project <primary>` SHALL load `conduct.py` and `converge.py` from the skill's sibling
packages by path, run with `GIT_OPTIONAL_LOCKS=0`, and print one project's state tree as JSON: each open version's stage and
its `why`, its state, its phases with the ticks of its worktree's `tasks.md`, its converge round, cap, blockers and each role's
executor, model, effort and fallback, its workers, its liveness and its dim notes; the project's run line, its **for you** rows
and its queued cuts. A state SHALL be one of `running`, `idle`, `waiting`, `stacked`, `blocked`, `halted`, `needs you` or
`unread`, by fixed rules read from the stage, the run log, the claim and the change folder: `running` is a station stage with an
unfinished spawn under a live claim, `idle` a station stage with none, `blocked` a waiting version that names a dependency
halted or needing a person, `halted` a `converge-halted` stage, a `build` stage whose `build.halt` names `HEAD`, or a version
whose last line of the newest run log is a halt, a worker's exit or a rescue's diagnosis alike, until a later line of the
version or a newer run log with none ends it, and
`needs you` a `human`, `integrating` or `released` stage. **For you** SHALL hold each version that needs a person or is halted,
each queued cut that halted, a stale claim, a usage limit whose reset is ahead and an unpushed default branch, each row with its
`why`; a rescue's or a supervisor's decision SHALL show dim on its version and never in it. The server SHALL list the projects the
home folder's `repos` record names, each that holds `.minions/`, with the `[[container]]` rows of `ui.toml`, found under
`$XDG_CONFIG_HOME/minionsfactory/`, else `~/.config/minionsfactory/`, naming, ordering or hiding them; a missing file SHALL halt
nothing, and a bad one SHALL exit 2 naming it. It SHALL read each project in a child process and kill a read past 10 s, showing
that project unread with the reason; a version whose projection raises SHALL show unread alone, the rest of its project read. It
SHALL write no repo, run no git command that changes one, and touch no network. It SHALL answer `/` with the page, `/events` with
the newest whole state and each newer one as server-sent events, each frame numbered, and `/state` with the newest frame as JSON,
bound to `127.0.0.1`; any other path SHALL be 404, and a request whose `Host` is neither `127.0.0.1:<port>` nor
`localhost:<port>` SHALL be refused. The page SHALL set every string as text.

#### Scenario: Each state has its why
- **WHEN** fixture run directories hold a version in each state, a halted one, one needing a person, a waiting one and its
  blocked dependent, a stacked one and a queued cut that halted
- **THEN** the projector prints each version with its state, its stage and the stage's `why`, its phases with the worktree's ticks,
  and the halted cut in the queue and in **for you**

#### Scenario: A halt in the newest run log
- **WHEN** a version's last line of the newest run log is `halt — rescue diagnosed`, and then a newer run log holds only a
  sibling's lines, and then the newest log holds its halt again followed by the run's `rejoin — <id>: build`
- **THEN** the version shows halted, then the state its stage gives once the newer log stands, and again once the rejoin
  follows its halt, while a refused `rejoin — <id>: still …` leaves it halted

#### Scenario: Converge and workers
- **WHEN** a version's status log holds a run marked `· amend`, a `verdicts` line per role and a top line `fix — sent R1`, and the
  newest run log holds an unfinished spawn of each checker
- **THEN** the version shows the round, the mark, `fixing`, each role's executor, model, effort and fallback, the open blockers
  and each unfinished spawn as a worker, with liveness `active` while a write is under a minute old and `quiet` after five

#### Scenario: A read that fails
- **WHEN** one version's `tasks.md` has no `## Progress` list, and another project's claim `pid` is a pipe the read cannot pass
- **THEN** that version shows unread with the reason while the rest of its project shows its state, and the project with the
  pipe is killed at the bound and shows unread

#### Scenario: A foreign Host
- **WHEN** a request names a `Host` other than `127.0.0.1:<port>` or `localhost:<port>`
- **THEN** it is refused on every path, and a request with an accepted `Host` for any path but `/`, `/events` and `/state` is 404

#### Scenario: The stream
- **WHEN** the state changes after a client holds `/events`
- **THEN** the client receives the newest numbered whole state, and a state that did not change is not sent again

### Requirement: The viewer starts, is found and stops by files in its own state folder

`viewer.py start`, which `/mf-ui` runs, SHALL start the server detached and print its URL; a second `start` SHALL find the
running server by its pid file and print the same URL, and `viewer.py stop`, which `/mf-ui stop` runs, SHALL end it. The pid,
port and log SHALL be files in `$XDG_STATE_HOME/minionsfactory/`, else `~/.local/state/minionsfactory/`, and the only files the
viewer writes: none in a repo. `stop` SHALL signal a pid only while that pid names a process whose command is the viewer's server,
SHALL refuse a pid at or below 1, and SHALL remove the files; a pid file that names no such process SHALL be stale, and `start`
replaces it. `viewer.py` SHALL be a standard-library `uv` script, and no file under `skills/mf-ui/` SHALL set HTML from a string.

#### Scenario: Start, find, stop
- **WHEN** `start` runs under a temporary state folder, then `start` again, then `stop`
- **THEN** the first writes the pid and port files and prints the URL, the second starts nothing and prints the same URL, and
  the stop signals that pid and removes both files

#### Scenario: A pid that is not the server
- **WHEN** the pid file names a process whose command is not the viewer's server
- **THEN** `stop` signals nothing, removes the stale files and says it was not running, and `start` starts a new server
