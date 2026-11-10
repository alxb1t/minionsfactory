# Sandbox tmp — tasks

Build the settled [design](design.md), one phase at a time; each test step goes red before its code. `C` is
`skills/mf-ship/scripts/conduct.py`, `K` is `tests/conftest.py`, `G` is `tests/test_guardrails.py`, `S` is
`tests/test_sandboxed.py`, `X` is `tests/test_conduct.py`. Inside a phase a sub-task's `Verify:` is its own; only the phase's end is green.

## Progress

- [x] 1 — The tests stop depending on where tmp lies · moderate
- [x] 2 — `sandboxed()` gives each command its own `TMPDIR` · hard
- [x] 3 — A Codex worker's own `TMPDIR`, the shell rules and the release text · hard
- [x] 4 — The planted-key scan reads only the folder it scans · moderate

## 1 — The tests stop depending on where tmp lies

- [x] 1.1 **HALT CHECK** The base stands as the design's [Context](design.md#context) reads it.
  Verify: `git grep -n -e '^def isolated_home(' -e '^def test_betterleaks_finds_a_planted_key(' -- tests/conftest.py tests/test_guardrails.py` prints a line for each.
- [x] 1.2 Make `.minions/tmp`: inside the repository, ignored by it, the folder the pinned `sandboxed()` names as a converge gate's `TMPDIR` in the primary ([F1](design.md#context)). Run `mkdir -p .minions/tmp`.
  Verify: `ls -d .minions/tmp` prints `.minions/tmp`.
