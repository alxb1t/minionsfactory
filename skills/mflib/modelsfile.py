"""Write and parse a change's models file: its tables, its keys, its hash and its text.

Each function does what the copy it replaces does. Why: 0142-models design D1 and D3.
"""

import contextlib
import hashlib
import os
import re
import tomllib
from pathlib import Path

from . import layout, statefile

# The tables of a models file, by the part of a models line that names each.
# Why: 0106-cut-scripts design D2; no `cut`: 0142-models design D11.
TABLES = {
    "build": "build",
    "build-moderate": "build.moderate",
    "converge": "converge",
    "conformance": "converge.conformance",
    "adversarial": "converge.adversarial",
    "fix": "converge.fix",
    "release": "release",
}
TOKEN = re.compile(r"[A-Za-z0-9._-]+")
# A cut's worker table under its old name. Why: 0095-converge-roles design D2.
OLD_WORKERS = {
    "converge.conformance": "converge.review",
    "converge.adversarial": "converge.security",
}


class Broken(ValueError):
    """Say what is wrong with a models file, as a phrase."""


def text(decided: bool, named: dict[str, list[str]], shadowed: bool) -> str:
    """Return the models file as TOML: one table per part of `TABLES`, in its order.

    e.g. {"build": ["codex/m", "high"]} → `[build]`, `model = "m"`, `effort = "high"`,
    `executor = "codex"`, a line each. Why: 0106 design D2; 0142-models design D1.
    """
    blocks = ['decide = "recommended"'] if decided else []
    for name, table in TABLES.items():
        if (rest := named.get(name)) is None:
            continue
        lines = [f"[{table}]"]
        if rest == ["skip"]:
            lines.append("skip = true")
        else:
            host, slash, model = rest[0].rpartition("/")
            lines += [f'model = "{model}"', f'effort = "{rest[1]}"']
            lines += [f'executor = "{host}"'] if slash else []
        lines += ["shadow = true"] if name == "converge" and shadowed else []
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def read(primary: Path, change: str) -> dict[str, object]:
    """Return the change's models file as TOML reads it; {} with no file.

    Text TOML refuses raises `Broken`. Why: 0142-models design D1.
    """
    path = layout.models_file(primary, change)
    if not path.is_file():
        return {}
    try:
        return tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        raise Broken(str(error)) from None


def table(data: dict[str, object], name: str) -> dict[str, object] | None:
    """Return a table of the parsed file; None for no such table.

    A dotted name walks in: e.g. "converge.fix" → `[converge]`'s `fix` table.
    """
    found: object = data
    for part in name.split("."):
        found = found.get(part) if isinstance(found, dict) else None
    return found if isinstance(found, dict) else None


def decides(data: dict[str, object]) -> bool:
    """Return whether the file says `decide = "recommended"` at its top.

    Why: 0085-self-healing-ship design D3.
    """
    return data.get("decide") == "recommended"


def shadows(data: dict[str, object]) -> bool:
    """Return whether the file says `[converge] shadow = true`.

    Why: 0097-cross-model design D3.
    """
    found = table(data, "converge")
    return found is not None and found.get("shadow") is True


def rescue_skips(data: dict[str, object]) -> bool:
    """Return whether the file says `[rescue] skip = true`."""
    found = table(data, "rescue")
    return found is not None and found.get("skip") is True


def auto_grants(data: dict[str, object]) -> bool:
    """Return whether the run may grant a cap: no `[converge] auto_grant = false`.

    Why: 0070-cap-policy design D4.
    """
    found = table(data, "converge")
    return found is None or found.get("auto_grant") is not False


def skipping(data: dict[str, object], names: tuple[str, ...]) -> frozenset[str]:
    """Return the tables of `names` that say `skip = true`.

    e.g. `[converge.adversarial] skip = true` → {"converge.adversarial"}
    """
    return frozenset(
        name
        for name in names
        if (found := table(data, name)) and found.get("skip") is True
    )


def _folder(primary: Path, change: str) -> int:
    """Return a descriptor on the change's folder, made, none of its parts a link."""
    return statefile.folder(layout.run_dir(primary), layout.CHANGES, change)


def digest(primary: Path, change: str) -> str | None:
    """Return the sha256 of the change's models file, read through no link.

    None when the file is missing, a link, or its folder is one. Why: 0106 design D7.
    """
    try:
        fd = _folder(primary, change)
        try:
            file = os.open(layout.MODELS, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        finally:
            os.close(fd)
    except OSError:
        return None
    with os.fdopen(file, "rb") as models:
        return hashlib.sha256(models.read()).hexdigest()


def _remove(primary: Path, change: str) -> None:
    """Remove the change's models file when it stands, through no link."""
    fd = _folder(primary, change)
    try:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(layout.MODELS, dir_fd=fd)
    finally:
        os.close(fd)


def write(primary: Path, change: str, text: str) -> None:
    """Write the change's models file from `text`, removed then made; raise `OSError`.

    Truncating the old file would write through a hard link. Why: 0106 design D7.
    """
    _remove(primary, change)
    fd = _folder(primary, change)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        file = os.open(layout.MODELS, flags, 0o644, dir_fd=fd)
    finally:
        os.close(fd)
    with os.fdopen(file, "w") as out:
        out.write(text)
