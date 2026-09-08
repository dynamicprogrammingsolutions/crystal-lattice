from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo-level test support (shared fixtures) is importable.
_TEST_SUPPORT = Path(__file__).resolve().parents[3] / "test"
if str(_TEST_SUPPORT) not in sys.path:
    sys.path.insert(0, str(_TEST_SUPPORT))

from runtime_env_reset import (  # noqa: E402, F401
    reset_runtime_env_overlay_between_tests,
)
