"""Read the price table: each model's row of dollars per million tokens.

Why: 0162-metric-scripts design D4.
"""

import errno
import tomllib
from pathlib import Path

from . import statefile

BOUND = 262_144
_PHRASES = {errno.ELOOP: "it is a link", errno.EISDIR: "it is not a file"}


class Unreadable(Exception):
    """Say why the price table cannot be read."""

    def __init__(self, reason: str) -> None:
        """Hold the reason."""
        super().__init__(reason)
        self.reason = reason


def _text(path: Path) -> str:
    """Return the file's text through no link; a bad file raises `Unreadable`.

    e.g. a link → "it is a link"; a file over `BOUND` bytes → "it is over 262144 bytes"
    """
    try:
        data = statefile.read_bytes(path, limit=BOUND + 1)
    except OSError as error:
        reason = _PHRASES.get(error.errno or 0, str(error.strerror))
        raise Unreadable(reason) from error
    if len(data) > BOUND:
        raise Unreadable(f"it is over {BOUND} bytes")
    try:
        return data.decode()
    except UnicodeDecodeError as error:
        raise Unreadable(str(error)) from error


def _number(price: object) -> bool:
    """Return whether a price is a number; a bool is none."""
    return isinstance(price, int | float) and not isinstance(price, bool)


def rows(path: Path) -> dict[str, dict[str, float]]:
    """Return the `[models]` table as a row of numbers by model.

    A row that is no table, or holds a price that is no number, is left out.
    A file it may not read, or holds no `models` table, raises `Unreadable`.
    """
    try:
        table = tomllib.loads(_text(path))
    except tomllib.TOMLDecodeError as error:
        raise Unreadable(str(error)) from error
    models = table.get("models")
    if not isinstance(models, dict):
        raise Unreadable("no models table")
    return {
        model: row
        for model, row in models.items()
        if isinstance(row, dict) and all(map(_number, row.values()))
    }
