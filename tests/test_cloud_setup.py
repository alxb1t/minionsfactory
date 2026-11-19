"""The cloud setup script, on a fake Linux machine behind its `run` and `fetch`.

Each test replaces `run`, `fetch`, `BIN` and the root, OS and tag checks, so no case
installs a thing on the host. Why: 0137-cloud-session design D6.
"""

import hashlib
import importlib.util
import io
import os
import re
import runpy
import subprocess
import sys
import tarfile
import tomllib
import urllib.error
from pathlib import Path
from types import ModuleType

import pytest
from mflib import layout, platform

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "scripts" / "cloud_setup.py"
_TAG = "v9.9.9"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("cloud_setup", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup = _load()


def _tarball(files: dict[str, bytes]) -> bytes:
    """Return a gzipped tarball holding `files`, each name a path inside it."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


class Machine:
    """A fake Linux machine: its packages, its programs and each command it ran."""

    def __init__(self, bin_dir: Path) -> None:
        self.bin = bin_dir
        self.packages: set[str] = set()
        self.calls: list[list[str]] = []
        self.fetched: list[str] = []
        self.failing: set[str] = set()
        self.downloads = {
            setup.UV_URL: _tarball(
                {
                    "uv-x86_64-unknown-linux-gnu/uv": f"uv {setup.UV} (x)".encode(),
                    "uv-x86_64-unknown-linux-gnu/uvx": b"uvx",
                }
            ),
            setup.BETTERLEAKS_URL: _tarball(
                {"betterleaks": setup.BETTERLEAKS.encode(), "README.md": b"read me"}
            ),
        }

    def run(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(argv)
        if argv[0] in self.failing:
            return subprocess.CompletedProcess(argv, 1, "", "first\nit broke\n")
        program = self.bin / argv[0]
        match argv:
            case ["dpkg", "-s", name]:
                code = 0 if name in self.packages else 1
            case ["apt-get", "update"]:
                code = 0
            case ["apt-get", "install", "-y", *names]:
                self.packages.update(names)
                code = 0
            case ["npm", "install", "-g", spec]:
                (self.bin / "openspec").write_text(spec.rpartition("@")[2])
                code = 0
            case ["make", "-C", _, "install-skills", tag]:
                (layout.data_dir() / tag.removeprefix("TAG=")).mkdir(parents=True)
                code = 0
            case _ if program.is_file():
                return subprocess.CompletedProcess(argv, 0, program.read_text(), "")
            case _:
                return subprocess.CompletedProcess(argv, 127, "", "not found")
        return subprocess.CompletedProcess(argv, code, "", "")

    def fetch(self, url: str) -> bytes:
        self.fetched.append(url)
        return self.downloads[url]

    def installs(self) -> list[list[str]]:
        """Return each command that changed the machine."""
        return [argv for argv in self.calls if argv[0] in {"apt-get", "npm", "make"}]


@pytest.fixture
def machine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Machine:
    """Return a fake Linux machine, root and in a clone at a tag, the script on it."""
    bin_dir = tmp_path / "usr-local-bin"
    bin_dir.mkdir()
    fake = Machine(bin_dir)
    tools = tuple(
        tool._replace(sha256=hashlib.sha256(fake.downloads[tool.url]).hexdigest())
        for tool in setup.TOOLS
    )
    monkeypatch.setattr(setup, "TOOLS", tools)
    monkeypatch.setattr(setup, "BIN", bin_dir)
    monkeypatch.setattr(setup, "run", fake.run)
    monkeypatch.setattr(setup, "fetch", fake.fetch)
    monkeypatch.setattr(setup, "is_root", lambda: True)
    monkeypatch.setattr(setup, "clone_tag", lambda: _TAG)
    monkeypatch.setattr(platform, "OS", "linux")
    monkeypatch.setattr(platform, "has_sandbox", lambda: True)
    return fake


def _report(capsys: pytest.CaptureFixture[str]) -> list[str]:
    return capsys.readouterr().out.splitlines()


def test_a_first_run_installs_each_step(
    machine: Machine, capsys: pytest.CaptureFixture[str]
) -> None:
    assert setup.main() == 0
    assert machine.installs() == [
        ["apt-get", "update"],
        ["apt-get", "install", "-y", "bubblewrap", "socat", "procps"],
        ["npm", "install", "-g", f"@fission-ai/openspec@{setup.OPENSPEC}"],
        ["make", "-C", str(setup.ROOT), "install-skills", f"TAG={_TAG}"],
    ]
    assert machine.fetched == [setup.UV_URL, setup.BETTERLEAKS_URL]
    assert sorted(path.name for path in machine.bin.iterdir()) == [
        "betterleaks",
        "openspec",
        "uv",
        "uvx",
    ]
    assert os.access(machine.bin / "uv", os.X_OK)
    assert (Path.home() / "mf-tmp").is_dir()
    assert layout.ship_file().read_text() == "[push]\ntags = false\n"
    assert tomllib.loads(layout.ship_file().read_text()) == {"push": {"tags": False}}
    report = _report(capsys)
    assert report[0] == "packages: installed bubblewrap, socat, procps"
    assert f"skills: installed {_TAG}" in report
    assert report[-2:] == ["sandbox: applies", "cloud_setup: ready"]


@pytest.mark.parametrize(
    ("case", "reason"),
    [("not root", "not root"), ("macos", "not Linux"), ("no tag", "no tag")],
)
def test_a_user_or_os_or_clone_the_script_refuses_runs_no_command(
    machine: Machine,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    case: str,
    reason: str,
) -> None:
    if case == "not root":
        monkeypatch.setattr(setup, "is_root", lambda: False)
    elif case == "macos":
        monkeypatch.setattr(platform, "OS", "macos")
    else:
        monkeypatch.setattr(setup, "clone_tag", lambda: None)
    assert setup.main() == 2
    assert machine.calls == []
    assert machine.fetched == []
    [line] = _report(capsys)
    assert line.startswith("cloud_setup: refused — ")
    assert reason in line


def test_the_script_as_a_program_refuses_off_linux(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "path", list(sys.path))
    with pytest.raises(SystemExit) as stopped:
        runpy.run_path(str(_SCRIPT), run_name="__main__")
    assert stopped.value.code == 2


@pytest.mark.parametrize("tool", ["uv", "betterleaks"])
def test_a_digest_that_differs_installs_nothing(
    machine: Machine, capsys: pytest.CaptureFixture[str], tool: str
) -> None:
    machine.downloads[getattr(setup, f"{tool.upper()}_URL")] += b"tampered"
    assert setup.main() == 1
    assert not (machine.bin / tool).exists()
    assert not any(argv[0] == "npm" for argv in machine.calls)
    differs = f"{tool}: the download's SHA-256 differs; nothing installed"
    assert _report(capsys)[-1] == f"cloud_setup: failed — {differs}"


def test_an_archive_that_lacks_a_program_fails_naming_it(
    machine: Machine,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    data = _tarball({"uv-x86_64-unknown-linux-gnu/uv": b"uv"})
    machine.downloads[setup.UV_URL] = data
    uv = setup.TOOLS[0]._replace(sha256=hashlib.sha256(data).hexdigest())
    monkeypatch.setattr(setup, "TOOLS", (uv, *setup.TOOLS[1:]))
    assert setup.main() == 1
    assert _report(capsys)[-1] == "cloud_setup: failed — uv: the archive holds no uvx"


def test_a_second_run_skips_each_step(
    machine: Machine, capsys: pytest.CaptureFixture[str]
) -> None:
    assert setup.main() == 0
    capsys.readouterr()
    machine.calls.clear()
    machine.fetched.clear()
    assert setup.main() == 0
    assert machine.installs() == []
    assert machine.fetched == []
    *steps, sandbox, ready = _report(capsys)
    assert steps == [
        "packages: stand",
        "uv: stands",
        "betterleaks: stands",
        "openspec: stands",
        "mf-tmp: stands",
        "ship.toml: stands",
        "skills: stand",
    ]
    assert [sandbox, ready] == ["sandbox: applies", "cloud_setup: ready"]


def test_a_ship_toml_that_stands_is_kept(
    machine: Machine, capsys: pytest.CaptureFixture[str]
) -> None:
    layout.ship_file().parent.mkdir(parents=True)
    layout.ship_file().write_text("[push]\ntags = true\n")
    assert setup.main() == 0
    assert layout.ship_file().read_text() == "[push]\ntags = true\n"
    assert "ship.toml: stands" in _report(capsys)


def test_a_sandbox_that_does_not_apply_fails_the_run(
    machine: Machine,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(platform, "has_sandbox", lambda: False)
    monkeypatch.setattr(platform, "no_sandbox", lambda: "it cannot apply here")
    assert setup.main() == 1
    assert _report(capsys)[-1] == "cloud_setup: failed — sandbox: it cannot apply here"


@pytest.mark.parametrize(
    ("program", "step"),
    [("apt-get", "packages"), ("npm", "openspec"), ("make", "skills")],
)
def test_a_command_that_fails_ends_the_run_naming_it(
    machine: Machine, capsys: pytest.CaptureFixture[str], program: str, step: str
) -> None:
    machine.failing.add(program)
    assert setup.main() == 1
    assert _report(capsys)[-1] == (
        f"cloud_setup: failed — {step}: {program} exited 1 — it broke"
    )


def test_a_tag_gone_before_the_install_fails_it(
    machine: Machine,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tags = iter([_TAG, None])
    monkeypatch.setattr(setup, "clone_tag", lambda: next(tags))
    assert setup.main() == 1
    assert _report(capsys)[-1] == (
        "cloud_setup: failed — skills: the clone stands on no tag"
    )


def _pyproject_uv() -> str:
    pyproject = tomllib.loads((_REPO / "pyproject.toml").read_text())
    lowest = re.search(r">=([\d.]+)", pyproject["tool"]["uv"]["required-version"])
    assert lowest
    return lowest[1]


def test_the_versions_are_the_repositorys() -> None:
    ci = (_REPO / ".github" / "workflows" / "ci.yml").read_text()
    agents = (_REPO / "AGENTS.md").read_text()
    assert _pyproject_uv() == setup.UV
    assert set(re.findall(r'(?m)^ +version: "([\d.]+)"', ci)) == {setup.UV}
    assert setup.BETTERLEAKS_URL in re.findall(r"curl -fsSLO (\S+)", ci)
    assert re.findall(r'echo "([0-9a-f]{64})  ', ci) == [setup.BETTERLEAKS_SHA256]
    [betterleaks] = re.findall(r"`betterleaks ([\d.]+)`", agents)
    [openspec] = re.findall(r"`@fission-ai/openspec@([\d.]+)`", agents)
    assert (betterleaks, openspec) == (setup.BETTERLEAKS, setup.OPENSPEC)
    assert [tool.url for tool in setup.TOOLS] == [setup.UV_URL, setup.BETTERLEAKS_URL]
    assert [tool.sha256 for tool in setup.TOOLS] == [
        setup.UV_SHA256,
        setup.BETTERLEAKS_SHA256,
    ]


def test_run_ends_a_command_and_reads_a_missing_one_as_127() -> None:
    done = setup.run([sys.executable, "-c", "print('hi')"])
    assert (done.returncode, done.stdout) == (0, "hi\n")
    assert setup.run(["no-such-program-of-mf"]).returncode == 127


def test_clone_tag_reads_the_exact_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    answers = iter(
        [
            subprocess.CompletedProcess([], 0, "v1.2.3\n", ""),
            subprocess.CompletedProcess([], 128, "", "fatal: no tag"),
        ]
    )
    monkeypatch.setattr(setup, "run", lambda argv: next(answers))
    assert setup.clone_tag() == "v1.2.3"
    assert setup.clone_tag() is None
    assert setup.is_root() is (os.geteuid() == 0)


def test_fetch_reads_https_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    def urlopen(url: str, timeout: int) -> io.BytesIO:
        if url.endswith("/gone"):
            raise urllib.error.URLError("refused")
        return io.BytesIO(b"bytes")

    monkeypatch.setattr(setup.urllib.request, "urlopen", urlopen)
    assert setup.fetch("https://example.test/x") == b"bytes"
    with pytest.raises(setup.Failed, match="not https"):
        setup.fetch("http://example.test/x")
    with pytest.raises(setup.Failed, match="refused"):
        setup.fetch("https://example.test/gone")
