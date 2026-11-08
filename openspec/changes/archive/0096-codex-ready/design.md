# Codex ready — design

How a Codex worker starts isolated, logs JSON, refuses a swapped root and is proved by a checker. **Verdict:** settled; build
the phases in order.

## Context

What the run does with Codex today, at `754ba66`; `C` is `skills/mf-ship/scripts/conduct.py`.

- **F1. No station has run on Codex.** `grep -rl 'executor codex' .minions/runs` prints nothing, and
  `grep -l '^executor' .minions/changes/*/models.toml` prints nothing: every run and every models file is Claude's.
- **F2. The argv.** `argv`'s Codex branch (`C:2741-2767`) starts `codex exec -s workspace-write` with `-c` roots, no network,
  untrusted trees, and no `--ignore-user-config`, so a worker loads `~/.codex/config.toml`: on this Mac a model, an effort, the
  `pencil` and `node_repl` MCP servers and plugins. D51 accepts "a Codex worker starts the operator's `mcp_servers`, until a
  change sets them empty" (`docs/decisions.md:650-652`).
- **F3. The flags exist.** `codex exec --help` lists `--ignore-user-config` — "Do not load `$CODEX_HOME/config.toml`; auth
  still uses `CODEX_HOME`" — and `--json` — "Print events to stdout as JSONL".
- **F4. The log.** Codex logs are plain text. `denials` (`C:2871`), `usage_limit` (`C:2898`) and `mcp_started` (`C:2923`) read
  Claude's stream-json alone; 0050's D4 kept Codex plain because "its sandbox has no denial event".
- **F5. The events.** `openspec/changes/archive/0029-terse-skills/evidence/codex/mf-build_new.events.jsonl` holds a real
  `--json` run: `thread.started`, `turn.started`, `item.completed` and
  `{"type":"turn.completed","usage":{"input_tokens":30101,"cached_input_tokens":13184,…,"output_tokens":303,…}}`. No event names
  a model or a dollar figure.
- **F6. The cost readers.** `_spent` in `scripts/metrics/run.py:185` and `_results`/`_spent` in
  `skills/mf-review-metrics/scripts/review_metrics.py:566-612` read a Claude `result` event's `total_cost_usd`; a Codex log is a
  gap. `git grep -n -i 'per_million\|price' -- scripts skills` finds no price table.
- **F7. The swap.** `reach` (`C:2561`) says "no listed path can be swapped for a symlink by a worker"; card `0050·S7` shows
  `<primary>/.git`, a forged `/tmp` entry and any root a worker can move break that. `argv` checks `.git` alone (`C:2742`), and
  Codex's `/tmp` default stays a root: `git grep -n exclude_slash_tmp` prints nothing.
- **F8. The probe.** `Run.probe` (`C:4443`) has a sandboxed worker edit, commit and gate a scratch repo, per executor. No
  check proves a Codex worker loads the skills and writes a findings file to the contract.
- **F9. The tests.** No fake `codex` exists; the `fake` fixture sets `MF_SHIP_AGENT`, which `argv` returns before any Codex
  flag (`C:2704-2705`). Codex argv asserts sit in `test_a_worker_carries_the_allowlist_and_a_denial_is_named`; its exact
  slices hold from `-s workspace-write` up to `network_access=false`.

## Goals / Non-Goals

**Goals:** a Codex worker starts on MF's settings alone; its log reads as a Claude log does; a swapped root halts; the probe
proves a real checker; the gate proves each with a fake `codex`.

**Non-Goals:** the models line's hosts, the mailbox, the shadow round, the metrics page's headline numbers — `cross-model`'s;
Codex's own sandbox flaws, which the threat model's *Out of scope* holds.

The cut decided these under the brief's switch, each logged in the brief's `## Decisions`:

