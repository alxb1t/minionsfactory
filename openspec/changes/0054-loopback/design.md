# Loopback — design

How a repo opts its Claude workers into loopback, what that exposes, and how a run shows it. Verdict at the end: ready to
build.

## Context

Read at `57706ab` (v0.46.1). `conduct.py` is `skills/mf-ship/scripts/conduct.py`.

- isekai's readiness proof, 2026-11-02: `conduct.py agent --executor claude` ran `make gate` in a fresh worktree; 4 failed and
  29 errors, each `PermissionError` binding `127.0.0.1` — its browser tests' free-port probe, a unit test's probe, a
  `socketserver`.
- Measured 2026-11-02, a probe in a scratch repo through `argv`, binding a port, connecting to it, then calling Ollama at
  `127.0.0.1:11434`:

  | worker | bind | its own port | Ollama |
  |---|---|---|---|
  | Claude, as `argv` builds it | refused | refused | refused |
  | Claude, `allowLocalBinding: true` | ok | ok | reached |
  | Codex, as `argv` builds it | refused | refused | refused |

- Claude Code's [sandboxing docs](https://code.claude.com/docs/en/sandboxing), read 2026-11-02: on macOS `allowLocalBinding`
  lets a command "listen on network ports and connect to any port on localhost, which includes every other service listening
  there"; on Linux and WSL2 a command's localhost is private, and the flag has no effect. It takes no port list.
- Codex has no loopback switch but `network_access=true`, which opens every host.
- `ship_lines` reads `Ship tools:` and `Ship network:` (`conduct.py:1390-1402`) into `ShipLines` (`:147`); `read_plan` reads it
  once (`:1990-2003`); `_agents_values` reads backticked values only (`:312-322`). `worker_settings` builds the sandbox
  (`:1427-1446`). `argv` starts each executor through `env` (`:1474`, `:1494`), so the conductor's `VIRTUAL_ENV` reaches every
  worker, which warns that it does not match `.venv`.
- D15 says "The anchors always block" (`docs/decisions.md:176`), and `skills/mf-converge/SKILL.md` now has the accepted-class
  exception (`0053·R1`). `_codex_config` returns `bool(twin) and not loaded`, ignoring `written` (`tests/escape_drill.py:347`,
  `0053·R2`).

## Goals / Non-Goals

**Goals:** a repo that opts in runs a loopback gate under a Claude worker; the exposure is stated and shown in each run's log;
workers stop inheriting `VIRTUAL_ENV`.

