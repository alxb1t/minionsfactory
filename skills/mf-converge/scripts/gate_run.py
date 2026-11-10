# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Run `make gate`, record a green run by its tree, and reuse the record.

    gate_run.py [--fresh] [--tree <path>]

Why: 0064-lighter-catch-up design D1; 0100-worker-diet design D10.
"""

import argparse
import hashlib
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


class Stop(Exception):
    """End the run with `code`; the message is what it prints."""

    def __init__(self, code: int, message: str) -> None:
        """Keep the exit code beside the message."""
        super().__init__(message)
        self.code = code


def _run(
    argv: list[str], env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Return a command's result, its output captured; a missing tool stops the run."""
    try:
        return subprocess.run(argv, capture_output=True, text=True, env=env)
    except FileNotFoundError:
        raise Stop(2, f"gate: cannot run — {argv[0]} is missing") from None


def _make_env() -> dict[str, str]:
    """Return this environment without `VIRTUAL_ENV`, which `uv run --script` sets."""
    return {key: value for key, value in os.environ.items() if key != "VIRTUAL_ENV"}


def _git(*args: str) -> str:
    """Return a git command's stdout; a failure stops the run with exit 2."""
    done = _run(["git", *args])
    if done.returncode != 0:
        lines = [line for line in done.stderr.splitlines() if line.strip()]
        first = lines[0] if lines else f"exit {done.returncode}"
        raise Stop(2, f"gate: cannot run — git {args[0]} failed: {first}")
    return done.stdout


def records() -> Path:
    """Return `.minions/gate` beside the primary checkout, from any worktree."""
    common = _git("rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common.strip()).parent / ".minions" / "gate"


def settled_tree() -> str | None:
    """Return the index's tree when the worktree is settled, else None."""
    if _run(["git", "diff", "--quiet"]).returncode != 0:
        return None
    if _git("ls-files", "--others", "--exclude-standard").strip():
        return None
    return _git("write-tree").strip()


def dry_run() -> str:
    """Return the sha256 of `make -n gate`'s output; a failure stops with its code."""
    done = _run(["make", "-n", "gate"], _make_env())
    if done.returncode != 0:
        sys.stderr.write(done.stderr)
        raise Stop(done.returncode, "gate: cannot run — `make -n gate` failed")
    return hashlib.sha256(done.stdout.encode()).hexdigest()


def read_record(path: Path) -> dict[str, str]:
    """Return a record's `key: value` lines; a missing file has none.

    e.g. the lines "dry: 9f…", "seconds: 382" → {"dry": "9f…", "seconds": "382"}
    """
    try:
        text = path.read_text()
    except OSError:
        return {}
    pairs = (line.partition(": ") for line in text.splitlines())
    return {key: value for key, _, value in pairs}


def write_record(path: Path, dry: str, seconds: int) -> str | None:
    """Write the record of a green run, replacing any record of the same tree."""
    if path.parent.is_symlink():
        return ".minions/gate is a link"
    path.parent.mkdir(parents=True, exist_ok=True)
    date = datetime.now(UTC).isoformat(timespec="seconds")
    staged = path.with_name(f"{path.name}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        staged.unlink(missing_ok=True)
        with os.fdopen(os.open(staged, flags, 0o644), "w") as file:
            file.write(f"dry: {dry}\ndate: {date}\nseconds: {seconds}\n")
    except OSError:
        return f"{staged.name} could not be created"
    staged.replace(path)
    return None


def gate(fresh: bool) -> int:
    """Reuse a record or run `make gate`; return the exit code."""
    tree, dry = settled_tree(), dry_run()
    if tree is not None and not fresh:
        record = read_record(records() / tree)
        if record.get("dry") == dry:
            seconds, date = record.get("seconds", "?"), record.get("date", "?")
            print(f"gate: reused — {tree} · {seconds}s · {date}")
            return 0
    start = time.monotonic()
    done = subprocess.run(
        ["make", "gate"],
        env=_make_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
    )
    code = done.returncode
    seconds = round(time.monotonic() - start)
    if code != 0:
        sys.stdout.write(done.stdout)
        print(f"gate: red — exit {code} · {seconds}s")
        return code
    # The gate may write the worktree; record only the tree it started and ended on.
    if tree is None or settled_tree() != tree or dry_run() != dry:
        print(f"gate: green — unrecorded, the worktree is not settled · {seconds}s")
        return 0
    if refused := write_record(records() / tree, dry, seconds):
        print(f"gate: green — unrecorded, {refused} · {seconds}s")
        return 0
    print(f"gate: green — {tree} · {seconds}s")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the gate in the current directory or `--tree`; return its exit code."""
    parser = argparse.ArgumentParser(description="Run make gate, or reuse its record.")
    parser.add_argument(
        "--fresh", action="store_true", help="run make gate whatever stands recorded"
    )
    parser.add_argument(
        "--tree", type=Path, help="gate this worktree, not the current directory"
    )
    args = parser.parse_args(argv)
    try:
        if args.tree is not None:
            try:
                os.chdir(args.tree)
            except OSError as error:
                raise Stop(
                    2, f"gate: cannot run — {args.tree}: {error.strerror}"
                ) from None
        return gate(args.fresh)
    except Stop as stop:
        print(stop)
        return stop.code


if __name__ == "__main__":
    sys.exit(main())
