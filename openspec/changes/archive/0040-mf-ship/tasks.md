# mf-ship — tasks

Build the settled [design](design.md), one phase at a time. The station and decision text is the design's, word for
word; `conduct.py` and `SKILL.md` follow [D2](design.md#d2) and [D6](design.md#d6).

## Progress

- [x] 1 — Write the ship script
- [x] 2 — Give the release, the cut and integrate what an unattended run needs
- [x] 3 — Write the ship station and record it
- [x] 4 — Ship the probe **HUMAN · METERED**

## 1 — Write the ship script

- [x] 1.1 **HALT CHECK** Run [D1](design.md#d1)'s check in a scratch directory.
  Verify: its `cat probe.txt` prints `ok`.
- [x] 1.2 Write `skills/mf-ship/scripts/conduct.py` per [D2](design.md#d2): its commands, the stage table, the
  checks, the loop, the workers, the run log and the report.
  Verify: `uv run --script skills/mf-ship/scripts/conduct.py --help` exits 0, and `uv run --script skills/mf-ship/scripts/conduct.py --help | grep -c 'status,check,log,run,agent,report'` prints `1`.
- [x] 1.3 Write `tests/test_conduct.py` with the tests [Tests](design.md#tests) names, each over `tmp_path` repos and
  a fake agent through `MF_SHIP_AGENT`.
  Verify: `uv run pytest -q tests/test_conduct.py` reports `10 passed`.
- [x] 1.4 **HALT CHECK** Run one worker through the script from a worktree of a scratch container, `<c>`: a primary
  `<c>/p` declaring `Worktrees: ../`, a worktree `<c>/wt`:
  `c=$(cd "$(mktemp -d)" && pwd -P) && git init -q "$c/p" && printf -- '- **Worktrees:** `../`\n' > "$c/p/AGENTS.md" && git -C "$c/p" add AGENTS.md && git -C "$c/p" commit -q -m init && git -C "$c/p" worktree add -q -b wt "$c/wt" && cd "$c/wt" && uv run --script "$OLDPWD/skills/mf-ship/scripts/conduct.py" agent --executor claude "Run each command as its own Bash call: git commit --allow-empty -m second, then git push --force origin main, then write the word ok to $c/p/.minions/probe.txt. Do not try alternatives."; echo "$c"`.
  Verify: with `<c>` the printed path, `git -C <c>/wt log --oneline | wc -l` prints `2`, `cat <c>/p/.minions/probe.txt` prints `ok`, and `grep -l 'has been denied' <c>/p/.minions/runs/agent-*.log` prints a path.
- [x] 1.5 Give converge's prompt in `skills/mf-ship/scripts/conduct.py` the generic engines, per [D2](design.md#d2), with a step asserting it in
  `test_a_worker_carries_the_allowlist_and_a_denial_is_named`; name them in D47 of `docs/decisions.md` and in Step 3's `Say once:` of
  `skills/mf-ship/SKILL.md`: `converge runs the generic review and security engines`.
  Verify: `grep -c 'Use the generic review and security engines' skills/mf-ship/scripts/conduct.py` prints `1`, `grep -c 'generic review and security engines' docs/decisions.md skills/mf-ship/SKILL.md` prints `1` for each file, and `uv run pytest -q tests/test_conduct.py` reports `10 passed`.
- [x] 1.6 Give `skills/mf-ship/scripts/conduct.py` [D2](design.md#d2)'s converge and integrate check rows — a status-log halt fails
  converge's check; an open merge names its note or `.red` — with one step each in `test_each_check_passes_only_on_disk_evidence`; and the resumed `integrate` stage row, with one
  step in `test_status_reads_each_stage_from_disk`.
  Verify: `grep -c 'semantic conflict, see' skills/mf-ship/scripts/conduct.py` prints `1`, `grep -c 'diff-filter=U' skills/mf-ship/scripts/conduct.py` prints at least `1`, and `uv run pytest -q tests/test_conduct.py` reports `10 passed`.

## 2 — Give the release, the cut and integrate what an unattended run needs

- [x] 2.1 Apply [D3](design.md#d3) to `skills/mf-release/SKILL.md`.
  Verify: `grep -c '^## Parameter — merge' skills/mf-release/SKILL.md` prints `1`, and `grep -c 'removed, kept or refused' skills/mf-release/SKILL.md` prints `1`.
- [x] 2.2 Apply [D4](design.md#d4) to `skills/mf-cut-change/SKILL.md`.
  Verify: `grep -c 'models/<change-id>.toml' skills/mf-cut-change/SKILL.md` prints `1`, and `grep -c 'or into a tracked file' skills/mf-cut-change/SKILL.md` prints `1`.
- [x] 2.3 Apply [D5](design.md#d5) to `skills/mf-integrate/SKILL.md`.
  Verify: `grep -c '<change-id>.red' skills/mf-integrate/SKILL.md` prints `3`.
- [x] 2.4 Amend D17 and D41 in `docs/decisions.md`, per [D7](design.md#d7).
  Verify: `grep -c 'a merge nobody said yes to' docs/decisions.md` prints `1`, and `grep -c 'models/<change-id>.toml' docs/decisions.md` prints `1`.

## 3 — Write the ship station and record it

- [x] 3.1 Write `skills/mf-ship/SKILL.md` per [D6](design.md#d6).
  Verify: `grep -c '^name: mf-ship$' skills/mf-ship/SKILL.md` prints `1`, and `grep -c 'scripts/conduct.py' skills/mf-ship/SKILL.md` prints at least `1`.
- [x] 3.2 Add the `mf-ship` pair to `_METRICS_SCRIPTS` in `tests/test_skills.py`, and its line to both expected lists
  of `test_the_metrics_script_scan_reports_a_missing_script`, per [D6](design.md#d6).
  Verify: `grep -c '("mf-ship", "scripts/conduct.py")' tests/test_skills.py` prints `1`, and `uv run pytest -q tests/test_skills.py -k metrics_script` reports `2 passed`.
- [x] 3.3 Amend D3 and add D47 after D45 in `docs/decisions.md`, per [D7](design.md#d7).
  Verify: `grep -c '^### D47 · ' docs/decisions.md` prints `1`, `grep -c 'No station is reimplemented' docs/decisions.md` prints `1`, and `uv run --script scripts/metrics/references.py` prints `0`.
- [x] 3.4 Edit `README.md`, `AGENTS.md`, `CONTRIBUTING.md` and `docs/README.md`, per [D8](design.md#d8).
  Verify: `grep -c 'skills/mf-ship/SKILL.md' README.md` prints `1`, `grep -c 'designed, not built' README.md` prints `0`, `grep -c 'mf-ship' AGENTS.md CONTRIBUTING.md` prints `1` for each file, and `grep -c 'the bundled scripts' docs/README.md` prints `1`.

## 4 — Ship the probe **HUMAN · METERED**

One fresh session runs this checklist from MF's primary; each `Verify:` runs in this worktree. The probe is
[D9](design.md#d9)'s. Every agent step runs through `conduct.py agent`, under [D2](design.md#d2)'s allowlist:
each such command starts with `C=$(cd ../v0.35_mf_ship && pwd)/skills/mf-ship/scripts/conduct.py &&`, run from MF's
primary before any `cd`.

- [x] 4.1 The hand-over: open a fresh session in MF's primary and prompt
  `Run phase 4 of 0040-mf-ship's tasks.md, the checklist, step by step.`; read its report; then run
  `/mf-build 0040-mf-ship` in this worktree.
  Verify: `test -f openspec/changes/0040-mf-ship/evidence/probe_run.md` exits 0.
- [x] 4.2 Point the installed skills at this worktree: `make -C ../v0.35_mf_ship install-skills SKILLS_DIR=$HOME/.claude/skills`.
  Verify: `grep -c '^skills: v0.35_mf_ship$' openspec/changes/0040-mf-ship/evidence/probe_run.md` prints `1`.
- [x] 4.3 Make the probe: `mkdir -p ../mf_ship_probe/mf_ship_probe && cd ../mf_ship_probe/mf_ship_probe && uv run --script "$C" agent --executor claude "Run the mf-bootstrap skill."`.
  Verify: `grep -c '^bootstrap commits: 1$' openspec/changes/0040-mf-ship/evidence/probe_run.md` prints `1`.
- [x] 4.4 Write [D9](design.md#d9)'s prep edits in `../mf_ship_probe/mf_ship_probe`, then
  `git -C ../mf_ship_probe/mf_ship_probe add .gitignore Makefile AGENTS.md tests/test_smoke.py && git -C ../mf_ship_probe/mf_ship_probe commit -m "chore: a unittest gate and worktrees"`.
  Verify: `grep -c '^prep gate: exit 0$' openspec/changes/0040-mf-ship/evidence/probe_run.md` prints `1`.
- [x] 4.5 Write [D9](design.md#d9)'s briefs to `../mf_ship_probe/briefs/todo.md` and `../mf_ship_probe/briefs/marks.md`;
  then, in `../mf_ship_probe/mf_ship_probe`, `uv run --script "$C" agent --executor claude "Run the mf-cut-change skill: 0001-todo v0.1 brief=../briefs/todo.md"`
  and `uv run --script "$C" agent --executor claude "Run the mf-cut-change skill: 0002-marks v0.2 brief=../briefs/marks.md"`.
  Verify: `grep -c '^cuts: v0.1_todo v0.2_marks · models 0001-todo.toml 0002-marks.toml$' openspec/changes/0040-mf-ship/evidence/probe_run.md` prints `1`.
- [x] 4.6 In `../mf_ship_probe/mf_ship_probe`, `uv run --script "$C" agent --executor claude "Run the mf-ship skill."`; then wait until
  `test -d ../mf_ship_probe/mf_ship_probe/.minions/runs/active` fails. `ls ../mf_ship_probe/mf_ship_probe/.minions/runs/*.md`
  prints the run log's path.
  Verify: `grep -c '^run: done$' openspec/changes/0040-mf-ship/evidence/probe_run.md` prints `1`.
- [x] 4.7 Run the pass checks in `../mf_ship_probe/mf_ship_probe` and write their results to
  `openspec/changes/0040-mf-ship/evidence/probe_run.md` in this worktree, one line each and no absolute path:
  `skills: v0.35_mf_ship` · `bootstrap commits: 1` · `prep gate: exit 0` · `cuts: …` (4.5's line) · `run: done` ·
  `tags: <git tag -l, space-joined>` · `version merges: <git log --oneline main | grep -c "Merge branch 'v0">` ·
  `integrate commits: <git log --oneline main | grep -c 'chore(integrate)'>` · `worktrees: <git worktree list | wc -l>` ·
  `log --verify: exit <code of conduct.py log --verify on 4.6's log>` · `todo list: <python3 todo.py add milk && python3 todo.py list>`.
  Verify: `grep -c '^tags: v0.1.0 v0.2.0$' openspec/changes/0040-mf-ship/evidence/probe_run.md` prints `1`, and the same file holds `version merges: 2`, `integrate commits: 1`, `worktrees: 1`, `log --verify: exit 0` and `todo list: 1. milk`.
- [x] 4.8 However 4.2–4.7 ended, restore the skills: `make -C ../v0.35_mf_ship uninstall-skills SKILLS_DIR=$HOME/.claude/skills && make install-skills SKILLS_DIR=$HOME/.claude/skills`.
  Verify: `readlink ~/.claude/skills/mf-release` does not contain `v0.35_mf_ship`, and `test -e ~/.claude/skills/mf-ship` fails.
- [x] 4.9 Delete the probe: `rm -rf ../mf_ship_probe`.
  Verify: `test -e ../mf_ship_probe` fails.
