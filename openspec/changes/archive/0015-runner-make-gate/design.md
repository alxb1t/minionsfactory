# 0015-runner-make-gate — design

**In one line:** `SubprocessGate` resolves the gate to `make gate` behind a `make -n gate` check and keeps its
loop; then the toml is deleted and its name retired under a scan. **Verdict: feasible** ([why](#verdict)).

Motivation is in [proposal.md → Why](proposal.md#why). This page holds the decisions, the runner's new shape,
every file the name leaves, the tests and the evidence.

## Context

- `orchestrator/gate.py`: `read_gate_commands(repo)` loads `.minions/minions.toml` with `tomllib` and raises a
  `FileNotFoundError` naming it when absent. `SubprocessGate.run_gate` runs each command through the injected
  `CommandRunner`, stops at the first red, and returns a `GateResult` of steps.
- `orchestrator/driver.py` and `orchestrator/converge.py` emit one `GateStep` event per step. Neither reads the
  toml.
- `tests/test_gate.py` writes a toml fixture for every `SubprocessGate` test.
- The skills run `make gate` since v0.11; `tests/test_skills.py` fails if a skill names the toml.

### Terms

| term | means |
|---|---|
| **the toml** | `.minions/minions.toml`, this repository's deprecated copy of the gate recipe |
| **the dry run** | `make -n gate` — prints what the gate would run, runs nothing |
| **a live mention** | the name in a tracked file outside the specs, `tests/`, `CHANGELOG.md` and the change archive |

## Goals / Non-Goals

**Goals**

- The runner and the skills run the same gate the same way.
- No live mention of the toml survives, and a scan keeps it that way.

**Non-Goals**

- Changing the target repos.
- Keeping one event per recipe command.
- Changing *Run the gate, stop at the first failure*.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | **The gate resolves to `["make gate"]`**, and `SubprocessGate.run_gate` keeps its loop over that list | the loop, the steps and the events stay as they are; the driver and converge change nothing | parsing the dry run into its commands — breaks on `cd frontend && npm ci`, the case the toml could not express |
| <a id="d2"></a>**D2** | **Every failure to find a gate raises `FileNotFoundError` naming `Makefile`** — no file, the dry run exits non-zero, or it prints no command | the same type the toml's absence raises today, so no caller changes | a new exception type |
| <a id="d3"></a>**D3** | **The dry run goes through the injected `CommandRunner`**; only the `Makefile` check reads the disk | unit tests fake `make` without spawning it, as they fake every command today | calling `subprocess` directly for the dry run |
| <a id="d4"></a>**D4** | **The gate spec**: *Read the target's gate command list* REMOVED, *Run the target's `make gate`* ADDED ([specs/gate/spec.md](specs/gate/spec.md)). The stop-at-first-failure tests keep their keys and move to a `Makefile` fixture | a changed title is REMOVED plus ADDED (`I9`) | MODIFIED under the old title, which would then be false |
| <a id="d5"></a>**D5** | **The file and its name retire**: delete the toml, `.gitignore` ignores all of `.minions/`, every live mention goes ([the list](#d5--where-the-name-leaves)), and `minions.toml` joins the retired-word scans in `tests/test_conventions.py` | `W2` — a retirement searches the whole tree; the scan keeps the name out | leaving the mentions for later |
| <a id="d6"></a>**D6** | **Phase order: the runner first, the deletion last** | `A4` — the old thing stays until the new one is proven; deleting the file is the irreversible act | one phase |
| <a id="d7"></a>**D7** | **The gate spec's Purpose paragraph is left to `mf-release`'s hand-edit** | the fold cannot reach a Purpose, and a living spec changes only at the fold | editing the living spec in the build |

### D1–D3 — the runner, before → after

```
  before:  run_gate(repo) ── read_gate_commands(repo) ── tomllib ── [the recipe's commands] ── loop, stop at first red
  after:   run_gate(repo) ── resolve the gate ─┬─ no Makefile            → FileNotFoundError("…Makefile…")
                                               ├─ make -n gate exits ≠ 0 → FileNotFoundError("…Makefile…")
                                               ├─ it prints no command   → FileNotFoundError("…Makefile…")
                                               └─ ["make gate"] ── the same loop
```

"Prints no command" means the dry run's output, stripped, is empty, or every non-empty line contains
`is up to date` or `Nothing to be done`. The resolver's name is the builder's; `read_gate_commands` and the
`tomllib` import go.

### D5 — where the name leaves

| file | the mention today (HEAD `a37c3e1`) | after |
|---|---|---|
| `.minions/minions.toml` | the file itself | deleted |
| `.gitignore` | `.minions/*` and `!.minions/minions.toml`, with a comment keeping "the gate command list" tracked | `.minions/`, comment updated |
| `Makefile` | comment, lines 7–9: the toml mirrors the recipe for the runner | comment: the skills, CI and the runner run `make gate` |
| `CLAUDE.md` | :59 (the runner seam) · :83 (the `.minions/` layout bullet) | the runner runs `make gate`; `.minions/` holds run output only |
| `README.md` | :40 and :53 (what the runner's target repo provides) | a root `Makefile` with a `gate` target; ignore `.minions/` |
| `docs/architecture.md` | :31 (invariant 6) · :81 (graph edge) | the runner runs `make gate` |
| `docs/modules/gate.md` | the module doc describes `read_gate_commands` | rewritten for D1–D3 — phase 1, with the code |
| `docs/modules/main.md` | :78 "keeping `minions.toml`" | ignore all of `.minions/` |
| `prompts/coder.md` | :95 input 6, "the gate config (`.minions/minions.toml`)" | "the root `Makefile`'s `gate` target" |
| `tests/test_conventions.py` | :54, a comment listing tracked unscanned files | the name leaves the comment; it appears once, as the new needle |

## Seams — what the tests hold

| scenario key | the test | seam |
|---|---|---|
| `gate:make-gate:resolves-to-make-gate` | a `Makefile` fixture; the fake runner prints a command for the dry run; the steps are `["make gate"]` | the injected `CommandRunner` |
| `gate:make-gate:missing-makefile-errors` | no `Makefile`; `FileNotFoundError` names it; the fake runner records no call | same |
| `gate:make-gate:missing-target-errors` | the dry run exits non-zero; `make gate` never runs | same |
| `gate:make-gate:empty-target-errors` | the dry run prints nothing, and separately only `'gate' is up to date` | same |
| `gate:run:all-green-passes` · `gate:run:stops-at-first-red` | unchanged keys; the fixture becomes a `Makefile` and the faked dry run | same |
| `sdd:retired-gate-config:named-nowhere` | a scan of `_SCANNED` for `minions.toml`, and a twin that plants it in each root | the scan helpers already in `tests/test_conventions.py` |

## Evidence

| id | observation | check |
|---|---|---|
| **E1** | the runner is the toml's last reader | `git grep -l 'minions.toml' -- orchestrator` prints only `orchestrator/gate.py` |
| **E2** | no skill names the toml | `grep -rl 'minions.toml' skills/` prints nothing |
| **E3** | the live mentions in [D5](#d5--where-the-name-leaves)'s table | `git grep -n 'minions.toml' -- . ':!openspec' ':!CHANGELOG.md' ':!tests'` |

## Dependencies

None.

## Risks / Trade-offs

- **One gate event instead of one per command.** → A red gate's step still carries the whole `make` output, which
  names the failing command.
- **A target repo still carrying only a toml breaks the runner.** → The runner is parked; the error names the
  `Makefile`, and every known target already has a `gate` target.
- **`mf-release` flags the gate spec's Purpose.** → Expected ([D7](#d7)); the hand-edit is one sentence.

## Verdict

**feasible.** The runner module, its tests, one convention scan, and doc lines. No dependency. Both phases end
green on their own.
