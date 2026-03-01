from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import os

import pytest

from agent_app.application_future import AgentApplication


def test_openrouter_agent_application_config_loads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure OpenRouter plugins resolve in AgentApplication without network calls."""

    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")

    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openrouter": {
                "provider": "openrouter",
                "model": "google/gemini-2.5-flash-lite",
                "api_key": os.getenv("OPENROUTER_API_KEY"),
                "base_url": "https://openrouter.ai/api/v1",
                "timeout": 60,
            }
        },
        "plugins": [
            "openrouter_plugins.openrouter_provider.OpenRouterProvider",
            "openrouter_plugins.openrouter_tools_extension.OpenRouterToolsExtension",
            "openrouter_plugins.openrouter_reasoning_extension.OpenRouterReasoningExtension",
            "openrouter_plugins.openrouter_usage_extension.OpenRouterUsageExtension",
            "openrouter_plugins.openrouter_websearch_extension.OpenRouterWebSearchExtension",
            "openrouter_plugins.openrouter_verbosity_extension.OpenRouterVerbosityExtension",
            "openrouter_plugins.claude_caching_extension.ClaudeCachingExtension",
        ],
        "agents": {"default": {"provider": "openrouter"}},
    }

    config_path = tmp_path / "config_openrouter_agent_app.json"
    config_path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root))
    errs = app.get_config_errors()
    assert errs == [], f"expected no config/plugin errors, got: {errs}"
