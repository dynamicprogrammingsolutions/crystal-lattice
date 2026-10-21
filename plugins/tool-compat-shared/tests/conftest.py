from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    """Prefer this checkout's src over any globally installed copy."""

    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    src_str = str(src)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)
