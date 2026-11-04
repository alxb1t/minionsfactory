# Gate hardening — design

The gate gets stricter and faster at once: parallel isolated tests and a quick check between phases, then pins, bug-pattern
and security lint, coverage on changed lines, a secret scan in the gate and at the push, and the same for a target's
bootstrap. Verdict at the end: ready to build.

## Context

Read at `40bd25e` (v0.52.0); `after: 0064-lighter-catch-up`, whose `gate_run.py` the stations gate through.

- **F1. The gate:** `uv sync --locked` · `ruff format --check` · `ruff check` · `ty check` · `pytest -q` (`Makefile:8-13`);
  Ruff selects `E F I D ANN` (`pyproject.toml:15`); dev group `pytest`, `ruff`, `ty` (`:7-12`); no markers, no coverage.
- **F2. CI** (`.github/workflows/ci.yml`): `actions/checkout@v4`, `astral-sh/setup-uv@v5` with Python 3.12, `make gate`; no
  `permissions`, no `timeout-minutes`, no `fetch-depth`.
- **F3. The guardrail:** `tests/test_guardrails.py:11-16` holds `_SHAPES` — a home path and four key shapes (Anthropic, GitHub,
  AWS, private key); `test_no_tracked_file_holds_a_home_path_or_a_key` (`:45`) and
  `test_the_guardrail_scan_reports_a_planted_path_and_key` (`:49`).
- **F4. The bootstrap's gate** is `openspec validate --all --strict --no-interactive` alone
  (`skills/mf-bootstrap/templates/Makefile.tmpl`); its preconditions (`skills/mf-bootstrap/SKILL.md:35-48`).
- **F5. The push:** `Run.push_left` → `Run.push`, each ref pushed from the conductor's scratch repo (`conduct.py:2493-2560`).
- **F6. The build's phase gate:** `skills/mf-build/SKILL.md:150`, "Run the full gate"; `I8` in both contract tables.
- **F7. The host:** 10 cores (`sysctl -n hw.ncpu`); `betterleaks version` prints `1.9.0`; `uv --version` prints `0.12.19`.

### The measurement

Taken at the cut in this worktree, no run competing for the CPU.

| step | time | command |
|---|---|---|
| `uv sync --locked`, `ruff format --check .`, `ruff check .`, `ty check` | under 1 s each | each, timed with `date +%s` |
| `pytest -q` | 378 s, `116 passed` | `uv run pytest -q --durations=30` |
| `betterleaks dir . --no-banner` | 1 s, no hit | the same |
| `pytest -q -n auto`, after phase 3, in the build | 107 s, `127 passed` | `make gate` |

Tests over 5 s, `uv run pytest -q --durations=30`: `test_a_forged_release_is_not_pushed` 60.9 s ·
`test_after_waits_for_its_dependency` 44.1 · `test_a_rerun_recovers_a_dead_release` 24.0 · `test_no_worker_pushes` 21.3 ·
`test_a_rerun_pushes_what_a_release_left` 18.5 · `test_a_run_pushes_only_tagged_merges` 15.4 ·
`test_a_local_release_is_pushed_when_origin_returns` 13.5 · `test_an_include_changed_on_the_branch_halts` (gate check) 11.8 ·
`test_a_run_goes_on_while_origin_is_down` 11.5 · `test_a_halted_dependency_blocks_a_chain` 10.5 ·
`test_a_changed_git_config_halts_a_merge_in` 10.4 · `test_a_ready_version_ships_past_a_slow_one` 8.2 ·
`test_a_new_executor_is_probed_mid_run` 7.9 · `test_each_check_passes_only_on_disk_evidence` 7.4 ·
`test_a_good_read_keeps_the_offline_base` 6.3 · `test_a_fixed_version_rejoins_a_live_run` 5.8 ·
`test_run_halts_when_a_worker_claims_what_disk_does_not_show` 5.2 — about 283 s of the 378.

`ruff check --select B,S --statistics .`: `S101` 1037 (assert, all in tests) · `S603` 38 · `S607` 24 · `B023` 14 · `B904` 1.

## Goals / Non-Goals

**Goals:** a full gate near the slowest test, a `make check` of seconds; no shared state between tests; pinned tools and CI;
bug-pattern and security lint; every changed line covered; no secret in the tree or a push; a target's bootstrap gate scanning.

**Non-Goals:** parallel gate steps; the targets' own gates changed; deptry, OSV-Scanner, agnix in MF's gate.

## Decisions

