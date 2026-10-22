# Migrate to AGENTS.md — design

Make the instruction package portable; keep Claude Code's native engines. Verdict: ready to build.
Scope is [the proposal](proposal.md); behavior is [the delta](specs/sdd/spec.md).

## Context

Premises were rechecked on `main` at `bba6569` before the cut. New paths below are explicit deliverables,
not claims that they already exist.

| evidence at the cut | implication |
|---|---|
| Root `CLAUDE.md` imports `@docs/principles.md` | A rename needs an explicit read instruction, not an import assumption |
| `skills/mf-bootstrap/templates/CLAUDE.md.tmpl` holds `## Tests` | Rename the template without losing its test policy |
| `tests/test_skills.py` uses `_CLAUDE_TEMPLATE` and `_layout_problems` | Update the template guard and layout fixture together |
| `docs/decisions.md` D8 and D18 name the old context | Edit the decisions where they live |
| `Makefile` defaults `SKILLS_DIR` to the Claude directory | Change the destination, not the gate recipe |
| Build Step 3 invokes `/simplify`; converge Step 3 invokes adopted engines | Add generic branches without replacing native behavior |
| Converge Step 7 omits the design from its dispatch | Close `0026·N1` when changing worker dispatch |
| Cut Step 6 says "Each entry" after Tests and Dependencies | Close `0026·N2` with "Each dependency" |
| Release's close-out and principles' gate paragraph exceed their wrapping convention | Close `0026·N3` |
| The latest release is `v0.26.0`; no active change exists | Cut `v0.27`, `0027-migrate-to-agents` |

Zed's native agent and external ACP agents are different executors. Its native agent supports shared skills,
`AGENTS.md` and fresh workers; ACP capabilities belong to the external agent, not to the editor.

