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
    assert config["agents"]["claude-anthropic"]["model"] == "claude-sonnet-5"
    assert "claude-sonnet-anthropic" not in config["agents"]
    assert (
        "claude_anthropic_model_variants"
        in config["agents"]["claude-anthropic"]["mixin_refs"]
    )
    variants = config["mixins"]["claude_anthropic_model_variants"]["$variants"]
    assert len(variants) == 5
    assert variants[0]["anthropic_reasoning_mode"] == "manual"
    assert variants[0]["anthropic_reasoning_budget_tokens"] == 1024
    assert variants[2]["anthropic_reasoning_effort"] == "high"
    assert variants[3]["anthropic_reasoning_mode"] == "adaptive"
    assert variants[3]["anthropic_reasoning_display"] == "summarized"
    assert variants[3]["anthropic_reasoning_effort"] == "high"
    assert "anthropic_thinking_retention" not in variants[3]
    assert "betas" not in variants[3]
    assert "request_options" not in variants[3]
    assert variants[4]["anthropic_compaction_trigger_tokens"] == 800000
    assert variants[4]["anthropic_tool_use_clear_trigger_tokens"] == 200000
    assert "path:${env:BUILTIN_PLUGINS}/anthropic-compatible" in config["plugins"]
    assert config["providers"]["anthropic"] == {
        "mixin_refs": ["provider_defaults"],
        "provider": "anthropic",
        "auth_mode": "api",
        "api_key": "${env:ANTHROPIC_API_KEY}",
        "base_url": "https://api.anthropic.com",
        "enable_anthropic_compaction": True,
        "anthropic_compaction_trigger_tokens": 150000,
        "anthropic_thinking_retention": "all",
        "enable_anthropic_tool_use_clearing": True,
        "anthropic_tool_use_clear_trigger_tokens": 100000,
        "anthropic_tool_uses_to_keep": 5,
        "capabilities": {
            "anthropic_reasoning_controls": True,
            "prompt_caching": True,
        },
    }
    app_config = config["application"]["application_config"]
    assert "ANTHROPIC_API_KEY" in app_config["editable_env_keys"]
    assert app_config["provider_env_keys"]["anthropic"] == "ANTHROPIC_API_KEY"


def test_default_config_declares_ordered_agent_display_metadata() -> None:
    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))

    expected = {
        "codex-openai": ("Codex · OpenAI", 10),
        "claude-anthropic": ("Claude · Anthropic", 40),
        "gemini": ("Gemini", 60),
        "qwen": ("Qwen", 70),
        "kimi": ("Kimi", 80),
        "grok": ("Grok", 90),
    }
    for agent_id, (title, order) in expected.items():
        display = config["agents"][agent_id]["display"]
        assert display["title"] == title
        assert isinstance(display["description"], str) and display["description"]
        assert display["order"] == order


def test_default_config_pins_openai_compatible_reasoning_effort() -> None:
    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))
    expected = {
        "type": "select",
        "options": ["high", "max"],
        "rich_ui": True,
    }

    for agent_id in ("glm-ollama", "deepseek-ollama", "kimi-ollama"):
        assert (
            config["agents"][agent_id]["request_options_ui"]["reasoning_effort"]
            == expected
        )


def test_default_config_declares_openai_context_maintenance_variants() -> None:
    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert config["providers"]["openai"]["mixin_refs"] == [
        "provider_defaults",
        "openai_responses_model_variants",
    ]
    assert config["providers"]["openai"]["enable_openai_automatic_compaction"] is False
    assert config["providers"]["openai"]["openai_compaction_trigger_tokens"] == 200000
    variants = config["mixins"]["openai_responses_model_variants"]["$variants"]
    assert variants == [
        {
            "$when": {
                "model": {
                    "$matches": (
                        "^gpt-(?:5\\.(?:[6-9]|[1-9][0-9]+)|"
                        "(?:[6-9]|[1-9][0-9]+))(?:\\.[0-9]+)*(?:$|-)"
                    ),
                },
            },
            "reasoning_context": "all_turns",
        },
    ]


