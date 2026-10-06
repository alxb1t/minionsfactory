# 0024-bootstrap — tasks

**In one line:** the skill and its templates, proved by scratch runs; the layout scan; the amended decisions and
the front door. The text is in [design.md](design.md).

## Progress

- [x] 1 — The skill
- [x] 2 — The layout scan
- [x] 3 — The record

## 1 — The skill

The skill and its templates, then [the scratch runs](design.md#the-scratch-runs) in `/tmp`, each by a fresh
sub-agent.

- [x] 1.1 **HALT CHECK** — the skill does not exist yet. Verify: `test -e skills/mf-bootstrap; echo $?` prints `1`.
- [x] 1.2 Write [the templates](design.md#the-templates) under `skills/mf-bootstrap/templates/`
  ([B2](design.md#b2), [B6](design.md#b6), [B9](design.md#b9), [B10](design.md#b10)). Verify:
  `find skills/mf-bootstrap/templates -type f | sort` prints the `.gitignore.tmpl`, `CHANGELOG.md.tmpl`,
  `CLAUDE.md.tmpl`, `Makefile.tmpl`, `README.md.tmpl`, `openspec/changes/archive/.gitkeep.tmpl`,
  `openspec/config.yaml.tmpl` and `openspec/specs/.gitkeep.tmpl` paths, and nothing else.
- [x] 1.3 The `Makefile` template's recipe line starts with a tab. Verify:
  `grep -c "^$(printf '\t')openspec validate --all --strict --no-interactive$" skills/mf-bootstrap/templates/Makefile.tmpl`
  prints `1`.
- [x] 1.4 Write [the skill](design.md#the-skill) to `skills/mf-bootstrap/SKILL.md` ([B1](design.md#b1)–[B8](design.md#b8)).
  Verify: `uv run pytest tests/test_skills.py -q -k gate` exits 0, and
  `grep -c '^## Step 5 — Report$' skills/mf-bootstrap/SKILL.md` prints `1`.
- [x] 1.5 The [**empty** run](design.md#the-scratch-runs). Verify:
  `cd /tmp/mf-bootstrap-empty && make gate >/dev/null && make -n gate && git status --porcelain && git rev-list --count HEAD && git check-ignore -q .minions/x && echo ignored`
  prints `openspec validate --all --strict --no-interactive`, `1` and `ignored`.
- [x] 1.6 The [**github** run](design.md#the-scratch-runs) ([B5](design.md#b5)). Verify:
  `cd /tmp/mf-bootstrap-github && git diff --quiet HEAD~1 HEAD -- README.md && grep -c '^\*\.pyc$' .gitignore && grep -c '^\.minions/$' .gitignore && make gate >/dev/null && echo green`
  prints `1`, `1` and `green`.
- [x] 1.7 The [**again** run](design.md#the-scratch-runs). Verify:
  `cd /tmp/mf-bootstrap-empty && git status --porcelain && git rev-list --count HEAD` prints `1`.
- [x] 1.8 The [**cut** run](design.md#the-scratch-runs). Verify: `git -C /tmp/mf-bootstrap-empty branch --list v0.1_hello`
  prints `v0.1_hello`, and `ls /tmp/mf-bootstrap-empty/openspec/changes/0001-hello` lists `design.md`, `proposal.md`,
  `specs` and `tasks.md`.

## 2 — The layout scan

- [x] 2.1 Add [the scan](design.md#the-scan) to `tests/test_skills.py`: `_layout_problems`,
  `test_the_bootstrap_templates_cover_the_target_layout` and `test_the_layout_scan_reports_every_breach`
  ([B11](design.md#b11)). Verify: `uv run pytest tests/test_skills.py -q -k layout` exits 0 and reports
  `2 passed`.

## 3 — The record

The decisions in force and the front door, word for word from [design.md](design.md#the-amended-decisions)
([B12](design.md#b12)). A wrapped line is checked joined: `tr -s '\n ' ' ' < <file>` turns the file into one line.

- [x] 3.1 **HALT CHECK** — the text to amend reads as design quotes it. Verify:
  `grep -c 'it installs nothing into the repo it works on' docs/decisions.md`,
  `grep -c 'They install nothing into it' docs/decisions.md`,
  `grep -c 'or CI runs it. The cut runs' docs/decisions.md` and
  `grep -c 'the skills install nothing into it' README.md` each print `1`.
- [x] 3.2 `docs/decisions.md`, D2. Verify:
  `tr -s '\n ' ' ' < docs/decisions.md | grep -c 'The stations install nothing into the repo they work on'` prints
  `1`, and `grep -c 'it installs nothing into the repo it works on' docs/decisions.md` prints `0`.
- [x] 3.3 `docs/decisions.md`, D8: the bold paragraph and the added bullet. Verify:
  `tr -s '\n ' ' ' < docs/decisions.md | grep -c 'writes validates the specs'` prints `1`, and
  `tr -s '\n ' ' ' < docs/decisions.md | grep -c 'a new target has no CI to turn red'` prints `1`.
- [x] 3.4 `docs/decisions.md`, D18: the bold line and the added bullet. Verify:
  `tr -s '\n ' ' ' < docs/decisions.md | grep -c 'writes it once into a new repo'` prints `1`,
  `tr -s '\n ' ' ' < docs/decisions.md | grep -c 'the layout scan in'` prints `1`, and
  `grep -c 'They install nothing into it' docs/decisions.md` prints `0`.
- [x] 3.5 `docs/decisions.md`, D21. Verify:
  `tr -s '\n ' ' ' < docs/decisions.md | grep -c 'bootstrap commit, made before any change exists, is the one without it'`
  prints `1`.
- [x] 3.6 `README.md`: the skills table's first row, and *What a target repo needs*. Verify:
  `grep -c 'skills/mf-bootstrap/SKILL.md' README.md` prints `1`,
  `tr -s '\n ' ' ' < README.md | grep -c 'writes it into a new repo; the other skills install nothing'` prints `1`,
  and `grep -c 'the skills install nothing into it' README.md` prints `0`.
- [x] 3.7 `CLAUDE.md`, the `skills/` line. Verify: `grep -c 'bootstrap, cut, build, converge, release' CLAUDE.md`
  prints `1`.
