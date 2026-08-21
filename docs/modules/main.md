---
module: orchestrator/__main__.py
summary: The composition root — wire the real adapters + post-build closures into the driver and run.
entry_point: main
public_api: [main, emit_and_render]
depends_on: [driver, provider, gate, state, status, diff, fanout, findings, converge, release]
---

# `__main__`

The **composition root** — `python -m orchestrator run --repo <target> [--base <ref>]`. It wires the *real*
adapters and the post-build closures into [`driver.run`](driver.md#run).

## What it does

[`main`](#main) resolves the target's vault from its `.env`, loads the coder prompt, builds the coder
[`Profile`](provider.md#profile), constructs [`ClaudeCodeProvider`](provider.md#claudecodeprovider) +
[`SubprocessGate`](gate.md#subprocessgate) + the status sink + the fan-out, converge, and release closures, calls
[`run`](driver.md#run), and exits `0` on `COMPLETE` / `1` on `HALTED`. Private `_make_*` helpers build the
closures the driver's seams expect; one status sink and one gate are shared across the run.

## Boundaries

This module is **deliberately untested** — it is the wiring, validated by running (a spy can't catch a missing
wire). No logic lives here that isn't exercised by the seams it composes; the interesting behaviour is in the
modules it imports.

## Data flow

```mermaid
flowchart TD
    main["main(argv)"] --> vault["_read_vault_dir(repo) — .env"]
    main --> emit["_make_emitter(repo) — .minions/ disk+stdout sink"]
    main --> ver["_plan_version(vault) — vX.Y from plan filename"]
    main --> roles["_fanout_roles() — reviewer/security/simplify prompts"]
    main --> fo["_make_fanout(...) — zero-arg closure, frozen diff at invoke-time"]
    main --> cv["_make_converge(...) — zero-arg closure over the findings files"]
    main --> rel["_make_release(...) — gather facts → verify_release_gate → prepare_release"]
    main --> run["run(provider, gate, coder_prompt, profile, emit_event, fanout, converge, release)"]
```

## How clients use it

```console
$ python -m orchestrator run --repo /path/to/target
▶ phase P1 — building
  coder spawned — running…
  ...
■ complete — 3 phase(s) advanced
```

## Edge cases & invariants

- The coder profile is the one build-capable profile in the system: `allowed_tools=("Edit", "Write", "Bash")`.
- `_make_emitter` creates `<repo>/.minions/`, **truncates `events.jsonl`** (a fresh log per run), and returns
  the `(event) -> None` sink.
- The fan-out closure computes the **frozen diff at invoke-time** (`compute_diff(repo, args.base, "HEAD")`,
  where `--base` defaults to `main`), not at bind time — the final `HEAD` doesn't exist until the build
  finishes.
- The converge closure reads the same three findings files fan-out wrote and re-verifies each round over the
  scoped `head..HEAD` diff — the two stages communicate through disk, not return values.
- The release closure gathers the facts for the **pure** [`verify_release_gate`](release.md#verify_release_gate)
  (`gate.run_gate`, the three findings, backlog/CHANGELOG text, `_git_tags`, `_tree_is_clean`), then
  [`prepare_release`](release.md#prepare_release)s with a real [`SubprocessReleaseGit`](release.md#releasegit) and
  prints the handoff — `_current_branch` and `date.today()` supply the branch and date.
- All three closures are invoked by [`run`](driver.md#run) **only at plan-complete**; a halted build reaches none.
- A higher-order gotcha: each seam is passed the *built closure* (`fanout=_make_fanout(...)`), not the factory.
- `.minions/` is the target's per-run artifact dir (git-ignore it in the target).

## Reference

### `main`

```python
def main(argv: list[str] | None = None) -> int
```

Parse `run --repo <target> [--base <ref>]`, wire the real adapters + the fan-out and converge closures into
[`run`](driver.md#run), print the outcome, and return a process exit code.

- **Returns** — `0` on [`RunStatus.COMPLETE`](driver.md#runstatus--runresult), `1` on `HALTED`.
- **Gotchas** — untested by design; validated by an end-to-end run against a real target.
- **Source** — [`__main__.py`](../../orchestrator/__main__.py)

### `emit_and_render`

```python
def emit_and_render(stream: Path, status: Path, event: Event) -> None
```

The status sink's body: record an event to disk ([`emit`](status.md#emit--read_status)) **and** print
[`render(event)`](status.md#render) live to stdout. `main` binds `stream`/`status` via `functools.partial` to
form the `(event) -> None` sink handed to `run`.

- **Source** — [`__main__.py`](../../orchestrator/__main__.py)
