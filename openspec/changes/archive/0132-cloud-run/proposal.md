---
bump: minor
version: 0.105
after: [0131-linux-runner]
---

# Cloud run

A run ships a version from a cloud session: a machine setting for the tag push, the tags origin already holds made at a run's start, origin's default branch fetched, `gc.auto` allowed, and a missing Codex a fallback for checkers.

Reading map: [design](design.md) holds the decisions, the tag and fetch rules and the tests, [tasks](tasks.md) its phases, [the spec delta](specs/sdd/spec.md) the requirements it adds.

## Why

[0131-linux-runner](../0131-linux-runner/design.md) lets a run stand on Linux; a cloud session still halts it where the probes found it. The cloud's GitHub proxy refuses a tag push and the cloud writes `gc.auto` into the clone's `.git/config`, which the config guard refuses. Its cached clone's default branch is behind `origin`, so a version is cut from a stale base, and it has no Codex, so a plan with Codex checkers halts at the start.

## What Changes

- `tags` under `[push]` in the operator's `ship.toml` makes a run on that machine push no tag and halt on none; a release's check passes with its tag on no remote.
- A run's start makes the local tag of each release commit `origin`'s default branch holds that has none, in the release's own shape, and pushes it where the machine pushes tags.
- A run's start fetches `origin`'s default branch through the conductor's scratch repo and fast-forwards the local one, never merging.
- `gc.auto` joins the keys the config guard allows in the repo's own git config.
- Where Codex is not on `PATH`, a checker a plan gives to Codex runs on Claude and the start says so once; a station on Codex still halts.
- D47, D17, D76 and D84 are amended, and the threat model and `mf-ship` say what a cloud machine pushes and fetches.

Requirements the delta touches, one line each:

- ADDED **A machine sets whether a run pushes tags** — the `[push]` table, its values, a release and `status` under `false`.
- ADDED **A run's start makes the tag of each release origin already holds** — the shape, the exceptions, the push.
- ADDED **A run's start brings origin's default branch in** — the fetch, the fast-forward, the states.
- ADDED **The git config guard allows `gc.auto`** — the one key.
- ADDED **A checker on Codex runs on Claude where Codex is not installed** — the third cause, the start line.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements above.

## Impact

- Code: `skills/mf-ship/scripts/conduct.py`.
- Tests: `tests/test_conduct.py`.
- Record: `docs/decisions.md` (D47, D17, D76, D84), `THREAT_MODEL.md`, `skills/mf-ship/SKILL.md`.
- A cloud session on a setup script can ship a version with no hand step at the release: the tag is made at the next run's start and pushed from a machine that pushes tags.

## Not in this change

- Commit signing: the session's setup turns it off with one git setting, and cloud commits are unsigned.
- A session's `claude/…` branch, the install of MF at a tag and the poll that keeps a VM up: the session's setup.
- Attribution, MF's own setup script and the run's record coming home: when a cloud session has run one version. Until then a cloud run's debt cards are pushed to a branch by the session and not imported.
- A cut's environment halt that names `/mf-plan` as its next act: when the line's halt texts are next amended.
- A Codex station in the cloud: a station on Codex still halts, and Codex's own sandbox is not proved there.
- Several versions at once in the cloud: when the run's state is a contract.
