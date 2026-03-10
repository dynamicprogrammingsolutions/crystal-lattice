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
            "openrouter_responses": {
                "provider": "openrouter_responses",
                "model": "google/gemini-2.5-flash-lite",
                "api_key": os.getenv("OPENROUTER_API_KEY"),
                "base_url": "https://openrouter.ai/api/v1",
                "timeout": 60,
            }
        },
        "plugins": [
            "openrouter_responses_plugins.openrouter_responses_provider.OpenRouterResponsesProvider",
            "openrouter_responses_plugins.openrouter_responses_tools_extension.OpenRouterResponsesToolsExtension",
            "openrouter_responses_plugins.openrouter_responses_reasoning_extension.OpenRouterResponsesReasoningExtension",
            "openrouter_responses_plugins.openrouter_responses_usage_extension.OpenRouterResponsesUsageExtension",
            "openrouter_responses_plugins.openrouter_responses_websearch_extension.OpenRouterResponsesWebSearchExtension",
            "openrouter_responses_plugins.openrouter_responses_verbosity_extension.OpenRouterResponsesVerbosityExtension",
            "openrouter_responses_plugins.openrouter_responses_claude_caching_extension.OpenRouterResponsesClaudeCachingExtension",
        ],
        "agents": {"default": {"provider": "openrouter_responses"}},
    }

    config_path = tmp_path / "config_openrouter_agent_app.json"
    config_path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root))
    errs = app.get_config_errors()
    assert errs == [], f"expected no config/plugin errors, got: {errs}"
