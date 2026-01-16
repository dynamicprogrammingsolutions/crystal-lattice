from __future__ import annotations

import sys
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

ROOT = REPO_DIR.parents[1]
CORE_PY = ROOT / "core" / "python"

if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
