# Capability: `cli` (the run-from-source entry point)

## Purpose

The `python -m orchestrator` entry: it parses args, wires the real seams (provider, gate, emitter,
fan-out, converge, release) together, runs the zero-token preflight before spend, and dispatches the
`specs check` subcommand. This spec captures the behavior shipped in `orchestrator/__main__.py`.

> `__main__.py` is **wiring** — argument parsing and dependency assembly, with no branching logic of
> its own to unit-test (design §9: "unit where logic; wiring is `spec_exempt`"). Its behavior is a
> system-boundary concern proven at the v0.7 dogfood tier, so every scenario here declares
> `Layers: e2e` (reserved — recorded, not enforced in v0.3). The one path exercised today is the
> `specs check` subcommand, which this repo's own gate runs on every push (dogfood).

## Requirements

### Requirement: CLI dispatch and wiring

The entry point SHALL parse the `run` and `specs check` subcommands, assemble the real seams for a
run, and dispatch `specs check` to the checker — returning a process exit code.

#### Scenario: `run` drives the target repo's plan
- **Key:** `cli:dispatch:run-drives-target`
- **Layers:** e2e
- **WHEN** `python -m orchestrator run --repo <target>` is invoked
- **THEN** it assembles the seams and drives the target's plan, exiting on the run's status

#### Scenario: `specs check` dispatches to the checker
- **Key:** `cli:dispatch:specs-check-subcommand`
- **Layers:** e2e
- **WHEN** `python -m orchestrator specs check [--strict]` is invoked
- **THEN** it runs the spec-binding check over the repo and exits with its 0/1 code

### Requirement: Zero-token preflight before spend

Before spawning any role the entry point SHALL run the **change-state** read, refusing a malformed target with a
diagnostic naming the specific problem — no active change under `changes/` outside `archive/`, a change missing one
of its four artifacts, a `tasks.md` with no `## Progress` checklist, or a `proposal.md` with no declared `version`
— rather than spending tokens mid-run. Every refusal SHALL surface as a preflight diagnostic and a non-zero exit;
no unhandled exception class SHALL be reachable from a misconfigured target. The preflight SHALL read nothing
outside the repository: no `.env`, no vault path, no settings grant.

#### Scenario: A misconfigured target is refused before spend
- **Key:** `cli:preflight:refuses-misconfigured-target`
- **Layers:** e2e
- **WHEN** the target's change is malformed or declares no version
- **THEN** the entry point prints a preflight failure naming the specific problem and exits non-zero without
  spawning a role

#### Scenario: A target with no `.env` and no settings grant runs
- **Key:** `cli:preflight:no-env-no-grant-runs`
- **Layers:** unit
- **WHEN** `run` is invoked against a repo carrying a well-formed change, no `.env`, no `VAULT_PROJECT_DIR` and no
  `.claude/settings.local.json` grant
- **THEN** the preflight passes to the change-state read and the first role is spawned — no preflight error, since
  no path outside the repository is resolved

> The vault-write half of this requirement is deleted with the `change-state` capability's *Vault-write preflight*.
> What remains is the half that was always about the repository: is there a well-formed change to build?
