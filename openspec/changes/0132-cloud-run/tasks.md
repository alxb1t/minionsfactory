# Cloud run — tasks

The phases follow [design](design.md): the pin, the setting, the tags, the fetch, the guard and Codex, the record. Each task names its files and links the decision it follows.

## Progress

- [x] 1 — The pin · moderate
- [x] 2 — The setting · moderate
- [x] 3 — The tags · hard
- [x] 4 — The fetch · hard
- [x] 5 — The guard and Codex · moderate
- [x] 6 — The record · moderate

## 1 — The pin

- [x] 1.1 In `tests/test_conduct.py` add `test_a_refused_tag_push_halts_the_run`, marked `slow`, shaped on `test_a_tag_alone_starts_one_run`: `_with_origin`, an executable `hooks/update` in the bare `origin` that exits 1 for a ref under `refs/tags/`, `_released(root, "v0.1.0")`, then `_run_claude` ends 1, the log's line before the close is `run · halt — git push origin v0.1.0 failed, exit 1`, and `origin`'s `main` is the local one ([D1](design.md#d1)).
  Verify: `uv run pytest tests/test_conduct.py::test_a_refused_tag_push_halts_the_run -q` passes.
- [x] 1.2 In `tests/test_conduct.py` add `test_a_local_default_behind_origin_passes`, marked `slow`: `_with_origin`, a clone that pushes a commit to `origin`, `git fetch -q origin` in the primary, then `status` prints `status: none — no open version`, `_run_claude` ends 0, and the primary's `main` is where it was ([D3](design.md#d3)).
  Verify: `uv run pytest tests/test_conduct.py::test_a_local_default_behind_origin_is_brought_up -q` passes — the name 4.6 gives it.
- [x] 1.3 In `tests/test_conduct.py` add `test_the_config_guard_refuses_a_gc_key`, shaped on `test_a_planted_remote_key_refuses_status_and_run`: `git config gc.auto 0` in the primary makes `_status` exit 1 with `gc.auto` in its line ([D4](design.md#d4)).
  Verify: `uv run pytest tests/test_conduct.py::test_the_config_guard_allows_gc_auto -q` passes — the name 5.2 gives it.

## 2 — The setting

- [x] 2.1 In `skills/mf-ship/scripts/conduct.py` add `_ship_file() -> tuple[Path, dict[str, Any]]` before `_cap`, holding the read `_cap` makes today and returning an empty dict for no file; make `_cap` call it and keep its checks and its messages ([D1](design.md#d1)).
  Verify: `git grep -n "^def _ship_file" -- skills/mf-ship/scripts/conduct.py` prints the line.
- [x] 2.2 In `skills/mf-ship/scripts/conduct.py` add `_pushes_tags() -> bool` after `_cap`: `True` for no table, no key or `True`, `False` for `False`, else a `Stop` with code 2 naming the file and saying `tags` is not true or false. Its docstring ends `Why: 0132-cloud-run design D1` ([D1](design.md#d1)).
  Verify: `git grep -n "^def _pushes_tags" -- skills/mf-ship/scripts/conduct.py` prints the line.
- [x] 2.3 In `tests/test_conduct.py` add `test_ship_toml_reads_tags`, shaped on `test_cap_reads_ship_toml` and its `_ship_toml`: no file, no `[push]`, no key and `true` give `True`; `false` gives `False`; a string, a number and an unreadable file raise `Stop` with code 2 matching the file's path ([D1](design.md#d1)).
  Verify: `uv run pytest tests/test_conduct.py -q -k ship_toml_reads_tags` passes.
- [x] 2.4 In `skills/mf-ship/scripts/conduct.py` add `self.tags: bool = True` after `self.cap` in `Run.__init__`, `tags = _pushes_tags()` after `cap = _cap()` in `run`, and `conductor.tags = tags` after `conductor.cap = cap` ([D1](design.md#d1)).
  Verify: `git grep -n -e "self.tags: bool = True" -e "tags = _pushes_tags()" -e "conductor.tags = tags" -- skills/mf-ship/scripts/conduct.py` prints a line holding each.
- [x] 2.5 In `tests/test_conduct.py`, in `test_cap_file_that_is_bad_stops_the_run`, add a step after its last assert: `_ship_toml('[push]\ntags = "yes"\n')`, then `_run_claude` ends 2, the output holds `ship.toml`, `.minions/runs/active` is absent and `_calls(calls)` is empty ([D1](design.md#d1)).
  Verify: `git grep -n -F 'tags = "yes"' -- tests/test_conduct.py` prints the line.
- [x] 2.6 In `skills/mf-ship/scripts/conduct.py` add `push_tags: bool = True` to `_unpushed` after `first_read` and to `_local_releases` after `default`. False makes `_unpushed` skip its loop over the tags, so `found` holds the default branch alone, and `_local_releases` name no tag ([D1](design.md#d1)).
  Verify: `git grep -n "push_tags: bool = True" -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.7 In `skills/mf-ship/scripts/conduct.py` pass `push_tags=self.tags` to `_unpushed` in `Run.push_left` and in `Run.unpushed`, and to `_local_releases` in `Run.unpushed` ([D1](design.md#d1)).
  Verify: `git grep -n "push_tags=self.tags" -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.8 In `skills/mf-ship/scripts/conduct.py`, in `Run.advance`, change `reason = ask(True, self.offline)` to `reason = ask(True, self.offline or not self.tags)`, with a comment that `offline` skips the check that the tag is on `origin` ([D1](design.md#d1)).
  Verify: `git grep -n -F "ask(True, self.offline or not self.tags)" -- skills/mf-ship/scripts/conduct.py` prints the line.
- [x] 2.9 In `skills/mf-ship/scripts/conduct.py`, in `status`, call `_unpushed(primary, push_tags=tags)` with `tags = _pushes_tags()` read first, and append `run · tags — this machine pushes none` after the unpushed line when `tags` is false ([D1](design.md#d1)).
  Verify: `git grep -n -F "run · tags — this machine pushes none" -- skills/mf-ship/scripts/conduct.py` prints the line.
- [x] 2.10 In `tests/test_conduct.py` add `test_status_says_a_machine_pushes_no_tag`, shaped on `test_a_tag_alone_starts_one_run` with `conduct["_keep_origin"](root)` called first: with no setting `status` names `main v0.1.0` and no `tags` line; with `[push] tags = false` it names `main` and prints the line ([D1](design.md#d1)).
  Verify: `uv run pytest tests/test_conduct.py -q -k status_says_a_machine` passes.
- [x] 2.11 In `tests/test_conduct.py`, in `test_a_refused_tag_push_halts_the_run`, add a step after the halt: the comment `# tags = false: no tag, no halt`, `_ship_toml("[push]\ntags = false\n")`, then `_run_claude` ends 0, `origin` lists no tag and the log holds no halt line ([D1](design.md#d1)).
  Verify: `git grep -n -F "# tags = false: no tag, no halt" -- tests/test_conduct.py` prints the line.
- [x] 2.12 In `tests/test_conduct.py` add `test_a_release_with_tags_false_lands_without_its_tag`, marked `slow`, shaped on `test_a_push_that_lands_before_origin_flaps_passes` with no flap and `_ship_toml("[push]\ntags = false\n")`: `run(0)` holds `0001-todo · check — release · pass`, `origin`'s `main` is the local one, `origin` lists no tag, the local `v0.1.0` stands and the version's worktree is gone. Its commit body says why no existing test fits ([D1](design.md#d1)).
  Verify: `uv run pytest tests/test_conduct.py -q -k a_release_with_tags_false` passes.

## 3 — The tags

- [x] 3.1 In `skills/mf-ship/scripts/conduct.py` add `_release_commits(primary: Path, base: str) -> dict[str, str]` after `_merges_a_release`, as [D2](design.md#d2) says, reading `base`'s first-parent merges and their second parents through `_history`. Its docstring ends `Why: 0132-cloud-run design D2`.
  Verify: `git grep -n "^def _release_commits" -- skills/mf-ship/scripts/conduct.py` prints the line.
- [x] 3.2 In `skills/mf-ship/scripts/conduct.py` add `_make_tags(primary: Path, base: str) -> list[str]` after `_release_commits`: `git tag -a -m <tag> <tag> <commit>` through `_git` for each entry whose `refs/tags/<tag>` does not exist, returning the tags made ([D2](design.md#d2)).
  Verify: `git grep -n "^def _make_tags" -- skills/mf-ship/scripts/conduct.py` prints the line.
- [x] 3.3 In `skills/mf-ship/scripts/conduct.py` add `start: bool = False` and `notes: list[str] | None = None` to `_unpushed` after `push_tags`, and `notes = [] if notes is None else notes` at its head. Under `first_read and start`, after `_close_releases(primary, base)`, call `_make_tags(primary, base)` and append `made <tag>` to `notes` for each tag it returns ([D2](design.md#d2)).
  Verify: `git grep -n -F "_make_tags(primary, base)" -- skills/mf-ship/scripts/conduct.py` prints the line.
- [x] 3.4 In `skills/mf-ship/scripts/conduct.py` add `self.fresh: bool = False` after `self.tags` in `Run.__init__`, and in `Run.ship` set `self.fresh = True` before `self.push_left(RETRIES)` and `self.fresh = False` after it ([D3](design.md#d3)).
  Verify: `git grep -n -e "self.fresh = True" -e "self.fresh = False" -- skills/mf-ship/scripts/conduct.py` prints a line holding each.
- [x] 3.5 In `skills/mf-ship/scripts/conduct.py`, in `Run.push_left`, make `notes: list[str] = []` before each read, pass `start=self.fresh, notes=notes` to `_unpushed`, and log each note as `self.log.event("run", "sync", note)` before `self.push(unpushed)` ([D3](design.md#d3)).
  Verify: `git grep -n -F 'self.log.event("run", "sync", note)' -- skills/mf-ship/scripts/conduct.py` prints the line.
- [x] 3.6 In `tests/test_conduct.py` add `test_the_tags_origin_holds_are_made_locally`, shaped on `test_a_forged_release_on_an_older_default_is_not_pushed` and its `_released` and `_with_origin`, calling `conduct["_make_tags"](root, base)` with `base` the tip `origin` holds: a deleted local tag is made, annotated, with the tag as its message, on the release commit; several are each made; a tag that points elsewhere is left; a release commit only local, a wrong subject and a merge with another tree get none ([D2](design.md#d2)).
  Verify: `uv run pytest tests/test_conduct.py -q -k tags_origin_holds` passes.
- [x] 3.7 In `tests/test_conduct.py` add `test_a_start_makes_a_missing_tag_and_pushes_it_where_tags_go`, marked `slow`, shaped on `test_a_tag_alone_starts_one_run`: a release pushed with its tag deleted locally, then `_run_claude` ends 0, the log holds `run · sync — made v0.1.0`, `v0.1.0` is annotated and `origin` lists it; the same for `v0.2.0` under `[push] tags = false`, where `origin` does not ([D2](design.md#d2)).
  Verify: `uv run pytest tests/test_conduct.py -q -k a_start_makes_a_missing_tag` passes.

## 4 — The fetch

- [x] 4.1 In `skills/mf-ship/scripts/conduct.py` add `keep: bool = False` to `_outside` and `_remote`; with it `_outside` adds `GIT_OBJECT_DIRECTORY` to the scratch environment, naming the object folder it already reads for the alternates file, so a fetch stores its objects in the primary, and with it write no alternates file ([D3](design.md#d3)).
  Verify: `git grep -n "GIT_OBJECT_DIRECTORY" -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 4.2 In `skills/mf-ship/scripts/conduct.py` add `_fetch_default(primary: Path, url: str, default: str, base: str, notes: list[str]) -> None` after `_unpushed`'s helpers, as the flow of [D3](design.md#d3): fetch when the primary lacks `base`, `--negotiation-tip` naming the local branch's sha read in the primary, a failure `Unreachable`, `git merge --ff-only` only when the local branch is a strict ancestor of `base`, a note for each act.
  Verify: `git grep -n "^def _fetch_default" -- skills/mf-ship/scripts/conduct.py` prints the line.
- [x] 4.3 In `skills/mf-ship/scripts/conduct.py`, in `_unpushed`, call `_fetch_default(primary, url, default, base, notes)` under `first_read and start`, after `base` is read and before the `cat-file` check that stops with `a person fetches` ([D3](design.md#d3)).
  Verify: `git grep -n -F "_fetch_default(primary, url, default, base, notes)" -- skills/mf-ship/scripts/conduct.py` prints the line.
- [x] 4.4 In `tests/test_conduct.py` add `test_a_start_fetches_and_fast_forwards_the_default`, calling `conduct["_unpushed"](root, first_read=True, start=True, notes=notes)` over a bare `origin` and a clone that pushes: behind with the objects absent and with them held, equal, ahead, and diverged, where the local branch never moves and no merge commit is made; the primary's tree follows a fast-forward; a patched `_remote` that fails a `fetch` raises `Unreachable` and moves nothing ([D3](design.md#d3)).
  Verify: `uv run pytest tests/test_conduct.py -q -k a_start_fetches` passes.
- [x] 4.5 In `tests/test_conduct.py` add `test_a_diverged_default_halts_at_the_push`, marked `slow`: a release merged locally and unpushed, a clone pushes a commit to `origin`, the objects absent, then `_run_claude` ends 1, the log's line before the close is `run · halt — git push origin main failed, exit 1`, and the local `main` is unmoved ([D3](design.md#d3)).
  Verify: `uv run pytest tests/test_conduct.py -q -k a_diverged_default_halts` passes.
- [x] 4.6 In `tests/test_conduct.py` rename `test_a_local_default_behind_origin_passes` to `test_a_local_default_behind_origin_is_brought_up`, drop its manual `git fetch`, and assert after the run that the primary's `main` is `origin`'s, the clone's file is in the tree and the log holds `run · sync — fast-forwarded main to` ([D3](design.md#d3)).
  Verify: `git grep -n "test_a_local_default_behind_origin_is_brought_up" -- tests/test_conduct.py` prints the line.

## 5 — The guard and Codex

- [x] 5.1 In `skills/mf-ship/scripts/conduct.py` change the `CONFIG_PLAIN` line `r"|protocol\.version|pull\.(rebase|ff)"` to end `|gc\.auto"` after `pull\.(rebase|ff)` ([D4](design.md#d4)).
  Verify: `git grep -n -F 'gc\.auto' -- skills/mf-ship/scripts/conduct.py` prints the line.
- [x] 5.2 In `tests/test_conduct.py` rename `test_the_config_guard_refuses_a_gc_key` to `test_the_config_guard_allows_gc_auto`: `gc.auto` in the primary's config makes `_status` exit 0, and `gc.autodetach` makes it exit 1 naming that key ([D4](design.md#d4)).
  Verify: `git grep -n "test_the_config_guard_allows_gc_auto" -- tests/test_conduct.py` prints the line.
- [x] 5.3 In `skills/mf-ship/scripts/conduct.py` add `CHECKERS = tuple(name for name in WORKERS if name != FIXER)` after `WORKERS`, with the comment that these are the stations a missing Codex does not halt ([D5](design.md#d5)).
  Verify: `git grep -n "^CHECKERS" -- skills/mf-ship/scripts/conduct.py` prints the line.
- [x] 5.4 In `skills/mf-ship/scripts/conduct.py`, in `Run.named`, skip a plan entry whose station is in the checkers tuple of 5.3 and whose executor is `codex` while `_executor_missing("codex")`, and skip a shadow whose executor is `codex` under the same test. Its docstring ends `Why: 0132-cloud-run design D5` ([D5](design.md#d5)).
  Verify: `git grep -n -F '_executor_missing("codex")' -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 5.5 In `skills/mf-ship/scripts/conduct.py`, in `Run.codex_ready`, return `False` first when `_executor_missing("codex")`, under the comment `# Not installed: the third cause of a fallback.` ([D5](design.md#d5)).
  Verify: `git grep -n -F "Not installed: the third cause" -- skills/mf-ship/scripts/conduct.py` prints the line.
- [x] 5.6 In `skills/mf-ship/scripts/conduct.py` add `self.codex_said: bool = False` to `Run.__init__`, and at the end of `Run.read_plan`, under `self.guard`, log `run · codex — not on PATH: a checker a plan gives Codex runs on Claude` once, when a station of the checkers tuple of 5.3, of a version just read, has `codex` for its executor while `_executor_missing("codex")` ([D5](design.md#d5)).
  Verify: `git grep -n -F "a checker a plan gives Codex runs on Claude" -- skills/mf-ship/scripts/conduct.py` prints the line.
- [x] 5.7 In `tests/test_conduct.py` add `test_a_checker_on_codex_runs_where_codex_is_missing`, shaped on the `Run` and `read_plan` steps of `test_a_codex_checker_runs_through_run_checker` with `_executor_missing` patched to report only `codex`: `named` leaves `codex` out for a conformance checker, its shadow and none other, keeps it for a build and the fixer, and `codex_ready` is false and probes nothing; the log holds a single `run · codex` line however many plans are read; with Codex present `named` keeps it ([D5](design.md#d5)).
  Verify: `uv run pytest tests/test_conduct.py -q -k a_checker_on_codex_runs_where` passes.
- [x] 5.8 In `tests/test_conduct.py` add `test_a_codex_checker_falls_back_where_codex_is_not_installed`, marked `slow`, shaped on the second half of `test_a_station_runs_on_its_executor`: with `[converge.conformance] executor = "codex"` and Codex missing the run ends 0, the checker runs on Claude and one `run · codex` line says why; with `[build] executor = "codex"` in a second primary the run ends 1 on `probe-codex — codex is not on PATH` ([D5](design.md#d5)).
  Verify: `uv run pytest tests/test_conduct.py -q -k a_codex_checker_falls_back_where` passes.

## 6 — The record

- [x] 6.1 In `docs/decisions.md`, D47, insert before the line ``- **Accepts:** what a command `Ship tools:` names runs, inside the sandbox.`` a bullet that opens `- **A start brings origin in:**` and says that a run's start fetches `origin`'s default branch through the conductor's scratch repo and fast-forwards the local one, never merging, a failure a wait; makes the local tag of each release commit `origin`'s default branch holds that has none, pushing it where the machine pushes tags; and that `gc.auto` joins the keys the config guard allows ([D1](design.md#d1), [D2](design.md#d2), [D3](design.md#d3), [D4](design.md#d4)).
  Verify: `git grep -n -F "A start brings origin in" -- docs/decisions.md` prints the line.
- [x] 6.2 In `docs/decisions.md`, D17, write ``tag, save where the machine's `ship.toml` sets `tags = false`; under `merge=yes`, `conduct.py` pushes. It never forces`` for ``tag; under `merge=yes`, `conduct.py` pushes. It never forces`` ([D1](design.md#d1)).
  Verify: `git grep -n -F "save where the machine's" -- docs/decisions.md` prints the line.
- [x] 6.3 In `docs/decisions.md`, D76, insert before its `- **Rejected:** a wait until any reset` line a bullet that opens `- **Not installed:**` and says that a Codex not on `PATH` is a third cause: a checker a plan gives Codex runs on Claude on converge's model and effort, the run says so once, and a station on Codex still halts at its probe ([D5](design.md#d5)).
  Verify: `git grep -n -F "a third cause" -- docs/decisions.md` prints the line.
- [x] 6.4 In `docs/decisions.md`, D84, insert before its `- **Accepts:** a count that passes the cap after a rejoin` line a bullet that opens `- **Also read:**` and says that `tags` under `[push]` of the same file is read by the same reader at a run's start and by `status`; `false` makes the machine push no tag, a value that is not `true` or `false` stops the run with exit 2, and the tag pushed or not is [D47](#d47--mf-ship-takes-cut-versions-to-the-default-branch-unattended)'s ([D1](design.md#d1)).
  Verify: `git grep -n -F "Also read:" -- docs/decisions.md` prints the line.
- [x] 6.5 In `THREAT_MODEL.md` write ``its local git fetches no missing object, save a run's start, which fetches `origin`'s default branch through that scratch repo into the primary's objects and fast-forwards the local branch, merging nothing.`` for `its local git fetches no missing object.` ([D3](design.md#d3)).
  Verify: `git grep -n -F "save a run's start" -- THREAT_MODEL.md` prints the line.
- [x] 6.6 In `THREAT_MODEL.md` write ``run without Betterleaks does not start. A machine whose `ship.toml` sets `tags = false` pushes no tag; a run's start makes the tag of each release commit `origin`'s default branch holds, and pushes it only where tags are pushed.`` for `run without Betterleaks does not start.` ([D1](design.md#d1), [D2](design.md#d2)).
  Verify: `git grep -n -F "pushes no tag; a run's start makes" -- THREAT_MODEL.md` prints the line.
- [x] 6.7 In `skills/mf-ship/SKILL.md`, the `run --executor <executor> --detach` row, write ``no file means no cap, and a bad one exits 2, naming the file. It reads `tags` under `[push]` there too: `false` makes a run push no tag and halt on none, and a bad value exits 2, naming the file |`` for `no file means no cap, and a bad one exits 2, naming the file |` ([D1](design.md#d1)).
  Verify: `git grep -n -F "makes a run push no tag" -- skills/mf-ship/SKILL.md` prints the line.
- [x] 6.8 In `skills/mf-ship/SKILL.md`, the `status` row, write ``and a merged version tag leaves `run · unread`; with `tags = false` a line `run · tags — this machine pushes none` follows the unpushed names |`` for ``and a merged version tag leaves `run · unread` |`` ([D1](design.md#d1)).
  Verify: `git grep -n -F "this machine pushes none" -- skills/mf-ship/SKILL.md` prints the line.
- [x] 6.9 In `skills/mf-ship/SKILL.md` Step 3, write ``secrets first. A run's start fetches `origin`'s default branch and fast-forwards the local one, never merging, and makes the local tag of each release commit `origin` holds that has none.`` for the line `secrets first.` ([D2](design.md#d2), [D3](design.md#d3)).
  Verify: `git grep -n -F "never merging, and makes the local tag" -- skills/mf-ship/SKILL.md` prints the line.
- [x] 6.10 In `skills/mf-ship/SKILL.md` Step 3, write `while Codex is limited or not installed, a Codex` and, on the next line, `checker runs on Claude, and the start says so once.` for `while Codex is limited, a Codex` and `checker runs on Claude.` ([D5](design.md#d5)).
  Verify: `git grep -n -F "limited or not installed" -- skills/mf-ship/SKILL.md` prints the line.
