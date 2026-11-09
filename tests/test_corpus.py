"""The corpus runner: this repo's readers of run data, run over a run directory.

A repository and a run directory under `tmp_path`, each case a `sys.executable -c`
reader. Why: 0103-fewer-rounds design D5.
"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "scripts" / "corpus.py"
_COPY = (
    "import sys, pathlib;"
    " pathlib.Path(sys.argv[2]).write_text(pathlib.Path(sys.argv[1]).read_text())"
)
_WHERE = (
    "import sys, pathlib;"
    " pathlib.Path(sys.argv[3]).write_text(sys.argv[1] + '|' + sys.argv[2])"
)
_MINIONS = "import sys, pathlib; pathlib.Path(sys.argv[2]).write_text(sys.argv[1])"
_FAIL_B = (
    "import sys\n"
    "for n in range(7):\n"
    "    print(f'line {n}', file=sys.stderr)\n"
    "sys.exit(1 if sys.argv[1].endswith('b/x.md') else 0)"
)
_SLEEP = "import time; time.sleep(5)"
_PREFIX = "corpus: cannot run — "


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("corpus", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


corpus = _load()


def _cases(path: Path, *cases: dict[str, object]) -> Path:
    """Write `cases` as `[[case]]` tables, each value as JSON, valid TOML here."""
    text = ""
    for case in cases:
        text += "[[case]]\n" + "".join(
            f"{k} = {json.dumps(v)}\n" for k, v in case.items()
        )
    path.write_text(text)
    return path


def _case(name: str, argv: list[str], **more: object) -> dict[str, object]:
    return {"name": name, "reads": "a reader, in prose", "argv": argv, **more}


def _repo(root: Path) -> Path:
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    return root


def test_the_corpus_runs_each_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _repo(tmp_path / "repo")
    monkeypatch.chdir(root)
    minions = tmp_path / "run"
    for name in ("a", "b"):
        (minions / "changes" / name).mkdir(parents=True)
        (minions / "changes" / name / "x.md").write_text(name.upper())
    # A link to a file and a link to a folder are no input.
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "x.md").write_text("OUT")
    (minions / "changes" / "c").symlink_to(outside)
    (minions / "changes" / "d").mkdir()
    (minions / "changes" / "d" / "x.md").symlink_to(minions / "changes" / "a" / "x.md")
    stale = minions / "corpus" / "copy-each" / "1" / "stale.txt"
    stale.parent.mkdir(parents=True)
    stale.write_text("old")
    py = sys.executable

    def run(*cases: dict[str, object]) -> tuple[int, list[str]]:
        found = _cases(tmp_path / "cases.toml", *cases)
        code = corpus.main(["--cases", str(found), "--minions", str(minions)])
        return code, capsys.readouterr().out.splitlines()

    # A pass per input, no input, and one run with no `each`; `{out}` is fresh.
    assert run(
        _case(
            "copy-each",
            [py, "-c", _COPY, "{input}", "{out}/copy.txt"],
            each=["changes/*/x.md"],
        ),
        _case(
            "none-here", [py, "-c", _COPY, "{input}", "{out}/c.txt"], each=["nothing/*"]
        ),
        _case("once", [py, "-c", _WHERE, "{primary}", "{minions}", "{out}/p.txt"]),
    ) == (
        0,
        [
            "corpus: copy-each · 2 runs · pass",
            "corpus: none-here · no input",
            "corpus: once · 1 runs · pass",
        ],
    )
    copies = minions / "corpus" / "copy-each"
    assert [(copies / n / "copy.txt").read_text() for n in "12"] == ["A", "B"]
    assert not stale.exists()
    where = (minions / "corpus" / "once" / "1" / "p.txt").read_text()
    assert where == f"{tmp_path}|{minions}"

    # A reader that exits 1 names the case and the input, and its first stderr lines.
    assert run(
        _case("bad-each", [py, "-c", _FAIL_B, "{input}"], each=["changes/*/x.md"])
    ) == (
        1,
        [
            "corpus: bad-each · changes/b/x.md · exit 1",
            *(f"  | line {n}" for n in range(5)),
            "corpus: bad-each · 2 runs · 1 failed",
        ],
    )

    # A reader past the timeout, and one that cannot start, fail.
    monkeypatch.setattr(corpus, "TIMEOUT_SECONDS", 0.5)
    assert run(
        _case("slow", [py, "-c", _SLEEP]), _case("ghost", ["nonesuch-program"])
    ) == (
        1,
        [
            "corpus: slow · once · timed out",
            "corpus: slow · 1 runs · 1 failed",
            "corpus: ghost · once · exit 127",
            "  | No such file or directory",
            "corpus: ghost · 1 runs · 1 failed",
        ],
    )

    # With no `--minions` and no `--cases`, a run from the repository finds its run
    # directory from git and its cases in `scripts/corpus.toml`.
    (root / "scripts").mkdir()
    reader = _case("once", [py, "-c", _MINIONS, "{minions}", "{out}/m.txt"])
    _cases(root / "scripts" / "corpus.toml", reader)
    done = subprocess.run([py, str(_SCRIPT)], cwd=root, capture_output=True, text=True)
    assert (done.returncode, done.stdout) == (0, "corpus: once · 1 runs · pass\n")
    written = (root / ".minions" / "corpus" / "once" / "1" / "m.txt").read_text()
    assert Path(written).resolve() == (root / ".minions").resolve()


def test_a_corpus_it_cannot_read_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _repo(tmp_path / "repo")
    monkeypatch.chdir(root)
    minions = tmp_path / "run"
    minions.mkdir()
    found = tmp_path / "cases.toml"

    def refused(minions: Path = minions, cases: Path = found) -> str:
        code = corpus.main(["--cases", str(cases), "--minions", str(minions)])
        said = capsys.readouterr().out.strip()
        assert code == 2
        assert said.startswith(_PREFIX)
        return said

    ok = ["true"]
    broken: list[list[dict[str, object]]] = [
        [{"name": "Bad Name", "reads": "r", "argv": ok}],
        [{"name": "a", "argv": ok}],
        [{"name": "a", "reads": "r"}],
        [{"name": "a", "reads": "r", "argv": []}],
        [{"name": "a", "reads": "r", "argv": [1]}],
        [_case("a", ok, each="changes/*")],
        [_case("a", ok, each=["../outside/*"])],
        [_case("a", ok, each=["/etc/*"])],
    ]
    for cases in broken:
        _cases(found, *cases)
        assert str(found) in refused()

    # A file that does not parse, one with no case, and one that is missing.
    found.write_text("[[case\n")
    assert str(found) in refused()
    found.write_text("x = 1\n")
    assert refused().endswith("no [[case]]")
    assert refused(cases=tmp_path / "missing.toml").endswith(
        "No such file or directory"
    )

    # A run directory that is a link, and a `corpus/` that is one.
    _cases(found, _case("a", ok))
    (tmp_path / "link").symlink_to(minions)
    assert refused(minions=tmp_path / "link").endswith("is a link")
    (minions / "corpus").symlink_to(tmp_path)
    assert refused().endswith("is a link")

    # No git, and a directory that is no repository.
    path = os.environ["PATH"]
    monkeypatch.setenv("PATH", "")
    assert refused() == f"{_PREFIX}git is missing"
    monkeypatch.setenv("PATH", path)
    elsewhere = tmp_path / "plain"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert "git rev-parse failed: fatal:" in refused()
