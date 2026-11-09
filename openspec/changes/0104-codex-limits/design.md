# Codex limits — design

How a Codex usage limit stops neither the run nor a converge, and how a Codex spawn's quota is recorded.
**Verdict:** settled; build the phases in order — the limit data, the probe, the mailbox fallback, the record, the linked
worktree, the request id and the record of decisions, then the person's real-Codex check.

## Context

What the line holds at `048246b`. `c:` is `skills/mf-ship/scripts/conduct.py`, `t:` is `tests/test_conduct.py`,
`V` is `skills/mf-converge/SKILL.md`. The facts are the brief's, re-read at `048246b`; the cut's notes hold each answer.

- **F1. The probe.** `Run.executors` (c:4831-4835) probes every executor any plan names, shadows included
  (`named`, c:4814-4829). The start loop (c:5475-5480) runs `self.probe(executor)` and stops on any halt; a halt on `run`
  stops every version (`stopped`, c:3753-3756), and threads start only when no halt stands (c:5481). A probe's failed spawn
  halts through `spawn` (c:3870-3872), which names `usage_limit(out)`. Run 20261108-200117 halted whole on
  `probe-codex-checker worker exit 1 · stopped by a usage limit · resets 8:40 PM`, a Claude-only version included.
- **F2. A joining version.** `admit` (c:5043-5058) calls `probe_for(change, self.named(change))` (c:5060-5080), which
  probes once, halts `change` on a refusal and stores it in `self.refused` from the change's last halt. `take_cut`
  (c:4891-4905) probes a cutter's executor the same way. No function tells a version's station executors from its checkers'.
- **F3. A mailbox checker.** `Run.checker` (c:3890-3903) takes models from `self.plan`, spawns through `self.worker`, and
  answers `_answer(code, killed, models, usage_limit(out))` (c:2795-2809): `exit 1 · … · stopped by a usage limit · resets …`.
  `V:136-137` reads exit 1 as a worker that failed; Step 5 then halts on the missing findings file, and the rescue runs
  (`Run.rescue`, c:3997-4015; its callers c:4342 and c:4437, each then `supervise`), though D53 (`docs/decisions.md:760-761`)
  gives a usage limit none. `_converge_halt` (c:897-900) reads the newest converge run's top `halt` line.
- **F4. The limit data.** `usage_limit` (c:3379-3406) and `_codex_limit` (c:3364-3376) read the `try again at` text, a wall
  clock with no date. A Codex `--json` log has no `rate_limits`; Codex's rollout,
  `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-…-<thread_id>.jsonl`, holds `payload.type == "token_count"` events whose
  `payload.rate_limits` has `primary` and `secondary`, each `used_percent`, `window_minutes` and `resets_at` (epoch
  seconds). The log's first `thread.started` names `thread_id`; `conduct.py` reads neither. `review_metrics.py` already
  resolves `CODEX_HOME` (`skills/mf-review-metrics/scripts/review_metrics.py:576-577`) and reads `token_count` under
  `payload` (`:551-552`).
- **F5. A fallback is cheap to place.** `_shadow(converge, checker)` (c:2331-2345) gives a Codex checker
  `("claude", converge's model, converge's effort)` when converge runs on Claude; a Claude worker already runs through
  the mailbox as a shadow.
- **F6. A wait is not.** No sleep-until exists. `work` (c:3162-3213) checks converge's `deadline` (c:3190) only between
  `between()` calls, and a served checker gets its own full `TIMEOUT` (c:3207): debt `0097·S2`. The converge conductor
  re-runs `checker --wait` each `CHECKER_WAIT` (c:66).
- **F7. The record.** `_answer` carries no tokens; a Codex log names no model, so `Run.worker` writes an `mf.spawn` line
  first (c:3943-3952). The findings frontmatter (`skills/mf-converge/references/worker.md:39-54`) has no `tokens` key, and
  `FINDINGS_KEYS` (c:256-259) is the probe's contract. `scripts/metrics/run.py`'s `_spent` (`:226-243`) raises a gap on a
  log with neither a `result` nor a `turn.completed` — a Codex worker stopped before its first turn. `prices.toml` has no
  row (`skills/mf-review-metrics/prices.toml:7`); `_priced_worker` (`review_metrics.py:937-948`) prices a converge worker by
  its row. The operator's ledger holds prices fitted 2026-11-07 that reproduce every `costUSD`.
