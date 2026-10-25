# Terse skills — design

Rewrite the skills, their role references and the shared context shorter, with every rule kept and every reader
reading it the same way. Verdict: ready to build. Scope is [the proposal](proposal.md).

## Context

Premises were re-checked on `main` at `a926ca1` (v0.28.0) before the cut.

| evidence at the cut | implication |
|---|---|
| Every reading set below opens with the shared context: 4,947 words (`sh measure.sh`, first line) | Phase 6 cuts a cost every station pays ([D5](#d5)) |
| Build repeats role boundaries and AGENTS authority (`skills/mf-build/SKILL.md:8-14,71-86,308-316`) | Say each once, where it binds ([D2](#d2)) |
| Converge repeats fresh-worker rules (`skills/mf-converge/SKILL.md:8-15,107-114,191-193,483-486`), freeze supersession (`:178-180,300-307,352-360`) and status ownership (`:278-287,335-340,365-379`) | One home each; the rest point to it |
| The cut repeats verification ownership, dependency approval and commit timing (`skills/mf-cut-change/SKILL.md:94-120`) | One statement each |
| The change-id inference and the gate constants are copied in build, converge and release | Reader-local repetition: each stays, shorter ([D2](#d2)) |
| The structural tests read `## Input contract`, `## Prose rules`, `## Rules for tests` and `## The card` by heading and bold first cell (`tests/test_skills.py`) | Interfaces ([D3](#d3)) |
| `0023·R7`, `R8`, `S1`, `S5` cite converge precondition 6 (`:158-165`) and release precondition 8 (`skills/mf-release/SKILL.md:93-100`) | Those blocks stay word for word ([D3](#d3)) |
| `0028·R4`: the backlog requirement's SHALL text names two pickup sizes and writes every card; the skill picks `one line and a test` too and skips moot cards (`skills/mf-converge/SKILL.md:391,407-408`) | The delta closes it ([D8](#d8)) |
| `codex-cli 0.163.0` and `Claude Code 2.1.308` are installed; Codex is configured for `gpt-6.1-sol` | The reader check's recipes ([D6](#d6)) |
| `/bin/sh` runs `git` here; the `bash` on `PATH` is an x86_64 build whose `git` fails | The change's scripts are POSIX `sh` and fail closed |

## Goals / Non-Goals

**Goal:** each station's instructions say each rule once, where it binds, in the fewest words that keep it — and
a fresh reader of the new text acts as a fresh reader of the old one did.

**Non-goals:** see [the exclusions](proposal.md#not-in-this-change).

## Decisions

The grilling settled these choices; the build does not reopen them.

### D1

| id | decision | because | rejected |
|---|---|---|---|
| D1 | Rewrite the five `SKILL.md` bodies, the three `references/generic-*.md`, `AGENTS.md`, `docs/principles.md` and `docs/decisions.md` | The skill bodies are what every target pays for; the shared docs are what MF pays for | The bootstrap templates (what a target receives); `description:` (how a host triggers a skill); the READMEs beyond moved links |

Behaviour is kept: workflows, permissions, halts, schemas, identifiers. History — `CHANGELOG.md`,
`openspec/changes/archive/` — is left alone.

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | Action-first: short numbered steps, condition tables, a small ASCII flow for a branch or a state, an example where a format is ambiguous. Each rule once, where it binds; a reason stays beside its rule when it changes how the rule is applied | `P1`…`P13` applied to MF's own instructions. A rule without its *why* loses the edge case | A new shared-reference file or conditional loading — a structural change for its own version |

**Reader-local repetition stays:** the `I`, `P` and `T` carriers, each skill's change-id inference and gate
constants, and each station's own safety lines in its *Never* list. Shorter, not removed.

**The style anchor — converge Step 5, before → after.** Every phase writes to this.

Before, `skills/mf-converge/SKILL.md:292-318` at `a926ca1`, 389 words (`sed -n 292,318p skills/mf-converge/SKILL.md | wc -w`).

After:

```markdown
## Step 5 — Read the verdicts (your own reads, from disk)

Read each findings file yourself; a station's report is a claim about its file, and the file is the contract.
Write `verdicts` to the status log after each read. A file is **not clean** — halt, naming it — when:

| the findings file | why |
|---|---|
| is missing | a station that never ran, or crashed, cannot pass the loop |
| resolved zero files, or materially fewer files or commits than **this round's freeze** | a scope failure, indistinguishable from a real clean |
| is review's, and its Summary does not say the stale-claim pass ran | drift outside the diff went unsearched |
| is review's, and its Summary does not say the test-cost pass ran, and the coverage-trace pass ran or the freeze removed no test | the test passes went unrun |

**This round's freeze** is Step 2's in round 1 and Step 6's re-freeze after it, never round 1's once
superseded: a verify round over a one-file fix that reports one file is converging. A station that resolved zero
files writes `changes-requested` with one finding, *scope resolution failed*.

Non-blocking cards — review `drift` and `nit`, security `medium` and `low` — stay in the findings files until
Step 9, so pickup can fix them first. Both `clean`, both scopes matching → converged: go to Step 8.
```

After: 236 words (`awk '/^## Step 5 — Read the verdicts/,/go to Step 8.$/' design.md | wc -w`). Each rule of the before is in the after; nothing is added.

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | Interfaces stay byte for byte | Other stations, the principles, the spec, the backlog's cards and the structural tests cite them | Renaming while updating every consumer — the cost is review, the gain is nothing |

The interfaces:

- every `## Step N — Title` heading, every numbered precondition and its number, and every other `## ` heading;
- the `## Input contract`, `## Prose rules`, `## Rules for tests` and `## The card` tables — their ids and rule text;
- every path, command, event, frontmatter key, status, severity, card field, trailer and quoted line a station
  writes or matches (`converge: skipped — no findings files`, `Next: …`, `Change: <change-id>`);
- every `### Dn · …` heading in `docs/decisions.md` and every `###` heading in `docs/principles.md`;
- converge precondition 6 (`skills/mf-converge/SKILL.md:158-165`) and release precondition 8
  (`skills/mf-release/SKILL.md:93-100`), word for word: `0023·R7`, `R8`, `S1` and `S5` point there.

`sh openspec/changes/0029-terse-skills/kept.sh <path> <from> <to>` prints `kept` when lines `<from>`–`<to>` of
`<path>` at `a926ca1` still appear, line breaks and indents aside.

### D4

| id | decision | because | rejected |
|---|---|---|---|
| D4 | `rule_map.md` in this change's directory: a `## <path>` section per rewritten file, a row per rule, exception, halt or output | Review checks the diff against it; no removal is silent | A map in the commit bodies — scattered and unreviewable as one |

```markdown
## skills/mf-converge/SKILL.md

| old (section · lines at a926ca1) | rule, exception, halt or output | new (section) | disposition |
|---|---|---|---|
| Step 5 · 298-299 | a missing findings file is not clean; halt naming it | Step 5, the table | kept |
| Step 5 · 313-316 | non-blocking cards wait for Step 9, because pickup fixes some | Step 5, last paragraph | merged into one sentence |
| Step 3 · 185-189 | there is no simplify findings file | Step 3 | cut: redundant with `mf-build` Step 3 and `mf-release` precondition 4 |
```

`cut` names the reachable authority that still states the rule; a rule cut from a station must still reach that
station — through its own text, or a file it reads.

### D5

| id | decision | because | rejected |
|---|---|---|---|
| D5 | Measure each reading set before and after with `sh openspec/changes/0029-terse-skills/measure.sh`; no target | Shorter skills with a longer linked reading are no gain; a quota rewards cutting rules | A percentage target; a claim about tokens or a bill |

Before, at `a926ca1` — words and bytes, from `sh openspec/changes/0029-terse-skills/measure.sh`:

| reading set | files | words | bytes |
|---|---|---:|---:|
| shared | `AGENTS.md`, `docs/principles.md`, `docs/decisions.md` | 4,947 | 30,840 |
| cut | shared + `mf-cut-change` | 8,191 | 49,584 |
| build, native | shared + `mf-build` | 9,155 | 55,105 |
| build, generic | shared + `mf-build` + generic simplify | 9,399 | 56,706 |
| converge conductor | shared + `mf-converge` | 10,847 | 65,817 |
| review worker, generic | shared + `mf-converge` + generic review | 11,232 | 68,335 |
| security worker, generic | shared + `mf-converge` + generic security | 11,202 | 68,283 |
| release | shared + `mf-release` | 7,735 | 47,997 |
| bootstrap | `mf-bootstrap` | 732 | 4,518 |

A native review or security worker reads the shared context and its native engine, which MF does not ship. The
after table goes in phase 7's commit body, from the same command.

### D6

| id | decision | because | rejected |
|---|---|---|---|
| D6 | A fresh-reader check under a **reader contract**, run on Codex and Claude Code, old text against new | The new text must read one way for every reader; a green gate proves nothing about reading | One named CLI; a full execution run per case — unbounded cost |

**The reader contract.** A run counts when it is a fresh process — no resumed session — with no tools or
read-only, started in an empty directory; its one input is a prompt on stdin and its one output an answers file;
old and new run on the same executor, model and settings; and the answers file opens with a line naming the
executor, its version and the model.

```
questions/<skill>.md + text at a926ca1 | HEAD ──sh build_prompts.sh──▶ .minions/0029-reader/<skill>_<old|new>.prompt.md
                                                                                    │ any executor under the contract
                                    evidence/<executor>/<skill>_<old|new>.md ◀──────┘ ──▶ evidence/verdicts.md
```

**Recipes**, from an empty directory, for the installed executors:

| executor | command |
|---|---|
| Codex 0.163 | `codex exec -m gpt-6.1-sol -s read-only --ephemeral --skip-git-repo-check -o <answers> - < <prompt>` |
| Claude Code 2.1 | `claude -p --model claude-opus-5-5 --tools "" --no-session-persistence --output-format text < <prompt> > <answers>` |
| any other | meets the contract; its folder under `evidence/` and its rows in `verdicts.md` are added the same way |

**Judging.** `evidence/verdicts.md` has one row per executor × question:
`| <executor> | <skill> | <n> | <old: match or off> | <new: match or off> | <verdict> |`, the verdict `match`,
`off` or `bad question`. `off` is a new answer departing from the expected one; it halts, whatever another
executor answered. An old answer off the expected one marks the question `bad question`: noted and kept.

**The questions** are in `questions/<skill>.md`, without answers. The expected answers, from the text at
`a926ca1`:

| skill | n | expected answer |
|---|---|---|
| cut | 1 | Halt and ask for `version`; never infer it from the id (Parameters) |
| cut | 2 | Halt; never search for a brief (Parameters) |
| cut | 3 | Halt: the default branch must be clean (Step 1) |
| cut | 4 | Put it to the human with the evidence and wait; never overturn a settled decision alone (Step 3) |
| cut | 5 | Read every one and run none; rewrite one that cannot run as written; flag one that already holds, except a `**HALT CHECK**` (Step 8) |
| cut | 6 | No: show the dependencies word for word and wait for an OK for each package (Step 9) |
| cut | 7 | `skip_specs: true` in `.openspec.yaml`, plus `specs/.gitkeep` (Step 6) |
| cut | 8 | At most three sentences — the branch, the commit id, `git status --porcelain` printing nothing — then model suggestions; last line `Next: /mf-build <change-id>, in a fresh session.` (Step 11) |
| build | 1 | Halt, listing the active changes (Parameter) |
| build | 2 | A previous pass was interrupted: continue that phase against its acceptance, and say so in the report (Step 1) |
| build | 3 | Halt: the plan's premise broke; never change code to make it pass (Step 2) |
| build | 4 | Halt: never weaken the gate; only a deletion the design's `## Tests` table names is not weakening (Step 2, stop-conditions) |
| build | 5 | Halt: state the justification and stop for approval (stop-condition 4) |
| build | 6 | One commit per phase, staged by name, never `git add -A`; the message ends with `Co-Authored-By:` and `Change: <change-id>`, contiguous (Step 2) |
| build | 7 | Do none of its tasks; halt with the person's checklist — commands in `sh` blocks, `Closes when:`, `Next: /mf-build` (Step 2) |
| build | 8 | The simplify pass — native `/simplify` in Claude Code, generic otherwise — applies its fixes; the gate re-runs; red halts and nothing is committed over it (Step 3) |
| converge | 1 | Halt: the tree must be clean (Step 1, precondition 1) |
| converge | 2 | Halt: an empty range (Step 2) |
| converge | 3 | Not clean: halt, naming the missing path (Step 5) |
| converge | 4 | No: each round is judged against its own freeze, and one file over a one-file fix range is converging (Step 5) |
| converge | 5 | Only the checker, on its verify pass; the fixer touches no counter and never writes `verdict: clean` (Step 4, Step 6) |
| converge | 6 | Halt at the cap: leave every findings file as it stands, write nothing to the backlog, report the open blocking ids (Step 7) |
| converge | 7 | A catch-up round: freeze `<head>..HEAD`, one Step 7 verify round, then the backlog and the report — no pickup (Catch-up round) |
| converge | 8 | No: halt and say so (Executor and worker selection, Never) |
| release | 1 | Release with converge skipped, stating `converge: skipped — no findings files` in the report and the release commit (precondition 4, Step 4) |
| release | 2 | Halt: one findings file without the other (precondition 4) |
| release | 3 | Halt: run `/mf-converge` for its catch-up round (precondition 7) |
| release | 4 | Halt: the version line is not aligned (precondition 5) |
| release | 5 | Halt: commit nothing, tag nothing; report the staged fold and archive and the uncommitted changelog cut; reverting them is the human's (Step 4.3) |
| release | 6 | Print the merge and push commands, and stop (Step 5, Step 6) |
| release | 7 | Halt: the default branch moved (Step 5.1) |
| release | 8 | No: never edit feature code or tests; halt, naming the build as owner (Never, precondition 1) |
| bootstrap | 1 | Halt, naming every collision (Step 1) |
| bootstrap | 2 | Skip it; the file stays as it is (The files) |
| bootstrap | 3 | Halt: commit nothing; report the paths written (Step 3) |
| bootstrap | 4 | `chore: bootstrap for minionsfactory`, ending with `Co-Authored-By:` and no `Change:` trailer (Step 4) |

Expected-answer count: `grep -cE '^\| (cut|build|converge|release|bootstrap) \| [0-9] \|' openspec/changes/0029-terse-skills/design.md` prints `36`.

### D7

| id | decision | because | rejected |
|---|---|---|---|
| D7 | Converge runs | A dropped halt — the gate-recipe check — would let a weakened gate ship: silent wrong output, an anchor. Review's fresh read of `rule_map.md` against the diff is this change's real check | A hand read of the whole diff |

### D8

| id | decision | because | rejected |
|---|---|---|---|
| D8 | A minor, `v0.29`, that changes no station; it closes `0028·R4` with one MODIFIED requirement | `mf-release` cannot tag a patch; R4's trigger fires here, and the spec catches up with the skill | A patch; leaving R4 for a later opening of Steps 8–9 |

## Tests

No test is added, removed or merged; the structural tests and the gate recipe stay.

| layer | at cut | added | removed | proof |
|---|---:|---:|---:|---|
| Unit test functions | 18 | 0 | 0 | `uv run pytest -q --collect-only \| tail -1` prints `18 tests collected` |
| Integration tests | 0 | 0 | 0 | — |
| End-to-end runs | 0 | 0 | 0 | — |
| Fresh-reader runs, outside the gate | 0 | 20 | 0 | the skills × old and new × Codex and Claude Code; metered, never in CI |

## Dependencies

None.

## Risks / Trade-offs

- **A rule is dropped in rewriting** → the rule map, the kept interfaces, the reader check, and converge's review
  reading the map against the diff.
- **The simplify pass edits skill text after the reader check** → review judges those edits like any other, and
  reads them against the rule map.
- **A reader's answer is judged by a person** → the expected answers are fixed here, before the rewrite; converge's
  review re-reads `verdicts.md` against them.
- **An executor flag differs from its recipe** → the HUMAN phase uses the installed versions named above; another
  version is recorded in the answers file's first line.
- **Metered runs cost money** → bounded by the question sets and two executors, run once per side.

## Migration Plan

```
1 converge + generic review/security ─▶ 2 build + generic simplify ─▶ 3 cut ─▶ 4 release ─▶ 5 bootstrap
  ─▶ 6 AGENTS · principles · decisions ─▶ 7 measure + prompts ─▶ 8 the reader check · HUMAN · METERED
    ─▶ simplify ─▶ converge ─▶ release
```

Each phase ends on a green gate. Nothing is irreversible: a phase reverts with its commit.

## Verdict

Ready to build. Acceptance: the kept interfaces, a rule map covering every rewritten file, the reading sets
measured before and after, and no `off` row in `verdicts.md`.
