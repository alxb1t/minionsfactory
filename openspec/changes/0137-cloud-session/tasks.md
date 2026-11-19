# Cloud session — tasks

The phases: pin `report`, make the worker's commit and git quiet, name the default branch in `report`, add `wait`, add the setup script, write the record, and a person gives the script the digest of `uv`.

## Progress

- [x] 1 — The pin · moderate
- [x] 2 — The worker · moderate
- [x] 3 — The report · moderate
- [x] 4 — The wait · hard
- [x] 5 — The setup · hard
- [x] 6 — The record · moderate
- [ ] 7 — The digest of uv **HUMAN**

## 1 — The pin

- [x] 1.1 In `tests/test_conduct.py`, add `test_report_with_tags_false_reads_not_pushed_today`, built on a bare `origin` as the
  release check's `pushed()` is: `main` and the merge on `origin`, the tag local, `[push]` `tags = false` in `layout.ship_file()`.
  Verify: `uv run pytest tests/test_conduct.py -q -k test_report_with_tags_false_reads_not_pushed_today` passes.

## 2 — The worker

- [x] 2.1 In `worker_settings` of `skills/mf-ship/scripts/conduct.py`, add `"attribution": {"sessionUrl": False}` to the
  returned JSON, per [D2](design.md#d2).
  Verify: `git grep -n -e "sessionUrl" -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.2 In `tests/test_conduct.py`, add that key to the expected dict of `test_a_claude_worker_starts_in_the_sandbox`.
  Verify: `uv run pytest tests/test_conduct.py -q -k test_a_claude_worker_starts_in_the_sandbox` passes.
- [x] 2.3 In `HOOKS_OFF` of `skills/mf-ship/scripts/conduct.py`, set `GIT_CONFIG_COUNT=4` and add `GIT_CONFIG_KEY_2=commit.gpgsign`
  and `GIT_CONFIG_KEY_3=tag.gpgsign`, each value `false`, per [D3](design.md#d3); say so in the comment above it.
  Verify: `git grep -n -F -e "GIT_CONFIG_KEY_3=tag.gpgsign" -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 2.4 In `tests/test_sandboxed.py`, set the literal of `HOOKS_OFF` in `test_the_deny_lists_are_literals` to those keys.
  Verify: `uv run pytest tests/test_sandboxed.py -q -k test_the_deny_lists_are_literals` passes.
- [x] 2.5 In `tests/test_conduct.py`, add `test_a_worker_git_signs_nothing_over_a_host_that_signs`: each executor's `env` prefix,
  run over a host environment holding `commit.gpgsign` true, makes `git config --get` print `false` for both signing keys.
  Verify: `uv run pytest tests/test_conduct.py -q -k test_a_worker_git_signs_nothing_over_a_host_that_signs` passes.
- [x] 2.6 In `tests/test_conduct.py`, add `test_the_conductor_merges_with_no_signing_key`: a spy on the git call of `merge_in`'s
  commit holds no `gpgsign` argument and no `GIT_CONFIG` variable.
  Verify: `uv run pytest tests/test_conduct.py -q -k test_the_conductor_merges_with_no_signing_key` passes.

## 3 — The report

- [x] 3.1 In `skills/mf-ship/scripts/conduct.py`, add `_on_default(primary, merge: str | None) -> bool | None` after `_pushed`, per
  [D4](design.md#d4): `None` with no `origin`; else `False` for no merge or a tip the primary lacks, as that section lists.
  Verify: `git grep -n -e "def _on_default(" -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 3.2 In `report`, ask `_pushes_tags()`; with `tags = false` print `default pushed, tag local`, `default pushed` or
  `not pushed` from `_on_default`, and `no origin` as before.
  Verify: `git grep -n -F -e "default pushed, tag local" -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 3.3 In `tests/test_conduct.py`, rename the pin of 1.1 to `test_report_with_tags_false_names_the_default_branch` and flip it:
  the merge on `origin` reads `default pushed, tag local`; no tag, `default pushed`; the merge off `origin`, `not pushed`.
  Verify: `uv run pytest tests/test_conduct.py -q -k test_report_with_tags_false_names_the_default_branch` passes.
- [x] 3.4 In `tests/test_conduct.py`, add `test_report_with_tags_false_reads_not_pushed_for_a_tip_the_primary_lacks`: `origin`'s
  default branch holds a commit the primary does not, and `report` prints `not pushed` and exits 0.
  Verify: `uv run pytest tests/test_conduct.py -q -k test_report_with_tags_false_reads_not_pushed_for_a_tip_the_primary_lacks` passes.
- [x] 3.5 In `tests/test_conduct.py`, add `test_report_with_a_bad_tags_value_exits_2`: `tags = "no"` makes `report` exit 2.
  Verify: `uv run pytest tests/test_conduct.py -q -k test_report_with_a_bad_tags_value_exits_2` passes.

## 4 — The wait

- [x] 4.1 In `skills/mf-ship/scripts/conduct.py`, add `WAIT_SECONDS = 60` beside `CLAIM_SECONDS` and `wait_run(cwd)`, per
  [D5](design.md#d5): it prints, flushing, and returns 0.
  Verify: `git grep -n -e "^def wait_run(" -e "^WAIT_SECONDS = 60" -- skills/mf-ship/scripts/conduct.py` prints a line for each.
- [x] 4.2 In `main`, call `commands.add_parser("wait", help="block until the live run ends")` and add its branch,
  `return wait_run(cwd)`.
  Verify: `git grep -n -F -e 'add_parser("wait"' -- skills/mf-ship/scripts/conduct.py` prints a line.
- [x] 4.3 In `tests/test_conduct.py`, add `test_wait_with_no_run_exits_0`: it prints `wait: none — no run is live`.
  Verify: `uv run pytest tests/test_conduct.py -q -k test_wait_with_no_run_exits_0` passes.
- [x] 4.4 In `tests/test_conduct.py`, add `test_wait_prints_each_poll_until_the_run_ends`: `_claim` and the sleep are replaced,
  the log gains lines, then none; it prints each poll's `wait: live · +<n> lines`, then `wait: ended` and `status`'s lines.
  Verify: `uv run pytest tests/test_conduct.py -q -k test_wait_prints_each_poll_until_the_run_ends` passes.
- [x] 4.5 In `tests/test_conduct.py`, add `test_wait_ends_on_a_halted_run`: a log ending in a halt and a cleared claim exit 0.
  Verify: `uv run pytest tests/test_conduct.py -q -k test_wait_ends_on_a_halted_run` passes.
- [x] 4.6 In `tests/test_conduct.py`, add `test_wait_reads_no_origin_at_a_poll`: a spy on `_remote` and `_outside` sees no call
  before the last poll.
  Verify: `uv run pytest tests/test_conduct.py -q -k test_wait_reads_no_origin_at_a_poll` passes.

## 5 — The setup

- [x] 5.1 Create `scripts/cloud_setup.py` as [D6](design.md#d6) says: the PEP 723 header, the seed line, the versions `UV`,
  `BETTERLEAKS` and `OPENSPEC`, the URL and digest constants of [D8](design.md#d8) (`UV_SHA256` is `"UNSET"`), `run`, `fetch`.
  Verify: `grep -n -e "^def run(" -e "^def fetch(" -e "^UV_SHA256 = " scripts/cloud_setup.py` prints a line for each.
- [x] 5.2 In `docs/modules.md`, add the row `scripts/cloud_setup.py` · `gate` · `layout.py, platform.py`, and name the script in
  the `gate` layer's line, per [D9](design.md#d9).
  Verify: `git grep -n -e "cloud_setup" -- docs/modules.md` prints a line.
- [x] 5.3 In `scripts/cloud_setup.py`, add `refuse()`, `install_packages()` and `install_tools()`: the refusals, `apt-get` for
  `bubblewrap`, `socat` and `procps`, and the checked download of `uv` and `betterleaks` into `/usr/local/bin`.
  Verify: `grep -n -e "^def refuse(" -e "^def install_packages(" -e "^def install_tools(" scripts/cloud_setup.py` prints a line for each.
- [x] 5.4 In `scripts/cloud_setup.py`, add `install_openspec()`, `make_folder()` and `write_ship_toml()`: `npm` at the version,
  `mf-tmp` under the home, and `ship.toml` at `layout.ship_file()` only where none stands.
  Verify: `grep -n -e "^def install_openspec(" -e "^def make_folder(" -e "^def write_ship_toml(" scripts/cloud_setup.py` prints a line for each.
- [x] 5.5 In `scripts/cloud_setup.py`, add `install_skills()`, `read_back()` and `main()`: `make install-skills` at the clone's
  tag, `platform.has_sandbox()`, and one report ending `cloud_setup: ready`; each step skips what stands.
  Verify: `grep -n -e "^def install_skills(" -e "^def read_back(" -e "^def main(" scripts/cloud_setup.py` prints a line for each.
- [x] 5.6 Create `tests/test_cloud_setup.py` with its fixtures, which replace `run`, `fetch` and the root and OS checks, and
  `test_a_first_run_installs_each_step`.
  Verify: `uv run pytest tests/test_cloud_setup.py -q -k test_a_first_run_installs_each_step` passes.
- [x] 5.7 In it, add `test_a_user_or_os_or_clone_the_script_refuses_runs_no_command`: not root, macOS and a clone at no tag each
  exit 2 with `run` never called.
  Verify: `uv run pytest tests/test_cloud_setup.py -q -k test_a_user_or_os_or_clone_the_script_refuses_runs_no_command` passes.
- [x] 5.8 In it, add `test_a_digest_that_differs_installs_nothing`: the download's hash differs, and the run fails naming the tool.
  Verify: `uv run pytest tests/test_cloud_setup.py -q -k test_a_digest_that_differs_installs_nothing` passes.
- [x] 5.9 In it, add `test_a_second_run_skips_each_step` and `test_a_ship_toml_that_stands_is_kept`.
  Verify: `uv run pytest tests/test_cloud_setup.py -q -k "test_a_second_run_skips_each_step or test_a_ship_toml_that_stands_is_kept"` passes.
- [x] 5.10 In it, add `test_a_sandbox_that_does_not_apply_fails_the_run`: `has_sandbox` false makes exit 1 and the report name it.
  Verify: `uv run pytest tests/test_cloud_setup.py -q -k test_a_sandbox_that_does_not_apply_fails_the_run` passes.
- [x] 5.11 In it, add `test_the_versions_are_the_repositorys`: `UV`, `BETTERLEAKS` and `OPENSPEC`, and the `betterleaks` URL and
  digest, each equal what the file [D6](design.md#d6) names for it holds, read at the test.
  Verify: `uv run pytest tests/test_cloud_setup.py -q -k test_the_versions_are_the_repositorys` passes.

## 6 — The record

- [x] 6.1 In `README.md`, add `## The cloud` before `## This repo's gate`: an environment's setup script clones MinionsFactory at a
  tag and runs `python3 scripts/cloud_setup.py`, on the Limited network with package managers; `TMPDIR` is `<home>/mf-tmp`.
  Verify: `git grep -n -e "cloud_setup" -- README.md` prints a line.
- [x] 6.2 In that section, give the session's prompt, cut, then `conduct.py wait` in the background; say the tag is made and
  pushed by the next run on a machine that pushes tags; and state one line a repository at a time, per [D10](design.md#d10).
  Verify: `git grep -n -F -e "conduct.py wait" -- README.md` prints a line.
- [x] 6.3 In `docs/decisions.md`, add `### D85 · A cloud environment's setup script is a script of this repository` after D84:
  the script, its digests, its refusals and the `mf-tmp` folder; the rejected shell script and start hook.
  Verify: `git grep -n -F -e "### D85 · " -- docs/decisions.md` prints a line.
- [x] 6.4 In `docs/decisions.md`, add `### D86 · One line of MF a repository at a time` after D85, with the reason of
  [D10](design.md#d10).
  Verify: `git grep -n -F -e "### D86 · " -- docs/decisions.md` prints a line.
- [x] 6.5 In `docs/decisions.md`, add D85 and D86 to the Repo conventions list of the group map at the top, so it ends
  `D76, D84, D85, D86`.
  Verify: `git grep -n -F -e "D76, D84, D85, D86" -- docs/decisions.md` prints a line.
- [x] 6.6 In `docs/decisions.md`, amend D21: a worker's commit under a run holds no `Claude-Session:` line, the run setting
  `attribution.sessionUrl` false.
  Verify: `git grep -n -e "sessionUrl" -- docs/decisions.md` prints a line.
- [x] 6.7 In `docs/decisions.md`, amend D17: the release commit, its tag and the merge are a worker's and unsigned; the
  conductor's own merges are signed where the machine signs.
  Verify: `git grep -n -F -e "signed where the machine signs" -- docs/decisions.md` prints a line.
- [x] 6.8 In `THREAT_MODEL.md`, add to the entry points `scripts/cloud_setup.py`, which a cloud environment runs as root: each
  download is held to a digest of the repository, and the signer signs the conductor's merges.
  Verify: `git grep -n -e "cloud_setup" -- THREAT_MODEL.md` prints a line.
- [x] 6.9 In `skills/mf-ship/SKILL.md`, add the `wait` row to the command table: what it prints, `wait: live · +<n> lines`,
  `wait: ended` and `status`'s lines, and its exit 0.
  Verify: `git grep -n -F -e "wait: live" -- skills/mf-ship/SKILL.md` prints a line.
- [x] 6.10 In the same table, add to the `report` row the words `default pushed, tag local` and `default pushed` for `tags = false`.
  Verify: `git grep -n -F -e "default pushed" -- skills/mf-ship/SKILL.md` prints a line.

## 7 — The digest of uv

- [ ] 7.1 Run `curl -fsSL https://github.com/astral-sh/uv/releases/download/0.12.19/uv-x86_64-unknown-linux-gnu.tar.gz.sha256`.
  In `scripts/cloud_setup.py` add the digest it prints in place of the `UV_SHA256 = "UNSET"`, as [D8](design.md#d8) says.
  Verify: `grep -c -F -e 'UV_SHA256 = "UNSET"' scripts/cloud_setup.py` prints `0`.
