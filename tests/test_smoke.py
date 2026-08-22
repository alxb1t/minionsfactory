"""Test smoke."""

import pytest

from orchestrator import describe


@pytest.mark.spec_exempt("smoke — package describe()")
def test_describe_names_the_orchestrator() -> None:
    assert describe() == "MinionsFactory orchestrator"
