from __future__ import annotations

import json
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


def test_default_config_enables_session_list_status_footer_and_archive() -> None:
    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert config["application"]["session_status_show_in_session_list_footer"] is True
    assert "path:${env:BUILTIN_PLUGINS}/session-archive-app" in config["plugins"]


def test_default_config_declares_provider_qualified_claude_agents() -> None:
    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert "claude" not in config["agents"]
    assert config["agents"]["claude-openrouter"]["provider"] == "openrouter"
    assert (
        config["agents"]["claude-openrouter"]["model"] == "anthropic/claude-haiku-4.5"
    )
    assert config["agents"]["claude-anthropic"]["provider"] == "anthropic"
    assert config["agents"]["claude-anthropic"]["model"] == "claude-haiku-4-5-20251001"
    assert config["agents"]["claude-anthropic"]["request_options"] == {
        "thinking": {"type": "enabled", "budget_tokens": 1024}
    }
    assert config["agents"]["claude-anthropic"]["request_options_ui"] == {
        "thinking": {
            "type": ["disabled", "enabled"],
            "budget_tokens": "number",
        }
    }
    assert config["agents"]["claude-sonnet-anthropic"]["provider"] == "anthropic"
    assert config["agents"]["claude-sonnet-anthropic"]["model"] == "claude-sonnet-5"
    assert config["agents"]["claude-sonnet-anthropic"]["betas"] == [
        "context-management-2025-06-27"
    ]
    assert config["agents"]["claude-sonnet-anthropic"]["request_options"] == {
        "thinking": {
            "type": "adaptive",
            "display": "summarized",
        },
        "output_config": {"effort": "high"},
        "context_management": {
            "edits": [
                {
                    "type": "clear_thinking_20251015",
                    "keep": "all",
                }
            ]
        },
    }
    assert "path:${env:BUILTIN_PLUGINS}/anthropic-compatible" in config["plugins"]
    assert config["providers"]["anthropic"] == {
        "mixin_refs": ["provider_defaults"],
        "provider": "anthropic",
        "auth_mode": "api",
        "api_key": "${env:ANTHROPIC_API_KEY}",
        "base_url": "https://api.anthropic.com",
    }
    app_config = config["application"]["application_config"]
    assert "ANTHROPIC_API_KEY" in app_config["editable_env_keys"]
    assert app_config["provider_env_keys"]["anthropic"] == "ANTHROPIC_API_KEY"


