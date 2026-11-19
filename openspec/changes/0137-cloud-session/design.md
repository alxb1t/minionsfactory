# Cloud session — design

A cloud session ships a version when its workers' commits name no session and sign nothing, `report` says what reached `origin`, `wait` keeps the VM up, and one script sets the machine up. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Probe 4 ran cut, build, converge and release in a cloud VM and pushed `main`. What it left is the list below; the facts are read at `727e41ed`.

```
worker settings   skills/mf-ship/scripts/conduct.py  worker_settings  no `attribution` key
worker git        skills/mf-ship/scripts/conduct.py  HOOKS_OFF        hooks and fsmonitor, nothing on signing
report            skills/mf-ship/scripts/conduct.py  report           push word from the tag alone
subcommands       skills/mf-ship/scripts/conduct.py  main             none waits for a run
setup             the probe's setup.sh, outside this repository
```

- A worker's commit carries `Claude-Session: <url>`, the operator's session, into pushed history.
- The cloud's global config signs through a loopback service a worker's sandbox refuses. The setup turns `commit.gpgsign` off for the whole machine, so the conductor's own merges, made outside a sandbox, go unsigned too.
- The proxy refuses a tag push, so with `tags = false` the release is on `origin` and `report` reads `not pushed`.
- A VM pauses after a few idle minutes. The harness refuses a foreground `sleep`, so the session polls from a background command, and only output at each poll is known to keep the VM up.
- The queue cap stays 1. This version is queued beside `0136-status-log` and runs when it ends.

## Goals / Non-Goals

Goals:

- A worker's commit holds no session link; a worker signs nothing; the conductor's merges are signed where the machine signs.
- `report` names what `origin` holds when no tag is pushed.
- A session starts a run, then waits on it with one command.
- One script in this repository sets a cloud VM up, and the README says how to use it.

Non-Goals:

