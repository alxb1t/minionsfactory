# Sandbox runner — design

`sandboxed(argv, cwd, trees)` in `skills/mf-ship/scripts/conduct.py` runs a plain command under macOS Seatbelt, and
`conduct.py sandboxed -- <cmd>` is its command. Verdict: ship the function and its command, tested at the lowest layer through
a fake `sandbox-exec`, with the real Seatbelt in tests that skip where it cannot nest.

Read [proposal](proposal.md) for why, [tasks](tasks.md) for the phases, and [the delta](specs/sdd/spec.md) for the
requirement.

## Context

Facts at `ccfa6a1`, each re-read at the cut.

| id | fact | where |
|---|---|---|
| F1 | a Claude worker's sandbox is Claude Code's, set by `worker_settings` from `SECRETS`, `TOKENS` and the trees; `conduct.py` itself runs outside any sandbox | `skills/mf-ship/scripts/conduct.py:231`, `:247`, `:3250` |
| F2 | `conduct.py` holds no `sandbox-exec`, no `sandboxed` and no wrapper for a plain command | `skills/mf-ship/scripts/conduct.py` |
| F3 | `argv` builds a worker's environment: `VIRTUAL_ENV` unset, `HOOKS_OFF`, `UV_CACHE_DIR` and `TMPDIR` under the primary's `.minions` | `skills/mf-ship/scripts/conduct.py:3425-3437`, `:310` |
| F4 | `reach(primary)` returns the primary and each open version's or queued cut's worktree; the primary is first | `skills/mf-ship/scripts/conduct.py:3186` |
| F5 | `CODEX_DENIAL` is `Operation not permitted`, the macOS sandbox's refusal in a command's output | `skills/mf-ship/scripts/conduct.py:230` |
| F6 | `Stop(code, message)` ends a command, and `main` prints it and returns its code; `Stop(2, …)` is "cannot run" | `skills/mf-ship/scripts/conduct.py:359`, `:7771` |
| F7 | `tests/test_conduct.py` loads `conduct.py` with `runpy.run_path`, whose result is a copy of the globals: a test fakes a tool on `PATH`, as `_no_ps` fakes `ps`, and patches no constant | `tests/test_conduct.py:153-171` |
| F8 | `sandbox-exec` sits at `/usr/bin/sandbox-exec`; run inside a worker's own sandbox it exits 71, `sandbox_apply: Operation not permitted`, so a Seatbelt profile cannot nest. Measured at the cut with `sandbox-exec -p "(version 1)(allow default)" /usr/bin/true` | the cutter's session |
| F9 | the gate runs `uv sync --locked` first, and `uv` reads a warm cache offline under `UV_OFFLINE=1` | `Makefile`, `make -n gate` |

## Goals / Non-Goals

**Goals:**

- One function and one command a person and the tests can run, which a later change calls without a rewrite.
- Fail closed: no OS sandbox, no run.

**Non-Goals:**

