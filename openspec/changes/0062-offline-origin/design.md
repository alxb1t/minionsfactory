# Offline origin — design

A run goes on when `origin` cannot be reached, its pushes waiting; an offline base the conductor keeps judges the default
branch meanwhile. Verdict at the end: ready to build.

## Context

Read at `e1f922b` (v0.50.0 merged). `conduct.py` is `skills/mf-ship/scripts/conduct.py`.

- **F1. The start read halts the run.** `ship()` logs `start`, then calls `push_left()` (`:2226-2237`) → `_unpushed(first_read=True)`
  → `_push_default` → `_origin_head` → `ls-remote --symref` (`:942`); a failure is `Stop(1, "conduct: halt — cannot read origin:
  nothing pushed")` (`:944`), as is a failed `ls-remote --heads --tags` (`:1196-1200`). `push_left` halts the run (`:2204-2206`),
  and `ship` closes with exit 1 before any worker (`:2238-2240`). No retry; `GIT_TIMEOUT = 60` (`:46`).
- **F2. What the read decides.** The base for `_foreign_commit` — every first-parent commit past it on the default branch must be a
  release merge on a ledger head (`:1141-1176`); ledger cleanup (`_close_releases`, `:878-887`); what to push. The base is origin's
  listed default sha; `status`, with no read, uses the local `origin/<default>` (`:1199-1202`), which a worker writes. `advance`'s
  integrate check uses that local ref too (`:1953-1955`).
- **F3. Home-folder records.** Kept URLs (`:834-840`), `<digest>.default` (`:932-934`), the ledger `<digest>.released/`
  (`:848-854`). None holds a base. On this machine: MF, isekai and gpunit each hold the URLs, `.default` and `.released`, and each
  tracking ref equals its local `main`, a release merge (`e1f922b`, `22291a5f`, `ba0fced`).
- **F4. A release's push.** After the release worker, `push_left()` (`:1981`); a failed push halts the run (`:2216-2219`); then
  `_check_release` fails "`<tag>` is not on origin" when `_pushed` cannot list it (`:783-784`). A dependent waits on
  `_shipped(primary, default, dependency)` — the archive folder on the local default branch (`:248-251`, `:2033-2037`) — so a local
  release already satisfies it.
- **F5. `status`** prints `run · unpushed <names>` from local refs (`:2440-2443`); a released version is merged, so it leaves the
  version list.
- **F6. ssh.** Neither `GIT_SSH_COMMAND` nor a global `core.sshCommand` is set here; `_outside` passes the environment through
  (`:1032-1050`).
- **F7. Who can write the home folder.** No worker: D51; where the home folder refuses a write, `conduct.py` is itself sandboxed
  (`_keep_origin`, `:899-931`). A worker can run `uv`, so the sandbox, not the tools list, keeps it from `anchor`.
- **F8. The cards.** `0049·S7` names `_pushed`'s refusal and a later `ls-remote` reading the config again; `_listed` now goes
  through `_outside`, which reads no repo config (`:1052-1057`). `0051·R12`: `_unpushed`'s no-read path runs
  `_foreign_commit(primary, f"origin/{default}", …)`, whose `rev-parse --verify` stops with git's raw error when the ref is missing.

## Goals / Non-Goals

**Goals:** a run builds, converges, integrates and releases while `origin` is down; pushes wait and resume; a forged commit on the
default branch still halts the run; the person sees what is local only.

