from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    root = Path(__file__).resolve().parents[3]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    core_py = root / "core/python"
    core_str = str(core_py)
    if core_str not in sys.path:
        sys.path.insert(0, core_str)

    src = Path(__file__).resolve().parents[1] / "src"
    src_str = str(src)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)