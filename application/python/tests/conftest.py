from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = (
    ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "config.json"
)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application" / "python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core" / "python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))

from repo_test_env import load_repo_root_env  # noqa: E402
from agent_app.runtime_env import RuntimeEnvOverlay  # noqa: E402


load_repo_root_env()


@dataclass(frozen=True)
class DefaultConfigTestEnv:
    config_path: Path
    env_overrides: dict[str, str]


DEFAULT_CONFIG_DUMMY_ENV = {
    "CLOUD_ORCHESTRATOR_URL": "http://cloud-orchestrator.test",
    "CLOUD_ORCHESTRATOR_TOKEN": "test-cloud-token",
    "OPENROUTER_API_KEY": "test-openrouter-key",
    "GEMINI_API_KEY": "test-gemini-key",
    "TAVILY_API_KEY": "test-tavily-key",
    "OPENAI_API_KEY": "test-openai-key",
    "FIREWORKS_API_KEY": "test-fireworks-key",
    "ZAI_API_KEY": "test-zai-key",
}


@pytest.fixture(autouse=True)
def _reset_runtime_env_overlay_between_tests():
    yield
    RuntimeEnvOverlay._reset_for_tests()


@pytest.fixture
def default_config_test_env(tmp_path: Path):
    """Build app-local env overrides for the canonical default config.

    Existing process env values, including values loaded from the repo-root
    .env, win over dummy fallbacks. Explicit test overrides win over both.
    """

    def build(
        *,
        config_path: Path = DEFAULT_CONFIG_PATH,
        cloud_runtime_build_context: Path | None = None,
        use_dummy_env: bool = False,
        **explicit_overrides: Any,
    ) -> DefaultConfigTestEnv:
        config_path = config_path.expanduser().resolve()
        env_overrides = {
            "CONFIG_DIR": str(config_path.parent),
            "BUILTIN_PLUGINS": str((ROOT / "plugins").resolve()),
            "CLOUD_RUNTIME_BUILD_CONTEXT": str(
                (
                    cloud_runtime_build_context
                    or tmp_path / "cloud-runtime-context"
                ).expanduser().resolve()
            ),
        }
        env_overrides.update({
            key: os.environ.get(key, fallback)
            for key, fallback in DEFAULT_CONFIG_DUMMY_ENV.items()
        })
        if use_dummy_env:
            env_overrides.update(DEFAULT_CONFIG_DUMMY_ENV)
        env_overrides.update(
            {key: str(value) for key, value in explicit_overrides.items()}
        )
        return DefaultConfigTestEnv(
            config_path=config_path,
            env_overrides=env_overrides,
        )

    return build
