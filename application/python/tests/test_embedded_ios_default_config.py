from __future__ import annotations

import json
from pathlib import Path

from agent_app.config import load_resolved_config


CONFIG_PATH = (
    Path(__file__).resolve().parents[1]
    / "agent_terminal_app"
    / "default_config"
    / "embedded-ios"
    / "config.json"
)


def _config_environment(tmp_path: Path) -> dict[str, str]:
    workspace = tmp_path / "workspace"
    auth = tmp_path / "auth"
    return {
        "EMBEDDED_WORKSPACE_DIR": str(workspace),
        "EMBEDDED_SMOKE_ENABLED": "true",
        "EMBEDDED_COMPATIBLE_ENABLED": "false",
        "EMBEDDED_COMPATIBLE_API_KEY": "",
        "EMBEDDED_COMPATIBLE_BASE_URL": "http://127.0.0.1:3000/v1",
        "EMBEDDED_COMPATIBLE_MODEL": "qwen3.5:0.8b",
        "EMBEDDED_REVIEWER_ENABLED": "false",
        "EMBEDDED_REVIEWER_API_KEY": "",
        "EMBEDDED_REVIEWER_CA_BUNDLE": "/bundle/reviewer-ca.pem",
        "EMBEDDED_OPENAI_ENABLED": "true",
        "EMBEDDED_OPENAI_API_KEY": "test-key",
        "EMBEDDED_OPENAI_BASE_URL": "https://api.openai.com/v1",
        "EMBEDDED_OPENAI_MODEL": "gpt-test",
        "EMBEDDED_OPENAI_AUTH_MODE": "api",
        "EMBEDDED_OPENROUTER_ENABLED": "false",
        "EMBEDDED_OPENROUTER_API_KEY": "",
        "EMBEDDED_OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
        "EMBEDDED_OPENROUTER_MODEL": "anthropic/test",
        "EMBEDDED_ANTHROPIC_ENABLED": "false",
        "EMBEDDED_ANTHROPIC_API_KEY": "",
        "EMBEDDED_ANTHROPIC_BASE_URL": "https://api.anthropic.com",
        "EMBEDDED_ANTHROPIC_MODEL": "claude-test",
        "EMBEDDED_CHATGPT_CREDENTIALS_PATH": str(auth / "chatgpt-auth.json"),
        "EMBEDDED_CHATGPT_RATE_LIMITS_PATH": str(
            auth / "chatgpt-rate-limits.json"
        ),
        "EMBEDDED_COST_TRACKING_DB_PATH": str(
            tmp_path / "cost-tracking.sqlite3"
        ),
    }


def test_embedded_ios_config_is_python_owned_and_secret_free() -> None:
    raw_text = CONFIG_PATH.read_text(encoding="utf-8")
    raw = json.loads(raw_text)
    settings = raw["embedded_settings"]

    assert settings["profileOrder"][-1] == "reviewer"
    assert settings["profiles"]["reviewer"]["agentId"] == "reviewer-codex"
    assert settings["profiles"]["reviewer"]["usesBundledReviewerCA"] is True
    assert raw["providers"]["reviewer"]["base_url"] == (
        "https://ireland-s1.dynamicprogrammingsolutions.com:3443/v1"
    )
    assert raw["providers"]["reviewer"]["model"] == "gpt-5.6-luna"
    assert raw["providers"]["reviewer"]["auth_mode_options"] == []
    assert raw["providers"]["openai"]["auth_mode_options"] == []
    assert raw["providers"]["openai"]["api_key"] == (
        "${env:EMBEDDED_OPENAI_API_KEY}"
    )
    assert "sk-" not in raw_text


def test_embedded_ios_config_resolves_selected_plugins_and_agents(
    tmp_path: Path,
) -> None:
    resolved, errors, _environment = load_resolved_config(
        CONFIG_PATH,
        env={},
        config_env=_config_environment(tmp_path),
    )

    assert not [
        error for error in errors if error.get("severity") != "warning"
    ]
    assert resolved["agents"]["openai-codex"]["enabled"] == "true"
    assert resolved["agents"]["reviewer-codex"]["enabled"] == "false"
    assert resolved["providers"]["openai"]["api_key"] == "test-key"
    assert resolved["agents"]["openai-codex"]["workspace_root"] == str(
        tmp_path / "workspace"
    )
    assert {
        "feature_system_message.system_message_feature.SystemMessageFeature",
        "feature_request_options.RequestOptionsFeature",
        "timestamp_extension.timestamp_extension.TimestampExtension",
        "timestamp_extension.duration_extension.DurationExtension",
        "cost_tracking_plugins.cost_tracking_extension.CostTrackingExtension",
        "embedded_workspace_settings.workspace_settings_feature.EmbeddedWorkspaceSettingsFeature",
        "openai_responses_plugins.openai_responses_attachments_extension.OpenAIResponsesAttachmentsExtension",
        "openai_responses_plugins.openai_responses_flex_processing_extension.OpenAIResponsesFlexProcessingExtension",
        "openai_responses_plugins.openai_responses_fast_mode_extension.OpenAIResponsesFastModeExtension",
        "openai_responses_plugins.openai_responses_prompt_caching_extension.OpenAIResponsesPromptCachingExtension",
        "openai_responses_plugins.openai_responses_websearch_extension.OpenAIResponsesWebSearchExtension",
        "openai_responses_plugins.openai_responses_verbosity_extension.OpenAIResponsesVerbosityExtension",
        "openrouter_plugins.openrouter_attachments_extension.OpenRouterAttachmentsExtension",
        "openrouter_plugins.claude_caching_extension.ClaudeCachingExtension",
        "openrouter_plugins.openrouter_websearch_extension.OpenRouterWebSearchExtension",
        "openrouter_plugins.openrouter_verbosity_extension.OpenRouterVerbosityExtension",
        "summarize_range_app.SummarizeRangeAppPlugin",
        "rebuild_native_app.RebuildNativeAppPlugin",
        "cost_tracking_plugins.cost_tracking_app_plugin.CostTrackingAppPlugin",
    }.issubset(set(resolved["plugins"]))

    assert resolved["providers"]["reviewer"]["show_flex_processing_ui"] is False
    assert resolved["providers"]["reviewer"]["show_fast_mode_ui"] is False
    assert resolved["providers"]["reviewer"]["image_attachment_mode"] == "inline"
    assert resolved["providers"]["openai"]["image_attachment_mode"] == "inline"