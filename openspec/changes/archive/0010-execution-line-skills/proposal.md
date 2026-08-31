---
version: v0.10
---

## Why

The four end-of-change stations this project actually ships releases with — build, converge, backlog export,
release — exist only as prompts pasted by hand into a fresh session. They drove `v0.9` end to end and are
proven, but a prompt that must be pasted travels to no other repository, and the practices are about to leave
this repo for real projects. **v0.10 is the last version**; whatever it does not carry, a real project will trip
over, and that trip is the next record.

## What Changes

- **Four skills land under `skills/mf-*/SKILL.md`**, hand-authored from the proven prompts — transcription, not
  invention:
  - `mf-build` — builds the active change one phase per pass (run each stated verification, never summarize it;
    green gate; CHANGELOG entry; tick the box; one trailered commit per phase), then closes with a `/simplify`
    pass whose edits are re-gated and committed on their own.
  - `mf-converge` — conducts the end-of-change loop and judges nothing itself: freeze the diff, fan out review
    and security as fresh read-only subagents, read the verdicts **from disk**, dispatch one fix subagent,
    re-verify, loop to a cap of three rounds.
  - `mf-backlog-export` — the human-invoked vault bridge; the vault path is an explicit parameter, and it
    commits nothing.
  - `mf-release` — verify · fold · archive · cut the changelog · tag · **stop**, naming merge and push as the
    human's.
- **The review content is adopted, not written.** `/code-review`, `/security-review` and `/simplify` are
  community skills; this change owns the *contract* around them — scope, severity vocabulary, output shape, the
  status machine and who may promote a verdict — and writes no rubric.
- **An installation path that is a command, not a claim** — `Makefile` gains `install-skills` /
  `uninstall-skills` symlink targets into the operator's personal skills directory. `README.md` gains the
  invocation lines and its stale `## Status` section is corrected.
- **`CLAUDE.md` declares the two lines** — `orchestrator/` + `prompts/` implement the automated line;
  `skills/mf-*` is the human-invoked line that ships releases. The duplication is declared, not resolved.
- **The retired-vocabulary scan widens from nine roots to ten.** `skills/` was a scanned root while it existed
  and was dropped from the tuple only because `v0.8` deleted the directory; re-creating it without re-adding it
  would re-open a closed gap. A skill is a role prompt, and role prompts are where retired vocabulary hides.

## Capabilities

### New Capabilities

<!-- None. The skills are operator tooling outside the orchestrator's behavioural surface; nothing in
     `orchestrator/` changes, so no capability is introduced. -->

### Modified Capabilities

- `sdd`: *Repository is the source of truth for change progress* — the shared retired-vocabulary root set goes
  from nine roots to ten, adding `skills/`. Both scan scenarios name the set verbatim, so the requirement
  changes with it.

## Impact

- **New:** `skills/mf-build/SKILL.md`, `skills/mf-converge/SKILL.md`, `skills/mf-backlog-export/SKILL.md`,
  `skills/mf-release/SKILL.md`.
- **Modified:** `Makefile` (new targets only — the `gate` target is not touched), `README.md`, `CLAUDE.md`,
  `tests/test_conventions.py` (the root tuple and both reintroduction tests), `openspec/specs/sdd/spec.md` via
  the delta.
- **Untouched by design:** `orchestrator/`, `prompts/`, `docs/sdd.md`, the `gate` array and its four mirrors,
  and every other capability under `openspec/specs/`.
- **Dependencies:** none added. The skills are markdown; the review engines are already installed.
- **Runtime artefacts:** `mf-converge` writes `.minions/findings/<change-id>_diff.patch` beside the findings
  files, under the already-gitignored `.minions/`.
