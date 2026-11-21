# Models — tasks

Pin the models file's code as it stands, give it a module, move the stations onto the module with no assert changed, fix the copies that disagree, then bring the record in line.

## Progress

- [ ] 1 — The pin · moderate
- [ ] 2 — The module · hard
- [ ] 3 — The stations · moderate
- [ ] 4 — The fix · hard
- [ ] 5 — The rule and the record · moderate

## 1 — The pin

- [ ] 1.1 In `tests/test_conduct.py`, rewrite `test_a_build_spawn_removes_the_halt_the_last_build_left` to reach the build's spawn through `_main(conduct, root, "run", "--executor", "claude", monkeypatch=monkeypatch)`, as the HUMAN-phase case above it does ([D14](design.md#d14)). It keeps its assertions: the spawn, the halt file gone, `rescue.md` kept.
  Verify: `uv run pytest tests/test_conduct.py::test_a_build_spawn_removes_the_halt_the_last_build_left -q` exits 0.
- [ ] 1.2 Create `tests/test_modelsfile.py`: a docstring `Why: 0142-models design D3.`, the conductor loaded by `conduct_load`, `brief_check.py` loaded as `tests/test_brief_check.py` loads it, and a helper that writes a change's `models.toml` under a repository in `tmp_path`. A case that would block on a pipe runs the read in a child process, killed after 10 s. Stage the file with `git add`, so the searches below see it.
  Verify: `git grep -n -F -e "0142-models design D3" -- tests` prints a line.
