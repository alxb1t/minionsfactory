## ADDED Requirements

### Requirement: A worker's commit names no session

`conduct.py` SHALL start each Claude worker with `attribution.sessionUrl` set to `false` in its `--settings`, so that a commit the worker makes holds no `Claude-Session:` line. The trailer block of a worker's commit SHALL stay `Co-Authored-By:` and `Change:`.

#### Scenario: A Claude worker's settings
- **WHEN** `conduct.py` builds a Claude worker's command line
- **THEN** its `--settings` JSON holds `attribution` with `sessionUrl` `false`
- **AND** its other keys are as they were

### Requirement: A worker's git signs nothing

`conduct.py` SHALL give the git of each worker, Claude's and Codex's, and of each command it runs under the OS sandbox, the keys `commit.gpgsign` and `tag.gpgsign` as `false` through git's config variables in the environment, beside the two keys it gives for hooks, over any value of those variables the host's environment holds. It SHALL tell its own git, the merges and tags it makes outside a sandbox, nothing on signing, so that a machine's signer signs them.

#### Scenario: A host that signs
- **WHEN** the environment holds `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=commit.gpgsign` and `GIT_CONFIG_VALUE_0=true`, and a worker's command line is run with `git config`
- **THEN** `git config --get commit.gpgsign` and `git config --get tag.gpgsign` each print `false`
- **AND** `core.hooksPath` and `core.fsmonitor` read as before

#### Scenario: The conductor's own merge
- **WHEN** the conductor makes an integrate or stack merge commit
- **THEN** its git call names no signing key and sets no config variable

### Requirement: `report` names the default branch where a machine pushes no tag

With `tags` `false` under `[push]` in `ship.toml`, `conduct.py report` SHALL read `origin`'s default branch alone, and print for each version `default pushed, tag local` when that branch holds the version's merge and a tag stands, `default pushed` when it holds the merge and no tag stands, and `not pushed` when it does not or `origin` cannot be read. With no `origin` it SHALL print `no origin`. With tags pushed it SHALL print `pushed`, `not pushed` or `no origin` by the tag, as before. A value of `tags` that is neither `true` nor `false`, and a file that cannot be read, SHALL stop `report` with exit 2, naming the file.

#### Scenario: The merge is on origin's default branch
- **WHEN** `tags` is `false`, the tag is local only, and `origin`'s default branch holds the version's merge
- **THEN** the version's line reads `default pushed, tag local`

#### Scenario: The merge is not on origin
- **WHEN** `tags` is `false` and `origin`'s default branch lacks the version's merge
- **THEN** the version's line reads `not pushed`

#### Scenario: Tags are pushed
- **WHEN** `ship.toml` holds no `tags`, or `true`, and `origin` lists the tag on the version's tip
- **THEN** the version's line reads `pushed`

#### Scenario: A bad value
- **WHEN** `tags` is a string
- **THEN** `report` exits 2, naming `ship.toml`

### Requirement: `conduct.py wait` blocks until the run ends

`conduct.py wait` SHALL print `wait: none — no run is live` and exit 0 when no claim is live. With a live claim it SHALL poll the claim every `WAIT_SECONDS` seconds, make no read of `origin` at a poll, and print at each poll the lines the newest run log gained since the wait began or the previous poll, then `wait: live · +<n> lines`, `<n>` the lines it just printed, 0 for none. When the claim is gone or stale it SHALL print `wait: ended` and `status`'s lines, and exit 0, whatever the run's close: a run that halted ends the wait as a run that is done does.

#### Scenario: No run
- **WHEN** no run is live
- **THEN** `wait` prints `wait: none — no run is live` and exits 0

#### Scenario: A run that ends
- **WHEN** a run is live at the first poll, its log gains two lines, and its claim is gone at the next
- **THEN** `wait` prints the two lines, `wait: live · +2 lines`, then `wait: ended` and `status`'s lines, and exits 0

#### Scenario: A run that halts
- **WHEN** a run's log ends in a halt and its claim is gone
- **THEN** `wait` prints `wait: ended` and `status`'s lines, and exits 0

#### Scenario: A poll with no new line
- **WHEN** the run's log gains nothing between two polls
- **THEN** `wait` prints `wait: live · +0 lines` at the second

#### Scenario: A poll reads no origin
- **WHEN** `wait` polls a live run
- **THEN** no remote git call is made until the one `status` makes at the end

### Requirement: A cloud environment's setup script makes a Linux machine ready

`scripts/cloud_setup.py`, run as root by `python3` on Linux, SHALL: install `bubblewrap`, `socat` and `procps` by `apt-get` where `dpkg` does not hold them; install `uv` and `betterleaks` at the versions the repository names, each download checked against the SHA-256 the script holds, a mismatch installing nothing; install `openspec` at its version by `npm`; make the folder `mf-tmp` under the home folder; write `ship.toml` with `tags = false` under `[push]` where no file stands; run `make install-skills` at the tag the clone stands on; read back that the OS sandbox applies; and print one report. It SHALL refuse, with exit 2, where the OS is not Linux, the user is not root or the clone stands on no tag. It SHALL run every command through one function, and a second run SHALL skip each step whose result stands.

#### Scenario: A first run as root on Linux
- **WHEN** the script runs as root on Linux in a clone at a tag, with no tool installed
- **THEN** it installs each package and tool, makes `mf-tmp`, writes `ship.toml`, runs the install at the tag and prints one report ending `cloud_setup: ready`

#### Scenario: Another user, or another OS
- **WHEN** the script runs as a user that is not root, or on macOS
- **THEN** it runs no command, and exits 2 naming the reason

#### Scenario: A download whose digest differs
- **WHEN** a download's SHA-256 differs from the one the script holds
- **THEN** nothing is installed from it and the script exits 1 naming the tool

#### Scenario: A second run
- **WHEN** the script runs again on the machine it made ready
- **THEN** it runs no install, and its report says each step stands

#### Scenario: A `ship.toml` that stands
- **WHEN** `ship.toml` already exists
- **THEN** the script leaves it as it is

#### Scenario: The sandbox does not apply
- **WHEN** the read-back finds that the OS sandbox does not apply
- **THEN** the report names it and the script exits 1