Primary sources: [Zed agent paths](https://zed.dev/docs/ai/agents),
[Zed skills](https://zed.dev/docs/ai/skills), [Zed instructions](https://zed.dev/docs/ai/instructions),
[Zed fresh-worker source](https://github.com/zed-industries/zed/blob/main/crates/agent/src/tools/spawn_agent_tool.rs),
[Pi worker example](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/examples/extensions/subagent/README.md).
These establish documented capabilities, not a completed run on those hosts.

## Goals / Non-Goals

**Goal:** an installed skill package can conduct the existing line on a capable executor without Claude commands.
The generic path changes engine instructions, not the findings, gate, phase or release contracts.

**Non-goals:** see [the exclusions](proposal.md#not-in-this-change). Host adapters, authentication and a new
autonomous runner are outside the package.

## Decisions

The grilling settled these choices; the build does not reopen them.

### D1

| id | decision | because | rejected |
|---|---|---|---|
| D1 | `AGENTS.md` is the context contract | The operator migrates target repos manually | Fallback names, shims, duplicate context |

Rename root `CLAUDE.md` to new `AGENTS.md` and its bootstrap template to new
`skills/mf-bootstrap/templates/AGENTS.md.tmpl`. Preserve their content except the agreed migration edits.

The root context explicitly says to read `docs/principles.md` and `docs/decisions.md` before work.
Cut, build, converge and release explicitly read root `AGENTS.md`; missing context halts naming it.
Bootstrap writes it into a new target and keeps its existing collision behavior.

Update `openspec/config.yaml`, `README.md`, `docs/README.md`, the live skill references and the template/layout
guards in `tests/test_skills.py`. Replace `_CLAUDE_TEMPLATE` with `_AGENTS_TEMPLATE` while retaining the existing
test functions and their assertions.

### D2

| id | decision | because | rejected |
|---|---|---|---|
| D2 | Route by executor evidence; report the selected path | Editor, provider and model do not identify the agent host | Model-name inference, silent native fallback |

Build checks the engine needed for its final simplify pass before production edits. Converge checks its engine
and worker needs before checker dispatch. Check only the native commands needed by that station; this adds no
general Claude command exposure.

```
executor positively identified as Claude Code?
  yes -> required native command invocable? -> yes -> existing native path
                                         -> no  -> halt; user may explicitly select generic for that run
  no  -> report generic -> load the bundled role instruction
```

Claude Code keeps `/simplify`, `/code-review` and `/security-review`, with existing engine scope and restrictions.
Native missing-command and missing-remote limitations remain native limitations; they do not block generic
security, which receives the explicit range.

An unidentified executor uses generic instructions and says so. A Claude model running through OpenRouter,
Codex through Zed ACP, and Zed's native agent use the generic path.
MF skill names identify instructions; each host uses its supported loading/invocation syntax.

### D3

| id | decision | because | rejected |
|---|---|---|---|
| D3 | Bundle generic role instructions beside their skills | Personal skill symlinks carry the complete package | New plugin dependency, copied proprietary prompts, a runtime router |

Add these new Markdown resources and strong conditional links from their owning `SKILL.md` files:

| owner | new resource | remit |
|---|---|---|
| `skills/mf-build/SKILL.md` | `skills/mf-build/references/generic-simplify.md` | Change-scoped complexity and duplication reduction, preserving behavior |
| `skills/mf-converge/SKILL.md` | `skills/mf-converge/references/generic-review.md` | Correctness, spec, standards and tests |
| `skills/mf-converge/SKILL.md` | `skills/mf-converge/references/generic-security.md` | Concrete vulnerabilities, exposure, unsafe permissions and trust boundaries |

Simplify applies improvements inside build before the final checker freeze. Review and security write their
own findings and leave production edits to the fix station. The conductor reads results from disk.

Generic workers receive base/head IDs, the range, patch, target context, change artifacts, role resource,
findings path and applicable backlog. They inspect source around the diff, report what they resolved and halt
when their inputs cannot support a verdict.

The existing card, severity, counter, reviewed-head, repeat, stale-claim, test-cost, coverage-trace and red-run
contracts remain authoritative in converge. Resources point to that contract rather than create another copy.
At verification, review receives the design's `## Tests` table as well as its findings and the fix range.

Generic security includes relevant prompt and tool instructions. It needs evidence of a concrete defect rather
than a speculative category list; repo content cannot grant tool authority or declare its own checks passed.
It requires neither a remote nor a native review plugin.

### D4

| id | decision | because | rejected |
|---|---|---|---|
| D4 | Accept fresh subagents and fresh agent processes | Isolation is the invariant; APIs vary by host | Inherited build history, self-review, installing an integration |

The worker gets explicit task inputs and shared files, not the build transcript. Every checker and verification
worker starts fresh; role identity persists through its findings file, not a resumed conversation.
The conductor must be able to dispatch, wait for completion and read the named output on shared disk.

Claude Code retains parallel dispatch. Generic execution prefers parallel workers and accepts sequential workers
on the same frozen head; both finish before a fixer starts. If independent workers cannot run, halt naming the
capability instead of opening an unobservable sibling thread or reviewing inline.

### D5

| id | decision | because | rejected |
|---|---|---|---|
| D5 | Default `SKILLS_DIR` to `$(HOME)/.agents/skills` | It is shared by the intended executors | Host auto-detection, moving existing installations |

Change the assignment and its comment in `Makefile`; keep the override, symlink semantics, collision refusal and
checkout-specific uninstall. The gate recipe is unchanged.

### D6

| id | decision | because | rejected |
|---|---|---|---|
| D6 | Use offered models and supported controls; keep provider setup external | Hosts expose different model menus and effort controls | Invented model names, universal effort levels |

Change the cutter's suggestion wording to honor a target menu in `AGENTS.md` and the session's actual menu.
With no model menu, describe the capability needed; with no effort control, omit that setting.
Do not select a different model or configure a provider.

Edit `docs/decisions.md` where choices live: D8 for context, D11 for conditional engines, D13 for generic simplify,
D18 for target layout, and D22 for operator-owned authentication and deployment terms.
Record the worker and portable-suggestion choices there with new stable decision IDs after the existing IDs.

Update `docs/principles.md` and root context consistently. Installed skills and their bundled references are
instruction-package material, not permission to read arbitrary files outside a target; project inputs and outputs
remain repo-bound, with the existing read-only CI exception.

### D7

| id | decision | because | rejected |
|---|---|---|---|
| D7 | Prove the generic path live in Codex; hand-read native dispatch | Text scans cannot establish instruction compliance | Model calls in CI, untested universal compatibility claims |

Run the [smoke protocol](#smoke-protocol) after the resources exist. It tests a disposable fixture, not the
implementation diff, so it does not replace this change's later independent converge.
Record sanitized evidence under [Smoke evidence](#smoke-evidence); keep raw run output gitignored.

### D8

| id | decision | because | rejected |
|---|---|---|---|
| D8 | Test resource integrity at the unit layer | A deployable package must carry the files its branches load | Paragraph-presence tests, a standing retired-name blacklist |

The new `_resource_problems` helper in `tests/test_skills.py` inspects actual local Markdown targets beginning
`references/` in each shipped `SKILL.md`. Resolve each target against the referring skill's directory and reject
a missing file, whitespace-only content or a resolved path outside that directory.

Ignore illustrative links such as `[design](design.md)` and external URLs. The fixture twin exercises valid,
missing, empty and escaping targets, including a real file outside the skill that must still be rejected.
This is a package guard, not an attempt to prove prompt semantics with matching words.

### D9

| id | decision | because | rejected |
|---|---|---|---|
| D9 | Preserve historical references; use a one-time retirement inventory | Old releases genuinely used the old context | Rewriting history, a permanent absence test |

The build inventories tracked `CLAUDE.md` and old installation-path mentions with `git grep -n` and classifies
each as fixed or kept in its phase commit. Keep `CHANGELOG.md`, `openspec/changes/archive/`, this change's
migration evidence and the living old requirement until release folds the delta.

Root and template renames are reversible in Git. There is no irreversible data migration and no compatibility
bridge to remove later; proving the migrated package precedes its release.

## Tests

The gate remains offline. Extend the existing template/layout fixtures; add the resource guard and its twin.
No test is deleted or merged, so the `I16` removal mapping is not applicable.

| layer / evidence | at cut | added | removed | proof / reason |
|---|---:|---:|---:|---|
| Unit test functions | 60 | 2 | 0 | AST count below; new names are listed below |
| Integration tests | 0 | 0 | 0 | Existing suite uses unit helpers and temporary files |
| Browser end-to-end runs | 0 | 0 | 0 | No browser behavior is introduced |
| Live agent smoke | 0 | 1 | 0 | Codex generic pass sequence; acceptance outside CI |
| Native dispatch review | 0 | 1 | 0 | Hand read against the base, recorded as evidence |

Count command, run at the cut:

```sh
python3 - <<'PY'
import ast
from pathlib import Path
for path in sorted(Path('tests').glob('test_*.py')):
    names = [n.name for n in ast.parse(path.read_text()).body
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith('test_')]
    print(f'{path}: {len(names)} tests')
PY
```

Output: `tests/test_guardrails.py: 2 tests`, `tests/test_principles.py: 2 tests`,
`tests/test_skills.py: 56 tests`. Proposed additions are the named functions below; no browser matrix is added.
The smoke is an agent workflow, not a browser test, and cannot be replaced by a text assertion (`T1`).

| test | disposition | scenario carried |
|---|---|---|
| `test_the_bootstrap_holds_its_template_tests_section` | Retain; update its target constant | Migrated template preserves the test policy |
| `test_the_template_tests_scan_reports_a_wrong_heading` | Retain | The template guard rejects a wrong heading |
| `test_the_bootstrap_templates_cover_the_target_layout` | Retain | D18's layout matches packaged templates |
| `test_the_layout_scan_reports_every_breach` | Retain; update its fixture | Missing AGENTS template is diagnosed |
| `test_bundled_role_references_resolve` | Add in `tests/test_skills.py` | Shipped resource targets are usable |
| `test_resource_scan_reports_missing_empty_and_escaping_targets` | Add in `tests/test_skills.py` | Invalid targets are rejected; valid and illustrative links are handled |

Planned addition count: `python3 -c 'from pathlib import Path; print(sum("| Add in `tests/test_skills.py` |" in line for line in Path("openspec/changes/0027-migrate-to-agents/design.md").read_text().splitlines() if line.startswith("| `test_")))'` prints `2`.
The live acceptance count is the fixture sequence above the [native dispatch review](#native-dispatch-review),
not a new gate test; no paid model call is added to a CI recipe.

## Smoke protocol

Use `.minions/0027-smoke/target/` as the disposable repo and `.minions/0027-smoke/` for transcripts.
Run it with the installed Codex executor after phase 2; use the configured model, without installing packages
or changing provider settings. Missing Codex execution, authentication or independent workers is a halt.

### Fixture

Create a Git repo on `main`, without a remote, and commit the correct baseline below. Use repo-local commit
identity `MF Smoke <smoke@example.invalid>` through command flags, leaving the operator's Git config alone.
Create branch `v0.1_smoke`, introduce the seeded changes, and commit them before the role exercise.

| fixture file | baseline / required content | seeded change |
|---|---|---|
| `AGENTS.md` | Test-only target; gate is `make gate`; follow `README.md` behavior; no external effects | Unchanged |
| `README.md` | `label` trims its name; `invoice_total` sums cents exactly; `notes_for` returns only notes owned by the given user | Unchanged |
| `notes.py` | Functions shown below | Functions shown below |
| `test_notes.py` | Stdlib `unittest` cases for `label(True, ' x ')` and `label(False, ' x ')`, both equal `'x'` | Unchanged until the fix |
| `Makefile` | `gate:` with tab-indented `python3 -m unittest -v` | Unchanged |
| `.gitignore` | `.minions/` and `__pycache__/` | Unchanged |
| `openspec/changes/0001-smoke/proposal.md` | `version: v0.1` frontmatter; fixture-only change scope | Add with the seeded change |
| `openspec/changes/0001-smoke/design.md` | Tests table naming future `test_invoice_total` and `test_notes_for`; no test removals | Add with the seeded change |
| `openspec/changes/0001-smoke/tasks.md` | Checked `## Progress` phase for this prepared fixture | Add with the seeded change |

Baseline `notes.py`:

```python
def label(owner, name):
    return str(name).strip()


def invoice_total(cents):
    return sum(cents)


def notes_for(user, notes):
    return [note for note in notes if note["owner"] == user]
```

Seeded `notes.py`:

```python
def label(owner, name):
    if owner:
        result = str(name).strip()
        return result
    else:
        result = str(name).strip()
        return result


def invoice_total(cents):
    return sum(cents) + 1


def notes_for(user, notes):
    return list(notes)
```

The initial fixture gate remains green: it covers label behavior but deliberately lacks the seeded regressions.
Never relax an assertion when a role flags the defect it was intended to expose.

### Live Codex exercise

Start a new Codex session, not resume or fork, with the fixture as its workspace. Supply only the acceptance
task, fixture paths and installed role resources; do not pass the production build transcript.
The installed CLI supports this invocation shape, checked at the cut:

```sh
codex exec -C .minions/0027-smoke/target --sandbox workspace-write --approve-for-me --ephemeral --json - < .minions/0027-smoke/runner-prompt.md > .minions/0027-smoke/codex-events.jsonl
```

Generate the gitignored `runner-prompt.md` at run time. It explicitly selects the generic resources built in
phase 2, names the fixture repository and its change artifacts, and instructs this sequence:

The coordinator keeps the expected seed findings as its acceptance key. Checker inputs contain the fixture
source/spec, resource and findings contract, not the seed key, fix snippets, this protocol or the producer's
conversation; capture those dispatch inputs as freshness evidence.

1. Load generic simplify, apply behavior-preserving label simplification, run the fixture gate and commit its edits.
2. Freeze the baseline-to-current range; write its patch into the fixture's `.minions/findings/`.
3. Dispatch fresh review and security workers with their resources, explicit range/context and own findings paths.
   Both complete before a fix; each writes the normal findings contract for `0001-smoke`.
4. Require review to identify the incorrect invoice total and security to identify the cross-user note exposure.
   Read actual cards and source evidence; a worker summary alone is insufficient.
5. Dispatch a fresh fixer. Add `test_invoice_total` expecting `[100, 250]` to total `350`, and `test_notes_for`
   expecting user `a` to receive only the `a` note from notes owned by `a` and `b`.
6. Capture the fixture tests failing against the seeded functions, then fix those functions, capture green and commit.
7. Start new review and security workers with the fix range, their own findings and the fixture design's Tests table.
   They verify or reopen findings; neither the fixer nor the conductor writes `verified`.
8. Read their on-disk verdicts; pass the smoke only when the seeded defects are verified and no blocking finding remains.

This acceptance exercise is not the station's final simplify or convergence on `0027`; those retain their normal
owners. If a role misses a seed, cannot preserve its boundary or cannot produce its artifact, record failure and
halt for the plan problem rather than have the builder manufacture a clean file.

### Native dispatch review

Read build and converge against `bba6569`. Record that Claude Code still invokes native `/simplify`,
`/code-review` and `/security-review`; native scoping, parallel dispatch and restrictions remain; missing commands
halt; generic worker serialization and no-remote support apply to the generic branch.
This is a hand review, not a claim that the Claude engines were run.

### Smoke evidence

The build appends the actual result here after the live exercise. Record the Codex executor/version, available
model identity, generic route, resource revisions, fixture base/head IDs, worker freshness/dispatch method,
findings paths/IDs, red/green exits and fresh verification verdicts.

Link the gitignored transcript and findings using repo-relative links. Include sanitized excerpts sufficient to
explain the result; omit home paths, repository-root expansions, credentials and private configuration.
Record the native hand review separately; do not label Zed/OpenRouter, Pi or Claude Code live-tested by this run.

Status at cut: not run. No worker finding, gate result or compatibility verdict is pre-certified here.

## Transition execution

This one-change handoff bootstraps Codex before the migrated `mf-build` exists. It is not a permanent fallback
and does not weaken the new product contract.

In a fresh Codex session on `v0.27_migrate_to_agents`, read the proposal, this design and the complete tasks.
Locate the cut commit with `git log --diff-filter=A --format=%H -- openspec/changes/0027-migrate-to-agents/design.md`;
require a single result and read that commit's `skills/mf-build/SKILL.md` as the fixed build ritual and rule source.

Apply these explicit transition instructions:

- Read the existing root `CLAUDE.md` before phase 1; after its rename read `AGENTS.md` and mandatory linked context.
  This exception applies to this migration only, not to any shipped skill or another target repo.
- Follow the cut-time build's `I`, `W`, `T`, `P` and `C` rules, input checks, stop conditions and per-phase ritual.
  Resume from disk; execute every task check; run the gate; update CHANGELOG and checkboxes; commit each phase by name.
- Do not invoke Claude-native commands from Codex. After phase 2 exists, use the new generic-simplify resource for
  the final own-change simplify pass required by the build ritual, after the phase-3 fixture exercise is complete.
- Keep simplify edits in their own trailered commit and rerun the full gate; report a no-op honestly if it changes
  nothing. The fixture's checker exercise does not authorize self-review of the production change.
- Fresh workers for the fixture smoke are authorized. Stop after the build; do not converge, release, tag, merge
  or push the production change. The now-migrated `mf-converge` is the next station in a fresh session.

No dependency is approved beyond [Dependencies](#dependencies). If a premise breaks, halt with evidence rather
than amend a settled decision or skip the smoke. Never write a machine path or a model recommendation into tracked prose.

## Cut self-check

The cutter records its completed checks here before committing. `I1` completes with the cut commit.
`P9`, `P12`, `P13` and `A2` were read: linked decisions, named deliverables, short tasks and explicit exclusions.

| item | status | evidence |
|---|---|---|
| I1 | at commit | Own version branch from clean `main`; commit and final status are reported in chat |
| I2 | met | `openspec validate 0027-migrate-to-agents --strict` exited 0 |
| I3 | met | `make gate` exited 0 on the staged cut; 60 tests passed; final annotation is rechecked before commit |
| I4 | met | Tasks Progress and phase/sub-task shape |
| I5 | met | Read every Verify without running it; the pre-existing CLI help check is explicitly HALT CHECK |
| I6 | met | Named files, linked decisions and single-reading tasks |
| I7 | met | Template and layout guards named in phase 1 |
| I8 | met | Context/template guards together; resources/guard together; smoke last |
| I9 | met | Old template requirement removed with migration; replacement and added behavior in the delta |
| I10 | met | Existing paths/symbols and retained test names rechecked against `bba6569`; new deliverables labeled |
| I11 | met | Dependencies is None |
| I12 | met | No own-change station ritual duplicated as a task; fixture smoke is acceptance |
| I13 | met | Proposal starts with version v0.27 |
| I14 | not applicable | No HUMAN phase; installed Codex runs the fixture; missing capability halts |
| I15 | met | Phase-3 capability premise is marked HALT CHECK |
| I16 | met | No test deletions or merges |

## Dependencies

None.

## Risks / Trade-offs

- **Host availability differs** -> check actual executor capabilities; an editor label is insufficient.
- **Generic review quality differs by model** -> require evidence-bearing cards and record actual smoke outcomes.
- **Instruction-level write boundaries are not an OS sandbox** -> preserve role restrictions and use host controls
  when available; this change does not claim to build a new enforcement boundary.
- **Installed resources live outside a target** -> resolve from the installed skill package; do not infer a cwd path.
- **Native command catalogs vary** -> halt on the needed missing command; no automatic generic fallback in Claude Code.
- **Historical names remain searchable** -> classify retained evidence in the one-time retirement inventory.
- **The smoke needs configured Codex access** -> halt if absent; no credential or provider installation step is added.

## Migration Plan

```
1 context + templates + existing guard fixtures
  -> 2 conditional engines + bundled roles + resource guard
    -> 3 Codex fixture evidence + native hand review + retirement inventory
      -> normal build simplify -> independent converge -> release
```

Each phase ends under the normal build ritual on a green gate. Rollback is Git revert of the phase commits;
the cut itself writes no production migration and performs no irreversible act.
The release folds the delta and closes the declared backlog cards under its existing rules.

## Verdict

Ready to build on the agreed scope. Acceptance is green structure checks plus observed generic behavior,
with native dispatch preserved by a hand read and no unobserved host marked tested.
