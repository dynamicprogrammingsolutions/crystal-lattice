from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import json
import os

import pytest

from agent_app.application_future import AgentApplication


def test_openai_responses_agent_application_config_loads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")

    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openai_responses": {
                "provider": "openai_responses",
                "model": "gpt-5-mini",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": "https://api.openai.com/v1",
                "timeout": 60,
            }
        },
        "plugins": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider",
            "openai_responses_plugins.openai_responses_native_compaction_extension.OpenAIResponsesNativeCompactionExtension",
            "openai_responses_plugins.openai_responses_tools_extension.OpenAIResponsesToolsExtension",
            "openai_responses_plugins.openai_responses_reasoning_extension.OpenAIResponsesReasoningExtension",
            "openai_responses_plugins.openai_responses_usage_extension.OpenAIResponsesUsageExtension",
            "openai_responses_plugins.openai_responses_verbosity_extension.OpenAIResponsesVerbosityExtension",
        ],
        "agents": {"default": {"provider": "openai_responses"}},
    }

    config_path = tmp_path / "config_openai_responses_agent_app.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root))
    errs = app.get_config_errors()
    assert errs == [], f"expected no config/plugin errors, got: {errs}"

    core, base_config, session = app.create_session("default")

    assert base_config["provider"] == "openai_responses"
    assert session.metadata == {"agent_id": "default"}

    providers = getattr(core, "_providers")
    assert len(providers) == 1

    provider_wrapper = providers[0]
    assert provider_wrapper.plugin_class.__name__ == "OpenAIResponsesProvider"

    extension_names = [ext.plugin_class.__name__ for ext in provider_wrapper.extensions]
    assert extension_names == [
        "OpenAIResponsesNativeCompactionExtension",
        "OpenAIResponsesToolsExtension",
        "OpenAIResponsesReasoningExtension",
        "OpenAIResponsesUsageExtension",
        "OpenAIResponsesVerbosityExtension",
    ]
