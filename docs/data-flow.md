# Data & control flow

Two views: **what runs today** (the provider seam, built in P2) and **the planned build-spine loop**
(P3–P5) that will call it. Planned pieces are labelled as such.

## Built today — running one role (`run_role`)

`ClaudeCodeProvider.run_role` is three moves. The middle one is the only side effect; the outer two are
pure and unit-tested. This is the **invoke/parse split** — isolate the untestable subprocess so all the
logic that can be *wrong* (argv assembly, JSON parsing) is pure.

```mermaid
sequenceDiagram
    participant Caller as caller (driver, PLANNED)
    participant P as ClaudeCodeProvider
    participant BC as build_command()
    participant Sub as subprocess.run (claude -p)
    participant PR as parse_result()

    Caller->>P: run_role(role_prompt, repo, profile)
    P->>BC: build_command(role_prompt, profile)
    BC-->>P: argv list (claude -p … --output-format json)
    Note over P,Sub: list argv, never shell=True (injection-safe)
    P->>Sub: subprocess.run(argv, cwd=repo, check=True, text=True)
    Sub-->>P: stdout (JSON result)
    P->>PR: parse_result(stdout)
    PR-->>P: RoleResult (Pydantic; unknown fields ignored)
    P-->>Caller: RoleResult
```

Testability map:

| Piece | Pure? | Unit-tested? |
| --- | --- | --- |
| `build_command(role_prompt, profile)` | yes | yes — argv includes headless JSON + profile perms |
| `subprocess.run(...)` | no (spawns `claude`) | **no** — exercised only in the P6 dogfood |
| `parse_result(stdout)` | yes | yes — parses the JSON fields, tolerates extra keys |

`FakeProvider.run_role` short-circuits the whole diagram: it returns a scripted `RoleResult` and spawns
nothing — this is what the driver's tests use.

## Planned — the build-spine loop (P5)

The driver is deterministic control flow with **no LLM**. Advance is **detected, not trusted**: a phase
only advances when a new commit landed **and** the plan's `current_phase` moved. Everything it reads
comes from disk, so resume is free.

```mermaid
flowchart TD
    start(["run(repo, provider, gate)"]) --> read["read_plan_state(...)<br/>(disk: plan + git)  — P4"]
    read --> spawn["provider.run_role(coder prompt, repo, profile)  — P2"]
    spawn --> rungate["gate.run_gate(repo)<br/>(orchestrator runs it)  — P3"]
    rungate --> check{"gate green<br/>AND advance detected?<br/>(new commit + current_phase moved)"}
    check -- yes --> more{"more phases?"}
    more -- yes --> read
    more -- no --> done(["plan complete"])
    check -- no --> halt["write HALT contract<br/>(state + reason) to disk"]
    halt --> stop(["halt — resume re-reads state from disk"])

    classDef planned fill:#fdebd0,stroke:#b9770e,color:#000;
    class read,rungate,check,halt planned;
```

Halt conditions (P5): a HALT report from the coder, a non-advancing phase (gate green but no
commit / `current_phase` didn't move), or a persistently-red gate.

## Planned — the gate runner (P3)

The orchestrator runs the **target's** gate itself so it can't be gamed. The command list is **read from
the target** (language-neutral: a Python target and a JS target differ only in config, not in
orchestrator code). It runs the commands in order and **stops at the first failure**.

```mermaid
sequenceDiagram
    participant Dr as driver (PLANNED P5)
    participant G as gate runner (PLANNED P3)
    participant Cfg as target gate config
    participant Cmd as gate commands (ruff / ty / pytest / …)

    Dr->>G: run_gate(repo)
    G->>Cfg: read ordered command list from target
    Cfg-->>G: [cmd1, cmd2, …]
    loop each command, in order
        G->>Cmd: run in repo
        Cmd-->>G: exit code + output
        Note over G: stop at first non-zero
    end
    G-->>Dr: GateResult (passed + which step + output)
```

## The state-on-disk backbone (why resume is free)

Every arrow that crosses a role/phase boundary is mediated by **files on disk**, never in-memory state:

- the **target plan** (frontmatter `current_phase` + progress ledger) — read by `state.py` (P4);
- **git** (did a new commit land?) — read by the driver (P5);
- the **HALT contract** the coder writes on genuine ambiguity — read on resume (P5);
- the framework's own **`CHANGELOG.md`** + per-phase commits — the resumable record of what shipped.

Because the loop keeps nothing in memory, a crashed or compacted run resumes by simply re-reading disk.
