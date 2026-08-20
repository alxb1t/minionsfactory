"""Run-from-source entry: `python -m orchestrator run --repo <target>`."""

import argparse
import sys
from collections.abc import Callable
from functools import partial
from pathlib import Path

from orchestrator.converge import ConvergeResult, converge
from orchestrator.diff import compute_diff
from orchestrator.driver import RunStatus, run
from orchestrator.fanout import RoleSpec, run_fanout
from orchestrator.findings import FindingsState, read_findings_state
from orchestrator.gate import Gate, SubprocessGate
from orchestrator.provider import ClaudeCodeProvider, Profile, Provider
from orchestrator.state import select_plan
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


def _fanout_roles() -> list[RoleSpec]:
    """Load the three read-only fan-out role prompts (review / security / simplify)."""
    prompts = Path(__file__).resolve().parent.parent / "prompts"
    return [
        RoleSpec("review", (prompts / "reviewer.md").read_text()),
        RoleSpec("security", (prompts / "security.md").read_text()),
        RoleSpec("simplify", (prompts / "simplify.md").read_text()),
    ]


def _plan_version(vault_dir: Path) -> str:
    """Derive the plan version (e.g. 'v0.6') from the highest plan's filename."""
    return select_plan(vault_dir).name.split("_")[0]


def _make_fanout(
    provider: Provider,
    repo: Path,
    vault_dir: Path,
    version: str,
    base: str,
    roles: list[RoleSpec],
    emit_event: Callable[[Event], None],
) -> Callable[[], list[FindingsState | None]]:
    def _fanout() -> list[FindingsState | None]:
        diff = compute_diff(repo, base, "HEAD")
        return run_fanout(
            provider,
            repo,
            vault_dir,
            version,
            diff,
            repo / ".minions" / "diff.patch",
            roles,
            emit_event,
        )

    return _fanout


def _make_converge(
    provider: Provider,
    gate: Gate,
    repo: Path,
    vault_dir: Path,
    version: str,
    roles: list[RoleSpec],
    fixer_prompt: str,
    coder_profile: Profile,
    emit_event: Callable[[Event], None],
) -> Callable[[], ConvergeResult]:
    paths = [
        vault_dir / "implementation_plans" / f"{version}_{r.name}.md" for r in roles
    ]

    def _read_states() -> list[FindingsState | None]:
        return [read_findings_state(p) for p in paths]

    def _run_verify() -> None:
        states = _read_states()
        head = next(s.head for s in states if s is not None)
        diff = compute_diff(repo, head, "HEAD")
        run_fanout(
            provider,
            repo,
            vault_dir,
            version,
            diff,
            repo / ".minions" / "diff.patch",
            roles,
            emit_event,
        )

    return lambda: converge(
        provider,
        gate,
        repo,
        fixer_prompt,
        coder_profile,
        _read_states,
        _run_verify,
        emit_event,
        max_rounds=3,
    )


def main(argv: list[str] | None = None) -> int:
    """Parse args and drive the target repo's plan; return a process exit code."""
    parser = argparse.ArgumentParser(prog="orchestrator")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="drive the target repo's plan")
    run_parser.add_argument(
        "--repo", type=Path, required=True, help="path to the target repo"
    )
    run_parser.add_argument(
        "--base",
        default="main",
        help="git ref the frozen feature diff is taken against (default: main)",
    )
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    vault_dir = _read_vault_dir(repo)
    provider = ClaudeCodeProvider()
    gate = SubprocessGate()
    emitter = _make_emitter(repo)
    version = _plan_version(vault_dir)
    roles = _fanout_roles()

    result = run(
        repo=repo,
        vault_project_dir=vault_dir,
        provider=provider,
        gate=gate,
        coder_prompt=_coder_prompt(),
        profile=_CODER_PROFILE,
        emit_event=emitter,
        fanout=_make_fanout(
            provider, repo, vault_dir, version, args.base, roles, emitter
        ),
        converge=_make_converge(
            provider,
            gate,
            repo,
            vault_dir,
            version,
            roles,
            _coder_prompt(),
            _CODER_PROFILE,
            emitter,
        ),
    )
    print(
        f"{result.status.name}: {result.reason} "
        f"(phases advanced: {result.phases_advanced})"
    )
    return 0 if result.status is RunStatus.COMPLETE else 1


if __name__ == "__main__":
    sys.exit(main())
