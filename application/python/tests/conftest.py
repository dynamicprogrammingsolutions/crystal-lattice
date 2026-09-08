from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TEST_SUPPORT = ROOT / "test"
if str(TEST_SUPPORT) not in sys.path:
    sys.path.insert(0, str(TEST_SUPPORT))
CORE_PY = ROOT / "core" / "python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))

from repo_test_env import load_repo_root_env  # noqa: E402
from runtime_env_reset import (  # noqa: E402,F401
    reset_runtime_env_overlay_between_tests,
)

load_repo_root_env()
