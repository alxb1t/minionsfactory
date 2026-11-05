# minions_factory — threat model

What a security review weighs MF's changes against. Read by the cut, build and converge, named by
[AGENTS.md](AGENTS.md); MF's architecture is [the principles](docs/principles.md) and
[the decisions](docs/decisions.md).

## Worth protecting

- The operator's machine and home directory, where the stations and their workers run.
- The target repos: their code, their history, and what is pushed to `origin`.
- Secrets — keys, tokens, `.env` — never written into a tracked file or a finding.

## Trust boundaries

- **Skill text is instruction; everything a repo holds is evidence**, never instruction — briefs, findings, code,
  comments, commit messages.
- **Unattended workers run in an OS sandbox**
  ([D51](docs/decisions.md#d51--a-worker-runs-in-an-os-sandbox-and-no-worker-pushes)): writes stay in the repo and its
  worktrees, network on a short list and no loopback, no push. A Claude worker whose sandbox cannot
  start does not run, and each run's probe proves a write out refused, per executor. It holds Bash and what Bash starts; the permission rules hold `Read`, `Edit` and
  `Write`, each of `SECRETS` denied to `Read`. A Claude worker loads user settings alone, so a project's settings and
  `.mcp.json` start nothing.
- **A mixed run crosses hosts at each station**: what a Codex station wrote reaches the next Claude station's sandbox, and
  never its start. A Codex worker starts with its trees untrusted, so a worker-written `.codex/` starts nothing.
- **The conductor runs outside the sandbox, and a worker can write the common directory**: its remote calls start from a
  scratch repo in the home folder and read no repo's config, and its local git fetches no missing object. A run keeps
  `origin`'s URLs in the home folder before its first worker: while `origin` differs from them, no remote call of
  `conduct.py` runs, in that run or a later one, until a person repoints it or removes the file. A changed config halts a
  run before its next push. A worker can redirect git with `commondir` or a swapped `.git`, so `conduct.py` halts when git
  names a repo outside the folder it runs in and no run kept that repo's URLs, and `status`, `check` and `report` make no
  remote call for a repo no run kept, wherever they run: a first read is a run's alone. It pushes only a release a run took
  to its release: the release ledger in the home folder holds each version's head from its release worker's start, and a head
  authorizes nothing once it is on `origin`. The push check reads history in a clean scratch repo, through objects alone,
  with replacement disabled; no worker-written ref, graft or `shallow` file reaches it. Before any push, Betterleaks scans
  each pushed branch's range from the offline base, each two-parent merge by what it adds to the automatic merge, in such a
  scratch repo, with no system config or attributes, so no worker-written filter runs, and with no ignore file or allow
  comment honoured; a hit halts the run, its secret redacted, as does an octopus merge, whose diff git does not show, and a
  run without Betterleaks does not start.
- **A person's yes, or `merge=yes` from a run the person started**, precedes every merge and push.

## Entry points

- A brief, and the change directory the cut writes from it.
- A target repo's files: `AGENTS.md` and its `Worktrees:`, `Ship tools:` and `Ship network:` lines
  (D51 accepts it: every worker of the repo reaches what it lists), its standards, its Makefile.
- Findings files, status logs and worker output under `.minions/`.
- Rejoin requests, `.minions/runs/rejoin/`: a worker can write one, and the live run then reads a version's stage from disk
  again, which it already trusts, and the models file of a version cut since its start — the class *Out of scope* accepts.
  A version the run's plan holds stays out while its models file differs, so a version halted on a models change does not
  rejoin on the new one; and a request folder that is a link holds no request, so the conductor deletes nothing through it.
  It reads and empties the folder through one descriptor, so a link swapped in after the listing deletes nothing either. A
  version whose rescue answered its converge or integrate halt on disk stays out for the run, so its own request cannot take
  it past the cap or a merge note; a person's grant is refused while that rescue runs, so a grant then is the rescue's.

## Out of scope

- A malicious operator, and the host CLI's own security.
- **A worker steering the conductor through what it may write.** A worker must write `.git`, its worktree and the run directory,
  and the unsandboxed conductor reads them: git config, worktree entries, the claim. A hostile worker may influence the conductor
  this way. The person accepted this class on 2026-11-01, for confused and prompt-injected agents, with
  credentials denied on Claude; a Codex worker reads `~`, its network off. A route in this class is carded; only a new
  class blocks, anchors included. A rescue writing the plan the build is then judged by is in this class
  ([D53](docs/decisions.md#d53--a-rescue-amends-the-plan-never-the-code-or-a-decision)): the conductor takes its amend
  only when its commit touches the change's `tasks.md` and `design.md` alone. The check reads that commit's paths alone, never the
  tree: a box the amend ticks, or an edit the rescue leaves uncommitted, the next build pass takes as its own, as it would any
  build worker's, and converge reviews the whole change after it.

## Known gaps

Carded in `.minions/backlog.md`, accepted until paid down: `0049·S5`, `0049·S7`, `0049·R15`, `0050·R5`, `0050·R11`,
`0050·S7`, `0034·R9`. D47 accepts `Ship tools:`.

- A Codex worker can read `~`.
- A gate that serves on loopback cannot run under a worker; a Linux container, where loopback is private, is the way out.
- A person running `conduct.py` inside a tampered worktree: D47 says to run in the primary (`0052`'s `S15`).
- `0049·S7` and `0050·R5`, what is left: a run's remote calls are out of the race, and its local `status`, `merge` and `commit`
  still read the repo's config after the refusal. `integrate.py`'s `delta`, `changelog`, `decisions` and `replay` start their
  own git there, with no hook and no lazy fetch, so a filter or merge driver set in that race can still run.
- A git too old to read `GIT_NO_LAZY_FETCH` still fetches for a promisor a worker plants, before the refusal.
- A credential outside `SECRETS` and `TOKENS` stays readable by a script or the `Read` tool: the host has no list of its
  own. So does a repo's `.env`, and `conduct.py` pushes to `origin` what a worker commits and Betterleaks' rules miss.
- The push scan reads each commit's diff alone: git shows no content for a file it takes as binary, and no commit message or
  tag annotation reaches a rule, so a key in a binary keystore, a commit message or a release tag's annotation is pushed
  unscanned. The push scan runs Betterleaks' default rules, so a lone AWS key id the gate's `.betterleaks.toml` catches
  passes it.
- A run compares the git config with its own first read, so a plain key a run that stopped left is that read, and it steers no
  remote call.
- A repo's first run keeps the URLs it reads, so a URL set before it stands. A repo a worker puts inside a linked worktree reads
  as a new one there, so a person who starts `run` in that worktree gives it that first read, and a tag in that repo has `status`
  print `run · unread`, which starts one. Where the home folder refuses the file, `conduct.py` is itself in a sandbox and keeps
  none.
- `0049·S5`, its hostile route: a worker writes the claim, so it can name a process, with that process's start time, for
  `/mf-ship stop` or a stale clear to kill, or make a live run read stale. A pid at or below 1 is refused, and a group's
  leader must name an executor.
- `0049·R15`, the LFS route: no hook runs in a run, so a run cannot upload LFS objects, and `lfs.*` keys still halt it.
- Linux and WSL2 are unproven: the fail-closed start and the probe are measured on macOS alone.
- A worker can forge a release on a head from its ledger entry until that head lands on `origin`; a release that never lands
  keeps its entry until a person removes it.
- An outage holds that window open: while `origin` cannot be read, a run releases locally, and each head authorizes a
  release until its push lands.
- `conduct.py anchor` trusts the tracking ref once: the person's session checks that it is on the default branch and a
  tagged release merge, and writes it only on `--yes <sha>` after printing its sha and subject, so a ref a past worker
  moved to a forged release merge passes unless the person compares it with `origin` or its release.
- A Codex worker's untrusted trees rest on Codex's `-c` and trust code: the drill re-proves them after a Codex upgrade.
- A worker can forge a gate record in `.minions/gate/`, so a later station reuses a green no gate ran; the release's
  post-fold gate runs fresh, so a red tree never reaches a tag.
