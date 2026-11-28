# Pins — design

Where the pin's files and the `ship.toml` read go, in which order, and what each phase keeps or turns. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`pin.py` reads the pin's files by `_read` and writes and removes them by `_write`: a plain `read_text`, a plain `write_text`, an `unlink`. The conductor reads `ship.toml` by `_ship_file`: `tomllib.loads` of `read_text`.

Neither follows the rule `0159-kept` set for the other kept files: no link, no block, a regular file, a bound, a strict decode, a staged write. So a bad byte in `source`, `pending` or `hold` ends a run in a traceback, a FIFO at `ship.toml` blocks a command, and a link is followed.

```
today                                   after
pin.py  _read/_write ──▶ pin files      pin.py ──▶ kept.py ──▶ pin files
conduct.py _ship_file ──▶ ship.toml     conduct.py ──▶ kept.py ──▶ ship.toml
```

`kept.py` already holds `_read`, `_replace` and `_remove`, and `pin.py` and the conductor already import `mflib.kept`. Facts of the region are in the [cases](#the-cases) and the [readings](#the-readings).

## Goals / Non-Goals

- **Goal:** a home for the pin's files and the `ship.toml` read, then the shared read and write for them, and a stop that names the file where one is broken.
- **Goal:** each move is proved by a pin written first and a test that changes only the line by which it reaches a name (Q26).
- **Non-goal:** `cloud_setup.py`'s write of `ship.toml` ([D12](#d12)); the cycle between `pin.py` and the conductor (Q260); a cache of `ship.toml`; a change to what `0159-kept` moved. The rest is in [proposal](proposal.md#not-in-this-change).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | One module and new test files: the pin's files and the `ship.toml` read go into `kept.py`, beside `_read`, `_replace` and `_remove` (Q199, Q255, P1) | Q199 is the person's standing decision; `kept.py` stays on `layout` and `statefile`, so the map row stays | a module for the pin too; a new `pinfile.py` |
| [D2](#d2) | `ship.toml` is read at each call, no cache; `_ship_file`, `_cap` and `_pushes_tags` stay in the conductor as short calls (P2, P5) | tests call them with no argument and `test_claim.py` stubs `_cap` and `_pushes_tags` with no-argument lambdas | a parse per command, which changes their signatures or hides a cache between tests |
| [D3](#d3) | A pin file that cannot be read stops `describe`, is named at `move` with nothing moved, and is never read as no pin (P3, Q200, Q201, Q265) | a raise from `move` in `run`'s `finally` would replace a finished run's exit | a broken file as none; a hard-link test |
| [D4](#d4) | A `ship.toml` that cannot be read raises `Broken`, worded `Stop` 2 `<path>: <phrase>` by `_ship_file` (P4) | the frame is today's; Q200 and Q201 add the shapes | a new exit code; a message of the module's own |
| [D5](#d5) | Until phase 4 the moves keep today's side; phase 4 alone turns a right side (Q26, K3) | an unchanged assert over moved code proves the move changed nothing | turning a reading while moving it |
| [D6](#d6) | `Broken` gains `path` and `phrase`, and names a path outside the kept folder as `<path>: <phrase>` | `relative_to` raises for a path outside the kept folder | a second error class for `ship.toml` |
| [D7](#d7) | The pin's files are written staged at 0600 in a folder of 0700 and removed by name under the folder's descriptor (Q203, Q258, Q259) | the staged write and the named removal are `kept`'s | a plain `write_text`; a mode change of a folder that stands |
| [D8](#d8) | An empty `source` reads as none (P12) | today `""` makes `move` take the current folder | reading `""` as a path |
| [D9](#d9) | A changed or added line only an error path reaches gets its test in the same phase, the test running the real path (P7) | the gate wants 100% of changed lines; `make check` does not measure it | a stubbed failure |
| [D10](#d10) | A new test over 1 s carries `slow`; no `Verify:` runs `tests/test_conduct.py` whole; each station task runs the region's slow sets with `-n auto` (K8, K9, P8, P9, P10) | `slow` tests broke in `0159-kept`'s phase 3 and ran first at the gate | whole-file conduct runs |
| [D11](#d11) | Card `0159·R3` is paid in phase 1 (P11) | its trigger, the next timed gate, is met | leaving the card open |
| [D12](#d12) | `cloud_setup.py` keeps its write of `ship.toml`, and the cycle with the conductor stays (Q260, Q261) | `cloud_setup.py` runs under the machine's own `python3`; each cross-load still needs names that are no kept file's | moving the write now |
| [D13](#d13) | The record: the spec delta, D55, D84, the threat model, principles and recipes say what holds after; Q205's list gains the pin's files (Q263) | A7: a decision in force is edited where it lives | leaving the list short |

### D1

The new functions of `kept.py`, names the cut's; each is public, since `pin.py` and the conductor call them (`check_names`):

| function | does |
|---|---|
| `source()`, `pending()`, `hold()`, `checkout()` | return the file's text stripped, or None for no file |
| `keep_source(text)`, `keep_pending(text)`, `keep_hold(text)`, `keep_checkout(text)` | write the text and one newline |
| `clear_pending()`, `clear_hold()` | remove the file; a gone one is quiet |
| `ship_data()` | return `ship.toml`'s parsed data, `{}` for no file |
| `ship_cap(data)`, `ship_tags(data)` | return `in_flight` or None, and `tags` or True, or raise `Broken` with today's phrase |

The private helpers `_pin_read(file)`, `_pin_keep(file, text)` and `_pin_clear(file)` hold the right sides; phase 4 changes their bodies and no caller. `holder`, `live` and `_origin` of `pin.py` stay calls into `kept.py`. Test files: `tests/test_pinfiles_pins.py` for phase 1's cases on today's side, `tests/test_kept_pinfiles.py` for the unit and round-trip cases of the new functions; `tests/test_kept.py` grows none, and `tests/test_kept_pins.py` changes only by [D11](#d11).

### D2

`run` reads the file at its start for the cap and again for the tags, and `cut`, `status` and `report` read it for their own key; that stays. A test that rewrites the file between calls of `_cap()` sees the new value.

### D3

Phase 4: `describe` lets a `Broken` through, so `Run.ship` raises it, `run` logs the halt and exits 2, as `kept` settled. `move`'s first read joins its `try`: a `Broken` is `pin: cannot move — <text>`, and the run's exit stays, because its versions are released by then. `install` reads no pin file. A live mark that cannot be read still reads as none.

### D4

`_ship_file` catches `kept.Broken` alone, its old `except` clauses gone, and raises `Stop(2, f"{path}: {error.phrase}")`: a `Broken` is an `OSError`, so an old clause left first would word the stop twice. `_cap` and `_pushes_tags` do the same for the check's `Broken`. `run`, `cut`, `status` and `report` exit 2 naming the file; the stop lands where it does today.

### D5

Phase 2 writes each function as its copy behaves today: a plain read, a plain write, an unlink, `tomllib`; `ship_data` raises the raw `OSError`, `UnicodeDecodeError` or `TOMLDecodeError`. Phase 3 sends the stations through them, `_ship_file` keeping its `except` tuple. Phase 4 changes the bodies of the pin helpers and of `ship_data` to the shared read and the staged write of `kept.py`, and turns the cases with them.

### D6

`Broken(path, phrase)` keeps `~/.mf-ship-origin/<name> cannot be read: <phrase>` for a path under the kept folder. For another path its text is `<path>: <phrase>`. Both keep `path` and `phrase` as attributes, so `_ship_file` can word today's frame. `tests/test_kept.py` passes unchanged.

### D7

A pin file's write is `_replace`'s: staged through the fixed name `<name>.tmp`, 0600, the folder made at 0700 and kept at its mode when it stands. A link at the name is replaced and its target left; a FIFO at the name does not block. A folder at the name, or a refused home, raises `Unwritten` or `Refused`, each an `OSError`, which `main` words as `pin: cannot install — <error>`, exit 2.

### D8

Only `source` changes by P12: a file of no bytes, or of white space alone, is no source, so `move` returns `None` and moves no link. A `source` naming a folder that is no repository is read as that path, and `describe` says nothing, as today.

### D9

Each error-path line is named in the task that changes it, with the case that reaches it. The `except kept.Broken` of `_ship_file` is reached by the bad-byte and folder cases of `test_cap_reads_ship_toml`; its `return` needs no new test.

### D10

The region's slow sets, as plain commands, each word a substring of a real test name:

| set | `-k` of `tests/test_conduct.py` |
|---|---|
| ship | `cap_reads_ship_toml or ship_toml_is_read or ship_toml_reads_tags or cap_file_that_is_bad` |
| cap | `cap_gates or cap_of_one or cap_counts or cap_close_starts or cap_writes or cap_status_and_cut_line or small_cap_is_granted` |
| tags | `start_makes_a_missing_tag or refused_tag_push or tags_false or status_says_a_machine_pushes_no_tag or report_with_a_bad_tags` |
| pin | `last_run_moves or re_pin_builds or run_holds_the_machine_awake or started_run_is_seen or run_on_linux_holds_nothing` |

Whole files beside them: `tests/test_pin.py`, `tests/test_claim.py`, `tests/test_structure.py`, `tests/test_kept_pinfiles.py`, `tests/test_pinfiles_pins.py`. Phase 1 and phase 2 tasks run only the test files they write or touch, with `tests/test_kept.py` and `tests/test_structure.py` in phase 2.

### D11

By the card's own Fix: the live-mark assertion joins the real-byte test of the kept `default`, and the patched twin that raises `Broken` at `default` goes, both in `tests/test_kept_pins.py`; the [Tests](#tests) table names both. `test_broken_run_releases_the_held_events_before_the_halt` is unchanged.

### D12

`write_ship_toml` stays in `cloud_setup.py`, listed, until the cloud machine's Python is known; only the read moves. `pin.py` still loads the conductor for `_scratch`, `SSH_COMMAND` and `GIT_TIMEOUT`, the conductor still loads `pin.py` for `trees`, `describe` and `move`, and `CYCLE_FILES` and the `PRIVATE_REACH` entry of `_scratch` stay.

### D13

The change's [spec delta](specs/sdd/spec.md) is written at the cut: Q205's sentence gains the pin's files (Q263), the kept requirement stops saying the pin's files are not its, and requirements for the pin's files and for `ship.toml` say the shapes.

Phase 5 edits the living pages `docs/decisions.md` (D55 and D84), `THREAT_MODEL.md`, `docs/principles.md` and `docs/recipes.md`. `docs/modules.md` stays: the `kept.py` row's `names` cell is `layout.py, statefile.py` before and after, `tomllib` being no script. The changelog entry of phase 4, which the build writes, says a `ship.toml` that is a link now stops the command.

## Tests

The change adds tests at the lowest layer: unit cases of the new functions and cases of the stations through `describe`, `move`, `install`, `main`, `_ship_file`, `_cap` and `_pushes_tags` ([T1](../../../CODING_STANDARDS.md)). No browser, so no end-to-end run.

| layer | adds | removes | the count's command |
|---|---|---|---|
| station cases, `tests/test_pinfiles_pins.py` | the 144 cases of the mutation run, written again | none | `uv run pytest tests/test_pinfiles_pins.py --collect-only -q` |
| unit and round-trip, `tests/test_kept_pinfiles.py` | a case per new function and per shape of phase 4 | none | `uv run pytest tests/test_kept_pinfiles.py --collect-only -q` |
| conductor, `tests/test_kept_pins.py` | one assertion | one test | `git grep -c "def test_" -- tests/test_kept_pins.py` |
| end-to-end runs | none | none | none |

A new test over 1 s carries `slow` (K8): each FIFO case, read in a child with a timeout, and each case that goes through `run`. A case that plants a pin file and calls `describe` carries none.

New tests that run through a conductor `run`, with the reason none existing fits ([T2](../../../CODING_STANDARDS.md)):

| test | why no existing test fits |
|---|---|
| a bad byte at `hold` halts the run, exit 2, the live mark gone | the pin's files are read at the `start` line, after the kept `default`; a run stops at its first broken read, so `test_stop_a_bad_byte_in_the_default_stops_run_with_exit_2_naming_it` cannot reach it |
| `run` with a valid `ship.toml` reads it for `_cap` and for `_pushes_tags` | a slow `run` is the only way to count the reads of `run`'s start |

The `I16` table, for the test the change deletes:

| removed test | carried by |
|---|---|
| `test_broken_run_logs_the_halt_naming_the_file_and_exits_2` | `test_stop_a_bad_byte_in_the_default_stops_run_with_exit_2_naming_it`, which gains the live-mark assertion; the halt line and exit 2 it asserted are the real-byte test's own |

Existing files the change may turn red: none until phase 4, which turns only the cases of `tests/test_pinfiles_pins.py`. `tests/test_pin.py`, `tests/test_claim.py` and `tests/test_conduct.py` plant plain one-line pin files, and match the path alone in a `ship.toml` stop, so they stay green. `tests/conduct_load.py` is read by the new cases and not edited.

## The readings

The mutation run left readings of the code. Each is settled: **as today** is pinned by phase 1's cases, kept by the module in phase 2 and by the stations in phase 3, and still so after phase 4; **turned** is pinned on today's side in phase 1 and changed, with its case, in phase 4 alone.

| reading | after |
|---|---|
| R1, W1 — a bad byte in `source`, `pending` or `hold` ends in a traceback | turned: `describe` and `install` stop the command, exit 2, naming the file; `move` names it in `pin: cannot move — <text>`, moves nothing, the run's exit stays. A bad byte in `checkout` is named where `move` reads it; `describe` does not read `checkout` |
| R3, R7 — a link, a dangling link, a folder or a FIFO at a pin file reads as the file or as none | turned: a broken file, named as R1 is; an absent file still reads as none |
| R4, W5 — a pin file over 65,536 bytes is read whole and used | turned: a broken file, never put in the `start` line or used as a path |
| W2 — a write follows a link | turned: it replaces the link with a regular file, the target untouched |
| W3 — a write at a FIFO blocks | turned: the staged file replaces the name |
| W9 — a file is written at 0666 less the umask | turned: 0600; the folder is made at 0700 and one that stands keeps its mode |
| W6 — `pin: cannot install — ` with the system's words | turned: the words after the dash are the staged write's and name the file; a removal's failure is the system's |
| S1 — a FIFO at `ship.toml` blocks | turned: the one read does not block; the command stops, exit 2 |
| S2 — a deeply nested `ship.toml` is a traceback | turned: a stop, exit 2, naming the file |
| S3 — a link at `ship.toml` is followed | turned: a stop, exit 2, naming the file |
| S4 — a `ship.toml` of any size is read | turned: over 65,536 bytes is a stop |
| S5 — the words after `<path>: ` are the system's | turned for the shapes the one read names — a link, a FIFO, a folder, a file that is no regular file, a bad byte, a file over its bound — and for a name the folder's path lacks or refuses (`Not a directory`, `Permission denied`), which ride the module's phrase; a TOML error keeps the parser's words |
| R2, W4 — an empty `source` is `""` | turned by D8 |
| R5 — a `pending` of several lines keeps its inner newlines | as today |
| R6 — `describe` says nothing when the skipped check is refused or fails | as today |
| R8 — a tree that is no git repository, or whose `VERSION` is a folder, reads `mf live unknown` | as today |
| W7, W8 — `install` writes `source` before it checks the release, and a failed step leaves the earlier ones done | as today |
| W10 — an empty `pending` stands; `move` ignores it | as today |
| S6 — a byte-order mark stops; CRLF reads | as today |
| S7, S8 — an unknown table or key, a misspelled key and a scalar where a table goes read as nothing set | as today |
| S9 — `in_flight` takes TOML's integer spellings; a float is refused | as today |
| S10 — `status`, `report` and `cut` read `ship.toml` once and `run` twice | as today |
| S11 — a config folder of mode 0500 reads; a file of mode 0 stops | as today |

R5, R6, W7, W8, S7 and S8 look wrong and are left for a round of the person's: no decision turns them, and a move changes no behaviour a decision does not name.

## The cases

Phase 1 writes these in `tests/test_pinfiles_pins.py`, each green on today's code and red on its mutant; a bracketed code is the mutant's name, and the mutation run's scratch files are not kept.

- A case reaches the code through a caller that stays: `describe`, `move`, `install` and `main` of `pin.py`, `_ship_file`, `_cap` and `_pushes_tags` of the conductor.
- No case goes through the reader and writer of `pin.py`, which phase 3 deletes.
- Kept folder = `~/.mf-ship-origin`. World = an MF checkout with local tags `v0.1.0` and `v0.2.0`, its origin holding only `v0.1.0`, the origin URL kept; SK = `" · skipped v0.2.0: not on origin"`.

### Cases R — the pin's reads

- `describe()`, source=repo, pending=`"  v0.2.0 \t\r\n"` → `" · pending v0.2.0"`; pending of `" \n"` or hold of `"   \n"` counts as none → SK. [A04]
- `describe()`, pending=`"v0.2.0\nsecond line\n"` → `" · pending v0.2.0\nsecond line"`, all lines read. [A06]
- `describe()`, source=repo, pending and then hold each a folder → SK; source a folder → `""`; no exception. [A02]
- `describe()`, source=repo, pending and hold empty files → SK; empty source → `""`. [A06]
- `describe()`, bad byte `b"\xff\xfe"` in source, pending or hold, one at a time → `UnicodeDecodeError` escapes. [A07]
- `move()`, cwd=repo whose origin URL is kept and holds newer `v0.2.0`, `source` an empty file → `"pin: moved to v0.2.0"`, an empty source being the current folder. [A05, A06]
- `move()`, same cwd and origin, no `source` file → `None`, nothing linked. [A03]
- `describe()` with links host1 → tree `v0.1.0`, host2 → tree `v0.2.0`, both with `VERSION` → `""`; one tree only → `" · mf v0.1.0"`. [C01]
- one tree, no `VERSION`, tree not a git repo → `" · mf live unknown"`; `VERSION` a folder → same. [C08, C04]
- one tree that is a git repo, no tag → `" · mf live <short hash>"`; after a lightweight tag `v7.7.7` → `" · mf live v7.7.7"`. [C07, C06]
- source=repo, no pending or hold → SK; hold=`v0.1.0` → `""`; hold removed, pending=`v0.2.0` → `" · pending v0.2.0"`; both → `" · pending v0.2.0"`. [C13, C21]
- links into tree `v0.2.0` (`VERSION` `v0.2.0`), source=repo with local `v0.2.0` not on origin → `" · mf v0.2.0"` only. [C19]
- source a plain folder, not a repo → `""`; source a missing path → `""`. [C18]

Shapes, through `describe`, at each of `source`, `pending`, `hold` and `checkout`; a FIFO is read in a child with a 30 s timeout. Rows are `source / pending / hold / checkout`:

- link to a regular file with good text: SK / `" · pending v0.2.0"` / `""` / SK; links are followed.
- dangling link, folder, empty file: `""` / SK / SK / SK.
- bad byte: `UnicodeDecodeError` / same / same / SK; `describe` never reads `checkout`.
- 70,000 extra bytes after the text: `""` / the whole 70,019-character line (`" · pending v0.2.0\n" + "x"*70000`) / `""` / SK; no cap.
- kept folder missing: `""` all four. Kept folder mode 0500: SK / pending / `""` / SK.
- FIFO at the file: returns, exit 0, no stderr, under the timeout: `""` / SK / SK / SK.
- through `main`, `run --executor claude` with a bad byte in source, pending or hold: `UnicodeDecodeError` escapes `main`; stdout `run: halt · .minions/runs/<ts>.md`; the run log line `run · halt — conduct.py failed: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte · cause run`. A bad byte in `checkout`: `Run.ship()` returns 0.

### Cases W — the pin's writes

`mf` is `_mf(tmp_path)`, `k` is `<home>/.mf-ship-origin`, `mark` is a live mark holding our pid, `main` runs in process with `chdir(mf)`.

- `install(mf, "live")` in a home with no kept folder, umask 022, then `mark` and `install(mf, "live")` again: `k` 0700; `source` `<mf>\n`, `hold` `live\n`, `checkout` `<mf>\n`, `pending` `live\n`, each 0644; with umask 077 in a second home the files are 0600 and the folder 0700. [B04, B10]
- HOME at `<tmp>/no/such/home`, `install(mf, "v0.1.0")` returns `pin: linked v0.1.0`; the home and `k` (0700) are made; `source` holds `<mf>\n`. [B05]
- Origin newer (`v0.2.0` pushed after a bare install of `v0.1.0`), no pending, no hold, `mark` named `other` standing: `move()` is `None` and no `data/v0.2.0` or `.v0.2.0-*` exists; with `_fetch` patched to raise `Refused` it is still `None`. [D02]
- Pending `live`, no `checkout` file: `move()` is `pin: moved to live`, links into `<mf>/skills`. [D07]
- Pending `""`, `"\n"` or `"  \n"`, no kept origin: `move()` is `None`, links unchanged, the pending file stays. [D09]
- Pending `v0.0.0` after an install of `v0.1.0`: `pin: cannot move — <data>/v0.0.0/skills holds no mf-* skill`; links and pending unchanged. [D23]
- Non-link `~/.agents/skills/mf-ship`, pending `v0.1.0`: `move()` is `pin: cannot move — ~/.agents/skills/mf-ship exists and is not a link`; `pending` still `v0.1.0\n`, `source` unchanged. [D18]
- `install` live, install `v0.1.0`, pending `v0.2.0` exported: `move()` is `pin: moved to v0.2.0`; `k` holds `checkout`, `hold` (`v0.1.0\n`), `source`. [D25]
- `~/.claude/skills` mode 0500, pending `v0.1.0`: `move()` returns `pin: cannot move — [Errno 13] Permission denied: …`, no exception; pending stays. [D21]
- Worktree of `mf`, `install(worktree, "live")`: `source` is `<mf>`, `checkout` is the worktree, resolved, links into `<worktree>/skills`. [E03, E05, E16]
- `install` from a link to `mf` and from `mf/skills`: `source` and `checkout` are `<mf>`; then `_out` in the namespace faked to answer `str(link)` for `--show-toplevel` and `str(link/.git)` for `--git-common-dir`: both files still `<mf>`. Real git never answers a link, so the fake is the only way. [E01, E02]
- `_mf(pushed=("v0.1.0",))`, `v0.3.0` pushed then deleted locally, bare install: `pin: linked v0.3.0` with no `skipped` note. [E11]
- `install(mf, r)` for `r` in `next`, `vnext`, `v1.2`, `v0.1.0-rc1`, `LIVE`: `Refused("<r> is not a version tag or live")`; after them `source` written, `pending` and `hold` (`v0.1.0\n`) still standing. [E18, E20, E28]
- Bare install, no kept origin, `hold` `v0.1.0`: `Refused` `no run kept origin…`; `hold` stays, `source` written. [E29]
- Bare install, origin readable, `_remote` faked to fail `clone`: `Refused` `cannot clone v0.2.0 from origin: fatal: refused`; `hold` stays. [E10]
- Pending `v0.9.0`, non-link `mf-ship`, `install(mf, "v0.1.0")`: `Refused`; `pending` `v0.9.0\n`, `hold` `v0.1.0\n`, `source` written, no links. [E25]
- Pending `v0.9.0`, clean `install(mf, "v0.1.0")`: pending gone. [E24]
- Folder at `source`, `main install v0.1.0`: exit 2, `pin: cannot install — [Errno 21] Is a directory: '<k>/source'`; nothing else made, no export.
- `k` mode 0500 and empty: exit 2, `pin: cannot install — [Errno 13] Permission denied: '<k>/source'`; `k` empty.
- A file at `k`: exit 2, `pin: cannot install — [Errno 17] File exists: '<k>'`; the file untouched.
- Folder at `hold` + tag install, pending `v0.9.0`: exit 2 `[Errno 21] Is a directory: '<k>/hold'`; `source` written, pending stays, tree exported, no links.
- Folder at `checkout` + `live`: exit 2 `[Errno 21]`; `hold` `live\n`, `source` written, no links.
- Folder at `pending` + `mark` + tag: exit 2 `[Errno 21]`; `hold` written, no links.
- Folder at `pending`, no mark, tag: exit 2 `[Errno 1|21] … '<k>/pending'`, EPERM on macOS from `unlink`; the links are made, the folder stays, `hold` written.
- Folder at `hold`, bare install: exit 2 `[Errno 1|21] … '<k>/hold'`; `v0.2.0` exported, no links, `source` written.
- A link, to a file and dangling, at each of `source`, `hold`, `checkout`, `pending`: the write follows it; the link stays a link; the target holds the new text, made when dangling.
- A link at `pending` (tag install) and at `hold` (bare install): the removal takes the link, the target keeps `orig\n`. A FIFO at `pending` and a dangling link at `hold`, tag install: `install` succeeds, the FIFO is removed, `hold` is written through the dangling link.
- A FIFO with no reader at `source`, `hold`, `checkout` and `pending`, child `pin.py install`, 4 s: `TimeoutExpired`, each.

`move`'s first read:

- `source` a link to a file holding `<mf>\n`: `pin: moved to v0.1.0`, link stays. `source` empty: `pin: moved to v0.1.0`, `source` stays empty.
- `source` dangling, and `source` a folder: `None`, pending stays.
- Bad byte `\xff\xfe` in `source`, in `pending` or in `checkout` (pending `live`): `UnicodeDecodeError` out of `move`; links, `source`, `pending` unchanged. In `hold` with no pending and a kept origin: `UnicodeDecodeError`.
- `pending` a link to a file `v0.1.0\n`: `pin: moved to v0.1.0`, link removed, target stays. `pending` dangling or a folder: `None`, left in place.
- `pending` or `checkout` of 70,000 `x`: `pin: cannot move — [Errno 63|36] File name too long: …`, pending stays. `source` of 70,000 `x` with pending `v0.1.0`: moved.
- A FIFO at `source` or `pending`, child, 60 s: prints `None`, no block, pending stays; at `checkout` with pending `live`: `pin: moved to live`, falling back to `source`, pending removed.

### Cases S — the `ship.toml` read

`P` is `layout.ship_file()`.

- `_ship_file()`, P absent: returns `(P, {})`, P the real spelled path; an empty file the same; `[queue] in_flight = 2` gives `(P, {"queue": {"in_flight": 2}})`. [F09]
- `_ship_file()` with `[other]`, `[queue]`, `[push]` tables: the whole dict returned; `_cap()` 2, `_pushes_tags()` False; also with a first key `queue = 3` that is no table. [F12]
- `.config/minionsfactory` is a file, then `_ship_file`, `_cap` and `_pushes_tags`: `Stop` code 2, text `P: [Errno 20] Not a directory: 'P'`. [F03]
- P = `b"[queue]\nin_flight = 2\n# \xe9\n"`: `_cap` stops 2, `P: 'utf-8' codec can't decode byte 0xe9 in position 24: invalid continuation byte`; `b"\xff\xfe"` gives `… byte 0xff in position 0: invalid start byte`. [F08]
- P a link to a valid file: read through, cap 2, tags False, `_ship_file`'s path the link's; P a dangling link: `(P, {})`, no cap, tags pushed.
- P a folder: all three stop 2, `P: [Errno 21] Is a directory: 'P'`.
- No file, no config folder, an empty file: `_cap()` None, `_pushes_tags()` True.
- A 70,025-byte valid file, a long comment: read, cap 2.
- `[queue`: stop 2 `P: Expected ']' at the end of a table declaration (at end of document)`; a duplicate key: `P: Cannot overwrite a value (at line 3, column 14)`; a byte-order mark first: `P: Invalid statement (at line 1, column 1)`; a CRLF file reads.
- `a = [` x 1000 then `]` x 1000, and 400 nested inline tables: `RecursionError` escapes `_ship_file`, `_cap` and `_pushes_tags`; 100 deep reads fine; the first failing depth is arrays 497, inline tables 331 on 3.12.
- P a FIFO, `_cap()` in a child python, timeout 4 s: the child blocks. `slow`.
- Config folder mode 0500 with a readable file: read; file mode 0: stop 2 `P: [Errno 13] Permission denied: 'P'`, skipped as root.
- `in_flight` = `0 -1 1.5 2.0 "2" true false [2] {a = 1}`: stop 2 ``P: `in_flight` is not a whole number above 0``; `1_0` gives 10, `0x10` gives 16, `1` gives 1.
- `tags` = `"true" "yes" 1 0 1.0 [true] {a = 1}`: stop 2 ``P: `tags` is not true or false``.
- An unknown table or key (`[zzz]`, `extra = 1`): ignored; `queue = 3` and `push = 1`, scalars for tables: cap None, tags True; `[push]` with no `tags` and `[queue]` with no `in_flight`: None and True.
- A good cap with a bad tags: `_cap` 2 while `_pushes_tags` stops; a bad cap with `tags = false`: `_pushes_tags` False while `_cap` stops.

Callers, the reads counted by wrapping `_ship_file` in the conductor's dict, which `_cap` and `_pushes_tags` look up by name:

- `status` with `[queue]` and `tags = false`: output `run · unpushed main\nrun · tags — this machine pushes none`, 1 read. `slow`.
- `status` with `[queue\n`: exit 2, the exact output `P: Expected ']' at the end of a table declaration (at line 1, column 7)`; a deep file: `RecursionError` out of `main`.
- `report`, released on origin: exit 0, 1 read; `[queue\n`: exit 2, the same one-line text; a deep file: `RecursionError` out of `main`. `slow`.
- `run --executor claude`, empty primary, fake worker, valid file: exit 0, 2 reads, for `_cap` and `_pushes_tags`; a deep file: `RecursionError`, no `runs/active` made. `slow`.
- `cut`, runner swapped, `_start_run` stubbed, `in_flight = 2`: `cut: queued 0001-d · run started · pid 4242 · cap 2`, 1 read; a deep file: `RecursionError`, `cuts/` still holds only `0001-d`.

Equivalent mutants, which no case can tell: B01 (`if not text` differs only for `""`), E22 (a live mark's path is never a primary's), F11 (an empty parse and `{}`). A03 and A05 show only through `move`, run with the current folder set to the repository. A phase that renames `_out` fakes git's answer another way.

## Dependencies

None.

## Risks / Trade-offs

- **The gate runs long.** `0159-kept`'s end gate went red several times, about 8 minutes a run. Each station task runs the slow sets of [D10](#d10) at its own verify, so a break shows there.
- **A line only an error path reaches** goes red at the gate, not at `make check` ([D9](#d9)); each such line is named with its test.
- **`cloud_setup.py` writes through a dangling link** at `ship.toml`, since its `exists` follows links; the file stays a link, and the next command stops, exit 2 ([D12](#d12)).
- **A pin file or `ship.toml` that is a link now stops** where it was followed. An operator who links `ship.toml` into a dotfiles repository sees exit 2; the changelog says so.
- **An older pinned conductor** reads the new 0600 files as before: its read is plain.
- **`move` at a run's close** names a broken file and moves nothing; the links stay at the old release until the person fixes the file.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the pin on today's side, the module as copies, the stations through it, the fix that turns the readings, the record.