@pytest.mark.parametrize(
    ("model", "expects_all_turns"),
    [
        ("gpt-5.1", False),
        ("gpt-5.2", False),
        ("gpt-5.5-pro", False),
        ("gpt-5.6-sol", True),
        ("gpt-5.10-preview", True),
        ("gpt-6-astra", True),
        ("gpt-6.1-custom", True),
        ("gpt-10-next", True),
        ("o3", False),
    ],
)
def test_default_openai_model_variants_only_set_reasoning_for_future_numeric_families(
    model: str,
    expects_all_turns: bool,
) -> None:
    from agent_app.config_variants import resolve_config_variants

    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))
    base = {
        "model": model,
        **config["mixins"]["openai_responses_model_variants"],
    }

    resolved, errors = resolve_config_variants(base, selector=base)

    assert errors == []
    assert "enable_openai_automatic_compaction" not in resolved
    assert "openai_compaction_trigger_tokens" not in resolved
    if expects_all_turns:
        assert resolved["reasoning_context"] == "all_turns"
    else:
        assert "reasoning_context" not in resolved


@pytest.mark.integration
def test_default_config_claude_anthropic_variants_follow_model_override(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

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
    monkeypatch.setenv("BUILTIN_PLUGINS", str((ROOT / "plugins").resolve()))
    monkeypatch.setenv(
        "CLOUD_RUNTIME_BUILD_CONTEXT", str(tmp_path / "cloud-runtime-context")
    )
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    assert app.get_config_errors() == []

    core, base_config, session = app.create_session("claude-anthropic")
    sonnet_config = app.resolve_effective_config(base_config, session)
    assert sonnet_config["model"] == "claude-sonnet-5"
    assert sonnet_config["anthropic_reasoning_mode"] == "adaptive"
    assert sonnet_config["anthropic_reasoning_display"] == "summarized"
    assert sonnet_config["anthropic_reasoning_effort"] == "high"
    assert sonnet_config["anthropic_thinking_retention"] == "all"
    assert sonnet_config["enable_anthropic_compaction"] is True
    assert sonnet_config["anthropic_compaction_trigger_tokens"] == 800000
    assert sonnet_config["enable_anthropic_tool_use_clearing"] is True
    assert sonnet_config["anthropic_tool_use_clear_trigger_tokens"] == 200000
    assert sonnet_config["anthropic_tool_uses_to_keep"] == 5
    assert "request_options" not in sonnet_config
    assert "betas" not in sonnet_config

    haiku_session = session.__class__(
        session_id=session.session_id,
        messages=session.messages,
        metadata={
            **session.metadata,
            "overrides": {"model": "claude-haiku-4-5-20251001"},
        },
    )
    haiku_config = app.resolve_effective_config(base_config, haiku_session)
    assert haiku_config["anthropic_reasoning_mode"] == "manual"
    assert haiku_config["anthropic_reasoning_budget_tokens"] == 1024
    assert haiku_config["anthropic_thinking_retention"] == "all"
    assert haiku_config["enable_anthropic_compaction"] is True
    assert haiku_config["anthropic_compaction_trigger_tokens"] == 150000
    assert haiku_config["enable_anthropic_tool_use_clearing"] is True
    assert haiku_config["anthropic_tool_use_clear_trigger_tokens"] == 100000
    assert haiku_config["anthropic_tool_uses_to_keep"] == 5
    assert "request_options" not in haiku_config
    assert "betas" not in haiku_config
    haiku_ui = core.get_ui_schema(
        config={
            **haiku_config,
            "capabilities": {
                **dict(haiku_config.get("capabilities") or {}),
                "anthropic_context_editing": True,
                "anthropic_compaction": False,
            },
        }
    )
    haiku_ui_keys = {
        element["key"] for element in haiku_ui if isinstance(element.get("key"), str)
    }
    assert "anthropic_reasoning_mode" in haiku_ui_keys
    assert "anthropic_reasoning_budget_tokens" in haiku_ui_keys
    assert "anthropic_reasoning_effort" not in haiku_ui_keys
    assert "anthropic_thinking_retention" in haiku_ui_keys
    assert "anthropic_thinking_turns_to_keep" not in haiku_ui_keys
    assert "enable_anthropic_tool_use_clearing" in haiku_ui_keys
    assert "anthropic_tool_use_clear_trigger_tokens" in haiku_ui_keys
    assert "anthropic_tool_uses_to_keep" in haiku_ui_keys
    assert "anthropic_clear_tool_inputs" not in haiku_ui_keys
    assert "enable_anthropic_compaction" not in haiku_ui_keys

    sonnet_ui = core.get_ui_schema(
        config={
            **sonnet_config,
            "capabilities": {
                **dict(sonnet_config.get("capabilities") or {}),
                "anthropic_context_editing": True,
                "anthropic_compaction": True,
            },
        }
    )
    sonnet_ui_by_key = {
        element["key"]: element
        for element in sonnet_ui
        if isinstance(element.get("key"), str)
    }
    model_ui = sonnet_ui_by_key["model"]
    assert model_ui["type"] == "dropdown"
    assert model_ui["icon"] == "cpu"
    assert model_ui["custom_value"]["enabled"] is True
    assert model_ui["rich_ui"]["kind"] == "dropdown"
    assert model_ui["rich_ui"]["show_label"] is False
    assert model_ui["rich_ui"]["label"] == "Model"
    assert model_ui["rich_ui"]["options"] == model_ui.get("options", [])
    assert model_ui["rich_ui"]["placements"] == ["composer"]
    assert model_ui["rich_ui"]["default_pinned"] is True
    assert "icon" not in model_ui["rich_ui"]
    assert all(element.get("ui_type") != "model_picker" for element in sonnet_ui)
    assert [
        option["value"]
        for option in sonnet_ui_by_key["anthropic_reasoning_effort"]["options"]
    ] == ["low", "medium", "high", "xhigh", "max"]
    assert sonnet_ui_by_key["anthropic_reasoning_effort"]["icon"] == "sliders"
    assert sonnet_ui_by_key["anthropic_reasoning_effort"]["rich_ui"] == {
        "kind": "dropdown",
        "label": "Reasoning effort",
        "show_label": False,
        "show_icon": False,
        "options": sonnet_ui_by_key["anthropic_reasoning_effort"]["options"],
        "placements": ["composer"],
        "default_pinned": True,
    }
    assert sonnet_ui_by_key["anthropic_thinking_retention"]["type"] == "select"
    assert sonnet_ui_by_key["enable_anthropic_compaction"]["type"] == "checkbox"
    assert sonnet_ui_by_key["enable_anthropic_compaction"]["default"] is True
    assert sonnet_ui_by_key["anthropic_compaction_trigger_tokens"]["default"] == 800000
    assert sonnet_ui_by_key["enable_anthropic_tool_use_clearing"]["default"] is True
    assert (
        sonnet_ui_by_key["anthropic_tool_use_clear_trigger_tokens"]["default"] == 200000
    )
    assert sonnet_ui_by_key["anthropic_tool_uses_to_keep"]["default"] == 5
    assert "anthropic_compaction_instructions" not in sonnet_ui_by_key
    assert "anthropic_thinking_turns_to_keep" not in sonnet_ui_by_key
    assert "anthropic_clear_tool_inputs" not in sonnet_ui_by_key

    opus_session = session.__class__(
        session_id=session.session_id,
        messages=session.messages,
        metadata={
            **session.metadata,
            "overrides": {"model": "claude-opus-4-5-20251101"},
        },
    )
    opus_config = app.resolve_effective_config(base_config, opus_session)
    assert opus_config["beta_headers"] == ["interleaved-thinking-2025-05-14"]
    assert opus_config["anthropic_reasoning_mode"] == "manual"
    assert opus_config["anthropic_reasoning_budget_tokens"] == 1024
    assert opus_config["anthropic_reasoning_effort"] == "high"
    assert "request_options" not in opus_config


@pytest.mark.integration
def test_default_config_openai_context_maintenance_variants_and_ui(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    for key in (
        "OPENROUTER_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "TAVILY_API_KEY",
        "OPENAI_API_KEY",
        "FIREWORKS_API_KEY",
        "ZAI_API_KEY",
        "CLOUD_ORCHESTRATOR_TOKEN",
    ):
        monkeypatch.setenv(key, f"test-{key.lower()}")
    monkeypatch.setenv("CLOUD_ORCHESTRATOR_URL", "http://cloud-orchestrator.test")

    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    monkeypatch.setenv("CONFIG_DIR", str(config_path.parent.resolve()))
    monkeypatch.setenv("BUILTIN_PLUGINS", str((ROOT / "plugins").resolve()))
    monkeypatch.setenv(
        "CLOUD_RUNTIME_BUILD_CONTEXT", str(tmp_path / "cloud-runtime-context")
    )

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    assert app.get_config_errors() == []

    api_core, api_base, api_session = app.create_session("codex-openai-api")
    api_config = app.resolve_effective_config(api_base, api_session)
    assert api_config["model"] == "gpt-5.4"
    assert api_config["auth_mode"] == "api"
    assert api_config["enable_openai_automatic_compaction"] is False
    assert api_config["openai_compaction_trigger_tokens"] == 200000
    api_ui = {
        element["key"]: element
        for element in api_core.get_ui_schema(config=api_config)
        if isinstance(element.get("key"), str)
    }
    assert api_ui["enable_openai_automatic_compaction"]["default"] is False
    assert api_ui["openai_compaction_trigger_tokens"]["default"] == 200000

    auto_core, auto_base, auto_session = app.create_session("codex-openai")
    auto_config = app.resolve_effective_config(auto_base, auto_session)
    assert auto_config["auth_mode"] == "auto"
    assert auto_config["enable_openai_automatic_compaction"] is False
    assert auto_config["openai_compaction_trigger_tokens"] == 200000
    assert "reasoning_context" not in auto_config

    gpt56_session = auto_session.__class__(
        session_id=auto_session.session_id,
        messages=auto_session.messages,
        metadata={
            **auto_session.metadata,
            "overrides": {"model": "gpt-5.6-luna"},
        },
    )
    gpt56_config = app.resolve_effective_config(auto_base, gpt56_session)
    assert gpt56_config["reasoning_context"] == "all_turns"
    assert gpt56_config["enable_openai_automatic_compaction"] is False
    assert gpt56_config["openai_compaction_trigger_tokens"] == 200000
    gpt56_ui = {
        element["key"]: element
        for element in auto_core.get_ui_schema(config=gpt56_config)
        if isinstance(element.get("key"), str)
    }
    assert gpt56_ui["reasoning_context"]["label"] == "Reasoning retention"
    assert gpt56_ui["reasoning_context"]["options"] == [
        {"value": "auto", "label": "Auto"},
        {"value": "current_turn", "label": "Current turn only"},
        {"value": "all_turns", "label": "All turns"},
    ]
    assert gpt56_ui["enable_openai_automatic_compaction"]["default"] is False

    astra_session = auto_session.__class__(
        session_id=auto_session.session_id,
        messages=auto_session.messages,
        metadata={
            **auto_session.metadata,
            "overrides": {"model": "gpt-6-astra"},
        },
    )
    astra_config = app.resolve_effective_config(auto_base, astra_session)
    assert astra_config["reasoning_context"] == "all_turns"
    assert astra_config["enable_openai_automatic_compaction"] is False
    assert astra_config["openai_compaction_trigger_tokens"] == 200000
    astra_ui = {
        element["key"]: element
        for element in auto_core.get_ui_schema(config=astra_config)
        if isinstance(element.get("key"), str)
    }
    assert astra_ui["reasoning_context"]["label"] == "Reasoning retention"
    assert astra_ui["enable_openai_automatic_compaction"]["default"] is False
    opted_in_config = app.resolve_effective_config(
        auto_base,
        astra_session,
        {
            "enable_openai_automatic_compaction": True,
            "openai_compaction_trigger_tokens": 250000,
        },
    )
    assert opted_in_config["enable_openai_automatic_compaction"] is True
    assert opted_in_config["openai_compaction_trigger_tokens"] == 250000
    opted_in_ui = {
        element["key"]: element
        for element in auto_core.get_ui_schema(config=opted_in_config)
        if isinstance(element.get("key"), str)
    }
    assert opted_in_ui["enable_openai_automatic_compaction"]["default"] is True
    assert opted_in_ui["openai_compaction_trigger_tokens"]["default"] == 250000


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
            "enable_openai_automatic_compaction": False,
            "openai_compaction_trigger_tokens": 200000,
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
            "model": "gpt-5.4",
            "auth_mode": "api",
            "enable_openai_automatic_compaction": False,
            "openai_compaction_trigger_tokens": 200000,
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
            "model": "claude-sonnet-5",
            "anthropic_reasoning_mode": "adaptive",
            "anthropic_reasoning_effort": "high",
            "anthropic_reasoning_display": "summarized",
            "anthropic_thinking_retention": "all",
            "enable_anthropic_compaction": True,
            "anthropic_compaction_trigger_tokens": 800000,
            "enable_anthropic_tool_use_clearing": True,
            "anthropic_tool_use_clear_trigger_tokens": 200000,
            "anthropic_tool_uses_to_keep": 5,
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
            "request_options_ui": {
                "reasoning_effort": {
                    "type": "select",
                    "options": ["high", "max"],
                    "rich_ui": True,
                }
            },
        },
        "deepseek-ollama": {
            "provider": "reference_openai_compatible",
            "base_url": "http://localhost:11434/v1",
            "model": "deepseek-v4-pro:cloud",
            "request_options": {"reasoning_effort": "max"},
            "request_options_ui": {
                "reasoning_effort": {
                    "type": "select",
                    "options": ["high", "max"],
                    "rich_ui": True,
                }
            },
        },
        "kimi-ollama": {
            "provider": "reference_openai_compatible",
            "base_url": "http://localhost:11434/v1",
            "model": "kimi-k2.6:cloud",
            "request_options": {"reasoning_effort": "max"},
            "request_options_ui": {
                "reasoning_effort": {
                    "type": "select",
                    "options": ["high", "max"],
                    "rich_ui": True,
                }
            },
        },
        "fireworks": {
            "provider": "reference_openai_compatible",
            "base_url": "https://api.fireworks.ai/inference/v1",
            "request_options": {"reasoning_history": "preserved"},
        },
        "zai": {
            "provider": "reference_openai_compatible",
            "base_url": "https://api.z.ai/api/coding/paas/v4",
            "request_options": {
                "reasoning_effort": "max",
                "thinking": {"type": "enabled", "clear_thinking": False},
            },
        },
    }

    for agent_id, expected in cases.items():
        _core, base_config, session = app.create_session(agent_id)
        effective_config = app.resolve_effective_config(base_config, session)
        for key, expected_value in expected.items():
            assert effective_config[key] == expected_value, (
                agent_id,
                key,
                effective_config.get(key),
            )


