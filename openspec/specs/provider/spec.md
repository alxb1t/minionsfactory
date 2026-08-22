# Capability: `provider` (the harness seam)

The seam the driver depends on to run one role instance and get a typed result — a real
`ClaudeCodeProvider` (`claude -p --output-format json`) plus a `FakeProvider` double, behind a
`Provider` Protocol so the driver never touches the CLI directly (harness-agnostic + unit-testable).
This spec captures the behavior shipped in `orchestrator/provider.py`; each `unit` scenario is bound
to its proving test, and the real headless spawn declares `Layers: e2e` (reserved for the v0.7
dogfood tier — recorded, not enforced now).

## Requirements

### Requirement: Build the headless `claude -p` argv

`build_command` SHALL build the headless `claude -p` argv for a role — requesting JSON output under
the profile's permission mode, pinning the model and reasoning effort only when supplied (omitting
each flag otherwise), and passing the profile's allowed/disallowed tools.

#### Scenario: The argv requests headless JSON under the profile
- **Key:** `provider:build-command:headless-json`
- **Layers:** unit
- **WHEN** `build_command` runs for a role prompt and a profile
- **THEN** the argv leads with `claude -p <prompt>`, requests `--output-format json`, sets the
  permission mode, and appends the profile's allowed tools

#### Scenario: The model is pinned when given
- **Key:** `provider:build-command:pins-model`
- **Layers:** unit
- **WHEN** a model is supplied
- **THEN** the argv carries `--model <model>`

#### Scenario: The model flag is omitted by default
- **Key:** `provider:build-command:omits-model-by-default`
- **Layers:** unit
- **WHEN** no model is supplied
- **THEN** the argv carries no `--model` flag

#### Scenario: The reasoning effort is set when given
- **Key:** `provider:build-command:sets-effort`
- **Layers:** unit
- **WHEN** an effort is supplied
- **THEN** the argv carries `--effort <effort>`

#### Scenario: The effort flag is omitted by default
- **Key:** `provider:build-command:omits-effort-by-default`
- **Layers:** unit
- **WHEN** no effort is supplied
- **THEN** the argv carries no `--effort` flag

### Requirement: Read-only role profile

`read_only_profile` SHALL produce a profile that denies Bash and Edit and scopes Write to only the
role's findings file — so a read-only role cannot mutate the repo.

#### Scenario: The read-only profile denies mutation and scopes the write
- **Key:** `provider:read-only-profile:denies-and-scopes-write`
- **Layers:** unit
- **WHEN** a read-only role is built for a findings file
- **THEN** the argv disallows Bash and Edit and allows Write only to that findings file

### Requirement: Parse the result and map failures

`parse_result` SHALL parse a headless JSON result into a typed `RoleResult`, and the real provider
SHALL raise `ProviderError` on a non-zero exit so the driver halts cleanly and resumably instead of
crashing with a raw traceback.

#### Scenario: The headless JSON parses into a typed result
- **Key:** `provider:result:parses-headless-json`
- **Layers:** unit
- **WHEN** a headless JSON result string is parsed
- **THEN** its fields (result, session id, cost, error flag) read out typed

#### Scenario: A non-zero exit raises ProviderError
- **Key:** `provider:result:nonzero-exit-raises-provider-error`
- **Layers:** unit
- **WHEN** the underlying `claude -p` process exits non-zero
- **THEN** a `ProviderError` carrying the failure detail is raised

#### Scenario: The real provider spawns claude -p end to end
- **Key:** `provider:real-spawn:runs-claude-headless`
- **Layers:** e2e
- **WHEN** `ClaudeCodeProvider.run_role` runs against a real repo
- **THEN** it spawns `claude -p` and returns the parsed result

> `Layers: e2e` (reserved): the real headless spawn is a system-boundary behavior proven at the v0.7
> dogfood tier; the unit-provable core is argv construction, profile scoping, parsing, and error
> mapping above (the network is never touched in a unit test).
