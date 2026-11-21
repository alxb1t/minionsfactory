# Run log — tasks

The phases: the pin, the modules, the stations, the fix, and the rule with the record. The decisions are in [design](design.md).

## Progress

- [x] 1 — The pin · hard
- [ ] 2 — The modules · hard
- [ ] 3 — The stations · moderate
- [ ] 4 — The fix · hard
- [ ] 5 — The rule and the record · moderate

## 1 — The pin

- [x] 1.1 Rename the hand-typed run logs of `tests/test_conduct.py` that stand as `"1.md"` to the stamp `20261101-100000.md`; no assert changes ([D3](design.md#d3)).
  Verify: `git grep -n -F -e '"1.md"' -- tests/test_conduct.py` prints nothing.
- [x] 1.2 Add `tests/test_runlog.py` with cases a and c of [the pin's cases](design.md#the-pins-cases), the conductor reached through the loader of [D3](design.md#d3).
  Verify: `uv run pytest tests/test_runlog.py -q` exits 0.
- [x] 1.3 Add cases b and f of [the pin's cases](design.md#the-pins-cases) to `tests/test_runlog.py`: the release's death and the rescue's read.
  Verify: `uv run pytest tests/test_runlog.py -q` exits 0.
- [x] 1.4 Add cases d, e and h of [the pin's cases](design.md#the-pins-cases) to `tests/test_runlog.py`: the log object, the stop and the order of logs.
  Verify: `uv run pytest tests/test_runlog.py -q` exits 0.
- [x] 1.5 Add cases g and i of [the pin's cases](design.md#the-pins-cases) to `tests/test_runlog.py`: `wait` and `report`'s reads.
  Verify: `uv run pytest tests/test_runlog.py -q` exits 0.
- [x] 1.6 **HALT CHECK** Add to `tests/test_runlog.py` each pin of the log listed under [the pin's cases](design.md#the-pins-cases), a pipe in a child marked `slow`.
  Verify: `uv run pytest tests/test_runlog.py -q` exits 0.
- [x] 1.7 Add `tests/test_claim.py` with cases j and k of [the pin's cases](design.md#the-pins-cases) and its own fake `ps`, which exits 1 for a pid it does not know.
  Verify: `uv run pytest tests/test_claim.py -q` exits 0.
- [x] 1.8 Add cases l and m of [the pin's cases](design.md#the-pins-cases) to `tests/test_claim.py`; `run`'s own pid and start go through the file's own fake `ps`, which knows the test's own pid with a start of its own and exits 1 for any other ([D3](design.md#d3)).
  Verify: `uv run pytest tests/test_claim.py -q` exits 0.
- [x] 1.9 **HALT CHECK** Add to `tests/test_claim.py` each pin of the claim listed under [the pin's cases](design.md#the-pins-cases), a pipe in a child marked `slow`; a pin that runs `run` registers the test's own pid with the file's fake `ps`, as 1.8's do.
  Verify: `uv run pytest tests/test_claim.py -q` exits 0.

## 2 — The modules

- [ ] 2.1 Add `def append(path, text, folder=None)`, `def open_regular(path, folder=None)` and an `offset` argument to the reads of `skills/mflib/statefile.py`, as [D6](design.md#d6) says.
  Verify: `grep -n -e "def append" skills/mflib/statefile.py` prints a line.
- [ ] 2.2 Add `def test_append` cases and the cases of the open and the offset to `tests/test_statefile.py`: a link refused, a pipe refused, the folder's descriptor, the offset.
  Verify: `uv run pytest tests/test_statefile.py -q` exits 0 and `grep -n -e "def test_append" tests/test_statefile.py` prints a line.
- [ ] 2.3 Add `skills/mflib/runlog.py` born with today's behaviour ([D2](design.md#d2)): `STOPPED`, `EVENT`, `EVENTS`, `class Event`, `def title`, `def line`, `def parse`, `def order` and `def newest`.
  Verify: `grep -n -e "def newest" skills/mflib/runlog.py` prints a line.
- [ ] 2.4 Add to `skills/mflib/runlog.py` the readers as the conductor has them: `def events`, `def release_died`, `def rescuing`, `def verify` and `class Tail`, which `wait` polls.
  Verify: `grep -n -e "def release_died" skills/mflib/runlog.py` prints a line.
- [ ] 2.5 Add to `skills/mflib/runlog.py` `class RunLog` and `def stop`, with the lock folder, its wait, the caller's `busy` error and the held list of [D2](design.md#d2).
  Verify: `grep -n -e "class RunLog" skills/mflib/runlog.py` prints a line.
- [ ] 2.6 Add the module's unit cases to `tests/test_runlog.py`, one for each function of `skills/mflib/runlog.py`, reached as `mflib.runlog`.
  Verify: `uv run pytest tests/test_runlog.py -q` exits 0.
- [ ] 2.7 Add `skills/mflib/claim.py`: `def take`, `def present`, `def mark`, `def conductor`, `def groups`, `def enter`, `def leave` and `def remove`, the conductor's access to the claim as it stands.
  Verify: `grep -n -e "def groups" skills/mflib/claim.py` prints a line.
- [ ] 2.8 Add the module's unit cases to `tests/test_claim.py`, one for each function of `skills/mflib/claim.py`, reached as `mflib.claim`.
  Verify: `uv run pytest tests/test_claim.py -q` exits 0.
- [ ] 2.9 Add a row for `skills/mflib/runlog.py` and one for `skills/mflib/claim.py` to `docs/modules.md`: layer `home`, names `—`, since neither imports `statefile` until phase 4 ([D2](design.md#d2)).
  Verify: `git grep -n -e "mflib/runlog.py" -- docs/modules.md` prints a line and `git grep -n -e "mflib/claim.py" -- docs/modules.md` prints a line.
- [ ] 2.10 Name the modules in `skills/mf-ship/SKILL.md`, in a sentence after "Its exits": the run log through `../../mflib/runlog.py`, the claim through `../../mflib/claim.py`.
  Verify: `git grep -n -F -e "../../mflib/claim.py" -- skills/mf-ship/SKILL.md` prints a line.

## 3 — The stations

- [ ] 3.1 **HALT CHECK** The viewer takes `EVENT`, `last_log`, `_claim` and `Stop` alone from the loaded conductor for the run log and the claim.
  Verify: `git grep -n -F -e 'conduct["_claim"]' -- skills/mf-ui/scripts/viewer.py` prints a line.
- [ ] 3.2 In `skills/mf-ship/scripts/conduct.py` import `mflib.runlog`, bind `EVENT` and `last_log` to the module's, and remove `class RunLog`; `Run.__init__` builds the module's `RunLog` with the `busy` error of [D2](design.md#d2).
  Verify: `git grep -n -e "class RunLog" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 3.3 In `skills/mf-ship/scripts/conduct.py` replace `def verify_log`, `def _release_died` and `def _rescuing` with calls to `mflib.runlog`, and remove `EVENTS`, `STOPPED` and the lock wait constant.
  Verify: `git grep -n -e "def verify_log" -e "def _release_died" -e "def _rescuing" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 3.4 In `skills/mf-ship/scripts/conduct.py` replace `def _log_stop` and `def _log_order` with the module's `stop` and `order`; `wait_run` polls a `Tail` and `report` reads the module's `events`.
  Verify: `git grep -n -e "def _log_stop" -e "def _log_order" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 3.5 In `skills/mf-ship/scripts/conduct.py` replace each pathname access of the claim — `active / "pid"`, `active / "start"`, `active.exists()`, `active.mkdir()`, `active.iterdir()`, `group.write_text`, `claim / str(worker.pid)` and `shutil.rmtree(active)` — with a call to `mflib.claim`.
  Verify: `git grep -n -F -e 'active / "pid"' -e 'active / "start"' -e 'active.exists()' -e 'active.mkdir()' -e 'active.iterdir()' -e 'group.write_text' -e 'claim / str(worker.pid)' -e 'shutil.rmtree(active)' -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 3.6 Add `claim.py` and `runlog.py` to the `names` cell of the conductor's row in `docs/modules.md`, each in its place in the order.
  Verify: `git grep -n -e "brief_check.py, claim.py" -- docs/modules.md` prints a line.
- [ ] 3.7 Re-point each line of `tests/test_conduct.py`, `tests/test_runlog.py` and `tests/test_claim.py` that reaches a name the conductor no longer defines to the module's; no assert changes.
  Verify: `uv run pytest tests/test_runlog.py tests/test_claim.py tests/test_viewer.py -q` exits 0.

## 4 — The fix

- [ ] 4.1 Add `"sync"` and `"codex"` to the event list of `skills/mflib/runlog.py` ([D4](design.md#d4)); the pin of the verify over a run that wrote one turns to the passing side.
  Verify: `git grep -n -e '"sync"' -- skills/mflib/runlog.py` prints a line.
- [ ] 4.2 In `skills/mflib/runlog.py` and `skills/mf-ship/scripts/conduct.py` remove the lock folder, its wait and the held error; the log object takes a lock of the process, and the stop line takes the module's append ([D5](design.md#d5), [D2](design.md#d2)).
  Verify: `git grep -n -e "LOCK_SECONDS" -- skills scripts` prints nothing.
- [ ] 4.3 In `skills/mflib/runlog.py` open the create, the append and the stop line under the runs folder's descriptor, as [D6](design.md#d6) says, and turn the write pins to the one side: a link and a pipe at the log, for the append and for the stop line. Turn the `names` cell of `skills/mflib/runlog.py`'s row in `docs/modules.md` from `—` to `statefile.py`.
  Verify: `uv run pytest tests/test_runlog.py tests/test_statefile.py -q` exits 0.
- [ ] 4.4 In `skills/mflib/runlog.py` read each log through `statefile.read`, and make `Tail` open its log once, read each span with `os.pread` and pass over a line longer than the bound ([D7](design.md#d7)), so no read of a log is the whole-file slice `read_bytes()[offset:]`. Turn the readers' pins to the one side: a bad byte, a pipe and a planted newer link.
  Verify: `git grep -n -F -e "os.pread" -- skills/mflib/runlog.py` prints a line and `git grep -n -F -e "read_bytes()[offset:]" -- skills scripts` prints nothing.
- [ ] 4.5 In `skills/mflib/runlog.py` make the order, the newest log, the release's death and the rescue's read pass over a name that is no stamp ([D8](design.md#d8)), and turn that pin to the one side.
  Verify: `uv run pytest tests/test_runlog.py -q` exits 0.
- [ ] 4.6 In `skills/mflib/runlog.py` make the verify pass an open spawn only under the stop line of the run itself ([D10](design.md#d10)), and turn its pin to the one side.
  Verify: `uv run pytest tests/test_runlog.py -q` exits 0.
- [ ] 4.7 In `skills/mflib/claim.py` read each entry through `statefile.read` by a bound, write each through `statefile.write` under the descriptor of `active` opened as [D9](design.md#d9) says, and raise `Refused` for a claim that is no folder. In `skills/mf-ship/scripts/conduct.py` turn `Refused` into `Stop` in `_conductor` and `_clear`, print it in `_close`, and end the worker's group in `work`, so `run` and `stop_run` halt naming the claim and `stop_run` kills nothing and writes no stop line. Turn the claim's pins to the one side, and the `names` cell of `skills/mflib/claim.py`'s row in `docs/modules.md` from `—` to `statefile.py`.
  Verify: `uv run pytest tests/test_claim.py tests/test_viewer.py -q` exits 0.
- [ ] 4.8 Lift the `slow` marker from each pin of `tests/test_runlog.py` and `tests/test_claim.py` that the fix makes end at once, and turn each assert of `tests/test_conduct.py` that holds a changed behaviour.
  Verify: `uv run pytest tests/test_runlog.py tests/test_claim.py -q` exits 0.

## 5 — The rule and the record

- [ ] 5.1 In `tests/test_structure.py` make `_format_name` name a string that contains `# Ship run` and one that holds the clock in either spelling, and add the clock pairs of `run.py` and `review_metrics.py` to `FORMAT_SITES` ([D12](design.md#d12)).
  Verify: `uv run pytest tests/test_structure.py -q` exits 0 and `git grep -n -F -e "# Ship run" -- tests/test_structure.py` prints a line.
- [ ] 5.2 Add to `tests/test_structure.py` the planted-breach twins of the run log's names, `def test_check_formats_run_log_…`: the title, each spelling of the clock, and a listed site that is gone.
  Verify: `uv run pytest tests/test_structure.py -q` exits 0 and `git grep -n -e "def test_check_formats_run_log" -- tests/test_structure.py` prints a line.
- [ ] 5.3 Amend D83 in `docs/decisions.md`: its format names gain the run log's title `# Ship run` and the event's clock, beside the card head.
  Verify: `git grep -n -F -e "# Ship run" -- docs/decisions.md` prints a line.
- [ ] 5.4 Amend D57 in `docs/decisions.md`: the run log is written and parsed by `skills/mflib/runlog.py` and the claim by `skills/mflib/claim.py`, beside the debt file's sentence.
  Verify: `git grep -n -e "mflib/claim.py" -- docs/decisions.md` prints a line.
- [ ] 5.5 In `THREAT_MODEL.md` name `skills/mflib/runlog.py` and `skills/mflib/claim.py` in the sentence on the conductor's writes and in the surface sentence of the shared home, and say that the claim and the log follow no link.
  Verify: `git grep -n -e "mflib/runlog.py" -- THREAT_MODEL.md` prints a line.
- [ ] 5.6 Add a sentence to `docs/recipes.md` after the debt file's: the run log is written and parsed through `skills/mflib/runlog.py` and the claim through `skills/mflib/claim.py`.
  Verify: `git grep -n -e "mflib/runlog.py" -- docs/recipes.md` prints a line.
