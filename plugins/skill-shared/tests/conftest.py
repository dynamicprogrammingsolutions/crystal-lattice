from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    root = Path(__file__).resolve().parents[3]
    src = root / "plugins/skill-shared/src"
    src_str = str(src)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)