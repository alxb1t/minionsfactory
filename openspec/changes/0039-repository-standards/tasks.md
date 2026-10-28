# Repository standards — tasks

Build the settled [design](design.md), one phase at a time. The station and template text is the design's, word for
word.

## Progress

- [x] 1 — Read the standards in the build and converge
- [ ] 2 — Write the standards in the bootstrap
- [ ] 3 — Adopt the standards in MF
- [ ] 4 — Bootstrap a scratch repo **HUMAN**

## 1 — Read the standards in the build and converge

- [x] 1.1 Replace the context paragraph at `skills/mf-build/SKILL.md:12-13` with [D1](design.md#d1)'s after text.
  Verify: `grep -c 'CODE_STANDARDS.md' skills/mf-build/SKILL.md` prints `1`.
- [x] 1.2 Apply [D1](design.md#d1) to Step 3's input line in `skills/mf-converge/SKILL.md`, and to
  `skills/mf-converge/references/generic-review.md` and `skills/mf-converge/references/generic-security.md`.
  Verify: `grep -c 'CODE_STANDARDS.md' skills/mf-converge/SKILL.md` prints `1`, `grep -c 'root standards files' skills/mf-converge/references/generic-review.md skills/mf-converge/references/generic-security.md` prints `1` for each file, and `grep -c 'standards files is a' skills/mf-converge/references/generic-review.md` prints `1`.
- [x] 1.3 Rewrite rows `C1` and `C2` of `skills/mf-build/SKILL.md` and add the override sentence after `:295`, per
  [D2](design.md#d2).
  Verify: `grep -c 'No explanatory comment' skills/mf-build/SKILL.md` prints `1`, and ``grep -c 'names a `C` rule replaces it' skills/mf-build/SKILL.md`` prints `1`.

## 2 — Write the standards in the bootstrap

- [ ] 2.1 Write `skills/mf-bootstrap/templates/CODING_STANDARDS.md.tmpl` and
  `skills/mf-bootstrap/templates/CONTRIBUTING.md.tmpl`, per [D3](design.md#d3).
  Verify: `ls skills/mf-bootstrap/templates/CODING_STANDARDS.md.tmpl skills/mf-bootstrap/templates/CONTRIBUTING.md.tmpl` lists both.
- [ ] 2.2 Add *Read first* to `skills/mf-bootstrap/templates/AGENTS.md.tmpl` and point *How a change is cut here* at
  the guide, per [D3](design.md#d3).
  Verify: `grep -c '(CODING_STANDARDS.md)' skills/mf-bootstrap/templates/AGENTS.md.tmpl` prints `1`, and `grep -c '(CONTRIBUTING.md)' skills/mf-bootstrap/templates/AGENTS.md.tmpl` prints `2`.
- [ ] 2.3 Edit the description, the halt row and the collision precondition of `skills/mf-bootstrap/SKILL.md`, per
  [D3](design.md#d3).
  Verify: `grep -c 'CODE_STANDARDS.md' skills/mf-bootstrap/SKILL.md` prints `1`, and `grep -c 'CONTRIBUTING.md' skills/mf-bootstrap/SKILL.md` prints `2`.
- [ ] 2.4 Extend the layout scan and the Tests-section guard in `tests/test_skills.py`, and their breach tests' expected
  lists, per [D5](design.md#d5).
  Verify: `grep -c '_TEMPLATE_LINKS' tests/test_skills.py` prints `2`, and `uv run pytest -q tests/test_skills.py -k 'template or layout'` reports `4 passed`.
- [ ] 2.5 Amend D18's line, add D46 after D18 in `docs/decisions.md`, and add the sentence after the tree in
  `README.md`, per [D4](design.md#d4).
  Verify: `grep -c '^### D46 · ' docs/decisions.md` prints `1`, `grep -c 'CODING_STANDARDS.md' README.md` prints `1`, and `uv run --script scripts/metrics/references.py` prints `0`.

## 3 — Adopt the standards in MF

- [ ] 3.1 Write `CODING_STANDARDS.md` and `CONTRIBUTING.md` at the root, per [D6](design.md#d6).
  Verify: `wc -w CODING_STANDARDS.md CONTRIBUTING.md | tail -1` prints a total below `300`.
- [ ] 3.2 Edit `AGENTS.md`'s *The record* and add the rows to `docs/README.md`, per [D6](design.md#d6).
  Verify: `grep -c '(CODING_STANDARDS.md)' AGENTS.md` prints `1`, `grep -c 'Docs are written' AGENTS.md` prints `0`, and `grep -c '../CONTRIBUTING.md' docs/README.md` prints `1`.
- [ ] 3.3 Add both files to `scripts/metrics/reading_set.py` and `scripts/metrics/references.py`, and extend their
  tests in `tests/test_metric_scripts.py`, per [D7](design.md#d7).
  Verify: `grep -c 'CONTRIBUTING.md' scripts/metrics/reading_set.py scripts/metrics/references.py` prints `1` for each file, `uv run pytest -q tests/test_metric_scripts.py` reports `8 passed`, and `uv run --script scripts/metrics/references.py` prints `0`.

## 4 — Bootstrap a scratch repo **HUMAN**

The installed skills are `main`'s, so the scratch runs use this branch's bootstrap by path.

- [ ] 4.1 In this worktree, print the paths:
  `echo "WT=$(git rev-parse --show-toplevel)"; A=$(mktemp -d)/scratch_a; B=$(mktemp -d)/scratch_b; mkdir "$A" "$B"; touch "$B/CODE_STANDARDS.md"; echo "A=$A B=$B"`.
  Verify: `ls -A "$B"` prints `CODE_STANDARDS.md`.
- [ ] 4.2 Open a fresh agent session in `$A` and prompt `Run the skill at $WT/skills/mf-bootstrap/SKILL.md here.`,
  with `$WT` the printed value.
  Verify: `ls "$A/CODING_STANDARDS.md" "$A/CONTRIBUTING.md"` lists both, `make -C "$A" gate` exits 0, `git -C "$A" log --oneline | wc -l` prints `1`, and `grep -c '(CODING_STANDARDS.md)' "$A/AGENTS.md"` prints `1`.
- [ ] 4.3 Open a fresh agent session in `$B` and prompt the same.
  Verify: the session halts naming `CODE_STANDARDS.md`, and `ls -A "$B"` prints only `CODE_STANDARDS.md`.
