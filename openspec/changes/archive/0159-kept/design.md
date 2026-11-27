# Kept — design

The conductor's and `gate_check.py`'s kept files move into `skills/mflib/kept.py`, then take one read and one write. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

A **kept file** is a file the conductor keeps in the home folder, `~/.mf-ship-origin/`, where no worker writes: the kept origin `<digest>`, `<digest>.default`, the offline base `<digest>.pushed`, the release ledger `<digest>.released/<change>`, the gate approval `<digest>.gate/<change>`, the live mark `live/<digest>`, `repos` and the probe mark `probe-<executor>-<pid>`. [layout](../../../skills/mflib/layout.py) names each path. Each file's writer sits in the conductor and its parser in another script, or in a copy: `pin.py` reads the origin and the live mark, `gate_check.py` the approval, and `tests/test_pin.py` writes an origin by hand.

The queue moved the same way in `0156-queue`: its module is `skills/mflib/queue.py`, its failures `OSError` subclasses the conductor words as a `Stop`. `kept.py` follows that shape on `statefile.py` and `layout.py`. The pin's files, `ship.toml` and the other readers of `repos` stay out.

The files are written today by unlink and `O_EXCL`, by `O_EXCL` alone, by `mkstemp` and `os.replace`, by plain `write_text` and by `O_APPEND` with `O_NOFOLLOW`. Reads follow a link, none is bounded, a FIFO blocks some of them, and a bad byte raises past every `except` that guards one. The mutation run of this region left cases no suite reaches; phase 1 writes them first.

```
phase 1   pins      tests only, green on today's code, red on the mutants
phase 2   module    kept.py, called by no script
phase 3   stations  conduct.py, pin.py, gate_check.py call it; no assert changes
phase 4   fix       the right sides: one read, one write, the stops
phase 5   record    spec, decisions, threat model, map, recipes
```

## Goals / Non-Goals

