# Review inputs — tasks

Build the settled [design](design.md), one phase at a time. The station, template and decision text is the design's,
word for word.

## Progress

- [ ] 1 — Read the architecture decisions and the threat model
- [ ] 2 — Write them in the bootstrap
- [ ] 3 — Adopt the threat model in MF
- [ ] 4 — Bootstrap a scratch repo through an agent

## 1 — Read the architecture decisions and the threat model

- [ ] 1.1 Replace the context paragraph at `skills/mf-build/SKILL.md:12-15` with [D1](design.md#d1)'s after text.
  Verify: `grep -c 'THREAT_MODEL.md' skills/mf-build/SKILL.md` prints `1`, and `grep -c 'no task of the change amends' skills/mf-build/SKILL.md` prints `1`.
- [ ] 1.2 Replace the context paragraph at `skills/mf-cut-change/SKILL.md:18-19` with [D1](design.md#d1)'s after text.
  Verify: `grep -c 'THREAT_MODEL.md' skills/mf-cut-change/SKILL.md` prints `1`, and `grep -c 'design within the decisions in force' skills/mf-cut-change/SKILL.md` prints `1`.
- [ ] 1.3 Apply [D1](design.md#d1) to Step 3's input line in `skills/mf-converge/SKILL.md`, and to
  `skills/mf-converge/references/generic-review.md` and `skills/mf-converge/references/generic-security.md`.
  Verify: `grep -c 'THREAT_MODEL.md' skills/mf-converge/SKILL.md` prints `1`, `grep -c 'architecture decisions and threat model' skills/mf-converge/references/generic-review.md skills/mf-converge/references/generic-security.md` prints `1` for each file, and `grep -c "Read the target's threat model first" skills/mf-converge/references/generic-security.md` prints `1`.

## 2 — Write them in the bootstrap

- [ ] 2.1 Write `skills/mf-bootstrap/templates/THREAT_MODEL.md.tmpl` and `skills/mf-bootstrap/templates/docs/decisions.md.tmpl`,
  per [D2](design.md#d2).
  Verify: `ls skills/mf-bootstrap/templates/THREAT_MODEL.md.tmpl skills/mf-bootstrap/templates/docs/decisions.md.tmpl` lists both.
- [ ] 2.2 Add [D2](design.md#d2)'s sentence to *Read first* in `skills/mf-bootstrap/templates/AGENTS.md.tmpl`.
  Verify: `grep -c '(THREAT_MODEL.md)' skills/mf-bootstrap/templates/AGENTS.md.tmpl` prints `1`, and `grep -c '(docs/decisions.md)' skills/mf-bootstrap/templates/AGENTS.md.tmpl` prints `1`.
- [ ] 2.3 Edit the description, the halt row and the collision precondition of `skills/mf-bootstrap/SKILL.md`, per
  [D2](design.md#d2).
  Verify: `grep -c 'THREAT_MODEL.md' skills/mf-bootstrap/SKILL.md` prints `2`, and `grep -c 'ARCHITECTURE.md' skills/mf-bootstrap/SKILL.md` prints `1`.
- [ ] 2.4 Extend `_TEMPLATE_LINKS`, `_ALSO_WRITTEN` and both breach tests' expected lists in `tests/test_skills.py`, per
  [D5](design.md#d5).
  Verify: `grep -c '"(THREAT_MODEL.md)"' tests/test_skills.py` prints `1`, and `uv run pytest -q tests/test_skills.py -k 'template or layout'` reports `4 passed`.
- [ ] 2.5 Amend D18's line and add D48 after D46 in `docs/decisions.md`, per [D3](design.md#d3).
  Verify: `grep -c '^### D48 · ' docs/decisions.md` prints `1`, and `uv run --script scripts/metrics/references.py` prints `0`.

## 3 — Adopt the threat model in MF

- [ ] 3.1 Write `THREAT_MODEL.md` at the root, per [D4](design.md#d4).
  Verify: `wc -w < THREAT_MODEL.md` prints a number below `330`, and `grep -c '0040·S2' THREAT_MODEL.md` prints `1`.
- [ ] 3.2 Add [D4](design.md#d4)'s sentence to `AGENTS.md` and its row to `docs/README.md`.
  Verify: `grep -c '(THREAT_MODEL.md)' AGENTS.md` prints `1`, and `grep -c '../THREAT_MODEL.md' docs/README.md` prints `1`.
- [ ] 3.3 Add `THREAT_MODEL.md` to `scripts/metrics/reading_set.py` and `scripts/metrics/references.py`, and extend
  their tests in `tests/test_metric_scripts.py`, per [D4](design.md#d4) and [D5](design.md#d5).
  Verify: `grep -c 'THREAT_MODEL.md' scripts/metrics/reading_set.py scripts/metrics/references.py` prints `1` for each file, `uv run pytest -q tests/test_metric_scripts.py` reports `8 passed`, and `uv run --script scripts/metrics/references.py` prints `0`.

## 4 — Bootstrap a scratch repo through an agent

[D6](design.md#d6)'s probe: run from this worktree, under the shell rules — no `cd`; `uv run --directory` sets each
worker's cwd.

- [ ] 4.1 `mkdir -p ../mf_inputs_probe/fresh ../mf_inputs_probe/taken && touch ../mf_inputs_probe/taken/THREAT_MODEL.md`,
  then `uv run --directory ../mf_inputs_probe/fresh --script ../../minionsfactory/skills/mf-ship/scripts/conduct.py agent --executor claude "Run the skill at ../../v0.36_review_inputs/skills/mf-bootstrap/SKILL.md here."`.
  Verify: `ls ../mf_inputs_probe/fresh/THREAT_MODEL.md ../mf_inputs_probe/fresh/docs/decisions.md` lists both, `grep -c '(THREAT_MODEL.md)' ../mf_inputs_probe/fresh/AGENTS.md` prints `1`, and `git -C ../mf_inputs_probe/fresh log --oneline | wc -l` prints `1`.
- [ ] 4.2 `uv run --directory ../mf_inputs_probe/taken --script ../../minionsfactory/skills/mf-ship/scripts/conduct.py agent --executor claude "Run the skill at ../../v0.36_review_inputs/skills/mf-bootstrap/SKILL.md here."`.
  Verify: `ls ../mf_inputs_probe/taken` prints only `THREAT_MODEL.md`, and `grep -l 'THREAT_MODEL.md' ../mf_inputs_probe/taken/.minions/runs/agent-*.log` prints a path.
- [ ] 4.3 Delete the probe: `rm -rf ../mf_inputs_probe`.
  Verify: `test -e ../mf_inputs_probe` fails.
