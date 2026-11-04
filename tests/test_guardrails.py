"""Guardrail scans: no tracked file holds a home path, and Betterleaks finds a key."""

import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent

# Each needle is built from parts so this file never matches itself.
# Why: 0023-backlog-paydown design B6.
_SHAPES = {
    "home path": re.compile("/(" + "Users" + "|" + "home" + r")/[A-Za-z][\w.-]*"),
}


def _hits(root: Path) -> list[str]:
    """Return one line per shape found in a file `git ls-files` lists under `root`.

    e.g. a home path on line 3 of `a.md` → "a.md:3: home path"
    """
    listed = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True
    ).stdout.decode()
    hits: list[str] = []
    for name in filter(None, listed.split("\0")):
        path = root / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not any(shape.search(text) for shape in _SHAPES.values()):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            hits += [
                f"{name}:{number}: {kind}"
                for kind, shape in _SHAPES.items()
                if shape.search(line)
            ]
    return hits


def test_no_tracked_file_holds_a_home_path_or_a_key() -> None:
    assert _hits(_REPO) == []


def test_the_isolation_fixture_holds_home_under_tmp_path(tmp_path: Path) -> None:
    names = ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "GIT_CONFIG_GLOBAL")
    assert Path.home().is_relative_to(tmp_path)
    assert all(Path(os.environ[name]).is_relative_to(tmp_path) for name in names)

    subprocess.run(["git", "config", "--global", "mf.probe", "yes"], check=True)

    assert "probe = yes" in (Path.home() / ".gitconfig").read_text()


def _noise(size: int, seed: str) -> str:
    """Return `size` URL-safe base64 characters drawn from `seed`'s digest."""
    digest = hashlib.sha512(seed.encode()).digest() * 2
    return base64.urlsafe_b64encode(digest).decode().replace("=", "")[:size]


def _token(size: int, seed: str) -> str:
    """Return `size` letters and digits drawn from `seed`'s digest."""
    return _noise(size, seed).replace("-", "x").replace("_", "y")


def test_betterleaks_finds_a_planted_key(tmp_path: Path) -> None:
    # Each key is built from parts so this file never matches itself.
    aws = base64.b32encode(hashlib.sha256(b"aws").digest()).decode()[:16]
    pem = "\n".join(_noise(64, f"pem{n}").replace("-", "+") for n in range(4))
    planted = [
        ("anthropic-api-key", "sk-" + "an" + "t-api03-" + _noise(93, "a") + "AA"),
        # One token per GitHub prefix the retired guardrail held.
        ("github-pat", "gh" + "p_" + _token(36, "gh")),
        ("github-oauth", "gh" + "o_" + _token(36, "gho")),
        ("github-app-token", "gh" + "u_" + _token(36, "ghu")),
        ("github-app-token", "gh" + "s_" + _token(36, "ghs")),
        ("github-refresh-token", "gh" + "r_" + _token(36, "ghr")),
        ("github-fine-grained-pat", "github" + "_pat_" + _token(82, "pat")),
        # A lone id fails the gate by MF's own rule; the default needs its secret.
        *(("aws-access-key-id", p + "IA" + aws) for p in ("AK", "AS")),
        (
            "aws-access-token",
            "AK"
            + "IA"
            + aws
            + "\naws_secret_access_key = "
            + base64.b64encode(hashlib.sha256(b"aws-secret").digest()).decode()[:40],
        ),
        (
            "private-key",
            "-----BEGIN RSA " + "PRIVATE KEY-----\n" + pem + "\n-----END RSA "
            "PRIVATE KEY-----",
        ),
    ]
    scanned = tmp_path / "scanned"
    scanned.mkdir()
    for number, (rule, key) in enumerate(planted):
        (scanned / f"{number}-{rule}.txt").write_text(f"value: {key}\n")
    report = tmp_path / "report.json"

    # The gate's own config, so a rule it drops fails here.
    done = subprocess.run(
        ["betterleaks", "dir", str(scanned), "--no-banner", "--redact"]
        + ["--config", str(_REPO / ".betterleaks.toml")]
        + ["--report-format", "json", "--report-path", str(report)],
        capture_output=True,
        text=True,
    )

    assert done.returncode == 1, done.stderr
    found: dict[str, set[str]] = {}
    for hit in json.loads(report.read_text()):
        found.setdefault(Path(hit["File"]).name, set()).add(hit["RuleID"])
    missed = [
        f"{number}-{rule}.txt"
        for number, (rule, _) in enumerate(planted)
        if rule not in found.get(f"{number}-{rule}.txt", set())
    ]
    assert missed == []
    assert set().union(*found.values()) == {rule for rule, _ in planted}
    assert not any(key in report.read_text() for _, key in planted)


