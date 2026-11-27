# Queue — tasks

Pin the queue as it is, move it into `skills/mflib/queue.py`, send the conductor's sites through it, fix the right sides, then record it.

## Progress

- [x] 1 — The pin · moderate
- [x] 2 — The module · hard
- [x] 3 — The stations · moderate
- [x] 4 — The fix · hard
- [x] 5 — The record · moderate

## 1 — The pin

Cases of the series' queue mutation run, written again at `HEAD`, each green as the code stands and red on the change its comment names. No case starts a worker ([D9](design.md#d9)).

- [x] 1.1 **HALT CHECK** The conductor still holds the writer the stations phase deletes.
  Verify: `git grep -q -e "^def _write_cut" -- skills/mf-ship/scripts/conduct.py` exits `0`.
- [x] 1.2 Create `tests/test_queue_pins.py` with its docstring, its helpers and the cases of `_queue_lock`, of the list and read of `_cuts` and of `_write_cut`, the first being `test_queue_lock_blocks_a_second_taker`. Plant a file, an empty file, a bad byte, a file over its bound, a link, a dangling link, a folder and a FIFO at an entry. A FIFO is read in a child process and its case carries the `slow` marker.
  Verify: `uv run pytest tests/test_queue_pins.py -n auto -q -k test_queue_lock_blocks_a_second_taker` exits `0`.
- [x] 1.3 Add to `tests/test_queue_pins.py` the cases of `_brief_of`, `_merge_tried`, the `briefs` write of `Run.cutting` and the `supervised` write of `Run.supervise`, the first being `test_a_record_is_stripped_and_a_prefix_is_no_try`: an empty record reads as none.
  Verify: `uv run pytest tests/test_queue_pins.py -n auto -q -k test_a_record_is_stripped_and_a_prefix_is_no_try` exits `0`.
- [x] 1.4 Add to `tests/test_queue_pins.py` the cases of `_requests`, `_requested` and `_request`, the first being `test_requests_unlinks_a_link_and_leaves_its_target`: the names come back as a set, a subfolder is left, a linked folder reads as none, only a regular file counts, the folder is made with its parents.
  Verify: `uv run pytest tests/test_queue_pins.py -n auto -q -k test_requests_unlinks_a_link_and_leaves_its_target` exits `0`.
- [x] 1.5 Add to `tests/test_queue_pins.py` the cases of `_cut_line`, `_halted_after`, `_next_id`, `cut`, `rejoin` and `grant`, the first being `test_rejoin_clears_the_chain_in_name_order`: the entry's key order, the lock around each write, an unreadable entry refused by `rejoin`, `all` asked when no change is named.
  Verify: `uv run pytest tests/test_queue_pins.py -n auto -q -k test_rejoin_clears_the_chain_in_name_order` exits `0`.
- [x] 1.6 Add to `tests/test_queue_pins.py` the run-level cases of `Run.cutting`, `Run.cut_halted`, `Run.wait_cut`, `Run.unwait`, `Run.take_requests`, `Run.in_flight` and `_close`, the first being `test_take_requests_reads_the_entries_again_when_a_request_stands`. Each runs over a fake worker that starts none.
  Verify: `uv run pytest tests/test_queue_pins.py -n auto -q -k test_take_requests_reads_the_entries_again_when_a_request_stands` exits `0`.
- [x] 1.7 Add to `tests/test_queue_pins.py` the pins of what no mutant reaches, the first being `test_a_fifo_at_an_entry_reads_in_a_child`: a link, a hard link, a folder, a bad byte, a file over its bound, a wrong type and a deep JSON at an entry; the same shapes at `briefs/<id>`, `supervised/<id>` and a request; a link at the `cuts` folder and at the `rejoin` folder.
  Verify: `uv run pytest tests/test_queue_pins.py -n auto -q -k test_a_fifo_at_an_entry_reads_in_a_child` exits `0`.
- [x] 1.8 Add to `tests/test_queue_pins.py` the pins of a failed write in `cut`, `rejoin`, `cut_halted`, `wait_cut`, `unwait`, the writes of `briefs` and `supervised`, and a request, the first being `test_a_failed_entry_write_in_cut_stops_it_and_removes_the_reservation`; each form of `waits`, null, empty and text; the cut halt's text written and matched.
  Verify: `uv run pytest tests/test_queue_pins.py -n auto -q -k test_a_failed_entry_write_in_cut_stops_it_and_removes_the_reservation` exits `0`.
