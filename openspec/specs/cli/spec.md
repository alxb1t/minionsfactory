# Capability: `cli` (the run-from-source entry point)

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

Before spawning any role the entry point SHALL run the plan-state read and the vault-write preflight,
refusing a malformed or misconfigured target with a diagnostic rather than spending tokens mid-run.

#### Scenario: A misconfigured target is refused before spend
- **Key:** `cli:preflight:refuses-misconfigured-target`
- **Layers:** e2e
- **WHEN** the target's plan is malformed or its vault access is not granted
- **THEN** the entry point prints a preflight failure and exits non-zero without spawning a role
