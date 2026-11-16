---
bump: minor
after: [0130-small-fixes]
---

# Linux runner

MF's sandbox runs on Linux: a `bwrap` side beside Seatbelt, reasons the port words, an exclude for the Linux sandbox's marks, and real `bwrap` proved in CI.

Reading map: [design](design.md) holds the decisions, the `bwrap` command and the tests, [tasks](tasks.md) its phases, [the spec delta](specs/sdd/spec.md) the requirements it changes.

## Why

On Linux, `sandboxed()` stops with exit 2: only `sandbox-exec` is known, so converge's first command and the npm fetch cannot run. A cloud session or a Linux machine therefore cannot ship a version. The port, `skills/mflib/platform.py`, is one file and already holds every OS call, so the Linux side belongs there.

## What Changes

- The port reads the host's OS once into one name, and every test sets that name.
- On Linux `confine` returns a `bwrap` command, `refused` reads Linux's text, and `has_sandbox` passes only when `bwrap` applies a trivial sandbox.
- The conductor's and the cut's "no sandbox" and "not held" reasons come from the port; Linux has no awake hold and says so.
- On Linux a run's start writes the names Claude Code's Linux sandbox mounts into a worktree to the clone's `.git/info/exclude`, before its first clean-tree check.
- CI's Linux job installs `bubblewrap`, opens user namespaces and runs the real-sandbox tests; the switch is named for any OS.
- D51 and D78 are amended, and the threat model, the OS recipe, `mf-ship` and `mf-cut-change` stop naming a Mac where Linux now works.

Requirements the delta touches, one line each:

- MODIFIED **A plain command runs in an OS sandbox** — Seatbelt or `bwrap`, the accepted differences, the refusal per OS.
- MODIFIED **The platform is reached through one port** — the OS name, `bwrap`, the reasons, the marks.
- MODIFIED **A live run holds the machine awake** — Linux holds nothing and says so.
- MODIFIED **A cut run by hand holds the machine awake** — the same for `awake.py`.
- MODIFIED **The gate holds the structure rules** — `bwrap` joins the OS commands only the port names.
- ADDED **A run on Linux hides the sandbox's marks from its tree checks** — the names, the write, the order.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements above.

## Impact

- Code: `skills/mflib/platform.py`, `skills/mf-ship/scripts/conduct.py`, `skills/mf-cut-change/scripts/awake.py`.
- Tests: `tests/conftest.py`, `tests/test_platform.py`, `tests/test_sandboxed.py`, `tests/test_awake.py`, `tests/test_conduct.py`, `tests/test_structure.py`.
- CI: `.github/workflows/ci.yml`.
- Record: `docs/decisions.md` (D51, D78), `THREAT_MODEL.md`, `docs/recipes.md`, `skills/mf-ship/SKILL.md`, `skills/mf-cut-change/SKILL.md`.
- A Linux machine, or a cloud session, can run converge and the npm fetch; the tag push and the session's git settings stay the operator's.

## Not in this change

- The cloud's own steps — a tag push, `gc.auto` in the guard's list, a fetch at a run's start, a run with no Codex — until a run in the cloud needs them.
- Commit signing, a session's `claude/…` branch, the install at a tag and the poll that keeps a VM up: the session's setup.
- Attribution, MF's own setup script and the run's record coming home: when a cloud session has run one version.
- An awake hold on Linux, `systemd-inhibit` among it: when a Linux machine that must stay awake runs a version.
- A container for workers, and WSL2: when a repo is hostile, or a run starts on WSL2.
- Codex's Linux sandbox and its refusal text: when a Codex worker runs on Linux.
- A stale claim whose leader reads `node`, and a cut by hand on Linux outside a run: when either is met.
- Debt card `0114·S3`: when a sandboxed command leaves an escaped child holding its output pipe.
- Several versions at once in the cloud: when the run's state is a contract.
