"""Status/event stream.

A typed event schema, an append-only writer, and a stdout renderer.
"""

from pathlib import Path
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, Field, TypeAdapter

Role = Literal["coder", "review", "security", "simplify"]


class PhaseStart(BaseModel):
    """A phase began."""

    kind: Literal["phase-start"] = "phase-start"
    ts: AwareDatetime
    phase: str


class RoleSpawn(BaseModel):
    """The role instance was spawned (its result has not landed yet)."""

    kind: Literal["role-spawn"] = "role-spawn"
    ts: AwareDatetime
    role: Role


class RoleReturned(BaseModel):
    """The role instance returned its result."""

    kind: Literal["role-returned"] = "role-returned"
    ts: AwareDatetime
    role: Role
    session_id: str
    total_cost_usd: float
    is_error: bool
    summary: str = ""  # the role's final message (why it stopped / what it did)


class GateStep(BaseModel):
    """One gate command ran (with its pass/fail outcome)."""

    kind: Literal["gate-step"] = "gate-step"
    ts: AwareDatetime
    command: str
    passed: bool


class Advance(BaseModel):
    """A phase advanced to the next."""

    kind: Literal["advance"] = "advance"
    ts: AwareDatetime
    from_phase: str
    to_phase: str


class Halt(BaseModel):
    """The run halted, with a reason."""

    kind: Literal["halt"] = "halt"
    ts: AwareDatetime
    reason: str


class RunSummary(BaseModel):
    """Terminal summary of the run (status + phases advanced)."""

    kind: Literal["run-summary"] = "run-summary"
    ts: AwareDatetime
    status: Literal["complete", "halted"]
    phases_advanced: int
    reason: str


Event = Annotated[
    PhaseStart | RoleSpawn | RoleReturned | GateStep | Advance | Halt | RunSummary,
    Field(discriminator="kind"),
]


_ADAPTER: TypeAdapter[Event] = TypeAdapter(Event)


def _no_emit(event: Event) -> None:
    """Default status sink: discard (a run without an observer is valid)."""


def append_event(stream: Path, event: Event) -> None:
    """Append one event as a JSON line (append-only history)."""
    with stream.open("a") as f:
        f.write(event.model_dump_json() + "\n")


def read_events(stream: Path) -> list[Event]:
    """Read the stream back into typed event variants."""
    return [_ADAPTER.validate_json(line) for line in stream.read_text().splitlines()]


def emit(stream: Path, status: Path, event: Event) -> None:
    """Record an event: append to the history and refresh the snapshot."""
    append_event(stream, event)
    _write_status(status, event)


class Status(BaseModel):
    """Current-state snapshot: where the run is + the latest event."""

    stage: str
    phase: str
    last_event: Event


def _write_status(status: Path, event: Event) -> None:
    """Overwrite the snapshot with the latest event (write mode — not append)."""
    status.write_text(event.model_dump_json())


def read_status(status: Path) -> Event:
    """Read the snapshot back as its typed event variant."""
    return _ADAPTER.validate_json(status.read_text())


def _short_phase(phase: str) -> str:
    """Trim a verbose phase label (`<index>: <title>`) to a short one-line CLI label."""
    head = phase.split(" — ")[0].split("\n")[0].strip()
    return head if len(head) <= 72 else head[:71] + "…"


def render(event: Event) -> str:
    """Format one event as a human-readable stdout line."""
    match event:
        case PhaseStart():
            return f"▶ building {_short_phase(event.phase)}"
        case RoleSpawn():
            return f"  {event.role} spawned — running…"
        case RoleReturned():
            flag = "error" if event.is_error else "ok"
            line = f"  {event.role} returned ({flag}, ${event.total_cost_usd:.2f})"
            if event.summary:
                gist = " ".join(event.summary.split())
                gist = gist[:300] + ("…" if len(gist) > 300 else "")
                line += f"\n    ↳ {gist}"
            return line
        case GateStep():
            return f"  gate: {event.command} {'✓' if event.passed else '✗'}"
        case Advance():
            return f"✅ phase done → advanced to {_short_phase(event.to_phase)}"
        case Halt():
            return f"⛔ halted: {event.reason}"
        case RunSummary():
            return f"■ {event.status} — {event.phases_advanced} phase(s) advanced"


def is_in_progress(status: Path) -> bool:
    """Whether a spawned role is still running (its result has not landed)."""
    match read_status(status):
        case RoleSpawn():
            return True
        case _:
            return False