- [ ] 1.3 Write cases a, b and c of [the cases](design.md#the-cases) as `def test_case_a_…`, `def test_case_b_…` and `def test_case_c_a_folder_at_the_models_file`, each by key from the loaded conductor. Each is seen red under the change its row names, then green; the commit's body names the line changed.
  Verify: `git grep -n -e "def test_case_c_a_folder_at_the_models_file" -- tests` prints a line.
- [ ] 1.4 Write cases d, e and f the same way, as `def test_case_d_…`, `def test_case_e_…` and `def test_case_f_only_a_top_level_decide`, the key readers and the parser reached by key.
  Verify: `git grep -n -e "def test_case_f_only_a_top_level_decide" -- tests` prints a line.
- [ ] 1.5 Write case g as `def test_case_g_integrate_reads_the_release_table` and its siblings, one test a row of its list: integrate, the rescue, the worker tables, the token check, the moderate table's executor, the executor defaults, wrong-typed words, the supervisor's defaults and a `claude` model on Codex.
  Verify: `git grep -n -e "def test_case_g_integrate_reads_the_release_table" -- tests` prints a line.
- [ ] 1.6 Write cases h, i, j and k as `def test_case_h_…`, `def test_case_i_…`, `def test_case_j_…` and `def test_case_k_only_auto_grant_false`, each a table of values and the answer each gives.
  Verify: `git grep -n -e "def test_case_k_only_auto_grant_false" -- tests` prints a line.
- [ ] 1.7 Write cases l, m, n and o as `def test_case_l_…`, `def test_case_m_…`, `def test_case_n_…` and `def test_case_o_a_moved_worker_table` at the run level: a `Run` on a repository in `tmp_path`, the worker spawns recorders, so no worker starts. Case m runs `take`, case n `read_plan`, case o the rejoin's take-back.
  Verify: `git grep -n -e "def test_case_o_a_moved_worker_table" -- tests` prints a line.
- [ ] 1.8 Write cases q and r as `def test_case_q_…` and `def test_case_r_the_models_text`: the conductor's child run of `brief_check.py` with a timeout, a failure and a bad byte in the child's output; the text `brief_check.py --models` prints for an item with every optional part, byte for byte.
  Verify: `git grep -n -e "def test_case_r_the_models_text" -- tests` prints a line.
- [ ] 1.9 Write a `def test_pin_…` for each row of [the pins](design.md#the-pins), as the code behaves today, the pipe row as `def test_pin_a_pipe_at_the_models_file`. A row whose read would block on a pipe runs it in a child process.
  Verify: `git grep -n -e "def test_pin_a_pipe_at_the_models_file" -- tests` prints a line.

## 2 — The module

- [ ] 2.1 In `skills/mflib/statefile.py` add `open_folder(root, *parts)` as [D13](design.md#d13) says, and its cases to `tests/test_statefile.py`: a missing part, a link at a part, a file at a part, a link at `root` followed, and nothing made.
  Verify: `git grep -n -e "^def open_folder" -- skills/mflib/statefile.py` prints a line.
- [ ] 2.2 In `skills/mflib/claim.py`, open the claim folder through `statefile.open_folder`: a missing parent and a missing claim read as no claim, a link at the claim and a file at it raise `Refused`, as today. No assert of `tests/test_claim.py` changes.
  Verify: `git grep -n -e "open_folder" -- skills/mflib/claim.py` prints a line.
- [ ] 2.3 In `skills/mflib/layout.py` add `MODELS = "models.toml"` and `models_file(primary, change)`, and let `OLD_LAYOUT`'s models entry take `MODELS`; add the case to `tests/test_layout.py`.
  Verify: `git grep -n -e "^def models_file" -- skills/mflib/layout.py` prints a line.
- [ ] 2.4 Create `skills/mflib/modelsfile.py` with the names of [D1](design.md#d1) that phase 2 lists, `TABLES` to `text`, each as its copy behaves today: `text` is `brief_check.py`'s text writer's body, `TABLES` its map. Seed `brief_check.py` with the line `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))` after its imports; nothing loads the module yet. Stage the module with `git add`, so the searches see it.
  Verify: `git grep -n -e "^def text(decided" -- skills/mflib` prints a line.
- [ ] 2.5 Add `read`, `table`, `decides`, `shadows`, `rescue_skips`, `auto_grants` and `skipping`, each the body of the conductor's copy: `read` is its models-file parser, following a link, raising `Broken` for text that is not TOML and letting a bad byte rise.
  Verify: `git grep -n -e "^def skipping" -- skills/mflib` prints a line.
- [ ] 2.6 Add `def digest(primary: Path, change: str)` and `write`, each the body of the conductor's copy: `digest` is its hash, open `O_NOFOLLOW`, `None` on an open error; `write` is its writer, remove then create, raising `OSError` as the copy does. Both go through `statefile.folder`, and `write` removes the file in its own `_remove(primary, change)`.
  Verify: `git grep -n -F -e "def digest(primary: Path, change: str)" -- skills/mflib` prints a line.
- [ ] 2.7 Write the module's unit cases in `tests/test_modelsfile.py` as `def test_module_…`, one per function of [D1](design.md#d1), `digest` as `def test_module_digest…`: `text` equals what `brief_check.py --models` prints for an item with every part, and each other function gives what the pins of its copy hold. Re-point no test of the conductor yet.
  Verify: `git grep -n -e "def test_module_digest" -- tests` prints a line.
- [ ] 2.8 In `docs/modules.md` add the row `skills/mflib/modelsfile.py`, layer `home`, names `layout.py, statefile.py`, after the `layout.py` row.
  Verify: `git grep -n -e "skills/mflib/modelsfile.py" -- docs/modules.md` prints a line.

## 3 — The stations

- [ ] 3.1 In `brief_check.py` move the parse of an item's models line into `models_of(opened, item)` returning `decided`, `named` and `shadowed`, print `modelsfile.text(...)` under `--models`, and take `modelsfile.TOKEN` and `modelsfile.TABLES`. Its text writer, its tables map and its token pattern go. Put `import mflib.modelsfile` directly after the seed line of 2.4, as `conduct.py` does with its own.
  Verify: `git grep -n -e "^def models_toml" -e "^TABLES = " -e "^TOKEN = " -- skills/mf-plan/scripts/brief_check.py` prints nothing.
- [ ] 3.2 In `conduct.py` add `_models_data(runs, change)`, which words `modelsfile.Broken` as the `Stop` the copy raised, and `_unwritten(change, error)`, which returns the `Stop` that words a failed write as [D2](design.md#d2) says. The conductor's models-file parser, hash and writer go; `_check_cut`, `cutting` and `cut` call `modelsfile.digest` and `modelsfile.write`.
  Verify: `git grep -n -e "^def _models_file" -e "^def _write_models" -e "^def _models_hash" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 3.3 In `conduct.py` let `_table`, `_decides`, `_shadows`, `_skips_rescue`, `_auto_grants` and `_skips` read `_models_data` through the module's `table`, `decides`, `shadows`, `rescue_skips`, `auto_grants` and `skipping`; `_models` takes the module's old-name map and `modelsfile.TOKEN`, and the conductor's old-name map and token pattern go; the by-hand converge check takes `modelsfile.TOKEN`.
  Verify: `git grep -n -e "^TOKEN = " -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 3.4 In `tests/test_conduct.py` re-point the line that takes the conductor's models-file hash by key to `mflib.modelsfile.digest`. Replace the line that takes its models-file writer by key with a local `write` that calls `mflib.modelsfile.write` and raises `conduct["_unwritten"](change, error)` on its `OSError`, and point the `__globals__` patch at `mflib.modelsfile.write.__globals__` and the module's `_remove`, its `plant` taking that step's arguments. No assert changes.
  Verify: `git grep -n -e "conduct\[\"_models_hash\"\]" -e "conduct\[\"_write_models\"\]" -- tests/test_conduct.py` prints nothing.
- [ ] 3.5 Re-point `tests/test_modelsfile.py`'s cases of phase 1 that take the conductor's models-file hash and writer by key to `mflib.modelsfile.digest` and `mflib.modelsfile.write`, the writer through the same local `write` as in 3.4, by their new lines only; the cases through `_models`, `_skips` and the run stay on the conductor.
  Verify: `git grep -n -e "conduct\[\"_models_hash\"\]" -e "conduct\[\"_write_models\"\]" -- tests/test_modelsfile.py` prints nothing.
- [ ] 3.6 In `docs/modules.md` add `modelsfile.py` to the `names` cells of the `skills/mf-ship/scripts/conduct.py` row and the `skills/mf-plan/scripts/brief_check.py` row, each in its alphabetical place.
  Verify: `git grep -c -e "modelsfile.py" -- docs/modules.md` prints `3`.

## 4 — The fix

- [ ] 4.1 **HALT CHECK** Premise of card 0111·S1: the conductor's per-station token check still guards the converge workers and the moderate table alone, so a `[build]` model that is no token passes. If this does not hold the plan is wrong.
  Verify: `git grep -n -F -e "if station in (*WORKERS, MODERATE):" -- skills/mf-ship/scripts/conduct.py` prints a line.
- [ ] 4.2 One map ([D4](design.md#d4)): remove `OLD_WORKERS`, the old checker-table map, from the module and from `_models`, and its fallback there. In `test_a_checker_on_another_host_is_planned_and_probed` the old-table lines now expect the defaults, `("claude", None, None)` for both stations. Turn case g's row for a worker table before its old name and the pin of keys no writer writes. Add `PERSON` to the module.
  Verify: `git grep -n -e "OLD_WORKERS" -- skills scripts` prints nothing.
- [ ] 4.3 One token rule ([D5](design.md#d5)): `read` checks every `model` and `effort` of every table of `TABLES` and `PERSON` and raises `Broken("<table> '<word>' is not a model or effort")`; the loop in `_models` goes, its moderate-executor check stays. Add a case that a `[build]` model `TMPDIR=/tmp/mf-codex-x` halts its version, and turn case g's token row and the pin of a word that is no token to every table.
  Verify: `git grep -n -F -e "is not a model or effort" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 4.4 One read ([D6](design.md#d6)): add `BOUND` and `def load(primary: Path, change: str)` to `modelsfile.py` and build `read` on it; `Broken` carries the phrases of the table. A bad byte no longer rises as `UnicodeDecodeError`. Turn the readers' clauses of the pins of a link, a pipe, a folder, a dangling link, a bad byte and the scopes of failure, cases d, m and n, the module's `read` cases of 2.7, and the third run of `test_run_halts_when_a_worker_claims_what_disk_does_not_show` to a halt of version `0001-todo` with `0002-marks` going on.
  Verify: `git grep -n -F -e "def load(primary: Path, change: str)" -- skills/mflib` prints a line.
- [ ] 4.5 In `conduct.py` let `_skips` raise the `Stop` of a broken file, and let `stage_of` and `_unjudged` read no skip when it does. Turn the `[converge` row of `test_a_checker_on_another_host_is_planned_and_probed` to `pytest.raises(conduct["Stop"])`, and case i's row for a bad byte likewise. Add `def test_stage_of_reads_no_skip_from_a_broken_file` to `tests/test_modelsfile.py`.
  Verify: `git grep -n -e "def test_stage_of_reads_no_skip_from_a_broken_file" -- tests` prints a line.
- [ ] 4.6 The hash through the read ([D7](design.md#d7)): `digest` hashes `load`'s bytes and raises `Broken` for a broken file; `_check_cut` calls it before it reads the entry's text and fails a broken file as `changes/<id>/models.toml: <why>`, a missing one as `no .minions/changes/<id>/models.toml`. Turn the pin of the queued text against the file, case c to the phrase `it is not a regular file`, and the module's `digest` cases of 2.7. Add `def test_the_cut_check_names_a_broken_models_file`.
  Verify: `git grep -n -e "def test_the_cut_check_names_a_broken_models_file" -- tests` prints a line.
- [ ] 4.7 The staged write ([D8](design.md#d8)): `write` calls `statefile.write(..., refuse_link=True, folder=fd)`, raising `statefile.WriteFailed`; the remove-first step and `_remove` go, and `_unwritten` takes the `WriteFailed`; the local `write` of 3.4 and 3.5 catches it, not the `OSError`. Turn the writers' clauses of the pins of a link, a hard link, a pipe and a folder, the module's `write` cases of 2.7, and `test_a_link_planted_after_the_removal_truncates_no_models_file` to a hard link planted before the write (the name replaced, the other name's content kept), and add `def test_a_link_at_the_models_file_is_refused`: a link at the file stops the cut with exit 2.
  Verify: `git grep -n -e "def test_a_link_at_the_models_file_is_refused" -- tests` prints a line.
- [ ] 4.8 Status names a broken file ([D10](design.md#d10)): in `conduct.py`'s `status`, append ` — <the Stop's text without "conduct: halt — ">` to a version's line when `_models_data` stops for it, with `def test_status_names_a_broken_models_file` in `tests/test_modelsfile.py`.
  Verify: `git grep -n -e "def test_status_names_a_broken_models_file" -- tests` prints a line.
- [ ] 4.9 In the status command's row of `skills/mf-ship/SKILL.md` say that a version whose models file is broken keeps its line and gains the clause of 4.8, with the example `0001-todo · build — changes/0001-todo/models.toml: it is not UTF-8`.
  Verify: `git grep -n -F -e "models.toml: it is not UTF-8" -- skills/mf-ship/SKILL.md` prints a line.
- [ ] 4.10 The writer's flag ([D9](design.md#d9)): add `--write <change-id>` to `brief_check.py`, valid beside `--models` alone, with its cases in `tests/test_brief_check.py`: it writes the file, prints `brief: wrote .minions/changes/<change-id>/models.toml`, exits 1 on an item out of shape, 2 on no item, and 2 on a failed write. Its `git rev-parse` runs with a timeout; a git that fails or finds no repository prints `brief: cannot write — <why>` and exits 2, with `def test_write_stops_with_2_when_git_finds_no_repository`.
  Verify: `git grep -n -F -e "--write" -- skills/mf-plan/scripts/brief_check.py` prints a line.
- [ ] 4.11 In `docs/modules.md` add `layout.py` to the names of the `brief_check.py` row, so it reads `station | conduct.py, layout.py, modelsfile.py, verify_check.py`.
  Verify: `git grep -n -F -e "station | conduct.py, layout.py, modelsfile.py, verify_check.py" -- docs/modules.md` prints a line.

## 5 — The rule and the record

- [ ] 5.1 Add `def test_the_one_map_round_trips` to `tests/test_modelsfile.py` ([D12](design.md#d12)): every table and key `modelsfile.text` writes for an item with every part, the switch and the shadow is read back by `modelsfile.read`, and the person's keys `[rescue]`, `[supervise]` and `auto_grant` are read though `text` writes none.
  Verify: `git grep -n -e "def test_the_one_map_round_trips" -- tests` prints a line.
- [ ] 5.2 In `docs/decisions.md` edit D57, D77 and D41 as [D15](design.md#d15) says: the file is written and parsed by `skills/mflib/modelsfile.py`; `brief_check.py --models --write` writes it for the attended cut; no prose calls it yet.
  Verify: `git grep -n -F -e "modelsfile.py" -- docs/decisions.md` prints a line.
- [ ] 5.3 In `THREAT_MODEL.md` say in the change folder's bullet that the models file is read through no link, bounded, and written staged refusing a link by `skills/mflib/modelsfile.py`, and add the module to the home folder's entry in the surfaces list, among the format modules.
  Verify: `git grep -n -F -e "modelsfile.py" -- THREAT_MODEL.md` prints a line.
- [ ] 5.4 In `docs/recipes.md` add the models file, written and parsed through `skills/mflib/modelsfile.py`, to the state-file recipe's line of modules, its path `layout.models_file(primary, change)`, and bring the rule line up to the format kinds `check_formats` holds: `status_log.md`, `## Run`, `# Ship run`, the card head and the run log's clock.
  Verify: `git grep -n -F -e "modelsfile.py" -- docs/recipes.md` prints a line.
