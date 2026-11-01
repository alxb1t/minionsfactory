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
  ([D51](docs/decisions.md#d51--a-worker-runs-in-an-os-sandbox-and-no-worker-pushes)): writes stay in the repo and its worktrees,
  network on a short list, no push. It holds Bash and what Bash starts; the permission rules hold `Read`, `Edit` and `Write`,
  each of `SECRETS` denied to `Read`. A Claude worker loads user settings alone, so a project's settings and `.mcp.json` start
  nothing.
- **A mixed run crosses hosts at each station**: what a Codex station wrote reaches the next Claude station's sandbox, and never
  its start.
- **The conductor runs outside the sandbox, and a worker can write the common directory**: its remote calls start from a scratch
  repo in the home folder and read no repo's config. A run keeps `origin`'s URLs in the home folder before its first worker: while
  `origin` differs from them, no remote call runs, in that run or a later one, until a person repoints it or removes the file. A
  changed config halts a run before its next remote call. A worker can redirect git with `commondir` or a swapped `.git`, so
  `conduct.py` halts when git names a repo outside the folder it runs in and no run kept that repo's URLs.
- **A person's yes, or `merge=yes` from a run the person started**, precedes every merge and push.

## Entry points

- A brief, and the change directory the cut writes from it.
- A target repo's files: `AGENTS.md` and its `Worktrees:`, `Ship tools:` and `Ship network:` lines, its standards, its
  Makefile.
- Findings files, status logs and worker output under `.minions/`.

## Out of scope

- A malicious operator, and the host CLI's own security.

## Known gaps

Carded in `.minions/backlog.md`, accepted until paid down: `0049·S5`, `0049·S7`, `0049·R15`, `0050·R5`, `0050·R11`,
`0050·S7`, `0034·R9`. D47 accepts `Ship tools:`.

- A Codex worker can read `~`.
- `0049·S7` and `0050·R5`, what is left: a run's remote calls are out of the race, and its local `status`, `merge` and `commit`
  still read the repo's config after the refusal.
- A credential outside `SECRETS` and `TOKENS` stays readable by a script: the host has no list of its own. So does a repo's
  `.env`, and `conduct.py` pushes to `origin` what a worker commits.
- A run compares the git config with its own first read, so a plain key a run that stopped left is that read, and it steers no
  remote call.
- A repo's first run with a version keeps the URLs it reads, so a URL set before it stands. Where the home folder refuses the
  file, `conduct.py` is itself in a sandbox and keeps none.
- Whether a Codex start reads a worker-written `.codex/config.toml` is not read from its docs.
- `0049·S5`, its hostile route: a worker writes the claim, so it can name a process, with that process's start time, for
  `/mf-ship stop` or a stale clear to kill, or make a live run read stale. A pid at or below 1 is refused, and a group's
  leader must name an executor.
- `0049·R15`, the LFS route: no hook runs in a run, so a run cannot upload LFS objects, and `lfs.*` keys still halt it.
