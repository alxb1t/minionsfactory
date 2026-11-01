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
  network on a short list, no push. It holds Bash and what Bash starts; the permission rules hold `Read`, `Edit` and `Write`.
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
- `0049·S5`, its hostile route: a worker writes the claim, so it can name a process, with that process's start time, for
  `/mf-ship stop` or a stale clear to kill, or make a live run read stale. A pid at or below 1 is refused, and a group's
  leader must name an executor.
- `0049·R15`, the LFS route: no hook runs in a run, so a run cannot upload LFS objects, and `lfs.*` keys still halt it.