- **F8. Pricing Codex.** D67 rejects list prices written by the cut (`docs/decisions.md:728`). Codex is plan quota here:
  0098 took 30% of a Plus 5-hour window.
- **F9. The linked worktree.** `argv`'s Codex roots are the common directory, `reach`'s trees, a brief's folder and the
  mailbox (c:3088-3093), checked by `_unswapped` (c:2996-3012) and passed as
  `sandbox_workspace_write.writable_roots` (c:3110). Codex's sandbox leaves a gitdir a `.git` pointer names read-only even
  inside a writable root: voice-receptionist-poc run 20261108-204402 halted at its converge gate on
  `.git/worktrees/0003-turn-speed/index.lock`; the person reproduced it, and the extra root fixed it. `_config_held`
  (c:1354-1361) lists `local` and `worktree` scopes through git, which reads a linked tree's `config.worktree` only under
  `extensions.worktreeConfig`. The probe's scratch repo is a plain one (c:5099-5115).
- **F10. The mailbox's debt.** `0097·S3`: `checker` (c:6244-6282) places `<role>.request` (c:6267) and polls
  `<role>.answer` (c:6269) with no unlink first, and a request carries no id (`serve_requests`, c:2761-2792). `0097·S6`:
  `THREAT_MODEL.md:80-84` says a forged request "spends at most that", while it can also hold its spawn past `TIMEOUT`
  (S2) and halt the run (`0097·S4`, open).
- **F11. The tests.** No test runs a usage limit through a probe or a mailbox checker; `tests/fake_codex.py`'s `limit` mode
  (`:49-51`) prints the failed turn after the worker's work. `t:` has no fixture isolating `CODEX_HOME`, which
  `tests/test_review_metrics.py:31-34` has.

## Goals / Non-Goals

**Goals:** the brief's acceptance — a probe stopped by a limit logs `codex limited until <time>` and the run goes on, a
Claude-only version and a checker version taken and a Codex-station version halted alone; a limited mailbox checker re-run
on Claude with converge's model and effort, its answer naming the fallback; a 92% window sending a checker to Claude with
no Codex spawn, and a reset ten minutes away waited for, then Codex; the reset read by `thread_id`; findings stamped with
the plan's model and the log's tokens; quota shares in the run metrics; Claude rows in `prices.toml`; no rescue for a
limit halt; an answer tied to its request; the gitdir root, the `config.worktree` refusal and the probe's `git write-tree`;
a green gate.

**Non-Goals:** a Codex station's own fallback; dollar prices for Codex; a usage subcommand; `0097·S4`, `R5`, `R6`, `S5`.

The cut decided these under the brief's switch, each logged in the brief's `## Decisions`:

