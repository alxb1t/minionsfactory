"""The models file: its parser, key readers, hash, writer and text, pinned by key.

Why: 0142-models design D3; the turned cases: its D4 to D10.
"""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from conduct_load import conduct as _conduct
from fake_worker import _commit, _done, _git
from mflib import layout, modelsfile, statefile

_REPO = Path(__file__).resolve().parent.parent
_BRIEF_CHECK = _REPO / "skills" / "mf-plan" / "scripts" / "brief_check.py"
_CHANGE = "0001-todo"
_FILE = f"conduct: halt — changes/{_CHANGE}/models.toml"
_CHILD_SECONDS = 10
_HASH_IN_CHILD = """
import sys
from pathlib import Path

sys.path[:0] = sys.argv[1:3]
from mflib import modelsfile

try:
    print(modelsfile.digest(Path(sys.argv[3]), sys.argv[4]))
except modelsfile.Broken as error:
    print(error)
"""
_EVERY_PART: str = (
    "build codex/gpt-6.1-sol high · converge claude-opus-5-5 high"
    " · release claude-sonnet-5-5 medium · cut claude-opus-5-5 high"
    " · build-moderate claude-sonnet-5-5 high · conformance codex/gpt-6.1-sol high"
    " · adversarial claude/claude-opus-5-5 high · fix claude-opus-5-5 medium · shadow"
)
_EVERY_TABLE = (
    'decide = "recommended"\n\n'
    '[build]\nmodel = "gpt-6.1-sol"\neffort = "high"\nexecutor = "codex"\n\n'
    '[build.moderate]\nmodel = "claude-sonnet-5-5"\neffort = "high"\n\n'
    '[converge]\nmodel = "claude-opus-5-5"\neffort = "high"\nshadow = true\n\n'
    '[converge.conformance]\nmodel = "gpt-6.1-sol"\neffort = "high"\n'
    'executor = "codex"\n\n'
    '[converge.adversarial]\nmodel = "claude-opus-5-5"\neffort = "high"\n'
    'executor = "claude"\n\n'
    '[converge.fix]\nmodel = "claude-opus-5-5"\neffort = "medium"\n\n'
    '[release]\nmodel = "claude-sonnet-5-5"\neffort = "medium"\n'
)
_DEFAULTS = ("claude", None, None)


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("brief_check", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


brief_check = _load(_BRIEF_CHECK)


@pytest.fixture
def conduct() -> dict[str, Any]:
    """Return a fresh load of the conductor: a test may patch its globals."""
    return _conduct()


def _models_toml(primary: Path, text: str | bytes, change: str = _CHANGE) -> Path:
    """Write `text` as the change's `models.toml` under `primary`; return its path."""
    path = layout.change_dir(primary, change) / "models.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_text(text)
    return path


def _repo(tmp_path: Path) -> Path:
    """Return a primary checkout on `main` whose versions live beside it."""
    root = tmp_path / "main"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    agents = (
        "- **Worktrees:** `../` — a version's worktree is `<this path>/<branch>`.\n"
    )
    _commit(root, {".gitignore": ".minions/\n", "AGENTS.md": agents}, "base")
    return root.resolve()


# why: the conductor's classes load at run time and have no static type.
def _version(conduct: dict[str, Any], root: Path, change: str = _CHANGE) -> Any:  # noqa: ANN401
    """Cut `change` in a linked worktree, its one phase unticked; return its version."""
    tree = root.parent / change
    _git(root, "worktree", "add", "-q", "-b", change, str(tree))
    folder = f"openspec/changes/{change}"
    files = {
        f"{folder}/proposal.md": "---\nbump: minor\n---\n",
        f"{folder}/tasks.md": "## Progress\n\n- [ ] 1 — Todo\n",
    }
    _commit(tree, files, f"cut {change}")
    return conduct["Version"](change, tree.resolve())


def _cut(tmp_path: Path, change: str = "0001-a") -> Path:
    """Return a clean primary whose branch `change` ends on its cut commit."""
    root = _repo(tmp_path)
    _git(root, "switch", "-q", "-c", change)
    files = {f"openspec/changes/{change}/proposal.md": "---\nbump: minor\n---\n"}
    _commit(root, files, f"docs({change}): land the change directory")
    _git(root, "switch", "-q", "main")
    return root


def _queue(primary: Path, change: str, models: str | None) -> None:
    """Queue `change`'s cut as `conduct.py cut` does, its entry holding `models`."""
    entry: dict[str, object] = {
        "bump": "minor",
        "brief": "/brief.md",
        "after": [],
        "executor": "claude",
        "model": None,
        "effort": None,
        "halt": None,
    }
    if models is not None:
        entry["models"] = models
    folder = layout.queue_cuts(primary)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / change).write_text(json.dumps(entry))