_TEMPLATES = _REPO / "skills" / "mf-bootstrap" / "templates"


def _ignored_sample(pattern: str) -> str:
    """Return a path the `.gitignore` line `pattern` ignores.

    e.g. "*.py[cod]" → "x.pyc"; ".venv/" → ".venv/x"
    """
    name = re.sub(r"\[(.)[^]]*\]", r"\1", pattern).replace("*", "x")
    return name + "x" if name.endswith("/") else name


@pytest.mark.parametrize(
    ("ignore", "config", "named"),
    [
        (_REPO / ".gitignore", _REPO / ".betterleaks.toml", (".env", ".venv/")),
        (
            _TEMPLATES / ".gitignore.tmpl",
            _TEMPLATES / ".betterleaks.toml.tmpl",
            (".env", ".venv/", "node_modules/"),
        ),
    ],
)
def test_the_gate_scan_skips_what_git_ignores(
    tmp_path: Path, ignore: Path, config: Path, named: tuple[str, ...]
) -> None:
    # A key in every path the `.gitignore` names, and one in a file git tracks.
    lines = [line.strip() for line in ignore.read_text().splitlines()]
    patterns = [line for line in lines if line and not line.startswith("#")]
    assert set(named) <= set(patterns)
    scanned = tmp_path / "scanned"
    scanned.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=scanned, check=True)
    shutil.copy(ignore, scanned / ".gitignore")
    shutil.copy(config, scanned / ".betterleaks.toml")
    key = "gh" + "p_" + _token(36, "ignored")
    for name in [*map(_ignored_sample, patterns), "tracked.txt"]:
        (scanned / name).parent.mkdir(parents=True, exist_ok=True)
        (scanned / name).write_text(f"token: {key}\n")
    listed = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard"],
        cwd=scanned,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    report = tmp_path / "report.json"

    done = subprocess.run(
        ["betterleaks", "dir", ".", "--no-banner", "--redact"]
        + ["--report-format", "json", "--report-path", str(report)],
        cwd=scanned,
        capture_output=True,
        text=True,
    )

    assert done.returncode == 1, done.stderr
    # Git would track the one file the scan reports, and no other key.
    hits = {Path(hit["File"]).as_posix() for hit in json.loads(report.read_text())}
    assert hits == {"tracked.txt"}
    assert {name for name in listed if key in (scanned / name).read_text()} == hits


def test_the_guardrail_scan_reports_a_planted_path_and_key(tmp_path: Path) -> None:
    # A staged file is listed before any commit; an untracked one is not.
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    planted = (
        ("See /" + "Users/someone/notes.", "home path"),
        ("Home: `/" + "home/someone`.", "home path"),
    )
    text = "\n".join(("Read me.", *(line for line, _ in planted)))
    (tmp_path / "notes.md").write_text(text)
    (tmp_path / "loose.md").write_text(text)
    subprocess.run(["git", "add", "notes.md"], cwd=tmp_path, check=True)

    assert _hits(tmp_path) == [
        f"notes.md:{number}: {kind}"
        for number, (_, kind) in enumerate(planted, start=2)
    ]
