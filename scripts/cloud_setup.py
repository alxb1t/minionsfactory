# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Make a cloud Linux machine ready for a run of MF, as root, from a clone at a tag.

Exit 0 ready · 1 a step failed · 2 refused. Why: 0137-cloud-session design D6.
"""

import hashlib
import io
import os
import re
import subprocess
import sys
import tarfile
import urllib.request
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills"))
import mflib.layout
import mflib.platform

TIMEOUT = 900
ROOT = Path(__file__).resolve().parents[1]
BIN = Path("/usr/local/bin")
FOLDER = "mf-tmp"
SHIP_TOML = "[push]\ntags = false\n"
PACKAGES = ("bubblewrap", "socat", "procps")
UV = "0.12.19"
BETTERLEAKS = "1.9.0"
OPENSPEC = "1.11.0"
# why: each download is checked before a byte is unpacked; 0137-cloud-session design D8
UV_URL = (
    "https://github.com/astral-sh/uv/releases/download/"
    f"{UV}/uv-x86_64-unknown-linux-gnu.tar.gz"
)
UV_SHA256 = "23bf5552d220e0842b65c862097b2ebaeba0064b74eda5e565e77fd25969d8c8"
BETTERLEAKS_URL = (
    "https://github.com/betterleaks/betterleaks/releases/download/"
    f"v{BETTERLEAKS}/betterleaks_{BETTERLEAKS}_linux_x64.tar.gz"
)
BETTERLEAKS_SHA256 = "f8b185a39ffcece2a1ca82bf3a4e7435cd81963ffd16b7a9128daf75f35f6de7"


class Failed(Exception):
    """End the run with exit 1; the message names the step and what failed."""


class Tool(NamedTuple):
    """A tool fetched as a tarball: its version, URL, digest and programs."""

    name: str
    version: str
    url: str
    sha256: str
    programs: tuple[str, ...]  # the files unpacked into `BIN`, by base name
    asks: tuple[str, ...]  # the arguments that print its version


TOOLS = (
    Tool("uv", UV, UV_URL, UV_SHA256, ("uv", "uvx"), ("--version",)),
    Tool(
        "betterleaks",
        BETTERLEAKS,
        BETTERLEAKS_URL,
        BETTERLEAKS_SHA256,
        ("betterleaks",),
        ("version",),
    ),
)


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """Return the ended command `argv`; one that cannot start or end exits 127."""
    try:
        return subprocess.run(
            argv, capture_output=True, text=True, errors="replace", timeout=TIMEOUT
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return subprocess.CompletedProcess(argv, 127, "", str(error))


def fetch(url: str) -> bytes:
    """Return the bytes at the `https` URL `url`; another scheme or an error fails."""
    if not url.startswith("https://"):
        raise Failed(f"{url}: not https")
    try:
        # why: the scheme is checked above; 0137-cloud-session design D6
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:  # noqa: S310
            return response.read()
    except OSError as error:
        raise Failed(f"{url}: {error}") from None


def _ok(done: subprocess.CompletedProcess[str], step: str) -> None:
    """Fail naming `step`, the program and its last error line, when `done` failed."""
    if done.returncode:
        last = (done.stderr.strip().splitlines() or ["no output"])[-1]
        raise Failed(f"{step}: {done.args[0]} exited {done.returncode} — {last}")


def _prints(argv: list[str], version: str) -> bool:
    """Return whether `argv` ends well and prints `version`, a `v` before it or not."""
    done = run(argv)
    found = re.search(rf"(?<![\w.])v?{re.escape(version)}(?![\w.])", done.stdout)
    return done.returncode == 0 and found is not None


def is_root() -> bool:
    """Return whether the script runs as root."""
    return os.geteuid() == 0


def clone_tag() -> str | None:
    """Return the tag the clone stands on, or None for none."""
    done = run(["git", "-C", str(ROOT), "describe", "--tags", "--exact-match"])
    if done.returncode:
        return None
    return done.stdout.strip() or None


def refuse() -> str | None:
    """Return why the script refuses this machine, or None for Linux, root and a tag."""
    if mflib.platform.OS != "linux":
        return "not Linux"
    if not is_root():
        return "not root"
    if clone_tag() is None:
        return "the clone stands on no tag: clone MinionsFactory at a tag"
    return None


def install_packages() -> list[str]:
    """Install by `apt-get` the packages `dpkg` lacks; return the report line."""
    missing = [name for name in PACKAGES if run(["dpkg", "-s", name]).returncode]
    if not missing:
        return ["packages: stand"]
    _ok(run(["apt-get", "update"]), "packages")
    _ok(run(["apt-get", "install", "-y", *missing]), "packages")
    return [f"packages: installed {', '.join(missing)}"]


def _unpack(tool: Tool, data: bytes) -> None:
    """Write the tool's programs out of the tarball `data` into `BIN`, by base name."""
    wanted = set(tool.programs)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        members = [
            member
            for member in archive.getmembers()
            if member.isfile() and PurePosixPath(member.name).name in wanted
        ]
        for member in members:
            source = archive.extractfile(member)
            target = BIN / PurePosixPath(member.name).name
            target.write_bytes(source.read() if source else b"")
            target.chmod(0o755)
    unpacked = {PurePosixPath(member.name).name for member in members}
    if lacking := sorted(wanted - unpacked):
        raise Failed(f"{tool.name}: the archive holds no {', '.join(lacking)}")


