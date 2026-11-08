# Worker diet — design

How each worker starts smaller, reads less and prints less, and how the metrics show what it costs.
**Verdict:** settled; build the phases in order — the spawn, the context, tool output, the metrics, the record.

## Context

What the line does at `ed7298f`; `C` is `skills/mf-ship/scripts/conduct.py`. Each count is the command's output or the
ledger the brief measured (0096-codex-ready $31.96, 0097-cross-model $55.44).

- **F1. The spawn.** `argv` (`C:2961-3060`) takes no station. Its Claude branch passes `--model`, `--effort`,
  `--output-format stream-json --verbose`, `--add-dir` per tree, `--settings` from `worker_settings` (`C:2879-2901`, the
  `sandbox` key alone), `--setting-sources user`, `--strict-mcp-config` and `--allowedTools`/`--disallowedTools` from
  `allowlist` (`C:2857-2876`, `TOOLS` at `C:161` allowing `Agent` to every station). No `--tools`, no TTL variable, no
  `--exclude-dynamic-system-prompt-sections`. `Run.worker` (`C:3755-3813`) knows the station and drops it.
- **F2. What leaks in.** Through `--setting-sources user` every worker gets 27 tools, the operator's plugins, the Terse
  output style and auto-memory. A main worker's first turn is ~28.6k tokens; tools trimmed to 8 save ~3.8k, plugins,
  output style and auto-memory ~2.2k more; ~13.5k is written fresh per spawn by the dynamic sections.
- **F3. The installed CLI.** `claude --help` lists `--tools <tools...>` ("e.g. "Bash,Edit,Read"") and
  `--exclude-dynamic-system-prompt-sections`. The 2.1.312 binary holds `ENABLE_PROMPT_CACHING_1H`, `FORCE_PROMPT_CACHING_5M`,
  `enabledPlugins`, `outputStyle`, `autoMemoryEnabled` and the error text `No such tool available`.
- **F4. Cache TTL.** MF sets none. Main sessions wrote 1h in an sdk-ts run and 5m in an sdk-cli one; the 1h premium cost
  $2.19 / $3.42. Only waits on foreground subagents outlast 5 minutes — the cut's plan reviews 628–689 s, converge's
  fan-out 598–609 s, fixers 308–396 s; no gate ran over 151 s.
- **F5. Reach.** `reach` (`C:2817-2831`) takes every worktree `_worktrees` (`C:506-519`) lists, so released 0055, 0056 and
  0057 stay in `--add-dir` and the write list. `open_versions` (`C:541-561`) and `_cuts` (`C:5587`) already name what is
  live; `C:5782-5783` joins them.
- **F6. Halts and logs.** `denials` (`C:3207-3236`) matches `DENIALS` (`C:180`); `Run.spawn` (`C:3694-3723`) halts on a kill
  or a non-zero exit; `Run.judge` (`C:3815-3833`) shows `shown` after a pass. The probe spawns `probe` or `probe-<executor>`
  (`C:4932`, `C:4960`) and judges it at `C:4963-4968`.
- **F7. Mandatory context.** `AGENTS.md:14-18` makes cut, build and converge read the principles (12.9k chars), all of
  `docs/decisions.md` (58.7k chars, 55 decisions) and `THREAT_MODEL.md` (20.0k chars); build carried ~23.6k tokens of it
  for 206 turns. The same rule sits in `skills/mf-build/SKILL.md:12-18`, `skills/mf-cut-change/SKILL.md:18-22`,
  `skills/mf-converge/SKILL.md:15-16` and `skills/mf-bootstrap/templates/AGENTS.md.tmpl:12-13`. Conformance already reads
  the cited decisions and an index, from `bundle` in `skills/mf-converge/scripts/bundle.py:107-138`, which only writes a
  file. `scripts/metrics/reading_set.py:27-32` counts converge's reading set with the shared context.
- **F8. Models.** `_models` (`C:2241-2284`) gives `None` for a `[converge]` naming no model, so the operator's
  `effortLevel: xhigh` and default model apply; only the supervisor has a coded default, `SUPERVISOR` (`C:120`). The
  conductor ran Opus high: $2.94 / $2.93, 60 turns, 58.7k thinking tokens. The cut's default is "the conductor,
  `[converge]`, on the mid tier · medium, … the fixer on the mid tier · high" (`skills/mf-cut-change/SKILL.md:387-388`);
  `skills/mf-converge/SKILL.md:352-354` puts a blocking fixer on adversarial's model; verify follows Step 3's dispatch
  (`:413-417`).