- [x] 1.9 Run each case once under the change its comment names, by hand, and restore the file. No source file stays changed.
  Verify: `git status --porcelain -- skills` prints nothing.

## 2 — The module

`skills/mflib/queue.py` behaves as each copy does today, and no script calls it yet ([D1](design.md#d1), [D2](design.md#d2)).

- [x] 2.1 **HALT CHECK** The module does not exist yet.
  Verify: `git ls-files --error-unmatch skills/mflib/queue.py` exits `1`.
- [x] 2.2 Add to `skills/mflib/statefile.py` a keyword `mode` to `folder`, the mode of each folder it makes, default `0o777`; and `def touch(path, folder, mode)`, which makes an empty file by its name under the descriptor with `O_CREAT`, `O_WRONLY`, `O_NOFOLLOW` and `O_NONBLOCK`. Add their cases to `tests/test_statefile.py`.
  Verify: `git grep -n -e "def touch" -- skills/mflib/statefile.py` prints a line, and `uv run pytest tests/test_statefile.py -n auto -q` exits `0`.
- [x] 2.3 Create `skills/mflib/queue.py` with its docstring and the record: the key names once, `REQUIRED`, `Entry` as a `TypedDict`, `UNREADABLE`, `halted_text(name)` returning `after <name> is cut-halted`, and the pattern of a change id. Its cases go in a new `tests/test_queue.py`, with the round-trip case of a record written and read.
  Verify: `uv run pytest tests/test_queue.py -n auto -q` exits `0`.
- [x] 2.4 Add `lock(primary)` and `Refused` to `skills/mflib/queue.py`, as `_queue_lock` behaves: the kept folder and the queue folder made mode 0700 with no parents, the lock opened `O_CREAT|O_RDWR|O_NOFOLLOW` mode 0600, a blocking `flock`, the descriptor closed in `finally`. `Refused` holds the error's `strerror`. Add the cases to `tests/test_queue.py`, the first being `test_the_lock_blocks_a_second_taker`.
  Verify: `uv run pytest tests/test_queue.py -n auto -q -k test_the_lock_blocks_a_second_taker` exits `0`.
- [x] 2.5 Add `entries(primary)`, `write(primary, change, entry)`, `remove(primary, change)` and `Unwritten` to `skills/mflib/queue.py`, as `_cuts`, `_write_cut` and the unlink of `Run.cutting` behave. `Unwritten` is an `OSError` that names the file. `entries` skips a name that is no change id and maps each unreadable shape to `UNREADABLE`. Add the cases to `tests/test_queue.py`, the first being `test_entries_skips_a_name_that_is_no_change_id`.
  Verify: `uv run pytest tests/test_queue.py -n auto -q -k test_entries_skips_a_name_that_is_no_change_id` exits `0`.
- [x] 2.6 Add `request(primary, name)`, `requests(queue)` and `requested(queue)` to `skills/mflib/queue.py`, as `_request`, `_requests` and `_requested` behave; `queue` is the queue's folder. Add the cases to `tests/test_queue.py`, the first being `test_requests_returns_the_names_it_unlinks`.
  Verify: `uv run pytest tests/test_queue.py -n auto -q -k test_requests_returns_the_names_it_unlinks` exits `0`.
- [x] 2.7 Add `brief(primary, change)`, `write_brief(primary, change, path)`, `merge_tried(primary, change, merge)` and `write_supervised(primary, change, merge)` to `skills/mflib/queue.py`, as `_brief_of`, `_merge_tried` and the writes of `briefs` and `supervised` behave. Add the cases to `tests/test_queue.py`, the first being `test_a_prefix_of_the_merge_is_no_try`.
  Verify: `uv run pytest tests/test_queue.py -n auto -q -k test_a_prefix_of_the_merge_is_no_try` exits `0`.
- [x] 2.8 Add the module's row to `docs/modules.md`: layer `home`, names `layout.py, statefile.py`.
  Verify: `git grep -n -e "skills/mflib/queue.py" -- docs/modules.md` prints the row.
- [x] 2.9 Run the map test over the new row, with the module's unit cases and the helpers' cases.
  Verify: `uv run pytest tests/test_queue.py tests/test_statefile.py tests/test_structure.py -n auto -q` exits `0`.

## 3 — The stations

The conductor's sites call the module. No assert changes; a test changes only the line by which it reaches a name, and the line by which it plants an entry ([D8](design.md#d8), [D10](design.md#d10)).

- [x] 3.1 **HALT CHECK** The module stands with its entry, request and record functions.
  Verify: `git grep -q -e "^def merge_tried" -e "^def requested" -e "^def write" -- skills/mflib/queue.py` exits `0`.
- [x] 3.2 In `skills/mf-ship/scripts/conduct.py` add `import mflib.queue` after `import mflib.platform`, make `_cuts` return `mflib.queue.entries(primary)`, send each writer of an entry to `mflib.queue.write` and the entry's unlink in `Run.cutting` to `mflib.queue.remove`, and send the key test of `rejoin` and the docstring of `_cuts` to `mflib.queue.REQUIRED`.
  Delete `_write_cut` and `CUT_KEYS`.
  Verify: `git grep -n -e "^def _write_cut" -e "CUT_KEYS" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 3.3 In `skills/mf-ship/scripts/conduct.py` make `_queue_lock` enter `mflib.queue.lock` and raise the `Stop` of today's words on `mflib.queue.Refused`.
  Verify: `git grep -n -e "fcntl.flock" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 3.4 In `skills/mf-ship/scripts/conduct.py` make `_requests` and `_request` call `mflib.queue.requests` and `mflib.queue.request`, and send `_close` to `mflib.queue.requested`.
  Delete `_requested`.
  Verify: `git grep -n -e "^def _requested" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 3.5 In `skills/mf-ship/scripts/conduct.py` make `_brief_of` call `mflib.queue.brief` and keep its `is_file` test; send the `briefs` write of `Run.cutting` to `mflib.queue.write_brief`, the `supervised` write of `Run.supervise` to `mflib.queue.write_supervised`, and its test of a tried merge to `mflib.queue.merge_tried`.
  Delete `_merge_tried`.
  Verify: `git grep -n -e "^def _merge_tried" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 3.6 In `skills/mf-ship/scripts/conduct.py` write the halt `after <name> is cut-halted` through `mflib.queue.halted_text` in `Run.cutting`, and match it through the same function in `_halted_after`.
  Verify: `git grep -n -e "queue.halted_text" -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 3.7 Change the line by which each test reaches a moved name, in `tests/test_conduct.py`, `tests/test_claim.py`, `tests/test_viewer.py` and `tests/test_modelsfile.py`, and the line by which each plants an entry; `tests/test_queue_pins.py` takes the module's names the same way. A patch of a moved name goes on `mflib.queue` through `monkeypatch`. No assert changes.
  Verify: `uv run pytest tests/test_conduct.py tests/test_claim.py tests/test_viewer.py tests/test_modelsfile.py tests/test_queue_pins.py -n auto -q` exits `0`.
- [x] 3.8 Add `queue.py` to the conductor's `names` cell in `docs/modules.md`, after `platform.py`.
  Verify: `uv run pytest tests/test_structure.py -n auto -q` exits `0`.

## 4 — The fix

The module keeps one side. The cases and pins of the pin phase turn to it ([D3](design.md#d3) to [D6](design.md#d6)).

- [x] 4.1 **HALT CHECK** The module still reads each entry by path, so the cases of this phase turn a standing side.
  Verify: `git grep -q -e "^def entries" -- skills/mflib/queue.py` exits `0`.
- [x] 4.2 In `skills/mflib/queue.py` add `BOUND_ENTRY`, 262,144, and make `entries` read each entry through the descriptor `statefile.open_folder` gives on the `cuts` folder, with `statefile.read_bytes` asked one byte past the bound so a longer file is refused, a strict decode and a catch of `RecursionError`. Check each value against the record's types and map every broken shape to the unreadable entry. A linked, missing and file-shaped folder lists nothing. Turn the pins of a link, a FIFO, a folder, a file over its bound, a wrong type and a deep JSON.
  Verify: `git grep -n -e "BOUND_ENTRY" -- skills/mflib/queue.py` prints a line, and `uv run pytest tests/test_queue.py tests/test_queue_pins.py -n auto -q` exits `0`.
- [x] 4.3 Turn each entry that `tests/test_conduct.py`, `tests/test_viewer.py` and `tests/test_modelsfile.py` plant by hand and the typed read turns away, to a typed entry. No assert changes.
  Verify: `uv run pytest tests/test_conduct.py tests/test_viewer.py tests/test_modelsfile.py -n auto -q` exits `0`.
- [x] 4.4 In `skills/mflib/queue.py` add `BOUND_RECORD`, 65,536, and make `brief` and `merge_tried` read through the descriptor `statefile.open_folder` gives on their own folder, asked one byte past the bound, with a strict decode; a link, a FIFO, a folder and a longer file each read as none. Turn the pins of the `briefs` and `supervised` shapes.
  Verify: `git grep -n -e "BOUND_RECORD" -- skills/mflib/queue.py` prints a line, and `uv run pytest tests/test_queue.py tests/test_queue_pins.py -n auto -q` exits `0`.
- [x] 4.5 Add `def is_wait(entry)` to `skills/mflib/queue.py`, true for a non-empty string `waits`, and make `Run.unwait` and `_cut_line` of `skills/mf-ship/scripts/conduct.py` use it. Turn the pins of each form of `waits`, and add to `tests/test_viewer.py` the case of a null and an empty `waits`.
  Verify: `git grep -n -e "def is_wait" -- skills/mflib/queue.py` prints a line, and `uv run pytest tests/test_queue.py tests/test_queue_pins.py tests/test_viewer.py -n auto -q` exits `0`.
- [x] 4.6 In `skills/mflib/queue.py` make `write`, `write_brief` and `write_supervised` go through `statefile.write` mode 0600 under the folder's descriptor. `write` makes `cuts` alone, mode 0700 with no parents, then opens it through `statefile.open_folder`, so a linked `cuts` folder is a failed write. A link at a name gives way to the staged move, and an entry over its bound is refused. Raise `Unwritten` naming the file. Turn the pins of the write.
  Verify: `git grep -n -e "statefile.write" -- skills/mflib/queue.py` prints a line, and `uv run pytest tests/test_queue.py tests/test_queue_pins.py -n auto -q` exits `0`.
- [x] 4.7 In `skills/mflib/queue.py` make `request` call `statefile.touch` under `statefile.folder` with mode 0700, no link followed, raising `Unwritten` on a failure. Make `requests` unlink a name that is no change id and not `all`, and return the rest. Make `requested` count a regular file so named. Turn the pins of the requests.
  Verify: `git grep -n -e "statefile.touch" -- skills/mflib/queue.py` prints a line, and `uv run pytest tests/test_queue.py tests/test_queue_pins.py -n auto -q` exits `0`.
- [x] 4.8 In `skills/mf-ship/scripts/conduct.py` turn `Unwritten` into `Stop(2, …)` naming the file in `cut` and `rejoin`, a failed request write included. `Run.cut_halted`, `Run.wait_cut`, `Run.unwait`, `Run.take_requests` and the writes of `briefs` and `supervised` let it rise as an `OSError` rose. Turn the pins of a failed write.
  Delete the reservation `cut` made, through `_remove_in`, before it raises.
  Verify: `git grep -n -e "queue.Unwritten" -- skills/mf-ship/scripts/conduct.py` prints a line, and `uv run pytest tests/test_queue_pins.py tests/test_conduct.py -n auto -q` exits `0`.
- [x] 4.9 Turn the cases of `tests/test_queue.py` that held today's side of the record, the lock and the list. Delete none.
  Verify: `uv run pytest tests/test_queue.py tests/test_statefile.py tests/test_structure.py -n auto -q` exits `0`.

## 5 — The record

The record says what the queue now is, where each fact lives ([D12](design.md#d12)). No task edits a debt card.

- [x] 5.1 Edit D58 in `docs/decisions.md`: the queue's entries, its `briefs` and `supervised` records and its rejoin requests are written and read through `skills/mflib/queue.py`, in a typed entry, no link followed. Edit D62: the rows are copied into a typed entry.
  Verify: `git grep -n -e "skills/mflib/queue.py" -- docs/decisions.md` prints a line.
- [x] 5.2 Edit D47 in `docs/decisions.md`: a request is made by its name under the `rejoin` folder's descriptor, and a name that is no change id is unlinked. Edit D84: `waits` is a wait when it is a non-empty string. Edit D61: a broken record reads as none, and a record is written staged.
  Verify: `git grep -n -e "non-empty string" -- docs/decisions.md` prints a line.
- [x] 5.3 Edit `THREAT_MODEL.md`: the rejoin requests and the cut queue name `skills/mflib/queue.py`, which reads each file through no link, bounded and decoded strictly, and writes it staged. Add the module to the line that lists the shared home's files.
  Verify: `git grep -n -e "skills/mflib/queue.py" -- THREAT_MODEL.md` prints a line.
- [x] 5.4 Edit `docs/recipes.md`: the format line names the queue, written and parsed through `skills/mflib/queue.py`, its folder `layout.queue_dir(primary)`.
  Verify: `git grep -n -e "skills/mflib/queue.py" -- docs/recipes.md` prints a line.
