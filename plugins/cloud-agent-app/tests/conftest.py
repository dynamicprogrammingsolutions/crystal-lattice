from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CORE_PY = ROOT / "core" / "python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))

from repo_test_env import load_repo_root_env  # noqa: E402
from agent_app.runtime_env import RuntimeEnvOverlay  # noqa: E402


load_repo_root_env()


@pytest.fixture(autouse=True)
def _reset_runtime_env_overlay_between_tests():
    yield
    RuntimeEnvOverlay._reset_for_tests()