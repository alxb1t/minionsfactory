# Home layout — tasks

The phases: pin the home's names on today's code, give them one module, move the conductor and the pin, move the readers, then hold it with the rule and the record. Each name is in the table of [D2](design.md#d2).

## Progress

- [x] 1 — The pin · moderate
- [x] 2 — The module · hard
- [ ] 3 — The conductor and the pin · hard
- [ ] 4 — The readers · moderate
- [ ] 5 — The rule and the record · hard

## 1 — The pin

Each case runs green on today's code and is seen red once under the change it names, which the worker reverts ([D4](design.md#d4)). No file under `skills/` changes.

- [x] 1.1 In `tests/test_conduct.py` beside `test_cap_reads_ship_toml`, add `test_ship_toml_is_read_from_its_spelled_path`: with `XDG_CONFIG_HOME` unset it reads `~/.config/minionsfactory/ship.toml`, spelled by hand; set elsewhere, it reads that file and not the home's. Red under `".config"` renamed at `conduct.py:7151`.
  Verify: `uv run pytest tests/test_conduct.py -q -k ship_toml_is_read_from_its_spelled_path` exits 0.
- [x] 1.2 In `tests/test_conduct.py` add `test_a_home_name_is_its_spelled_path`, run for a primary and for a symlink to it. It spells the kept file, `.released`, `.default` and `.pushed` under `~/.mf-ship-origin` by hand, the digest by `hashlib` over `root.resolve()`. Red under `.resolve()` dropped at `conduct.py:1788` and a suffix renamed at `:1796`, `:1874` and `:1888`.
  Verify: `uv run pytest tests/test_conduct.py -q -k a_home_name_is_its_spelled_path` exits 0.
- [x] 1.3 In `tests/test_conduct.py` add `test_the_queue_names_are_their_spelled_paths`: `_queue_lock` makes `<digest>.queue/lock`, and `_merge_tried` reads a file planted at `<digest>.queue/supervised/<change>`, both spelled by hand. Extend `test_a_supervisor_settles_an_integrate_note` to assert the entry its run wrote stands at that path. Red under `"lock"` at `:7236`, `"supervised"` at `:7211` and at `:5143`.
  Verify: `uv run pytest tests/test_conduct.py -q -k the_queue_names_are_their_spelled_paths` exits 0.
- [x] 1.4 In `tests/test_conduct.py` add `test_the_scratch_folder_is_named_by_its_prefix`: a folder `_scratch` makes has the parent `Path.home()` and a name starting `.mf-ship-remote-`, spelled by hand. Red under the prefix renamed at `conduct.py:1995`.
  Verify: `uv run pytest tests/test_conduct.py -q -k scratch_folder_is_named_by_its_prefix` exits 0.
- [x] 1.5 In `tests/test_conduct.py` add `test_a_skill_is_looked_for_in_each_hosts_spelled_folder`: `_unlinked` stops for `claude` while `~/.claude/skills/mf-ship` is missing and for `codex` while `~/.agents/skills/mf-build` is missing, both spelled by hand. Red under either folder renamed at `conduct.py:183`.
  Verify: `uv run pytest tests/test_conduct.py -q -k skill_is_looked_for_in_each_hosts_spelled_folder` exits 0.
- [x] 1.6 In `tests/test_viewer.py` add `test_the_fingerprint_changes_when_a_cut_is_queued`, beside the fingerprint tests, queueing through its `_queue` helper. Red under `"cuts"` renamed at `viewer.py:588`.
  Verify: `uv run pytest tests/test_viewer.py -q -k fingerprint_changes_when_a_cut_is_queued` exits 0.
- [x] 1.7 In `tests/test_review_metrics.py` add `test_the_config_and_the_record_stand_at_their_spelled_paths`: with `XDG_CONFIG_HOME` unset, `config_path()` is `~/.config/minionsfactory/review-metrics.toml` and `recorded()` is `~/.mf-ship-origin/repos`, spelled by hand. Red under `".config"` renamed at `review_metrics.py:153` and the folder at `:162`.
  Verify: `uv run pytest tests/test_review_metrics.py -q -k config_and_the_record_stand_at_their_spelled_paths` exits 0.
- [x] 1.8 In `tests/test_review_metrics.py` add `test_the_codex_sessions_fall_back_to_their_spelled_folder`: with `CODEX_HOME` unset, `_codex_sessions` reads `~/.codex/sessions`, spelled by hand. Red under `".codex"` renamed at `review_metrics.py:595`.
  Verify: `uv run pytest tests/test_review_metrics.py -q -k codex_sessions_fall_back_to_their_spelled_folder` exits 0.
- [x] 1.9 In `tests/test_pin.py` add `test_the_data_folder_follows_its_variable`: with `XDG_DATA_HOME` unset an install exports under `~/.local/share/minionsfactory`, set elsewhere under that folder, both spelled by hand and reached through `install` alone. Red under `".local"` renamed at `pin.py:50`.
  Verify: `uv run pytest tests/test_pin.py -q -k data_folder_follows_its_variable` exits 0.
- [x] 1.10 In `tests/test_pin.py` add `test_a_live_install_keeps_its_checkout_under_the_home_folder`: `install(root, "live")` writes `~/.mf-ship-origin/checkout`, and `move` links the `skills` of the path that file holds, both spelled by hand. Red under `"checkout"` renamed at `pin.py:327` and at `:370`.
  Verify: `uv run pytest tests/test_pin.py -q -k live_install_keeps_its_checkout_under_the_home_folder` exits 0.

## 2 — The module

The home half lands in `skills/mflib/layout.py` and nothing calls it yet ([D1](design.md#d1)). Each public name has a one-line docstring that keeps the `Why:` of the def it replaces.

- [x] 2.1 In `skills/mflib/layout.py` make the module docstring say it names the run directory's paths and the home folder's, and that it reads `HOME` and the environment when asked ([D9](design.md#d9)). Add `import hashlib`, `KEPT_ORIGINS`, `kept_dir`, `digest`, `kept_file`, `released_dir`, `default_file` and `pushed_file` of [D2](design.md#d2).
  Verify: `git grep -n -e "^def digest" -e "^def kept_file" -e "^def pushed_file" -e "^KEPT_ORIGINS" -- skills/mflib/layout.py` prints each of them.
- [x] 2.2 In `skills/mflib/layout.py` add `queue_dir`, `queue_lock`, `queue_cuts`, `queue_rejoin`, `queue_briefs` and `queue_supervised`, then `gate_approval`, `live_dir`, `live_mark`, `repos_file` and `probe_mark`, as [D2](design.md#d2) gives them.
  Verify: `git grep -n -e "^def queue_dir" -e "^def queue_supervised" -e "^def gate_approval" -e "^def probe_mark" -- skills/mflib/layout.py` prints each of them.
- [x] 2.3 In `skills/mflib/layout.py` add `SCRATCH_PREFIX`, `scratch_parent`, `pin_source`, `pin_pending`, `pin_hold` and `pin_checkout`, then `config_dir`, `ship_file`, `review_metrics_file`, `ui_file`, `data_dir` and `state_dir`. Each variable reads empty as unset ([D1](design.md#d1)).
  Verify: `git grep -n -e "^SCRATCH_PREFIX" -e "^def pin_checkout" -e "^def config_dir" -e "^def state_dir" -- skills/mflib/layout.py` prints each of them.
- [x] 2.4 In `skills/mflib/layout.py` add `SKILLS`, `skills_dir`, `codex_home` and `claude_home`, as [D2](design.md#d2) gives them.
  Verify: `git grep -n -e "^SKILLS" -e "^def skills_dir" -e "^def codex_home" -e "^def claude_home" -- skills/mflib/layout.py` prints each of them.
- [x] 2.5 In `tests/test_layout.py` add `test_a_kept_name_is_its_spelled_path`, parametrised over `kept_dir`, `kept_file`, `released_dir`, `default_file`, `pushed_file`, the `queue_*` names, `gate_approval`, `live_dir`, `live_mark`, `repos_file`, `probe_mark` and the `pin_*` names, each against `~/.mf-ship-origin/...` spelled by hand. Add `test_a_linked_path_has_the_primarys_digest`.
  Verify: `uv run pytest tests/test_layout.py -q -k "a_kept_name_is_its_spelled_path or a_linked_path_has_the_primarys_digest"` exits 0.
- [x] 2.6 In `tests/test_layout.py` add `test_a_root_follows_its_variable`, parametrised over the config files, `data_dir`, `state_dir`, `codex_home`, `claude_home`, `skills_dir` and `scratch_parent`: each against its hand-spelled path with the variable unset and set, and its answer changes when `HOME` or the variable changes between calls. The state root's case sets `XDG_STATE_HOME` itself.
  Verify: `uv run pytest tests/test_layout.py -q -k a_root_follows_its_variable` exits 0.
- [x] 2.7 In `tests/test_layout.py` add `test_an_empty_variable_reads_as_unset`: each of `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_STATE_HOME`, `CODEX_HOME` and `CLAUDE_CONFIG_DIR` set to `""` gives the fallback path.
  Verify: `uv run pytest tests/test_layout.py -q -k an_empty_variable_reads_as_unset` exits 0.

## 3 — The conductor and the pin

`conduct.py` and `pin.py` take every home path from the module, and their pairs leave the rule's lists ([D3](design.md#d3), [D5](design.md#d5), [D6](design.md#d6)). No assert changes: a test line changes only the name it reaches.

- [ ] 3.1 In `skills/mf-ship/scripts/conduct.py` delete `KEPT_ORIGINS`, `_digest`, `_kept_file`, `_ledger`, `_default_file` and `_pushed_file`. Each caller, and each `Path.home() / KEPT_ORIGINS` join, takes the name [D2](design.md#d2) pairs with it: `kept_file`, `released_dir`, `default_file`, `pushed_file`, `queue_dir`, `live_mark`, `repos_file`, `probe_mark` and `gate_approval` of `mflib.layout`. The halt messages that spell `~/{KEPT_ORIGINS}/<name>` take `mflib.layout.KEPT_ORIGINS`.
  Verify: `git grep -n -w -e _digest -e _kept_file -e _ledger -e _default_file -e _pushed_file -e "Path.home() / KEPT_ORIGINS" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 3.2 In `skills/mf-ship/scripts/conduct.py` each join off `_queue(primary)` or `_queue(self.primary)` takes `mflib.layout.queue_supervised`, `queue_briefs`, `queue_cuts`, `queue_rejoin` or `queue_lock`, and each other call takes `queue_dir`. `_queue` stays as the one line `return mflib.layout.queue_dir(primary)` that 3.1 left, which the viewer and the tests still reach.
  Verify: `git grep -n -F -e "_queue(primary)" -e "_queue(self.primary)" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 3.3 In `skills/mf-ship/scripts/conduct.py` `_scratch` takes `scratch_parent()` and `SCRATCH_PREFIX` of `skills/mflib/layout.py` in place of `.mf-ship-remote-`, and keeps its temp-folder fallback. `_plugins_off` takes `claude_home()` in place of `CLAUDE_CONFIG_DIR`, `_ship_file` takes `ship_file()` in place of `XDG_CONFIG_HOME`, and `_codex_home` is deleted with its caller taking `codex_home()`.
  Verify: `git grep -n -F -e _codex_home -e CLAUDE_CONFIG_DIR -e XDG_CONFIG_HOME -e mf-ship-remote- -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 3.4 In `skills/mf-ship/scripts/conduct.py` delete `SKILLS`; `_unlinked` takes `mflib.layout.skills_dir(executor)`. `_queue`'s docstring says the home folder's queue without spelling `.mf-ship-origin`.
  Verify: `git grep -n -w -e SKILLS -e mf-ship-origin -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 3.5 In `skills/mf-ship/scripts/pin.py` delete `KEPT`, `HOSTS`, `data` and `_kept`. `_read` and `_write` take a path of `pin_source()`, `pin_pending()`, `pin_hold()` or `pin_checkout()`; `live` lists `live_dir()`; each `data()` is `data_dir()`; each `Path.home() / host` takes `skills_dir(executor)`, the loops running over `mflib.layout.SKILLS.items()` and keeping `host` only where a message spells it. No `Path.home()`, `XDG_DATA_HOME` or `.mf-ship-origin` stands in the file.
  Verify: `git grep -n -F -e "Path.home()" -e XDG_DATA_HOME -e mf-ship-origin -e KEPT -e HOSTS -- skills/mf-ship/scripts/pin.py` prints nothing.
- [ ] 3.6 In `tests/test_conduct.py`, `tests/test_pin.py` and `tests/test_viewer.py` each line that reaches `KEPT_ORIGINS`, `SKILLS`, `_digest`, `_kept_file`, `_ledger`, `_default_file`, `_pushed_file` or `_codex_home` of the conductor takes the module's name (`from mflib import layout`). The cases of phase 1 that name them take the module's too.
  Verify: `grep -rnE "\[.(KEPT_ORIGINS|SKILLS|_digest|_kept_file|_ledger|_default_file|_pushed_file|_codex_home).\]" tests` prints nothing.
- [ ] 3.7 In `tests/test_structure.py` delete the pairs `("conduct.py", ".mf-ship-origin")` and `("pin.py", ".mf-ship-origin")` from `LAYOUT_SITES`.
  Verify: `git grep -n -e 'conduct.py", ".mf-ship-origin' -e 'pin.py", ".mf-ship-origin' -- tests/test_structure.py` prints nothing.

## 4 — The readers

`gate_check.py`, the viewer and `review_metrics.py` take their home paths from the module, and the conductor's `_queue` goes ([D3](design.md#d3), [D5](design.md#d5)). Each keeps its own guard and error text.

- [ ] 4.1 In `skills/mf-converge/scripts/gate_check.py` delete `KEPT`, the constant for `.mf-ship-origin`, and the comment above it; `approval` reads `mflib.layout.gate_approval(_primary(), change)`. Reword `approval`'s docstring to name `digest` of the shared home in place of `_digest`.
  Verify: `git grep -n -F -e KEPT -e mf-ship-origin -e _digest -- skills/mf-converge/scripts/gate_check.py` prints nothing.
- [ ] 4.2 In `skills/mf-ui/scripts/viewer.py` delete `config_path`, `state_folder` and `recorded`, which spell `XDG_CONFIG_HOME`, `XDG_STATE_HOME`, `Path.home()` and `.mf-ship-origin`; their callers take `mflib.layout.ui_file()`, `state_dir()` and `repos_file()`. `fingerprint` takes `mflib.layout.queue_cuts(self.primary)` in place of `self.conduct["_queue"]`.
  Verify: `git grep -n -F -e "Path.home()" -e XDG_ -e mf-ship-origin -e '"_queue"' -- skills/mf-ui/scripts/viewer.py` prints nothing.
- [ ] 4.3 In `skills/mf-review-metrics/scripts/review_metrics.py` delete `config_path` and `recorded`, which spell `XDG_CONFIG_HOME`, `Path.home()` and `.mf-ship-origin`; their callers take `mflib.layout.review_metrics_file()` and `repos_file()`, and `_codex_sessions` takes `mflib.layout.codex_home()` in place of `CODEX_HOME`.
  Verify: `git grep -n -F -e "Path.home()" -e XDG_ -e CODEX_HOME -e mf-ship-origin -- skills/mf-review-metrics/scripts/review_metrics.py` prints nothing.
- [ ] 4.4 In `skills/mf-ship/scripts/conduct.py` delete the one-line def that phase 3 left, `def _queue(primary: Path)`; it has no caller there.
  Verify: `git grep -n -F -e "def _queue(" -- skills/mf-ship/scripts/conduct.py` prints nothing.
- [ ] 4.5 In `tests/test_conduct.py`, `tests/test_viewer.py` and `tests/test_review_metrics.py` each line that reaches the conductor's `_queue`, the viewer's `config_path`, `state_folder` or `recorded`, or `review_metrics.config_path` or `review_metrics.recorded`, takes the module's name. The cases of phase 1 that name them take the module's too.
  Verify: `grep -rnE "(conduct\[.?_queue.?\]|ns\[.(config_path|state_folder|recorded)|review_metrics\.(config_path|recorded))" tests` prints nothing.
- [ ] 4.6 In `tests/test_structure.py` delete the pairs `("gate_check.py", ".mf-ship-origin")`, `("review_metrics.py", ".mf-ship-origin")` and `("viewer.py", ".mf-ship-origin")` from `LAYOUT_SITES`, and `("viewer.py", "_queue")` from `PRIVATE_REACH`.
  Verify: `git grep -n -e 'gate_check.py", ".mf-ship-origin' -e 'review_metrics.py", ".mf-ship-origin' -e 'viewer.py", "_queue' -- tests/test_structure.py` prints nothing.

## 5 — The rule and the record

The sixth rule gains its new reaches after the phases that clean their sites ([D7](design.md#d7)); the record says what the code reaches ([D8](design.md#d8), [D9](design.md#d9)).

- [ ] 5.1 In `tests/test_structure.py` `check_layout` reports `x.py spells <name>: a home-folder name outside layout.py` for a string constant outside `skills/mflib/layout.py` that contains `.mf-ship-origin` or equals `XDG_CONFIG_HOME`, `XDG_DATA_HOME` or `XDG_STATE_HOME`, whatever `listed` holds. The module passes.
  Verify: `git grep -n -F ".mf-ship-origin" -- "skills/mf-*/scripts/*.py" "scripts/*.py"` prints nothing, and `git grep -n -F XDG_ -- "skills/mf-*/scripts/*.py" "scripts/*.py"` prints nothing.
- [ ] 5.2 In `tests/test_structure.py` add the twins: `test_check_layout_fails_on_a_home_folder_name` for `".mf-ship-origin"` and `"~/.mf-ship-origin/x"`, `test_check_layout_fails_on_an_xdg_name` for each XDG name, `test_check_layout_ignores_a_list_for_a_home_name`, and `test_layout_sites_name_no_home_folder_name`. The planted-constant case of `.mf-ship-origin` in `test_check_layout_fails_on_a_planted_constant` goes to the first.
  Verify: `uv run pytest tests/test_structure.py -q -k "home_folder_name or an_xdg_name or ignores_a_list_for_a_home_name or layout_sites_name_no_home"` exits 0.
- [ ] 5.3 In `docs/principles.md` the closed list under *The repo reaches nothing outside itself* gains `<digest>.released`, `<digest>.default`, the probe's mark, the scratch folders `.mf-ship-remote-*`, `settings.json` under `~/.claude` or `CLAUDE_CONFIG_DIR`, the Codex sessions the conductor reads, and the queue's `briefs/` and `supervised/` ([D8](design.md#d8)).
  Verify: `git grep -c -e "supervised" -- docs/principles.md` exits 0.
- [ ] 5.4 In `THREAT_MODEL.md` and `docs/modules.md` the lines that say `the port to the OS and the run directory's layout` say `the port to the OS, and the layout of the run directory and of the home folder`. In `docs/recipes.md` the executor recipe's rows for the conductor's `SKILLS` (where its skills live) and pin's `HOSTS` (the skills folders the pin links) give way to a row for `skills/mflib/layout.py`'s `SKILLS`.
  Verify: `git grep -n -e "the run directory's layout" -e "where its skills live" -e "skills folders the pin links" -- THREAT_MODEL.md docs` prints nothing.
- [ ] 5.5 In `docs/recipes.md` the state-file recipe's rule line states that no string constant outside `skills/mflib/layout.py` contains `.mf-ship-origin` or equals an XDG variable's name, and that `LAYOUT_SITES` lists neither.
  Verify: `git grep -n -e "mf-ship-origin" -- docs/recipes.md` prints a line.