- The out list of [proposal](proposal.md#not-in-this-change).
- The release commit, its tag and the release merge stay unsigned: they are a worker's, made in its sandbox.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The parts: the workers' git and attribution, `report`'s words, `wait`, the setup script | probe 4's list of what is left | the record home, a second line, a conductor-made release merge, `UV_NATIVE_TLS` |
| [D2](#d2) | Each Claude worker's settings hold `attribution.sessionUrl` false | the line names the operator's session in pushed history; the documented switch | stripping the line after the commit; `attribution.commit` |
| [D3](#d3) | `HOOKS_OFF` gains `commit.gpgsign` and `tag.gpgsign`, false | a worker's sandbox cannot reach the signer; the conductor's own git stays as it is | a signing key in each worker's `.git/config`; a global config the setup edits |
| [D4](#d4) | With `tags = false` `report` reads `origin`'s default branch for the merge | `not pushed` reads as a failure when `main` is on `origin` | naming the tag only; a new word for every case |
| [D5](#d5) | `conduct.py wait` blocks until the run ends, a line at every poll, no read of `origin` | only output at each poll keeps a VM up; `status` costs a network read a call | a foreground `sleep`; polling `status` |
| [D6](#d6) | The setup is `scripts/cloud_setup.py`, standard library alone, every command through one function | the gate asks every changed line covered, which a shell script escapes | a shell script; a session start hook in a target |
| [D7](#d7) | The script makes `mf-tmp` under the home; the README has the operator set `TMPDIR` to it | the conductor stops where `TMPDIR` is in a repository; probe 4 ran with it outside `/tmp` | trusting `/tmp`, unproven for a whole run |
| [D8](#d8) | `betterleaks`'s URL and digest are CI's; `uv`'s digest is a last phase, for a person | CI already holds the first; a worker's network reaches no GitHub host | a placeholder digest shipped; a digest a worker invents |
| [D9](#d9) | `scripts/cloud_setup.py` takes the layer `gate` in `docs/modules.md` | D83 of `docs/decisions.md` rejects a layer table beyond the map's | a sixth layer |
| [D10](#d10) | One line a repository at a time, across machines, stated in the README and a decision | change numbers and tags come from local state, and `origin` is fetched at a start alone | building the two-line case |
| [D11](#d11) | The proof is probe 5, after the release: a cloud session on the shipped script | no test on the MacBook runs the script for real | a test with a fake VM |

### D1

**The version is these parts and no more.** The workers' git and attribution ([D2](#d2), [D3](#d3)), `report`'s words ([D4](#d4)), `wait` ([D5](#d5)) and the setup script ([D6](#d6) to [D8](#d8)). The record home, a second line of MF on one repository, a release merge made by the conductor and `UV_NATIVE_TLS` each need a design of their own.

### D2

**`worker_settings` adds `"attribution": {"sessionUrl": False}` to the JSON it returns.** A Codex worker has no settings JSON and needs none. The trailer block `Co-Authored-By:` and `Change:` is asked for in the skills' prose and is not touched.

### D3

**`HOOKS_OFF` gains `commit.gpgsign` and `tag.gpgsign`.** `GIT_CONFIG_COUNT=4`, then `KEY_2=commit.gpgsign`, `KEY_3=tag.gpgsign`, each value `false`. The tuple is read by the Claude worker's command line, the Codex worker's and `sandboxed()`. Each takes the keys; no command run under the OS sandbox can sign anyway.

- The count is set, so a host that holds `GIT_CONFIG_COUNT` and keys of its own has its keys 0 to 3 replaced and its later keys ignored.
- The conductor's own git keeps `NO_HOOKS` and `SCRATCH_IDENTITY`. Its integrate and stack merges are signed where the machine's global config signs, as probe 4 showed outside a sandbox.
- The config guard reads the repository's own keys, and an environment variable is no key of the repository: it is untouched.

### D4

**`report` asks `_pushes_tags()`, as `status` does.** With tags pushed the push word is as today. With `tags = false` it asks a new helper whether `origin`'s default branch holds the version's merge, and prints:

```
no origin                   no remote
default pushed, tag local   the merge is on origin's default branch, a tag stands
default pushed              the merge is on it, no tag stands
not pushed                  it is not, or origin cannot be read
```

The helper is `_on_default(primary, merge: str | None) -> bool | None`:

- It returns `None` with no `origin`, as `_pushed` does.
- It reads the branch's tip by one `ls-remote` through `_remote`, as `_pushed` reads the tag, and tests the merge with `_history_ancestor`.
- It returns `False` for no merge, no kept URL, an unreadable `origin` and a tip the primary lacks. It finds the last with `cat-file -e` first, because `merge-base` stops with exit 2 on an unknown object.

A bad `tags` value exits 2 in `report`, as it does in `status`.

### D5

**`wait(cwd)` is a loop over `_claim`.** It prints and returns 0.

```
claim not live at the start  ──▶  wait: none — no run is live
live  ──▶  every WAIT_SECONDS: new lines of last_log, then wait: live · +<n> lines
not live (gone or stale)  ──▶  wait: ended, then status(cwd), exit 0
```

- The offset is the newest log's size when the wait begins; a poll prints the lines past it. A newer log than the one it holds is read from its start.
- A poll reads the claim and the log, and no `origin`. Only the end's `status` does.
- Every print flushes: the session reads a pipe.
- `WAIT_SECONDS` is 60.

### D6

**The script is a module of functions behind one runner.** `run(argv)` is the one function that starts a command, and a test replaces it. `fetch(url)` is the one download, and a test replaces it. The script has the PEP 723 header the standards ask for, and the VM's `python3` runs it.

| step | does | skipped when |
|---|---|---|
| refuse | stop, exit code 2, unless Linux, root and a clone at a tag | never |
| packages | `apt-get install -y bubblewrap socat procps` | `dpkg -s` holds each |
| `uv`, `betterleaks` | `fetch`, check the SHA-256 constant of each, unpack to `/usr/local/bin` | the tool prints its version |
| `openspec` | `npm install -g @fission-ai/openspec@<version>` | `openspec --version` prints it |
| folder | `mf-tmp` under the home | it stands |
| `ship.toml` | `tags = false` under `[push]`, at `layout.ship_file()` | the file stands |
| install | `make install-skills TAG=<tag>` | `layout.data_dir() / <tag>` stands |
| read-back | `platform.has_sandbox()`; the report's last line `cloud_setup: ready` or the failure | never |

The tag is `git describe --tags --exact-match` of the clone. The versions are constants of the script. A case reads the lowest `uv` from `pyproject.toml`, `uv` and the `betterleaks` tarball URL and digest from `.github/workflows/ci.yml`, and `betterleaks` and `openspec` from `AGENTS.md`, and fails where one differs. The script names no OS command of the structure rule's list, and no `.minions/` or home-folder name outside `layout.py`.

`fetch(url)` opens the URL with `urllib.request.urlopen` after it checks the scheme is `https`, and returns the bytes. Its one `noqa: S310` carries a `# why:` line. The apt step lists the packages of the table above and no more: a VM that lacks `make` fails the install step, the report names it, and the fifth probe reads it.

### D7

**The folder is `mf-tmp` under the home.** The README has the operator set `TMPDIR` to its path in the environment's variables, which the setup script cannot read: they are not set while it runs.

### D8

**`betterleaks`'s URL and digest are the CI workflow's own; `uv`'s digest is a person's.** `BETTERLEAKS_URL` is `https://github.com/betterleaks/betterleaks/releases/download/v1.9.0/betterleaks_1.9.0_linux_x64.tar.gz` and `BETTERLEAKS_SHA256` is `f8b185a39ffcece2a1ca82bf3a4e7435cd81963ffd16b7a9128daf75f35f6de7`, as the install step of the workflow holds them; a case ties both to it. `UV_URL` is the `uv` release asset `uv-x86_64-unknown-linux-gnu.tar.gz` at the version, and `UV_SHA256` holds `UNSET` until the last phase: a digest of `UNSET` equals no hash, so the script fails closed before it. The last phase is a person's, who prints the digest from the release's own `.sha256` asset; the release waits on it.

### D9

**The map row is `scripts/cloud_setup.py` · `gate` · `layout.py, platform.py`.** The `gate` line of `docs/modules.md` then reads "the scripts `make gate` and `make corpus` run, and the setup script a cloud environment runs".

### D10

**The rule: one line of MF a repository at a time.** A second machine cuts the same number, and a cloud machine's tags never reach `origin`. The README states it; the decision records why. Nothing is built.

### D11

**The fifth probe proves it.** The plan prepares a cloud environment whose setup script is the shipped one, and the person starts the session. It is no task of this change.

## Tests

Each test sits at the lowest layer that can fail for it (T1); all are unit tests, and none is a browser's.

| layer | added | edited |
|---|---|---|
| unit, `tests/test_conduct.py` | the report pin and its flip, the signing test, the conductor's merge test, the wait tests, a bad-`tags` test | `test_a_claude_worker_starts_in_the_sandbox` |
| unit, `tests/test_sandboxed.py` | none | `test_the_deny_lists_are_literals` |
| unit, `tests/test_cloud_setup.py`, new | a test per case of the spec's setup requirement, and the versions test | none |
| end-to-end | none: 0 tests, on 0 engines | none |

- The report tests use a real bare `origin`, as the existing report check does: git's own answer is the point (T1).
- The wait tests replace `_claim` and the sleep, so none waits (T2: no existing test reaches a live run).
- The count is `uv run pytest tests/test_conduct.py tests/test_sandboxed.py tests/test_cloud_setup.py --collect-only -q`, before and after the build.
- Removed or merged tests: none, so the table of `I16` is empty.

## Dependencies

None.

## Risks / Trade-offs

- **No package joins the lock.** The tools the script installs, `uv`, `betterleaks` and `openspec`, are the operator's tooling at the versions `AGENTS.md` and `pyproject.toml` name, per the OpenSpec decision and D52 of `docs/decisions.md`.

- **A release before phase 7** would ship a script that refuses to install. The phase is last and the release checks every box.
- **`uv`'s digest is copied by a person** from the release's `.sha256` asset. A wrong one fails the check, closed. The `.sha256` asset sits beside the tarball, so its fetch proves `UV_URL` as well.
- **The cloud image may restrict user namespaces.** CI sets the AppArmor switch for `bwrap`; the script sets none, as probe 4's VM needed none. A VM that does restrict fails the read-back, and the report names it.
- **`sandboxed()` commands take the signing keys too.** A `Verify:` that commits in a fixture is told not to sign, which it did not need. Accepted.
- **The release commit and merge stay unsigned**, as probe 4 left them, until the release's steps are scripts.
- **A clone at no tag is refused.** A setup script that clones the default branch gets exit 2 and a message; the README says to clone at a tag.

## Verdict

Ready to build. Each phase but the last is a worker's; the last is the person's and closes the change.
