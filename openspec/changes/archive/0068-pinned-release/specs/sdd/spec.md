## ADDED Requirements

### Requirement: A machine runs one pinned MF release

`make install-skills` SHALL export a release's `skills/` tree into `$XDG_DATA_HOME/minionsfactory/<tag>/skills/`, falling back to
`~/.local/share/minionsfactory/`, with a `VERSION` file naming the tag at the tree's root, and SHALL point every `mf-*` link on both
`~/.claude/skills` and `~/.agents/skills` into it. Bare, it SHALL take the newest version tag the kept `origin` holds, exported from a
fresh scratch clone of that URL, and clear a hold; `TAG=<tag>` SHALL take that tag from the checkout and hold it; `TAG=live` SHALL
link the checkout and hold. It SHALL record MF's primary in `~/.mf-ship-origin/source`, refuse a destination that is not a link, and
keep every exported tree. While any run is live — a mark `~/.mf-ship-origin/live/<digest>` holding a live pid, which each conductor
writes first at its start and removes at its end — it SHALL move no link, writing `~/.mf-ship-origin/pending` instead. A conductor
ending as the last live run, and an install with no run live, SHALL move the links to the pending tag, or to a newer version tag the
source's kept `origin` holds, exported from a scratch clone; a hold SHALL stop only the move to a newer tag, never a pending one;
no link SHALL move at a run's start. The run's `start` line SHALL name the release it
runs on, `· mf <tag>` or `· mf live <describe>`, `· pending <tag>` while a move waits, and `· skipped <tag>: not on origin`. A station run by hand leaves no live mark.

#### Scenario: A release lands while another repo runs
- **WHEN** MF releases while a run is live in another repo
- **THEN** no link moves, and the links move to the new tag when the last live run ends

#### Scenario: A tag only the local repo holds
- **WHEN** the newest local version tag is not on the kept `origin`
- **THEN** a bare install and a conductor's move skip it, and the `start` line names it

#### Scenario: A planted object
- **WHEN** a replace ref or a rewritten loose object in the primary's `.git` changes what a tag's tree reads
- **THEN** the export, from a scratch clone of `origin`, holds the tag's real tree

#### Scenario: A hold
- **WHEN** the person runs `make install-skills TAG=v0.55.0` or `TAG=live`
- **THEN** no conductor moves the links until a bare `make install-skills`

## REMOVED Requirements

### Requirement: Skills install into the shared user directory by default
**Reason**: one install now links both hosts into one exported release; `SKILLS_DIR` names one directory and leaves the other
host's links behind (`0051·R10`).
**Migration**: run `make install-skills` once; it links `~/.claude/skills` and `~/.agents/skills` together.

## MODIFIED Requirements

### Requirement: A run needs its skills linked

At a run's start, `conduct.py` SHALL find each `skills/mf-*` beside itself linked where its executor looks,
`~/.claude/skills` for `claude` and `~/.agents/skills` for `codex`, every `mf-*` link on both pointing into one tree, and
SHALL else stop, naming the skill or the links and `make install-skills`.

#### Scenario: A skill added by a release
- **WHEN** a release adds a skill and nobody installs it
- **THEN** the next run stops at its start, naming it

#### Scenario: A mixed install
- **WHEN** one `mf-*` link points into another tree than the rest
- **THEN** the run stops at its start, naming the links

### Requirement: A data file records where its values came from

Each data file SHALL record the change, its version, the base and the analyzed revisions, `measured_on`,
`mf_version`, `executor` and `model`. `mf_version` SHALL come from the collector's own package — its checkout's `git describe`, or the `VERSION` file at an
installed tree's root — or be `unknown`;
`executor` SHALL be what the station reported, worded as the build's *Executor* reports it; `model` SHALL be the
station's own report, or `unidentified`. None SHALL be guessed from a name.

#### Scenario: The collector runs from a frozen copy
- **WHEN** the collector's package is not inside a git checkout, and no `VERSION` file stands at its tree's root
- **THEN** the data file records `mf_version: unknown`
- **AND WHEN** it runs from an installed release, its `VERSION` reading `v0.56.0`
- **THEN** the data file records `mf_version: v0.56.0`
