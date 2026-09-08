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

from runtime_env_reset import (  # noqa: E402,F401
    reset_runtime_env_overlay_between_tests,
)

# Several tests wire the feature-system-message plugin into their
# applications and import it at module level, so it must be importable at
# collection time. The application environment never installs plugins
# that the default config loads dynamically, so provision it on the fly
# (hermetically, pip install --target) when it is not already installed.
from plugin_provision import (  # noqa: E402
    module_importable,
    provision_plugin,
)

if not module_importable("feature_system_message"):
    import atexit
    import shutil
    import tempfile

    _FEATURE_SYSTEM_MESSAGE_DIR = tempfile.mkdtemp(
        prefix="feature_system_message_plugin_"
    )
    provision_plugin(
        _ROOT / "plugins" / "feature-system-message",
        Path(_FEATURE_SYSTEM_MESSAGE_DIR),
    )
    sys.path.insert(0, _FEATURE_SYSTEM_MESSAGE_DIR)
    atexit.register(shutil.rmtree, _FEATURE_SYSTEM_MESSAGE_DIR, ignore_errors=True)


def pytest_configure() -> None:
    from repo_test_env import load_repo_root_env

    load_repo_root_env()
