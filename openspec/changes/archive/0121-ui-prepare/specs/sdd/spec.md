## MODIFIED Requirements

### Requirement: A queued cut prefetches the packages it approves

`conduct.py cut`, after it reads the brief's `## Dependencies` and before it reserves a number, SHALL fetch each Python package the
brief approves for the slug into `.minions/uv-cache`, wheels only, from PyPI's hosts only, so the sandboxed gate's offline
`uv sync --locked` finds it. It SHALL refuse a Python row whose package is not a plain name or whose constraint is not a plain
version specifier, each clause an operator and a version — a bare version, a URL, a path or a VCS reference included — and a fetch that
fails, exiting 2 and reserving nothing.
The fetch SHALL read no `uv` or `pip` setting of the person's environment or home folder, and SHALL have a timeout.
A row whose package starts `npm:` is no Python row: [A queued cut fetches the npm packages it approves](#requirement-a-queued-cut-fetches-the-npm-packages-it-approves) holds it.

#### Scenario: An approved package
- **WHEN** the brief approves `ast-grep-cli` at `>=0.51.1,<0.52` for the slug
- **THEN** `conduct.py cut` runs one wheels-only fetch of `ast-grep-cli>=0.51.1,<0.52` against PyPI's index into `.minions/uv-cache`, and queues the cut

#### Scenario: A URL off PyPI's hosts
- **WHEN** a row's package or constraint is a URL whose host is not `pypi.org` or `files.pythonhosted.org`
- **THEN** `conduct.py cut` exits 2 naming the row, and runs no fetch and reserves nothing

#### Scenario: A bare version
- **WHEN** a Python row's constraint is `1.3.0`, with no operator
- **THEN** `conduct.py cut` exits 2 naming the row, and runs no fetch and reserves nothing

#### Scenario: A brief with no package
- **WHEN** the brief's `## Dependencies` is `None.` or holds no row for the slug
- **THEN** `conduct.py cut` runs no fetch

#### Scenario: A fetch that fails
- **WHEN** the fetch exits non-zero or times out
- **THEN** `conduct.py cut` exits 2 naming the package, and reserves nothing

### Requirement: A plain command runs in an OS sandbox

`conduct.py` SHALL run a plain command — one that is no worker — under macOS Seatbelt, through `conduct.py sandboxed -- <cmd>`.
The command SHALL write only to the trees of the repository it runs in — the primary and each open version's worktree — to its
own fresh temporary folder, and to `/dev/null` and the terminal devices; SHALL read none of the credential paths a worker is denied
(`~/.ssh`, `~/.aws`, `~/.config/gh`, `~/.netrc`, `~/.gnupg`, `~/.kube`, `~/.docker/config.json`, `~/.git-credentials`,
`~/.config/git/credentials`, `~/.npmrc`, `~/.pypirc`, `~/.codex/auth.json` and `~/.claude/.credentials.json`) and write none; and
SHALL have no network of any kind, loopback included. It SHALL start with the credential variables of a Claude worker unset, with
`VIRTUAL_ENV` unset, with git's hooks off, with `UV_OFFLINE=1`, with `uv`'s cache in the run directory, with npm offline, its
install scripts off and its cache in the run directory, and with `TMPDIR` naming that
temporary folder: one made for the command alone, outside every repository, under the conductor's own `TMPDIR`, and removed by
`conduct.py` when the command ends. A conductor whose own `TMPDIR` lies inside a git repository SHALL run nothing, print a line
naming `TMPDIR` and exit 2. Its exit code SHALL be the
command's own, a signal's exit shifted to `128` plus its number. When a failed command's output holds the OS's refusal,
`Operation not permitted`, `conduct.py` SHALL print one `sandboxed: denied —` line after it, so a refused write or call reads as
a refusal. Where `sandbox-exec` is not on `PATH`, `conduct.py` SHALL run nothing, print a line holding `no OS sandbox` and exit 2: it SHALL
never run the command bare.

A command the conductor starts with a deadline SHALL run in a process group of its own. Past its deadline the group SHALL be
sent SIGTERM and, after a short grace, SIGKILL; `conduct.py` SHALL then print one `sandboxed: timed out —` line and exit 124.
Converge SHALL give each command it runs the seconds left to its own deadline.

#### Scenario: A command writes outside the trees
- **WHEN** a command run through `conduct.py sandboxed` writes a file in a folder outside every tree
- **THEN** the write fails with `Operation not permitted`, the command's exit is non-zero, and one `sandboxed: denied —` line
  follows its output
- **AND** a write inside a tree succeeds

#### Scenario: A command reads a credential
- **WHEN** a command run through `conduct.py sandboxed` reads a file under `~/.ssh`
- **THEN** the read fails with `Operation not permitted`

#### Scenario: A command calls the network
- **WHEN** a command run through `conduct.py sandboxed` connects to a loopback port that a listener holds open
- **THEN** the connect fails, and the listener sees none

#### Scenario: The command's exit passes through
- **WHEN** a command run through `conduct.py sandboxed` exits with 3
- **THEN** `conduct.py` exits with 3, and a command a signal ended exits with `128` plus the signal's number

#### Scenario: A worker's credentials stay unset
- **WHEN** `GITHUB_TOKEN` and `VIRTUAL_ENV` are set where `conduct.py sandboxed` starts
- **THEN** the command sees neither, and sees `UV_OFFLINE=1`

#### Scenario: A command's npm
- **WHEN** a command run through `conduct.py sandboxed` reads its environment
- **THEN** it sees `npm_config_offline=true`, `npm_config_ignore_scripts=true` and `npm_config_cache` naming `.minions/npm-cache` of the primary

#### Scenario: A command's own temporary folder
- **WHEN** a command run through `conduct.py sandboxed` runs `git rev-parse` in its `TMPDIR`, and writes a file there
- **THEN** the `git rev-parse` fails, the write succeeds, and the folder is gone after the command ends

#### Scenario: The conductor's temporary folder lies in a repository
- **WHEN** `conduct.py sandboxed -- true` runs with `TMPDIR` naming a folder inside a git repository
- **THEN** `true` does not run, the output names `TMPDIR`, and the exit is 2

#### Scenario: No OS sandbox stands
- **WHEN** `sandbox-exec` is not on `PATH` and `conduct.py sandboxed -- true` runs
- **THEN** `true` does not run, the output holds `no OS sandbox`, and the exit is 2

#### Scenario: A command past its deadline
- **WHEN** a command that starts a child runs under a deadline and outlives it
- **THEN** the command and its child are gone, the output holds a `sandboxed: timed out —` line, and the exit is 124
- **AND WHEN** the command ignores SIGTERM
- **THEN** SIGKILL ends it after the grace

## ADDED Requirements

### Requirement: A queued cut fetches the npm packages it approves

A `## Dependencies` row whose package is `npm:<name>`, a scoped name allowed, and whose constraint is one exact version, SHALL be
an npm row. `conduct.py cut` SHALL refuse an npm row whose name or version is anything else — a range, a tag, a URL, a path, a
git reference or an alias included — exiting 2 and reserving nothing; a Python row SHALL read as before. At each `conduct.py cut`
and at each run's start, for each `package-lock.json` tracked at the default branch, and at a cut for an empty manifest where the
cut approves npm rows in a repository with none, the conductor SHALL install the lock's tree and then the cut's approved npm rows
into `.minions/npm-cache`, from a scratch folder under `.minions/tmp`, under the OS sandbox with the network open: it SHALL write
the scratch folder and the cache alone, read no credential path, run no install script, fix the registry to npm's own, read no
npm setting of the person's environment or home folder, resolve nothing published in the last 7 days, and have a timeout. A fetch
that fails or times out at a cut SHALL exit 2 and reserve nothing; at a run's start it SHALL halt the run. A missing `npm` SHALL
halt by name, only where a row or a lock needs it. The cut SHALL print each package the approved rows add to the lock's tree, its
version and its install-script flag.

#### Scenario: An approved npm package
- **WHEN** the brief approves `npm:vue` at `3.5.43` for the slug
- **THEN** `conduct.py cut` runs `npm` with install scripts off, the fixed registry and a 7-day bound under the OS sandbox with the network open, into `.minions/npm-cache`, and queues the cut

#### Scenario: A row that is no exact version
- **WHEN** an npm row's constraint is `^3.5.43`, `latest`, a URL, a path or a git reference, or its name is an alias
- **THEN** `conduct.py cut` exits 2 naming the row, and runs no fetch and reserves nothing

#### Scenario: A tracked lock
- **WHEN** the default branch tracks a `package-lock.json` and a run starts
- **THEN** the conductor installs that lock's tree into `.minions/npm-cache`
- **AND WHEN** a repository tracks no lock and the cut approves no npm row
- **THEN** no `npm` runs

#### Scenario: A fetch that fails
- **WHEN** the npm fetch exits non-zero or times out at a cut
- **THEN** `conduct.py cut` exits 2 naming the package, and reserves nothing

#### Scenario: No npm
- **WHEN** `npm` is not on `PATH` and a row or a lock needs it
- **THEN** the conductor halts, naming `npm`
- **AND WHEN** no row and no lock needs it
- **THEN** it halts for nothing

#### Scenario: The queue prints the new packages
- **WHEN** an approved row pulls in packages the lock's tree lacks
- **THEN** the cut prints each one with its version and its install-script flag

### Requirement: A worker's npm runs offline from the run directory's cache

A Claude worker, a Codex worker and a plain command run by `conduct.py sandboxed` SHALL start with `npm_config_cache` naming
`.minions/npm-cache` of the primary, `npm_config_offline=true` and `npm_config_ignore_scripts=true`, so no worker reaches the npm
registry and no install script runs. `AGENTS.md` of this repository SHALL declare no `Ship` line for it.

#### Scenario: A Claude worker and a Codex worker
- **WHEN** the conductor builds the command line of a Claude worker, and of a Codex worker
- **THEN** each carries the npm settings beside `UV_CACHE_DIR`

### Requirement: A build halts on a direct npm package no row approves

When a build ends, `conduct.py` SHALL compare each `package.json` tracked on the version's branch with the default branch's file
at the same path and with the npm rows of `design.md`'s `## Dependencies` at the cut commit. A direct package — one under
`dependencies`, `devDependencies`, `optionalDependencies` or `peerDependencies` — that the default branch's manifest does not hold at
that specifier, and that no row approves at that exact version, SHALL halt the version before converge, naming the file, the
package and its specifier.

#### Scenario: A package no row approves
- **WHEN** a version's `ui/package.json` adds `left-pad` at `1.3.0` and no row names `npm:left-pad` at `1.3.0`
- **THEN** the version halts before converge, naming `ui/package.json`, `left-pad` and `1.3.0`

#### Scenario: Every package approved
- **WHEN** each package a version adds is a row of the cut's `design.md` at the same exact version
- **THEN** the version goes on to converge

#### Scenario: A range for an approved package
- **WHEN** a version's manifest holds `vue` at `^3.5.43` and the row approves `3.5.43`
- **THEN** the version halts, naming the package and `^3.5.43`