- **Goals:** each kept file's write, read, listing and removal in one module; the conductor, `pin.py` and `gate_check.py` go through it; a broken kept file stops its command and never reads as its permissive answer.
- **Non-goals:** the pin's files `source`, `pending`, `hold` and `checkout`, and `ship.toml`, which are `pins`' · `cloud_setup.py`, which keeps its own write of `ship.toml` until the cloud machine's Python is known · the viewer's `projects` and the metrics script's `_recorded_repos` · the cycle between `pin.py` and the conductor, and `CYCLE_FILES` · the process probe, of which only the mark moves · the scratch folder · the queue lock and the reads outside it · any gate rule for the home's names.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | One module, `skills/mflib/kept.py`, of layer `home`, on `layout` and `statefile` alone, takes the kept files | the queue's shape; each format's writer and parser sit in different scripts | a module per file; a module for `pins` too |
| [D2](#d2) | The module's functions and its failures are a fixed list | a caller and a test name each by one word | a class holding the primary |
| [D3](#d3) | A name stays as a short call when a test reaches it, a script borrows it or it holds the conductor's own `Stop`, log or git call; else it goes | a test may change only the line by which it reaches a name | every old name kept; every old name deleted |
| [D4](#d4) | A move changes no assert; each phase ends green; the pins come first; the tests have files of their own | an unchanged assert over moved code proves the move | a one-time split of `tests/test_conduct.py` |
| [D5](#d5) | A function first behaves as its copy does, and phase 4 alone changes a right side | the pins prove the move; the fix is a diff of its own | the fix in the move |
| [D6](#d6) | One read: no link, no block, a regular file alone, bounded, decoded strictly | no home read of the conductor's goes through the helper today | `read_text`; a hard-link check |
| [D7](#d7) | A broken file's answer is per file: a stop, none, or no head | the line's safe side differs by file | one answer for all |
| [D8](#d8) | A write is staged at 0600 and follows no link; a file written once stays; `repos` appends; a folder is made at 0700; a removal is by name under the folder's descriptor | the files are written in forms that differ today | one write for every file |
| [D9](#d9) | Only the cross-loads that name a kept file go: the conductor's of `pin.py` for `holder`, and `pin.py`'s of the conductor for `_kept_origin` | each other cross-load needs a name of the other that is no kept file's | cutting the cycle here |
| [D10](#d10) | A ledger entry is one commit id: 40 lower-case hex digits, whole text, stripped | `merge-base` accepts an abbreviation that a set member never matches | the first line, unstripped |
| [D11](#d11) | The record names the new rules in one added requirement; the Q205 sentence of the halt requirement is the one modified | each other sentence stays true | a modified block for every requirement that names a kept file |
| [D12](#d12) | `.default` is written with a newline and read stripped | the other one-line files end in one | no newline, as today |

### D1

`skills/mflib/kept.py` imports `layout` and `statefile` and no conductor class, so a failure the conductor words as a `Stop` is an `OSError` subclass of the same words. The conductor imports it as `import mflib.kept`, between `findings` and `layout`. The module spells no change-id pattern: an approval's or a ledger entry's change comes in as an argument, so card 0156·S1 stays untouched.

### D2

Every function takes the `primary` it names by `layout`'s digest. `Urls` is `tuple[list[str], list[str]]`; `Heads` is a `NamedTuple` of `heads: set[str]` and `bad: list[str]`.

| function | replaces | does |
|---|---|---|
| `origin(primary) -> Urls \| None` | `_kept_origin`'s read | the kept URLs, or None before a run's first |
| `origin_stands(primary) -> bool` | `is_file` of `primary_of`, `_read_url` and `_unread` | whether a kept origin stands |
| `keep_origin(primary, urls)` | the write of `_keep_origin` | write once |
| `default(primary) -> str \| None` | the reads of `_kept_default` and `_push_default` | the kept default branch's text, or None |
| `default_stands(primary) -> bool` | `exists` of `_keep_origin` | whether the name stands |
| `keep_default(primary, name)` | the `.default` write of `_keep_origin` | write once |
| `base(primary) -> str \| None` | `_offline_base` | the offline base's sha, or None |
| `base_stands(primary) -> bool` | `is_file` of `anchor` | whether a base stands |
| `keep_base(primary, sha)` | `_keep_base`'s write | replace |
| `record_release(primary, change, head)` | `_record_release` | one entry per change, replaced |
| `release_entries(primary) -> list[Path]` | the deleted `_ledger_entries` | every name in the ledger folder; none for a missing folder or a file at its name |
| `release_heads(primary) -> Heads` | `_ledger_heads`' read | each entry's head |
| `close_releases(primary, landed)` | the loop of `_close_releases` | remove each entry whose head `landed(head)` says is on the default branch |
| `approve(primary, change, hashed)` | the write of `approve_gate` | replace the change's entry |
| `approval(primary, change) -> str \| None` | `gate_check.approval` | the entry's first line, or None |
| `holder(mark) -> int \| None` | `pin.holder` | the pid a live mark holds while that process runs |
| `live(mine=None) -> list[str]` | `pin.live` | the marks standing, `mine` aside |
| `mark_live(primary, pid, parent) -> Path \| None` | the deleted `_mark_live` | write the run's mark; None when another process holds it |
| `unmark(mark, pid)` | the deleted `_unmark` | remove the mark when it holds `pid` |
| `record_repo(primary)` | `_record_repo` | add the primary's line to `repos`, once |
| `make_probe_mark(executor, pid) -> Path` | the create of `Run.probe` | an empty mark, made anew |
| `remove_probe_mark(mark)` | the unlink of `Run.probe`'s `finally` | remove it |
| `probe_executor(mark) -> str` | the `split` of `check_probe` | the executor the name holds |
| `probe_untouched(mark) -> bool` | the test of `check_probe` | whether the mark stands and is empty |

The failures are `Refused`, `Unwritten` and, from phase 4, `Broken`, each an `OSError` subclass, so a caller words a write failure by catching `OSError` and printing `strerror`. `Refused` says a folder of the kept files cannot be made or opened; `strerror` holds the error's. `Unwritten(path, cause)` says one write failed, naming the file, with the cause's `errno` and `strerror`. `Broken(path, phrase)` says a kept file cannot be read; `str` of it is `~/.mf-ship-origin/<name> cannot be read: <phrase>`, `<name>` the path under the kept folder.

### D3

The conductor's names that stay as short calls into the module: `_kept_origin`, `_keep_origin`, `_kept_default`, `_push_default`, `_refuse_origin`, `_read_url`, `_keep_base`, `_offline_base`, `_record_release`, `_ledger_heads`, `_close_releases`, `_record_repo`, `approve_gate`, `anchor`, `check_probe`, `probe_gate` and `Run.probe`, with `pin.py`'s `holder`, `live` and `_origin`. Tests seed or patch them, a script borrows them, or they hold a `Stop`, a log line or a git call: tests seed `_keep_origin`, and `_push_then_forge` swaps `_close_releases` for a no-op, which holds only while the name stays a global of the conductor.

`_ledger_entries`, `_mark_live` and `_unmark` are deleted: no test at the base reaches them by name, no script borrows them, and they hold file work alone. Their callers call the module. The pins that phase 1 writes do reach them, and phase 3 retargets those pins to the module before it deletes the names.

### D4

- In a move phase no assert changes, only the line by which a test reaches a name or plants a file; the conformance check holds it on the phase's diff.
- A region's new tests have files of their own: `tests/test_kept_pins.py` for phase 1's cases and `tests/test_kept.py` for the module's unit and round-trip cases. The old tests stay where they are.
- A case of `tests/test_kept_pins.py` is named by its group — `test_ledger_`, `test_origin_`, `test_remote_`, `test_base_`, `test_probe_`, `test_live_`, `test_repos_`, `test_approval_`, `test_anchor_`, `test_mixed_`, `test_shape_`, `test_odd_` or `test_write_`, and in phase 4 `test_broken_` or `test_stop_` — so a `-k` selects a group.
- A case of `tests/test_kept.py` is named by its group: `test_origin_`, `test_base_`, `test_ledger_`, `test_approval_`, `test_live_`, `test_repos_`, `test_probe_` or `test_roundtrip_`, and in phase 4 one prefix a task, named in the task.
- A new test over 1 s carries `slow`, which `make check` skips.
- No `Verify:` runs `tests/test_conduct.py` whole: it names a `-k` and `-n auto`, as does every command over more than one test file. The small files are named whole.

### D5

Phase 2 writes each function as its copy behaves today, a link followed and a bad byte raising included; phase 3 sends the scripts through it; phase 4 turns each reading the list below names. Phase 1's cases are therefore green on every phase but where phase 4 turns one, and phase 4 turns that case in the commit that turns the code.

### D6

- A read opens through `statefile.read_bytes`: no link, no block, a regular file alone.
- It asks for one byte past the bound and raises `Broken` over it, as `marks.read` does, and decodes strictly. The bound is 65,536 bytes, and for `repos` 262,144.
- A hard link reads as the file: no case plants a second name at an inode.
- The `Broken` phrases are `it is not a file` (a link, a folder, a FIFO), `it is over <bound> bytes`, `it is not text`, `it is not a pair of URL lists` and `it is not a commit id`.

### D7

| file | a link, FIFO, folder, bad byte, oversize file or wrong shape |
|---|---|
| kept origin, `.default`, offline base | `Broken`: the command stops, exit 2, naming the file; an empty offline base or one of white space alone is no base |
| gate approval | approves nothing: `approval` is None |
| ledger entry | no head, named, and it stays |
| live mark | reads as none |
| `repos` | reads as none, and nothing is appended |
| probe mark | as today |

- `Broken` is no `Stop`, so no `except Stop` of the conductor swallows it.
- `main` catches it beside `Stop`, prints it as `conduct: cannot run — <text>` and exits 2.
- On `run`'s own thread the `except Exception` around `conductor.ship()` in `run` logs it as the run's halt, naming the file, and `run` exits 2 for it, not 1. It first releases the run log's `held` events, which wait while a list is held, so the halt reaches the log; a `Broken` also removes the live mark.
- A `Broken` raised in a version's thread halts that version, naming the file, and the run's exit is the halt's. The kept origin, read in `Run.__init__`, stops `run` through `main`.
- `pin.py` catches `OSError`, which `Broken` is, and prints it as a failed command.
- A name that stands at the kept origin or `.default` and is no regular file is kept by no write ([D8](#d8)) and stops the next read.
- The bad names of the ledger go to the run log, one line each, or to stderr for a command ([D10](#d10)).

### D8

| file | write |
|---|---|
| kept origin, `.default` | written once: staged at 0600 only when `lstat` finds no name; a file, a link or a folder that stands stays |
| probe mark | an empty file at 0600, made anew: a stale mark of its name is unlinked by name first |
| offline base, ledger entry, gate approval, live mark | staged through `statefile.write` at 0600, replacing a file or a link at the name and leaving a link's target |
| `repos` | one append to a regular file that stands, through no link, made first by `statefile.touch` at 0600 |

- A kept folder is made at 0700 by `statefile.folder` with `mode=0o700` and `layout.kept_dir()` as its `root`. The folder `<digest>.released`, `<digest>.gate` or `live` is its one part, so the kept folder is 0700 too and a link at the part is refused; a file that sits in the kept folder itself takes the call with no part. The mode of a folder that stands is left. A removal opens it by `statefile.open_folder` on the same root and part.
- A removal unlinks the name under that descriptor; a folder that cannot be opened removes nothing.
- A failed staged write leaves no staged file. Writers of one name race on the staged name `<name>.tmp`, and the loser gets `Unwritten`, never a half file.

### D9

The conductor loads `pin.py` for `trees`, `describe` and `move`, and `pin.py` loads the conductor for `_scratch`, `SSH_COMMAND` and `GIT_TIMEOUT`. So `_pin` stays, `CYCLE_FILES` stays, and `_scratch` stays a `PRIVATE_REACH` entry. Only `("pin.py", "_kept_origin")` leaves the list, in phase 3, the phase that ends the borrow. `holder` and `live` stay in `pin.py` as short calls for its own callers and tests.

### D10

`release_heads` takes a ledger entry as a head when its whole text, stripped, is 40 lower-case hex digits. Any other entry is named in `bad` and stays, so a person decides.

The conductor reaches the log through a keyword `on_bad`, a callable of one string, on `_ledger_heads`, `_foreign_commit`, `_local_releases` and `_unpushed`; it is not their `notes`. Each forwards it down to `_ledger_heads`, and each defaults to a line on stderr, `conduct: ledger — <name> is no commit id: skipped`, which a command prints. `Run` passes a method that logs the same text as a `ledger` event at each call of those functions, so the one-argument calls that tests make keep their set.

### D11

The delta adds one requirement for the rules of the kept files, and modifies the halt requirement's sentence of what a run keeps in the home folder, which gains `.default`, the live mark, `repos` and the probe mark. The sentences on the origin, `.default`, the base, the approval and the mark stay true; the added requirement states what a broken file does. The pin's files join the list in `pins`.

### D12

`.default` is written `<name>\n` and read stripped, so a file an older run kept reads the same. An older pinned conductor reads the new text as a moved default and halts its pushes; the changelog says so. Pins only move forward here.

## Tests

The change adds tests at the unit layer and, through the loaded conductor and real git repositories, at the integration layer. It adds no end-to-end test and removes none; no test is deleted or merged, so no `I16` table stands. Phase 3 changes the line by which a test reaches a name in `tests/test_conduct.py`, `tests/test_pin.py` and `tests/test_gate_check.py`; phase 4 turns the cases of the readings below in `tests/test_kept_pins.py`, and the structure test loses one `PRIVATE_REACH` entry.

| file | layer | holds | count command |
|---|---|---|---|
| `tests/test_kept_pins.py` | integration | the cases below, each on today's side | `uv run pytest tests/test_kept_pins.py --collect-only -q` |
| `tests/test_kept.py` | unit | each function of D2, a round-trip case of each format, each phase 4 failure | `uv run pytest tests/test_kept.py --collect-only -q` |
| `tests/test_conduct.py` | integration | the line by which a test reaches a name or plants a file | `git grep -c "^def test_" -- tests/test_conduct.py` |
| `tests/test_pin.py` | integration | its hand-written origin planted through the module | `git grep -c "^def test_" -- tests/test_pin.py` |
| `tests/test_gate_check.py` | unit | the line that plants an approval, and a bad byte approving nothing | `git grep -c "^def test_" -- tests/test_gate_check.py` |
| `tests/test_claim.py` | integration | the `_pin` stub of `run` keeps `move` alone, nothing reading its `holder` | `git grep -c "^def test_" -- tests/test_claim.py` |
| `tests/test_structure.py` | unit | `PRIVATE_REACH` loses an entry; the map row and `names` cells hold | `git grep -c "^def test_" -- tests/test_structure.py` |

## The cases

Phase 1 writes these again in `tests/test_kept_pins.py`, each on today's side. They come from the mutation run at the base of this version, a code in brackets a mutant's name there; the scratch files are not kept.

- `c` is the loaded conductor, `p` a `_primary` repo, `kept` the home's `.mf-ship-origin`, `H` a head, `S` a sha.
- No case starts a worker.
- A case that reads a FIFO runs in a child with a timeout and carries `slow`.

**L — the ledger**
- `_record_release(p, "0001-a", H)` in a home with no kept folder: kept folder made (mode 0755, reading 3), `<digest>.released` 0700, one entry named by the change, 0600, text `H\n` (L01, L02, L07, L08, L09, L10).
- Record `0001-a`, `0002-b`, then `0001-a` again with a new head: two entries, the first holds the newest head (L04); a link at the entry's name is replaced by a regular file and its target left.
- `_ledger_entries`, deleted in phase 3: no folder `[]`; a file at the folder name `[]`; entries `0001-a`, `0002-b` and `.hidden` all listed (L11, L12, L13, L14).
- `_ledger_heads`: no folder `set()`; entries `"h1\nh1b\n"`, `"h2 \n"`, `"h3"`, `""` give `{"h1", "h2 ", "h3", ""}` (L17, L18; reading 1).
- `_close_releases(p, main)` with `_released` v0.1.0, v0.2.0 and `_unmerged_release` v0.3.0: only `release-v0.3.0` stays, its text unchanged, and a second call changes nothing (L25); an entry whose first line is the landed head and has a second line is removed; one `_released` entry and base = the commit before it: entry stays; no folder: quiet.

**O — kept origin, `.default`, offline base**
- `_kept_origin(p)`: no file `None`; file `[["u1"],["u2","u3"]]` gives `(["u1"],["u2","u3"])` (O02, O03, O04, O05); a folder at the name `None` (O01).
- `_keep_origin(p)` over a local bare origin with fetch URL A and push URL B (push URL set in the global git config, not the repo's): returns `None`; kept folder 0700; origin file 0600 with `[[A],[B]]` (O06, O09, O23, O24); `.default` 0600 with text `main` and no newline (O10, O15, O22).
- A standing origin file `[["old"],["old"]]` and `.default` `dev`, origin repointed: both stay, returns `None` (O08, O11); with only `.default` removed it is written again (O15).
- No origin: file `[[],[]]`, no `.default`, `None` (O16); an origin path that does not exist: file kept, no `.default`, `None` (O19); an origin whose HEAD is detached (`update-ref --no-deref HEAD <sha>`): file kept, no `.default` (O18); a dangling link or a folder at `.default`: left alone, returns `None` (O17 equivalent, O20).
- Kept folder mode 0500: returns `"Permission denied"` (O12, O13, O39); the same with only `.default` missing (O21); `os.open` patched to raise a bare `OSError()` returns `"OSError"` for the origin file and again for `.default` (O13, O39). A write that fails after the origin file is made leaves a half-written file, and a failed `.default` write leaves its file.
- `_kept_default(p)`: no file and `refs/remotes/origin/HEAD` → `origin/trunk`: `trunk`; no such ref: `main`; file `dev\n`: `dev\n` (not stripped); file `dev`: `dev` (O25, O26, O27); a folder at the name reads as git's (`trunk`) (O25).
- `_keep_base(p, S)`: returns `None`; folder 0700, file 0600, text `S\n`, nothing else beside (O29, O31, O34); with the folder standing at 0755: second call replaces, folder stays 0755, no leftover (O30, O33); a non-empty folder at the file name: returns one of `Is a directory`/`File exists`/`Directory not empty` and one hidden `.<digest>.pushed-xxxx` temp stays in the kept folder (O35, O36); kept folder mode 0500: `"Permission denied"` (O37); a file at the kept folder: `"File exists"` (O38); `tempfile.mkstemp` patched to raise `OSError()`: `"OSError"` (O39).
- `_offline_base(p)`: no file `None`; `S\n`, `  S  \n\n`: `S`; `abc\ndef\n`: `abc\ndef`; empty and whitespace-only `None` (O41, O42, O43, O44); a folder at the name `None` (O40).
- `_push_default(p, url)` over a bare origin whose HEAD names `main`: no `.default` → `main`; `.default` `main` → `main`; `.default` `` (empty) → Stop code 1 (O46, O47); `.default` `dev` → Stop 1 with the text `conduct: halt — origin's HEAD names main, and the run kept dev: a person decides, then removes ~/.mf-ship-origin/<digest>.default` (O49, O51, O54); `.default` `main\n` → Stop 1, `kept main\n:` (O52); origin HEAD detached: Stop 1 with the `names no branch: a person pushes the default branch, or points origin's HEAD at it` text, and with `.default` `main` the `names no branch, and the run kept main:` text (O48, O50, O51); a folder at `.default` → `main` (O45).
- `_refuse_origin(p)` with fetch `https://example.invalid/a.git` and the push URL `…/b.git` set in the global git config: returns `(fetch-list, push-list)` with no kept file, and with an equal one; a kept file whose push list is the fetch list: Stop 1 (O56, O57, O58); a kept file of other URLs: Stop 1 ending `or remove ~/.mf-ship-origin/<digest> to keep what it reads now` (O59, O65); no origin: `([], [])`; a local path with `MF_SHIP_AGENT` unset: Stop 1 `points origin at a local repo`; set: returned (O60, O63); a local push URL alone: Stop (O61); `/x/a:b/c` Stop, `host:path` accepted (O62 equivalent: `fullmatch` against `match`); the agent returns fetch then push (O64); `core.sshCommand` set in the repo's config: Stop 1 `could name a program` (O55).
- `_read_url(p, first_read)` with a network origin: `True` reads with no kept file, `False` reads `None`, with a kept file `False` reads the URL (O66, O67, O71); a folder at the kept name: `None` (O67); no origin: `None` for both (O68); two fetch URLs: the first (O70); fetch URL, not the push URL (O69).

**M — the probe mark, live mark, repos**
- `check_probe(s, mark)` on a scratch repo whose HEAD holds `probe.txt` `ok\n` and whose `.gated` exists: empty mark `None`, mark `None` `None`; a mark of 1 byte and of 8 bytes, a gone mark, a folder at the mark: `codex wrote outside its reach: it runs unsandboxed` (named by `probe-<executor>-<pid>`) (M03, M04, M06); mark `probe-claude-7` names `claude` (M01).
- `.arch`: a dangling link `the worker's shell runs an unreadable .arch on a <arch> host` (M07); text of 16 characters named (`runs as aaaa…`), 17 and 20 unreadable (M09); the native arch in upper case is a different shell (M14); the native arch passes.
- `probe.txt` absent `HEAD holds no probe.txt`; `no\n` `probe.txt reads 'no'`; `ok` with no newline and `  ok \n` pass (M12); no `.gated`, or `.gated` a folder: `make gate left no .gated` (M13).
- `_mark_live(pin, p)`, deleted in phase 3 (pin = `c["_pin"]()`): returns `live/<digest>`, text `<pid>\n`, kept and live folders 0700 (M18, M19, M20, M21, M22, M24, M25); again from the same process: same mark (M20, M21); a mark holding the parent's pid, its own, `3999999`, `junk`, or empty is taken over (M15, M16); a live other process's pid (a `sleep` child) is left and `None` returned (M17); a file at the kept folder and a kept folder of mode 0500 return `None` (M23); a folder at the mark returns `None`.
- `_unmark(pin, mark)`, deleted in phase 3: removes the mark holding this pid; `None` is quiet (M38); a mark holding the parent's pid, `3999999` or `junk` stays (M39, M42).
- `_record_repo(link-to-p)`: kept folder 0700, `repos` 0600, one line `<p resolved>\n`, and a second call with `p` adds nothing (M26, M33, M34, M35); two repos give two lines (M27); a recorded line `<p>x` does not stop `<p>` being added (M29); a list `\xff\xfe\n` takes the append (M36); a dangling link at `repos`, and a link to a regular file, write nothing through (M32, M37); a file at the kept folder or a folder of mode 0500 records nothing and raises nothing; a list of mode 0 stays as it is (M37).
- `Run.probe("claude")` with `fake("first-turn")`, a run's claim folder, and `spawn` wrapped: at the spawn the mark exists, empty, 0600, in a 0700 folder (M43, M44, M45, M46, M48), the call passes `limits=True` and the given `deadline` (M64, M65), `.gitignore` of the scratch reads `.gated\n.arch\n` and there is no `tree` (M61, M62, M63, M68); afterwards no `probe-*` in the kept folder, the scratch is gone (M51, M53), `claude` is in `probed`, no halt, a `check — probe · pass` event (M59, M66); with the kept folder standing at 0755 and a stale `probe-claude-<pid>` of text `junk`: the mark is empty at the spawn, the folder keeps 0755 (M45, M46); kept folder mode 0500: no spawn, one halt `probe — cannot write the probe mark: Permission denied` (M49, M50); a file at the kept folder: no spawn, one halt with that prefix, and `probe` then raises `NotADirectoryError` out of its `finally` (reading 14); `PATH` empty and no agent: halt once `probe-nosuchexec — nosuchexec is not on PATH`, and for the run's own executor `probe — claude is not on PATH` (M54, M55, M56); `_unlinked` patched to raise `Stop(2, "skill not linked")`: one halt `probe — skill not linked` and no spawn (M57); `fake("unsandboxed")`: one halt `probe check fail — claude wrote outside its reach: it runs unsandboxed`, no mark left, not probed (M58); the mark is named by this process's pid (M67).

**G — approval, anchor**
- `approve_gate(root, "0002-gate", H)` for a version made by `_version`: returns `approve-gate: approved — H · 0002-gate`; `<digest>.gate` 0700, entry `0002-gate` 0600, text `H\n` (G05, G11, G12, G15, G16); a second approval with another hash replaces the first (G07, G08, G09); a link at the entry is replaced and its target left; an unknown change and a branch with no worktree: Stop 2 `approve-gate: cannot run — no version worktree holds <change>` (G01, G02); `H+"0"`, `H[:-1]`, `H.upper()`, `"x"+H`, `not-a-hash`, empty: Stop 1 `approve-gate: refused — not the hash a halt names: <hash>`, nothing written (G03, G04); a file at the kept folder: Stop 2 `…cannot write the approval — Not a directory; a sandbox refuses the home folder: run it outside one`, kept folder 0500: `Permission denied` (G13, G14).
- `anchor(root, yes)` over a bare origin with a `_released` v0.1.0 pushed: `yes` = the tracked sha writes the base (text `S\n`) and returns `anchor: S · Merge branch 'release-v0.1.0'`; `yes` = `S[:8]`, `S[:-1]` or empty: Stop 2 `origin/main is S, not <yes>`, base not written (G30, G35); `yes` None: Stop 1 with the `anchor: check S · …` line (G29); `.default` `trunk`: Stop 2 `origin/trunk is missing` (G22); `core.sshCommand` in the repo's config: Stop 1 `could name a program` (G17); kept folder mode 0500: Stop 2 `anchor: cannot write the offline base — Permission denied; a sandbox refuses the home folder: run it outside one` (G32, G33); a folder at the base: Stop 2 `cannot write the offline base` (G20); a base standing: Stop 2 `an offline base stands: ~/.mf-ship-origin/<digest>.pushed`; a fresh origin with no release merge: Stop 2 `origin/main is no release merge`; the tracking ref on a commit off `main`: Stop 2 `origin/main is not on main` (G26, G27, G28).
- `approval(change)` (module loaded by `importlib` with `_primary` patched): no entry `None`; `H\nsecond\n` → `H`; `H \n` → `H ` (not stripped); empty entry → `""`; a folder at the entry `None`; a bad byte raises `UnicodeDecodeError`; an entry of mode 0 `None`; another change `None` (G36, G37, G38, G39, G40, G41).

**C — mixed functions**
- `primary_of(tree)` for a version worktree outside the primary: no kept origin: Stop 1 `…no run kept its URLs`; a folder at the kept name: Stop 1; a regular kept file: returns the primary (C01, C02, C03, C04).
- `_unread(p)` over a bare origin: false with no merged release tag; true after `_released` v0.1.0; still true with a folder at the kept name; false with a regular kept file (C05, C06).
- `c["Run"](p, "claude").pushes`: `["/a.git"]` from the repo's origin, `["/p1.git","/p2.git"]` with a kept file `[["/f.git"],["/p1.git","/p2.git"]]` (C17, C18).
- `Run.unpushed()` with `offline`, a kept base, `_released` v0.2.0 past it, `.default` `main` and `origin/HEAD` → `trunk`: ` · unpushed main v0.2.0`; with `offline` false: `""` (C19, C20).
- `_unpushed(p, first_read=False)` with a kept origin file and `origin/HEAD` → `trunk`: Stop `origin has no trunk`, no base kept (C11); `_unpushed(p, first_read=True, start=False)` over an origin that holds the release: the base file reads the origin's tip and the ledger holds no head (C13, C14, C16).
- `run`: with `Run.ship` stubbed and `mflib.claim.take` raising `PermissionError`: exit 2, no live mark (C40); with `_close` raising `RuntimeError`: the error propagates and no live mark stands (C42).
- Offline flow (`_offline_retries`, origin renamed away, `_keep_base` at `main`, one version): the run logs `0001-todo · ledger — 0001-todo <head>` and `_ledger_heads` holds that head (C25, C26); with `.default` `trunk` while git's default is `main`: the run halts (exit 1) with a halt naming `trunk` and no ledger event (C28 killed by the suite; the case pins it).
- `Run.push([("refs/heads/main", new)])` over a history that holds an octopus merge before the kept base: returns true, no halt, the base becomes `new`, origin holds `new` (C29).

**No mutant reaches**
- At the kept origin, `.default`, the offline base, a ledger entry, the approval, the live mark and `repos`: a link, a FIFO read in a child with a timeout, a folder, a bad byte, an empty file and a file over its bound, each on today's side. No case plants a second name at an inode.
- A write in `_keep_origin` that fails after the file is made leaves a half-written file; one in `_keep_base` leaves its temp file.
- The ways `.default` guards its write: a live link skips the write, a dangling link hits `FileExistsError`.
- The readers of `repos`: the conductor's, the viewer's `projects` and the metrics script's `_recorded_repos`, each on a list with a bad byte and a list of mode 0.
- `.default` is written with no newline.

Equivalent: L06 and G10 (the entry is unlinked just before the create, so `O_EXCL` sees a name only through a race between the two calls), L26 (`unlink` of an entry just listed), O17 (`is_file` against `exists` at `.default`), O32 (`os.replace` against `os.rename` on one volume), O53 (`kept or name` where `kept` is `None` or equals `name`), O62 (`NETWORK_URL` ends in `.+` or `.*`), M10, M31 (`os.fdopen(fd, "a")` seeks to the end), M40, M41 and M47. Unpinned: C21 and C22, `Run.advance`'s read of the offline base at integrate: no case stays inside the function, and phase 3 changes that line by its call alone.

## The readings

Each reading of the mutation run, by its number there. "As today" means pinned by phase 1's cases, kept by the module in phase 2 and by the stations in phase 3, and still so after phase 4.

**As today, through every phase**

- 2 — `_ledger_entries`, deleted in phase 3: every name in the folder is listed; a file at the folder's name and a missing folder give none.
- 4 — a link at a ledger entry's or the approval's name is replaced by a regular file and its target left.
- 7 — with no `origin`, the kept origin holds two empty lists.
- 11 — `_push_default`: exit 1 in both cases, the kept file named in the remedy, `no branch` for a missing HEAD, an empty `.default` a name that differs.
- 12, 13 — `_refuse_origin`'s refusal of a program key and its exit 1 for a changed origin; `_read_url`'s first fetch URL.
- 15, 16 — `check_probe`'s reading of the mark and of `.arch`.
- 17 — `_mark_live`'s take-over and `_unmark`'s own-pid removal.
- 19, 21 — `approve_gate`'s and `anchor`'s exits and refusals.
- 22 to 26 — `Run.unpushed`, `Run.__init__`'s push list, `_unpushed`'s first read, `Run.push`'s scan past the base, `run`'s removal of the live mark.
- 6, in part — `_keep_origin` keeps no `.default` and says nothing when origin is unreachable or its HEAD names no branch.
- 9, in part — a file at the kept folder's name: the keep of the base returns quietly; a folder that stands keeps its mode.
- 10, in part — an offline base that is empty or whitespace alone reads as none.
- 20, in part — an empty approval is the empty string, which approves nothing; the first line is the value.
- 5, in part — a folder at `repos` reads as none.

**As today until phase 4, where a decision turns it**

- 1 — a ledger entry is one commit id: its whole text, stripped, is 40 hex digits; an entry with a second line, a space inside or nothing is no head, is named and stays ([D10](#d10)). Today the first line, unstripped, is the head.
- 3 — every folder the module makes is 0700, the home's `.mf-ship-origin` included when the ledger, the approval or the probe is the first write; a folder that stands keeps its mode ([D8](#d8)). Today that parent takes the umask's mode.
- 5, 27 — a folder, or anything that is no regular file, at the kept origin, `.default` or the offline base stops the command, exit 2, naming the file; `anchor`, `primary_of` and `_unread` with it ([D6](#d6), [D7](#d7)). Today it reads as absent.
- 6, in part — a link or a folder standing at `.default` or at the kept origin: the keep writes nothing over it and the read that follows stops, exit 2, naming the file ([D7](#d7), [D8](#d8)). Today the keep is silent and the read takes it as absent.
- 8 — `.default` is written with a newline and read stripped; `main\n` is `main` and halts no push ([D12](#d12)).
- 9, in part — a failed keep of the base leaves no staged file ([D8](#d8)).
- 10, in part — an offline base that is not empty and not 40 hex digits, stripped, stops the command, exit 2, naming the file ([D7](#d7)). Today `abc\ndef` is read as a base.
- 14 — `Run.probe` with a file at the kept folder's name halts as it logs and raises nothing: the mark is removed by its name under the folder's descriptor, and a folder that cannot be opened removes nothing ([D8](#d8)).
- 18 — `_record_repo` reads `repos` by the one read: a bad byte, a list over 262,144 bytes or a name that is no regular file is a list that cannot be read, and then it records nothing, quietly ([D6](#d6), [D7](#d7)). Today a bad byte is replaced and the line appended.
- 20, in part — an approval with a bad byte approves nothing: `None`, no raise ([D7](#d7)).

## Dependencies

None.

## Risks / Trade-offs

- **An older pinned conductor** reads `.default` with a newline as a moved default and halts its pushes ([D12](#d12)); the changelog says so, and pins only move forward.
- **Phase 3 is wide**: it moves the files of `conduct.py`, `pin.py` and `gate_check.py`. Phase 1's cases are its proof, and a move changes no assert.
- **Mutants C21 and C22 stay unpinned**; conformance reads the line phase 3 changes there.
- **`Broken` is an `OSError`**, so an `except OSError` around a kept read catches it: `_record_repo`, `approval` and `holder` want that, and no other kept read sits under one.
- **A race on `<name>.tmp`** between two writers of one name ends in `Unwritten` for the loser; the approval's writer and a live run write different files.

## Verdict

Ready to build in order: the pins, the module, the stations, the fix, the record. Each phase ends on a green `make check`, and the last on a green `make gate`.