**Non-Goals:** Claude's or Codex's API down; a first-ever run with no kept URL; telling auth from network errors.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | An offline base, `<digest>.pushed`, written after every good read and every default-branch push | the judge needs origin's last known sha; the conductor writes the home folder and no worker does | the tracking ref, which a worker writes |
| [D2](#d2) | Every failed read or push is a wait; a good read showing something wrong halts | isekai's outage refused SSH auth intermittently: network and auth cannot be told apart | classifying git's errors |
| [D3](#d3) | Three tries at the start, two per release, one before the close; ssh options when the operator set none | a dead host must not hang a run, nor a prompt block it | a background retry thread |
| [D4](#d4) | A release made offline passes as released locally | merge and tag are local; the push already resumes at the next read | holding the version |
| [D5](#d5) | The record: the `start` line, `push — waiting`, the close's `· unpushed`, `report` | the person must see what is local only | a new `status` form: `run · unpushed` already prints it (F5) |
| [D6](#d6) | `conduct.py anchor` seeds the first base from the tracking ref, checked, in a person's session | the first outage finds no base; the person's session is not a run's | automatic trust of the tracking ref at a run's start |
| [D7](#d7) | The cards: `0049·S7` checked and closed with its evidence; `0051·R12` named | `_pushed` and `_unpushed` are opened | — |

### D1

`_pushed_file(primary)` returns `Path.home() / KEPT_ORIGINS / f"{_digest(primary)}.pushed"`. `_keep_base(primary, sha)` writes it
owner-only, replacing an older one through a temp file and `os.replace`. Written in `_unpushed(first_read=True)` once `base` is
read (`held.get(f"refs/heads/{default}")`), and in `push_left` after a `heads` push succeeds, with its `sha`. Read by
`_offline_base(primary)` → the sha, or `None`.

Offline, `_foreign_commit` takes `_offline_base(primary)` as `base` in `push_left`'s judge and in `advance`'s integrate check, in
place of `origin/<default>`. Online, both are as today.

### D2

`Unreachable(Stop)` — raised in place of the two `Stop(1, "conduct: halt — cannot read origin: nothing pushed")` (`:944`, `:1200`),
its message git's last stderr line. `push_left` catches it: the run is **offline** (`self.offline = True`), and it returns
`True`. A failed `push` re-reads `origin` once with `ls-remote --heads`: that read failing too makes it the same wait —
`self.log.event("run", "push", f"waiting: {why}")`, `self.offline = True`, return `True`; that read succeeding means `origin`
refused the push, and the run halts as today, `git push origin <name> failed, exit N`, so
`test_a_rerun_pushes_what_a_release_left`'s rejected push stays a halt. Every other `Stop` halts the run, as today: a refused URL, `_push_default`'s kept-name halt, origin's default not a commit
this repo has, a foreign commit.

Offline with no offline base → `Stop(1, "conduct: halt — cannot read origin, and no offline base: a person runs conduct.py anchor")`,
a run halt before any worker.

### D3

`RETRIES = (0, 10, 30)` — the start's read, each try after `time.sleep(delay)`; `PUSH_RETRIES = (0, 10)` — a release's push. Tests
patch both to zeros. `ship()` reads `origin` before it logs `start`, so the `start` line can carry D5's field; a halt the read
raises is logged after `start`. Before the close, a run that is offline or holds pending refs calls `push_left()` once more.

`_outside` adds `GIT_SSH_COMMAND="ssh -o ConnectTimeout=15 -o BatchMode=yes"` to its environment when `GIT_SSH_COMMAND` is unset
and `git config --global --get core.sshCommand` prints nothing.

### D4

`check(..., offline=self.offline)` → `_check_release(…, offline)`: offline, a tag `_pushed` cannot list is no failure. `advance`
then appends the tag to `self.released`, logs `push — waiting: <tag> released locally`, and removes the worktree, as today. The
ledger keeps the head; the next good read pushes it (`_unpushed`) and `_close_releases` removes it. A dependent needs nothing new
(F4).

### D5

- **`start`:** `· origin: unreachable — pushes wait` after `versions …` when the read failed.
- **`push — waiting: <why>`:** each failed read or push, and each local release.
- **The close:** `closing()` gains `· unpushed <names>` when `_unpushed(self.primary)` lists any — names as `status` prints them.
- **`report`:** a `run · waited <why>` line per `push — waiting` event of the last run, before the version lines.
- **`status`:** no change: `run · unpushed <names>` (F5).

### D6

`conduct.py anchor`, a subcommand: exit 2, naming the check, when `.minions/runs/active` is live, `.pushed` stands, the default
branch's tracking ref is missing, it is not an ancestor of the local default branch (`_history_ancestor`), or it is no release
merge (`_merges_a_release(primary, sha, _release_tags(primary))`). The default branch is `<digest>.default`'s name, else
`default_branch`. Otherwise it writes `.pushed` and prints `anchor: <sha> · <subject>`, exit 0. It needs a person's session: no
worker can write the home folder (D51, F7). `skills/mf-ship/SKILL.md` names it in the command table and in the halt table, beside
D6's halt.

### D7

`0049·S7`: the build runs its *Still true?* — read `_pushed` — and records in the commit body that its remote call goes through
`_outside`, so the card closes with that evidence. `0051·R12`: the no-read path checks `origin/<default>` with `_maybe(…,
"rev-parse", "--verify", …)`, and on `None` stops `Stop(1, "conduct: halt — origin has no <default>: push it by hand")`.

## Tests

`grep -c '^def test_' tests/test_conduct.py` prints `36`; `uv run pytest -q --collect-only tests/` collects `107`. This change adds
five tests, unit and integration layer, no end-to-end run (`T1`); none is deleted or merged.

| test | layer | why new (`T2`) |
|---|---|---|
| `test_a_good_read_keeps_the_offline_base` | integration, fake worker | no test reads the home folder's base |
| `test_anchor_seeds_the_offline_base` | unit | a new subcommand |
| `test_a_run_goes_on_while_origin_is_down` | integration, fake worker | `test_a_rerun_pushes_what_a_release_left` starts with `origin` up; the outage needs its own setup |
| `test_a_local_release_is_pushed_when_origin_returns` | integration, fake worker | its two runs are one flow |
| `test_the_remote_calls_carry_the_ssh_options` | unit | `_outside`'s environment |

The outage is the fixture's bare `origin` renamed away, its return the rename back; `RETRIES` and `PUSH_RETRIES` patched to zeros.
`0051·R12`'s step joins `test_status_reads_each_stage_from_disk`.

## Dependencies

None.

## Risks / Trade-offs

- **The ledger's window** stays open for the outage's length: a head authorizes a release until it lands on `origin`. Same class,
  held longer; `THREAT_MODEL.md` *Known gaps* says so.
- **The anchor trusts the tracking ref** once, checked by the person's session; a ref a past worker moved to a forged release
  merge would pass. `THREAT_MODEL.md` names it.
- **A long outage** releases several versions locally; the next good read pushes them in one go, judged as today.

## Verdict

Ready to build.
