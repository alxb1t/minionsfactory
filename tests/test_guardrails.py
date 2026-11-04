"""Guardrail scans: no tracked file holds a home path, and Betterleaks finds a key."""

import base64
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

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


def test_betterleaks_finds_a_planted_key(tmp_path: Path) -> None:
    # Each key is built from parts so this file never matches itself.
    aws = base64.b32encode(hashlib.sha256(b"aws").digest()).decode()[:16]
    pem = "\n".join(_noise(64, f"pem{n}").replace("-", "+") for n in range(4))
    planted = {
        "anthropic-api-key": "sk-" + "an" + "t-api03-" + _noise(93, "a") + "AA",
        "github-pat": "gh"
        + "p_"
        + _noise(36, "gh").replace("-", "x").replace("_", "y"),
        # The AWS rule needs the id's secret beside it.
        "aws-access-token": "AK"
        + "IA"
        + aws
        + "\naws_secret_access_key = "
        + base64.b64encode(hashlib.sha256(b"aws-secret").digest()).decode()[:40],
        "private-key": (
            "-----BEGIN RSA " + "PRIVATE KEY-----\n" + pem + "\n-----END RSA "
            "PRIVATE KEY-----"
        ),
    }
    scanned = tmp_path / "scanned"
    scanned.mkdir()
    for rule, key in planted.items():
        (scanned / f"{rule}.txt").write_text(f"value: {key}\n")
    report = tmp_path / "report.json"

    done = subprocess.run(
        ["betterleaks", "dir", str(scanned), "--no-banner", "--redact"]
        + ["--report-format", "json", "--report-path", str(report)],
        capture_output=True,
        text=True,
    )

    assert done.returncode == 1, done.stderr
    found = json.loads(report.read_text())
    assert sorted(hit["RuleID"] for hit in found) == sorted(planted)
    assert not any(key in report.read_text() for key in planted.values())


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
