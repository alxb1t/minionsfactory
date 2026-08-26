"""Run-from-source entry: `python -m orchestrator run --repo <target>`."""

import argparse
import subprocess
import sys
from collections.abc import Callable
from datetime import date
from functools import partial
from pathlib import Path

from orchestrator.converge import ConvergeResult, converge
from orchestrator.diff import compute_diff
from orchestrator.driver import RunStatus, run
from orchestrator.fanout import (
    RoleSpec,
    assemble_prompt,
    build_inputs_block,
    run_fanout,
)
from orchestrator.findings import FindingsState, findings_path, read_findings_state
from orchestrator.gate import Gate, SubprocessGate
from orchestrator.provider import (
    ClaudeCodeProvider,
    Profile,
    Provider,
    ProviderError,
)
from orchestrator.release import (
    ReleaseResult,
    SubprocessReleaseGit,
    deferred_work_text,
    prepare_release,
    verify_release_gate,
)
from orchestrator.specs import run_check
from orchestrator.state import (
    PlanContractError,
    PreflightError,
    read_change_state,
    read_head,
    read_vault_dir,
    select_change,
    verify_vault_access,
)
from orchestrator.status import Event, emit, render

_CODER_PROFILE = Profile(
    permission_mode="default",
    allowed_tools=("Edit", "Write", "Bash"),
)


def _prompt(name: str) -> str:
    """Load a role prompt shipped with this repo."""
    return (Path(__file__).resolve().parent.parent / "prompts" / name).read_text()


def _coder_prompt() -> str:
    """Load the warm whole-plan coder prompt."""
    return _prompt("coder.md")


def _fixer_prompt() -> str:
    """Load the converge-loop fixer prompt."""
    return _prompt("fixer.md")


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


def _findings_map(repo: Path, change_id: str, roles: list[RoleSpec]) -> dict[str, Path]:
    """Resolve every role's findings path under the repo, keyed by role name."""
    return {r.name: findings_path(repo, change_id, r.name) for r in roles}


def _make_fanout(
    provider: Provider,
    repo: Path,
    vault_dir: Path,
    version: str,
    base: str,
    roles: list[RoleSpec],
    emit_event: Callable[[Event], None],
) -> Callable[[], list[FindingsState | None]]:
    change_dir = select_change(repo)

    def _fanout() -> list[FindingsState | None]:
        diff = compute_diff(repo, base, "HEAD")
        return run_fanout(
            provider,
            repo,
            vault_dir,
            change_dir.name,
            version,
            diff,
            repo / ".minions" / "diff.patch",
            read_head(repo),
            change_dir,
            roles,
            mode="review",
            emit_event=emit_event,
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
    change_dir = select_change(repo)
    findings = _findings_map(repo, change_dir.name, roles)
    paths = list(findings.values())
    fixer = assemble_prompt(
        build_inputs_block(change_dir, findings, read_head(repo), version, vault_dir),
        fixer_prompt,
    )

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
            change_dir.name,
            version,
            diff,
            repo / ".minions" / "diff.patch",
            read_head(repo),
            change_dir,
            roles,
            mode="verify",
            emit_event=emit_event,
        )

    return lambda: converge(
        provider,
        gate,
        repo,
        fixer,
        coder_profile,
        _read_states,
        _run_verify,
        emit_event,
        max_rounds=3,
    )


def _git_tags(repo: Path) -> list[str]:
    """List the repo's git tags."""
    completed = subprocess.run(
        ["git", "tag"], cwd=repo, capture_output=True, text=True, check=True
    )
    return completed.stdout.split()


def _tree_is_clean(repo: Path) -> bool:
    """Whether the repo's working tree has no uncommitted changes."""
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip() == ""


def _current_branch(repo: Path) -> str:
    """Return the repo's current git branch name."""
    completed = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _make_release(
    gate: Gate,
    repo: Path,
    vault_dir: Path,
    version: str,
    branch: str,
    today: str,
    roles: list[RoleSpec],
) -> Callable[[], ReleaseResult]:
    change_dir = select_change(repo)
    findings = _findings_map(repo, change_dir.name, roles)
    findings_paths = list(findings.values())

    def _release() -> ReleaseResult:
        verdict = verify_release_gate(
            version=version,
            gate_result=gate.run_gate(repo),
            findings=[read_findings_state(p) for p in findings_paths],
            backlog_text=deferred_work_text(repo, version),
            changelog_text=(repo / "CHANGELOG.md").read_text(),
            existing_tags=_git_tags(repo),
            tree_is_clean=_tree_is_clean(repo),
        )
        result = prepare_release(
            verdict, repo, version, today, branch, SubprocessReleaseGit()
        )
        if result.handoff:
            # The release stage spawns no role — `prompts/release.md` is invoked by
            # hand — so the orchestrator *emits* the same Inputs block with the
            # handoff rather than prepending it at spawn. Path resolution still
            # lives in one place in code; the human-invoked role reads it, not a shell.
            print(
                build_inputs_block(
                    change_dir, findings, read_head(repo), version, vault_dir
                )
                + result.handoff
            )
        return result

    return _release


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
    run_parser.add_argument(
        "--model",
        default=None,
        help="claude model for every role, e.g. claude-opus-4-8 (default: CLI default)",
    )
    run_parser.add_argument(
        "--effort",
        default="medium",
        help="reasoning effort: low|medium|high|xhigh|max (default: medium)",
    )
    specs_parser = subparsers.add_parser("specs", help="spec-binding checks")
    specs_sub = specs_parser.add_subparsers(dest="specs_command", required=True)
    check_parser = specs_sub.add_parser("check", help="check the spec↔test binding")
    check_parser.add_argument(
        "--repo", type=Path, default=Path.cwd(), help="repo to check (default: cwd)"
    )
    check_parser.add_argument(
        "--strict",
        action="store_true",
        help="also require every test to carry a spec or spec_exempt marker",
    )
    args = parser.parse_args(argv)

    if args.command == "specs":
        return run_check(args.repo.resolve(), strict=args.strict)

    repo = args.repo.resolve()

    try:  # zero-token preflight: refuse a malformed / misconfigured target before spend
        change_state = read_change_state(repo)
        vault_dir = read_vault_dir(repo)
        verify_vault_access(repo, vault_dir)
    except (PlanContractError, PreflightError) as error:
        print(f"preflight failed: {error}")
        return 1

    provider = ClaudeCodeProvider(model=args.model, effort=args.effort)
    gate = SubprocessGate()
    emitter = _make_emitter(repo)
    version = change_state.version  # declared by the change, not derived from a path
    roles = _fanout_roles()
    branch = _current_branch(repo)
    today = date.today().isoformat()
    change_dir = select_change(repo)
    coder_prompt = assemble_prompt(
        build_inputs_block(
            change_dir,
            _findings_map(repo, change_dir.name, roles),
            change_state.head,
            version,
            vault_dir,
        ),
        _coder_prompt(),
    )

    try:
        result = run(
            repo=repo,
            provider=provider,
            gate=gate,
            coder_prompt=coder_prompt,
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
                _fixer_prompt(),
                _CODER_PROFILE,
                emitter,
            ),
            release=_make_release(gate, repo, vault_dir, version, branch, today, roles),
        )
    except ProviderError as error:
        print(
            "⛔ provider error — the run halted; re-run to resume from the last "
            f"committed phase:\n   {error}"
        )
        return 2
    print(
        f"{result.status.name}: {result.reason} "
        f"(phases advanced: {result.phases_advanced})"
    )
    return 0 if result.status is RunStatus.COMPLETE else 1


if __name__ == "__main__":
    sys.exit(main())
