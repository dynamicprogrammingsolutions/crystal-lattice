from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CORE_PY = REPO_ROOT / "core" / "python"
PLUGIN_SRC = Path(__file__).resolve().parents[1] / "src"


def _ensure_on_path(path: Path) -> None:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


_ensure_on_path(REPO_ROOT)
_ensure_on_path(CORE_PY)
_ensure_on_path(PLUGIN_SRC)
