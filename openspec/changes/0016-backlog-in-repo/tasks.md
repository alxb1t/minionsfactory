# 0016-backlog-in-repo — tasks

**In one line:** converge gets its backlog writer first, then the release stops reading the old file, then the export
is deleted. The why of each task is in [design.md](design.md).

## Progress

- [x] 1 — Converge picks up and writes the backlog
- [ ] 2 — The release stops reading the backlog
- [ ] 3 — The export retires

## 1 — Converge picks up and writes the backlog

The writer lands while the release still reads only the per-version file, so no release can block on the new
file ([D7](design.md#d7)). The text is in [D2–D3](design.md#d2d3--mf-converge-before--after).

- [x] 1.1 **HALT CHECK** — the release reads only the per-version file. Verify:
  `grep -c '\.minions/backlog\.md' skills/mf-release/SKILL.md` prints `0`, and
  `grep -c '<version>_backlog.md' skills/mf-release/SKILL.md` prints `1`.
- [x] 1.2 Test first: in `tests/test_skills.py`, add the converge backlog scan and its twin, bound to
  `sdd:repo-backlog:converge-writes-one-file` ([Seams](design.md#seams--what-the-tests-hold)).
  Verify: `uv run pytest tests/test_skills.py -q` fails, naming `skills/mf-converge/SKILL.md`.
- [x] 1.3 `skills/mf-converge/SKILL.md`: the `## Parameter`, Step 5, Step 6 and Step 7 rows of D2–D3.
  Verify: `grep -c '_backlog.md' skills/mf-converge/SKILL.md` prints `0`.
- [x] 1.4 `skills/mf-converge/SKILL.md`: add Step 8 — Pickup and Step 9 — Write the backlog; the report becomes
  Step 10. Verify: `grep -c -e '^## Step 8 — Pickup' -e '^## Step 9 — Write the backlog' -e '^## Step 10 — Report' skills/mf-converge/SKILL.md` prints `3`.
- [x] 1.5 `skills/mf-converge/SKILL.md`: the **Fix** row takes the closed size set of [D4](design.md#d4), and
  `## Never` gets the lines in the `## Never` row of D2–D3. Verify: ``grep -c '^| \*\*Fix\*\* |.*`one line and a test`' skills/mf-converge/SKILL.md`` prints `1`.
- [x] 1.6 The scans pass. Verify: `uv run pytest tests/test_skills.py -q` exits 0.

## 2 — The release stops reading the backlog

The text is in [D5–D6](design.md#d5d6--mf-release-and-mf-cut-change-before--after). The runner is not touched
([D9](design.md#d9)).

- [ ] 2.1 Test first: in `tests/test_skills.py`, add the release backlog scan and its twin, bound to
  `sdd:repo-backlog:release-does-not-read`. Verify: `uv run pytest tests/test_skills.py -q` fails, naming
  `skills/mf-release/SKILL.md`.
- [ ] 2.2 `skills/mf-release/SKILL.md`: delete precondition 5, renumber, and drop every count of preconditions, per
  the D5 rows. Verify: `grep -c -e '_backlog.md' -e 'seven' skills/mf-release/SKILL.md` prints `0`.
- [ ] 2.3 `skills/mf-release/SKILL.md`: add Step 4.6 — *Clear the paid-down cards* — and its Step 5 report item, per
  [D6](design.md#d6). Verify: `grep -c 'Clear the paid-down cards' skills/mf-release/SKILL.md` prints `1` or more,
  and `grep -c 'backlog: none' skills/mf-release/SKILL.md` prints `1` or more.
- [ ] 2.4 `skills/mf-cut-change/SKILL.md` Step 6: add the paydown bullet from the D6 row.
  Verify: `grep -c 'backlog: \[' skills/mf-cut-change/SKILL.md` prints `1`.
- [ ] 2.5 `docs/sdd.md`: *The findings contract* and *The release fold* take the `docs/sdd.md` row of
  [D7](design.md#d7--where-the-exports-name-leaves), with one sentence on the runner's divergence.
  Verify: `grep -c 'exported by the human' docs/sdd.md` prints `0`, and `grep -c '\.minions/backlog\.md' docs/sdd.md` prints `1` or more.
- [ ] 2.6 The scans pass. Verify: `uv run pytest tests/test_skills.py -q` exits 0.

## 3 — The export retires

The irreversible act, last ([D7](design.md#d7)). Every file is in
[D7 — where the export's name leaves](design.md#d7--where-the-exports-name-leaves).

- [ ] 3.1 **HALT CHECK** — only the expected files name the export. Verify:
  `git grep -l 'mf-backlog-export' -- . ':!openspec' ':!CHANGELOG.md'` prints exactly `README.md`,
  `skills/mf-backlog-export/SKILL.md`, `skills/mf-converge/SKILL.md` and `tests/test_skills.py`.
- [ ] 3.2 Test first: in `tests/test_conventions.py`, add `mf-backlog-export` as a retired needle with its scan and
  twin over `_SCANNED`, bound to `sdd:retired-export:named-nowhere`. In `tests/test_skills.py`, replace
  `_CARD_CARRIERS` and the parity scan with the card-owner scan and twin, keeping the key
  `sdd:backlog-cards:fields-agree` ([D8](design.md#d8)). Verify: `uv run pytest tests/test_skills.py tests/test_conventions.py -q` fails.
- [ ] 3.3 Delete `skills/mf-backlog-export/`. Verify: `test ! -e skills/mf-backlog-export` exits 0.
- [ ] 3.4 `skills/mf-converge/SKILL.md` `## The card`: the intro says no other skill carries the card.
  Verify: `grep -c 'mf-backlog-export' skills/mf-converge/SKILL.md` prints `0`.
- [ ] 3.5 `README.md`, `CLAUDE.md`, `.gitignore`: their D7 rows. Verify: `grep -c 'mf-backlog-export' README.md`
  prints `0`, `grep -c 'converge, backlog' CLAUDE.md` prints `0`, and `grep -c 'backlog.md' .gitignore` prints `1` or more.
- [ ] 3.6 No live mention remains. Verify:
  `git grep -l 'mf-backlog-export' -- . ':!openspec' ':!CHANGELOG.md' ':!tests'` prints nothing.
- [ ] 3.7 The scans pass. Verify: `uv run pytest tests/test_skills.py tests/test_conventions.py -q` exits 0.
