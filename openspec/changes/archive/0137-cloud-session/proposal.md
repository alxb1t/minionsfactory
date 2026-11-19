---
bump: minor
version: 0.109
beside: [0136-status-log]
---

# Cloud session

A cloud session can ship a version with no hand step but the tag: a worker's commit names no session and is signed by nobody, `report` names the default branch where no tag is pushed, `conduct.py wait` keeps the VM up, and a script in the repository sets the machine up.

Reading map: [design](design.md) holds the decisions, the test cost and the setup script's shape; [tasks](tasks.md) holds the phases, the last a person's.

## Why

Probe 4 passed end to end in a cloud session and left these for the person's hands:

- Each worker's commit carries `Claude-Session: <url>`, the operator's session, in pushed history.
- The setup turns signing off for the whole machine, so the conductor's own merges go unsigned too.
- `report` reads `not pushed` for a release whose `main` is on `origin`, because the proxy refuses the tag.
- The session keeps the VM up by polling `status` by hand, and its setup is the probe's `setup.sh`.

## What Changes

- **A worker's commit names no session:** each Claude worker's settings gain `attribution.sessionUrl` false.
- **A worker's git signs nothing:** `HOOKS_OFF` gains `commit.gpgsign` and `tag.gpgsign`, false; the conductor's own git is told nothing.
- **`report` names the default branch:** with `tags = false` its word reads `origin`'s default branch, not the tag.
- **`conduct.py wait`:** a new command that blocks until the live run ends and prints a line at every poll.
- **`scripts/cloud_setup.py`:** a new script, run by a cloud environment's setup, that makes a Linux machine ready for a run.
- **The record:** a README section on the cloud, new decisions D85 and D86 and D17 and D21 amended, the threat model and `mf-ship`'s command table.
- **The digest of `uv`:** a last phase for the person, who gives the script the digest of the `uv` release it downloads.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: adds the requirements *A worker's commit names no session*, *A worker's git signs nothing*, *`report` names the default branch where a machine pushes no tag*, *`conduct.py wait` blocks until the run ends* and *A cloud environment's setup script makes a Linux machine ready*.

## Impact

- `skills/mf-ship/scripts/conduct.py`: `worker_settings`, `HOOKS_OFF`, `report`, `wait` and the parser.
- `scripts/cloud_setup.py` and `tests/test_cloud_setup.py`, new; `docs/modules.md` gains a row.
- `tests/test_conduct.py` and `tests/test_sandboxed.py`: the sandbox settings test and the deny lists test edited, the rest added.
- `README.md`, `docs/decisions.md`, `THREAT_MODEL.md` and `skills/mf-ship/SKILL.md`.
- Runs beside `0136-status-log` on `conduct.py` and `skills/mf-ship/SKILL.md`; nothing waits on it.

## Not in this change

- A second line of MF on one repository: stated as a rule, not built.
- The record coming home, and the leak scan's rule for the workers' stream-json logs.
- A release merge made by the conductor, so that it signs it.
- `UV_NATIVE_TLS`, which only warns.
- A session start hook, and anything written into a target repository.
- Several versions at once in the cloud; Codex in the cloud.
- Probe 5, run by the person after the release.
