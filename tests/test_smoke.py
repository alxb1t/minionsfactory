"""Test smoke."""

from orchestrator import describe


def test_describe_names_the_orchestrator() -> None:
    assert describe() == "MinionsFactory orchestrator"
