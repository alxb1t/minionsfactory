---
bump: patch
---

# Sandbox tmp

A sandboxed command's and a Codex worker's `TMPDIR` lies outside every repository, and MF's tests stop depending on where their
temporary folder lies. A patch: a defect of what the line already does ([AGENTS.md](../../../AGENTS.md)).

Read [design](design.md) for the decisions, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirements.

## Why

0110-gate-hardening's converge halted `cap reached` on a gate that was red only inside `converge.py`'s sandbox: `sandboxed()` sets
`TMPDIR` to `.minions/tmp` of the primary, inside its git repository, so the corpus, facts, plan check, skip stub, verify check, next tag, pin and planted-key tests, which make a repository or scan a
folder under their `tmp_path`, find the primary's repository above it ([design](design.md#context), F1–F3). Every converge from v0.91.0 on meets
this. A Codex worker has no temporary folder at all, and its checker once halted `not clean` on a here-document (F5).

## What Changes

- **The tests' layer** — `tests/conftest.py` sets `GIT_CEILING_DIRECTORIES` at pytest's base temp for every test; the planted-key
  test scans a folder that is its own repository, from inside it, so the gate's `.minions/` allowlist never reads the path above
  it. This layer alone makes the gate green under the pinned `sandboxed()`.
- **The runner's layer** — `sandboxed()` gives each command a fresh `TMPDIR` outside every repository, writable, removed after it;
  `tests/conftest.py` also sets `TMPDIR` to a folder beside each test's `tmp_path`, so a test's fresh folder lies under the ceiling.
- **The Codex worker** — `argv()` gives each Codex worker a fresh `TMPDIR` outside every repository as its own writable root,
  and `conduct.py` removes it when the worker ends; `SHELL_RULES` forbids a here-document.

Requirements, in [the delta](specs/sdd/spec.md), both MODIFIED:

- *A plain command runs in an OS sandbox* — its `TMPDIR` is a fresh folder outside every repository, removed after it; a conductor
  whose own `TMPDIR` lies in a repository runs nothing.
- *A worker runs in an OS sandbox* — a Codex worker's `TMPDIR` is its own fresh folder and its one extra writable root; the shell
  rules every worker's prompt carries forbid a here-document.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdd`: the requirements above.

## Impact

Changes `skills/mf-ship/scripts/conduct.py`, `tests/conftest.py`, `tests/test_guardrails.py`, `tests/test_sandboxed.py`,
`tests/test_conduct.py` and `skills/mf-release/SKILL.md`. Dependencies: none. The gate recipe stays unchanged.

0110-gate-hardening integrates this patch after its release and re-pin, and rejoins; its round-1 fixes stand.

## Not in this change

- A Claude worker's `TMPDIR`: Claude's own sandbox gives it one, and `.minions/tmp/` stays its scratch folder.
- A Codex fixer, or the whole converge on Codex: a version of its own.
- A change to the gate recipe, or to a decision in force: [D51](../../../docs/decisions.md#d51--a-worker-runs-in-an-os-sandbox-and-no-worker-pushes) holds, and no repository becomes writable.