@pytest.mark.integration
def test_default_config_openai_compatible_composer_schema(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    for key in (
        "OPENROUTER_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "TAVILY_API_KEY",
        "OPENAI_API_KEY",
        "FIREWORKS_API_KEY",
        "ZAI_API_KEY",
        "CLOUD_ORCHESTRATOR_TOKEN",
    ):
        monkeypatch.setenv(key, f"test-{key.lower()}")
    monkeypatch.setenv("CLOUD_ORCHESTRATOR_URL", "http://cloud-orchestrator.test")

    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    monkeypatch.setenv("CONFIG_DIR", str(config_path.parent.resolve()))
    monkeypatch.setenv("BUILTIN_PLUGINS", str((ROOT / "plugins").resolve()))
    monkeypatch.setenv(
        "CLOUD_RUNTIME_BUILD_CONTEXT", str(tmp_path / "cloud-runtime-context")
    )

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    assert app.get_config_errors() == []

    core, base_config, session = app.create_session("glm-ollama")
    effective_config = app.resolve_effective_config(base_config, session)
    ui_by_key = {
        element["key"]: element
        for element in core.get_ui_schema(config=effective_config)
        if isinstance(element.get("key"), str)
    }

    model_ui = ui_by_key["model"]
    assert model_ui["type"] == "dropdown"
    assert isinstance(model_ui["options"], list)
    assert model_ui["custom_value"] == {
        "enabled": True,
        "option_label": "Use '{value}' as a custom model ID",
    }
    assert model_ui["rich_ui"] == {
        "kind": "dropdown",
        "label": "Model",
        "show_label": False,
        "options": model_ui["options"],
        "placeholder": "Search models or enter a model ID",
        "custom_value": {
            "enabled": True,
            "option_label": "Use '{value}' as a custom model ID",
        },
        "placements": ["composer"],
        "default_pinned": True,
    }

    reasoning_ui = ui_by_key["request_options__reasoning_effort"]
    assert reasoning_ui["type"] == "select"
    assert reasoning_ui["icon"] == "sliders"
    assert reasoning_ui["default"] == "max"
    assert reasoning_ui["rich_ui"] == {
        "kind": "dropdown",
        "label": "Reasoning Effort",
        "show_label": False,
        "show_icon": False,
        "options": [
            {"value": "high", "label": "high"},
            {"value": "max", "label": "max"},
        ],
        "placements": ["composer"],
        "default_pinned": True,
    }


def test_default_config_pricing_includes_resolve_per_model_rates() -> None:
    """The bundled pricing extracts resolve through the config pipeline.

    The ollama, fireworks, and zai providers reference their pricing file via
    ``token_rates: {"$include": "${env:CONFIG_DIR}/pricing/<provider>.json"}``;
    after resolution the merged per-model rates are present and the control
    key is consumed. The zai agent's legacy flat rates moved into the
    provider-level extract.
    """

    from agent_app.config import load_resolved_config

    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    resolved, errors, _env = load_resolved_config(config_path, env={})

    include_errors = [
        error for error in errors if str(error.get("type", "")).startswith("include")
    ]
    assert include_errors == []

    ollama_rates = resolved["providers"]["ollama"]["token_rates"]
    assert "$include" not in ollama_rates
    assert ollama_rates["models"]["glm-5.2"] == {
        "input": 1.4,
        "cached": 0.26,
        "completion": 4.4,
    }
    assert ollama_rates["models"]["deepseek-v4-pro"]["input"] == 1.32

    fireworks_rates = resolved["providers"]["fireworks"]["token_rates"]
    assert "$include" not in fireworks_rates
    # The default fireworks model is not priced by the current table, so no
    # entry matches it; the extract still ships the priced serverless models.
    assert "gpt-oss-20b" not in fireworks_rates["models"]
    assert fireworks_rates["models"]["glm-5.3"]["completion"] == 12.15

    zai_rates = resolved["providers"]["zai"]["token_rates"]
    assert "$include" not in zai_rates
    assert zai_rates["models"]["glm-5.3-flash"] == {
        "input": 0.15,
        "cached": 0.03,
        "completion": 0.5,
    }
    assert "token_rates" not in resolved["agents"]["zai"]
