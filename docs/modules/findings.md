---
module: orchestrator/findings.py
summary: Read a role's findings file into a validated convergence verdict — the loop's signal.
entry_point: read_findings_state
public_api: [read_findings_state, FindingsState, all_findings_clean]
depends_on: [state]
---

# `findings`

Read a role's findings file into a typed, validated **convergence verdict** — purely from disk. This is the
read-half of the converge loop.

## What it does

[`read_findings_state`](#read_findings_state) reuses [`parse_frontmatter`](state.md#parse_frontmatter) to read a
findings file's frontmatter and validates it into a [`FindingsState`](#findingsstate) (`verdict` /
`open_blocking` / `round` / `head`). A missing file reads as `None`.

## Boundaries

This is **principle 2 made concrete**: the orchestrator decides "are we done?" from `verdict`/`open_blocking`
in *this file*, never from what a fixer *claims*. Those fields are owned by the **verify pass** (the fixer only
flips a finding `open → fixed`; the verifier owns the counters), so the signal can't be gamed. This module only
reads — it does not run the verify pass ([`fan-out`](fanout.md) does).

## How clients use it

```python
states = [read_findings_state(p) for p in findings_paths]  # one per role
converged = all_findings_clean(states)  # every file present and verdict == "clean"
```

## Edge cases & invariants

- A **missing file → `None`** (a not-yet-run role, not a crash) — which keeps `verdict` a strict `Literal` and
  forces the converge loop to handle "not run" explicitly.
- `verdict` is a closed `Literal`: a typo'd verdict is **rejected** at read, not silently accepted.
- No new parser — the findings file and the plan share [`parse_frontmatter`](state.md#parse_frontmatter).

## Reference

### `FindingsState`

```python
class FindingsState(BaseModel):  # frozen
    verdict: Literal["clean", "changes-requested"]  # closed set; typo → rejected
    open_blocking: int  # coerced from the frontmatter string
    round: int  # coerced
    head: str  # short SHA the pass reviewed (→ next re-verify: head..HEAD)
```

A role's findings verdict, read from the file's frontmatter (a trust boundary).

- **Why Pydantic, not a dataclass** — unlike its sibling [`ChangeState`](state.md#changestate), this boundary read
  has ints to coerce and a closed `verdict` to validate. Pydantic *where boundary data needs validating*, not
  at every boundary.
- **Consumed by** — [`converge`](converge.md#converge) and [`verify_release_gate`](release.md#verify_release_gate)
  (both clean iff `verdict == "clean"` for all three, via [`all_findings_clean`](#all_findings_clean));
  collected by [`run_fanout`](fanout.md#run_fanout); `head` scopes the next re-verify's diff.

### `read_findings_state`

```python
def read_findings_state(path: Path) -> FindingsState | None
```

Read a findings file into a validated [`FindingsState`](#findingsstate); a **missing file → `None`**.

- **Gotchas** — reuses [`parse_frontmatter`](state.md#parse_frontmatter) and `model_validate`s the dict: Pydantic
  coerces the ints, ignores extra frontmatter keys, validates `verdict`. `None` (not an exception) on a missing
  file so `ty` forces the loop to handle "not run".
- **Called by** — [`run_fanout`](fanout.md#run_fanout) and the converge closures in [`__main__`](main.md).
- **Source** — [`findings.py`](../../orchestrator/findings.py) · **Tests** — [`test_findings.py`](../../tests/test_findings.py)

### `all_findings_clean`

```python
def all_findings_clean(states: Sequence[FindingsState | None]) -> bool
```

Whether every findings file is present and its verdict is `clean` — the shared convergence/release signal.

- **Gotchas** — a missing file (`None`) counts as **not clean**, so a not-yet-run role can never let the loop
  converge or the release gate pass falsely.
- **Called by** — [`converge`](converge.md#converge) (the loop's clean check) and
  [`_findings_blocker`](release.md#verify_release_gate) inside [`verify_release_gate`](release.md#verify_release_gate).
- **Source** — [`findings.py`](../../orchestrator/findings.py) · **Tests** — [`test_findings.py`](../../tests/test_findings.py)
