from __future__ import annotations

import sys
from pathlib import Path


# Ensure this plugin repository is importable.
REPO_DIR = Path(__file__).resolve().parent
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))


# Ensure core SDK + application layer are importable when running tests
# directly from this plugin repo.
ROOT = REPO_DIR.parents[1]
CORE_PY = ROOT / "core" / "python"
APP_PY = ROOT / "application" / "python"

if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