| id | decision | brief | rejected |
|---|---|---|---|
| [D1](#d1) | `pytest-xdist -n auto`; an autouse isolation fixture; `slow` above 5 s; `make check` | 20–27 | `make -j` (28: the other steps are under 1 s) |
| [D2](#d2) | `mf-build` runs `make check` after each phase but the last when `make -n check` exits 0; `I8` reworded | 21, 23 | a full gate per phase |
| [D3](#d3) | uv by `required-version`; CI pinned by SHA, `permissions`, `timeout-minutes`, `fetch-depth: 0`; `zizmor` in the gate | S1, 5, 12 | mise (S1) |
| [D4](#d4) | Ruff `B` and `S`; `S101` in tests, `S603`, `S607` ignored with a reason; `B023`, `B904` fixed; `--strict-markers` | 5 | — |
| [D5](#d5) | `coverage` over the parallel run, subprocesses patched; `diff-cover` at 100%, base `main` in a worktree, `origin/main` in CI | 4, 12, the cut | `origin/main` everywhere (an outage makes it lag local `main`) |
| [D6](#d6) | Betterleaks in the gate and in CI by checksum; operator tooling, a new decision; the guardrail's key shapes retire | 2, 3, 9, 11 | a baseline file |
| [D7](#d7) | `conduct.py` scans each push range from scratch, halts on a hit; a run stops at its start without Betterleaks | 2, 10 | a scan inside the primary's config |
| [D8](#d8) | The bootstrap: the scan and `check` in `Makefile.tmpl`, a `betterleaks version` precondition, the recipes in `CODING_STANDARDS.md.tmpl` | 6, 7, 17, 23, 24 | a stack's lines in the template |

### D1

`pytest-xdist` in the dev group; `-n auto` on the gate's and `check`'s pytest lines. `tests/conftest.py` holds an autouse fixture
setting `HOME`, `GIT_CONFIG_GLOBAL`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` under each test's `tmp_path`; a test
that then reaches a real home path, a fixed port or a global config is fixed to its own `tmp_path`. `slow` is registered in
`[tool.pytest.ini_options] markers`; each test in *The measurement* over 5 s carries `@pytest.mark.slow`. `make check` runs
`ruff format --check`, `ruff check`, `ty check` and `pytest -q -n auto -m "not slow"`.

### D2

`skills/mf-build/SKILL.md`'s phase gate: `make -n check` exits 0 → `make check` after each phase but the last, the gate after the
last; else the gate after each, as before. `I8` in `skills/mf-build/SKILL.md` and `skills/mf-cut-change/SKILL.md`: "let each phase
end on a green `make check`, the last on a green gate". A new test the builder writes that runs over 5 s carries `slow` — a line
beside `T1`, in both rule tables, and in `skills/mf-converge/SKILL.md`'s copy, which the fix station writes tests to.

### D3

`[tool.uv] required-version = ">=0.12.19,<0.13"` in `pyproject.toml`. `ci.yml`: `permissions: contents: read`;
`timeout-minutes: 20`; `actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0` with `fetch-depth: 0` and
`persist-credentials: false`; `astral-sh/setup-uv@d4b2f3b6ecc6e67c4457f6d3e41ec42d3d0fcb86 # v5.4.2` with `version: "0.12.19"`.
`zizmor` in the dev group and in the gate over `ci.yml`; each finding fixed or ignored in `ci.yml` with a reason.

### D4

`select` gains `B` and `S`; `per-file-ignores` — `"tests/**"` adds `S101` (pytest's asserts); `ignore` adds `S603` and `S607`, each
with a comment: `conduct.py`'s subprocesses are argv lists by design, and `git`, `make`, `uv` resolve on `PATH` by D8's precedent.
The `B023` and `B904` hits are fixed. `addopts = ["--strict-markers"]`.

### D5

`[tool.coverage.run]` — `parallel = true`, `patch = ["subprocess"]`, `source = ["skills", "scripts"]`; the gate runs
`coverage run -m pytest -q -n auto`, then `coverage combine -q`, `coverage xml -q`, then
`diff-cover coverage.xml --compare-branch=$(DIFF_BASE) --fail-under=100`, `DIFF_BASE ?= main` at the top of `Makefile`; CI runs
`make gate DIFF_BASE=origin/main`. A line left uncovered carries `# pragma: no cover` with its reason. `.coverage*` and
`coverage.xml` join `.gitignore`.

### D6

`betterleaks dir . --no-banner --redact` in the gate; `.betterleaks.toml` allowlists `.minions/` and each path `.gitignore`
names, each with a reason, and no tracked file, so the scan reads what git can track and a gitignored `.env` or `.venv/` never turns it red; it adds an
`aws-access-key-id` rule, a lone `AKIA` or `ASIA` id, which the retired shape caught and the default rule skips without its secret. CI
installs `betterleaks_1.9.0_linux_x64.tar.gz` from the `betterleaks/betterleaks` v1.9.0 release, checked against
`f8b185a39ffcece2a1ca82bf3a4e7435cd81963ffd16b7a9128daf75f35f6de7` with `sha256sum -c`, before `make gate`. `docs/decisions.md`
gains a decision: a gate tool off PyPI is operator tooling — on `PATH`, its version in `AGENTS.md` (`betterleaks 1.9.0`), installed
by exact version and checksum in CI. `AGENTS.md`'s gate line names the new steps. `_SHAPES` keeps the home path; the four key shapes
retire to the scan (the `## Tests` table).

### D7

`_scan(primary, base, sha)` runs `betterleaks git --no-banner --redact --ignore-gitleaks-allow --gitleaks-ignore-path=<scratch>
--exit-code 3 --log-opts='--remerge-diff <base>..<sha>' <scratch>` — `git log -p` prints no merge's diff, so a two-parent merge
is read by what it adds to the automatic merge of its parents; a clean merge adds nothing, so a hit names the commit that brought
the key — against `_scratch`'s bare repo borrowing the primary's objects, `GIT_CONFIG_NOSYSTEM=1` and `GIT_ATTR_NOSYSTEM=1`, so
no worker-written config or attributes — `diff.*.textconv` among them — run, and no `betterleaks:allow` or `gitleaks:allow`
comment and no ignore file in the conductor's folder, which a worker can write, hides a hit. git skips `--remerge-diff` for an
octopus merge and shows it no diff, so a commit `git rev-list --min-parents=3` lists in the range →
`Stop(1, "conduct: halt — the push range holds an octopus merge, which the scan cannot read: <commit>; nothing pushed")`;
MF's own merges take one branch. `Run.push` scans each heads ref's range before its first push; exit 3 →
`Stop(1, "conduct: halt — the push range holds a secret: <rule> in <file> at <commit>; nothing pushed")`, the report read with
`--report-format json`, redacted. `preconditions` stops with 2, `run: cannot run — betterleaks is not on PATH: brew install
betterleaks`. Pays `0051·S6`.

### D8

`Makefile.tmpl`'s `gate` adds `betterleaks dir . --no-banner --redact`, and a `check` target holds `openspec validate --all
--strict --no-interactive`; `.gitignore.tmpl` gains `.env`, `.venv/` and `node_modules/`, and `.betterleaks.toml.tmpl` allowlists
each path it names, as D6 does for MF; `skills/mf-bootstrap/SKILL.md` Step 1 adds `betterleaks version` runs. `CODING_STANDARDS.md.tmpl`
gains the recipes — Python: Ruff `B`/`S`, ty, deptry, `--strict-markers`, diff-cover; TS: `tsc`/`vue-tsc --noEmit`, Oxlint, knip,
vitest coverage and diff-cover on lcov; Docker: Hadolint — the any-stack rule (one tool per job from format, lint, types, tests with
coverage, security patterns, recorded in the target's `docs/decisions.md`), and the `slow` rule with `make check`.

## Tests

`uv run pytest -q --collect-only tests/` collects `116` at the cut. No end-to-end test (`T1`). The tests added, unit or
integration: `test_the_isolation_fixture_holds_home_under_tmp_path` (`T2`: a new fixture), `test_betterleaks_finds_a_planted_key`
(the scan's own twin, `T6`), `test_a_secret_in_the_push_range_halts_the_run` and `test_a_run_without_betterleaks_stops_at_start`
(new conductor paths), and a step in `test_the_bootstrap_templates_cover_the_target_layout`. Converge round 1 adds
`test_the_gate_scan_skips_what_git_ignores`, over MF's and the template's `.gitignore` and `.betterleaks.toml`, and a step in
`test_a_secret_in_the_push_range_halts_the_run` with a key only a merge commit adds; round 3 adds steps there with a key behind
an allow comment, a key an octopus merge adds and a key an ignore file in the conductor's folder names, and renames
`test_no_tracked_file_holds_a_home_path_or_a_key` and `test_the_guardrail_scan_reports_a_planted_path_and_key` to
`test_no_tracked_file_holds_a_home_path` and `test_the_guardrail_scan_reports_a_planted_path`, which check home paths alone.

| removed or merged | carried by |
|---|---|
| the Anthropic, GitHub, AWS and private-key shapes in `_SHAPES`, with their cases in `test_the_guardrail_scan_reports_a_planted_path_and_key` | `test_betterleaks_finds_a_planted_key`, which plants in `tmp_path`, scanned under the gate's `.betterleaks.toml`, an Anthropic key, a private key, a token per GitHub prefix (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`, `github_pat_`), a lone `AKIA` and `ASIA` id, and an id with its secret — and asserts the scan's exit and each file's rule id |

## Dependencies

| package | constraint | group | why |
|---|---|---|---|
| `pytest-xdist` | `>=3.8.0` | dev | the tests on every core (D1) |
| `coverage` | `>=7.17.1` | dev | coverage across the parallel run and its subprocesses (D5) |
| `diff-cover` | `>=11.0.1` | dev | 100% of changed lines (D5) |
| `zizmor` | `>=1.32.0` | dev | the CI workflow's lint (D3) |

Betterleaks `1.9.0` is operator tooling, never `uv add`ed (D6).

## Risks / Trade-offs

- **The slowest test sets the floor:** about 61 s; splitting it is a later change.
- **A slow test broken mid-build** surfaces at the build's last gate.
- **Coverage over subprocesses** may add test time; the build records the gate's time after phase 3 beside *The measurement*.
- **The push scan** needs Betterleaks on every machine that runs `mf-ship`; the start halts and names the install.

## Verdict

Ready to build.
