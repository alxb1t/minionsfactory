# Pins — tasks

In order: pin the region on today's side, add the module as copies, send the stations through it, turn the readings, write the record. Decisions are in [design](design.md); the cases are its [The cases](design.md#the-cases).

## Progress

- [x] 1 — The pin · moderate
- [x] 2 — The module · moderate
- [x] 3 — The stations · moderate
- [x] 4 — The fix · hard
- [ ] 5 — The record · moderate

## 1 — The pin

- [x] 1.1 **HALT CHECK** `kept.py` still defines `_read`, `_replace` and `_remove`, which the new functions call, and `conduct.py` still defines `_ship_file`.
  Verify: `git grep -n -e "^def _read" -- skills/mflib/kept.py` exits `0`; `git grep -n -e "^def _replace" -- skills/mflib/kept.py` exits `0`; `git grep -n -e "^def _remove" -- skills/mflib/kept.py` exits `0`; `git grep -n -e "^def _ship_file" -- skills/mf-ship/scripts/conduct.py` exits `0`.
- [x] 1.2 Create `tests/test_pinfiles_pins.py`: its docstring, helpers imported from `tests/test_pin.py` and `tests/conduct_load.py`, and Cases R of [the cases](design.md#the-cases), each named `test_r_<what>`. A FIFO case runs in a child with a timeout and carries `slow`.
  Verify: `uv run pytest tests/test_pinfiles_pins.py -n auto -q` exits `0`.
- [x] 1.3 Add Cases W for `install` to `tests/test_pinfiles_pins.py`: the world and `install` rows, the folder, link and FIFO rows at `source`, `hold`, `checkout` and `pending`, each named `test_wi_<what>`. Each case holds today's side.
  Verify: `uv run pytest tests/test_pinfiles_pins.py -k "test_wi_" -n auto -q` exits `0`.
- [x] 1.4 Add Cases W for `move`'s reads to `tests/test_pinfiles_pins.py`: the `move` rows and the first-read rows, a bad byte, a link, an oversize file and a FIFO at each file `move` reads, each named `test_wm_<what>`.
  Verify: `uv run pytest tests/test_pinfiles_pins.py -k "test_wm_" -n auto -q` exits `0`.
- [x] 1.5 Add Cases S for `_ship_file`, `_cap` and `_pushes_tags` to `tests/test_pinfiles_pins.py`, reaching them as `conduct["_ship_file"]` through `tests/conduct_load.py`, each named `test_s_<what>`; a FIFO case runs in a child python and carries `slow`.
  Verify: `uv run pytest tests/test_pinfiles_pins.py -k "test_s_" -n auto -q` exits `0`.
- [x] 1.6 Add the Cases S callers to `tests/test_pinfiles_pins.py`: `status`, `report`, `run` and `cut` with the reads of `ship.toml` counted by wrapping `_ship_file` in the conductor's dict, each named `test_sc_<what>` and each over 1 s marked `slow` ([D10](design.md#d10)).
  Verify: `uv run pytest tests/test_pinfiles_pins.py -k "test_sc_" -n auto -q` exits `0`.
- [x] 1.7 Pay card `0159·R3` in `tests/test_kept_pins.py` per [D11](design.md#d11): add the live-mark assertion to `test_stop_a_bad_byte_in_the_default_stops_run_with_exit_2_naming_it`, and delete `test_broken_run_logs_the_halt_naming_the_file_and_exits_2`.
  Verify: `git grep -c -e "test_broken_run_logs_the_halt_naming_the_file_and_exits_2" -- tests/test_kept_pins.py` prints nothing; `uv run pytest tests/test_kept_pins.py tests/test_pinfiles_pins.py -n auto -q` exits `0`.

## 2 — The module

- [x] 2.1 In `skills/mflib/kept.py` give `Broken` the attributes `path` and `phrase`, and word a path outside the kept folder as `<path>: <phrase>` ([D6](design.md#d6)); name the pin's files and `ship.toml` in the module docstring. Create `tests/test_kept_pinfiles.py` with the `Broken` cases, each named `test_broken_<what>`.
  Verify: `uv run pytest tests/test_kept_pinfiles.py tests/test_kept.py tests/test_structure.py -n auto -q` exits `0`.
- [x] 2.2 Add to `skills/mflib/kept.py` the readers `source`, `pending`, `hold` and `checkout`, the writers `keep_source`, `keep_pending`, `keep_hold` and `keep_checkout`, and the clears `clear_pending` and `clear_hold`, over `_pin_read`, `_pin_keep` and `_pin_clear`, each as its copy in `pin.py` behaves ([D1](design.md#d1), [D5](design.md#d5)). Add their unit and round-trip cases to `tests/test_kept_pinfiles.py`, each named `test_pin_<what>`.
  Verify: `uv run pytest tests/test_kept_pinfiles.py -k "test_pin_" -n auto -q` exits `0`; `uv run pytest tests/test_kept_pinfiles.py tests/test_kept.py tests/test_structure.py -n auto -q` exits `0`.
- [x] 2.3 Add to `skills/mflib/kept.py` `ship_data`, `ship_cap` and `ship_tags`, each as its copy in `conduct.py` behaves: `ship_data` raises the raw `OSError`, `UnicodeDecodeError` and `TOMLDecodeError` of its parse, and the checks raise `Broken` with today's phrase. Add their cases to `tests/test_kept_pinfiles.py`, each named `test_ship_<what>`; a folder raises the `OSError` `read_text` raises.
  Verify: `uv run pytest tests/test_kept_pinfiles.py -k "test_ship_" -n auto -q` exits `0`; `uv run pytest tests/test_kept_pinfiles.py tests/test_kept.py tests/test_structure.py -n auto -q` exits `0`.
- [x] 2.4 Confirm no script calls the new functions yet and the map row of `kept.py` stands.
  Verify: `git diff --quiet HEAD -- skills/mf-ship/scripts/pin.py skills/mf-ship/scripts/conduct.py docs/modules.md` exits `0`.

## 3 — The stations

- [x] 3.1 In `skills/mf-ship/scripts/pin.py`, `describe` reads `source`, `pending` and `hold` through `mflib.kept`. No assert of any test changes.
  Verify: `git grep -n -e "mflib.kept.pending()" -- skills/mf-ship/scripts/pin.py` prints a line; `uv run pytest tests/test_pin.py tests/test_pinfiles_pins.py tests/test_structure.py -n auto -q` exits `0`; `uv run pytest tests/test_conduct.py -k "last_run_moves or re_pin_builds or run_holds_the_machine_awake or started_run_is_seen or run_on_linux_holds_nothing" -n auto -q` exits `0`.
- [x] 3.2 In `pin.py`, `move` reads `source`, `pending`, `checkout` and `hold` through `mflib.kept` and clears `pending` by `mflib.kept.clear_pending`. No assert changes.
  Verify: `git grep -n -e "mflib.kept.checkout()" -- skills/mf-ship/scripts/pin.py` prints a line; `uv run pytest tests/test_pin.py tests/test_pinfiles_pins.py tests/test_structure.py -n auto -q` exits `0`; `uv run pytest tests/test_conduct.py -k "last_run_moves or re_pin_builds or run_holds_the_machine_awake or started_run_is_seen or run_on_linux_holds_nothing" -n auto -q` exits `0`.
- [x] 3.3 In `pin.py`, `install` writes `source`, `hold`, `checkout` and `pending` and clears `hold` and `pending` through `mflib.kept`; delete `_read` and `_write`. No assert changes.
  Verify: `git grep -c -e "^def _read" -e "^def _write" -- skills/mf-ship/scripts/pin.py` prints nothing; `uv run pytest tests/test_pin.py tests/test_pinfiles_pins.py tests/test_structure.py -n auto -q` exits `0`.
- [x] 3.4 In `skills/mf-ship/scripts/conduct.py`, `_ship_file` returns `(path, mflib.kept.ship_data())`, keeping its `except` and its `Stop` frame; it stays a no-argument call.
  Verify: `git grep -c -e "tomllib.loads(path.read_text())" -- skills/mf-ship/scripts/conduct.py` prints nothing; `uv run pytest tests/test_claim.py tests/test_pinfiles_pins.py tests/test_structure.py -n auto -q` exits `0`.
- [x] 3.5 In `conduct.py`, `_cap` and `_pushes_tags` call `mflib.kept.ship_cap` and `ship_tags`, and word a `Broken` as `Stop(2, f"{path}: {error.phrase}")`; each `except` is reached by the wrong-type cases of Cases S. No assert changes.
  Verify: `git grep -n -e "mflib.kept.ship_cap" -- skills/mf-ship/scripts/conduct.py` prints a line; `uv run pytest tests/test_conduct.py -k "cap_reads_ship_toml or ship_toml_is_read or ship_toml_reads_tags or cap_file_that_is_bad or cap_gates or cap_of_one or cap_counts or cap_close_starts or cap_writes or cap_status_and_cut_line or small_cap_is_granted or start_makes_a_missing_tag or refused_tag_push or tags_false or status_says_a_machine_pushes_no_tag or report_with_a_bad_tags" -n auto -q` exits `0`.

## 4 — The fix

- [x] 4.1 In `pin.py`, `move`'s first read, of `source`, joins its `try`, so a `Broken` is `pin: cannot move — <text>` ([D3](design.md#d3)). Add the case `test_wb_source_broken_is_named` to `tests/test_pinfiles_pins.py`: `mflib.kept.source` patched to raise `Broken` gives that text; the real bad byte follows in 4.2.
  Verify: `uv run pytest tests/test_pinfiles_pins.py -k "test_wb_source_broken_is_named" -n auto -q` exits `0`; `uv run pytest tests/test_pin.py tests/test_pinfiles_pins.py tests/test_structure.py -n auto -q` exits `0`.
- [x] 4.2 In `kept.py`, `_pin_read` reads through `_read`, and `source` returns None for an empty file ([D3](design.md#d3), [D8](design.md#d8)). Turn the read cases of R1, W1, R2, R3, R4, R7 and W5 in `tests/test_pinfiles_pins.py` and `tests/test_kept_pinfiles.py`; add the slow case of a bad byte at `hold` through `run`.
  Verify: `uv run pytest tests/test_kept_pinfiles.py tests/test_kept.py tests/test_pin.py tests/test_pinfiles_pins.py tests/test_structure.py -n auto -q` exits `0`; `uv run pytest tests/test_conduct.py -k "last_run_moves or re_pin_builds or run_holds_the_machine_awake or started_run_is_seen or run_on_linux_holds_nothing" -n auto -q` exits `0`.
- [x] 4.3 In `kept.py`, `_pin_keep` writes through `_replace` and `_pin_clear` unlinks by name through `_remove` ([D7](design.md#d7)). Turn the write cases of W2, W3, W6 and W9; a second `install` replaces `source` whole and leaves no `source.tmp`.
  Verify: `uv run pytest tests/test_kept_pinfiles.py tests/test_kept.py tests/test_pin.py tests/test_pinfiles_pins.py tests/test_structure.py -n auto -q` exits `0`.
- [x] 4.4 In `kept.py`, `ship_data` reads through `_read` and raises `Broken` for a TOML error and a `RecursionError`. In `conduct.py`, `_ship_file` is one `try` over `kept.ship_data()` with one `except kept.Broken` that raises `Stop(2, f"{path}: {error.phrase}")`; `ship_data` answers an absent file. Turn the cases of S1 to S5; each new `except` has its case.
  Verify: `uv run pytest tests/test_kept_pinfiles.py tests/test_kept.py tests/test_claim.py tests/test_pinfiles_pins.py tests/test_structure.py -n auto -q` exits `0`; `uv run pytest tests/test_conduct.py -k "cap_reads_ship_toml or ship_toml_is_read or ship_toml_reads_tags or cap_file_that_is_bad or cap_gates or cap_of_one or cap_counts or cap_close_starts or cap_writes or cap_status_and_cut_line or small_cap_is_granted or start_makes_a_missing_tag or refused_tag_push or tags_false or status_says_a_machine_pushes_no_tag or report_with_a_bad_tags" -n auto -q` exits `0`.

## 5 — The record

- [ ] 5.1 In `docs/decisions.md`, D55 says the pin's files go through `kept.py`, a pin file that cannot be read stops the `start` line and `install`'s write, and a move names it and moves nothing.
  Verify: `git grep -n -e "pin file" -- docs/decisions.md` prints a line naming D55's text.
- [ ] 5.2 In `docs/decisions.md`, D84 says a `ship.toml` that is a link, a FIFO, a folder, a file over its bound and a file nested too deep cannot be read, and stops `run`, `cut`, `status` and `report`.
  Verify: `git grep -n -e "FIFO" -- docs/decisions.md` prints a line naming D84's text.
- [ ] 5.3 In `THREAT_MODEL.md`, the line on the shared home's modules names the pin's files and `ship.toml` among the kept files.
  Verify: `git grep -n -e "pin's" -- THREAT_MODEL.md` prints a line naming the kept files.
- [ ] 5.4 In `docs/principles.md`, the sentences on `conduct.py`'s read of `ship.toml` and `pin.py`'s pinned release name `skills/mflib/kept.py` as the read and the write.
  Verify: `git grep -n -e "mflib/kept.py" -- docs/principles.md` prints a line naming the pinned release.
- [ ] 5.5 In `docs/recipes.md`, the paragraph on the home's modules adds the pin's files and the `ship.toml` read to the kept files.
  Verify: `git grep -n -e "ship.toml" -- docs/recipes.md` prints a line naming the kept files.
