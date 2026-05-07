from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    root = Path(__file__).resolve().parents[3]
    for rel in (
        "plugins/codex-tools/src",
        "plugins/openai_responses/src",
        "plugins/openrouter/src",
        "core/python",
    ):
        path = root / rel
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
