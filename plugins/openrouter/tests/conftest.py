from __future__ import annotations

import os
import sys
from pathlib import Path


def pytest_configure() -> None:
    root = Path(__file__).resolve().parents[3]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    test_support = root / "test"
    test_support_str = str(test_support)
    if test_support_str not in sys.path:
        sys.path.insert(0, test_support_str)

    src = Path(__file__).resolve().parents[1] / "src"
    src_str = str(src)
    if not os.environ.get("CRYSTAL_EMBEDDED_PROVIDER_BUNDLE") and src_str not in sys.path:
        sys.path.insert(0, src_str)

    from repo_test_env import load_repo_root_env

    load_repo_root_env()