| id | decision | because |
|---|---|---|
| C10 | Codex limited at the probe is probed again in the mailbox before its first checker past the reset; that probe failing on anything but a limit halts the version, as a live probe does | D51 and D47 run no Codex worker its run never probed |
| C11 | a primary window at 90% or more is a limit until its `resets_at`, so C3's wait rule applies to it too | the acceptance sends a 92% window to Claude and waits on a reset ten minutes away: one rule reads both |
| C12 | a shadow on Codex does not fall back: limited, it answers exit 1 naming the limit, starting no worker | a Claude shadow would repeat the Claude checker; a shadow that exited 1 already halts nothing (`V:157-158`) |
| C13 | every folder directly under `<common>/worktrees/` is a Codex root, a link left out, not only the gitdir a root's `.git` file names | the probe's linked tree sits inside its scratch primary, whose `.git` names none; each folder is inside `common`, already a root |
| C14 | the real-Codex check is a `slow` test skipped unless `MF_REAL_CODEX=1`, run by the person in a last `**HUMAN` phase | no worker sandbox starts Codex's own seatbelt, and the build holds no Codex login |
| C15 | "the metrics price a Claude spawn" is the review metrics' worker pricing from the real `prices.toml`; `run.py` keeps a Claude log's `total_cost_usd` | the fitted rows reproduce `costUSD`; a subagent worker has no `result` of its own |
| C16 | the answer adds ` · tokens <n>` and ` · request <id>`; the findings gain an optional `tokens:` key; `run.py` counts a Codex log with no `turn.completed` as no tokens and no dollars | `V:91` takes the mailbox role's figures from its answer; a limited Codex attempt leaves such a log beside its Claude re-run |
| C17 | `V` has converge halt on a mailbox answer naming `stopped by a usage limit`, its `halt` line naming it | C5's no-rescue rule needs the halt to name the limit |

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | The limit data: rollout by `thread_id`, windows, reset, headroom | C4 | a usage subcommand — Codex CLI 0.163.0 has none |
| [D2](#d2) | The probe: a limit is no refusal; station versions halt alone | C1, C10 | halting the run — F1 |
| [D3](#d3) | The mailbox fallback, the wait and converge's remaining time | C2, C3, C11, C12, `0097·S2` | a wait until any reset — F6 |
| [D4](#d4) | No rescue and no supervisor for a limit halt | C5, C17 | the conductor telling a limit from a failure |
| [D5](#d5) | The record: answer, findings stamp, quota line, run metrics, Claude prices | C6, C7, C15, C16 | Codex dollars — F8 |
| [D6](#d6) | The linked worktree's gitdir, `config.worktree`, the probe's `git write-tree` | C9, C13, C14 | the gitdir from the cwd's `.git` alone — C13 |
| [D7](#d7) | An answer names its request | `0097·S3` | dropping a second request per role — a resend after a kill is the case |
| [D8](#d8) | D76; D47, D51, D53, D67, D68; the threat model; the skills | C8, `0097·S6` | — |

### D1

New in c:, beside `usage_limit`:

- **`LIMIT_WAIT = 900`**, **`HEADROOM = 90`** and **`FALLBACK = "fallback: codex usage limit"`**, by `CHECKER_WAIT`, with
  a comment naming this design.
- **`class Window(NamedTuple)`** — `used: float`, `resets: float`, the epoch seconds `resets_at` names.
- **`_codex_home() -> Path`** — `Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")`.
- **`_thread_id(log: Path) -> str | None`** — the first `thread.started` event's `thread_id`, when it fullmatches
  `[0-9A-Za-z-]+`; else None. The log is worker-written: the pattern keeps a glob out.
- **`_rollout(thread: str | None) -> Path | None`** — with a thread, the one file
  `_codex_home() / "sessions"` globs as `*/*/*/rollout-*-<thread>.jsonl`; with None, the newest by `st_mtime` of
  `*/*/*/rollout-*.jsonl`; None when none is a regular file.
- **`_windows(rollout: Path | None) -> dict[str, Window]`** — the last event whose `payload.type` is `token_count` and whose
  `payload.rate_limits` is an object: each of `primary` and `secondary` whose `used_percent` and `resets_at` are numbers;
  `{}` for none, an unreadable file or None.
- **`_next_clock(text: str, now: float) -> float | None`** — a `try again at` time, `5:50 PM` by `%I:%M %p`, as the
  epoch of its next local occurrence after `now`; None when it does not parse.
- **`_reset_at(log: Path, now: float) -> float`** — from `_windows(_rollout(_thread_id(log)))`: the latest `resets` of the
  windows at `used >= 100`, else of the window most used; else `_next_clock` of `usage_limit`'s text; else `math.inf`.
- **`_headroom(now: float) -> float | None`** — the newest rollout's `primary` window's `resets` when `used >= HEADROOM`
  and `resets > now`; else None.

The test, `test_the_codex_limit_data_is_read_from_its_rollout`, writes a rollout under a `tmp_path` `CODEX_HOME`. An
autouse fixture `_no_codex_sessions` in t: points `CODEX_HOME` at an empty folder, as `tests/test_review_metrics.py:31-34`
does, so no test reads the operator's sessions.

### D2

- **`Run.limited: dict[str, float]`** — an executor's reset, set in `__init__` beside `self.refused`.
- **`Run.limit(executor: str, log: Path) -> None`** — stores `_reset_at(log, time.time())`, then logs
  `self.log.event("run", "limited", f"{executor} limited until {when}")`, `when` the reset as local `%Y-%m-%d %H:%M`, or
  `a reset it did not name` for `math.inf`. `"limited"` joins `EVENTS`.
- **`Run.limited_until(executor: str) -> float | None`** — the stored reset while it is ahead of `time.time()`; a passed one
  is dropped and gives None.
- **`Run.limited_reason(executor: str) -> str`** — `f"{station} — {executor} limited until {when}"`, `station` named as
  `probe` names it.
- **`Run.worker`** — after a Codex worker exits non-zero and `usage_limit(out)` is not empty, calls `self.limit("codex", out)`.
- **`Run.spawn(..., limits: bool = False)`** — with `limits`, a non-zero exit while `self.limited_until(models[0])` holds
  halts nothing and returns None. `probe` and `probe_checker` pass `limits=True`; a limited probe leaves the executor
  unprobed, with no halt.
- **`Run.on_stations(change: str) -> list[str]`** — the executors of the change's planned tables in `PLANNED` save
  `converge.conformance` and `converge.adversarial`.
- **`probe_for(change, executors, stations)`** — a third parameter, the executors whose limit halts `change`: `admit`
  passes `self.on_stations(change)`, `take_cut` the cutter's executor. An executor with a limit holding is not probed, and
  a limit its probe records counts the same: it halts `change` with `limited_reason` when the executor is in `stations`,
  and is passed over otherwise. Only a probe that ends with no limit and no pass stores `self.refused`.
- **`Run.hold_limited(changes: list[str], cuts: list[str]) -> set[str]`** — after the start loop, with no halt on
  `run`: halts each planned change whose `on_stations` names a limited executor by `self.halt(change, reason)`, and each
  queued cut whose executor is limited by `cut_halted(change, reason, False)`, `reason` being `limited_reason`; returns
  the cuts it halted. `test_a_usage_limit_at_the_probe_is_no_refusal` also takes a joining version through `probe_for`
  while the limit holds: one whose `[build]` names Codex halts with no probe, a checker-only one goes on.
- **The start** (c:5475-5481) — `held = bool(self.halts)` is read after the probe loop and before `hold_limited`; threads
  start when neither `held` nor `self.blocked`, and no cut thread starts for a cut `hold_limited` returned.
- **`take`** — returns at once when `self.stopped(version.change)`, before `catch_up`: a version `hold_limited` halted
  merges nothing, and its dependants block as on any halt.

### D3

- **Converge's time (`0097·S2`)** — `work` and `Run.worker` gain `timeout: float | None = None`, `None` read as the global
  `TIMEOUT` at call time, which `test_run_halts_on_a_timeout` sets; `work` uses it for its `deadline` and `worker.wait`.
  `Run.worker` calls `work` as now when it is None, with `timeout=timeout` otherwise, as it already branches on
  `between`: test stand-ins of `work` keep their arguments.
  `Run.spawn` computes `deadline = time.monotonic() + TIMEOUT` and passes it to `Run.server(who, cwd, mailbox, deadline)`,
  which passes it to `self.checker(who, role, cwd, text, deadline)`.
- **The refusal** — `Run.checker`, once `deadline` has passed, answers `exit 1 · refused: converge's time is spent`,
  spawning nothing; else each run it spawns gets `timeout=deadline - time.monotonic()`. 3.1's test drives `work` with a
  short `timeout`, and `Run.checker` on a `Run` twice: with a passed deadline, and with one a moment ahead over a checker
  that sleeps, whose answer names `timed out`. `tests/fake_worker.py`'s `_checker` sleeps 60 s under the mode
  `checker-sleep`.
- **`Run.codex_ready(change: str, deadline: float) -> bool`** — `reset` is the later of `limited_until("codex")` and
  `_headroom(time.time())`. A `reset` with `reset - time.time() <= LIMIT_WAIT` and before `deadline` on the monotonic
  clock → `time.sleep` until it, then go on; any other `reset` → False. Then, Codex unprobed,
  `self.probe_for(change, ["codex"], [])`; return whether `"codex"` is in `self.probed`.
- **`Run.checker`** — the rule keys on the executor the role runs on, a shadow's after `_shadow`: on `codex` with
  `codex_ready` False, a shadow answers `_answer(1, False, models, " · stopped by a usage limit")`, spawning nothing, and
  any other role runs on `_shadow(self.plan[change, "converge"], models)` with the fallback named. A Codex run that exits
  with `usage_limit(out)` not empty asks `codex_ready` once more: True runs Codex again, once; False answers by the rule
  above — a shadow exit 1 naming the limit, any other role on Claude. A second limited Codex exit takes that same
  answer, never a third Codex run. Only `probe_for`'s refusal halts the version here (C10).
- **`V`, *A mailbox role*** — the answer's form gains ` · fallback: codex usage limit`, ` · tokens <n>` and
  ` · request <id>`; "exit 1 is a worker that failed" gains ", and a checker role's answer naming
  `stopped by a usage limit` halts with that part in the `halt` line; a shadow's halts nothing, as below" (C17).
- **The fallback's test** — `test_a_limited_checker_falls_back_to_claude` patches `time.sleep` with a stand-in that moves
  a patched `time.time` past the reset it sleeps to. With `"codex"` in `run.probed`: a Codex exit on a limit two hours
  off, re-run on Claude; one ten minutes off, run again on Codex; a second limited exit, on Claude; a 92% window far and
  near; a limited shadow, and a shadow's limited exit, each exit 1 with no Claude run; a spent deadline. With Codex
  limited at the probe and unprobed, a reset ten minutes off: waited for, probed, then run on Codex (C10).
- **`V`'s events table, `verdicts`** — "for a mailbox role, the executor, model and effort its answer names" becomes "for a
  mailbox role, the executor, model, effort and tokens its answer names, then ` · fallback: codex usage limit` when it
  names it".

### D4

`Run.rescue`, beside its `verify: halt` test (c:4012-4015): `held == "converge-halted"` and a `halt` naming
`usage limit` → return False, with no worker, no rescue counted and no diagnosis. `Run.supervise` returns False at
the same halt, in its first test. The version then halts for the person, as D53 says.

### D5

- **The answer** — `_answer(code, killed, models, limit, fallback=False, tokens=None, request="")` appends, in order,
  ` · fallback: codex usage limit`, ` · tokens <n>` and ` · request <id>`, each when given.
- **`tokens_of(log: Path) -> int | None`** — a Codex log's `turn.completed` input and output tokens summed; else a Claude
  log's last `result` event's `modelUsage` summed over `inputTokens`, `outputTokens`, `cacheReadInputTokens` and
  `cacheCreationInputTokens`, as `run.py` sums them; None for neither.
- **`_stamp(folder: Path, name: str, model: str | None, tokens: int | None) -> None`** — opens `folder` with
  `O_DIRECTORY | O_NOFOLLOW`, reads `name` as a regular file following no link, sets its frontmatter's `model:` to `model`
  and puts `tokens: <n>` after it, replacing one there, and writes it whole with `_place`. A file that is no regular file,
  or has no frontmatter, is left as it is. `Run.checker` calls it on `_change_dir(self.primary, change)` and
  `f"{role}.md"` after each run it answers.
- **`worker.md`** — `model: <the model, as the host reports it, or unknown>` gains "; a mailbox checker's, `conduct.py`
  stamps"; a `tokens: <int; a mailbox checker's alone, which conduct.py stamps from its log>` line follows it.
  `FINDINGS_KEYS`' comment gains "save `tokens`, which `conduct.py` stamps": the probe's contract is unchanged.
- **The quota line** — `Run.worker`, for a Codex worker: `before = _windows(_rollout(None))` before `work`; after it,
  `after = _windows(_rollout(thread))`, only when `thread = _thread_id(out)` is not None, since `_rollout(None)` is the
  newest. With `after`, it appends one line to `out`, opened
  `O_WRONLY | O_APPEND | O_NOFOLLOW`: `{"type": "mf.quota", "five_hour": <share>, "weekly": <share>}`, `primary` as
  `five_hour` and `secondary` as `weekly`, each share `after.used - before.used` when both name the same `resets`, else
  `after.used`, rounded to one decimal and never below 0; a window `after` lacks is left out.
- **`run.py`** — `_spent` returns `(0.0, 0)` for a log whose first line is an `mf.spawn` and that holds no `result` and no
  `turn.completed`. **`Version.quota(window: str) -> float`** sums the `mf.quota` line's `window` key over the version's
  Codex logs — each spawn of `SPENT`'s stages and its checkers whose first line is an `mf.spawn` — rounded to one decimal,
  a log with no `mf.quota` line passed over; no Codex log holding one raises `Gap`. `METRICS` gains `codex-window-5h` (`five_hour`) and
  `codex-window-week` (`weekly`).
- **`metrics/catalogue.toml`** — after `tokens-integrate`, two `[[metric]]` tables: `id = "codex-window-5h"`,
  `title = "Codex 5-hour window used"`, and `id = "codex-window-week"`, `title = "Codex weekly window used"`; each
  `group = "run"`, `unit = "%"`, `better = "lower"`, `script = "scripts/metrics/run.py"`, `args` its id.
- **`prices.toml`** — under `[models]`, from the ledger's fitted rows:
  `"claude-opus-5-5" = { input = 4.0, cached_input = 0.2, output = 20.0, cache_write = 5.0, cache_write_1h = 8.0 }` and
  `"claude-sonnet-5-5" = { input = 2.0, cached_input = 0.1, output = 10.0, cache_write = 2.5, cache_write_1h = 4.0 }`;
  the header's `Why:` gains `0104-codex-limits design D5`.

### D6

- **The roots** — **`_gitdirs(common: Path) -> list[Path]`** returns each entry directly under `common / "worktrees"`
  that `os.lstat` reads as a folder, no link, sorted; `[]` when there is none. `argv`'s Codex `folders` gain
  `_gitdirs(common)` after `common`; `_unswapped` checks them with the rest.
- **`config.worktree`** — `_config_held(cwd)` also lists, for each file `<common>/worktrees/*/config.worktree`,
  `git config --file <it> --list --name-only`, keeping each name `CONFIG_PLAIN` does not fullmatch. `_common_dir(cwd)`
  names `common`.
- **The probe** — for a Codex executor, `probe` runs `git worktree add -q --detach tree` in the scratch repo, `tree/` in
  its `.gitignore`, and spawns `f"{PROBE} {TREE_PROBE}"`, `TREE_PROBE = "Then run git write-tree in tree/ and write what it
  prints to tree/tree.txt."`. **`check_tree(tree: Path) -> str | None`** — None when `tree.txt`, stripped, equals what
  `git write-tree` prints in `tree`; else `"the worker could not write a linked worktree's index: git write-tree"`. The
  probe's check is `check_probe(scratch, mark) or check_tree(scratch / "tree") or mcp_started(executor, out)` for Codex.
- **`tests/fake_worker.py`** — its probe runs `git write-tree` in `tree/` and writes the output to `tree/tree.txt` when
  the prompt holds `TREE_PROBE`'s text, unless the mode `tree-silent` is set.
- **The real check** — `test_a_linked_tree_writes_under_the_codex_sandbox`, marked `slow`, skipped unless
  `MF_REAL_CODEX=1` and `codex` is on `PATH`: a `tmp_path` repo with a linked worktree; the `-c sandbox_workspace_write.*`
  pairs `argv("codex", …)` gives for that worktree; then
  `codex sandbox -c 'sandbox_mode="workspace-write"' <those pairs> -C <the worktree> -- git write-tree` exits 0.

### D7

- **The CLI** — `checker`, sending, removes `<role>.answer` through `fd`, then places `<role>.request` as
  `f"request {request}\n{text}"`, `request = secrets.token_hex(8)`, and places `<role>.sent` holding `request`. Waiting,
  with or without `--wait`, it reads `<role>.sent`; an answer whose last ` · request <id>` names no id, or another, is
  removed and waited past; the answer it prints is removed with `<role>.sent`, so the mailbox ends empty. It refuses, with
  exit 2 as for a long prompt now, a prompt past `REQUEST_BYTES` less the id line's length, so the server's bound never
  refuses one the CLI sent.
- **The CLI's test** — `test_the_checker_command_sends_and_waits` rewrites its answers to end ` · request <id>`, the id its
  `<role>.sent` holds, sending again before each later answer; a leftover answer naming another id, and `garbled`, are
  each waited past, the call exiting 3.
- **The server** — `serve_requests` takes the first line `request <16 hex digits>` off the prompt; a request without one
  answers `exit 1 · refused: <role>.request names no request`. `spawn(role, prompt)` becomes `spawn(role, prompt, request)`,
  and `Run.checker` passes `request` to `_answer`. Every refusal whose request's first line carries an id names it.
- **`REQUEST_ID = re.compile(r"request ([0-9a-f]{16})")`** names both.

### D8

- **D76**, in `docs/decisions.md` after D70's block, and `D76` after `D72` on the map's *Repo conventions* line:

### D76 · A Codex usage limit falls back, and halts only what runs on Codex

**A usage limit at the run's probe is no refusal: the run logs `codex limited until <time>`, and only a version or cut with a
station on Codex halts, alone, with no rescue. A mailbox checker on Codex that is limited — a limit recorded, or a primary
window at 90% or more by Codex's rollout file — runs on Claude on converge's model and effort until the reset, save a reset at
most 15 minutes away inside converge's time, which it waits for; its answer names `fallback: codex usage limit`. The reset
comes from the rollout the log's `thread_id` names, else the `try again at` text. Each Codex spawn records its share of the
5-hour and weekly windows, never dollars.**

- **Why:** one operator session at 99% of a Plus window stopped run 20261108-200117 whole, a Claude-only version included;
  a wait in the mailbox blocks its thread and costs conductor turns; Codex here is plan quota.
- **Accepts:** the headroom read counts any Codex use, the operator's too · a limited shadow on Codex answers exit 1 and
  drives nothing · a Codex station still halts its version · a forged `thread_id` reads another rollout, misstating a reset
  or a share.
- **Rejected:** a wait until any reset · dollar prices for Codex · the conductor telling a limit from a failure — `conduct.py`
  falls back inside the mailbox.

- **D47** — "a failed probe at the start halts the run, and one in a live run only the versions on its executor" gains
  "; a probe a usage limit stopped, only the versions with a station on its executor
  ([D76](#d76--a-codex-usage-limit-falls-back-and-halts-only-what-runs-on-codex))".
- **D51** — *Accepts*' "a Codex worker can read `~`, with its network off" gains " · a Codex worker writes each linked
  worktree's folder under the common directory, as a Claude worker does".
- **D53** — "A timeout, a usage limit, a failed worker" becomes "A timeout, a usage limit, a converge halt naming one, a
  failed worker".
- **D67** — "A run's Codex probe, past its scratch edit, runs one conformance checker" becomes "A run's Codex probe writes a
  linked worktree's index and, past its scratch edit, runs one conformance checker"; "dollars priced by
  `skills/mf-review-metrics/prices.toml`" gains ", which holds the fitted Claude rows and no Codex row".
- **D68** — "`conduct.py` spawns the checker on the plan's model and effort" becomes "`conduct.py` spawns the checker on
  the plan's model and effort, within converge's remaining time, or on Claude while Codex is limited
  ([D76](#d76--a-codex-usage-limit-falls-back-and-halts-only-what-runs-on-codex)), and answers naming the request".
- **`THREAT_MODEL.md`** — *Trust boundaries*' "a forged event misstates a denial, a limit, a cost or the checker probe's
  usage and MCP checks" gains "; a forged `thread_id` reads another Codex rollout, misstating a reset or a quota share,
  which bounds a wait to `LIMIT_WAIT`"; after "as it reads a subagent's.", "`conduct.py` stamps a mailbox findings file's
  `model:` and `tokens:` and appends a Codex log's `mf.quota` line, following no link." *Entry points*' "so a forged
  request spends at most that." becomes "so a forged request spends at most that, each checker within converge's remaining
  time, its answer naming its request; a request holding a NUL byte still halts the run (`0097·S4`)." (`0097·S6`). The
  sandbox bullet's "writes stay in the repo and its open worktrees" gains ", a Codex worker's also in each linked
  worktree's folder under the common directory".
- **`skills/mf-ship/SKILL.md`** — the diagram's `probe worker ─▶ check probe` gains a line below,
  `a usage limit: codex limited until <time>; only a version with a station on Codex halts`; the say-once paragraph's
  "a Codex probe then runs one checker on a fixture" gains ", and a usage limit at it halts only the versions with a station
  on Codex"; its mailbox sentence gains "; while Codex is limited, a Codex checker runs on Claude".

## Tests

The tests the change adds and edits, at `pytest`'s unit layer save the run over the fake hosts. No browser, so no engine
runs (`T1`).

| file | before | after | counted by |
|---|---|---|---|
| `tests/test_conduct.py` | 145 | 153 | `grep -c "^def test_" tests/test_conduct.py` |
| `tests/test_review_metrics.py` | 13 | 14 | `grep -c "^def test_" tests/test_review_metrics.py` |
| `tests/test_metric_scripts.py` | 15 | 15 | `grep -c "^def test_" tests/test_metric_scripts.py` |

- **Added:** `test_the_codex_limit_data_is_read_from_its_rollout` (D1); `test_a_usage_limit_at_the_probe_is_no_refusal` —
  `probe` over `fake_codex("limit")`, `probe_for` with and without a station on Codex (D2);
  `test_a_limited_checker_falls_back_to_claude` — `Run.checker` over the fake hosts: a limit far and near, a 92% window far
  and near, a shadow, a spent deadline (D3); `test_a_usage_limit_converge_halt_gets_no_rescue` (D4);
  `test_a_codex_limit_at_the_probe_halts_its_stations_alone`, `slow` — a `main run` over the fake hosts with a Claude-only version, a checker version and a Codex-build version;
  no run in the suite starts on a limited probe, so none reaches its state (`T2`), and its commit body says so (D2, D3);
  `test_a_mailbox_checker_is_stamped_and_counted` (D5); `test_a_program_key_in_a_worktree_config_halts` (D6);
  `test_a_linked_tree_writes_under_the_codex_sandbox`, `slow`, skipped unless `MF_REAL_CODEX=1` (D6, C14);
  `test_the_claude_rows_price_a_worker` in `tests/test_review_metrics.py` (D5).
- **Edited:** `test_a_checker_request_is_bounded` — a served checker's timeout is what converge has left, and a request
  needs its id (D3, D7); `test_the_checker_command_sends_and_waits` — the id, the removed answer, a leftover answer waited
  past (D7); `test_the_codex_probe_runs_a_checker` — `tree-silent` fails the probe naming `git write-tree` (D6);
  `test_a_worker_carries_the_allowlist_and_a_denial_is_named` — a linked tree's folder under `worktrees/` among the roots
  (D6); the `probe_for` stub of `test_a_checker_on_another_host_is_planned_and_probed` (`t:3971`) — `probe_for`'s third
  parameter (D2);
  `test_run_metrics_read_cost_and_review_yield` in `tests/test_metric_scripts.py` — `mf.quota` lines summed, a Codex log
  with no turn, a Codex log with no `mf.quota` line passed over, and a version with none a gap (D5).
- **Fakes:** `tests/fake_codex.py` appends a `token_count` event at `FAKE_CODEX_USED` percent to the rollout
  `FAKE_CODEX_ROLLOUT` names, when set; `tests/fake_worker.py` writes `tree/tree.txt` (D6), and its checker sleeps under
  `checker-sleep` (D3).
- **Removed:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[The rollout's shape changes in a later Codex]** → every read is lenient: no window is no headroom, and the reset falls
  back to the text, then to the run's end.
- **[A wait blocks the version's thread up to `LIMIT_WAIT`]** → only inside converge's remaining time; the conductor's
  `--wait` re-runs cost turns for at most that long.
- **[Headroom reads the operator's own sessions]** → that is the shared plan; D76 accepts it.
- **[`codex sandbox`'s flags differ from the test's]** → the person runs it in the `**HUMAN` phase; a failure there is a
  plan amend, and every Codex run's probe writes a linked worktree's index anyway.
- **[A gitdir root lets a Codex worker write another tree's index]** → each is inside `common`, which a worker already
  writes; a Claude worker could already.

## Verdict

Settled: the limit data, the probe, the mailbox fallback, the record, the linked worktree, then the request id and the
record of decisions, each phase ending on a green `make check`, the last automated one on the gate; the person's real-Codex
check closes it.