- **F9. Stamps.** `stamp.py` (`skills/mf-converge/scripts/stamp.py:104-116`) takes one event; it ran 23 times a run, 20
  Bash-only turns, 25–30% of the conductor's cost. `C:762-771` reads the top line under the newest heading.
- **F10. Tool output.** `pyproject.toml:37` sets `addopts = ["--strict-markers"]`: long tracebacks; build's 31 pytest runs
  printed 63k chars. `gate_run.py:124` runs `subprocess.run(["make", "gate"])`, inheriting `VIRTUAL_ENV` from `uv run
  --script` — ~550 tokens of warnings a gate, ~12 gates a version — and streams all output; its last line is the summary
  `mf-release` reads (`openspec/specs/sdd/spec.md:547`). The bootstrap's templates hold no pytest config; its
  `CODING_STANDARDS.md.tmpl:18` names `--strict-markers`.
- **F11. Metrics.** `review_metrics.py`'s `STATIONS` (`:56`) lacks `cut` and `supervise`; per-station cost lives only in the
  HTML `cost_table` (`:1234`); nothing reads a first turn or a subagent's cost. `review-metrics.json` holds `generated`,
  `records`, `roles`, `shadow`, `escapes` and `headline` (`:1431-1436`). `model_table` (`:1245`) lost its median duration
  and tokens (`0097·R4`); `README.md:36` says "per model" (`0097·R3`). `run.py`'s `role_tokens`
  (`scripts/metrics/run.py:516-550`) already reads a subagent's usage by `task_started` and `parent_tool_use_id`.
  `prices.toml` holds no row. Repos come from the operator's config alone (`:152-174`), which names three of the four
  repos the conductor keeps state for under `~/.mf-ship-origin/`.
- **F12. The tests.** `grep -c "^def test_"` prints `140` for `tests/test_conduct.py`, `7` for `tests/test_gate_run.py`, `2`
  for `tests/test_stamp.py`, `2` for `tests/test_bundle.py`, `11` for `tests/test_review_metrics.py`, `15` for
  `tests/test_metric_scripts.py` and `21` for `tests/test_skills.py`.

## Goals / Non-Goals

**Goals:** the acceptance of the brief's item 1 — every Claude station's argv carries its tools, the settings off and the
dynamic-sections flag; the TTL per station; reach to live worktrees; a missing tool halts; the conductor on Sonnet high,
verify and the fixer at medium; `gate_run.py` quiet and without `VIRTUAL_ENV`; short tracebacks; the metrics per worker,
round, role and station with first-turn context; the probe's first turn reported; a green gate.

**Non-Goals:** the savings themselves, judged in the ledger over three versions after each diet ships; a Codex worker's
flags, which `--ignore-user-config` already trims; the cut-converge and build-per-phase diets.

The cut decided these under the brief's switch, each logged in the brief's `## Decisions`:

