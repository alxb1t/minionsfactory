# Host-free tests — design

A fix in `tests/` for each leak of the host into a test, with no change under `skills/` or `scripts/`. Verdict: ready to build, in the phase of [tasks](tasks.md).

## Context

CI's Linux gate runs `make gate`, which runs `uv run coverage run -m pytest -q -n auto` (`Makefile:22`) with `patch = ["subprocess"]` (`pyproject.toml:27-29`). The patch sets coverage's variables in the test process, so a Python child of a test starts coverage too.

The conductor's sandboxed command keeps every variable but `VIRTUAL_ENV` and the tokens (`skills/mf-ship/scripts/conduct.py:3451-3455`), so the variables reach the sandboxed child. Under a real sandbox its coverage cannot write its data file, and its traceback joins the output the tests compare whole. The `real_sandbox` fixture clears no variable (`tests/test_sandboxed.py:694-703`).

The other leak is the host's `PATH`. `_executor_missing("codex")` is true when `MF_SHIP_AGENT` is unset and `PATH` holds no `codex` (`skills/mf-ship/scripts/conduct.py:4306-4308`). `test_a_checker_on_another_host_is_planned_and_probed` and `test_a_checker_falls_back_when_the_weekly_window_is_spent` take `tmp_path` alone and expect Codex planned and ready; they pass where `codex` is installed and fail on CI.

Why no run saw either: the Mac's gate runs inside the build's sandbox, where `sandbox-exec` cannot nest and the real-sandbox tests skip; CI's macOS job runs them without coverage; the Mac has Codex. The proof of this change is CI's Linux gate after the push, read by the person: the build's own gate skips the real-sandbox tests.

## Goals / Non-Goals

- Goal: the real-sandbox tests pass under `coverage run` on a host whose `PATH` holds no `codex`.
- Goal: each fix has a case that fails when the fix is removed, held where no real sandbox applies.
- Non-goal: any change to production's environment, to `ci.yml`, or to the fixtures `fake_codex` and `fake`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The `real_sandbox` fixture clears `COVERAGE_PROCESS_START` and `COVERAGE_PROCESS_CONFIG` through a helper `_clear_coverage` | a target's own gate must keep its coverage; the child of a test is the test's concern | the conductor dropping them from a sandboxed command's environment: it changes production for a test; running the gate without coverage in CI |
| [D2](#d2) | The two Codex tests take the `fake_codex` fixture | it is the suite's one way to put a fake `codex` and `claude` on `PATH` | setting `MF_SHIP_AGENT` by hand in each; patching `_executor_missing`; installing Codex in CI |
| [D3](#d3) | One test holds `_clear_coverage` over each variable alone, with no real sandbox | a fixture that skips under the build's sandbox must still be held by the gate; one case per conjunct (`W5`) | a test that starts a real sandboxed child: it skips where the fix is needed |

### D1

`_clear_coverage(monkeypatch)` calls `monkeypatch.delenv(name, raising=False)` for `COVERAGE_PROCESS_START` and `COVERAGE_PROCESS_CONFIG`. `monkeypatch.delenv` restores them at the test's end, so a later test under the same gate keeps its coverage. The fixture calls it after setting the host's side and before `_require_sandbox`, so it runs when the test then skips.

`COVERAGE_FILE` and the rest stay: only the variables that start coverage in a child go.

### D2

The fixture `fake_codex` builds on `fake`, which sets `MF_SHIP_AGENT` at setup (`tests/test_conduct.py:277-298`), and puts a fake `codex` and `claude` first on `PATH` (`tests/test_conduct.py:301-327`). Neither test calls its setter: the tests need the fixture's environment, not its modes. Each takes `@pytest.mark.usefixtures("fake_codex")` and gains no parameter.

### D3

The test sets one variable, calls `_clear_coverage`, and asserts the variable is gone from `os.environ` and `COVERAGE_FILE` is kept. It runs once for each variable. It needs no sandbox, so it runs on the Mac's gate too.

## Tests

One unit test added, in `tests/test_sandboxed.py`; none removed, merged or moved; no end-to-end test added. The `I16` table has no row.

| layer | before | after | command |
|---|---|---|---|
| unit, `tests/test_sandboxed.py` | 31 functions | 32 | `git grep -c "^def test_" -- tests/test_sandboxed.py` |
| unit, `tests/test_conduct.py` | 217 functions | 217 | `git grep -c "^def test_" -- tests/test_conduct.py` |
| end-to-end runs added | 0 | 0 | none: no browser, no engine |

| new test | layer | why not lower or merged |
|---|---|---|
| `test_a_real_sandbox_child_starts_no_coverage` | unit, a case for each variable | the helper is the lowest layer that can fail for a variable left in the environment; no existing test reaches it (`T1`, `T2`) |

Its twin is the case itself: with the helper's `delenv` removed the variable stays in `os.environ` and the test fails (`T6`).

## Dependencies

None.

## Risks / Trade-offs

- A real-sandbox test passing on CI is read after the push, never by the build: the build's sandbox skips them. A test red there after this change gets a second patch.
- `fake_codex` makes `MF_SHIP_AGENT` set at setup, so each Codex test passes with or without a real `codex` on the host's `PATH`. It reads Codex's readiness from the fake, which is what the tests assume.
- The helper names the variables as literals: a later coverage release that names a third variable shows as a red real-sandbox test on CI.

## Verdict

Ready to build as one phase of [tasks](tasks.md). No decision of `docs/decisions.md` is added or overturned.
