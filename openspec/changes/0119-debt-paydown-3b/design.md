# Debt paydown 3b — design

One decision per fix of `conduct.py` and `converge.py`, each behind a test that is red before it. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The brief's plan splits the debt paydown by file: `0118-debt-paydown-3a` touches no `conduct.py`; this change touches `conduct.py`, `converge.py` and their tests alone. Every card here is a fix of one line and a test, or a reason to record. [Paydown 2](../archive/0088-paydown-2/design.md) is the method: each test red before its fix.

## Goals / Non-Goals

- Goal: close each id of `proposal.md`'s `debt:` line, and the ideas, with a test that fails without the fix.
- Non-goal: a design-sized card. [Not in this change](proposal.md#not-in-this-change) lists them.
- Non-goal: a requirement, a skill line or a threat-model line. See [D10](#d10).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the debt paydown splits by file; this version holds `conduct.py`, `converge.py` and their tests | reviewable diffs, no file in common with 3a | one change over both |
| [D2](#d2) | build on Sonnet high; converge fully on Codex; patch bump | conductor code builds high; the person asked to prove Codex can converge; AGENTS.md's patch line | a minor |
| [D3](#d3) | a category outside the non-security ones is a security one (`0095·S2`) | the design already says an unreadable category bars | a list of security spellings |
| [D4](#d4) | the run-start move links with `follow_symlinks=False` and unlinks a name that is no regular file (`0095·S4`) | the card's fix | a re-check before the link |
| [D5](#d5) | a restored `models.toml` is created with `O_EXCL`, never truncated (`0106·S4`) | a link planted after the removal then fails the write | an atomic rename |
| [D6](#d6) | cleanup chmods a path's parent only when the path is not the folder it removes (`0111·S2`) | the root's parent is the system temp folder | a catch of `PermissionError` |
| [D7](#d7) | a `test fixed` path is exempt under `tests/` and `test/` alone, and `HEAD` must be integrate's merge (`0090·S5`) | the card's fix; integrate's own commits are not held by the settle | a body-line check alone |
| [D8](#d8) | `rejoin` stops with 2 on a new brief row with a cell that is not printable ASCII, naming the row by `repr` (`0091·S6`) | a terminal control character hides a row from the person's yes | a strip of the cell |
| [D9](#d9) | a stacked version waits while its dependency is unreleased on the default branch; a wait recomputes the unreleased set at each poll (`0099·S3`, `0099·S4`) | the dependent's own archive is a worker's word; the set changes while it waits | a provenance check of the archive |
| [D10](#d10) | no spec delta: `skip_specs: true` | each fix makes the code meet a requirement or scenario in force; a test binds it | a MODIFIED block per fix |
| [D11](#d11) | `lacked` takes a result whose text opens with the missing-tool message (`0100·S3`) | a failed command that prints the phrase is no missing tool | a check of the use's name against the station's tools |
| [D12](#d12) | `codex_ready` skips the probe, and returns False, with less than `PROBE_ROOM` of converge's time left (`0104·S7`) | a probe killed by a spent deadline halts a version for a budget artifact | a floor in `probe_for` |
| [D13](#d13) | a request for a version whose rescue runs is written again and logged once (the rejoin idea) | `take_requests` deletes every request before it skips a live thread | a request that waits in the run |
| [D14](#d14) | `converge.halt` stamps nothing on a log whose newest run ended (the ended-log idea) | `stamp.py` refuses an event after `halt` or `done` | a stamp that rewrites the end |
| [D15](#d15) | each test-cost card closes on a stated reason beside its test; a docstring over the comment limit is cut to the comment limit | `T2` asks for a reason; `C7` sets the limit | a merge of run tests |
| [D16](#d16) | a card closed without code shows its evidence here | paydown 2's method | none |

### D1

Phases follow files and risk: phase 1 holds the security and link cards, phase 2 the stacking, tool, probe, rejoin and converge cards, phase 3 the test-cost reasons and docstrings.

### D2

The models line of the brief names Sonnet high for build, Sonnet medium for converge, release and cut, Codex `gpt-6.1-sol` high for the checkers and medium for the fixer.

### D3

`_security_card` today reads `_category(card) in ("security", "")`. A new constant `NON_SECURITY` holds `stability`, `data integrity`, `functional correctness`, `performance` and `maintainability`; `_security_card` returns true when the severity blocks and the category is outside it.

```
before:  "security (exposure of secrets)"  -> not "security" -> no bar
after:   "security (exposure of secrets)"  -> not in NON_SECURITY -> bars
```

### D4

`Run.migrate_layout` calls `os.link(old, name, dst_dir_fd=fd)`, which follows a link swapped in after the check. The call takes `follow_symlinks=False`; the new name is read with `os.lstat(name, dir_fd=fd)`. A name that is no regular file is unlinked, `old` stays, and the method returns `<old> became a link: a person settles what it names`.

### D5

`_write_in_change` gains `fresh: bool = False`. With `fresh` the flags hold `O_EXCL` in place of `O_TRUNC`, so a name that stands raises `FileExistsError`, an `OSError`. `_write_models` passes `fresh=True` after it removes the old file and keeps its `Stop(2, …)`.

### D6

In `_remove_temp.unlock`, `os.chmod(os.path.dirname(path), 0o700)` runs only when `os.fspath(path)` differs from `os.fspath(folder)`: `rmtree` hands the callback the root as a `Path` and its children as `str`. The root's parent is then never changed.

### D7

A new constant `TEST_PATHS = ("tests/", "test/")`. `_settle_kept` keeps a `test fixed` path only when it starts with one of them, and returns `integrate committed past its merge` when `git rev-parse HEAD` is not the merge it read. The threat model's sentence names "a test its body names fixed" and stays as it reads; the bound is now narrower than the sentence.

### D8

`rejoin` checks each cell of each row in `new` with `cell.isascii() and cell.isprintable()` before it computes the hash, and stops with 2: `rejoin: cannot run — the brief's row <row!r> holds a character a terminal may act on`. The `repr` keeps the escape out of the line.

### D9

In `stage_of`, `if stacked is not None and lacking` becomes `if stacked is not None and (lacking or missing)`, naming `lacking or missing`. `Run.until` takes a callable `still` in place of the `stack` flag: its test becomes `self.stackable(version, still())`. `Run.ready` passes `unreleased`. A dependency that releases while the wait runs then leaves the awaited one as the sole member, and the wait stacks.

### D10

The change adds no requirement and modifies none: each fix makes the code meet one already in force. Examples: a card whose category cannot be read bars (`0095-converge-roles` design D2), a dependent never converges before its dependency's release (the threat model's stacked-build line). A test binds each, so the change has `skip_specs: true` and `specs/.gitkeep`.

### D11

`lacked` counts a result when `text.removeprefix("<tool_use_error>").lstrip().startswith(MISSING)`. A pytest line or a grep error that holds the phrase later in its text is none.

### D12

A new constant `PROBE_ROOM = 120` seconds. `Run.codex_ready` returns False before `probe_for` when `"codex"` is not in `self.probed` and `deadline - time.monotonic() < PROBE_ROOM`: Claude checks, no probe starts, no halt is recorded. The value is the cutter's: a probe's own run is short, and 120 leaves room for it.

### D13

`Run.take_requests` skips a version with a live thread. When the request names that version and `_rescuing(self.primary / ".minions" / "runs", change)` holds, it now writes the request again with `_request(self.primary, change)` and logs `<change>: still running — its rescue holds the request` once, a new set `self.kept` holding the changes logged. The next poll after the thread ends takes it; a request `all` is not kept.

### D14

`converge.halt` reads `latest(context)` first and returns when its newest event is `halt` or `done`: the caller has printed the reason, and the log stays as it was. A halt on a run that is open stamps as before.

### D15

Reasons, each at the top of its test as a `# T2:` line after the test's `# Why:` line, the pattern of `test_a_run_builds_each_pinned_scripts_environment_before_its_first_thread`:

| test | reason |
|---|---|
| `test_a_shadow_round_drives_no_fix` | its fake `shadow-blocks` mode and a models file of Codex checkers with `shadow = true` are the state; no other run test reaches it |
| `test_every_station_starts_lean` | it writes the operator's `settings.json` with plugins before the run and reads each Claude station's argv; no other run test holds that state |
| `test_a_worker_asking_for_a_missing_tool_halts` | its fake `missing-tool` mode makes the build worker ask for a tool; no other run test reaches that halt |

`0112·R3` needs no edit: the sync-order test carries its `# T2:` line. `_temp_folder` and `_remove_temp` each keep a summary line, a blank line and a `Why:` line; the `e.g.` line goes. `_settle_kept` cites the delta's requirement in place of a findings card.

### D16

Evidence for a card that closes with no code, as the commands print it at the cut:

| card | command | prints |
|---|---|---|
| `0112·R3` | `git grep -n 'T2: the three-version test' -- tests/test_conduct.py` | a line: the sync-order test's reason |
| `0090·R4` | `git grep -n 'security S2' -- skills/mf-ship/scripts/conduct.py` | the `_settle_kept` line alone: no other docstring cites it |

## Tests

New tests are unit tests (`T1`); this change adds no end-to-end run and no engine. The reasons for the run tests it keeps are in [D15](#d15).

| layer | test | change | evidence command |
|---|---|---|---|
| unit | `tests/test_conduct.py` | a new test, `_write_models` over a planted link; steps in existing tests, named in [tasks](tasks.md) | `grep -c '^def test_' tests/test_conduct.py` prints 176 before |
| unit | `tests/test_converge.py` | a new test, `halt` over an ended log | `grep -c '^def test_' tests/test_converge.py` prints 31 before |
| end-to-end | none added | none | none |

No test is deleted or merged, so `I16` holds no table.

## Dependencies

None.

## Risks / Trade-offs

- `TEST_PATHS` names its folders alone: a target repo whose tests live elsewhere gets a halt where a settle used to pass. The halt names the path, and the person settles it.
- `PROBE_ROOM` is a guess: too high skips a probe Codex could have run; the checker falls back to Claude, which costs a round on another host, never a halt.
- A kept rejoin is written each poll while a rescue runs: one small file, replaced in the home folder's queue.

## Verdict

Ready to build, in the phases of [tasks](tasks.md).
