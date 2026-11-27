# Roots — tasks

Pin today's opens and the riders, move the riders, move the roots, say what is true. Each phase cites [design](design.md).

## Progress

- [x] 1 — Pin the roots and the riders · moderate
- [x] 2 — The riders · moderate
- [x] 3 — The root · hard
- [ ] 4 — The record · moderate

## 1 — Pin the roots and the riders

- [x] 1.1 In `tests/test_statefile.py` add a case for each opener of the marks (`marks.write`), the models file (`modelsfile.write`), the findings (`findings.stamp`), the claim (`claim.take`) and the run log (`runlog.stop`): `.minions` is a link to a folder outside, and the call lands in that folder. Name each `test_<module>_follows_a_link_at_minions`, per [D7](design.md#d7).
  Verify: `uv run pytest tests/test_statefile.py -q` exits `0`.
- [x] 1.2 In `tests/test_conduct.py` add the same case for `_restamp`, `_free_log`, `migrate_layout`, a cut's reservation (`_remove_in` through `Run.cutting`) and `conduct.py grant`, each reached through `tests/conduct_load.py`.
  Verify: `uv run pytest tests/test_conduct.py -n auto -q` exits `0`.
- [x] 1.3 In `tests/test_converge.py` add the case for converge's `_change_folder`: `.minions` is a link, and the folder opens in its target.
  Verify: `uv run pytest tests/test_converge.py -q` exits `0`.
- [x] 1.4 In `tests/test_gate_run.py` pin `read_record` as it is: a record that is a link is read through, and a record with a byte that is not UTF-8 raises `UnicodeDecodeError`.
  Verify: `uv run pytest tests/test_gate_run.py -q` exits `0`.
- [x] 1.5 In `tests/test_facts.py` pin `write_notes` as it is: a `cut-notes.md` that is a link is written through to its target, whether `fresh` or appended. `context.md` refuses a link today by `cut_context._write`, and its case stands.
  Verify: `uv run pytest tests/test_facts.py -q` exits `0`.
- [x] 1.6 In `tests/test_cut_pre.py` pin `check_reserved` and `check_id` as they are: a reservation that is a link is read through.
  Verify: `uv run pytest tests/test_cut_pre.py -q` exits `0`.

## 2 — The riders

- [x] 2.1 In `skills/mflib/layout.py` add `RUNS`, `CUTS` and `GRANTS` beside `MINIONS` and `CHANGES`, and `cuts_dir(primary)` and `def grants_dir(primary)`; build `runs_dir` and `cut_reservation` on them. In `tests/test_layout.py` check each name against its hand-spelled path.
  Verify: `git grep -q -F "def grants_dir" -- skills/mflib/layout.py` exits `0`.
- [x] 2.2 In `skills/mf-ship/scripts/conduct.py` make `Run.cutting`, `_next_id`, `cut`, `_granted`, `Run.ship` and `grant` drop the literals `"cuts"` and `"grants"` and call `mflib.layout` for the names, per [D6](design.md#d6).
  Verify: `git grep -n -e '"cuts"' -e '"grants"' -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 2.3 In `skills/mf-converge/scripts/gate_run.py` drop `path.read_text()` from `read_record` for `mflib.statefile.read_bytes` and a strict decode: a link or a bad byte gives `{}`. Turn the pins of 1.4 to that.
  Verify: `git grep -n -F "path.read_text()" -- skills/mf-converge/scripts/gate_run.py` prints nothing.
- [x] 2.4 In `skills/mflib/statefile.py` add `write_or_say(path, text) -> str | None`: the staged write refusing a link, its failure as the line `<path> is a link` or `<path>: <reason>`, else `None`. Make `write` in `bundle.py` and in `open_cards.py` call it and raise their own `Stop`, dropping their `ELOOP` test and the `errno` import `bundle.py` then leaves unused. Add its cases to `tests/test_statefile.py`.
  Verify: `git grep -n ELOOP -- skills/mf-converge/scripts/bundle.py skills/mf-converge/scripts/open_cards.py` prints nothing.
- [x] 2.5 In `skills/mf-cut-change/scripts/facts.py` write and append `cut-notes.md` through `mflib.statefile`, an append as a read and a staged write that refuses a link; load `mflib.statefile` after the seed line its folder fixes. In `skills/mf-cut-change/scripts/cut_context.py` write `context.md` through the staged write, its refusal of a link still saying `is a link`, and add a case to `tests/test_cut_context.py`: a hard link at `context.md` keeps the other name's text. In `docs/modules.md` add `statefile.py` to the rows of `facts.py` and `cut_context.py`. Turn the pins of 1.5 to the refusal.
  Verify: `uv run pytest tests/test_cut_context.py tests/test_facts.py tests/test_structure.py -n auto -q` exits `0`.
- [x] 2.6 In `skills/mf-ship/scripts/conduct.py` make `grant` open its folder through `_folder_fd` with the primary as root and `mflib.layout.MINIONS` and `mflib.layout.GRANTS` as parts, and create the grant in it with `O_NOFOLLOW`: no `mkdir` or `touch` of a plain path. Turn the grant case of 1.2 to the refusal, asserting the stop and the unchanged target and no message.
  Verify: `uv run pytest tests/test_conduct.py -n auto -q` exits `0`.
- [x] 2.7 In `skills/mf-cut-change/scripts/cut_pre.py` read the reservations through `mflib.statefile.open_folder` with the primary as root and `mflib.layout.MINIONS` and `mflib.layout.CUTS` as parts: a missing folder holds none, and a link at `.minions` or `cuts/` fails both checks, naming it. `check_reserved` takes a regular file by `lstat` through the descriptor, and a link or a folder there fails naming it; `check_id` lists through it. Add `statefile.py` to its row of `docs/modules.md`. Turn the pins of 1.6, and add cases to `tests/test_cut_pre.py`: a missing `cuts/` holds none, and a link at `cuts/` and a link at `.minions` each fail both checks.
  Verify: `uv run pytest tests/test_cut_pre.py tests/test_structure.py -n auto -q` exits `0`.
- [x] 2.8 In `skills/mf-converge/scripts/converge.py` drop the literals `.with_suffix(".open.md")` in `open_cards` and `{each}.open.md` in the verify prompt, and name the page through `mflib.layout.open_name`.
  Verify: `git grep -n -F -e 'with_suffix(".open.md")' -e '{each}.open.md' -- skills/mf-converge/scripts/converge.py` prints nothing.

## 3 — The root

- [x] 3.1 **HALT CHECK** `skills/mf-release/scripts/release.py` opens no folder itself, per [D4](design.md#d4): it needs no edit.
  Verify: `git grep -n -e "statefile.folder" -e "open_folder" -- skills/mf-release/scripts/release.py` exits `1`.
- [x] 3.2 In `skills/mflib/layout.py` add `def beneath(path)`, per [D2](design.md#d2): the root and the parts to open that folder, the nearest `.minions` ancestor taken; with none, the path itself and no parts. Add its cases to `tests/test_layout.py`: a path below `.minions`, one with none, one with a nested `.minions`.
  Verify: `git grep -q -F "def beneath" -- skills/mflib/layout.py` exits `0`.
- [x] 3.3 In `skills/mflib/marks.py` make `_folder` and `read` open from `primary`, with `layout.MINIONS` the first part, in place of `layout.run_dir(primary)` as root. In `skills/mflib/modelsfile.py` do the same in `load` and `write`.
  Verify: `git grep -n -e "folder(layout.run_dir" -- skills/mflib/marks.py skills/mflib/modelsfile.py` prints nothing.
- [x] 3.4 In `skills/mflib/findings.py` open `_staged`'s folder through `layout.beneath(folder.parent)` with `folder.name` as the last part, and add `layout.py` to the row of `findings.py` in `docs/modules.md`.
  Verify: `git grep -n -e "folder(folder.parent" -- skills/mflib/findings.py` prints nothing.
- [x] 3.5 In `skills/mflib/claim.py` open `active.parent` in `_open`, `take` and `remove` through `layout.beneath`, `_open` adding `active.name` as its last part, and add `layout.py` to the row of `claim.py` in `docs/modules.md`.
  Verify: `git grep -n -e "folder(active.parent" -- skills/mflib/claim.py` prints nothing.
- [x] 3.6 In `skills/mflib/runlog.py` open the runs folder in `stop`, `RunLog.__init__` and `RunLog.event` through `layout.beneath`, and add `layout.py` to its row of `docs/modules.md`.
  Verify: `git grep -n -e "folder(runs)" -e "folder(self.runs)" -- skills/mflib/runlog.py` prints nothing.
- [x] 3.7 In `skills/mf-ship/scripts/conduct.py` make `_restamp` open from `runs.parent` as root with `mflib.layout.MINIONS` as the first part, dropping `statefile.folder(runs` for it.
  Verify: `git grep -n -F "statefile.folder(runs" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 3.8 In `skills/mf-ship/scripts/conduct.py` make the calls of `_free_log` in `Run.worker` pass `self.primary` as root: the run's own log with parts `mflib.layout.MINIONS`, `mflib.layout.RUNS` and the stamp, a version's worker log with `mflib.layout.MINIONS` before `CHANGES`.
  Verify: `git grep -n -e "_free_log(self.runs" -e "_free_log(mflib.layout.run_dir" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 3.9 In `skills/mf-ship/scripts/conduct.py` make the `_folder_fd` calls of `Run.migrate_layout` and `cut`, and the `_remove_in` call of `Run.cutting`, pass the primary as root and `mflib.layout.MINIONS` as the first part; add `minions` to `migrate_layout`'s list of links to refuse. Keep the name `_folder_fd`, and leave `_fresh_tmp`, `sandboxed`, `_scratch_folder`, `_fetch_npm` and `_hide_marks`, per [D3](design.md#d3).
  Verify: `git grep -n -e "_folder_fd(mflib.layout.run_dir" -e "_remove_in(mflib.layout.run_dir" -e "minions, mflib.layout.CHANGES" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [x] 3.10 In `skills/mf-converge/scripts/converge.py` make `_change_folder` open from the primary with `mflib.layout.MINIONS` as the first part, in place of `run_dir` as root.
  Verify: `git grep -n -e "folder(run_dir" -- skills/mf-converge/scripts/converge.py` prints nothing.
- [x] 3.11 Turn each case of 1.1, 1.2 and 1.3 but the grant's from "lands in the target" to "is refused, the target unchanged"; the pins of the sites [D3](design.md#d3) keeps stand.
  Verify: `uv run pytest tests/test_statefile.py tests/test_conduct.py tests/test_converge.py tests/test_structure.py -n auto -q` exits `0`.
- [x] 3.12 Check that no opener of the home passes the run directory as root.
  Verify: `git grep -n -e "folder(layout.run_dir" -e "folder(run_dir" -e "folder(runs" -e "folder(self.runs" -e "_free_log(self.runs" -- skills` prints nothing.

## 4 — The record

- [ ] 4.1 In `THREAT_MODEL.md` rewrite the sentences of the run log and the claim, the models file, the findings files and the marks so each says its folder is opened from the primary, `.minions` a part refused as a link; the sentences carry the words `part refused`. Drop "but follow the `.minions` root" from the marks and keep the stand test's and the time's clause; reword the "other in-process writes" sentence for the riders of [D6](design.md#d6).
  Verify: `git grep -q -F "part refused" -- THREAT_MODEL.md` exits `0`.
- [ ] 4.2 In `docs/recipes.md` add `mark's name` to the `check_formats` line, and word the sentences of the run log, the claim and the findings so each folder is found through `layout.beneath`.
  Verify: `git grep -q -F "mark's name" -- docs/recipes.md` exits `0`.
