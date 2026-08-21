---
module: orchestrator/state.py
summary: Reconstruct "where are we" from disk, and guard the target contract before a run.
entry_point: read_plan_state
public_api: [read_plan_state, PlanState, select_plan, parse_frontmatter, read_head, validate_plan, PlanContractError, verify_vault_access, PreflightError]
depends_on: []
---

# `state`

Reconstruct **where the run stands** from disk alone — the highest-version plan's phase state plus the target
repo's git head. This is what makes resume free.

## What it does

[`read_plan_state`](#read_plan_state) selects the active plan ([`select_plan`](#select_plan)), reads its
frontmatter ([`parse_frontmatter`](#parse_frontmatter)) for `current_phase` + the `phaseN` flags, and pairs it
with the git head ([`read_head`](#read_head)) into a [`PlanState`](#planstate). The driver reads it before and
after each phase to **detect** advance.

It also owns the **read-side of the target contract**: [`validate_plan`](#validate_plan) refuses a malformed or
non-code-phase plan at read time (a [`PlanContractError`](#plancontracterror)), and
[`verify_vault_access`](#verify_vault_access) preflights that the target grants the coder vault write access (a
[`PreflightError`](#preflighterror)) — so a misconfigured target halts **before any spend**, not obscurely
mid-run.

## Boundaries

It reads state; it never writes it. It knows nothing about *why* a phase advanced — it only reports the two
facts (`current_phase`, `head`) the driver compares. Plan selection deliberately ignores `archive/` (completed
predecessors are historical record).

## Data flow

```mermaid
flowchart LR
    sp["select_plan(vault) — highest vX.Y_, ignore archive/"] --> pf["parse_frontmatter(text)"]
    pf --> ph["phaseN flags + current_phase"]
    rh["head_reader(repo) — git rev-parse HEAD"] --> ps["PlanState"]
    ph --> ps
```

## How clients use it

```python
before = read_plan_state(vault_project_dir, repo)
#  ... run the coder + gate ...
after = read_plan_state(vault_project_dir, repo)
advanced = after.head != before.head and after.current_phase != before.current_phase
```

## Edge cases & invariants

- Plan selection compares versions as `(int, int)` tuples, so `v0.10 > v0.2` (not string order).
- `parse_frontmatter` is stdlib-only (no YAML dependency): it splits each line on the **first** `:` and stops at
  the closing `---` fence — sufficient for our flat, known keys.
- `read_head` is the one untested side effect; `read_plan_state`'s injectable `head_reader` lets the composition
  be tested without spawning git.
- **Fail-closed contract checks.** `validate_plan` refuses no-frontmatter / missing-`current_phase` /
  no-`phaseN` / non-code-status plans — including the *silent* case where a zero-phase plan would otherwise read
  as already "complete". `verify_vault_access` refuses a target missing the vault grant. Both raise, never pass
  on doubt.
- The status allowlist (`{done, wip, planned, todo}`) is the "code phase" vocabulary; `driver._plan_complete`
  keys only on `"planned"`, so the two vocabularies aren't yet identical (a known reconciliation).

## Reference

### `PlanState`

```python
@dataclass(frozen=True)
class PlanState:
    current_phase: str  # the plan's free-form phase pointer (frontmatter)
    phases: dict[str, str]  # phase0…phaseN → "done" / "planned"
    head: str  # the target repo's git HEAD sha
```

Where-are-we, read from disk.

- **Why a dataclass, not Pydantic** — its fields are pass-through strings that need no coercion or validation (contrast [`FindingsState`](findings.md#findingsstate), which does). Pydantic where boundary data needs validating, not at every boundary.
- **Consumed by** — [`decide`](driver.md#decide) (compares `before` vs `after`) and [`driver.run`](driver.md#run) (plan-complete check reads `phases`).

### `select_plan`

```python
def select_plan(vault_project_dir: Path) -> Path
```

Return the **highest-version** `vX.Y_*implementation_plan.md` under `implementation_plans/`, ignoring
`archive/`.

- **Gotchas** — a shallow `glob` (never descends into `archive/`); version compared as `(int, int)` so `v0.10 > v0.2`.
- **Called by** — [`read_plan_state`](#read_plan_state); also [`__main__`](main.md) to derive the plan version for findings filenames.
- **Source** — [`state.py`](../../orchestrator/state.py) · **Tests** — [`test_state.py`](../../tests/test_state.py)

### `parse_frontmatter`

```python
def parse_frontmatter(text: str) -> dict[str, str]
```

Parse a plan's leading `---`-fenced YAML frontmatter into flat `key -> str` values — a small stdlib-only
extractor for our known, flat keys.

- **Gotchas** — splits on the **first** `:` (`str.partition`), strips surrounding quotes, stops at the closing fence; returns `{}` if the text does not start with `---`.
- **Reused by** — [`read_findings_state`](findings.md#read_findings_state) (no new parser for the findings file).
- **Source** — [`state.py`](../../orchestrator/state.py) · **Tests** — [`test_state.py`](../../tests/test_state.py)

### `read_head`

```python
def read_head(repo: Path) -> str
```

Return the target repo's git HEAD sha via `git rev-parse HEAD` (list-argv, no shell).

- **Gotchas** — the one untested side effect (exercised in the dogfood run).
- **Source** — [`state.py`](../../orchestrator/state.py)

### `read_plan_state`

```python
def read_plan_state(
    vault_project_dir: Path,
    repo: Path,
    head_reader: Callable[[Path], str] = read_head,
) -> PlanState
```

Compose [`select_plan`](#select_plan) → [`parse_frontmatter`](#parse_frontmatter) →
[`validate_plan`](#validate_plan) → git head into a [`PlanState`](#planstate).

- **Params** — `head_reader`: the git-head seam (defaults to [`read_head`](#read_head)); tests inject a stub so the composition runs without git.
- **Returns** — [`PlanState`](#planstate)
- **Raises** — [`PlanContractError`](#plancontracterror) on a malformed / non-code-phase plan (via `validate_plan`).
- **Called by** — [`driver.run`](driver.md#run) via the injected `state_reader` seam; also directly in [`__main__`](main.md)'s preflight (to fail a malformed plan before spend).
- **Source** — [`state.py`](../../orchestrator/state.py) · **Tests** — [`test_state.py`](../../tests/test_state.py)

### `validate_plan`

```python
def validate_plan(frontmatter: dict[str, str]) -> None
```

Raise [`PlanContractError`](#plancontracterror) if the plan frontmatter breaks the execution contract: a `---`
fence carrying `current_phase` and ≥1 `phaseN` flag, each with a recognized code-phase status.

- **Raises** — [`PlanContractError`](#plancontracterror) with a specific message per violation (no frontmatter / missing `current_phase` / no `phaseN` flags / a non-code status).
- **Gotchas** — the status allowlist is `{done, wip, planned, todo}`; anything else (e.g. `research`) is refused as non-code — the execution-side mirror of an authoring `/plan-check`. A non-code phase can't be told from a code phase structurally, so an out-of-vocabulary status *is* the signal.
- **Called by** — [`read_plan_state`](#read_plan_state).
- **Source** — [`state.py`](../../orchestrator/state.py) · **Tests** — [`test_state.py`](../../tests/test_state.py)

### `PlanContractError`

```python
class PlanContractError(ValueError):  # a plan breaks the execution contract
```

Raised by [`validate_plan`](#validate_plan). Caught in [`__main__`](main.md)'s preflight to print a clean
diagnostic and exit `1` — never a bare traceback mid-run.

### `verify_vault_access`

```python
def verify_vault_access(repo: Path, vault_project_dir: Path) -> None
```

Raise [`PreflightError`](#preflighterror) unless the target's `.claude/settings.local.json` grants the coder
write access to the vault (the vault dir, or an ancestor, under `additionalDirectories`).

- **Why** — the coder + read-only roles write vault files (findings, bookkeeping) *outside* the repo cwd; without the grant a run would fail mid-flight. Checked before any spawn.
- **Gotchas** — checks both `permissions.additionalDirectories` and a top-level `additionalDirectories`; a grant *covers* the vault if it equals or is an ancestor of it (`Path.is_relative_to`). The exact settings schema is confirmed live at the P8 dogfood.
- **Called by** — [`__main__`](main.md)'s preflight.
- **Source** — [`state.py`](../../orchestrator/state.py) · **Tests** — [`test_state.py`](../../tests/test_state.py)

### `PreflightError`

```python
class PreflightError(Exception):  # the target isn't configured for a run
```

Raised by [`verify_vault_access`](#verify_vault_access). Caught in [`__main__`](main.md)'s preflight → clean
diagnostic + exit `1`, before any spend.