@pytest.mark.integration
def test_default_config_effective_agent_configs_stay_intact(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    # Default config placeholder resolution records missing env vars as
    # config errors, so set stable dummy values for providers we inspect.
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("FIREWORKS_API_KEY", "test-fireworks-key")
    monkeypatch.setenv("ZAI_API_KEY", "test-zai-key")
    monkeypatch.setenv("CLOUD_ORCHESTRATOR_URL", "http://cloud-orchestrator.test")
    monkeypatch.setenv("CLOUD_ORCHESTRATOR_TOKEN", "test-cloud-token")

    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    monkeypatch.setenv("CONFIG_DIR", str(config_path.parent.resolve()))
    monkeypatch.setenv(
        "CLOUD_RUNTIME_BUILD_CONTEXT", str(tmp_path / "cloud-runtime-context")
    )
    monkeypatch.setenv("BUILTIN_PLUGINS", str((ROOT / "plugins").resolve()))
    session_root = tmp_path / "sessions"

    app = AgentApplication(
        str(config_path), str(session_root), event_store=InMemoryEventStore()
    )
    assert app.get_config_errors() == []
    search_elements = [
        element
        for element in app.get_application_ui_schema()
        if element.get("plugin") == "session_main_search"
        and element.get("ui_type") == "session_list_filter"
    ]
    assert [element["id"] for element in search_elements] == [
        "session_search",
        "session_title_search",
        "session_first_message_search",
    ]
    assert search_elements[0]["main_search"] is True
    assert search_elements[1]["main_search"] is False
    assert search_elements[2]["main_search"] is False
    assert (
        app.get_application_config()["session_status_show_in_session_list_footer"]
        is True
    )
    status_meta = next(
        element
        for element in app.get_application_ui_schema()
        if element.get("plugin") == "session_status"
        and element.get("id") == "session_status_meta"
    )
    assert status_meta["role"] == "meta"
    assert status_meta["order"] == 100
    pin_action = next(
        element
        for element in app.get_application_ui_schema()
        if element.get("plugin") == "session_pinned"
        and element.get("id") == "toggle_session_pinned"
    )
    assert pin_action["ui_type"] == "session_list_action"
    assert pin_action["rich_ui"]["value_path"] == "metadata.pinned"
    assert pin_action["rich_ui"]["default_pinned"] is True
    assert pin_action["rich_ui"]["placements"] == [
        "header_trailing",
        "actions_bar",
    ]
    assert pin_action["rich_ui"]["appearance"]["active"]["tone"] == "highlight"
    archive_action = next(
        element
        for element in app.get_application_ui_schema()
        if element.get("plugin") == "session_archive"
        and element.get("id") == "toggle_session_archived"
    )
    assert archive_action["rich_ui"]["value_path"] == "metadata.archived"
    assert archive_action["rich_ui"]["default_pinned"] is True
    list_filters = {
        element["id"]: element
        for element in app.get_application_ui_schema()
        if element.get("ui_type") == "session_list_filter"
    }
    assert list_filters["pinned_state"] == {
        "ui_type": "session_list_filter",
        "id": "pinned_state",
        "label": "Pinned",
        "icon": "star",
        "order": 10,
        "type": "boolean",
        "match": "equals",
        "data": "metadata.pinned",
        "missing_value": False,
        "default": None,
        "options": [
            {
                "value": False,
                "label": "Not pinned",
                "icon": "star",
                "tone": "muted",
            },
            {
                "value": True,
                "label": "Pinned",
                "icon": "star",
                "tone": "highlight",
            },
        ],
        "plugin": "session_pinned",
    }
    assert list_filters["session_status"] == {
        "ui_type": "session_list_filter",
        "id": "session_status",
        "label": "Status",
        "icon": "circle",
        "order": 20,
        "type": "select",
        "match": "one_of",
        "multiple": True,
        "data": "metadata.status",
        "missing_value": "todo",
        "default": [],
        "options": [
            {"value": "todo", "label": "To do", "tone": "muted"},
            {
                "value": "in_progress",
                "label": "In progress",
                "tone": "primary",
            },
            {"value": "blocked", "label": "Blocked", "tone": "danger"},
            {"value": "done", "label": "Done", "tone": "success"},
        ],
        "plugin": "session_status",
    }
    assert list_filters["archive_state"]["default"] is False
    assert list_filters["archive_state"]["data"] == "metadata.archived"

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
            "model": "z-ai/glm-5.2",
            "reasoning_effort": "max",
            "request_options": {
                "provider": {"order": ["z-ai"], "allow_fallbacks": False}
            },
        },
        "claude-openrouter": {
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
        "claude-anthropic": {
            "provider": "anthropic",
            "model": "claude-haiku-4-5-20251001",
            "request_options": {"thinking": {"type": "enabled", "budget_tokens": 1024}},
            "web_search_enabled": True,
            "web_search_provider": "gemini_api",
            "mcp_enabled": False,
            "mcp_reuse_runtime": True,
            "mcp_fail_on_startup_error": False,
        },
        "claude-sonnet-anthropic": {
            "provider": "anthropic",
            "model": "claude-sonnet-5",
            "betas": ["context-management-2025-06-27"],
            "request_options": {
                "thinking": {
                    "type": "adaptive",
                    "display": "summarized",
                },
                "output_config": {"effort": "high"},
                "context_management": {
                    "edits": [
                        {
                            "type": "clear_thinking_20251015",
                            "keep": "all",
                        }
                    ]
                },
            },
            "web_search_enabled": True,
            "web_search_provider": "gemini_api",
            "mcp_enabled": False,
            "mcp_reuse_runtime": True,
            "mcp_fail_on_startup_error": False,
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
        "glm-ollama": {
            "provider": "reference_openai_compatible",
            "base_url": "http://localhost:11434/v1",
            "model": "glm-5.2:cloud",
            "request_options": {"reasoning_effort": "max"},
            "request_options_ui": {"reasoning_effort": ["high", "max"]},
        },
        "deepseek-ollama": {
            "provider": "reference_openai_compatible",
            "base_url": "http://localhost:11434/v1",
            "model": "deepseek-v4-pro:cloud",
            "request_options": {"reasoning_effort": "max"},
            "request_options_ui": {"reasoning_effort": ["high", "max"]},
        },
        "kimi-ollama": {
            "provider": "reference_openai_compatible",
            "base_url": "http://localhost:11434/v1",
            "model": "kimi-k2.6:cloud",
            "request_options": {"reasoning_effort": "max"},
            "request_options_ui": {"reasoning_effort": ["high", "max"]},
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