**Non-Goals:** loopback for Codex; a port allowlist; a container.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `- **Ship loopback:** yes` turns on `allowLocalBinding` for Claude workers | the flag has no port list; the person opts in per repo | always on: it hides the exposure from every repo |
| [D2](#d2) | A Codex station under it halts its version | measured: Codex cannot bind with its network off | turning Codex's network on |
| [D3](#d3) | A `loopback` event per listener at run start | the exposure seen, with no manual step | halting on a listener: a recurring manual step |
| [D4](#d4) | `env -u VIRTUAL_ENV` | the conductor's environment means nothing to a worker | — |
| [D5](#d5) | The record: D51, D15, `THREAT_MODEL.md`, `mf-ship` Step 3 | A7; `0053·R1` | the bootstrap template opting in |
| [D6](#d6) | The drill: a loopback row; a written trust entry fails it | the fake worker holds no sandbox; `0053·R2` | — |
| [D7](#d7) | Built by hand | the drill runs real workers, which a sandboxed worker cannot start | `/mf-ship` |

### D1

`ShipLines` gains a third field, `loopback: bool`. `ship_lines` reads it with `_agents_flag(primary, "Ship loopback")`: the text
after `**Ship loopback:**`, up to an optional ` — `, stripped. Absent → `False`; `yes` → `True`; anything else →
`Stop(1, "conduct: halt — AGENTS.md: Ship loopback <value!r> is not yes")`.

`worker_settings` takes `loopback`, and adds `"allowLocalBinding": True` to `network` when it is true; the key is absent
otherwise. `argv` passes it from `lines`, and `conduct.py agent` reads it from `AGENTS.md`, as it reads `Ship network:`.

### D2

`read_plan`, when `self.lines.loopback` is true, keeps a version whose plan names `codex` for any station out of the plan, as
it keeps a refused table out, and records the station. `take` halts that version before its first worker:
`Stop(1, "conduct: halt — AGENTS.md: Ship loopback needs Claude workers: <station> names codex")`. A run whose own executor is
`codex` in such a repo halts the run with the same text, naming `the run`. `conduct.py agent` is unchanged: a person's tool.

### D3

`_loopback_listeners()` runs `lsof -nP -iTCP -sTCP:LISTEN` and returns each `(process, address)` whose address is on
`127.0.0.0/8`, `[::1]` or `*`, once each. `lsof` failing → one entry, `("lsof", "unavailable")`. `Run.ship`, after
`read_plan`, when `self.lines.loopback` is true, logs `self.log.event("run", "loopback", f"{process} {address}")` per entry.
`EVENTS` gains `loopback`. Nothing halts.

`lsof` without root names the operator's processes alone, so a root daemon's listener, Tailscale's on the measuring machine,
goes unlogged, and the record says so. `netstat -anv -p tcp` names every owner's listener, but measured 2026-11-02 it printed
every TCP socket under Apple's `/usr/bin/python3` and none under Homebrew's or the repo's `.venv` Python: under `conduct.py`'s
`uv` Python it would log nothing (converge round 1, `R1`).

### D4

Both executors' `env` prefixes become `("env", "-u", "VIRTUAL_ENV", *HOOKS_OFF, cache)` and the Codex one keeps its `path`.

### D5

- **D51**, *Accepts*: after "a domain `Ship network:` lists", add "· in a repo whose `AGENTS.md` declares `Ship loopback: yes`,
  a Claude worker reaches every service on the Mac's loopback; on Linux the flag does nothing". Its rule: "its scripts reach
  no unlisted domain" gains ", save through a local service where a repo opts into loopback" (converge round 1, `S1`).
- **D15**: after "- **The anchors always block:** data loss, spend, exposure of personal data or secrets, silent wrong
  output.", add "Save one class: a route in a class the threat model's *Out of scope* accepts by name is carded, anchors
  included." (`0053·R1`).
- **`THREAT_MODEL.md`**, *Entry points*: "`Ship tools:` and `Ship network:` lines" → "`Ship tools:`, `Ship network:` and
  `Ship loopback:` lines". *Trust boundaries*: "network on a short list" → "network on a short list and loopback only where a
  repo opts in". *Out of scope* gains the class by name, so D15 cards a route in it (converge round 1, `S1`):
  "**A loopback repo's local services.** In a repo that declares `Ship loopback: yes`, a Claude worker reaches every service
  listening on the Mac's loopback, and an unauthenticated one acts for it outside the sandbox: one that fetches what it is
  asked, a model pull or a dev proxy, carries what the worker reads past the domain list. The person accepts this class per
  repo, by declaring the line (D51); a route in it is carded, anchors included. Each run logs what the operator's own
  processes listen on there: `lsof` without root names no other user's, so a root daemon's listener goes unlogged. A Linux
  container, where loopback is private, is the way out."
- **`skills/mf-ship/SKILL.md`** Step 3, after "`conduct.py` holds the push.": "In a repo that declares `Ship loopback: yes`,
  its Claude workers reach every service on the Mac's loopback, and the run's log names those the operator's own processes
  hold; a root daemon's goes unlogged."

### D6

`tests/escape_drill.py`:

- A **loopback row**: in a scratch repo whose `AGENTS.md` declares `Ship loopback: yes`, a Claude worker through `argv` runs a
  script that binds `127.0.0.1`, listens, and connects to its own port. It prints `claude loopback: bound` when both succeed,
  else `claude loopback: failed — <reason>`, and `main` needs it.
- **`0053·R2`**: the Codex step's result moves into `_codex_held(twin, loaded, written)`, true only for a loaded twin, an
  unloaded plant and no written entry; `_codex_config` returns it.

`tests/test_escape_drill.py` loads the drill with `runpy` and asserts `_codex_held` on each case, a written entry among them.

### D7

Built by hand, in a session with network: `/mf-build`, `/mf-converge`, `/mf-release`. Not `/mf-ship`. After the release, the
person re-runs isekai's proof in `../try-sandbox`; that run is outside this change.

## Tests

Counted at `57706ab`: `uv run pytest --collect-only -q | tail -1` prints `99 tests collected`. All below are unit or
integration tests; none is end-to-end, and none runs on an engine.

| test | change | holds |
|---|---|---|
| `test_a_claude_worker_starts_in_the_sandbox` | edited | D1: a repo with the line gives `allowLocalBinding: true`, one without has no key, `Ship loopback: maybe` halts; D4: neither executor's command sets `VIRTUAL_ENV` |
| `test_the_plan_is_read_once` | edited | D2: a Codex station in a loopback repo halts its version and the other goes on; D3: the run's log holds a `loopback` event per listener from a fake `lsof` on `PATH`, and none without the line |
| `test_codex_held` in `tests/test_escape_drill.py` | added | D6: `_codex_held` is false when the twin did not load, the plant loaded, or an entry was written |

Each guard's twin is a step in its own test, per `T6`. None is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- **A loopback repo's workers reach every local service on the Mac**, Ollama, Docker and Redis among them on the measuring
  machine, and one that fetches a URL carries what a worker read past the domain list. Stated in D51 and accepted by name in
  `THREAT_MODEL.md`'s *Out of scope*, and the operator's own listeners logged per run.
- **`lsof`'s output can change across macOS releases.** A parse failure logs `lsof unavailable`, so the run goes on.
- **Linux**: the flag does nothing there, and loopback is already private.

## Verdict

Ready to build.
