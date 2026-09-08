"""Shared pytest fixture: reset the ``RuntimeEnvOverlay`` between tests.

Tests that build applications (directly or through the server) install
runtime environment overlays. The overlay state is process-global, so
any suite hosting such tests must reset it between tests to prevent
conflicting overlay values across tests.

Suites consume this fixture by importing it in their ``conftest.py``:

    from runtime_env_reset import reset_runtime_env_overlay_between_tests  # noqa: F401
"""

from __future__ import annotations

import pytest

from agent_app.runtime_env import RuntimeEnvOverlay


@pytest.fixture(autouse=True)
def reset_runtime_env_overlay_between_tests():
    yield
    RuntimeEnvOverlay._reset_for_tests()
