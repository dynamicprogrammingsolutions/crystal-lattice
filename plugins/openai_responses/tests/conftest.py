from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    # Ensure repo root is importable for app/core modules used by tests.
    root = Path(__file__).resolve().parents[3]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    test_support = root / "test"
    test_support_str = str(test_support)
    if test_support_str not in sys.path:
        sys.path.insert(0, test_support_str)

    # Ensure this plugin package's src/ is importable.
    src = Path(__file__).resolve().parents[1] / "src"
    src_str = str(src)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

    # Ensure this plugin's benchmark/ directory is importable so tests can
    # import the refresh scripts (refresh_openai_responses_models,
    # refresh_openai_responses_pricing) as top-level modules.
    benchmark = Path(__file__).resolve().parents[1] / "benchmark"
    benchmark_str = str(benchmark)
    if benchmark_str not in sys.path:
        sys.path.insert(0, benchmark_str)

    from repo_test_env import load_repo_root_env

    load_repo_root_env()
