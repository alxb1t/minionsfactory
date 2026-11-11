# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Run this repo's readers of run data over the run directory, one case at a time.

Exit 0 pass · 1 a run failed · 2 unreadable. Why: 0103-fewer-rounds design D5.
"""

import argparse
import fcntl
import os
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any

TIMEOUT_SECONDS = 300
SHOWN = 5
DEFAULT = "scripts/corpus.toml"
NAME = re.compile(r"[a-z0-9-]+")


class Stop(Exception):
    """End the run with exit 2; the message says what could not be read."""


def _git(root: Path, *argv: str) -> str:
    """Return a git command's stdout, run in `root`; a failure stops."""
    try:
        done = subprocess.run(
            ["git", *argv],
            cwd=root,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        raise Stop("git is missing") from None
    if done.returncode:
        first = done.stderr.strip().partition("\n")[0]
        raise Stop(f"git {argv[0]} failed: {first}")
    return done.stdout.strip()


def _strings(value: object) -> bool:
    """Return whether `value` is a list of strings."""
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def broken(case: dict[str, Any]) -> str | None:
    """Return how a case breaks the schema, or None when it holds."""
    name = case.get("name")
    if not isinstance(name, str) or not NAME.fullmatch(name):
        return "a name is not [a-z0-9-]+"
    if not isinstance(case.get("reads"), str):
        return f"{name}: reads is not prose"
    argv = case.get("argv")
    if not argv or not _strings(argv):
        return f"{name}: argv is not a non-empty list of strings"
    each = case.get("each", [])
    unsafe = (
        [g for g in each if PurePosixPath(g).is_absolute()] if _strings(each) else []
    )
    if (
        not _strings(each)
        or unsafe
        or any(".." in PurePosixPath(g).parts for g in each)
    ):
        return f"{name}: each is not a list of globs under the run directory"
    if "shape" in case:
        try:
            re.compile(case["shape"])
        except (TypeError, re.error):
            return f"{name}: shape is not a regex"
    return None


def load(path: Path, shown: str) -> list[dict[str, Any]]:
    """Return the cases of a cases file; one unreadable or off the schema stops."""
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except OSError as error:
        raise Stop(f"{shown}: {error.strerror}") from None
    except tomllib.TOMLDecodeError as error:
        raise Stop(f"{shown}: {error}") from None
    cases = data.get("case")
    if (
        not isinstance(cases, list)
        or not cases
        or not all(isinstance(c, dict) for c in cases)
    ):
        raise Stop(f"{shown}: no [[case]]")
    for case in cases:
        if why := broken(case):
            raise Stop(f"{shown}: {why}")
    return cases


def inputs(case: dict[str, Any], minions: Path) -> Sequence[Path | None]:
    """Return each input of a case, sorted; `[None]` for the one run of no `each`.

    A link, and a file whose real path leaves the run directory, is no input.
    """
    if "each" not in case:
        return [None]
    base = minions.resolve()
    found = {
        path
        for pattern in case["each"]
        for path in minions.glob(pattern)
        if path.is_file()
        and not path.is_symlink()
        and path.resolve().is_relative_to(base)
    }
    return sorted(found)


def run_case(case: dict[str, Any], minions: Path, root: Path) -> tuple[list[str], int]:
    """Return a case's lines, and how many of its runs failed."""
    name = case["name"]
    if (minions / "corpus" / name).is_symlink():
        raise Stop(f"corpus/{name} is a link")
    found = inputs(case, minions)
    shape = re.compile(case["shape"], re.MULTILINE) if "shape" in case else None
    kept = [
        p
        for p in found
        if shape is None or p is None or shape.search(p.read_text(errors="replace"))
    ]
    skipped = len(found) - len(kept)
    found = kept
    if not found:
        return [f"corpus: {name} · no input"], 0
    lines: list[str] = []
    failed = 0
    for number, path in enumerate(found, 1):
        out = minions / "corpus" / name / str(number)
        shutil.rmtree(out, ignore_errors=True)
        out.mkdir(parents=True)
        values = {
            "minions": str(minions),
            "primary": str(minions.parent),
            "input": "" if path is None else str(path),
            "out": str(out),
        }
        argv = list(case["argv"])
        for key, value in values.items():
            argv = [arg.replace("{" + key + "}", value) for arg in argv]
        shown = "once" if path is None else path.relative_to(minions).as_posix()
        try:
            done = subprocess.run(
                argv,
                cwd=root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                timeout=TIMEOUT_SECONDS,
            )
            code, stderr = done.returncode, done.stderr.splitlines()
        except subprocess.TimeoutExpired:
            lines.append(f"corpus: {name} · {shown} · timed out")
            failed += 1
            continue
        except OSError as error:
            code, stderr = 127, [str(error.strerror)]
        if code:
            failed += 1
            lines.append(f"corpus: {name} · {shown} · exit {code}")
            lines += [f"  | {line}" for line in stderr[:SHOWN]]
    result = "pass" if not failed else f"{failed} failed"
    gone = f" · {skipped} skipped" if skipped else ""
    return [*lines, f"corpus: {name} · {len(found)} runs{gone} · {result}"], failed


@contextmanager
def _locked(minions: Path) -> Iterator[None]:
    """Hold an exclusive lock on `corpus.lock` in `minions` while the body runs.

    A link at that name, or a file that cannot be opened, is a `Stop`.
    """
    # why: 0112-uv-race design D4
    flags = os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW
    try:
        fd = os.open(minions / "corpus.lock", flags, 0o600)
    except OSError as error:
        raise Stop(f"corpus.lock cannot be opened: {error.strerror}") from None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def run(cases: Path | None, minions: Path | None) -> int:
    """Run every case; return the exit code, 2 by `Stop`."""
    root = Path(_git(Path.cwd(), "rev-parse", "--show-toplevel"))
    if minions is None:
        common = _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
        minions = Path(common).parent / ".minions"
    minions = minions.absolute()
    if minions.is_symlink() or (minions / "corpus").is_symlink():
        raise Stop("the run directory or its corpus/ is a link")
    shown = str(cases) if cases else DEFAULT
    loaded = load(cases or root / DEFAULT, shown)
    minions.mkdir(parents=True, exist_ok=True)
    failed = 0
    with _locked(minions):
        for case in loaded:
            lines, count = run_case(case, minions, root)
            print(*lines, sep="\n")
            failed += count
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    """Run the corpus from inside the repository; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Run this repo's readers of run data over the run directory."
    )
    parser.add_argument("--cases", type=Path, help=f"the cases file, {DEFAULT}")
    parser.add_argument("--minions", type=Path, help="the run directory")
    args = parser.parse_args(argv)
    try:
        return run(args.cases, args.minions)
    except Stop as stop:
        print(f"corpus: cannot run — {stop}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