def _hash_in_child(primary: Path, change: str) -> str | None:
    """Return what the module's digest prints in a child; None when it was killed."""
    paths = [str(_REPO / "tests"), str(_REPO / "skills")]
    child = subprocess.Popen(
        [sys.executable, "-c", _HASH_IN_CHILD, *paths, str(primary), change],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        out, _ = child.communicate(timeout=_CHILD_SECONDS)
    except subprocess.TimeoutExpired:
        child.kill()
        child.communicate()
        return None
    return out.strip()


def _writer(conduct: dict[str, Any]) -> Callable[[Path, str, str], None]:
    """Return the cut's write of the models file: the module's, a failure a `Stop`."""

    def write(primary: Path, change: str, text: str) -> None:
        try:
            modelsfile.write(primary, change, text)
        except statefile.WriteFailed as error:
            raise conduct["_unwritten"](change, error) from None

    return write


def _open_fds() -> int:
    return len(os.listdir("/dev/fd"))


def _brief(tmp_path: Path, head: str, line: str) -> Path:
    brief = tmp_path / "brief.md"
    brief.write_text(f"## For the cut\n1. {head}\n   - models: {line}\n")
    return brief


def _printed(brief: Path, slug: str, capsys: pytest.CaptureFixture[str]) -> str:
    assert brief_check.main(["--models", str(brief), slug]) == 0
    return capsys.readouterr().out


# why: the conductor's classes load at run time and have no static type.
def _ran(conduct: dict[str, Any], primary: Path) -> Any:  # noqa: ANN401
    """Return a run on `primary` whose take records how far it got; no worker starts."""
    run = conduct["Run"](primary, "claude")
    run.reached, run.spawned = [], []
    run.spawn = lambda *args, **_: run.spawned.append(args)
    run.catch_up = lambda version: run.reached.append(version.change)
    run.ready = lambda version, threads: False
    return run


# The cases: each green on the code as it stands, red under its row's change.


def test_case_a_the_token_and_the_moderate_table(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    token = modelsfile.TOKEN
    for taken in ("a_b", "ABC", "gpt-6.1-sol", "x"):
        assert token.fullmatch(taken), taken
    for refused in ("", "a b", "a;b", "a/b", "é"):
        assert not token.fullmatch(refused), refused
    models, minions = conduct["_models"], tmp_path / ".minions"
    table = '[build]\nexecutor = "codex"\n[build.moderate]\nmodel = "m"\n'
    _models_toml(tmp_path, table)
    assert models(minions, _CHANGE, "build.moderate", "claude") == ("codex", "m", None)
    _models_toml(tmp_path, '[build.moderate]\neffort = "a;b"\n')
    with pytest.raises(conduct["Stop"], match=r"build\.moderate 'a;b' is not a model"):
        models(minions, _CHANGE, "build.moderate", "claude")


def test_case_b_the_hash_leaks_no_descriptor(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    hashed = modelsfile.digest
    _models_toml(tmp_path, "[build]\n")
    before = _open_fds()
    for _ in range(20):
        assert hashed(tmp_path, _CHANGE) == hashlib.sha256(b"[build]\n").hexdigest()
    assert _open_fds() == before


def test_case_c_a_folder_at_the_models_file(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    primary = _cut(tmp_path)
    (layout.change_dir(primary, "0001-a") / "models.toml").mkdir(parents=True)
    check = conduct["_check_cut"]
    said = "changes/0001-a/models.toml: it is not a regular file"
    assert check(primary, "0001-a", primary) == said


def test_case_d_the_parser_reads_a_folder_bad_toml_and_a_bad_byte(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    parsed, minions = conduct["_models_data"], tmp_path / ".minions"
    (layout.change_dir(tmp_path, _CHANGE) / "models.toml").mkdir(parents=True)
    with pytest.raises(conduct["Stop"]) as stopped:
        parsed(minions, _CHANGE)
    said = f"{_FILE}: it is not a regular file"
    assert (stopped.value.code, str(stopped.value)) == (1, said)
    (layout.change_dir(tmp_path, _CHANGE) / "models.toml").rmdir()
    _models_toml(tmp_path, "[converge\n")
    with pytest.raises(conduct["Stop"], match=f"^{_FILE}: ") as stopped:
        parsed(minions, _CHANGE)
    assert stopped.value.code == 1
    _models_toml(tmp_path, b"\xff")
    with pytest.raises(conduct["Stop"]) as stopped:
        parsed(minions, _CHANGE)
    assert (stopped.value.code, str(stopped.value)) == (1, f"{_FILE}: it is not UTF-8")


def test_case_e_a_string_where_a_table_belongs(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    table, minions = conduct["_table"], tmp_path / ".minions"
    _models_toml(tmp_path, 'build = "x"\nconverge = "y"\n')
    assert table(minions, _CHANGE, "build") is None
    assert table(minions, _CHANGE, "converge.fix") is None
    _models_toml(tmp_path, '[converge.fix]\nmodel = "m"\n')
    assert table(minions, _CHANGE, "converge.fix") == {"model": "m"}


def test_case_f_only_a_top_level_decide(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    decides, minions = conduct["_decides"], tmp_path / ".minions"
    assert not decides(minions, _CHANGE)
    for text, held in (
        ('decide = "recommended"\n', True),
        ('decide = "Recommended"\n', False),
        ("decide = true\n", False),
        ('[converge]\ndecide = "recommended"\n', False),
    ):
        _models_toml(tmp_path, text)
        assert decides(minions, _CHANGE) is held, text


def test_case_g_integrate_reads_the_release_table(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    models, minions = conduct["_models"], tmp_path / ".minions"
    _models_toml(tmp_path, '[release]\nmodel = "m"\neffort = "e"\n')
    assert models(minions, _CHANGE, "integrate", "claude") == ("claude", "m", "e")
    _models_toml(tmp_path, '[integrate]\nmodel = "m"\n')
    assert models(minions, _CHANGE, "integrate", "claude") == _DEFAULTS


def test_case_g_the_rescue_reads_its_table_else_the_build(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    models, minions = conduct["_models"], tmp_path / ".minions"
    _models_toml(tmp_path, '[build]\nmodel = "b"\n[rescue]\nmodel = "r"\n')
    assert models(minions, _CHANGE, "rescue", "claude") == ("claude", "r", None)
    _models_toml(tmp_path, '[build]\nmodel = "b"\n')
    assert models(minions, _CHANGE, "rescue", "claude") == ("claude", "b", None)
    _models_toml(tmp_path, '[build]\nmodel = "b"\n[rescue]\n')
    assert models(minions, _CHANGE, "rescue", "claude") == _DEFAULTS


def test_case_g_a_worker_table_before_its_old_name(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    models, minions = conduct["_models"], tmp_path / ".minions"
    _models_toml(
        tmp_path,
        '[converge.review]\nmodel = "old"\n[converge.conformance]\nmodel = "new"\n'
        '[converge.security]\neffort = "old"\n[converge.adversarial]\neffort = "new"\n',
    )
    conformance = models(minions, _CHANGE, "converge.conformance", "claude")
    assert conformance == ("claude", "new", None)
    adversarial = models(minions, _CHANGE, "converge.adversarial", "claude")
    assert adversarial == ("claude", None, "new")
    # The old name alone is ignored: the worker reads its defaults.
    _models_toml(
        tmp_path, '[converge.review]\nmodel = "old"\n[converge.security]\nmodel = "o"\n'
    )
    for station in ("converge.conformance", "converge.adversarial"):
        assert models(minions, _CHANGE, station, "claude") == _DEFAULTS, station


def test_case_g_the_token_check_reaches_every_table(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    models, minions = conduct["_models"], tmp_path / ".minions"
    tables = (*modelsfile.TABLES.values(), *modelsfile.PERSON)
    assert set(tables) >= {*conduct["WORKERS"], conduct["MODERATE"], "build"}
    for table in tables:
        for key in ("model", "effort"):
            _models_toml(tmp_path, f'[{table}]\n{key} = "a b"\n')
            said = f"{_FILE}: {table} 'a b' is not a model or effort"
            for station in ("build", table):
                with pytest.raises(conduct["Stop"]) as stopped:
                    models(minions, _CHANGE, station, "claude")
                assert (stopped.value.code, str(stopped.value)) == (1, said)


def test_case_g_the_moderate_table_refuses_an_executor(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    models, minions = conduct["_models"], tmp_path / ".minions"
    _models_toml(tmp_path, '[build.moderate]\nexecutor = "claude"\n')
    with pytest.raises(conduct["Stop"]) as stopped:
        models(minions, _CHANGE, "build.moderate", "claude")
    said = f"{_FILE}: build.moderate names an executor"
    assert (stopped.value.code, str(stopped.value)) == (1, said)


def test_case_g_the_executor_defaults(tmp_path: Path, conduct: dict[str, Any]) -> None:
    models, minions = conduct["_models"], tmp_path / ".minions"
    _models_toml(tmp_path, '[converge]\nexecutor = "codex"\n')
    for station in ("converge.conformance", "converge.adversarial"):
        assert models(minions, _CHANGE, station, "claude") == ("codex", None, None)
    assert models(minions, _CHANGE, "converge.fix", "codex") == _DEFAULTS
    assert models(minions, _CHANGE, "build", "codex") == ("codex", None, None)


def test_case_g_a_word_of_another_type_reads_as_none(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    models, minions = conduct["_models"], tmp_path / ".minions"
    for station in ("build", "converge.conformance"):
        _models_toml(tmp_path, f"[{station}]\nmodel = 3\neffort = [1]\n")
        assert models(minions, _CHANGE, station, "claude") == _DEFAULTS, station


def test_case_g_the_supervisors_defaults_fill_each_missing_part(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    models, minions = conduct["_models"], tmp_path / ".minions"
    opus, high = conduct["SUPERVISOR"]
    assert models(minions, _CHANGE, "supervise", "claude") == ("claude", opus, high)
    _models_toml(tmp_path, '[supervise]\nmodel = "m"\n')
    assert models(minions, _CHANGE, "supervise", "claude") == ("claude", "m", high)
    _models_toml(tmp_path, '[supervise]\neffort = "low"\n')
    assert models(minions, _CHANGE, "supervise", "claude") == ("claude", opus, "low")


def test_case_g_a_claude_model_on_the_runs_codex(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    models, minions = conduct["_models"], tmp_path / ".minions"
    _models_toml(tmp_path, '[build]\nmodel = "claude-opus-5-5"\n')
    with pytest.raises(conduct["Stop"]) as stopped:
        models(minions, _CHANGE, "build", "codex")
    said = f"{_FILE}: build on codex, model claude-opus-5-5"
    assert (stopped.value.code, str(stopped.value)) == (1, said)
    # A checker naming no executor of its own is not held to it.
    table = (
        '[converge]\nexecutor = "codex"\n[converge.conformance]\nmodel = "claude-x"\n'
    )
    _models_toml(tmp_path, table)
    held = models(minions, _CHANGE, "converge.conformance", "claude")
    assert held == ("codex", "claude-x", None)


def test_case_h_only_true_shadows(tmp_path: Path, conduct: dict[str, Any]) -> None:
    shadows, minions = conduct["_shadows"], tmp_path / ".minions"
    assert not shadows(minions, _CHANGE)
    for text, held in (
        ("[converge]\nshadow = true\n", True),
        ('[converge]\nshadow = "true"\n', False),
        ("[converge]\nshadow = 1\n", False),
        ("[converge]\nshadow = false\n", False),
        ("shadow = true\n", False),
        ("[converge.conformance]\nshadow = true\n", False),
    ):
        _models_toml(tmp_path, text)
        assert shadows(minions, _CHANGE) is held, text


def test_case_i_the_fixer_is_never_skipped(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    skips, minions = conduct["_skips"], tmp_path / ".minions"
    _models_toml(tmp_path, "[converge.fix]\nskip = true\n")
    assert skips(minions, _CHANGE) == frozenset()
    _models_toml(tmp_path, b"[converge]\nskip = true\n\xff")
    with pytest.raises(conduct["Stop"]) as stopped:
        skips(minions, _CHANGE)
    assert str(stopped.value) == f"{_FILE}: it is not UTF-8"
    _models_toml(tmp_path, "[converge]\nskip = true\n")
    assert skips(minions, _CHANGE) == frozenset(("converge", *conduct["WORKERS"]))


def test_case_j_only_a_boolean_rescue_skip(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    skips, minions = conduct["_skips_rescue"], tmp_path / ".minions"
    assert not skips(minions, _CHANGE)
    for text, held in (
        ("[rescue]\nskip = true\n", True),
        ('[rescue]\nskip = "true"\n', False),
        ("[rescue]\nskip = 1\n", False),
        ("skip = true\n", False),
        ("[build]\nskip = true\n", False),
    ):
        _models_toml(tmp_path, text)
        assert skips(minions, _CHANGE) is held, text


def test_case_k_only_auto_grant_false(tmp_path: Path, conduct: dict[str, Any]) -> None:
    grants, minions = conduct["_auto_grants"], tmp_path / ".minions"
    assert grants(minions, _CHANGE)
    for text, held in (
        ("[converge]\nauto_grant = false\n", False),
        ("[converge]\nauto_grant = true\n", True),
        ('[converge]\nauto_grant = "false"\n', True),
        ("[converge]\nauto_grant = 0\n", True),
        ("auto_grant = false\n", True),
        ("[converge.fix]\nauto_grant = false\n", True),
    ):
        _models_toml(tmp_path, text)
        assert grants(minions, _CHANGE) is held, text


def test_case_l_a_station_moved_after_the_plan(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    root = _repo(tmp_path)
    version = _version(conduct, root)
    _models_toml(root, '[converge.adversarial]\nmodel = "a"\n')
    run = _ran(conduct, root)
    run.read_plan([version])
    assert run.planned_models(_CHANGE, "converge.adversarial") == ("claude", "a", None)
    _models_toml(root, '[converge.adversarial]\nmodel = "b"\n')
    assert run.planned_models(_CHANGE, "build") == _DEFAULTS
    with pytest.raises(conduct["Stop"]) as stopped:
        run.planned_models(_CHANGE, "converge.adversarial")
    said = f"{_FILE} changed during the run"
    assert (stopped.value.code, str(stopped.value)) == (1, said)


def test_case_m_a_take_reads_every_planned_station_again(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    root = _repo(tmp_path)
    version = _version(conduct, root)
    run = _ran(conduct, root)
    run.take(version, {})
    assert (run.reached, run.halts, run.spawned) == ([_CHANGE], [], [])
    for text, said in (
        ('[converge.conformance]\nmodel = "a b"\n', "converge.conformance 'a b'"),
        ('[converge.fix]\neffort = "a;b"\n', "converge.fix 'a;b'"),
        ('[build.moderate]\nexecutor = "claude"\n', "build.moderate names"),
        ("[converge\n", f"{_FILE}: "),
        (b"\xff", f"{_FILE}: it is not UTF-8"),
    ):
        _models_toml(root, text)
        run = _ran(conduct, root)
        run.take(version, {})
        assert run.reached == run.spawned == [], text
        [(who, why)] = run.halts
        assert who == _CHANGE
        assert why.startswith(_FILE) and said in why, why


def test_a_build_model_that_is_no_token_halts_its_version(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    # Card 0111·S1. Why: 0142-models design D5.
    root = _repo(tmp_path)
    version = _version(conduct, root)
    _models_toml(root, '[build]\nmodel = "TMPDIR=/tmp/mf-codex-x"\n')
    run = _ran(conduct, root)
    run.take(version, {})
    said = f"{_FILE}: build 'TMPDIR=/tmp/mf-codex-x' is not a model or effort"
    assert (run.halts, run.reached, run.spawned) == ([(_CHANGE, said)], [], [])
    _models_toml(root, '[build]\nmodel = "gpt-6.1-sol"\n')
    run = _ran(conduct, root)
    run.take(version, {})
    assert (run.halts, run.reached) == ([], [_CHANGE])


def test_case_n_the_plans_read(
    tmp_path: Path, conduct: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repo(tmp_path)
    version = _version(conduct, root)
    _models_toml(
        root,
        'decide = "recommended"\n[rescue]\nskip = true\n'
        "[converge]\nauto_grant = false\nshadow = true\n"
        '[converge.adversarial]\nskip = true\n[build]\nmodel = "m"\n',
    )
    run = _ran(conduct, root)
    run.read_plan([version])
    assert run.planned == {_CHANGE}
    assert {station for _, station in run.plan} == set(conduct["PLANNED"])
    assert run.plan[_CHANGE, "build"] == ("claude", "m", None)
    assert run.grants_auto == {_CHANGE: False}
    assert run.skips == run.decides == run.shadowed == {_CHANGE}
    assert run.skipped == {_CHANGE: frozenset({"converge.adversarial"})}
    # A broken file plans nothing and raises nothing: text TOML refuses, a bad
    # byte, a folder.
    path = _models_toml(root, "[converge\n")
    for broken in (b"[converge\n", b'[build]\nmodel = "\xff"\n', None):
        if broken is None:
            path.unlink()
            path.mkdir()
        else:
            path.write_bytes(broken)
        run = _ran(conduct, root)
        run.read_plan([version])
        assert (run.planned, run.plan, run.grants_auto) == ({_CHANGE}, {}, {})
    path.rmdir()
    # The note of a missing Codex reads the checkers alone.
    names = conduct["Run"].read_plan.__globals__
    monkeypatch.setitem(names, "_executor_missing", lambda executor: True)
    noted = " · run · codex — not on PATH: a checker a plan gives Codex runs on Claude"
    for text, said in (
        ('[build]\nexecutor = "codex"\n[converge.fix]\nexecutor = "codex"\n', False),
        ('[converge.adversarial]\nexecutor = "codex"\n', True),
    ):
        _models_toml(root, text)
        run = _ran(conduct, root)
        run.read_plan([version])
        logged = any(
            line.endswith(noted) for line in run.log.path.read_text().split("\n")
        )
        assert (run.codex_said, logged) == (said, said), text


def test_case_o_a_moved_worker_table(tmp_path: Path, conduct: dict[str, Any]) -> None:
    root = _repo(tmp_path)
    version = _version(conduct, root)
    _models_toml(root, '[converge.conformance]\nmodel = "a"\n')
    run = _ran(conduct, root)
    admitted: list[str] = []
    run.admit = lambda version, stage=None: admitted.append(version.change) or False
    run.read_plan([version])
    assert not run.take_back(version, {})
    assert admitted == [_CHANGE]
    _models_toml(root, '[converge.conformance]\nmodel = "b"\n')
    threads: dict[str, object] = {}
    assert not run.take_back(version, threads)
    assert (admitted, threads) == ([_CHANGE], {})
    last = run.log.path.read_text().splitlines()[-1]
    assert last.endswith(
        f" · run · rejoin — {_CHANGE}: still halted —"
        f" changes/{_CHANGE}/models.toml changed during the run"
    )


def test_case_q_the_child_run_of_brief_check(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    text, names = conduct["_models_text"], conduct["main"].__globals__
    brief = tmp_path / "brief.md"
    for code, said in (
        ("import sys; print('\\n  \\nfirst\\nsecond'); sys.exit(1)", "a: first"),
        ("import sys; sys.stderr.write('\\nerr\\n'); sys.exit(1)", "a: err"),
        ("import sys; sys.exit(3)", "a: exit 3"),
    ):
        names["UV_RUN"] = (sys.executable, "-c", code)
        with pytest.raises(conduct["Stop"]) as stopped:
            text(brief, "a")
        assert stopped.value.code == 2
        assert str(stopped.value) == f"cut: cannot run — the brief's models for {said}"
    names["UV_RUN"] = (
        sys.executable,
        "-c",
        "import sys; sys.stdout.buffer.write(b'x = \"\\xff\"')",
    )
    assert text(brief, "a") == 'x = "\ufffd"'
    names["UV_RUN"] = (sys.executable, "-c", "import time; time.sleep(5)")
    names["GIT_TIMEOUT"] = 0.2
    with pytest.raises(conduct["Stop"]) as stopped:
        text(brief, "a")
    said = "cut: cannot run — brief_check.py timed out"
    assert (stopped.value.code, str(stopped.value)) == (2, said)


def test_case_r_the_models_text(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    head = "**full** · minor · after: none · debt: none · decide: recommended  \t"
    assert _printed(_brief(tmp_path, head, _EVERY_PART), "full", capsys) == _EVERY_TABLE


# The pins: each holds what the code does today, where no changed line reaches.


def test_pin_a_bad_byte(tmp_path: Path, conduct: dict[str, Any]) -> None:
    root = _repo(tmp_path)
    version = _version(conduct, root)
    minions = root / ".minions"
    _models_toml(root, b'[build]\nmodel = "\xff"\n')
    for name, args in (
        ("_models_data", ()),
        ("_table", ("build",)),
        ("_decides", ()),
        ("_models", ("build", "claude")),
        ("_shadows", ()),
        ("_skips_rescue", ()),
        ("_auto_grants", ()),
        ("_skips", ()),
    ):
        with pytest.raises(conduct["Stop"]) as stopped:
            conduct[name](minions, _CHANGE, *args)
        assert str(stopped.value) == f"{_FILE}: it is not UTF-8", name
    with pytest.raises(modelsfile.Broken, match=r"^it is not UTF-8$"):
        modelsfile.digest(root, _CHANGE)
    run = _ran(conduct, root)
    assert run.models(_CHANGE, "build") is None
    run.read_plan([version])
    assert (run.plan, run.grants_auto, run.skipped) == ({}, {}, {})
    assert run.skips == run.decides == run.shadowed == set()
    run.take(version, {})
    assert (run.halts, run.reached) == ([(_CHANGE, f"{_FILE}: it is not UTF-8")], [])


def test_pin_text_that_is_not_toml(tmp_path: Path, conduct: dict[str, Any]) -> None:
    root = _repo(tmp_path)
    version = _version(conduct, root)
    minions = root / ".minions"
    _models_toml(root, "[converge\n")
    for name, args in (
        ("_models_data", ()),
        ("_table", ("build",)),
        ("_decides", ()),
        ("_models", ("build", "claude")),
        ("_shadows", ()),
        ("_skips_rescue", ()),
        ("_auto_grants", ()),
        ("_skips", ()),
    ):
        with pytest.raises(conduct["Stop"], match=f"^{_FILE}: ") as stopped:
            conduct[name](minions, _CHANGE, *args)
        assert stopped.value.code == 1, name
    run = _ran(conduct, root)
    assert run.models(_CHANGE, "build") is None
    run.take(version, {})
    [(who, why)] = run.halts
    assert (who, run.reached) == (_CHANGE, [])
    assert why.startswith(f"{_FILE}: ")


def test_pin_a_link_at_the_models_file(tmp_path: Path, conduct: dict[str, Any]) -> None:
    primary = _cut(tmp_path)
    minions = primary / ".minions"
    target = tmp_path / "target.toml"
    target.write_text('[build]\nmodel = "m"\n')
    models = layout.change_dir(primary, "0001-a") / "models.toml"
    models.parent.mkdir(parents=True)
    models.symlink_to(target)
    file = "conduct: halt — changes/0001-a/models.toml: it is a link"
    with pytest.raises(conduct["Stop"]) as stopped:
        conduct["_models"](minions, "0001-a", "build", "claude")
    assert (stopped.value.code, str(stopped.value)) == (1, file)
    with pytest.raises(modelsfile.Broken, match=r"^it is a link$"):
        modelsfile.digest(primary, "0001-a")
    check = conduct["_check_cut"]
    said = "changes/0001-a/models.toml: it is a link"
    for queued in (target.read_text(), None):
        _queue(primary, "0001-a", queued)
        assert check(primary, "0001-a", primary) == said
    # A dangling link is a link.
    models.unlink()
    models.symlink_to(tmp_path / "gone.toml")
    with pytest.raises(conduct["Stop"]) as stopped:
        conduct["_models_data"](minions, "0001-a")
    assert str(stopped.value) == file
    # The writer refuses a link, and its target keeps its bytes.
    models.unlink()
    models.symlink_to(target)
    with pytest.raises(conduct["Stop"]) as stopped:
        _writer(conduct)(primary, "0001-a", "[release]\n")
    assert stopped.value.code == 2
    assert models.is_symlink()
    assert target.read_text() == '[build]\nmodel = "m"\n'


def test_pin_a_hard_link_at_the_models_file(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    other = tmp_path / "other.toml"
    other.write_text("[build]\n")
    models = layout.change_dir(tmp_path, _CHANGE) / "models.toml"
    models.parent.mkdir(parents=True)
    os.link(other, models)
    _writer(conduct)(tmp_path, _CHANGE, "[release]\n")
    assert (models.read_text(), other.read_text()) == ("[release]\n", "[build]\n")
    assert models.stat().st_nlink == other.stat().st_nlink == 1


def test_pin_a_pipe_at_the_models_file(tmp_path: Path, conduct: dict[str, Any]) -> None:
    root = _repo(tmp_path)
    version = _version(conduct, root)
    models = layout.change_dir(root, _CHANGE) / "models.toml"
    models.parent.mkdir(parents=True)
    os.mkfifo(models)
    with pytest.raises(conduct["Stop"]) as stopped:
        conduct["_models_data"](root / ".minions", _CHANGE)
    assert str(stopped.value) == f"{_FILE}: it is not a regular file"
    run = _ran(conduct, root)
    run.read_plan([version])
    assert run.plan == {}
    assert _hash_in_child(root, _CHANGE) == "it is not a regular file"
    _writer(conduct)(root, _CHANGE, "[build]\n")
    assert models.read_text() == "[build]\n"


def test_pin_a_folder_at_the_models_file(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    primary = _cut(tmp_path)
    (layout.change_dir(primary, "0001-a") / "models.toml").mkdir(parents=True)
    with pytest.raises(conduct["Stop"]) as stopped:
        conduct["_models_data"](primary / ".minions", "0001-a")
    assert str(stopped.value).endswith("models.toml: it is not a regular file")
    said = conduct["_check_cut"](primary, "0001-a", primary)
    assert said == "changes/0001-a/models.toml: it is not a regular file"
    with pytest.raises(conduct["Stop"]) as stopped:
        _writer(conduct)(primary, "0001-a", "[build]\n")
    assert stopped.value.code == 2
    with pytest.raises(modelsfile.Broken, match=r"^it is not a regular file$"):
        modelsfile.digest(primary, "0001-a")


def test_pin_a_word_that_is_no_token(tmp_path: Path, conduct: dict[str, Any]) -> None:
    models, minions = conduct["_models"], tmp_path / ".minions"
    stations = ("build", "rescue", "release", "integrate", "supervise", "converge")
    for word in ("TMPDIR=/tmp/x", "a b"):
        for table in ("build", "rescue", "release", "supervise", "converge"):
            _models_toml(tmp_path, f'[{table}]\nmodel = "{word}"\n')
            for station in stations:
                with pytest.raises(conduct["Stop"], match="is not a model or effort"):
                    models(minions, _CHANGE, station, "claude")
        for station in (*conduct["WORKERS"], conduct["MODERATE"]):
            _models_toml(tmp_path, f'[{station}]\nmodel = "{word}"\n')
            with pytest.raises(conduct["Stop"], match="is not a model or effort"):
                models(minions, _CHANGE, station, "claude")


def test_pin_keys_no_writer_writes(tmp_path: Path, conduct: dict[str, Any]) -> None:
    minions = tmp_path / ".minions"
    _models_toml(
        tmp_path,
        '[rescue]\nmodel = "r"\nskip = true\n[supervise]\nmodel = "s"\n'
        "[converge]\nauto_grant = false\n",
    )
    models = conduct["_models"]
    assert models(minions, _CHANGE, "rescue", "claude") == ("claude", "r", None)
    assert models(minions, _CHANGE, "supervise", "claude")[1] == "s"
    assert conduct["_skips_rescue"](minions, _CHANGE)
    assert not conduct["_auto_grants"](minions, _CHANGE)
    _models_toml(
        tmp_path,
        '[converge.review]\nmodel = "a"\nskip = true\n'
        '[converge.security]\neffort = "b"\nskip = true\n',
    )
    assert models(minions, _CHANGE, "converge.conformance", "claude") == _DEFAULTS
    assert models(minions, _CHANGE, "converge.adversarial", "claude") == _DEFAULTS
    assert conduct["_skips"](minions, _CHANGE) == frozenset()


def test_pin_the_cut_part(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    line = "build a b · converge a b · release a b · cut opus high"
    printed = _printed(
        _brief(tmp_path, "**x** · minor · after: none", line), "x", capsys
    )
    assert "cut" not in printed and "opus" not in printed
    assert "cut" not in modelsfile.TABLES


def test_pin_where_skip_and_shadow_count(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    minions = tmp_path / ".minions"
    skips, rescue = conduct["_skips"], conduct["_skips_rescue"]
    for table in ("build", "release", "supervise", "converge.fix", "build.moderate"):
        _models_toml(tmp_path, f"[{table}]\nskip = true\nshadow = true\n")
        assert skips(minions, _CHANGE) == frozenset(), table
        assert not rescue(minions, _CHANGE), table
        assert not conduct["_shadows"](minions, _CHANGE), table
    for checker in ("converge.conformance", "converge.adversarial"):
        _models_toml(tmp_path, f'[{checker}]\nskip = true\nmodel = "m"\n')
        assert skips(minions, _CHANGE) == frozenset({checker})
        assert conduct["_models"](minions, _CHANGE, checker, "claude")[1] == "m"
    _models_toml(tmp_path, '[converge]\nskip = true\nmodel = "m"\n')
    assert conduct["_models"](minions, _CHANGE, "converge", "claude")[1] == "m"


def test_pin_wrong_types(tmp_path: Path, conduct: dict[str, Any]) -> None:
    minions = tmp_path / ".minions"
    for text in (
        '[converge]\nskip = "yes"\n',
        "[converge]\nskip = 1\n",
        "[converge.adversarial]\nskip = 1\n",
    ):
        _models_toml(tmp_path, text)
        assert conduct["_skips"](minions, _CHANGE) == frozenset(), text
    for text, name in (
        ('[rescue]\nskip = "yes"\n', "_skips_rescue"),
        ("[converge]\nshadow = 1\n", "_shadows"),
        ("decide = true\n", "_decides"),
    ):
        _models_toml(tmp_path, text)
        assert not conduct[name](minions, _CHANGE), text
    for text in ('[converge]\nauto_grant = "false"\n', "[converge]\nauto_grant = 0\n"):
        _models_toml(tmp_path, text)
        assert conduct["_auto_grants"](minions, _CHANGE), text
    models = conduct["_models"]
    for text in (
        "[build]\nmodel = 3\neffort = 4\n",
        "[build]\nmodel = [1]\neffort = [2]\n",
        "[build]\nmodel = { a = 1 }\neffort = { b = 2 }\n",
        'build = "x"\n',
    ):
        _models_toml(tmp_path, text)
        assert models(minions, _CHANGE, "build", "claude") == _DEFAULTS, text
    assert conduct["_table"](minions, _CHANGE, "build") is None
    for value, shown in (
        ("3", "3"),
        ('"Claude"', "'Claude'"),
        ('["claude"]', "['claude']"),
    ):
        _models_toml(tmp_path, f"[build]\nexecutor = {value}\n")
        with pytest.raises(conduct["Stop"]) as stopped:
            models(minions, _CHANGE, "build", "claude")
        assert str(stopped.value) == f"{_FILE}: executor {shown} unknown"


def test_pin_the_queued_text_against_the_file(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    primary = _cut(tmp_path)
    check = conduct["_check_cut"]
    models = _models_toml(primary, "[build]\n", "0001-a")
    _queue(primary, "0001-a", "[build]\n")
    assert check(primary, "0001-a", primary) is None
    models.write_text("[build]\n ")
    changed = "changes/0001-a/models.toml changed since the cut was queued"
    assert check(primary, "0001-a", primary) == changed
    _queue(primary, "0001-a", None)
    for text in ("[build]\n ", "anything\n", ""):
        models.write_text(text)
        assert check(primary, "0001-a", primary) is None, text
    # A broken file fails the check even with no queued text.
    models.write_bytes(b"\xff")
    said = "changes/0001-a/models.toml: it is not UTF-8"
    assert check(primary, "0001-a", primary) == said


def test_pin_models_text_and_its_written_file(
    tmp_path: Path, conduct: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    head = "**full** · minor · after: none · debt: none · decide: recommended"
    brief = _brief(tmp_path, head, _EVERY_PART)
    assert _printed(brief, "full", capsys) == _EVERY_TABLE
    conduct["main"].__globals__["UV_RUN"] = (sys.executable,)
    text = conduct["_models_text"](brief, "full")
    assert text == _EVERY_TABLE
    _writer(conduct)(tmp_path, _CHANGE, text)
    written = layout.change_dir(tmp_path, _CHANGE) / "models.toml"
    assert written.read_bytes() == _EVERY_TABLE.encode()


# The fix: a broken file, the cut's check and the write. Why: 0142-models D6 to D10.


def test_the_cut_check_names_a_broken_models_file(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    primary = _cut(tmp_path)
    check = conduct["_check_cut"]
    assert check(primary, "0001-a", primary) == "no .minions/changes/0001-a/models.toml"
    path = _models_toml(primary, b"#" * (modelsfile.BOUND + 1), "0001-a")
    for queued in ("[build]\n", None):
        _queue(primary, "0001-a", queued)
        said = "changes/0001-a/models.toml: it is over 65536 bytes"
        assert check(primary, "0001-a", primary) == said
    path.write_text("[build]\n")
    assert check(primary, "0001-a", primary) is None


def test_a_link_at_the_models_file_is_refused(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    primary = _cut(tmp_path)
    target = tmp_path / "target.toml"
    target.write_text("keep me\n")
    models = layout.models_file(primary, "0001-a")
    models.parent.mkdir(parents=True)
    models.symlink_to(target)
    _queue(primary, "0001-a", "[build]\n")
    with pytest.raises(conduct["Stop"]) as stopped:
        _ran(conduct, primary).cutting("0001-a")
    said = "cut: cannot run — changes/0001-a/models.toml cannot be written: "
    assert stopped.value.code == 2
    assert str(stopped.value).startswith(said)
    assert (models.is_symlink(), target.read_text()) == (True, "keep me\n")


# why: the conductor's classes load at run time and have no static type.
def _built(conduct: dict[str, Any], root: Path) -> Any:  # noqa: ANN401
    """Return a version whose one phase is ticked and whose build is done at `HEAD`."""
    version = _version(conduct, root)
    tasks = {f"openspec/changes/{_CHANGE}/tasks.md": "## Progress\n\n- [x] 1 — Todo\n"}
    _commit(version.tree, tasks, "build")
    _done(root, _CHANGE, _git(version.tree, "rev-parse", "HEAD"))
    return version


def test_stage_of_reads_no_skip_from_a_broken_file(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    root = _repo(tmp_path)
    version = _built(conduct, root)
    stage_of, unjudged = conduct["stage_of"], conduct["_unjudged"]
    _models_toml(root, "[converge]\nskip = true\n")
    skipped = ("release", "converge skipped by plan; main is an ancestor")
    assert stage_of(root, version) == skipped
    assert unjudged(root / ".minions", version.tree, _CHANGE) is None
    _models_toml(root, b"[converge]\nskip = true\n\xff")
    assert stage_of(root, version) == ("converge", "no conformance findings file")
    said = unjudged(root / ".minions", version.tree, _CHANGE)
    assert said == "no conformance findings file"


def test_status_names_a_broken_models_file(
    tmp_path: Path, conduct: dict[str, Any]
) -> None:
    root = _repo(tmp_path)
    _version(conduct, root)
    _version(conduct, root, "0002-marks")
    _models_toml(root, b"\xff")
    lines = conduct["status"](root).splitlines()
    said = "0001-todo · build — changes/0001-todo/models.toml: it is not UTF-8"
    assert said in lines
    assert "0002-marks · build" in lines


# The module: each function gives what the pins of its copy hold.


def test_module_text(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    parts = [part.split() for part in _EVERY_PART.split(" · ")]
    named = {name: rest for name, *rest in parts}
    head = "**full** · minor · after: none · debt: none · decide: recommended"
    printed = _printed(_brief(tmp_path, head, _EVERY_PART), "full", capsys)
    assert modelsfile.text(True, named, parts[-1:] == [["shadow"]]) == printed
    assert printed == _EVERY_TABLE
    skipped = {"converge": ["skip"], "cut": ["opus", "high"]}
    assert modelsfile.text(False, skipped, False) == "[converge]\nskip = true\n"
    assert "cut" not in modelsfile.TABLES


def test_module_read(tmp_path: Path) -> None:
    assert modelsfile.read(tmp_path, _CHANGE) == {}
    path = _models_toml(tmp_path, '[build]\nmodel = "m"\n')
    assert modelsfile.read(tmp_path, _CHANGE) == {"build": {"model": "m"}}
    _models_toml(tmp_path, "[converge\n")
    with pytest.raises(modelsfile.Broken) as broken:
        modelsfile.read(tmp_path, _CHANGE)
    with pytest.raises(tomllib.TOMLDecodeError) as refused:
        tomllib.loads("[converge\n")
    assert str(broken.value) == str(refused.value)
    _models_toml(tmp_path, b"\xff")
    with pytest.raises(modelsfile.Broken, match=r"^it is not UTF-8$"):
        modelsfile.read(tmp_path, _CHANGE)
    target = tmp_path / "target.toml"
    target.write_text("decide = 1\n")
    path.unlink()
    path.symlink_to(target)
    with pytest.raises(modelsfile.Broken, match=r"^it is a link$"):
        modelsfile.read(tmp_path, _CHANGE)
    path.unlink()
    path.symlink_to(tmp_path / "gone.toml")
    with pytest.raises(modelsfile.Broken, match=r"^it is a link$"):
        modelsfile.read(tmp_path, _CHANGE)
    path.unlink()
    os.mkfifo(path)
    with pytest.raises(modelsfile.Broken, match=r"^it is not a regular file$"):
        modelsfile.read(tmp_path, _CHANGE)
    path.unlink()
    path.mkdir()
    with pytest.raises(modelsfile.Broken, match=r"^it is not a regular file$"):
        modelsfile.read(tmp_path, _CHANGE)
    path.rmdir()
    # Every table's words are tokens; a key the map does not name is ignored.
    for table in (*modelsfile.TABLES.values(), *modelsfile.PERSON):
        _models_toml(tmp_path, f'[{table}]\nmodel = "m"\neffort = "a;b"\n')
        said = f"^{table} 'a;b' is not a model or effort$"
        with pytest.raises(modelsfile.Broken, match=said):
            modelsfile.read(tmp_path, _CHANGE)
    _models_toml(tmp_path, '[converge]\ntier = "a b"\n[other]\nmodel = "a b"\n')
    assert modelsfile.read(tmp_path, _CHANGE)["converge"] == {"tier": "a b"}


def test_module_load(tmp_path: Path) -> None:
    assert modelsfile.load(tmp_path, _CHANGE) is None
    folder = layout.change_dir(tmp_path, _CHANGE)
    folder.mkdir(parents=True)
    assert modelsfile.load(tmp_path, _CHANGE) is None
    bound = modelsfile.BOUND
    assert bound == 65536
    full = b"#" * (bound - 1) + b"\n"
    path = _models_toml(tmp_path, full)
    assert modelsfile.load(tmp_path, _CHANGE) == full
    path.write_bytes(full + b"\n")
    with pytest.raises(modelsfile.Broken, match=r"^it is over 65536 bytes$"):
        modelsfile.load(tmp_path, _CHANGE)
    # A link at the change's folder is followed by no read.
    path.unlink()
    elsewhere = tmp_path / "elsewhere"
    folder.rename(elsewhere)
    folder.symlink_to(elsewhere)
    with pytest.raises(modelsfile.Broken, match=r"^its folder cannot be opened: "):
        modelsfile.load(tmp_path, _CHANGE)


def test_module_table() -> None:
    data = tomllib.loads('build = "x"\nconverge = "y"\n[release.fix]\nmodel = "m"\n')
    assert modelsfile.table(data, "build") is None
    assert modelsfile.table(data, "converge.fix") is None
    assert modelsfile.table(data, "release.fix") == {"model": "m"}
    assert modelsfile.table(data, "rescue") is None
    assert modelsfile.table({}, "build") is None


def test_module_decides() -> None:
    for text, held in (
        ("", False),
        ('decide = "recommended"\n', True),
        ('decide = "Recommended"\n', False),
        ("decide = true\n", False),
        ('[converge]\ndecide = "recommended"\n', False),
    ):
        assert modelsfile.decides(tomllib.loads(text)) is held, text


def test_module_shadows() -> None:
    for text, held in (
        ("", False),
        ("[converge]\nshadow = true\n", True),
        ('[converge]\nshadow = "true"\n', False),
        ("[converge]\nshadow = 1\n", False),
        ("[converge]\nshadow = false\n", False),
        ("shadow = true\n", False),
        ("[converge.conformance]\nshadow = true\n", False),
    ):
        assert modelsfile.shadows(tomllib.loads(text)) is held, text


def test_module_rescue_skips() -> None:
    for text, held in (
        ("", False),
        ("[rescue]\nskip = true\n", True),
        ('[rescue]\nskip = "true"\n', False),
        ("[rescue]\nskip = 1\n", False),
        ("skip = true\n", False),
        ("[build]\nskip = true\n", False),
    ):
        assert modelsfile.rescue_skips(tomllib.loads(text)) is held, text


def test_module_auto_grants() -> None:
    for text, held in (
        ("", True),
        ("[converge]\nauto_grant = false\n", False),
        ("[converge]\nauto_grant = true\n", True),
        ('[converge]\nauto_grant = "false"\n', True),
        ("[converge]\nauto_grant = 0\n", True),
        ("auto_grant = false\n", True),
        ("[converge.fix]\nauto_grant = false\n", True),
    ):
        assert modelsfile.auto_grants(tomllib.loads(text)) is held, text


def test_module_skipping() -> None:
    names = ("converge", "converge.conformance", "converge.adversarial")
    for text, held in (
        ("", set()),
        ("[converge.fix]\nskip = true\n", set()),
        ("[converge]\nskip = true\n", {"converge"}),
        ('[converge.adversarial]\nskip = true\nmodel = "m"\n', {names[2]}),
        ('[converge]\nskip = "yes"\n', set()),
        ("[converge.conformance]\nskip = 1\n", set()),
        ("[build]\nskip = true\n", set()),
    ):
        assert modelsfile.skipping(tomllib.loads(text), names) == held, text
    fix = tomllib.loads("[converge.fix]\nskip = true\n")
    assert modelsfile.skipping(fix, ("converge.fix",)) == {"converge.fix"}


def test_module_digest(tmp_path: Path) -> None:
    assert modelsfile.digest(tmp_path, _CHANGE) is None
    path = _models_toml(tmp_path, b"[build]\nmodel = \"\xc3\xa9\"\nx = 'a b'\n")
    wanted = hashlib.sha256(b"[build]\nmodel = \"\xc3\xa9\"\nx = 'a b'\n").hexdigest()
    before = _open_fds()
    for _ in range(20):
        assert modelsfile.digest(tmp_path, _CHANGE) == wanted
    assert _open_fds() == before
    target = tmp_path / "target.toml"
    target.write_text("[build]\n")
    path.unlink()
    path.symlink_to(target)
    with pytest.raises(modelsfile.Broken, match=r"^it is a link$"):
        modelsfile.digest(tmp_path, _CHANGE)
    path.unlink()
    path.mkdir()
    with pytest.raises(modelsfile.Broken, match=r"^it is not a regular file$"):
        modelsfile.digest(tmp_path, _CHANGE)
    path.rmdir()
    path.write_bytes(b"\xff")
    with pytest.raises(modelsfile.Broken, match=r"^it is not UTF-8$"):
        modelsfile.digest(tmp_path, _CHANGE)


def test_module_write(tmp_path: Path) -> None:
    path = layout.models_file(tmp_path, _CHANGE)
    modelsfile.write(tmp_path, _CHANGE, _EVERY_TABLE)
    assert path.read_bytes() == _EVERY_TABLE.encode()
    target = tmp_path / "target.toml"
    target.write_text('[build]\nmodel = "m"\n')
    path.unlink()
    path.symlink_to(target)
    with pytest.raises(statefile.WriteFailed) as failed:
        modelsfile.write(tmp_path, _CHANGE, "[release]\n")
    assert failed.value.step == "replace"
    assert path.is_symlink()
    assert target.read_text() == '[build]\nmodel = "m"\n'
    path.unlink()
    os.link(target, path)
    modelsfile.write(tmp_path, _CHANGE, "[build]\n")
    assert (path.read_text(), target.read_text()) == (
        "[build]\n",
        '[build]\nmodel = "m"\n',
    )
    assert path.stat().st_nlink == target.stat().st_nlink == 1
    path.unlink()
    os.mkfifo(path)
    modelsfile.write(tmp_path, _CHANGE, "[build]\n")
    assert path.read_text() == "[build]\n"
    path.unlink()
    path.mkdir()
    with pytest.raises(statefile.WriteFailed) as failed:
        modelsfile.write(tmp_path, _CHANGE, "[build]\n")
    assert (failed.value.step, path.is_dir()) == ("replace", True)
    assert os.listdir(path.parent) == ["models.toml"]
    path.rmdir()
    # A link at the change's folder: the write makes nothing through it.
    folder, elsewhere = path.parent, tmp_path / "elsewhere"
    folder.rename(elsewhere)
    folder.symlink_to(elsewhere)
    with pytest.raises(statefile.WriteFailed) as failed:
        modelsfile.write(tmp_path, _CHANGE, "[build]\n")
    assert (failed.value.step, os.listdir(elsewhere)) == ("create", [])
