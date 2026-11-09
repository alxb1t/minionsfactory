---
name: mf-converge
description: Converge a built change through its conductor script — `conduct.py converge` freezes the diff, fans out conformance and adversarial as fresh read-only workers, reads their verdicts from disk, runs one fix pass and re-verifies, to a cap of three rounds. Use when every phase of a change is built and committed and the branch needs converging before release.
---

# mf-converge — run the converge script

> **You start the script and relay what it prints. You judge nothing.** [`converge.py`](scripts/converge.py) conducts the
> loop; its checkers, its fixer and its verify workers are fresh processes it starts. You do not review, fix or release:
> `mf-release` finalizes, in a separate session.

`mf-ship` calls the same script in-process; this skill is its other front, per D78 in `docs/decisions.md`.

```
  preconditions ─▶ freeze ─▶ checkers ─▶ verdicts ── clean ─▶ pickup ─▶ debt ─▶ report
                                 ▲           │ a blocker
                                 └─ verify ◀─ fix              cap three rounds
```

## Parameters

| parameter | holds | none given |
|---|---|---|
| `change-id` | the change to converge | inferred, as below |
| `conformance=`, `adversarial=` | `<model>/<effort>`, `default` for none; or `skip`, which stubs that checker | the executor's default |
| `fix=` | `<model>/<effort>`: the fixer's, whatever card it is sent | the executor's default |
| `grant=yes` | one round past the cap, for a cap the person granted | no grant |
| `--executor` | `claude` or `codex`: the host every worker runs on | `claude` |

Without a `change-id`, the candidates are the directories `git ls-files openspec/changes/ ':!openspec/changes/archive/'`
lists, and the candidate's branch is its id. None, several, or a current branch that differs → **halt**, naming them. Echo
`change-id: <id> (inferred: the one active change; branch <branch> agrees)`.

## Run it

From the primary checkout, in the foreground, and wait — never end your turn while it runs:

```sh
uv run --script <this package>/../mf-ship/scripts/conduct.py converge <change-id> [conformance=…] [adversarial=…] [fix=…] [grant=yes]
```

`<this package>` is this installed skill's folder. `uv` missing → **halt**, naming it.

## What it prints

Each status-log event as it writes it, `HH:MM:SS · round N · <event> — <detail>`, to
`.minions/changes/<change-id>/status_log.md` in the run directory; then its last lines:

| exit | last lines | means |
|---|---|---|
| 0 | the close-out: verdicts and rounds, each blocking card's end state, each `inconclusive` section and fix note, the debt, the gate's exit; then `Next: /mf-release, in a fresh session.` | converged |
| 1 | `converge: halt — <reason>`; the log's `halt` line ends ` · head <sha>` | halted: a cap, an amend, a red gate, a worker that failed twice |
| 2 | `converge: cannot run — <why>` | no OS sandbox, no worktree, an executor not on `PATH`, a bad argument |

The steps, the events, each halt and each worker's inputs are in `converge.py`'s module docstring and its functions'. What a
worker reads is in [the worker reference](references/worker.md), [fix](references/fix.md) and [verify](references/verify.md).

## Report, then stop

Relay the close-out as printed, or the halt in full, and the exit code. On a halt, the last line names its answer — an amend
commit, a fixed gate, `/mf-ship grant <change-id>` — then `/mf-converge` again: a re-run resumes from the status log.

## Never

- **Never review, fix or judge in your own context**, and never report a verdict the script did not print.
- **Never edit a findings file, the status log or the debt.** The script and its workers own them.
- **Never weaken the gate**, archive, fold, tag, merge or push.
- **Never write a secret or a real absolute path from the machine the run is on** into a tracked file.
