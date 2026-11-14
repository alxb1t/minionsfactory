# Linux CI green — tasks

A phase for each cause: the replay's identity, make's inherited variables, and the `sleep` tests. Decisions are in [design](design.md).

## Progress

- [x] 1 — The replay's identity · moderate
- [ ] 2 — Make's variables · moderate
- [ ] 3 — The sleep tests · moderate

## 1 — The replay's identity

- [x] 1.1 In `tests/conftest.py`, have `isolated_home` write `[user]` and `useConfigOnly = true` into `home / ".gitconfig"` ([D3](design.md#d3)). In `tests/test_guardrails.py`, have `test_the_isolation_fixture_holds_home_under_tmp_path` assert that `git config --global --get user.useConfigOnly` prints `true`.
  Verify: `uv run pytest tests/test_guardrails.py -q` exits 0.
- [x] 1.2 **HALT CHECK** With the fixture set and `integrate.py` unchanged, the replay tests fail on git's identity error. A pass means the identity is not the cause: stop.
  Verify: `uv run pytest tests/test_integrate.py -q -k replay` exits 1.
- [x] 1.3 In `skills/mf-integrate/scripts/integrate.py`, add `SCRATCH_IDENTITY` after `NO_HOOKS`, as `conduct.py` holds it, with `user.name=mf-integrate`, `user.email=mf-integrate@example.invalid` and `commit.gpgsign=false` ([D1](design.md#d1)). In `replay`, put `*SCRATCH_IDENTITY` before `"-c", "rerere.enabled=false"`.
  Verify: `uv run pytest tests/test_integrate.py -q` exits 0.

## 2 — Make's variables

- [ ] 2.1 In `skills/mf-converge/scripts/gate_run.py`, add `CLEARED = ("MAKEFLAGS", "MFLAGS", "MAKELEVEL")` and `_dry_env()`, which returns `_make_env()` without those keys. `dry_run` runs `make -n gate` under `_dry_env()`; the gate run in `gate` keeps `_make_env()` ([D2](design.md#d2)).
  Verify: `git grep -n "_dry_env" -- skills/mf-converge/scripts/gate_run.py` prints the definition and its use in `dry_run`.
- [ ] 2.2 In `tests/test_gate_run.py`, add `test_a_record_holds_under_inherited_make_flags`: it sets `MAKEFLAGS` to `w`, runs `_gate` on a green repo made by `_repo`, removes `MAKEFLAGS`, runs `_gate` again, and asserts the second output starts with `gate: reused — `.
  Verify: `uv run pytest tests/test_gate_run.py -q -k test_a_record_holds_under_inherited_make_flags` exits 0.
- [ ] 2.3 In `skills/mf-cut-change/scripts/cut_pre.py`, add `CLEARED` as in 2.1, give `_tool` an optional `env` that it passes to `subprocess.run`, and have `check_gate` pass the environment without those keys ([D2](design.md#d2)).
  Verify: `git grep -n "CLEARED" -- skills/mf-cut-change/scripts/cut_pre.py` prints the tuple and its use in `check_gate`.
- [ ] 2.4 In `tests/test_cut_pre.py`, add `test_an_empty_gate_halts_under_inherited_make_flags`: it sets `MAKEFLAGS` to `w`, builds `_repo(tmp_path, gate="gate:\n")`, and asserts `_run` prints `cut_pre: halt — gate: ` with the line `` `make -n gate` prints no command: the recipe is empty ``.
  Verify: `uv run pytest tests/test_cut_pre.py -q -k test_an_empty_gate_halts_under_inherited_make_flags` exits 0.

## 3 — The sleep tests

- [ ] 3.1 In `test_stop_ends_a_live_run` in `tests/test_conduct.py`, delete `sleep = shutil.which("sleep")`, its `assert sleep` and `executor.symlink_to(sleep)`. Start `worker` as `subprocess.Popen(["sleep", "60"], start_new_session=True)`. Keep `executor = tmp_path / "claude"` for `_register` ([D4](design.md#d4)).
  Verify: `uv run pytest tests/test_conduct.py -q -k test_stop_ends_a_live_run` exits 0.
- [ ] 3.2 In `test_a_stale_claim_is_cleared`, do the same: delete the `sleep` lookup, its assert and the link, and start `group`, `recycled`, `unstamped`, `sibling` and `refusing` as `subprocess.Popen(["sleep", "60"], start_new_session=True)`. Keep `executor` as the registered `comm`.
  Verify: `uv run pytest tests/test_conduct.py -q -k test_a_stale_claim_is_cleared` exits 0.
- [ ] 3.3 Check that no test of `tests/test_conduct.py` links to the machine's `sleep`.
  Verify: `git grep -n "symlink_to(sleep)" -- tests/test_conduct.py` prints nothing and exits 1.
