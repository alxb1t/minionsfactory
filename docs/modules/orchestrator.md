# Module reference — `orchestrator`

The current public API of the `orchestrator` package, as built through **P3**. Signatures below mirror
the code; the docstrings in the source remain the authoritative "what each unit does".

---

## `orchestrator/__init__.py`

The package marker. Currently holds one trivial smoke keeper from P1 (it proves import wiring + the gate;
it will be superseded as real modules are re-exported here).

| Symbol | Signature | Purpose |
| --- | --- | --- |
| `describe` | `describe() -> str` | Return a one-line description of the orchestrator (`"MinionsFactory orchestrator"`). |

---

## `orchestrator/provider.py` — the provider seam

Invoke a role as a fresh headless instance and parse its result. The driver depends on the **`Provider`
Protocol** here, never on the `claude` CLI directly.

### `RoleResult` — the typed CLI result (Pydantic `BaseModel`)

Parsed from `claude -p --output-format json`. Unknown fields in the CLI output are **ignored** (robust to
CLI version drift).

| Field | Type | Notes |
| --- | --- | --- |
| `subtype` | `str` | e.g. `"success"` |
| `is_error` | `bool` | the hard success/failure signal |
| `result` | `str` | the model's final text |
| `session_id` | `str` | for observability / later resume |
| `total_cost_usd` | `float` | cost accounting |
| `stop_reason` | `str \| None` | optional (defaults to `None`) |

### `parse_result`

```python
parse_result(stdout: str) -> RoleResult
```

Pure. Parses + validates a headless JSON string into a `RoleResult`
(`RoleResult.model_validate_json(stdout)`). Unit-tested.

### `Profile` — permission profile (frozen `dataclass`)

Internal config (constructed by us, not parsed at a boundary → a plain dataclass, not Pydantic).

| Field | Type | Default |
| --- | --- | --- |
| `permission_mode` | `str` | `"default"` |
| `allowed_tools` | `tuple[str, ...]` | `()` |
| `disallowed_tools` | `tuple[str, ...]` | `()` |

### `Provider` — the seam (`typing.Protocol`)

```python
class Provider(Protocol):
    def run_role(
        self, role_prompt: str, repo: Path, profile: Profile
    ) -> RoleResult: ...
```

Any class with a matching `run_role` **is** a `Provider` (structural typing — no inheritance required).
`ty` enforces conformance at the point the driver declares `provider: Provider`.

### `build_command`

```python
build_command(role_prompt: str, profile: Profile) -> list[str]
```

Pure. Assembles the `claude -p` argv: `claude -p <prompt> --output-format json --permission-mode <mode>`,
appending `--allowedTools <…>` / `--disallowedTools <…>` only when the profile carries them. Returns a
**list** (each element one argument) — the argv is later passed to `subprocess.run` **without a shell**,
so a dynamic prompt can't inject commands. Unit-tested.

### `ClaudeCodeProvider` — the real adapter

```python
class ClaudeCodeProvider:
    def run_role(self, role_prompt: str, repo: Path, profile: Profile) -> RoleResult
```

`build_command` → `subprocess.run(argv, cwd=repo, capture_output=True, text=True, check=True)` →
`parse_result(stdout)`. The `subprocess.run` call is the one untestable side effect (exercised only in
the P6 dogfood). `check=True` means a non-zero exit raises `CalledProcessError` — the driver will decide
how to treat that; P6 may refine it.

### `FakeProvider` — the scripted test double

```python
class FakeProvider:
    def __init__(self, result: RoleResult) -> None
    def run_role(self, role_prompt: str, repo: Path, profile: Profile) -> RoleResult
```

Returns the preset `RoleResult` (by identity), ignoring its arguments; spawns nothing. Satisfies
`Provider` structurally. Ships in the package (not `tests/`) as the seam's reference double — this is
what the driver's unit tests inject.

---

## `orchestrator/gate.py` — the gate runner

The orchestrator runs the **target repo's own** quality gate itself (un-gameable) and returns a typed
verdict. The driver depends on the **`Gate` Protocol** here.

### `StepResult` — one command's outcome (frozen `dataclass`)

| Field | Type | Notes |
| --- | --- | --- |
| `command` | `str` | the gate command as written in `minions.toml` |
| `exit_code` | `int` | `0` = pass |
| `output` | `str` | combined stdout + stderr (for the halt report) |

### `GateResult` — the aggregate verdict (frozen `dataclass`)

| Field | Type | Notes |
| --- | --- | --- |
| `passed` | `bool` | all steps green |
| `steps` | `tuple[StepResult, ...]` | steps actually run — truncated at the first failure |

### `read_gate_commands`

```python
read_gate_commands(repo: Path) -> list[str]
```

Read the ordered gate command list from `repo/minions.toml` (`tomllib`). Language-neutral: a JS target
ships a different list, no orchestrator change. Unit-tested.

### `run_command`

```python
run_command(command: str, repo: Path) -> StepResult
```

Run one gate command in `repo` via `shlex.split` + `subprocess.run(check=False)` (no shell). `check=False`
is deliberate — a non-zero exit is the gate's *signal*, captured into `StepResult`, not an exception. The
one untested side effect (exercised only in the P6 dogfood).

### `CommandRunner` — the injected-executor type

```python
CommandRunner = Callable[[str, Path], StepResult]
```

### `Gate` — the seam (`typing.Protocol`)

```python
class Gate(Protocol):
    def run_gate(self, repo: Path) -> GateResult: ...
```

### `SubprocessGate` — the real gate

```python
class SubprocessGate:
    def __init__(self, runner: CommandRunner = run_command) -> None
    def run_gate(self, repo: Path) -> GateResult
```

Reads the commands, runs each via the injected `runner` (defaults to the real `run_command`), and
**stops at the first non-zero step**. The `runner` injection is what lets the fail-fast logic be
unit-tested without spawning real tools.

### `FakeGate` — the scripted test double

```python
class FakeGate:
    def __init__(self, result: GateResult) -> None
    def run_gate(self, repo: Path) -> GateResult
```

Returns the preset `GateResult` (by identity), ignoring the repo; runs nothing. Satisfies `Gate`
structurally. Ships in the package as the seam's reference double — what the driver's tests inject.

---

## Planned modules (not yet built)

| Module | Phase | Public surface (planned) |
| --- | --- | --- |
| `state.py` | P4 | `read_plan_state(vault_project_dir, repo) -> PlanState` (state-from-disk; highest-version plan) |
| `driver.py` | P5 | `run(repo, provider, gate)` — the build-spine loop + halt-contract + resume |
| `__main__.py` | P5 | `python -m orchestrator run --repo <target>` |
