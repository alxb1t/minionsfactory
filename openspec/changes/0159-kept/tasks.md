# Kept — tasks

The phases run in order: the pins, the module, the stations, the fix, the record. Each task names its files; the decisions are in [design](design.md).

## Progress

- [x] 1 — The pin · moderate
- [x] 2 — The module · hard
- [x] 3 — The stations · hard
- [x] 4 — The fix · hard
- [x] 5 — The record · moderate

## 1 — The pin

- [x] 1.1 Create `tests/test_kept_pins.py` with its fixtures: the loaded conductor `c`, a `_primary` repo `p` of its own helper, and the isolated home folder. Add one case, `test_the_kept_folder_lies_under_the_home`, that `kept_dir` is under it.
  Verify: `uv run pytest tests/test_kept_pins.py -n auto -q` exits `0`.
- [x] 1.2 Write the ledger cases of [the cases](design.md#the-cases) in `tests/test_kept_pins.py`, each on today's side and named `test_ledger_…` ([D4](design.md#d4)).
  Verify: `uv run pytest tests/test_kept_pins.py -k ledger -n auto -q` exits `0`.
- [x] 1.3 Write the cases of `_kept_origin`, `_keep_origin` and `_kept_default` in `tests/test_kept_pins.py`, each named `test_origin_…`, a failing write as `Permission denied` and a bare `OSError()`.
  Verify: `uv run pytest tests/test_kept_pins.py -k origin -n auto -q` exits `0`.
- [x] 1.4 Write the cases of `_keep_base` and `_offline_base` in `tests/test_kept_pins.py`, each named `test_base_…`.
  Verify: `uv run pytest tests/test_kept_pins.py -k base -n auto -q` exits `0`.
- [x] 1.5 Write the cases of `_push_default`, `_refuse_origin` and `_read_url` in `tests/test_kept_pins.py`, each named `test_remote_…`, the halt texts word for word.
  Verify: `uv run pytest tests/test_kept_pins.py -k remote -n auto -q` exits `0`.
- [x] 1.6 Write the cases of `check_probe`, its `.arch` readings and `Run.probe` in `tests/test_kept_pins.py`, each named `test_probe_…`, the run through `fake("first-turn")` with `spawn` wrapped.
  Verify: `uv run pytest tests/test_kept_pins.py -k probe -n auto -q` exits `0`.
- [x] 1.7 Write the cases of `_mark_live` and `_unmark` in `tests/test_kept_pins.py`, each named `test_live_…`, the live other process a `sleep` child.
  Verify: `uv run pytest tests/test_kept_pins.py -k live -n auto -q` exits `0`.
- [x] 1.8 Write the cases of `_record_repo` in `tests/test_kept_pins.py`, each named `test_repos_…`.
  Verify: `uv run pytest tests/test_kept_pins.py -k repos -n auto -q` exits `0`.
- [x] 1.9 Write the cases of `approve_gate`, `anchor` and `approval` in `tests/test_kept_pins.py`, each named `test_approval_…` or `test_anchor_…`, `approval` loaded by `importlib` with `_primary` patched.
  Verify: `uv run pytest tests/test_kept_pins.py -k "approval or anchor" -n auto -q` exits `0`.
- [x] 1.10 Write the mixed cases of [the cases](design.md#the-cases) in `tests/test_kept_pins.py`, each named `test_mixed_…`: `primary_of`, `_unread`, `Run.pushes`, `Run.unpushed`, `_unpushed`, `run`, the offline flow and `Run.push`.
  Verify: `uv run pytest tests/test_kept_pins.py -k mixed -n auto -q` exits `0`.
- [x] 1.11 Write the cases of a link, a FIFO read in a child with a timeout, a folder, a bad byte, an empty file and a file over its bound at the kept origin, `.default`, the offline base and a ledger entry, each named `test_shape_…`, each on today's side and each FIFO case marked `slow`.
  Verify: `uv run pytest tests/test_kept_pins.py -k shape -n auto -q` exits `0`.
- [x] 1.12 Write the same shapes at the approval, the live mark and `repos`, each named `test_odd_…`, no case planting a second name at an inode.
  Verify: `uv run pytest tests/test_kept_pins.py -k odd -n auto -q` exits `0`.
- [x] 1.13 Write the cases of a write that fails after the file is made in `_keep_origin` and `_keep_base`, of the ways `.default` guards its write, of the readers of `repos` and of `.default` written with no newline, each named `test_write_…`.
  Verify: `uv run pytest tests/test_kept_pins.py -k write -n auto -q` exits `0`.

## 2 — The module

- [x] 2.1 Create `skills/mflib/kept.py` with its docstring, imports of `layout` and `statefile` alone, `Urls`, `Heads` and the failures `Refused` and `Unwritten` of [D2](design.md#d2). Add its row, layer `home`, `names` `layout.py, statefile.py`, to `docs/modules.md` between `findings.py` and `layout.py`.
  Verify: `uv run pytest tests/test_structure.py -n auto -q` exits `0`.
- [x] 2.2 Write `origin`, `origin_stands`, `keep_origin`, `default`, `default_stands` and `keep_default` in `skills/mflib/kept.py`, each as its copy in `skills/mf-ship/scripts/conduct.py` behaves ([D5](design.md#d5)). Create `tests/test_kept.py` with their unit cases, each named `test_origin_…`, a failure raised as `Unwritten`.
  Verify: `uv run pytest tests/test_kept.py -k origin -n auto -q` exits `0`.
- [x] 2.3 Write `base`, `base_stands` and `keep_base` in `skills/mflib/kept.py` as their copies behave, with their unit cases in `tests/test_kept.py`, each named `test_base_…`.
  Verify: `uv run pytest tests/test_kept.py -k base -n auto -q` exits `0`.
- [x] 2.4 Write `record_release`, `release_entries`, `release_heads` and `close_releases` in `skills/mflib/kept.py` as their copies behave, `bad` of `Heads` empty. Write their unit cases in `tests/test_kept.py`, each named `test_ledger_…`, among them a folder at an entry raising `Unwritten` naming the path.
  Verify: `uv run pytest tests/test_kept.py -k ledger -n auto -q` exits `0`.
- [x] 2.5 Write `approve` and `approval` in `skills/mflib/kept.py` as their copies behave, with their unit cases in `tests/test_kept.py`, each named `test_approval_…`.
  Verify: `uv run pytest tests/test_kept.py -k approval -n auto -q` exits `0`.
- [x] 2.6 Write `holder`, `live`, `mark_live` and `unmark` in `skills/mflib/kept.py` as `holder` and `live` of `skills/mf-ship/scripts/pin.py` and the mark functions of the conductor behave, with their unit cases in `tests/test_kept.py`, each named `test_live_…`.
  Verify: `uv run pytest tests/test_kept.py -k live -n auto -q` exits `0`.
- [x] 2.7 Write `record_repo` in `skills/mflib/kept.py` as its copy behaves, with its unit cases in `tests/test_kept.py`, each named `test_repos_…`.
  Verify: `uv run pytest tests/test_kept.py -k repos -n auto -q` exits `0`.
- [x] 2.8 Write `make_probe_mark`, `remove_probe_mark`, `probe_executor` and `probe_untouched` in `skills/mflib/kept.py` as the probe's lines behave, with their unit cases in `tests/test_kept.py`, each named `test_probe_…`. `Run.probe` keeps its own handling of the failure ([D5](design.md#d5)).
  Verify: `uv run pytest tests/test_kept.py -k probe -n auto -q` exits `0`.
- [x] 2.9 Write in `tests/test_kept.py` a round-trip case of each format, each named `test_roundtrip_…`: the kept origin, `.default`, the offline base, a ledger entry, an approval, a live mark and `repos`, each written by the module's writer and read by its reader.
  Verify: `uv run pytest tests/test_kept.py -k roundtrip -n auto -q` exits `0`.

## 3 — The stations

- [x] 3.1 In `skills/mf-ship/scripts/conduct.py` import `mflib.kept` between `findings` and `layout`, and send `_kept_origin`, `_keep_origin`, `_kept_default` and `_push_default` through it ([D3](design.md#d3)): `_keep_origin` keeps its `_urls`, `_origin_head` and `Stop` handling and returns the `strerror`, or the type name, of an `OSError` the module raises. Add `kept.py` to the conductor's `names` in `docs/modules.md`.
  Verify: `uv run pytest tests/test_kept_pins.py -k "origin or remote" -n auto -q` exits `0`.
- [x] 3.2 Send `_refuse_origin`, `primary_of`, `_read_url` and `_unread` of `skills/mf-ship/scripts/conduct.py` through `origin` and `origin_stands`, their halt texts as they are; a test changes only the line by which it reaches a name ([D4](design.md#d4)).
  Verify: `uv run pytest tests/test_kept_pins.py tests/test_conduct.py -k "remote or mixed or kept_urls or refused_home or no_worker_pushes" -n auto -q` exits `0`.
- [x] 3.3 Send `_keep_base`, `_offline_base` and `anchor` of `skills/mf-ship/scripts/conduct.py` through `keep_base`, `base` and `base_stands`; `_keep_base` returns the `strerror`, or the type name, of an `OSError` the module raises, as it does.
  Verify: `uv run pytest tests/test_kept_pins.py tests/test_conduct.py -k "base or anchor" -n auto -q` exits `0`.
- [x] 3.4 Send `_record_release`, `_ledger_heads` and `_close_releases` of `skills/mf-ship/scripts/conduct.py` through the ledger functions, `_close_releases` passing `_history_ancestor` as `landed`.
  Verify: `uv run pytest tests/test_kept_pins.py tests/test_conduct.py -k "ledger or forged or a_rerun_pushes" -n auto -q` exits `0`.
- [x] 3.5 Retarget the pins in `tests/test_kept_pins.py` that reach `_ledger_entries` to `release_entries`, which lists the same names ([D4](design.md#d4)).
  Verify: `uv run pytest tests/test_kept_pins.py -k ledger -n auto -q` exits `0`.
- [x] 3.6 Delete `_ledger_entries` from `skills/mf-ship/scripts/conduct.py`.
  Verify: `git grep -c "_ledger_entries" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 3.7 Send `approve_gate` of `skills/mf-ship/scripts/conduct.py` through `approve`: its hash check and `Stop` words stay, and an `OSError` of the module words as `cannot write the approval — <strerror>; a sandbox refuses the home folder: run it outside one`.
  Verify: `uv run pytest tests/test_kept_pins.py tests/test_conduct.py -k "approval or anchor or approve_gate" -n auto -q` exits `0`.
- [x] 3.8 In `skills/mf-converge/scripts/gate_check.py` import `mflib.kept` after its seed line and send `approval` through it. Add `kept.py` to its row's `names` in `docs/modules.md`.
  Verify: `uv run pytest tests/test_gate_check.py -n auto -q` exits `0`.
- [x] 3.9 In `run` and `_record_repo` of `skills/mf-ship/scripts/conduct.py` call `mark_live`, `unmark` and `record_repo`; `_pin` stays for `move` and `trees` ([D9](design.md#d9)). The `_pin` stub of `tests/test_claim.py` keeps `move` alone.
  Verify: `uv run pytest tests/test_claim.py tests/test_mark_pins.py -n auto -q` exits `0`.
- [x] 3.10 Retarget the pins in `tests/test_kept_pins.py` that reach `_mark_live` and `_unmark` to `mark_live` and `unmark`, the pid and the parent's passed as arguments ([D4](design.md#d4)).
  Verify: `uv run pytest tests/test_kept_pins.py -k live -n auto -q` exits `0`.
- [x] 3.11 Delete `_mark_live` and `_unmark` from `skills/mf-ship/scripts/conduct.py`.
  Verify: `git grep -c -e "_mark_live" -e "_unmark" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 3.12 In `skills/mf-ship/scripts/pin.py` import `mflib.kept` after its seed line, send `holder` and `live` through it and `_origin` through `origin`, so the `_conduct` load keeps `_scratch`, `SSH_COMMAND` and `GIT_TIMEOUT` alone. Add `kept.py` to its row's `names` in `docs/modules.md`.
  Verify: `uv run pytest tests/test_pin.py -n auto -q` exits `0`.
- [x] 3.13 Make `PRIVATE_REACH` in `tests/test_structure.py` list `_scratch` alone for `pin.py`, and in `tests/test_pin.py` plant the origin with the module's `keep_origin` in place of the hand-written JSON.
  Verify: `uv run pytest tests/test_structure.py tests/test_pin.py -n auto -q` exits `0`.
- [x] 3.14 Send `Run.probe` and `check_probe` of `skills/mf-ship/scripts/conduct.py` through `make_probe_mark`, `remove_probe_mark`, `probe_executor` and `probe_untouched` ([D5](design.md#d5)); `Run.probe`'s halt `cannot write the probe mark: <strerror>` stays the conductor's text, the `strerror` of an `OSError` the module raises.
  Verify: `uv run pytest tests/test_kept_pins.py tests/test_conduct.py -k probe -n auto -q` exits `0`.

## 4 — The fix

- [x] 4.1 Add `Broken` and one read to `skills/mflib/kept.py` per [D6](design.md#d6): `statefile.read_bytes` with a limit one past the bound, `Broken` over it, a strict decode, a name that is no regular file `it is not a file`, a missing name None. Cases in `tests/test_kept.py`, each named `test_read_…`.
  Verify: `uv run pytest tests/test_kept.py -k test_read_ -n auto -q` exits `0`.
- [x] 4.2 In `main` of `skills/mf-ship/scripts/conduct.py` catch `kept.Broken` beside `Stop`: print `conduct: cannot run — <text>` and return `2`. In `run` release `conductor.log.held` before the halt is logged, give code `2`, not `1`, to a `Broken` that `conductor.ship()` raises, and unmark where `Stop` unmarks ([D7](design.md#d7)). Cases in `tests/test_kept_pins.py`, each named `test_broken_…`, with the kept reads patched to raise, one reading the run log.
  Verify: `uv run pytest tests/test_kept_pins.py -k test_broken_ -n auto -q` exits `0`.
- [x] 4.3 Read `origin`, `default` and `base` by that read in `skills/mflib/kept.py`: `origin` checks a pair of lists of strings, `default` strips, `base` strips and checks 40 hex digits, an empty or blank base is None; `origin_stands` and `base_stands` raise `Broken` for a name that is no regular file. Turn the pins of readings 5, 10 and 27 of [the readings](design.md#the-readings) in `tests/test_kept_pins.py`, with unit cases in `tests/test_kept.py`, each named `test_strict_…`.
  Verify: `uv run pytest tests/test_kept.py -k test_strict_ -n auto -q` exits `0`.
- [x] 4.4 Read `approval` by the one read in `skills/mflib/kept.py`: a file that cannot be read gives None, a bad byte included. Turn the pin of reading 20, and write `test_a_bad_byte_approves_nothing` in `tests/test_gate_check.py` and unit cases in `tests/test_kept.py`, each named `test_bad_byte_approval_…`.
  Verify: `uv run pytest tests/test_gate_check.py tests/test_kept.py -k bad_byte -n auto -q` exits `0`.
- [x] 4.5 Make `release_heads` hand back `Heads` with `bad` naming each entry that is not one commit id ([D10](design.md#d10)), and `close_releases` leave such an entry. Give `_ledger_heads`, `_foreign_commit`, `_local_releases` and `_unpushed` of `skills/mf-ship/scripts/conduct.py` the keyword `on_bad` of [D10](design.md#d10), each forwarding it to `_foreign_commit` and `_ledger_heads`, and pass the run's from each call in `Run`. Turn the pin of reading 1; unit cases in `tests/test_kept.py` and the conductor's in `tests/test_kept_pins.py`, each named `test_heads_…`.
  Verify: `uv run pytest tests/test_kept.py tests/test_kept_pins.py -k test_heads_ -n auto -q` exits `0`.
- [x] 4.6 Write `keep_origin` and `keep_default` in `skills/mflib/kept.py` once, staged at 0600 through `statefile.write` only when `lstat` finds no name, and `default_stands` by `lstat`; `.default` is written `<name>\n` and read stripped ([D12](design.md#d12)). `Unwritten` on a failure. Turn the pins of readings 6 and 8 and the assert in `tests/test_conduct.py` that pins `.default` with no newline; unit cases in `tests/test_kept.py`, each named `test_once_…`.
  Verify: `uv run pytest tests/test_kept.py -k test_once_ -n auto -q` exits `0`.
- [x] 4.7 Write `keep_base`, `record_release`, `approve` and `mark_live` in `skills/mflib/kept.py` through `statefile.write` at 0600, each folder made by `statefile.folder` with `layout.kept_dir()` as root and the folder as its one part ([D8](design.md#d8)). A failed write leaves no staged file. Turn the pins of readings 3 and 9; unit cases in `tests/test_kept.py`, each named `test_staged_…`.
  Verify: `uv run pytest tests/test_kept.py -k test_staged_ -n auto -q` exits `0`.
- [x] 4.8 Make `record_repo` in `skills/mflib/kept.py` read `repos` by the read at 262,144 bytes, record nothing when it cannot be read, and append through `statefile.touch` and `statefile.append`. Make `holder` and `live` read by the read, a failure none. Turn the pin of reading 18; unit cases in `tests/test_kept.py`, each named `test_lenient_…`.
  Verify: `uv run pytest tests/test_kept.py -k test_lenient_ -n auto -q` exits `0`.
- [x] 4.9 Make `close_releases`, `unmark` and `remove_probe_mark` unlink a name under the descriptor of `statefile.open_folder` on the folder's root and part, a folder that cannot be opened unlinking nothing. Make `make_probe_mark` unlink the stale mark by name, then `statefile.touch` it at 0600. Turn the pin of reading 14; unit cases in `tests/test_kept.py`, each named `test_unlink_…`.
  Verify: `uv run pytest tests/test_kept.py -k test_unlink_ -n auto -q` exits `0`.
- [x] 4.10 Write the failure cases of each fix in `tests/test_kept_pins.py`, each named `test_stop_…`: a bad byte in `.default` stops `run` with exit `2` naming the file; a second `approve-gate` leaves the second hash in the entry; a second keep of the origin leaves the standing file; a bad byte in the live mark still reads as none.
  Verify: `uv run pytest tests/test_kept_pins.py -k test_stop_ -n auto -q` exits `0`.
- [x] 4.11 Keep the conductor's own tests that reach the kept files green: `tests/test_conduct.py` changes only where a decision of this phase turns an assert.
  Verify: `uv run pytest tests/test_conduct.py -k "kept_urls or anchor or offline_base or approve_gate or forged" -n auto -q` exits `0`.

## 5 — The record

- [x] 5.1 In `docs/decisions.md` add to D51 a bullet `**Kept files:**` saying they are written and read through `skills/mflib/kept.py`, a file that cannot be read stops the command, exit 2, and a ledger entry that is no commit id authorizes nothing; its `**Offline base:**` bullet gains that a base that cannot be read stops the command.
  Verify: `git grep -n -e "skills/mflib/kept.py" -- docs/decisions.md` prints a line.
- [x] 5.2 In `docs/decisions.md` add to D55 that an unreadable mark reads as none.
  Verify: `git grep -n -e "unreadable mark" -- docs/decisions.md` prints a line.
- [x] 5.3 In `THREAT_MODEL.md` add to the sentence on the kept URLs that a kept origin that cannot be read stops the run, and to the sentence on the release ledger that a non-commit entry authorizes nothing, is named in the log and stays.
  Verify: `git grep -n -e "non-commit entry" -- THREAT_MODEL.md` prints a line.
- [x] 5.4 In `THREAT_MODEL.md` add `kept.py` to the list of the shared home's modules that follow no link.
  Verify: `git grep -n -e "the kept files, kept.py" -- THREAT_MODEL.md` prints a line.
- [x] 5.5 In `docs/recipes.md` add that the kept files are written and parsed through `skills/mflib/kept.py`, their paths `layout.kept_file(primary)` and its neighbours in the layout module.
  Verify: `git grep -n -e "skills/mflib/kept.py" -- docs/recipes.md` prints a line.
