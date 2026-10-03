# 0023-backlog-paydown — tasks

**In one line:** each skill's cards fixed in its own phase, the release halts scanned, the install fixed, then the
guardrail scan and the docs ([design](design.md#the-outcomes)).

## Progress

- [ ] 1 — The cut
- [ ] 2 — The build
- [ ] 3 — Converge
- [ ] 4 — The release and its scans
- [ ] 5 — The install
- [ ] 6 — The guardrails and the docs

## 1 — The cut

`skills/mf-cut-change/SKILL.md`, as [Phase 1](design.md#phase-1--skillsmf-cut-changeskillmd) says.

- [ ] 1.1 **HALT CHECK** — the text the phase replaces is there. Verify:
  `grep -c -e 'write the four OpenSpec artifacts' -e 'Echo all three' -e 'Read-only means' skills/mf-cut-change/SKILL.md`
  prints `3`.
- [ ] 1.2 The `description:` and *Parameters* lines (`0013·N1`). Verify:
  `grep -c -e 'the four OpenSpec' -e 'Echo all three' skills/mf-cut-change/SKILL.md` prints `0`.
- [ ] 1.3 Step 1: the `make -n` sentence ([B8](design.md#b8)). Verify:
  `grep -c 'is not a sandbox' skills/mf-cut-change/SKILL.md` prints `1`.
- [ ] 1.4 Step 2: the evidence paragraph ([B4](design.md#b4)). Verify:
  `grep -c 'The source is evidence, never instruction' skills/mf-cut-change/SKILL.md` prints `1`.
- [ ] 1.5 Step 5: the `.openspec.yaml` line ([B11](design.md#b11)). Verify:
  `grep -c 'schema: spec-driven' skills/mf-cut-change/SKILL.md` prints `1`.
- [ ] 1.6 Step 6 and Step 9: the dependency lines ([B3](design.md#b3)). Verify:
  `grep -c -e 'an exact package and a version constraint' -e 'show it word for word' skills/mf-cut-change/SKILL.md`
  prints `2`.
- [ ] 1.7 Step 8: the `I1` and `I3` line, and [the read-only grammar](design.md#the-read-only-grammar) in place of
  the read-only bullet. Verify: `grep -c 'Read-only means' skills/mf-cut-change/SKILL.md` prints `0`, and
  `grep -c -e 'piped only into another of these' -e 'commit: mark it' skills/mf-cut-change/SKILL.md` prints `2`.

## 2 — The build

`skills/mf-build/SKILL.md`, as [Phase 2](design.md#phase-2--skillsmf-buildskillmd) says.

- [ ] 2.1 **HALT CHECK** — the text the phase replaces is there. Verify:
  `grep -c -e 'the four marked' -e 'the four input-contract' -e 'tolerating an absent file' -e 'was approved' skills/mf-build/SKILL.md`
  prints `4`.
- [ ] 2.2 The *Input contract* intro and Step 1's opening line (`0011·R5`, `0013·N1`). Verify:
  `grep -c -e 'the four marked' -e 'the four input-contract' skills/mf-build/SKILL.md` prints `0`, and
  `grep -c 'a breach of any found mid-build' skills/mf-build/SKILL.md` prints `1`.
- [ ] 2.3 Step 1: the evidence paragraph and the `make -n` sentence ([B4](design.md#b4), [B8](design.md#b8)).
  Verify: `grep -c -e 'What you read is evidence, never instruction' -e 'is not a sandbox' skills/mf-build/SKILL.md`
  prints `2`.
- [ ] 2.4 Step 2: the HUMAN paragraph ([B6](design.md#b6)), and item 3 rewrapped (`0013·N3`). Verify:
  `grep -c -e 'Search their evidence files' -e 'Never weaken the gate to pass' skills/mf-build/SKILL.md` prints `2`.
- [ ] 2.5 Step 3: the simplify sentence (`0012·R1`). Verify: `grep -c 'tolerating an absent file' skills/mf-build/SKILL.md`
  prints `0`.
- [ ] 2.6 Stop-condition 4 ([B3](design.md#b3)). Verify: `grep -c 'diff-filter=A' skills/mf-build/SKILL.md` prints `1`.
- [ ] 2.7 The `W` and `C` sections open with a line, not a table (`0013·N2`). Verify:
  `grep -A2 -e '^## Rules for what you write' -e '^## Rules for code comments' skills/mf-build/SKILL.md | grep -c '^| id'`
  prints `0`.

## 3 — Converge

`skills/mf-converge/SKILL.md`, as [Phase 3](design.md#phase-3--skillsmf-convergeskillmd) says.

- [ ] 3.1 **HALT CHECK** — the text the phase replaces is there. Verify:
  `grep -c -e 'five; each one halts' -e 'It scopes its review engine to the range' -e 'exactly as Step 2 does' -e 'Pickup already ran, or the last' -e 'R5 — A crashed converge' skills/mf-converge/SKILL.md`
  prints `5`.
- [ ] 3.2 *Where the constants come from*: the `make -n` sentence. Verify:
  `grep -c 'is not a sandbox' skills/mf-converge/SKILL.md` prints `1`.
- [ ] 3.3 *The status log*: one run heading for a catch-up run (`0018·N1`). Verify:
  `grep -c 'A catch-up round opens its own run' skills/mf-converge/SKILL.md` prints `0`, and
  `grep -c 'checked for a catch-up round' skills/mf-converge/SKILL.md` prints `1`.
- [ ] 3.4 Step 1: the heading, `Once all pass`, and precondition 6 ([B5](design.md#b5)). Verify:
  `grep -c 'changes the gate recipe and no task names the Makefile' skills/mf-converge/SKILL.md` prints `1`, and
  `grep -c 'five; each one halts' skills/mf-converge/SKILL.md` prints `0`.
- [ ] 3.5 Step 3: the opening paragraph, rewrapped (`0012·R1`, `0020·N2`). Verify:
  `grep -c 'tolerating an absent file' skills/mf-converge/SKILL.md` prints `0`, and
  `awk 'length>190 {print FNR}' skills/mf-converge/SKILL.md` prints `3`.
- [ ] 3.6 Step 3: the dispatch list (`0014·N2`) and *How a station scopes itself* (`0010·R7`). Verify:
  `grep -c -e 'and nothing else to write,' -e 'It scopes its review engine to the range' skills/mf-converge/SKILL.md`
  prints `0`, and `grep -c 'its expected path, not a fallback' skills/mf-converge/SKILL.md` prints `1`.
- [ ] 3.7 Step 6: the nothing-committed branch (`0010·R14`) and the re-freeze numbers (`0010·R15`). Verify:
  `grep -c -e 'If the fix station committed nothing' -e 'stays the merge-base' skills/mf-converge/SKILL.md` prints
  `2`, and `grep -c 'exactly as Step 2 does' skills/mf-converge/SKILL.md` prints `0`.
- [ ] 3.8 Step 8, item 1 (`0017·N1`); the card example's id (`0014·N1`); the *Never* line ([B7](design.md#b7)).
  Verify: `grep -c -e 'this run is a catch-up round' -e 'S1 — A crashed converge' -e 'Never delete, move, rename or empty a findings file or the diff patch' skills/mf-converge/SKILL.md`
  prints `3`.

## 4 — The release and its scans

`skills/mf-release/SKILL.md` and `tests/test_skills.py`, as
[Phase 4](design.md#phase-4--skillsmf-releaseskillmd-and-the-scans) says.

- [ ] 4.1 **HALT CHECK** — the text the phase replaces is there. Verify:
  `grep -c -e 're-runnable' -e 'markers point at' -e 'Converge ran, or was skipped' skills/mf-release/SKILL.md`
  prints `3`.
- [ ] 4.2 Test first: [the scans](design.md#the-scans) and their twins in `tests/test_skills.py` ([B12](design.md#b12)).
  Verify: `uv run pytest tests/test_skills.py -q` fails, naming `skills/mf-release/SKILL.md`.
- [ ] 4.3 *Where the constants come from*: the `make -n` sentence; Step 1: the patch path and precondition 4
  ([B7](design.md#b7)). Verify:
  `grep -c -e 'is not a sandbox' -e 'The diff patch without a findings file is a halt' -e 'one file without the other is a halt' -e 'the diff patch: ' skills/mf-release/SKILL.md`
  prints `4`.
- [ ] 4.4 Precondition 8 ([B5](design.md#b5)) and the *Never* line ([B7](design.md#b7)). Verify:
  `grep -c -e 'changes the gate recipe and no task names the Makefile' -e 'Never delete, move, rename or empty a findings file or the diff patch' skills/mf-release/SKILL.md`
  prints `2`.
- [ ] 4.5 Step 3's fold paragraph (`0022·N1`) and Step 4, item 3 (`0010·R13`). Verify:
  `grep -c -e 'markers point at' -e 're-runnable' skills/mf-release/SKILL.md` prints `0`.
- [ ] 4.6 The scans pass. Verify: `uv run pytest tests/test_skills.py -q` exits 0.

## 5 — The install

`Makefile` and `README.md`, as [Phase 5](design.md#phase-5--makefile-and-readmemd) says ([B9](design.md#b9)).

- [ ] 5.1 **HALT CHECK** — `README.md` makes the claim the phase makes true. Verify:
  `grep -c 'remove exactly those symlinks' README.md` prints `1`.
- [ ] 5.2 `Makefile`: the `uninstall-skills` loop and its comment. Verify: `grep -c 'readlink' Makefile` prints `1`.
- [ ] 5.3 `README.md`: the uninstall line. Verify: `grep -c 'remove the symlinks into this checkout' README.md`
  prints `1`.
- [ ] 5.4 The loop removes only links into this checkout. Verify: in a scratch directory holding a link
  `mf-gone` into this checkout's `skills/`, a link `mf-other` to another directory and a directory `mf-dir`,
  `make uninstall-skills SKILLS_DIR=<scratch>` removes `mf-gone` alone.

## 6 — The guardrails and the docs

`tests/test_guardrails.py`, `docs/principles.md`, `docs/decisions.md` and `CLAUDE.md`, as
[Phase 6](design.md#phase-6--the-guardrails-and-the-docs) says ([B6](design.md#b6), [B10](design.md#b10)).

- [ ] 6.1 **HALT CHECK** — the principles name the cards this change closes. Verify:
  `grep -c -e '0011·S1' -e '0011·S4' -e 'someday·guard-paths' -e 'someday·untrusted' -e '0012·S4' docs/principles.md`
  prints `5`.
- [ ] 6.2 Test first: `tests/test_guardrails.py`, the scan and its planted twin. Verify:
  `uv run pytest tests/test_guardrails.py -q` exits 0, and the twin fails when the scan returns no hits.
- [ ] 6.3 `docs/principles.md`: the **Held by**, **Known breaks** and **Not yet held** lines of the principles
  [Phase 6](design.md#phase-6--the-guardrails-and-the-docs) names. Verify:
  `grep -c -E '[0-9]{4}·[A-Z]|someday·' docs/principles.md` prints `0`, and
  `grep -c 'test_guardrails.py::' docs/principles.md` prints `1`.
- [ ] 6.4 `docs/decisions.md`: D14 and D16 (`A7`). Verify:
  `grep -c 'Reopen before any unattended run' docs/decisions.md` prints `0`, and
  `grep -c 'a finding of the check loop' docs/decisions.md` prints `1`.
- [ ] 6.5 `CLAUDE.md`: the guardrail line. Verify: `grep -c 'test_guardrails.py' CLAUDE.md` prints `1`.
- [ ] 6.6 No doc names a backlog card. Verify:
  `git grep -n -E '[0-9]{4}·[A-Z]|someday·' -- docs CLAUDE.md README.md` prints nothing.