- [x] 1.3 In `G` extend `test_the_isolation_fixture_holds_home_under_tmp_path`: `GIT_CEILING_DIRECTORIES` equals `str(tmp_path.parent)`, per [D1](design.md#d1).
  Verify: `git grep -n 'GIT_CEILING_DIRECTORIES' -- tests/test_guardrails.py` prints a line.
- [x] 1.4 In `K`'s `isolated_home` take `tmp_path_factory: pytest.TempPathFactory` and set `GIT_CEILING_DIRECTORIES` to `str(tmp_path_factory.getbasetemp())`, a `# Why: 0111-sandbox-tmp design D1` comment above it.
  Verify: `uv run pytest -q tests/test_guardrails.py -k isolation_fixture` exits 0.
- [x] 1.5 In `test_betterleaks_finds_a_planted_key` run `subprocess.run(["git", "init", "-q", str(scanned)], check=True)` after `scanned.mkdir()`, so the scanned folder is its own repository.
  Verify: `git grep -n -F -e '"git", "init", "-q", str(scanned)' -- tests/test_guardrails.py` prints a line.
- [x] 1.6 Run the acceptance's tests of the read-or-write cases and the planted key at pytest's default base temp: a build's sandbox refuses git's writes of `.git/hooks` and `.gitconfig` inside the repository, so converge's gate, under the pinned `sandboxed()`, runs them with `TMPDIR` inside the primary ([F7](design.md#context)).
  Verify: `uv run pytest -q tests/test_corpus.py tests/test_facts.py tests/test_plan_check.py tests/test_skip_stub.py tests/test_verify_check.py tests/test_next_tag.py tests/test_pin.py tests/test_guardrails.py` exits 0.

## 2 — `sandboxed()` gives each command its own `TMPDIR`

- [x] 2.1 **HALT CHECK** The base stands as the design's [Context](design.md#context) reads it.
  Verify: `git grep -n -e '^def sandboxed(' -e '^def _profile(' -e '^def _folder_fd(' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 2.2 In `K`'s `isolated_home` also set `TMPDIR` to `str(tmp_path_factory.mktemp("tmp"))`, per [D4](design.md#d4); extend the same `G` test: `TMPDIR` names a folder under `tmp_path.parent` and not under `tmp_path`.
  Verify: `git grep -n -F -e 'mktemp("tmp")' -- tests/conftest.py` prints a line.
- [x] 2.3 In `S` add `test_a_command_gets_a_fresh_tmpdir_outside_every_repository` and `test_a_tmpdir_in_a_repository_runs_nothing`, on `fake_sandbox_exec`, as [the Tests table](design.md#tests) says.
  Verify: `git grep -n -e 'def test_a_command_gets_a_fresh_tmpdir_outside_every_repository' -e 'def test_a_tmpdir_in_a_repository_runs_nothing' -- tests/test_sandboxed.py` prints a line for each.
- [x] 2.4 In `S` extend the scrubbed-environment test, `test_the_command_runs_a_command_in_the_cwd` and `test_a_write_outside_the_trees_is_denied` as the table says; the profile assertions build `_profile([*trees, Path(env["TMPDIR"])], …)`.
  Verify: `git grep -n -F -e '[*trees, Path(env["TMPDIR"])]' -- tests/test_sandboxed.py` prints a line.
- [x] 2.5 In `X` extend `test_the_run_hands_converge_its_trees_and_sandbox`: its command prints `os.environ["TMPDIR"]` after the cwd, and the profile it reads is `_profile` of the trees and that folder.
  Verify: `git grep -n -F -e 'os.environ["TMPDIR"]' -- tests/test_conduct.py` prints a line.
- [x] 2.6 Add `_temp_folder(prefix)` to `C` before `_profile`, as [D2](design.md#d2) says: `dir=os.environ.get("TMPDIR") or "/tmp"`, and both stops of the design, each exit 2.
  Verify: `git grep -n '^def _temp_folder(' -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.7 In `sandboxed()` keep the link guard as `_folder_fd(trees[0], ".minions")`; after it make `_temp_folder("mf-sandbox-")`, write it in the profile's trees, set `TMPDIR` to it and remove it in a `finally` around the spawn, per [D3](design.md#d3); add `0111-sandbox-tmp design D3` to its `Why:`.
  Verify: `uv run pytest -q tests/test_sandboxed.py` exits 0.

## 3 — A Codex worker's own `TMPDIR`, the shell rules and the release text

- [x] 3.1 **HALT CHECK** The base stands as the design's [Context](design.md#context) reads it.
  Verify: `git grep -n -e '^def argv(' -e '^def _unswapped(' -e '^def agent(' -e '^SHELL_RULES = ' -e '^    def worker(' -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 3.2 In `X` add `test_a_codex_worker_gets_its_own_temporary_folder` and `test_a_codex_temp_folder_is_removed` as [the Tests table](design.md#tests) says.
  Verify: `git grep -n -e 'def test_a_codex_worker_gets_its_own_temporary_folder' -e 'def test_a_codex_temp_folder_is_removed' -- tests/test_conduct.py` prints a line for each.
- [x] 3.3 In `X` move the Codex assertions of the executor loop at `:9929`, the argv blocks at `:10662` and `:10745`, the cutter block at `:10793` and the root lists at `:10856` and `:10903` to the folder and `TMPPREFIX` of [D5](design.md#d5), read in the env order of 3.4, the lists compared up to the last root; `test_a_worker_carries_the_allowlist_and_a_denial_is_named` also asserts `here-document` in the rules.
  Verify: `git grep -n 'here-document' -- tests/test_conduct.py` prints a line.
- [x] 3.4 In `argv()` make `_temp_folder("mf-codex-")` for a Codex worker after `_unswapped`, as [D5](design.md#d5) says: last writable root, the env prefix `cache`, `TMPDIR=<folder>`, `TMPPREFIX=<folder>/zsh`, then `PATH`, the comment above `exclude_tmpdir_env_var` rewritten; `.minions/tmp` stays in the Claude branch, and `_fresh_tmp`'s docstring names the Claude workers' `TMPDIR`.
  Verify: `git grep -n 'mf-codex-' -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 3.5 Add `_temp_of` and `_temp_gone` to `C` after `argv()`, per [D6](design.md#d6); in `Run.worker` and `agent` call `_temp_gone(command)` in a `finally` around `work()`.
  Verify: `uv run pytest -q tests/test_conduct.py -k "codex_worker_gets_its_own or codex_temp_folder"` exits 0.
- [x] 3.6 In `SHELL_RULES` insert ` no here-document (<<): write a file with your editing tool;` after `use its output literally;`, per [D7](design.md#d7); its last words stay.
  Verify: `uv run pytest -q tests/test_conduct.py -k worker_carries_the_allowlist` exits 0.
- [x] 3.7 In `skills/mf-release/SKILL.md` replace lines 175-176 per [D8](design.md#d8): `.minions/tmp/` on Claude, a fresh folder outside every repository on Codex.
  Verify: `git grep -n 'outside every repository' -- skills/mf-release/SKILL.md` prints a line.
- [x] 3.8 Run the brief's acceptance tests at pytest's default base temp, as 1.6 does.
  Verify: `uv run pytest -q tests/test_sandboxed.py tests/test_corpus.py tests/test_facts.py tests/test_plan_check.py tests/test_skip_stub.py tests/test_verify_check.py tests/test_next_tag.py tests/test_pin.py tests/test_guardrails.py` exits 0.

## 4 — The planted-key scan reads only the folder it scans

- [x] 4.1 **HALT CHECK** The planted-key test scans the absolute `str(scanned)` with the gate's own config, as converge's round-1 gate ran it.
  Verify: `git grep -n -F -e '"dir", str(scanned)' -e 'str(_REPO / ".betterleaks.toml")' -- tests/test_guardrails.py` prints a line for each.
- [x] 4.2 In `G`'s `test_betterleaks_finds_a_planted_key` make `scanned` `tmp_path / ".minions" / "scanned"`, made with `parents=True`, a `# Why: 0111-sandbox-tmp design D9` comment above it, per [D9](design.md#d9): the test now fails at pytest's default base temp as converge's gate failed it with `tmp_path` under the primary's `.minions/tmp`.
  Verify: `uv run pytest -q tests/test_guardrails.py -k planted_key` exits 1, its output reading `scanned ~0 bytes`.
- [x] 4.3 In the same test run the scan with `cwd=scanned` on `"."` in place of `str(scanned)`, the gate's own `betterleaks dir .`, `--config` and `--report-path` still absolute, per [D9](design.md#d9).
  Verify: `uv run pytest -q tests/test_guardrails.py -k planted_key` exits 0.
- [x] 4.4 Run the brief's acceptance tests at pytest's default base temp, as 3.8 does.
  Verify: `uv run pytest -q tests/test_sandboxed.py tests/test_corpus.py tests/test_facts.py tests/test_plan_check.py tests/test_skip_stub.py tests/test_verify_check.py tests/test_next_tag.py tests/test_pin.py tests/test_guardrails.py` exits 0.
