from __future__ import annotations

import pytest

from agent_app.runtime_env import RuntimeEnvOverlay


@pytest.fixture(autouse=True)
def _reset_runtime_env_overlay_between_tests():
    yield
    RuntimeEnvOverlay._reset_for_tests()
