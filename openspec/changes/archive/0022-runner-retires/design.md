# 0022-runner-retires — design

**In one line:** how the runner, its binding and the absence tests leave, in an order where every phase ends on a
green gate and the delete comes last. **Verdict:** settled — `R1`…`R12`, every text written below.

## Context

See [proposal.md](proposal.md#why) for why. The measurements, at the cut:

| measure | value | command |
|---|---|---|
| lines in the runner's code, prompts and pages | 4852 | `git ls-files orchestrator prompts docs/architecture.md docs/modules \| xargs cat \| wc -l` |
| lines in the runner's tests | 2918 | `git grep -l orchestrator -- tests ':!tests/test_conventions.py' \| xargs cat \| wc -l` |
| the runner's test files | 13 | `git grep -l orchestrator -- tests ':!tests/test_conventions.py' \| wc -l` |
| lines in the runner's capabilities | 819 | `cat openspec/specs/{build-loop,cli,converge,diff,fanout,gate,provider,release,status}/spec.md \| wc -l` |
| lines in the tracked tree, less history and the lock | 12140 | `git ls-files -- ':!openspec/changes/archive' ':!CHANGELOG.md' ':!uv.lock' \| xargs cat \| wc -l` |
| markers on the tests that survive | 30 | `grep -c '^\s*@pytest\.mark\.spec' tests/test_skills.py tests/test_principles.py` |

Constraints the order follows:

- **`orchestrator/__main__.py:35` imports `run_check`** from `orchestrator/specs.py`, and `:276-289` wire the
  `specs check` subcommand. The checker cannot be deleted before the runner without editing runner code.
- **`pyproject.toml` registers the `spec` and `spec_exempt` markers.** Pytest warns on an unregistered marker, so the
  registration goes when the last marked test goes.
- **The fold cannot delete a capability file, nor reach a Purpose** (`skills/mf-release/SKILL.md`, Step 2). D10
  says a deleted capability leaves no directory behind.

### The runner's tests

`tests/test_converge.py` · `tests/test_diff.py` · `tests/test_driver.py` · `tests/test_fanout.py` ·
`tests/test_findings.py` · `tests/test_gate.py` · `tests/test_main.py` · `tests/test_provider.py` ·
`tests/test_release.py` · `tests/test_smoke.py` · `tests/test_specs.py` · `tests/test_state.py` ·
`tests/test_status.py`.

## Goals / Non-Goals

**Goals:** the runner, its binding and `.env.example` leave the tree; no test asserts an absence; no live text names the runner;
each phase ends on a green `make gate`.

**Non-Goals:** a trailer check; any new scan; a README rewrite; a change to `mf-converge` or `mf-release`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="r1"></a>**R1** | The binding stops in phase 1: the gate's `specs check` line goes, and the surviving tests drop their markers. `orchestrator/specs.py` and `tests/test_specs.py` go with the runner in phase 4 | the check is off before any runner test is deleted, so it never sees an orphan; the checker is imported by the runner's CLI | the checker kept as a script in `bin/` — no target can run it, and it alone makes specs carry keys |
| <a id="r2"></a>**R2** | The runner's capabilities leave by REMOVED requirements; the release deletes the emptied capability directories by hand | living specs change only through the fold; the fold cannot delete a file; D10 | deleting the directories in a phase under `skip_specs` — the living spec would change outside the fold |
| <a id="r3"></a>**R3** | `sdd`'s runner-held requirements are REMOVED: *Enforced binding*, *Full backfill traceability*, *Reviewer conformance*, *Release fold*, *Change structure*, *Repository is the source of truth for change progress*, *Commit-to-change traceability*. No card for the trailer | the skills hold that ground; D21 keeps the trailer as a convention | a trailer check moved onto `mf-release` — a new behaviour, not a retirement |
| <a id="r4"></a>**R4** | No test asserts an absence: `tests/test_conventions.py` is deleted; *The retired gate config is named nowhere* and *The backlog export is named nowhere* are REMOVED; [the principle](#the-principles) is rewritten. The `tests/test_skills.py` needles that guard a live rule against its opposite stay | a test holds what is true now; a needle against a rule's opposite tests what the skill says now | a scan for the runner's names |
| <a id="r5"></a>**R5** | [D36 and D37](#the-decisions) enter `docs/decisions.md` in *Repo conventions*, after D23 | a gate check and a test file retired on purpose have their reasons on record, against *Never weaken the gate to pass*; `A7` | one decision for both — they answer separate questions |
| <a id="r6"></a>**R6** | `Key:` and `Layers:` leave `sdd` by MODIFIED requirements, each copied from HEAD without them | the fold is the only path into living specs; the keys fed only the checker | leaving the bullets in place |
| <a id="r7"></a>**R7** | `sdd`'s Purpose is rewritten by a hand-edit flagged for the release; the name `sdd` stays | the fold cannot reach a Purpose; a rename is a REMOVED and ADDED of every requirement | a rename |
| <a id="r8"></a>**R8** | The front door's runner sections are deleted, with nothing in their place; D4 is unchanged | `CHANGELOG.md` and `git log` are the history; D4 is still true — the tests run on uv | a line pointing at the last tag that held the runner |
| <a id="r9"></a>**R9** | `pydantic` leaves `pyproject.toml`, and `uv.lock` is re-locked, in phase 4 | only the runner imports it | — |
| <a id="r10"></a>**R10** | Pays down `0020·N1` (closed by [R4](#r4): the principle no longer claims a scan), `0020·N3` ([config.yaml](#openspecconfigyaml)) and `0021·N1` ([the harms](#skillsmf-cut-changeskillmd)) | each card's trigger is this change | `0020·N2` — this change does not open `skills/mf-converge/SKILL.md` |
| <a id="r11"></a>**R11** | The phases, in order: the binding stops · the absence tests go · the text follows · the runner goes | `A4`: the delete is the last act; phase 2 stands apart as D37's own | the delete before the text |
| <a id="r12"></a>**R12** | `.env.example` is deleted in phase 4, and `CLAUDE.md` stops naming it in phase 3. *Found at the cut; put to the human.* | its one claim is that "the orchestrator reads nothing outside the repository"; nothing reads `.env` once the runner goes; D23 | rewording it as scaffolding for a target — no target reads this repo's file |

## The decisions

Inserted after D23, before `## The autonomous line`. The diagram's line `Repo conventions D19…D23` becomes
`Repo conventions D19…D23, D36, D37`.

```markdown
### D36 · Specs are bound by review, not by a checker

**A scenario says what proves it in prose; review judges whether a test proves it. No marker ties a test to a
scenario, and the gate does not check the binding.**

- **Why:** a binding checker is per-language code no target repo can run, and it made every spec carry keys only it
  read.
- **Gave up:** the gate failing on a requirement with no test.

### D37 · Tests hold what is true now; nothing tests an absence

**A test asserts a behaviour or a rule the repo holds today. A retired name leaves the tree in the commit that
retires it, checked once by that change's acceptance. A scan may name what a live rule forbids; it never lists
retired names.**

- **Why:** a scan for retired words grows with every retirement, and tests a history rather than the system.
- **Gave up:** a reintroduced name turning the gate red. Review's stale-claim pass looks for it instead.
```

## The principles

`docs/principles.md`, *The repo reaches nothing outside itself*, its **Held by**:

```
before:  - **Held by:**
           `tests/test_conventions.py::test_the_retired_vault_vocabulary_is_named_nowhere_in_code_prompts_or_docs`; each
           skill's rule never to write an absolute path.
after:   - **Held by:** each skill's rule never to write an absolute path.
```

*A retired word is retired everywhere*, whole:

```markdown
### A retired word is retired everywhere

**When a thing is deleted, its name leaves code, skills and docs in the same commit.**

- **Why:** a resurrected word resurrects its assumptions.
- **Held by:** the retiring change's acceptance, run once; `mf-build`'s `W2` list in the phase commit; review's
  stale-claim pass. No standing scan ([D37](decisions.md#d37--tests-hold-what-is-true-now-nothing-tests-an-absence)).
```

## The front door

### `CLAUDE.md`

- `:30` — `· strict types · the tests · the spec binding.` → `· strict types · the tests.` (phase 1)
- `:57-58` — the sentence `One part stays live: `orchestrator/specs.py` is the spec-binding check the gate runs.`,
  deleted. (phase 1)
- `:38-40` — `Tracked here and installed by symlink (`make install-skills`); a shipped skill is a role prompt, and is
  inside the retired-vocabulary scan for that reason.` → `Tracked here and installed by symlink
  (`make install-skills`).` (phase 2)
- `:41` — `the autonomous design; and the deprecated runner's pages.` → `the autonomous design.` (phase 3)
- `:51-59` — the `---` rule and the `## The deprecated runner` section, deleted; the `---` at `:60` stays. (phase 3)
- `:70-71` — `the committed `CLAUDE.md` / `.env.example` stay path-free.` → `the committed `CLAUDE.md` stays
  path-free.` ([R12](#r12), phase 3)

### `README.md`

- `:55-56` — `· strict type-check · tests · the spec-binding check.` → `· strict type-check · tests.` (phase 1)
- `:68-69` — the sentence `One part stays live until then: `python -m orchestrator specs check` is the
  spec-binding check this repo's gate runs.`, deleted. (phase 1)
- `:64-69` — the blank line and the `## The deterministic runner — deprecated` section after it, deleted; the file
  ends at `:63`. (phase 3)

### `docs/README.md`

- `:25-29` — the `## Deprecated` section and the blank line after it, deleted. (phase 3)

### `Makefile`

- `:15` — `uv run python -m orchestrator specs check --strict`, deleted. (phase 1)
- `:7-8` — `The mf-* skills, CI and the` / `# parked runner run `make gate`;` → `The mf-* skills and CI run` /
  `# `make gate`;`. (phase 3)

### `openspec/config.yaml`

Closes `0020·N3`. In phase 3.

```
proposal, 2nd:  … This repo's reader requires it, and the CLI neither emits nor checks it.
           →    … The skills read it, and the CLI neither emits nor checks it.
design, 1st:    … take the highest seam that gives the coverage — this repository lives on its seams (the
                `Provider` Protocol, the `run_gate` seam).
           →    … take the highest seam that gives the coverage.
tasks, 1st:     … `orchestrator/state.py` reads only that section and matches only that form.
           →    … `mf-build` ticks only that section, and only that form.
tasks, 2nd:     … `- [ ] N.M` sub-tasks live inside those sections, where the progress parser never sees them.
           →    … `- [ ] N.M` sub-tasks live inside those sections.
```

## The skills

### `skills/mf-build/SKILL.md`

The `W2` example at `:126-129` (phase 3):

```
before:      retired: read_change_state → load_change
               orchestrator/state.py — fixed
               docs/modules/state.md — fixed
               openspec/specs/sdd/spec.md — kept: a spec names the old term until the fold
after:       retired: docs/sdd.md → docs/principles.md
               skills/mf-build/SKILL.md — fixed
               CLAUDE.md — fixed
               openspec/specs/sdd/spec.md — kept: a spec names the old term until the fold
```

- `:220`, `C8`'s example — `` `# remove when the runner runs make gate` `` →
  `` `# remove when the OpenSpec CLI checks version:` `` (phase 3).
- `:226` — `A comment, before → after, from this repo's `tests/test_conventions.py`:` → `A comment, before →
  after:` (phase 2).

### `skills/mf-cut-change/SKILL.md`

- `:182`, `A5`'s example — `"when the runner resumes", not "in v0.15"` → `"when a target repo has no remote", not
  "in v0.15"` (phase 3).
- `:201-202`, *Suggesting models*, **Converge** — `A new code path, a dependency, or an anchored harm means run it`
  → `A new code path, a dependency, or an anchored harm — data loss, spend, exposure of personal data or secrets,
  silent wrong output — means run it`. Closes `0021·N1` (phase 3).

## The tests and `pyproject.toml`

- **Phase 1:** each `@pytest.mark.spec(...)` and `@pytest.mark.spec_exempt(...)` decorator line in
  `tests/test_skills.py` and `tests/test_principles.py` is deleted. Each is one line, directly above its `def`.
- **Phase 4:** `[project] dependencies` becomes `[]`; the `markers = [...]` entry of `[tool.pytest.ini_options]`
  is deleted; `uv lock` re-locks.

## Dependencies

None. `pydantic` is removed ([R9](#r9)); nothing is added.

## Risks / Trade-offs

- **A requirement can ship with no test** → D36 accepts it; review judges each scenario's test.
- **A retired name can come back** → D37 accepts it; review's stale-claim pass looks for it.
- **An untrailed commit can reach a release** → D21 is a convention `mf-build` writes; nothing checks it ([R3](#r3)).
- **Between phases 3 and 4, no doc names `orchestrator/` while it exists** → nothing reads it; phase 4 deletes it.
- **`openspec/specs/` names the runner until the fold** → expected: the specs change at the release.

## For the release

The hand-edits, flagged:

1. **Delete the emptied capability directories** ([R2](#r2)): `git rm -r openspec/specs/build-loop
   openspec/specs/cli openspec/specs/converge openspec/specs/diff openspec/specs/fanout openspec/specs/gate
   openspec/specs/provider openspec/specs/release openspec/specs/status`.
2. **Rewrite `sdd`'s Purpose** ([R7](#r7)) as:

   ```markdown
   ## Purpose

   The rules the `mf-*` skills hold, each proved by a scan over the skill text.
   ```

After the hand-edits: `ls openspec/specs` prints `sdd`, and `grep -c 'Key:' openspec/specs/sdd/spec.md` prints `0`.

## Verdict

Cut as settled. The binding stops first and the delete comes last; D36 and D37 record what the gate gives up.
