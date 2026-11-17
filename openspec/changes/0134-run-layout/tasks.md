# Run layout — tasks

The phases: pin the region on today's code, born the module, move the conductor, move the stations, make the old layout one table, close with the sixth rule and the record.

## Progress

- [x] 1 — The pin · moderate
- [x] 2 — The module · hard
- [x] 3 — The conductor follows · moderate
- [ ] 4 — The stations follow · moderate
- [ ] 5 — The old layout is one table · hard
- [ ] 6 — The sixth rule and the record · hard

## 1 — The pin

Tests only: no file under `skills/` or `scripts/` changes in this phase ([D11](design.md#d11)).

- [x] 1.1 **HALT CHECK** The premise of the move: the change folder is one join, `"changes" / change`, in the folder finder of `conduct.py`, `gate_check.py` and `run.py`.
  Verify: `git grep -c -F '".minions" / "changes" / change' -- skills/mf-ship/scripts/conduct.py skills/mf-converge/scripts/gate_check.py scripts/metrics/run.py` prints a line for each of those files.
- [x] 1.2 Write `tests/old_layout.py`: `ENTRIES`, each old path under `.minions/` as a literal pattern (`findings/{}_review.md` … `gate-check/{}`) mapped to its new name; `ROLES`, `changes/{}/review.md` and `changes/{}/security.md` likewise; `LOG`, `runs/20261101-230000/{}_converge-2.log` mapped to `logs/20261101-230000-converge-2.log`; and `plant(minions, change, old)`, which writes the one file.
  Verify: `grep -n -e "ENTRIES" tests/old_layout.py` prints a line.
- [x] 1.3 In `tests/test_conduct.py` add `test_a_run_moves_each_old_entry_alone` and `test_status_names_each_old_entry_alone`, each over `ENTRIES`, `ROLES` and `LOG`, built as `test_a_run_moves_an_old_layout` (`:7456`) and `test_status_names_an_old_layout` (`:7592`) are: the first calls `migrate_layout` and finds the file at its new name, and a second call moves nothing; the second finds `status` naming the change `old layout`.
  Verify: `uv run pytest tests/test_conduct.py -q -k "test_a_run_moves_each_old_entry_alone or test_status_names_each_old_entry_alone"` exits 0.
- [x] 1.4 In `tests/test_converge.py` add `test_converge_halts_on_each_old_entry_alone` over `ENTRIES` and `ROLES`: it plants the one file through `plant`, as `_old` (`:367-370`) plants one, and runs converge as the test that uses `_old` does, finding the halt names that path.
  Verify: `uv run pytest tests/test_converge.py -q -k test_converge_halts_on_each_old_entry_alone` exits 0.
- [x] 1.5 In `tests/test_gate_check.py` add `test_gate_check_halts_on_each_old_entry_alone` and in `tests/test_integrate.py` `test_integrate_halts_on_each_old_entry_alone`, each over `ENTRIES` and `ROLES`: exit 2, the entry's path and `is the old layout: /mf-ship moves it`, as `tests/test_gate_check.py:96` and `tests/test_integrate.py:69` hold.
  Verify: `uv run pytest tests/test_gate_check.py tests/test_integrate.py -q -k "test_gate_check_halts_on_each_old_entry_alone or test_integrate_halts_on_each_old_entry_alone"` exits 0.
- [x] 1.6 In `tests/test_metric_scripts.py` add `test_run_metrics_halt_on_each_old_entry_alone` over `ENTRIES` and `LOG`: `OldLayout` naming the path, as `:582` holds.
  Verify: `uv run pytest tests/test_metric_scripts.py -q -k test_run_metrics_halt_on_each_old_entry_alone` exits 0.
- [x] 1.7 In `tests/test_converge.py` add `test_a_freeze_reads_the_cards_of_a_lone_backlog`: with an old `backlog.md` holding one card and no `debt.md`, the freeze's `debt-cards.md` holds the card. The read is `converge.py:523-525`; the lock rule `:1296-1300` is held by `tests/test_converge.py:1969-1982`.
  Verify: `uv run pytest tests/test_converge.py -q -k lone_backlog` exits 0.
- [x] 1.8 In `tests/test_viewer.py` add `test_the_fingerprint_changes_when_a_change_folders_file_is_written`, beside `:628`: a file written under `changes/<id>/` changes the fingerprint, and the run log is not the file.
  Verify: `uv run pytest tests/test_viewer.py -q -k change_folders_file_is_written` exits 0.
- [x] 1.9 Write `tests/test_run_dir_finders.py`: from a linked worktree and from the primary, each of `integrate.py`'s `_run_dir`, `cut_pre.py`'s `run_directory`, `metrics.py`'s `run_directory`, `awake.py`'s `_record` and `run.py`'s `Version` gives the primary's `.minions/`. The repo and worktree are built with `tests/fake_worker.py`'s `_git`.
  Verify: `uv run pytest tests/test_run_dir_finders.py -q` exits 0.
- [x] 1.10 See each case of 1.3 to 1.9 red under one change to the code it holds — an entry removed from its table, the `.parent` dropped from a finder, a `changes/*/*` stat dropped from the fingerprint — then revert it, and name each change in the phase's commit body.
  Verify: `git diff --stat -- skills scripts` prints no line.

## 2 — The module

- [x] 2.1 Write `skills/mflib/layout.py` with the names of [D2](design.md#d2) but the old-layout table and its reader: each a function of a primary `Path`, public, computed when called, `os`, `pathlib` and `re` the only imports, `MINIONS = ".minions"` and `CHANGES = "changes"` the only joins' words. It runs no git ([D3](design.md#d3)).
  Verify: `grep -n -e "^def change_dir" -e "^def primary_of" -e "^def run_dir" skills/mflib/layout.py` prints a line for each.
- [x] 2.2 Write `tests/test_layout.py`: each function against the path spelled by hand under a `tmp_path` primary; `primary_of` of the common directory git answers from a linked worktree and from the primary gives one primary.
  Verify: `uv run pytest tests/test_layout.py -q` exits 0.
- [x] 2.3 Add the row `| skills/mflib/layout.py | home | — |` to `docs/modules.md`, between the rows of `__init__.py` and `platform.py`.
  Verify: `git grep -n -F "skills/mflib/layout.py" -- docs/modules.md` prints a line.
- [x] 2.4 In `tests/test_structure.py` widen `check_seed` to `scripts/` per [D7](design.md#d7): a file under `scripts/` takes the seed with `parents[N] / "skills"`, `N` its depth. Add `test_check_seed_passes_a_scripts_seed_of_its_depth`, `test_check_seed_fails_on_no_scripts_seed` and `test_check_seed_fails_on_a_scripts_seed_of_the_wrong_depth`.
  Verify: `uv run pytest tests/test_structure.py -q -k scripts_seed` exits 0.
- [x] 2.5 Turn the `outside-skills` case of `test_check_seed_passes_a_seeded_or_exempt_import` into a case of `test_check_seed_fails_on_an_unseeded_import`, per the table of design's `## Tests`.
  Verify: `git grep -n -e "outside-skills" -- tests/test_structure.py` prints no line.

## 3 — The conductor follows

A move: no assert changes ([D6](design.md#d6)).

- [x] 3.1 In `conduct.py`, which holds the seed already (`:42-43`), add `import mflib.layout` after `import mflib.platform`, and make `primary_of` (`:503-504`), `_repo` (`:487`) and `preconditions` (`:4503`) take the primary from `layout.primary_of`; `_common_dir` keeps its `resolve()`.
  Verify: `grep -n -e "import mflib.layout" skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 3.2 Move `OLD_LAYOUT`, `OLD_ROLES`, `OLD_ID`, `OLD_STAMP`, `OLD_LOG`, `_old_files` and `_old_layout` from `conduct.py` into `layout.py` as the names of [D5](design.md#d5), and make `migrate_layout` (`:6800-6805`), `grant` (`:7995`), `status` and `report` (`:8197`, `:8307`) read them from `layout`. Add to `tests/test_layout.py` `test_old_files_finds_each_old_entry_alone` over `ENTRIES`, `ROLES` and `LOG`, and `test_old_layout_names_the_first_sorted_path`.
  Verify: `uv run pytest tests/test_layout.py -q -k "old_files_finds_each_old_entry_alone or old_layout_names_the_first_sorted_path"` exits 0.
- [x] 3.3 Delete `_change_dir` from `conduct.py`; each of its calls becomes `layout.change_dir`, and the descriptors `_folder_fd` and `_remove_in` open over `layout.run_dir(primary)`, `layout.CHANGES` and the id.
  Verify: `git grep -n -w "_change_dir" -- skills/mf-ship/scripts/conduct.py` prints no line.
- [x] 3.4 In `conduct.py` make `_run_dir`, the claim, `runs/`, `gate/`, `cuts/<id>`, `metrics/<id>.html` and the debt names (`DEBT`, `DEBT_LOCK`, `OLD_DEBT`, `OLD_DEBT_LOCK`) read `layout.run_dir`, `layout.claim_file`, `layout.runs_dir`, `layout.gate_dir`, `layout.cut_reservation`, `layout.metrics_page`, `layout.debt_file`, `layout.debt_lock`, `layout.backlog_file` and `layout.backlog_lock`. Where the text of a debt name is the point — a halt or event message, the substring test at `:1655`, `_clear_stale_lock`'s `name` — the site takes the same text as `layout.debt_lock(primary).relative_to(primary)`.
  Verify: `git grep -n -e "^DEBT" -e "^OLD_DEBT" -- skills/mf-ship/scripts/conduct.py` prints no line.
- [x] 3.5 In `pin.py` add the seed, as `conduct.py`'s `:42` is, and `import mflib.layout`; take the primary at `:351` from `layout.primary_of(Path(common).resolve())`. Add `layout.py` to the `names` cells of `conduct.py` and `pin.py` in `docs/modules.md`, in base-name order.
  Verify: `grep -n -e "import mflib.layout" skills/mf-ship/scripts/pin.py` prints a line.
- [x] 3.6 Point each test that reached a moved name at its new place, changing no assert.
  Verify: `uv run pytest tests/test_conduct.py tests/test_pin.py tests/test_sandboxed.py tests/test_layout.py tests/test_structure.py -q` exits 0.

## 4 — The stations follow

A move: no assert changes. Each script keeps its git call, its guard and its error text ([D3](design.md#d3)). A script that holds the seed already gains `import mflib.layout` after it; one that does not gains both.

- [ ] 4.1 In `converge.py` add the seed and import, and read `layout.change_dir` for `Context.folder` (`:302-305`). `debt_lock` takes a primary, not `.minions`, its one caller (`:1455-1467`) passes it and its `minions` local goes, and the debt and backlog joins (`:523-524`, `:1296`, `:1301`, `:1456`, `:1534`) read `layout.debt_file`, `layout.debt_lock` and `layout.backlog_file`; `:491`'s junit report stays.
  Verify: `git grep -c -e "import mflib.layout" -- skills/mf-converge/scripts/converge.py` prints a line.
- [ ] 4.2 In `gate_check.py` and `gate_run.py` add the seed and import; `_primary` (`:96-99`) takes `layout.primary_of`, `_change_dir` is deleted and its calls read `layout.change_dir`, and `records` (`:67-70`) returns `layout.gate_dir` of the primary.
  Verify: `git grep -c -e "import mflib.layout" -- skills/mf-converge/scripts/gate_check.py skills/mf-converge/scripts/gate_run.py` prints a line for each of those files.
- [ ] 4.3 In `integrate.py` add the seed and import; a `_primary(cwd)` holds the git call, `_run_dir(cwd)` returns `layout.run_dir` of it, and `_change_dir` is deleted, its calls reading `layout.change_dir(_primary(cwd), change)`.
  Verify: `git grep -c -e "import mflib.layout" -- skills/mf-integrate/scripts/integrate.py` prints a line.
- [ ] 4.4 In `cut_context.py` and `cut_pre.py` add the seed and import, and in `awake.py`, which holds the seed, the import; read `layout.run_dir`, `layout.debt_file`, `layout.change_dir` and `layout.cut_reservation` at their finders and joins. `cut_pre.py`'s second git call (`:124`) stays.
  Verify: `git grep -c -e "import mflib.layout" -- skills/mf-cut-change/scripts/cut_context.py skills/mf-cut-change/scripts/cut_pre.py skills/mf-cut-change/scripts/awake.py` prints a line for each of those files.
- [ ] 4.5 In the build's `metrics.py` add the seed and import; `run_directory(root)` (`:205-208`) and the page's path (`:597`) read `layout.run_dir` and `layout.metrics_page`.
  Verify: `git grep -c -e "import mflib.layout" -- skills/mf-build/scripts/metrics.py` prints a line.
- [ ] 4.6 In `review_metrics.py` add the seed and import; delete `_change_dir` and `CHANGES` and the folder constants at `:33-36`, and read `layout.change_dir`, `layout.run_dir` and `layout.runs_dir` of the repo as named, with no git ([D4](design.md#d4)).
  Verify: `git grep -c -e "import mflib.layout" -- skills/mf-review-metrics/scripts/review_metrics.py` prints a line.
- [ ] 4.7 In `viewer.py`, which holds the seed, add the import and read `layout.run_dir`, `layout.runs_dir`, `layout.claim_file` and `layout.change_dir` at `:214-225`, `:305`, `:364`, `:579` and `:581`.
  Verify: `git grep -c -e "import mflib.layout" -- skills/mf-ui/scripts/viewer.py` prints a line.
- [ ] 4.8 In `scripts/metrics/run.py`, `scripts/metrics/debt.py` and `scripts/corpus.py` add the seed of [D7](design.md#d7) and the import, delete `run.py`'s `_change_dir`, and read `layout.primary_of`, `layout.run_dir`, `layout.change_dir`, `layout.debt_file` and `layout.runs_dir` at the finders, `DEBT` (`:16`, printed as `no {DEBT}` at `:39`, so that text stays) and `:299`.
  Verify: `git grep -c -e "import mflib.layout" -- scripts/metrics/run.py scripts/metrics/debt.py scripts/corpus.py` prints a line for each of those files.
- [ ] 4.9 Add `layout.py` to the `names` cell of each script that imports it, in `docs/modules.md`, in base-name order; point each test that reached a moved name at its new place. Converge's cell gains `layout.py`, and `tests/test_skills.py`'s `test_mf_converge_names_each_script_the_map_says_it_loads` holds `skills/mf-converge/SKILL.md` to that cell: name `../../mflib/layout.py` in its list of what converge loads (`:56-57`), beside `../../mf-integrate/scripts/integrate.py`, for the run directory's paths.
  Verify: `uv run pytest tests/test_structure.py tests/test_skills.py -q` exits 0.
- [ ] 4.10 No script under `skills/` or `scripts/` holds `def _change_dir`.
  Verify: `git grep -n -e "def _change_dir" -- skills scripts` prints no line.

## 5 — The old layout is one table

The one behaviour change of the version ([D5](design.md#d5)).

- [ ] 5.1 In `skills/mf-converge/scripts/converge.py` delete its `OLD_LAYOUT` and `old_layout`; its halt reads `layout.old_layout(primary, change)`, its words and return code stay (`:793-795`).
  Verify: `git grep -n -e "^OLD_LAYOUT" -- skills/mf-converge/scripts/converge.py` prints no line.
- [ ] 5.2 In `gate_check.py` and `integrate.py` delete their `OLD_LAYOUT` and `_old_layout`; the halts read `layout.old_layout` and keep their words and exit 2 (`:489-492`, `:270-273`).
  Verify: `git grep -n -e "^OLD_LAYOUT" -- skills/mf-converge/scripts/gate_check.py skills/mf-integrate/scripts/integrate.py` prints no line.
- [ ] 5.3 In `scripts/metrics/run.py` delete `OLD_LAYOUT`, `OLD_LOG`, its own `_old_layout` and the worker-log loop at `:150-158`; `Version` raises `OldLayout` from `layout.old_layout` with the same words.
  Verify: `git grep -n -e "^OLD_LAYOUT" -e "^OLD_LOG" -- scripts` prints no line.
- [ ] 5.4 Turn the cases of 1.4 to 1.6 to the one table: each of the four copies is tested over `ENTRIES`, `ROLES` and `LOG`. Add to each of the four test files `test_a_halt_names_the_first_sorted_path`: it plants `build/{}.done` and `findings/{}_review.md`, and finds the halt naming `.minions/build/<id>.done`.
  Verify: `uv run pytest tests/test_converge.py tests/test_gate_check.py tests/test_integrate.py tests/test_metric_scripts.py -q -k test_a_halt_names_the_first_sorted_path` exits 0.
- [ ] 5.5 In `tests/test_layout.py` add `test_the_table_equals_the_literals`: `OLD_LAYOUT`, `OLD_ROLES` and `OLD_LOG` equal `tests/old_layout.py`'s `ENTRIES`, `ROLES` and `LOG`.
  Verify: `uv run pytest tests/test_layout.py -q -k test_the_table_equals_the_literals` exits 0.
- [ ] 5.6 Add the old worker log, `.minions/runs/<stamp>/<change-id>_<station>[-<n>].log`, to the old-layout lists of `skills/mf-build/SKILL.md`, `skills/mf-integrate/SKILL.md` and `skills/mf-release/SKILL.md`, after `release/<change-id>.held` and `gate-check/<change-id>/`.
  Verify: `git grep -c -F "runs/<stamp>/<change-id>_" -- skills/mf-build/SKILL.md skills/mf-integrate/SKILL.md skills/mf-release/SKILL.md` prints a count for each of those files.
- [ ] 5.7 Every definition of the table stands in the module alone; a test that reached a deleted name reaches it through `layout`, changing no assert.
  Verify: `git grep -n -e "^OLD_LAYOUT" -- skills scripts` prints a line of `skills/mflib/layout.py` alone.

## 6 — The sixth rule and the record

- [ ] 6.1 In `tests/test_structure.py` add `check_layout(root, listed=LAYOUT_SITES)` per [D8](design.md#d8), `test_check_layout_holds_on_the_tree`, and the twins `test_check_layout_fails_on_a_planted_constant`, `test_check_layout_fails_on_a_planted_prefix`, `test_check_layout_passes_the_layout_module`, `test_check_layout_fails_on_a_listed_site_that_is_gone` and `test_check_layout_passes_a_docstring`.
  Verify: `uv run pytest tests/test_structure.py -q -k "check_layout_fails or check_layout_passes"` exits 0.
- [ ] 6.2 Write `LAYOUT_SITES` from the rule's own output on the tree: each remaining pair of base name and name.
  Verify: `uv run pytest tests/test_structure.py -q -k test_check_layout_holds_on_the_tree` exits 0.
- [ ] 6.3 In `docs/decisions.md` edit D57: the finder is `change_dir` of `skills/mflib/layout.py`; drop *each script finding it through its own `_change_dir`* and the accepts clause that waits for the home. Edit D83: the sixth rule, in its list of what `tests/test_structure.py` holds.
  Verify: `git grep -c -F "mflib/layout.py" -- docs/decisions.md` prints a count.
- [ ] 6.4 In `docs/recipes.md` rewrite the state-file recipe's rows, its paragraph on the finder and its rules line, which name `_change_dir`: a reader takes `change_dir` from `skills/mflib/layout.py`, and `check_layout` holds that `.minions` is joined there alone.
  Verify: `git grep -n -e "_change_dir" -- docs/recipes.md` prints no line.
- [ ] 6.5 In `THREAT_MODEL.md` extend the surface sentence of `skills/mflib/*` (`:126`) to say the home holds the run directory's layout, beside the port to the OS: `the port to the OS and the run directory's layout`.
  Verify: `git grep -n -F "the run directory's layout" -- THREAT_MODEL.md` prints a line.
- [ ] 6.6 In `docs/modules.md` extend the line that defines the `home` layer to say it holds the port to the OS and the run directory's layout.
  Verify: `git grep -n -F "run directory's layout" -- docs/modules.md` prints a line.
