"""Write and parse a change's models file: its tables, its keys, its hash and its text.

Why: 0142-models design D1, D4 to D8.
"""

import errno
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
    "build-close": "build.close",
    "converge": "converge",
    "conformance": "converge.conformance",
    "adversarial": "converge.adversarial",
    "fix": "converge.fix",
    "rescue": "rescue",
    "supervise": "supervise",
    "release": "release",
}
TOKEN = re.compile(r"[A-Za-z0-9._-]+")
BOUND = 65536
_PHRASES = {errno.ELOOP: "it is a link", errno.EINVAL: "it is not a regular file"}


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


def load(primary: Path, change: str) -> bytes | None:
    """Return the change's models file's bytes, read once; None with no file.

    A link, no regular file, a file over `BOUND` bytes or one not UTF-8 raises
    `Broken`. Why: 0142-models design D6.
    """
    try:
        fd = statefile.open_folder(layout.run_dir(primary), layout.CHANGES, change)
    except FileNotFoundError:
        return None
    except OSError as error:
        raise Broken(f"its folder cannot be opened: {error.strerror}") from None
    try:
        data = statefile.read_bytes(layout.MODELS, folder=fd, limit=BOUND + 1)
    except FileNotFoundError:
        return None
    except OSError as error:
        raise Broken(_PHRASES.get(error.errno, str(error.strerror))) from None
    finally:
        os.close(fd)
    if len(data) > BOUND:
        raise Broken(f"it is over {BOUND} bytes")
    try:
        data.decode()
    except UnicodeDecodeError:
        raise Broken("it is not UTF-8") from None
    return data


def read(primary: Path, change: str) -> dict[str, object]:
    """Return the change's models file parsed; {} with no file.

    A broken file raises `Broken`, as does a `model` or `effort` string of a table of
    `TABLES` that is no token. Why: 0142-models design D5 and D6.
    """
    if (data := load(primary, change)) is None:
        return {}
    try:
        parsed = tomllib.loads(data.decode())
    except tomllib.TOMLDecodeError as error:
        raise Broken(str(error)) from None
    except RecursionError:
        # why: 3.12's parser recurses per nested array; 0142-models adversarial S1.
        raise Broken("it nests too deep") from None
    for name in TABLES.values():
        found = table(parsed, name) or {}
        for word in (found.get("model"), found.get("effort")):
            if isinstance(word, str) and not TOKEN.fullmatch(word):
                raise Broken(f"{name} {word!r} is not a model or effort")
    return parsed


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


def digest(primary: Path, change: str) -> str | None:
    """Return the sha256 of the bytes `load` reads; None with no file.

    A broken file raises `Broken`. Why: 0142-models design D7.
    """
    data = load(primary, change)
    return None if data is None else hashlib.sha256(data).hexdigest()


def write(primary: Path, change: str, text: str) -> None:
    """Write the change's models file from `text`, staged and refusing a link.

    A failure raises `statefile.WriteFailed`. Why: 0142-models design D8.
    """
    try:
        fd = statefile.folder(layout.run_dir(primary), layout.CHANGES, change)
    except OSError as error:
        raise statefile.WriteFailed("create", error) from error
    try:
        statefile.write(Path(layout.MODELS), text, refuse_link=True, folder=fd)
    finally:
        os.close(fd)