def install_tools() -> list[str]:
    """Install each fetched tool that prints no version; return the report lines."""
    lines: list[str] = []
    for tool in TOOLS:
        if _prints([tool.name, *tool.asks], tool.version):
            lines.append(f"{tool.name}: stands")
            continue
        data = fetch(tool.url)
        if hashlib.sha256(data).hexdigest() != tool.sha256:
            raise Failed(
                f"{tool.name}: the download's SHA-256 differs; nothing installed"
            )
        _unpack(tool, data)
        lines.append(f"{tool.name}: installed {tool.version}")
    return lines


def install_openspec() -> list[str]:
    """Install the OpenSpec CLI at its version by `npm`; return the report line."""
    if _prints(["openspec", "--version"], OPENSPEC):
        return ["openspec: stands"]
    _ok(run(["npm", "install", "-g", f"@fission-ai/openspec@{OPENSPEC}"]), "openspec")
    return [f"openspec: installed {OPENSPEC}"]


def make_folder() -> list[str]:
    """Make the run's temporary folder under the home; return the report line."""
    folder = Path.home() / FOLDER
    if folder.is_dir():
        return [f"{FOLDER}: stands"]
    folder.mkdir(parents=True)
    return [f"{FOLDER}: made {folder}"]


def write_ship_toml() -> list[str]:
    """Write `ship.toml`, pushing no tag, where none stands; return the report line."""
    path = mflib.layout.ship_file()
    if path.exists():
        return ["ship.toml: stands"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(SHIP_TOML, encoding="utf-8")
    return [f"ship.toml: written {path}"]


def install_skills() -> list[str]:
    """Install MF's skills at the clone's tag; return the report line."""
    tag = clone_tag()
    if tag is None:
        raise Failed("skills: the clone stands on no tag")
    if (mflib.layout.data_dir() / tag).is_dir():
        return ["skills: stand"]
    _ok(run(["make", "-C", str(ROOT), "install-skills", f"TAG={tag}"]), "skills")
    return [f"skills: installed {tag}"]


def read_back() -> list[str]:
    """Return the line saying the OS sandbox applies; fail naming why it does not."""
    if not mflib.platform.has_sandbox():
        raise Failed(f"sandbox: {mflib.platform.no_sandbox()}")
    return ["sandbox: applies"]


STEPS: tuple[Callable[[], list[str]], ...] = (
    install_packages,
    install_tools,
    install_openspec,
    make_folder,
    write_ship_toml,
    install_skills,
    read_back,
)


def main() -> int:
    """Run each step in order, printing its lines; return the exit code."""
    if reason := refuse():
        print(f"cloud_setup: refused — {reason}", flush=True)
        return 2
    try:
        for step in STEPS:
            for line in step():
                print(line, flush=True)
    except Failed as failed:
        print(f"cloud_setup: failed — {failed}", flush=True)
        return 1
    print("cloud_setup: ready", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
