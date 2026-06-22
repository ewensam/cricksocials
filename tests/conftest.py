"""pytest configuration for CrickSocials tests."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: marks tests that hit the live Play Cricket website "
        "(deselect with -m 'not integration')",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip integration tests unless -m integration is explicitly passed."""
    if config.getoption("-m", default="") == "integration":
        return  # user asked for integration tests — run them

    skip_integration = pytest.mark.skip(
        reason="integration tests skipped by default; run with -m integration"
    )
    for item in items:
        if item.get_closest_marker("integration"):
            item.add_marker(skip_integration)
