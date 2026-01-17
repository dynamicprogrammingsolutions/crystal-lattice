from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_PY = ROOT / "core" / "python"
APP_PY = ROOT / "application" / "python"
PLUGIN_REPOS = ROOT / "plugins"

# Keep repo-root importable for local development.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ensure core packages and legacy built-in plugins package are importable.
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))

# Some plugin tests may reuse application-layer helpers.
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))

# Ensure plugin repository packages are importable for their own test suites.
for repo_name in (
    "codex-tools",
    "openrouter",
    "feature-system-message",
    "feature-file-context",
    "feature-web-context",
):
    repo_dir = PLUGIN_REPOS / repo_name
    if not repo_dir.is_dir():
        continue

    src_dir = repo_dir / "src"
    if src_dir.is_dir() and str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    elif str(repo_dir) not in sys.path:
        sys.path.insert(0, str(repo_dir))
