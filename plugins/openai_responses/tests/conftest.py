from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is importable for app/core modules used by tests.
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Ensure repo-level test support (repo_test_env, shared fixtures) is importable.
_TEST_SUPPORT = _ROOT / "test"
if str(_TEST_SUPPORT) not in sys.path:
    sys.path.insert(0, str(_TEST_SUPPORT))

# Ensure this plugin package's src/ is importable.
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Ensure this plugin's benchmark/ directory is importable so tests can
# import the refresh scripts (refresh_openai_responses_models,
# refresh_openai_responses_pricing) as top-level modules.
_BENCHMARK = Path(__file__).resolve().parents[1] / "benchmark"
if str(_BENCHMARK) not in sys.path:
    sys.path.insert(0, str(_BENCHMARK))

from runtime_env_reset import (  # noqa: F401
    reset_runtime_env_overlay_between_tests,
)


def pytest_configure() -> None:
    from repo_test_env import load_repo_root_env

    load_repo_root_env()
