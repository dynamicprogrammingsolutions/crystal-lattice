from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))


@pytest.mark.integration
def test_default_config_effective_agent_configs_stay_intact(
    tmp_path: Path,
    monkeypatch,
    default_config_test_env,
) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    default_env = default_config_test_env(use_dummy_env=True)
    session_root = tmp_path / "sessions"

    app = AgentApplication(
        str(default_env.config_path),
        str(session_root),
        event_store=InMemoryEventStore(),
        env_overrides=default_env.env_overrides,
    )
    assert app.get_config_errors() == []

    cases = {
        "cloud-script-author": {
            "provider": "openai_responses",
            "model": "gpt-5.4-mini",
            "auth_mode": "auto",
            "allowed_paths": [
                ".",
                "..",
                str(
                    Path(__file__).resolve().parents[3] / "plugins" / "cloud-agent-app"
                ),
                str(
                    Path(__file__).resolve().parents[1]
                    / "agent_terminal_app"
                    / "default_config"
                    / "cloud-agent"
                    / "profiles"
                ),
            ],
            "shell_tool_mode": "auto",
            "system_message_enabled": True,
            "skills_enabled": True,
        },
        "codex-openai-api": {
            "provider": "openai_responses",
            "auth_mode": "api",
            "shell_tool_mode": "auto",
            "skills_enabled": True,
            "skills_roots": [".agents/skills"],
        },
        "glm": {
            "provider": "openrouter",
            "model": "z-ai/glm-5",
            "request_options": {
                "provider": {"order": ["z-ai"], "allow_fallbacks": False}
            },
        },
        "claude": {
            "provider": "openrouter",
            "model": "anthropic/claude-haiku-4.5",
            "reasoning_max_tokens": 16000,
            "web_search_enabled": True,
            "web_search_provider": "gemini_api",
            "mcp_enabled": False,
            "mcp_reuse_runtime": True,
            "mcp_fail_on_startup_error": False,
            "request_options": {
                "provider": {"order": ["anthropic"], "allow_fallbacks": False}
            },
        },
        "openrouter-image": {
            "provider": "openrouter_image_generation",
            "model": "black-forest-labs/flux.2-klein-4b",
            "aspect_ratio": "1:1",
        },
        "ollama": {
            "provider": "reference_openai_compatible",
            "base_url": "http://localhost:11434/v1",
            "reasoning_field": "reasoning",
        },
        "fireworks": {
            "provider": "reference_openai_compatible",
            "base_url": "https://api.fireworks.ai/inference/v1",
            "request_options": {"reasoning_history": "preserved"},
        },
        "zai": {
            "provider": "reference_openai_compatible",
            "base_url": "https://api.z.ai/api/paas/v4",
            "request_options": {
                "thinking": {"type": "enabled", "clear_thinking": False}
            },
        },
    }

    for agent_id, expected in cases.items():
        _core, base_config, _session = app.create_session(agent_id)
        for key, expected_value in expected.items():
            assert base_config[key] == expected_value, (
                agent_id,
                key,
                base_config.get(key),
            )
