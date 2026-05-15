from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    root = Path(__file__).resolve().parents[3]
    path = root / "plugins/mcp-shared/src"
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)