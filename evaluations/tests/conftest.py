from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVAL_SRC = ROOT / "evaluations" / "src"
APP_PY = ROOT / "application" / "python"
CORE_PY = ROOT / "core" / "python"

for path in (EVAL_SRC, APP_PY, CORE_PY, ROOT):
    raw = str(path)
    if raw not in sys.path:
        sys.path.insert(0, raw)
