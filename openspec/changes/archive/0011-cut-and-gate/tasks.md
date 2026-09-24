# 0011-cut-and-gate — tasks

**In one line:** four phases — `mf-release` gets simpler, the skills run `make gate`, `mf-build` gets its input
contract, and `mf-cut-change` is written. Each phase is one commit. The why of every task is in
[design.md](design.md); this page is the what and the check.

## Progress

- [x] 1 — `mf-release` drops its separate binding step
- [x] 2 — The skills run `make gate`
- [x] 3 — `mf-build` gets its input contract
- [x] 4 — `mf-cut-change`, the cut station

## 1 — `mf-release` drops its separate binding step

First, so no later commit ships a skill that runs a binding command read from an array it stopped reading
([D16](design.md#d16)). All edits are in `skills/mf-release/SKILL.md`, per [D4](design.md#d4).

- [x] 1.1 *Where the constants come from*: drop the spec-binding constant; the version file is the one constant
  that may be absent. Verify: `sed -n '/^## Where the constants/,/^## Step 1/p' skills/mf-release/SKILL.md | grep -c -i binding` prints `0`.
- [x] 1.2 Step 1, item 7: the tree is clean (`git status --porcelain` prints nothing), and nothing more.
  Verify: `grep '^7\. ' skills/mf-release/SKILL.md | grep -c -i binding` prints `0`.
- [x] 1.3 Step 2: add one line — a rename arrives as REMOVED (old title) + ADDED (new title); the fold has no
  rename operation. Verify: `grep -c 'old title' skills/mf-release/SKILL.md` prints `1`.
- [x] 1.4 Step 3 becomes `## Step 3 — Archive — staged, not committed`: move the change into the archive, stage
  the fold and the move by name, commit nothing (`R8`). Verify: `grep -c '^## Step 3 — Archive — staged, not committed' skills/mf-release/SKILL.md` prints `1`.
- [x] 1.5 Step 4, item 3: delete the closing sentence that points at Step 3's verification.
  Verify: `grep -c 'as Step 3 does' skills/mf-release/SKILL.md` prints `0`.
- [x] 1.6 Step 4, item 4: after staging by name, `git diff --quiet` must exit 0 and
  `git ls-files --others --exclude-standard` must print nothing, else halt (`R16`); after the commit,
  `git status --porcelain` prints nothing. Verify: with `sed -n '/^4\. \*\*Commit\*\*/,/^5\. /p' skills/mf-release/SKILL.md`
  piped to each, `grep -c 'git diff --quiet'`, `grep -c 'ls-files --others --exclude-standard'` and
  `grep -c 'After it, .git status --porcelain.'` each print `1`.
- [x] 1.7 *Never*: delete the post-fold binding line. Verify: `grep -c -i binding skills/mf-release/SKILL.md`
  prints `1`, and `grep -i binding skills/mf-release/SKILL.md | grep -c 'declared deviation'` prints `1` — no
  step of the skill runs a binding check; the one line naming it is Step 3's declared deviation from `docs/sdd.md`.

## 2 — The skills run `make gate`

The gate rule is [D1](design.md#d1); the copies of the gate are [D2](design.md#d2); the toml stays for the
runner only, per [D3](design.md#d3).

- [x] 2.1 Test first: create `tests/test_skills.py` with the gate scan and its bite test, both bound to
  `sdd:skills-gate:skills-run-make-gate` ([Seams](design.md#seams--what-the-tests-hold)).
  Verify: `uv run pytest tests/test_skills.py -q` fails, naming `minions.toml` in three skills.
- [x] 2.2 `skills/mf-build/SKILL.md`: Step 1 item 4 and Step 2 item 3 follow D1. Verify:
  `grep -c 'minions.toml' skills/mf-build/SKILL.md` prints `0`; `grep -c 'make -n gate' skills/mf-build/SKILL.md` prints `1` or more.
- [x] 2.3 `skills/mf-converge/SKILL.md`: *Where the constants come from* and preconditions 4–5 follow D1; Step 2
  item 3 runs `mkdir -p .minions/findings` first (`R6`). Verify: 2.2's two greps on this file, and
  `grep -c 'mkdir -p .minions/findings' skills/mf-converge/SKILL.md` prints `1`.
- [x] 2.4 `skills/mf-release/SKILL.md`: *Where the constants come from* follows D1.
  Verify: 2.2's two greps on this file.
- [x] 2.5 `.github/workflows/ci.yml`: the six `run:` steps become one, `run: make gate`. Verify:
  `grep -c 'run: make gate' .github/workflows/ci.yml` prints `1`; `grep -c 'run: uv ' .github/workflows/ci.yml` prints `0`.
- [x] 2.6 `Makefile`: a comment above `gate:`. `.minions/minions.toml`: the new comment, array untouched. Verify:
  `grep -c -i deprecated .minions/minions.toml` prints `1` or more; `git diff main -- .minions/minions.toml | grep -c '^[-+]  "'` prints `0`.
- [x] 2.7 `CLAUDE.md`, `README.md`, `openspec/config.yaml`: D2's rows. Verify:
  `grep -n 'minions.toml' CLAUDE.md README.md | grep -v -i -e deprecated -e runner` prints nothing;
  `grep -c -e 'six commands' -e 'six gate commands' CLAUDE.md openspec/config.yaml` prints `0` for both files.
- [x] 2.8 `docs/sdd.md`, `docs/architecture.md`: D2's rows. Verify: `grep -c -i -e 'minions.toml' -e 'the array' docs/sdd.md`
  prints `0`; `grep -n 'minions.toml' docs/architecture.md | grep -v -i -e deprecated -e runner` prints nothing.
- [x] 2.9 The gate scan passes. Verify: `uv run pytest tests/test_skills.py -q` exits 0.

## 3 — `mf-build` gets its input contract

All edits are in `skills/mf-build/SKILL.md`: the table is [The input contract](design.md#the-input-contract),
Step 1 is [D6](design.md#d6), Step 2 and the stop-conditions are [D7](design.md#d7).

- [x] 3.1 Add `## Input contract` after *Parameter*: rows `**I1**`…`**I15**`, columns *the change must* and
  *Step 1 checks it*. Verify: `grep -c '^| \*\*I[0-9]*\*\* |' skills/mf-build/SKILL.md` prints `15`.
- [x] 3.2 Step 1: check `I1`, `I4`, `I13`, `I14` first, halting with the id; narrow the dirty-tree rule. Verify:
  `sed -n '/^## Step 1/,/^## Step 2/p' skills/mf-build/SKILL.md | grep -c 'ls-files --error-unmatch'` prints `1`.
- [x] 3.3 Step 2: the HUMAN-phase rule. Verify:
  `sed -n '/^## Step 2/,/^## Step 3/p' skills/mf-build/SKILL.md | grep -c '\*\*HUMAN'` prints `1` or more.
- [x] 3.4 Step 2 item 2: tick each `N.M` once its check passes; a failed `**HALT CHECK**` halts. Verify:
  `sed -n '/^## Step 2/,/^## Step 3/p' skills/mf-build/SKILL.md | grep -c -e 'N.M' -e 'HALT CHECK'` prints `2` or more.
- [x] 3.5 Step 2 item 4: a CHANGELOG entry is 1–3 short lines, what changed and why. Verify:
  `grep -c 'the style of the entries already there' skills/mf-build/SKILL.md` prints `0`.
- [x] 3.6 Stop-condition 4: a package under `design.md`'s `## Dependencies` is added as listed; any other halts.
  Verify: `sed -n '/^## Stop-conditions/,/^## What you must NOT/p' skills/mf-build/SKILL.md | grep -c '## Dependencies'` prints `1` or more.
- [x] 3.7 **HALT CHECK** — this change meets `I1`. Verify:
  `git ls-files --error-unmatch openspec/changes/0011-cut-and-gate/tasks.md` exits 0, and `git branch --show-current` prints `v0.11_cut_and_gate`.
- [x] 3.8 **HALT CHECK** — this change meets `I4` and `I13`. Verify:
  `grep -c '^- \[.\] [0-9]* — ' openspec/changes/0011-cut-and-gate/tasks.md` prints `4`; `grep -c '^version: v0.11$' openspec/changes/0011-cut-and-gate/proposal.md` prints `1`.

## 4 — `mf-cut-change`, the cut station

The skill's body is [The cut, step by step](design.md#the-cut-step-by-step) and
[How the artifacts read](design.md#how-the-artifacts-read). Its sections, in order: *Parameters* · Step 1…11 ·
*Input contract* · *How the artifacts read* · *Never*.

- [x] 4.1 Test first: add the contract-ids scan and its bite test to `tests/test_skills.py`, bound to
  `sdd:input-contract:ids-agree`. Verify: `uv run pytest tests/test_skills.py -q` fails —
  `skills/mf-cut-change/SKILL.md` does not exist.
- [x] 4.2 Create `skills/mf-cut-change/SKILL.md` with `name: mf-cut-change` and a `description:` saying when to
  use it. It sits inside `tests/test_conventions.py`'s retired-vocabulary scan. Verify: `head -4 skills/mf-cut-change/SKILL.md`
  shows both keys inside a `---` block; `uv run pytest tests/test_conventions.py -q` exits 0.
- [x] 4.3 Write *Parameters* and the eleven steps, one `## Step N` heading each.
  Verify: `grep -c '^## Step [0-9]' skills/mf-cut-change/SKILL.md` prints `11`.
- [x] 4.4 Write `## Input contract`: rows `**I1**`…`**I15**`, each saying how the cutter meets and checks it.
  Verify: `grep -c '^| \*\*I[0-9]*\*\* |' skills/mf-cut-change/SKILL.md` prints `15`.
- [x] 4.5 Write `## How the artifacts read`: 16 numbered table rows, then the before → after example. Verify:
  `sed -n '/^## How the artifacts read/,/^## Never/p' skills/mf-cut-change/SKILL.md | grep -c '^| [0-9]* |'` prints `16`.
- [x] 4.6 Write `## Never`: the seven bullets in [design.md → Never](design.md#never).
  Verify: `sed -n '/^## Never/,$p' skills/mf-cut-change/SKILL.md | grep -c '^- '` prints `7`.
- [x] 4.7 `CLAUDE.md`: delete *How a change is cut here*; move its OpenSpec tooling sentence into *Layout*'s
  `openspec/` bullet; the `skills/` bullet names five skills. Verify: `grep -c -i 'how a change is cut here' CLAUDE.md`
  prints `0`; `grep -c 'fission-ai/openspec' CLAUDE.md` prints `1`.
- [x] 4.8 `openspec/config.yaml`: the `context:` line and the two rules that point at the deleted section state
  their facts directly — the `version:` frontmatter, and the `skip_specs` + `specs/.gitkeep` pair. Verify:
  `grep -c -i 'how a change is cut here' openspec/config.yaml` prints `0`; `openspec validate 0011-cut-and-gate --strict` exits 0.
- [x] 4.9 `README.md`: the skills section lists five skills, `mf-cut-change` first. Verify:
  `grep -c 'skills/mf-cut-change/SKILL.md' README.md` prints `1`; `make install-skills SKILLS_DIR="$(mktemp -d)"` prints five `linked` lines.
- [x] 4.10 The contract scan passes. Verify: `uv run pytest tests/test_skills.py -q` exits 0.