| id | decision | because |
|---|---|---|
| C1 | a Codex log's dollars are its `turn.completed` tokens priced by a new `skills/mf-review-metrics/prices.toml`, by the model its spawn line names; the table lands with no rows, and a model with no row is a cost gap naming it, its tokens still read | F5: `--json` carries tokens and no dollars, and F6: no price table exists; inventing list prices would record wrong numbers |
| C2 | this version's `THREAT_MODEL.md` names the host crossing it builds — a worker-written JSON log the conductor parses — and the closed swap window; the mailbox is named by `cross-model`, which builds it | a mailbox named before it exists is a stale claim |

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `--ignore-user-config` and `--json` on every Codex worker | X1 | a Codex profile MF writes |
| [D2](#d2) | `tests/fake_codex.py`, a fake `codex` on `PATH` | X1 | faking through `MF_SHIP_AGENT` |
| [D3](#d3) | A Codex denial and MCP call read from the events | X1 | no Codex denials |
| [D4](#d4) | A Codex usage limit read from a failed turn | X1 | — |
| [D5](#d5) | Each Codex worker log opens with a spawn line | X1 | the run log's spawn event |
| [D6](#d6) | A price table prices a Codex log, in both readers | X1, C1 | dollars left a gap |
| [D7](#d7) | A root that is a link halts the Codex spawn; no `/tmp` root | X7 | recording the limit alone |
| [D8](#d8) | The checker fixture | X1 | the 0042 fixture |
| [D9](#d9) | The checker probe passes on the contract, its verdict logged | X1 | judging the verdict |
| [D10](#d10) | D67; D47, D51 and the threat model amended | X7, X8, C2 | — |

### D1

`argv`'s Codex list gains `*("--ignore-user-config", "--json")` directly after `*("-s", "workspace-write")`, so the exact
slices of F9 hold. The model and effort stay the models file's `-m` and `-c model_reasoning_effort=`; absent, Codex's own
defaults, never the operator's. A comment cites this design's D1. Auth still reads `CODEX_HOME`, so a worker signs in as the
operator does.

### D2

`tests/fake_codex.py` stands in for `codex`:

- It appends its argv, as one JSON list a line, to `FAKE_CODEX_ARGV`, then changes to the directory after `-C`.
- It always hands the last argument, the prompt, to `_fake` of `tests/fake_worker.py`, loaded with `runpy`, so a probe or a
  station acts on disk, and records its call, as the fake worker does.
- It prints `--json` events: `{"type":"thread.started","thread_id":"fake"}`, then per `FAKE_CODEX_MODE`, then one
  `{"type":"turn.completed","usage":{"input_tokens":1000,"cached_input_tokens":400,"output_tokens":100}}`.
  `deny` adds an `item.completed` whose item is `{"type":"command_execution","command":"rm -rf ~/x","aggregated_output":"rm: ~/x:
  Operation not permitted","exit_code":1,"status":"failed"}`; `mcp` adds an `item.completed` whose item is
  `{"type":"mcp_tool_call","server":"pencil","tool":"draw","status":"completed"}`; `limit` prints
  `{"type":"turn.failed","error":{"message":"You've hit your usage limit. Try again at 5:50 PM."}}` in place of the turn and
  exits 1.

`tests/test_conduct.py` gains the `fake_codex` fixture, built on `fake`: it writes `bin/codex` under `tmp_path`, a `#!/bin/sh`
script that runs `sys.executable -S tests/fake_codex.py "$@"`, prepends `bin` to `PATH`, and sets `FAKE_CODEX_ARGV`. It returns
a setter, `fake_codex(mode, codex_mode="")`, that calls `fake(mode)` — so `FAKE_CALLS`, `FAKE_MODE` and `HOME` stand — then
deletes `MF_SHIP_AGENT` and sets `FAKE_CODEX_MODE`, and returns `fake`'s calls path. A test that uses it never calls `fake`
after, since `fake` sets `MF_SHIP_AGENT` again. The Codex `PATH` puts the system folders first; none holds a `codex`, so the
fake is found.

### D3

`denials` also reads each `item.completed` event whose item is a `command_execution` with a non-zero `exit_code` and an
`aggregated_output` holding `Operation not permitted`, the macOS sandbox's refusal, as `Bash(<command>)`. `mcp_started` also
reads each `item.started` or `item.completed` event whose item is an `mcp_tool_call`, naming its `server`:
`codex started an MCP server: pencil`. Its docstring's "A log with no `init` event, as Codex's, passes" goes. Each reader keeps
one pass over the log and tells the formats apart by the event's shape, never by an executor argument.

### D4

`usage_limit` also reads a `turn.failed` event's `error.message`, or an `error` event's `message`, holding `usage limit`, any
case. The reset is the text after `try again at ` or `try again in `, any case, up to a full stop or the end: the fake's
message gives ` · stopped by a usage limit · resets 5:50 PM`.

### D5

`Run.spawn`, for a Codex worker, writes one line to the log's descriptor before `work` starts it:
`{"type":"mf.spawn","executor":"codex","model":<model or null>,"effort":<effort or null>}`. A reader takes the log's first
line alone as its spawn line, so a worker that prints one later sets nothing. A Claude log keeps no spawn line: its `result`
event carries its own dollars.

### D6

`skills/mf-review-metrics/prices.toml` holds a `[models]` table of rows
`"<model>" = { input = <usd>, cached_input = <usd>, output = <usd> }`, US dollars per million tokens, and lands with no rows
under a comment naming that form and this design (C1). For a log with no `result` event and at least one `turn.completed`:

- **tokens** — the sum of each `turn.completed`'s `input_tokens` and `output_tokens`; `cached_input_tokens` is a part of
  `input_tokens`.
- **dollars** — over the same events, `(input − cached) × input + cached × cached_input + output × output`, over a million,
  at the row of the spawn line's model.
- **a gap** — no spawn line, a `null` model or no row: the dollars are a gap naming the model, `default` for `null`, and the
  tokens are read.

`PRICES`, in each reader, is a module constant holding the table's path, read when a Codex log is priced, never at import:

- **`scripts/metrics/run.py`** — `PRICES` is `skills/mf-review-metrics/prices.toml` under the repo root beside the script.
  `_spent` takes the Codex branch, and `Version.spent` raises the dollar gap only for the cost metrics, so `tokens` and
  `tokens-<stage>` read. `_reader` in `tests/test_metric_scripts.py` gains an optional `prices` path, set as the loaded
  module's `PRICES` when given.
- **`review_metrics.py`** — `PRICES` is `prices.toml` in its script's parent folder. `_results` also keeps a log's spawn line
  and its `turn.completed` events, so `read_<station>` counts a Codex log as read; `_spent` takes the Codex branch when its
  events hold no `result`, turns and seconds gaps. Its test sets the loaded module's `PRICES` to a table it writes.

### D7

`argv`'s Codex branch, after the `.git` check, calls a new `_unswapped(paths)`, over the common directory, each writable root
— a cutter's run directory and brief folder among them — and `cwd`. Each must be a folder by `os.lstat`, no link, and
`Path(path).resolve()` must equal it; the first that fails stops with 1:
`conduct: halt — the writable root <path> is a link or moved: a worker swapped it`. `reach` and `_common_dir` hand over
resolved paths, so a worktree swapped before `reach` runs fails `_points_back` and drops out of the roots, as today; the check
catches a swap between `reach` and the spawn, the version's own tree as `cwd`, and a cutter's unresolved folders. Its test
swaps the worktree `argv` gets as `cwd`, then a cutter's brief folder. A Stop in a version's thread halts
that version alone (`C:3838`). The list also gains `-c sandbox_workspace_write.exclude_slash_tmp=true`, beside
`exclude_tmpdir_env_var`, so a forged worktree entry under `/tmp` names no folder a Codex worker could make. `reach`'s
docstring says a listed path a worker swaps halts the next Codex spawn, and cites this design's D7. A swap after the check,
while Codex starts, is not caught: the threat model's *Known gaps* names it.

### D8

`checker_fixture(scratch)` in `C` builds the checker's scratch repo, on `main`, with `SCRATCH_IDENTITY`:

- **base commit** — `AGENTS.md`, `# Probe fixture`, and `total.py`, `def total(prices: list[float]) -> float:` returning
  `sum(prices)`;
- **change commit** — `openspec/changes/0001-probe/` with `proposal.md`, `design.md`, `tasks.md` and `specs/probe/spec.md`,
  whose requirement says `total` SHALL round its sum to cents, with the scenario `total([0.1, 0.2])` returns `0.3`; `total.py`
  gains a docstring and no rounding — the seeded defect;
- **the packet** — `.minions/changes/0001-probe/diff.patch`, `git diff <base> <head>`, and `.gitignore` naming `.minions/`.

It returns the base and head shas. `CHECKER_PROBE`, beside `PROBE`, is the prompt: "You are converge's conformance checker for
change 0001-probe in this directory. Load the mf-converge skill's references/generic-conformance.md and references/worker.md.
Judge the range {base}..{head}, its patch .minions/changes/0001-probe/diff.patch and openspec/changes/0001-probe/, and write
.minions/changes/0001-probe/conformance.md to the worker reference's findings file contract. Edit nothing else."

### D9

`Run.probe`, for `executor == "codex"`, adds the executor to `probed` only once its sandbox check passes and then
`probe_checker` passes. `probe_checker(executor, who)` spawns `<station>-checker` — `probe-codex-checker`, or
`probe-checker` on a Codex run — in a second `tempfile.mkdtemp` scratch, `.resolve()`d as the first is, so D7's check passes
it, built by `checker_fixture`, with the models `(executor, None, None)`, and removes the scratch after. Its test patches
`_unlinked` through the loaded module's globals, as other tests patch `_executor_missing`. `check_checker(scratch, log)` returns why it fails, else None:

- `conformance.md` is no regular file by `os.lstat` → `the checker wrote no conformance.md`;
- a key of `FINDINGS_KEYS` — `type`, `plan`, `project`, `branch`, `head`, `reviewed`, `round`, `open_blocking`, `verdict`, `mode`,
  `workers`, `model`, `packet` — missing from its frontmatter → `conformance.md lacks <key>`;
- `type` other than `conformance`, or `plan` other than `0001-probe` → naming the value;
- the log holds no `turn.completed` with `usage` → `codex's log holds no usage event`.

A pass's `check` event reads `<station> · pass · verdict <verdict>`: the verdict is shown and never judged, since a probe proves the
runtime, not a model's judgment. `mcp_started` runs over the checker's log too. `tests/fake_worker.py` answers the
prompt: a prompt holding `conformance checker for change 0001-probe` is the station `checker`, recorded as `checker`; it writes
`conformance.md` with every key, `verdict: changes-requested` and `open_blocking: 1`, and prints D2's `turn.completed` line,
save under `FAKE_MODE` `checker-silent`, where it writes nothing.

### D10

- **D67**, in `docs/decisions.md` after D51, in the *Repo conventions* group and the map's line:

### D67 · A Codex worker starts on MF's settings, logs JSON and is proved by a checker

**A Codex worker starts with `--ignore-user-config` and `--json`: the operator's Codex config sets nothing, and its log reads
as a Claude log does — denials, usage limit, tokens, and dollars priced by `skills/mf-review-metrics/prices.toml`. A writable
root that is a link halts the next Codex spawn, and no Codex worker has `/tmp`. A run's Codex probe, past its scratch edit,
runs one conformance checker on a fixture, passing on a findings file to the contract and a log with a usage event.**

- **Why:** no station had run on Codex; a worker loaded the operator's MCP servers and plugins, and its plain log read as
  nothing.
- **Accepts:** a priced cost only for a model the table holds · the checker's verdict unjudged · a swap after the check, while
  Codex starts.
- **Rejected:** an MF-written Codex profile · judging the checker's verdict · list prices written by the cut.

- **D51** — the body's "each run's probe proves a write out refused" gains ", and on Codex one checker"; the Accepts drop
  "a Codex worker starts the operator's `mcp_servers`, until a change sets them empty" and gain "a Codex worker loads no user
  config ([D67](#d67--a-codex-worker-starts-on-mfs-settings-logs-json-and-is-proved-by-a-checker))".
- **D47** — the *Executors* bullet's "One probe runs per executor" gains ", Codex's with a checker on a fixture".
- **`THREAT_MODEL.md`** — *Trust boundaries*: "A Codex worker still starts the operator's `mcp_servers`." becomes "A Codex worker
  starts with `--ignore-user-config`: the operator's Codex config starts nothing."; the mixed-run bullet gains "The conductor
  parses a Codex worker's JSON log, which the worker writes: a forged event misstates a denial, a limit or a cost, never a
  stage." *Known gaps*: `0050·S7` leaves the carded list; the `mcp_servers` bullet goes; the `0050·R11` bullet becomes "A
  worker that swaps a writable root for a link after the check that directly precedes a Codex spawn, and back, widens that
  worker's roots: whether Codex resolves a root once or per command is unproven (`0050·S7`, `0050·R11`)."
- **`skills/mf-ship/SKILL.md`** — "the probe proves a write out refused" gains "; a Codex probe then runs one checker on a
  fixture".

## Tests

The tests the change adds and extends, all at the unit and integration layer of `pytest`; no end-to-end test, so no engine
runs (`T1`).

| file | before | after | counted by |
|---|---|---|---|
| `tests/test_conduct.py` | 131 | 135 | `grep -c "^def test_" tests/test_conduct.py` |
| `tests/test_metric_scripts.py` | 15 | 15 | `grep -c "^def test_" tests/test_metric_scripts.py` |
| `tests/test_review_metrics.py` | 10 | 10 | `grep -c "^def test_" tests/test_review_metrics.py` |

- **Added:** `test_a_codex_worker_starts_on_mf_settings_alone` (D1, D2; integration, `conduct.py agent` over the fake),
  `test_a_codex_log_reads_as_json` (D3, D4; unit), `test_a_swapped_root_halts_a_codex_spawn` (D7; unit, `argv`),
  `test_the_codex_probe_runs_a_checker` (D8, D9; integration, `Run.probe` over the fake).
- **Extended:** `test_a_worker_carries_the_allowlist_and_a_denial_is_named` (`--ignore-user-config`, `--json`, `exclude_slash_tmp`),
  `test_a_station_runs_on_its_executor` (the spawn line; the checker call), `test_run_metrics_read_cost_and_review_yield` (a
  priced Codex log, a gap without a row), `test_run_logs_give_cost_turns_and_tokens_per_station` (a priced Codex cell).
- **Edited for the checker call:** each test whose exact call or spawn list holds a Codex probe that spawns —
  `test_a_new_executor_is_probed_mid_run` and `test_a_station_runs_on_its_executor` — gains the `checker` call after each
  `probe-codex`. `test_a_cut_halt_is_shown_and_rejoin_cuts_again` and `test_a_missing_skill_stops_a_run` halt their Codex probe
  before it spawns, and stay as they are.
- **Removed:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Codex's wording moves]** → the denial's `Operation not permitted` and the limit's `usage limit` are Codex's text, read
  from its events; a new wording reads as no denial and a bare exit. The probe cannot raise a limit; a person re-reads them
  after a Codex upgrade, as `THREAT_MODEL.md` already asks for the trust flags.
- **[The probe spends]** → one checker turn per run that names Codex, on Codex's default model; a run with no Codex station
  starts none.
- **[A flaky checker halts every Codex station]** → the probe judges the contract, never the verdict ([D9](#d9)); a model that
  writes no file is the halt this version wants.
- **[An empty price table]** → every Codex dollar figure is a gap until a person adds a row (C1); the tokens read meanwhile.
- **[The swap race]** → a check directly before the spawn narrows the window to Codex's start; it stays a named gap.

## Verdict

Settled: config isolation, JSON events, the swap window, then the probe and the record, each phase ending on a green
`make check`, the last on the gate.
