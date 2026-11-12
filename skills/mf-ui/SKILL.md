---
name: mf-ui
description: Show every project's ship line as one live page on loopback — each version's stage and why, its phases, converge round, workers and liveness, what needs the person, and the queue — read from the run directories, worktrees and home queue of the recorded repos, in a state folder it alone writes. Use to watch several versions at once, or to start or stop the viewer; an operator tool, never part of a run.
---

# mf-ui — one page for the ship line

> **Your role is OPERATOR.** You start or stop the viewer and pass on its URL. You write into no repo, change no run
> and decide nothing for a version.

## Parameters

| given | does |
|---|---|
| none, or `start` | start the server detached, or find the running one, and print its URL |
| `stop` | end the server `start` started |

The projects are the lines of `~/.mf-ship-origin/repos` that hold `.minions/`. The optional `ui.toml`, in
`$XDG_CONFIG_HOME/minionsfactory/`, else `~/.config/minionsfactory/`, sets `port` (default `8737`) and `[[container]]` rows
of `path`, `name` and `hide`, per [D82](../../docs/decisions.md#d82--the-viewer-is-an-operator-tool).

## Run

`/mf-ui` runs `uv run --script <this package>/scripts/viewer.py start`. Exit 0 → give the person the URL it printed. Exit 2 →
**halt**, copying what it printed: `ui.toml` is bad. Exit 1 → **halt**, copying its line: the server exited, and its log is
`viewer.log` in the state folder.

`/mf-ui stop` runs `uv run --script <this package>/scripts/viewer.py stop`, and prints `viewer: stopped` or
`viewer: not running`.

The state folder is `$XDG_STATE_HOME/minionsfactory/`, else `~/.local/state/minionsfactory/`. It holds `viewer.pid`,
`viewer.port` and `viewer.log`: the only files the viewer writes.

`viewer.py project <primary>` prints one project's state tree as JSON, for a person or a script to read.

## Report

**Close-out:** at most two sentences — the URL, or that the viewer stopped. The page sets every string as text, and only the
person opens it.
