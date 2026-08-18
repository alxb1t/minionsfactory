"""Run-from-source entry: `python -m orchestrator run --repo <target>`."""

import argparse
import sys
from collections.abc import Callable
from functools import partial
from pathlib import Path

from orchestrator.driver import RunStatus, run
from orchestrator.gate import SubprocessGate
from orchestrator.provider import ClaudeCodeProvider, Profile
from orchestrator.status import Event, emit, render

_CODER_PROFILE = Profile(
    permission_mode="default",
    allowed_tools=("Edit", "Write", "Bash"),
)


def _read_vault_dir(repo: Path) -> Path:
    """Read VAULT_PROJECT_DIR from the target repo's .env."""
    for line in (repo / ".env").read_text().splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == "VAULT_PROJECT_DIR":
            return Path(value.strip().strip('"'))
    raise SystemExit("VAULT_PROJECT_DIR not found in the target repo's .env")


def _coder_prompt() -> str:
    """Load the coder role prompt shipped with this repo."""
    return (
        Path(__file__).resolve().parent.parent / "prompts" / "coder-per-phase.md"
    ).read_text()


def emit_and_render(stream: Path, status: Path, event: Event) -> None:
    """Record an event to disk and render it live to stdout."""
    emit(stream, status, event)
    print(render(event))


def _make_emitter(repo: Path) -> Callable[[Event], None]:
    """Build the disk+stdout status sink rooted at the target's .minions/."""
    minions = repo / ".minions"
    minions.mkdir(exist_ok=True)
    stream, status = minions / "events.jsonl", minions / "status.json"
    stream.write_text("")
    return partial(emit_and_render, stream, status)


def main(argv: list[str] | None = None) -> int:
    """Parse args and drive the target repo's plan; return a process exit code."""
    parser = argparse.ArgumentParser(prog="orchestrator")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="drive the target repo's plan")
    run_parser.add_argument(
        "--repo", type=Path, required=True, help="path to the target repo"
    )
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    result = run(
        repo=repo,
        vault_project_dir=_read_vault_dir(repo),
        provider=ClaudeCodeProvider(),
        gate=SubprocessGate(),
        coder_prompt=_coder_prompt(),
        profile=_CODER_PROFILE,
        emit_event=_make_emitter(repo),
    )
    print(
        f"{result.status.name}: {result.reason} "
        f"(phases advanced: {result.phases_advanced})"
    )
    return 0 if result.status is RunStatus.COMPLETE else 1


if __name__ == "__main__":
    sys.exit(main())