- A caller of `sandboxed()`, in `conduct.py` or a skill.
- A Linux runner, a per-host network filter, a time limit, a memory limit.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the profile starts at `(allow default)` and carves out the denials | a command needs the OS's many reads; the carve-outs are the policy | `(deny default)` and a list of allows |
| [D2](#d2) | `sandboxed(argv, cwd, trees) -> int` runs under `sandbox-exec`, in a scrubbed environment, and tees the output | F3: the gate runs as a worker's gate does | a shell string; a bare run |
| [D3](#d3) | `conduct.py sandboxed -- <cmd>` runs `sandboxed` over `reach(primary_of(cwd))` | a person runs what the tests run | a flag on `agent` |
| [D4](#d4) | D51 is amended in `docs/decisions.md`; the delta adds one requirement beside *A worker runs in an OS sandbox* | A7: the page says what holds | a new decision id |
| [D5](#d5) | tests run a fake `sandbox-exec` on `PATH`; the real-Seatbelt tests apply the real one and skip where it cannot nest | F7, F8 | a patched constant; a skip of every test |

### D1

The profile is Seatbelt text built by `_profile(trees, home)`, in this order, a later rule beating an earlier one:

```
(version 1)
(allow default)
(deny file-write*)
(allow file-write* (subpath "<tree>") … (literal "/dev/null") (literal "/dev/tty")
                   (literal "/dev/dtracehelper") (literal "/dev/autofs_nowait")
                   (literal "/dev/stdout") (literal "/dev/stderr"))
(deny file-read* file-write* (subpath "<secret>") …)
(deny network*)
```

- Each `<tree>` is the tree resolved; each `<secret>` is a `SECRETS` entry with its `~` taken to `home` and the path resolved,
  whether or not it exists. Seatbelt matches real paths, so `/tmp` is `/private/tmp`.
- A path is quoted with `\` and `"` escaped. A tree holding a `"` stays one string.
- The secrets rule follows the trees rule, so a secret inside a tree stays denied.
- `(deny network*)` takes loopback and sockets too: no gate in this repo binds a port, and a port bind is the
  [D51](../../../docs/decisions.md#d51--a-worker-runs-in-an-os-sandbox-and-no-worker-pushes) line a worker keeps.

Measured: F8 shows a profile cannot be applied inside a worker, so the order rule and the `/dev` list are read from Apple's
profiles and checked by the real-Seatbelt tests ([D5](#d5)), which a person runs in a plain terminal.

### D2

`sandboxed(argv, cwd, trees)` returns the command's exit as an `int`.

```
sandbox_exec = shutil.which("sandbox-exec")        none → Stop(2, "conduct: cannot run — no OS sandbox: sandbox-exec is not on PATH")
env          = os.environ − VIRTUAL_ENV − TOKENS + HOOKS_OFF + UV_OFFLINE=1
               + UV_CACHE_DIR=<trees[0]>/.minions/uv-cache + TMPDIR=<trees[0]>/.minions/tmp   (made, as `argv` makes it)
run          = sandbox-exec -p <_profile(trees, Path.home())> <argv…>   cwd=cwd, stdin closed, stdout+stderr piped
output       = each line written to sys.stdout; a line holding CODEX_DENIAL marks the run denied
after        = exit ≠ 0 and denied → one line on sys.stderr: "sandboxed: denied — the OS sandbox refused a call: writes stay in the trees, no network"
return       = the exit; a signal's negative code −9 → 137 (128 plus the signal's number)
```

- `trees[0]` is the primary ([F4](#context)); an empty `trees` is a programming error and is not guarded.
- `HOOKS_OFF` is a tuple of `KEY=VALUE` strings; split each at its first `=`.
- A `sandbox-exec` that cannot apply the profile exits 71 and its own message; that exit passes through, and nothing ran bare.
- `PATH` is the operator's, as it is for `git` and `uv`: a planted `sandbox-exec` is the operator's own compromise.
- The output goes to `sys.stdout`, so a caller redirects it; a caller that needs it in a file takes the file with a later
  parameter, which this change does not add.

Rejected: `subprocess.run(..., shell=True)` — a shell string is the injection the shell rules forbid. Rejected: running bare when
`sandbox-exec` is missing — D51's "a builder's code never runs outside a sandbox" is the point.

### D3

`main` gains a `sandboxed` subparser whose one argument is stored as `argv` — never `command`, which is the subcommand's own
`dest` — with `metavar="cmd"` and `nargs=argparse.REMAINDER`; a leading `--` is dropped before the call. The branch tests
`args.command == "sandboxed"`, calls `sandboxed(args.argv, cwd, reach(primary_of(cwd)))` and returns its exit.

- An empty `argv` ends with `Stop(2, "sandboxed: cannot run — no command")`.
- The module docstring's command list gains `conduct.py sandboxed -- <cmd>`.
- `skills/mf-ship/SKILL.md`'s command table gains one row, after `anchor`.

### D4

`docs/decisions.md`'s D51 headline gains, after "its scripts reach no unlisted domain.":

```
 A plain command a run starts on a builder's code — the gate, a check script, a `Verify:` — runs under `sandboxed()`:
 macOS Seatbelt, writes inside the version's trees alone, no credential read and no network, and no OS sandbox ends it
 with exit 2.
```

and its **Accepts** list gains `a plain command has no network, so one that needs a registry fails red · Linux has no runner until
a run starts there`; its **Rejected** list gains `a plain command run bare where no OS sandbox stands`.

The delta's requirement is ADDED: *A worker runs in an OS sandbox* is about workers and stays as written.

### D5

See [Tests](#tests).

## Tests

All tests land in `tests/test_sandboxed.py`, which loads `conduct.py` as `tests/test_conduct.py` does (F7). No test is removed.

| test | layer | proves | `T` |
|---|---|---|---|
| `test_the_profile_confines_writes_reads_and_network` | unit | [D1](#d1): the order of the rules, each tree and secret, the escape of a `"` | T1 |
| `test_a_command_runs_under_sandbox_exec_with_a_scrubbed_environment` | unit | [D2](#d2): argv, cwd, `UV_OFFLINE`, the tokens and `VIRTUAL_ENV` gone, `HOOKS_OFF`, the cache and `TMPDIR` | T1 |
| `test_the_exit_passes_through` | unit | the exit, and a signal's `128 + n`, by parametrize | T1 |
| `test_no_sandbox_exec_stops_with_2` | unit | fail closed: nothing ran | T1 |
| `test_a_denial_in_the_output_gets_a_line` | unit | the denial line on a failed command, none on a passed one | T1 |
| `test_the_command_runs_a_command_in_the_cwd` | unit | [D3](#d3): `--` dropped, the version's trees, the exit; no command exits 2 | T1 |
| `test_the_command_exits_2_with_no_os_sandbox` | unit | `main` prints `no OS sandbox` and returns 2 | T1 |
| `test_a_write_outside_the_trees_is_denied` | integration, real Seatbelt | a write outside fails, one inside passes | T1 |
| `test_a_secret_read_is_denied` | integration, real Seatbelt | a read of a file under the home's `.ssh` fails | T1 |
| `test_a_network_connect_is_denied` | integration, real Seatbelt | a connect to a local listener fails, and the listener sees none | T1 |

- Counts: the file holds 10 tests, 7 unit and 3 integration, by `grep -c '^def test_' tests/test_sandboxed.py`, which prints `10`;
  the end-to-end runs it adds are none.
- The fake `sandbox-exec` is a fixture the unit tests ask for by name, never an autouse one: the real-Seatbelt tests run on
  the unchanged `PATH`. `_seatbelt()` finds `sandbox-exec` with `shutil.which`, is false when it is missing, and is true only
  when the probe below exits 0.
- `test_the_command_exits_2_with_no_os_sandbox` sets `PATH` to a folder holding a link to the real `git` alone, made before
  the `PATH` is set: `primary_of` runs `git` ([F6](#context)) and must still pass.
- The real-Seatbelt tests start with `pytest.skip` unless `sandbox-exec` applies a trivial profile — `sandbox-exec -p
  "(version 1)(allow default)" /usr/bin/true` exits 0 — so a worker's gate skips them ([F8](#context)) and `diff-cover` counts
  the lines the fake covers.
- Each real test's trees are under `tmp_path`, and its home is the conftest's isolated one: no real credential is read.
- I16 table: no test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

| risk | mitigation |
|---|---|
| the real Seatbelt tests skip in every build worker and converge worker, so the profile's order and `/dev` list are never seen to hold before release | the person runs `uv run pytest -q -rs tests/test_sandboxed.py` in a plain terminal before the release; the next change's first real gate runs under the profile |
| a gate that needs `/dev/fd` or a pty fails under the profile | the failure prints the denial line and the exit, and the `/dev` list is one line of `_profile` to widen |
| `(deny network*)` blocks a gate that binds loopback | no gate here does; a gate that does fails red, as it does in a worker (D51) |
| `0106-cut-scripts` edits `conduct.py`'s `main` and `PROMPTS` too | this change adds one subparser, one branch, one docstring line and one function; a conflict is a text merge for `mf-integrate` |

## Migration Plan

None. Nothing calls `sandboxed()` until a later change does.

## Verdict

Build as written: `sandboxed()` first, its command and the record of decisions second.