| id | decision | because |
|---|---|---|
| C1 | "every repo on the line" is every repo a run started in: `conduct.py run` records its primary in `~/.mf-ship-origin/repos`, and `review_metrics.py` reads it beside the config | the config named three of four repos with run state (F11), and the home folder is where the conductor already keeps per-repo state and no worker writes |
| C2 | "context at first write" is a log's first assistant turn: its input, cache-read and cache-write tokens; a Codex log's first `turn.completed` input tokens | that turn writes the prefix every later turn re-reads; it is the figure the brief's ~28.6k and the acceptance's 22k measure |
| C3 | the fixer runs at its own table's effort, `medium` when it names none, also when a blocking card puts it on adversarial's model; verify runs on its role's model at `medium` | T9 sets both at medium; the model rule for blockers stays D64's |
| C4 | "when a phase touches them" is when a task names `docs/principles.md` or `THREAT_MODEL.md`; the cut reads them when its brief's phases do | a reading rule the worker can check without judgment |
| C5 | a mailbox checker gets the build's tools; `conduct.py agent`, which names no station, keeps the host's tools and cache default | T17 lists no checker, and a checker writes its findings file; the escape drill's agent starts a subagent |
| C6 | a converge subagent's round is read from its Agent description, which converge writes `<role> round <N>`; a worker's dollars are priced by `prices.toml` rows, the operator's (D67), which gain `cache_write` and `cache_write_1h` for a Claude model; a subagent's tokens and dollars are a gap | a stream-json event names no round; D67 rejects list prices the cut writes; no event holds a subagent's final output count |

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | A tool table per station, and `--tools` | T6, T17 | `Agent` kept for every station |
| [D2](#d2) | Settings off and no dynamic sections | T6 | `--setting-sources` without `user` — T6 keeps the user settings and turns named parts off |
| [D3](#d3) | Cache TTL per station, by environment | T5 | 1h everywhere — build never waits past 5 minutes |
| [D4](#d4) | Reach to open versions and queued cuts | T6 | a list of stale ids |
| [D5](#d5) | A missing tool halts | T17 | a denial event alone |
| [D6](#d6) | The probe reports its first turn | T20, C2 | a failed probe over 22k — the number is a target, judged in the ledger |
| [D7](#d7) | Cited decisions and an index for cut and build; none for the conductor | T7, C4 | a decisions summary file |
| [D8](#d8) | The conductor on Sonnet high; verify and the fixer at medium | T9, C3 | a default per worker in `conduct.py` — it would rewrite every converge prompt |
| [D9](#d9) | One `stamp.py` call, several events | T9 | a batch file the conductor writes |
| [D10](#d10) | `gate_run.py` without `VIRTUAL_ENV`, quiet on green | T10 | the tail of make's output on green |
| [D11](#d11) | `--tb=short` | T10 | the flag in the `Makefile` — a gate change for a print setting |
| [D12](#d12) | The metrics per worker, round, role and station | T13, C1, C2, C6 | a second data file |
| [D13](#d13) | D69; D48, D50, D64 amended; the threat model, the principles and the README | T13 | — |

### D1

- **`STATION_TOOLS`** — a dict beside `argv`: `"cut"` and `"converge"` map to
  `("Bash", "Read", "Edit", "Write", "Glob", "Grep", "Skill", "Agent")`, `"probe"` to `("Bash", "Read")`. **`WORKER_TOOLS`**
  is `("Bash", "Read", "Edit", "Write", "Glob", "Grep", "Skill")`.
- **`tools_for(station)`** — a module function: a station starting `probe` takes `STATION_TOOLS["probe"]`; `cut` and
  `converge` their row; any other, `converge-<role>` mailbox checkers among them, `WORKER_TOOLS` (C5).
- **`argv`** gains a keyword `station: str | None = None`. On Claude, with a station, it passes
  `--tools <tools joined by ",">` after `--strict-mcp-config`. `Run.worker` passes `station=station` on each of its three
  calls. The docstring names this design's D1–D4.

### D2

- **`worker_settings`** returns `{"sandbox": …, "enabledPlugins": _plugins_off(), "outputStyle": "default",
  "autoMemoryEnabled": False}`.
- **`_plugins_off()`** reads `<CLAUDE_CONFIG_DIR, else ~/.claude>/settings.json`, and maps each key of its `enabledPlugins`
  to `False`; a missing or unreadable file, or no `enabledPlugins` object, gives `{}`. User settings merge under
  `--settings`, so each enabled plugin must be named to be turned off. `tests/conftest.py`'s home fixture also deletes
  `CLAUDE_CONFIG_DIR`, so no test reads the operator's.
- **`argv`** passes `--exclude-dynamic-system-prompt-sections` on every Claude worker, after `--strict-mcp-config`.

### D3

`CACHE_HOUR = ("cut", "converge")`. On Claude, with a station, `argv`'s environment gains, after `TMPDIR`,
`ENABLE_PROMPT_CACHING_1H=1` for a station of `CACHE_HOUR`, else `FORCE_PROMPT_CACHING_5M=1`. With no station, the prefix
is as now, so `test_no_hook_runs_in_a_worker`'s `HOOKS_OFF` slice holds. A subagent's cache is the host's: 5 minutes.

### D4

`reach(primary)` keeps `root` and each `_worktrees` path whose branch is in `{v.change for v in open_versions(root)}` or
`_cuts(root)`, skipping a path inside one taken, as now. A cutter's reach is unchanged: its `brief` branch of `argv` names
its own worktree. The spec's *A worker's reach stops at the repository* defines an open worktree so.

### D5

- **`MISSING = "No such tool available"`**; **`lacked(log)`** returns the name of each `tool_use` whose `tool_result`
  `is_error` and holds `MISSING`, read as `denials` reads a log.
- **`Run.spawn`** — after the timeout check and before the exit check, `lacked(out)` non-empty halts `who`:
  `<station> asked for a tool its station lacks: <names>`, and returns `None`.
- **`tests/fake_worker.py`** — under `FAKE_MODE` `missing-tool`, the build prints a `tool_use` of `Agent` and its
  `tool_result`, `No such tool available: Agent`, as its `deny` mode prints a denial.

### D6

**`first_turn(log)`** returns, of the first `assistant` event holding a `message.usage` object, its input, cache-read and
cache-write tokens summed; else the first `turn.completed` usage's `input_tokens`; else `None`. `Run.probe` passes `judge`
the `shown` ` · first turn <n> tokens` when it is not `None`, and none otherwise, so a probe's check line is as now. Under
`FAKE_MODE` `first-turn`, the fake probe in `tests/fake_worker.py` prints one `assistant` event whose usage holds 3 input,
15000 cache-read and 4000 cache-write tokens; no other mode prints one, so `test_a_new_executor_is_probed_mid_run`'s check
line holds.

### D7

- **`bundle.py --decisions <file>…`** — prints the `Decisions the change cites` and `Every decision` sections `bundle` writes,
  for the files given, and writes nothing; a file it cannot read → `bundle: cannot bundle — <why>`, exit 2. `bundle` and it
  share one function, `decisions_text(plan, decisions)`. The positional `change` and `bundle` stay, both or neither, and the
  usage line names both forms.
- **`AGENTS.md`'s *The record*** — the mandatory context is the coding standards and the contribution guide; every station
  but the cut, the build and the converge conductor also reads the principles and the decisions. The cut and the build read
  the index `skills/mf-converge/scripts/bundle.py --decisions` prints and, in full, the decisions their work cites or touches,
  and the principles and the threat model when a task names the file. The converge conductor reads none of it. The
  conformance and adversarial sentence stays.
- **`skills/mf-build/SKILL.md:12-18`** — the decisions clause becomes: run
  `uv run --script <this package>/../mf-converge/scripts/bundle.py --decisions openspec/changes/<change-id>/proposal.md
  openspec/changes/<change-id>/design.md openspec/changes/<change-id>/tasks.md` and read what it prints, and in full any
  other decision whose index line a phase touches; `ARCHITECTURE.md` and `docs/adr/*.md` whole; the principles and the
  threat model when a task names the file. The halt on breaking a decision in force stays.
- **`skills/mf-cut-change/SKILL.md:18-22`** — the same, `bundle.py --decisions <brief>` for a brief, the conversation's
  decisions read from the index otherwise, and the principles and the threat model when the source's phases name the file.
- **`skills/mf-converge/SKILL.md:15-16`** — "read root `AGENTS.md`, the mandatory context it names, and the change" becomes
  "read root `AGENTS.md` and the change — no other mandatory context: you judge nothing".
- **`skills/mf-bootstrap/templates/AGENTS.md.tmpl:12-13`** — "Before designing, building or reviewing, also read [the
  decisions in force](docs/decisions.md) and [the threat model](THREAT_MODEL.md)." becomes "The cut and the build read
  [the decisions](docs/decisions.md) their work cites, in full, and an index of the rest; converge's adversarial worker
  reads [the threat model](THREAT_MODEL.md), and the cut and the build when a task names it." Both links stay, so
  `_TEMPLATE_LINKS` in `tests/test_skills.py` holds.
- **`scripts/metrics/reading_set.py`** — `SETS["converge"]` becomes `("AGENTS.md", "skills/mf-converge/SKILL.md",
  "skills/mf-converge/references/worker.md")`; the docstring names this design's D7.
- **`tests/test_skills.py`** — `_METRICS_SCRIPTS` gains `("mf-build", "../mf-converge/scripts/bundle.py")` and
  `("mf-cut-change", "../mf-converge/scripts/bundle.py")`, and the expected lists of
  `test_the_metrics_script_scan_reports_a_missing_script` their `not named` lines.

### D8

- **`CONDUCTOR = ("claude-sonnet-5-5", "high")`** beside `SUPERVISOR`; `_models` gives it whole to `converge` on Claude
  when the table names neither a model nor an effort; a table naming either keeps what it names, the other `None`. The
  docstring names this design's D8. A Claude shadow checker takes converge's models through `_shadow`, so with no
  `[converge]` model it runs on `CONDUCTOR` too: 0097's C4 puts a shadow on converge's model.
- **`skills/mf-converge/SKILL.md`** — Step 6: the fixer runs "on `adversarial=`'s model when any card it is sent is blocking
  and adversarial is no mailbox role, else on `fix=`'s", gaining "always at the fixer's effort: `fix=`'s, `medium` when it
  names `default`". Step 7 gains "Each verify worker runs on its role's model at effort `medium`."
- **`skills/mf-cut-change/SKILL.md:387-388`** — "the conductor, `[converge]`, on the mid tier · medium" becomes "the
  conductor, `[converge]`, on Sonnet 5.5 · high, where the session offers it"; "the fixer on the mid tier · high" becomes
  "the fixer on the mid tier · medium".

### D9

`stamp.py`'s `event` takes `nargs="*"`: `main` passes the list to `stamp(text, events, run, mark)`, which inserts each under
the first `## Run` line in order, so the last given is on top, each with the clock's time, and returns the lines written;
`main` prints each. No event and no `--run`, or events with `--run`, is `USAGE`. The docstring shows the form
`stamp.py <log> '<event>' ['<event>' …]`. `skills/mf-converge/SKILL.md`'s *An event* bullet says several events with no
command between them go in one call, last on top, and Step 5 writes both `verdicts` lines in one call after both reads.

### D10

`gate_run.py` builds `env`, `os.environ` without `VIRTUAL_ENV`, and passes it to both `make -n gate` and `make gate`. `gate`
runs `make gate` with `stdout=PIPE, stderr=STDOUT, text=True, errors="replace"`. Red → write make's output to stdout, then
`gate: red — …`. Green → the summary line alone, as now. The module docstring names this design's D10. The summary stays the
last line, so `mf-release` reads its seconds as before.

### D11

`pyproject.toml`'s `addopts` becomes `["--strict-markers", "--tb=short"]`: both `Makefile` pytest lines take it, and
`make -n gate` does not change. The bootstrap's `CODING_STANDARDS.md.tmpl:18` "pytest with `--strict-markers`" becomes
"pytest with `--strict-markers` and `--tb=short`".

### D12

`skills/mf-review-metrics/scripts/review_metrics.py`:

- **Stations** — `STATIONS` gains `cut` and `supervise` before `*CHECKERS`. `_spent` gains `first`, `first_turn` of the log's
  events — the first `assistant` event holding a `usage` object, else `None` — so `_results` also keeps that event;
  `_cost_logs` records `first_<station>`, the first log's. `cost_table`'s cell gains ` · first <n>` when it is not `None`,
  and no suffix otherwise.
- **Workers** — `_converge_workers(repo, change)` reads each converge log through `_log_workers` — `_workers` (`:767`)
  already names a findings file's worker count: a `task_started` event's `tool_use_id` and description,
  `WORKER = re.compile(r"\b(conformance|adversarial|fix|verify)\b.*?\bround (\d+)\b", re.I)`; then the `assistant` events of
  that `parent_tool_use_id`: its model, its start and the first one's context. The CLI writes each with the usage its
  message's stream opened with and a placeholder output count, and no event holds a subagent's totals, so a subagent's
  tokens are a gap. Each mailbox checker's log is a worker too, its role from its station, its round a gap, its tokens its
  last `result` event's `usage` — the four `USAGE` kinds, the 5-minute and 1-hour split of `cache_creation` — or its
  `turn.completed` events' summed. A worker record holds `repo`, `change`, `role`, `round`, `run`, `model`, `tokens`,
  `first`, `dollars` and `source` (`subagent` or `mailbox`); its `run` is the status log's run whose window of its round
  holds its first event, else `None`.
- **Dollars** — `_priced_worker(row, usage)`: input × `input`, cache read × `cached_input`, 5-minute write × `cache_write`,
  1-hour write × `cache_write_1h`, output × `output`, over a million; no row, or a key a non-zero kind needs, → `None`; a
  worker with no tokens, every subagent among them, → `None`. `prices.toml`'s comment names the Claude keys.
- **The data** — `_priced_rounds` gives each `records` entry `dollars`: the workers' of its own run, round and role summed
  — an amend run restarts at round 1 — `None` when none or any is `None`. A subagent's dollars and a mailbox checker's
  round being gaps, a run's records hold `None` until an event holds a subagent's totals; Risks accepts it.
  `review-metrics.json` gains `workers` and `stations`, one per change and station from `_cost_logs`.
- **Repos** — `recorded()` returns `Path.home() / ".mf-ship-origin" / "repos"`, read at call time, as the tests' home is
  set after import; `settings` adds each line of it that names a folder holding `.minions/`, resolved, after the config's,
  each once; `--repo` reads no record. `conduct.py`'s `run` calls
  `_record_repo(primary)` after it takes the claim: it appends the resolved primary to that file, made `0o600`, when no line
  holds it; a home folder that refuses it records nothing, as `_mark_live` writes nothing there, so
  `test_a_request_at_a_runs_close_starts_the_next_run` holds.
- **The role table** (`0097·R4`) — `_role` records gain the change's `duration` and `tokens`; `model_table` gains
  `median duration (s)` and `median tokens` after `median workers`. `summary` prints the same.
- **Text** — `skills/mf-review-metrics/SKILL.md` names the cost per worker, the stations, first-turn context and the run's
  repo list in *Run* and *Report*; `README.md:36` "per model" → "per role, executor and model" (`0097·R3`).

### D13

- **D69**, in `docs/decisions.md` after D67, in *Repo conventions* and the map's line:

### D69 · A worker starts lean

**A Claude worker starts with its station's tools alone — the cut and converge `Agent` too, the probe `Bash` and `Read` —
with the operator's plugins, output style and auto-memory off and the dynamic prompt sections moved out, and reaches only the
worktrees of open versions and queued cuts. The cut and converge ask for the 1-hour cache, every other station the 5-minute
one. A tool its station lacks halts the version. The cut and the build read the decisions they cite and an index; the
converge conductor reads no mandatory context.**

- **Why:** a worker's first turn was ~28.6k tokens before any work, re-read every turn; build carried all 55 decisions for
  206 turns; only the cut's and converge's waits outlast 5 minutes.
- **Accepts:** a station that needs a new tool halts until its row changes · a decision the build does not cite is read by
  its index line alone.
- **Rejected:** `Agent` for every station · `--setting-sources` without user settings · 1h for every station.

- **D48** — "The cut designs within the decisions in force" gains ", reading those it cites and an index".
- **D50** — "the repos the operator's config names" gains ", and every repo a run started in"; "tables per repo and per role,
  executor and model" gains ", the cost per worker, round, role and station, with first-turn context".
- **D64** — "Converge's conductor runs on the mid tier · medium" becomes "Converge's conductor runs on Sonnet 5.5 · high";
  "and its fixer on the mid tier · high, on adversarial's model when a" becomes "and its fixer on the mid tier · medium, on
  adversarial's model, adversarial running on converge's host, when a" (`0097·R2`); the body gains "Verify runs at medium."
- **`THREAT_MODEL.md` *Trust boundaries*** — "It holds Bash and what Bash starts;" gains, before it, "A Claude worker has its
  station's tools alone, and the operator's plugins, output style and auto-memory start nothing."; "writes stay in the repo
  and its worktrees" becomes "writes stay in the repo and its open worktrees".
- **`docs/principles.md`, *The repo reaches nothing outside itself*** — the review-metrics item's "repos the operator names"
  gains " or a run started in"; the item opening "`conduct.py`'s record of `origin`'s URLs" gains, after "the offline base
  beside it", ", the list of repos a run started in, `repos`,".

## Tests

The tests the change adds and extends, all at the unit and integration layer of `pytest`; no end-to-end test, so no engine
runs (`T1`).

| file | before | after | counted by |
|---|---|---|---|
| `tests/test_conduct.py` | 140 | 144 | `grep -c "^def test_" tests/test_conduct.py` |
| `tests/test_gate_run.py` | 7 | 8 | `grep -c "^def test_" tests/test_gate_run.py` |
| `tests/test_stamp.py` | 2 | 2 | `grep -c "^def test_" tests/test_stamp.py` |
| `tests/test_bundle.py` | 2 | 3 | `grep -c "^def test_" tests/test_bundle.py` |
| `tests/test_review_metrics.py` | 11 | 13 | `grep -c "^def test_" tests/test_review_metrics.py` |
| `tests/test_metric_scripts.py` | 15 | 15 | `grep -c "^def test_" tests/test_metric_scripts.py` |
| `tests/test_skills.py` | 21 | 21 | `grep -c "^def test_" tests/test_skills.py` |

- **Added:** `test_every_station_starts_lean` (D1–D3; integration, `main run --executor claude` over `fake_codex`, with
  `_unlinked` and `_executor_missing` patched through `main`'s globals as `test_a_shadow_round_drives_no_fix` does, reading
  `FAKE_CLAUDE_ARGV`; unit, `argv`'s environment per station and `_plugins_off` over a planted `settings.json`), `test_reach_stops_at_live_worktrees` (D4; unit, a merged version's kept
  worktree and a queued cut's), `test_a_worker_asking_for_a_missing_tool_halts` (D5; integration over `fake`, `missing-tool`),
  `test_the_probe_reports_its_first_turn` (D6; integration over `fake`, and `first_turn` on a Codex log),
  `test_a_gate_runs_without_the_venv_and_quiet_when_green` (D10), `test_decisions_print_what_the_files_cite` (D7),
  `test_workers_are_priced_per_round_and_role` (D12, the spec's worker scenario) and `test_every_repo_a_run_started_in` (D12).
- **Extended:** `test_the_supervisor_runs_on_its_own_table` — the conductor's `CONDUCTOR` default on Claude and none on Codex
  (D8); `test_a_stamp_writes_the_clock_time_under_the_latest_run` — two events in one call, the last on top (D9);
  `test_a_log_out_of_shape_is_not_stamped` — events with `--run` refused (D9); `test_run_logs_give_cost_turns_and_tokens_per_station`
  — the `cut` and `supervise` cells and `first_<station>` (D12); `test_the_page_draws_charts_and_lists_gaps` — the role table's
  median duration and tokens (D12).
- **Edited:** `test_a_claude_worker_starts_in_the_sandbox` — the settings' three new keys, and
  `--exclude-dynamic-system-prompt-sections` before `--allowedTools` (D2); `test_a_station_runs_on_its_executor` and
  `test_the_plan_is_read_once` — each `argv` spy takes `**_`, so a `station=` keyword passes (D1);
  `test_codex_sessions_fill_the_rounds` — each expected record gains `dollars: None` (D12); `test_reading_sets_count_words` — `converge` counts `9` with both
  decisions files (D7); `_METRICS_SCRIPTS` and the expected lists of `test_the_metrics_script_scan_reports_a_missing_script`
  (D7).
- **Removed:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[A station's skill asks for a tool its row lacks]** → it halts naming the tool, never runs half-equipped; the rescue
  amends nothing here, the person edits the row. `mf-build`, `mf-simplify`, `mf-release`, `mf-rescue`, `mf-supervise` and
  `mf-integrate` start no subagent (`grep -n -i subagent` over them names none).
- **[The settings keys or TTL variables change in a later CLI]** → the probe's first-turn line shows it in every run; D69
  names the intent, not the variable.
- **[A plugin enabled outside `settings.json`]** → it still loads; the probe's first turn shows the cost.
- **[A quiet gate hides a slow step]** → `gate_run.py` prints the seconds, and a red gate prints everything.
- **[The conductor on Sonnet misreads a verdict]** → T9 reverts it on a halt traced to it; the models file can name Opus per
  version.
- **[A worker's dollars need a price row]** → a gap, never a zero, until the operator fills `prices.toml` (D67).
- **[No event holds a subagent's totals]** → its tokens and dollars are gaps, never a sum of the placeholder counts its
  assistant events carry, so a round and role's dollars are a gap too; a mailbox checker's dollars are priced, and the
  stations' cost holds converge whole.

## Verdict

Settled: the spawn, the context, tool output, the metrics, then the record, each phase ending on a green `make check`, the
last on the gate.
