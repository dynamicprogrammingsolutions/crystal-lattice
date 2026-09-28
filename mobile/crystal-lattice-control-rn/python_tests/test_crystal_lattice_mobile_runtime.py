from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
import sys
import time

import pytest


RUNTIME_MODULE = (
    Path(__file__).resolve().parents[1]
    / "ios"
    / "CrystalLatticePythonRuntime"
    / "Python"
    / "crystal_lattice_mobile_runtime.py"
)
CORE_PYTHON = Path(__file__).resolve().parents[3] / "core" / "python"
EMBEDDED_TOOLS_SHARED = (
    Path(__file__).resolve().parents[3]
    / "plugins"
    / "embedded-tools-shared"
    / "src"
)
EMBEDDED_CLAUDE_TOOLS = (
    Path(__file__).resolve().parents[3]
    / "plugins"
    / "embedded-claude-tools"
    / "src"
)
EMBEDDED_CODEX_TOOLS = (
    Path(__file__).resolve().parents[3]
    / "plugins"
    / "embedded-codex-tools"
    / "src"
)
OPENAI_RESPONSES_PLUGIN = (
    Path(__file__).resolve().parents[3]
    / "plugins"
    / "openai_responses"
    / "src"
)
ANTHROPIC_PLUGIN = (
    Path(__file__).resolve().parents[3]
    / "plugins"
    / "anthropic-compatible"
    / "src"
)
OPENROUTER_PLUGIN = (
    Path(__file__).resolve().parents[3]
    / "plugins"
    / "openrouter"
    / "src"
)
REFERENCE_PROVIDER_PLUGIN = (
    Path(__file__).resolve().parents[3]
    / "plugins"
    / "reference-openai-compatible-provider"
    / "src"
)
APPLICATION_PLUGIN_SOURCES = tuple(
    Path(__file__).resolve().parents[3] / "plugins" / project / "src"
    for project in (
        "chatgpt-auth-app",
        "generate-title-app",
        "session-actions-app",
        "session-archive-app",
        "session-main-search-app",
        "session-message-count-meta-app",
        "session-ordering-buckets-app",
        "session-pinned-app",
        "session-status-app",
        "session-timestamp-meta-app",
        "session-title-app",
        "session-asset-attachments",
    )
)


def load_runtime_module():
    for path in (
        CORE_PYTHON,
        EMBEDDED_TOOLS_SHARED,
        EMBEDDED_CLAUDE_TOOLS,
        EMBEDDED_CODEX_TOOLS,
        OPENAI_RESPONSES_PLUGIN,
        ANTHROPIC_PLUGIN,
        OPENROUTER_PLUGIN,
        REFERENCE_PROVIDER_PLUGIN,
        *APPLICATION_PLUGIN_SOURCES,
    ):
        sys.path.insert(0, str(path))
    spec = importlib.util.spec_from_file_location(
        "crystal_lattice_mobile_runtime",
        RUNTIME_MODULE,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def call(module, root: Path, method: str, path: str, body=None):
    response = json.loads(
        module.execute_json(
            json.dumps(
                {
                    "method": method,
                    "path": path,
                    "body": body,
                }
            ),
            str(root),
        )
    )
    assert response["status"] < 300, response
    return response["data"]


def test_in_process_transport_session_request_flow(tmp_path: Path) -> None:
    module = load_runtime_module()

    try:
        assert call(module, tmp_path, "GET", "/agents") == {"agents": ["local"]}
        created = call(
            module,
            tmp_path,
            "POST",
            "/sessions",
            {"agent_id": "local"},
        )
        session_id = created["session"]["session_id"]
        started = call(
            module,
            tmp_path,
            "POST",
            f"/sessions/{session_id}/send_message",
            {
                "message": {
                    "role": "user",
                    "content": "hello",
                }
            },
        )

        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            events = call(
                module,
                tmp_path,
                "GET",
                (
                    f"/events?session_id={session_id}"
                    f"&request_id={started['request_id']}"
                ),
            )
            if any(
                event.get("type") == "request_completed" for event in events["events"]
            ):
                break
            time.sleep(0.01)
        else:
            raise AssertionError("Embedded request did not complete")

        messages = call(
            module,
            tmp_path,
            "GET",
            f"/sessions/{session_id}/messages",
        )
        assert [entry["message"]["role"] for entry in messages["messages"]] == [
            "user",
            "assistant",
        ]
        assert (
            messages["messages"][-1]["message"]["content"]
            == "Embedded runtime smoke response"
        )
    finally:
        module.shutdown_runtime()


def test_external_claude_like_tools_reject_escapes_and_round_trip_text(
    tmp_path: Path,
) -> None:
    module = load_runtime_module()
    from embedded_claude_tools import ClaudeLikeReadTool, ClaudeLikeWriteTool

    assert not hasattr(module, "WorkspaceReadTool")
    assert not hasattr(module, "WorkspaceWriteTool")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    read_tool = ClaudeLikeReadTool()
    write_tool = ClaudeLikeWriteTool()
    read_state = read_tool.init({"working_directory": str(workspace)})
    write_state = write_tool.init({"working_directory": str(workspace)})

    assert not write_tool.execute_tool(
        "Write",
        {"file_path": "../outside.txt", "content": "blocked"},
        write_state,
    )["success"]
    assert not read_tool.execute_tool(
        "Read",
        {"file_path": str(tmp_path / "outside.txt")},
        read_state,
    )["success"]

    written = write_tool.execute_tool(
        "Write",
        {"file_path": "nested/output.txt", "content": "hello\nworld\n"},
        write_state,
    )
    assert written["success"]
    read = read_tool.execute_tool(
        "Read",
        {"file_path": "nested/output.txt"},
        read_state,
    )
    assert read["success"]
    assert read["result"] == "1\thello\n2\tworld"

    outside = tmp_path / "outside"
    outside.mkdir()
    symlink = workspace / "linked"
    symlink.symlink_to(outside, target_is_directory=True)
    escaped = write_tool.execute_tool(
        "Write",
        {"file_path": "linked/escape.txt", "content": "blocked"},
        write_state,
    )
    assert not escaped["success"]
    assert not (outside / "escape.txt").exists()


def test_fixed_runtime_config_loads_separate_tool_families(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = load_runtime_module()
    from embedded_claude_tools import (
        ClaudeLikeEditTool,
        ClaudeLikeGlobTool,
        ClaudeLikeGrepTool,
        ClaudeLikeReadTool,
        ClaudeLikeWebFetchTool,
        ClaudeLikeWriteTool,
    )
    from embedded_codex_tools import (
        CodexLikeApplyPatchTool,
        CodexLikeCurlTool,
        CodexLikeFindTool,
        CodexLikeRgTool,
        CodexLikeSedTool,
    )

    config = {"working_directory": str(tmp_path / "workspace")}
    claude_names = [
        tool().get_tool_schemas(tool().init(config))[0]["function"]["name"]
        for tool in (
            ClaudeLikeReadTool,
            ClaudeLikeWriteTool,
            ClaudeLikeEditTool,
            ClaudeLikeGlobTool,
            ClaudeLikeGrepTool,
            ClaudeLikeWebFetchTool,
        )
    ]
    codex_names = []
    for tool in (
        CodexLikeSedTool,
        CodexLikeRgTool,
        CodexLikeFindTool,
        CodexLikeCurlTool,
        CodexLikeApplyPatchTool,
    ):
        instance = tool()
        schema = instance.get_tool_schemas(instance.init(config))[0]
        codex_names.append(
            schema.get("name") or schema.get("function", {}).get("name")
        )

    assert claude_names == ["Read", "Write", "Edit", "Glob", "Grep", "WebFetch"]
    assert codex_names == ["sed", "rg", "find", "curl", "apply_patch"]

    legacy_config = module._config_payload(
        {
            "api_key": "test-key",
            "model": "test-model",
            "proxy_url": "https://proxy.test/v1",
        },
        tmp_path / "workspace",
    )
    assert legacy_config["agents"]["compatible-claude"]["plugins"] == [
        "embedded_claude_tools.read_tool.ClaudeLikeReadTool",
        "embedded_claude_tools.write_tool.ClaudeLikeWriteTool",
        "embedded_claude_tools.edit_tool.ClaudeLikeEditTool",
        "embedded_claude_tools.glob_tool.ClaudeLikeGlobTool",
        "embedded_claude_tools.grep_tool.ClaudeLikeGrepTool",
        "embedded_claude_tools.web_fetch_tool.ClaudeLikeWebFetchTool",
    ]

    full_configuration = {
        "version": 3,
        "default_agent": "openai-codex",
        "providers": {
            profile_id: {
                "enabled": True,
                "api_key": f"{profile_id}-key",
                "base_url": f"https://{profile_id}.test/v1",
                "model": f"{profile_id}-model",
            }
            for profile_id in module.PROFILE_ORDER
        },
    }
    runtime_config = module._config_payload(
        full_configuration,
        tmp_path / "workspace",
    )
    assert runtime_config["providers"]["compatible"]["provider"] == (
        "reference_openai_compatible"
    )
    assert runtime_config["providers"]["reviewer"]["provider"] == "openai_responses"
    assert runtime_config["providers"]["reviewer"]["provider_transport"] == (
        "requests"
    )
    assert runtime_config["providers"]["reviewer"]["auth_mode_options"] == ["api"]
    assert runtime_config["providers"]["openai"]["provider"] == "openai_responses"
    assert runtime_config["providers"]["openai"]["provider_transport"] == "requests"
    assert runtime_config["providers"]["openai"]["auth_mode_options"] == [
        "api",
        "chatgpt",
    ]
    assert runtime_config["providers"]["openrouter"]["provider"] == "openrouter"
    assert runtime_config["providers"]["anthropic"]["provider"] == "anthropic"
    assert runtime_config["providers"]["anthropic"]["provider_transport"] == (
        "requests"
    )
    assert runtime_config["agents"]["openai-codex"]["plugins"] == (
        module.CODEX_TOOL_PLUGINS
    )
    assert runtime_config["agents"]["reviewer-codex"]["plugins"] == (
        module.CODEX_TOOL_PLUGINS
    )
    for agent_id in (
        "compatible-claude",
        "openrouter-claude",
        "anthropic-claude",
    ):
        assert runtime_config["agents"][agent_id]["plugins"] == (
            module.CLAUDE_TOOL_PLUGINS
        )
    assert (
        "openai_responses_plugins.openai_responses_chatgpt_auth_feature."
        "OpenAIResponsesChatGPTAuthFeature"
        in runtime_config["plugins"]
    )

    from anthropic_plugins.provider import AnthropicProvider
    from openai_responses_plugins.openai_responses_provider import (
        OpenAIResponsesProvider,
    )
    from openrouter_plugins.openrouter_provider import OpenRouterProvider
    from reference_openai_compatible_provider.provider import OpenAICompatibleProvider

    for provider_type in (
        AnthropicProvider,
        OpenAIResponsesProvider,
        OpenRouterProvider,
        OpenAICompatibleProvider,
    ):
        monkeypatch.setattr(provider_type, "get_models", lambda self, config: [])

    runtime = module.MobileRuntime(
        str(tmp_path / "runtime"),
        full_configuration,
    )
    try:
        assert runtime.application.list_agents() == [
            "anthropic-claude",
            "compatible-claude",
            "local",
            "openai-codex",
            "openrouter-claude",
            "reviewer-codex",
        ]
        default_session = runtime.create_session()
        assert default_session.metadata["agent_id"] == "openai-codex"
        assert {
            plugin["id"] for plugin in runtime.application.list_application_plugins()
        } == {
            "chatgpt_auth",
            "generate_title",
            "session_actions",
            "session_archive",
            "session_main_search",
            "session_message_count_meta",
            "session_ordering_buckets",
            "session_pinned",
            "session_status",
            "session_timestamp_meta",
            "session_title",
            "session_asset_attachments",
        }
    finally:
        runtime.application.close()


def test_chatgpt_profile_and_reviewer_ca_are_configurable(tmp_path: Path) -> None:
    module = load_runtime_module()
    runtime_config = module._config_payload(
        {
            "version": 3,
            "default_agent": "openai-codex",
            "providers": {
                "reviewer": {
                    "enabled": True,
                    "api_key": "review-key",
                    "base_url": "https://reviewer.test/v1",
                    "model": "reviewer-model",
                    "tls_ca_bundle": "/runtime/reviewer-ca.pem",
                },
                "openai": {
                    "enabled": True,
                    "api_key": "",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-5.6-luna",
                    "auth_mode": "chatgpt",
                },
            },
        },
        tmp_path / "runtime" / "workspace",
    )

    assert runtime_config["providers"]["reviewer"]["tls_ca_bundle"] == (
        "/runtime/reviewer-ca.pem"
    )
    assert runtime_config["providers"]["reviewer"]["provider"] == "openai_responses"
    assert runtime_config["agents"]["reviewer-codex"]["plugins"] == (
        module.CODEX_TOOL_PLUGINS
    )
    assert runtime_config["providers"]["openai"]["auth_mode"] == "chatgpt"
    assert "openai-codex" in runtime_config["agents"]
    assert runtime_config["application"]["chatgpt_auth"]["credentials_path"].endswith(
        "/config/auth/chatgpt-auth.json"
    )
    normalized_auto = module._normalized_runtime_configuration(
        {
            "providers": {
                "openai": {
                    "enabled": True,
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-5.6-luna",
                    "auth_mode": "auto",
                }
            }
        }
    )
    assert normalized_auto["providers"]["openai"]["auth_mode"] == "api"


def test_chatgpt_saved_default_and_session_override_are_independent(
    tmp_path: Path,
) -> None:
    module = load_runtime_module()
    runtime_root = tmp_path / "runtime"
    credentials_path = runtime_root / "config" / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True)
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "chatgpt-access-token",
                "expires_at": "2099-01-01T00:00:00Z",
                "account_id": "account-1",
            }
        ),
        encoding="utf-8",
    )
    runtime = module.MobileRuntime(
        str(runtime_root),
        {
            "version": 3,
            "default_agent": "openai-codex",
            "providers": {
                "openai": {
                    "enabled": True,
                    "api_key": "openai-api-key",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-5.6-luna",
                    "auth_mode": "chatgpt",
                }
            },
        },
    )
    try:
        session = runtime.create_session(agent_id="openai-codex")
        loaded = runtime.application.load_session(session.session_id)
        assert loaded is not None
        _core, base_config, stored_session = loaded
        assert base_config["auth_mode"] == "chatgpt"
        assert runtime.runtime_configuration["providers"]["openai"]["auth_mode"] == (
            "chatgpt"
        )

        runtime.application.patch_session_settings(
            session.session_id,
            {"auth_mode": "api"},
        )
        assert runtime.application.get_session_settings(session.session_id) == {
            "auth_mode": "api"
        }
        loaded = runtime.application.load_session(session.session_id)
        assert loaded is not None
        _core, base_config, stored_session = loaded
        assert base_config["auth_mode"] == "chatgpt"
        assert runtime.application.resolve_effective_config(
            base_config,
            stored_session,
        )["auth_mode"] == "api"

        runtime.application.delete_session_setting(
            session.session_id,
            "auth_mode",
        )
        loaded = runtime.application.load_session(session.session_id)
        assert loaded is not None
        _core, base_config, stored_session = loaded
        assert runtime.application.get_session_settings(session.session_id) == {}
        assert runtime.application.resolve_effective_config(
            base_config,
            stored_session,
        )["auth_mode"] == "chatgpt"
        assert runtime.runtime_configuration["providers"]["openai"]["auth_mode"] == (
            "chatgpt"
        )
    finally:
        runtime.application.close()


def test_provider_import_smoke_uses_requests_transports(tmp_path: Path) -> None:
    module = load_runtime_module()

    result = call(
        module,
        tmp_path,
        "GET",
        "/embedded/runtime/provider-imports",
    )
    assert result == {
        "providers": [
            "openai_responses:requests",
            "openrouter:requests",
            "anthropic:requests",
        ]
    }


def test_local_session_remains_usable_after_provider_enable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_runtime_module()
    root = tmp_path / "runtime"
    smoke_runtime = module.MobileRuntime(str(root))
    session_id = smoke_runtime.create_session(agent_id="local").session_id
    smoke_runtime.application.close()

    from reference_openai_compatible_provider.provider import (
        OpenAICompatibleProvider,
    )

    monkeypatch.setattr(
        OpenAICompatibleProvider,
        "get_models",
        lambda self, config: [],
    )
    configured_runtime = module.MobileRuntime(
        str(root),
        {
            "version": 3,
            "default_agent": "compatible-claude",
            "providers": {
                "compatible": {
                    "enabled": True,
                    "api_key": "compatible-key",
                    "base_url": "https://compatible.test/v1",
                    "model": "compatible-model",
                }
            },
        },
    )
    try:
        assert "local" in configured_runtime.application.list_agents()
        loaded = configured_runtime.application.load_session(session_id)
        assert loaded is not None
        updated = configured_runtime.append_message(
            session_id,
            {
                "role": "user",
                "content": "continue after provider enable",
            },
        )
        assert updated.messages[-1].content == "continue after provider enable"
        reloaded = configured_runtime.application.load_session(session_id)
        assert reloaded is not None
        assert reloaded[2].messages[-1].content == (
            "continue after provider enable"
        )
        assert configured_runtime.create_session(agent_id="local").metadata[
            "agent_id"
        ] == "local"
    finally:
        configured_runtime.application.close()


def test_application_plugins_actions_snapshots_and_settings_routes(
    tmp_path: Path,
) -> None:
    module = load_runtime_module()

    try:
        actions = call(module, tmp_path, "GET", "/application/actions")["actions"]
        action_pairs = {
            (action.get("plugin"), action.get("id"))
            for action in actions
            if isinstance(action, dict)
        }
        assert ("session_actions", "copy_session") in action_pairs
        assert ("chatgpt_auth", "login_start") in action_pairs
        assert ("generate_title", "generate_title_for_session") in action_pairs
        assert ("session_title", "set_session_title") in action_pairs
        assert ("session_archive", "toggle_session_archived") in action_pairs

        chatgpt_status = call(
            module,
            tmp_path,
            "POST",
            "/actions",
            {
                "plugin": "chatgpt_auth",
                "action_id": "check_status",
                "inputs": {},
            },
        )
        assert chatgpt_status["status"] == "ok"
        assert (
            chatgpt_status["result"]["display"]["title"]
            == "ChatGPT Login Status"
        )

        application_ui = call(
            module,
            tmp_path,
            "GET",
            "/application/ui-schema",
        )["elements"]
        assert any(
            element.get("ui_type") == "session_list_filter"
            for element in application_ui
            if isinstance(element, dict)
        )
        assert any(
            element.get("ui_type") == "session_list_action"
            for element in application_ui
            if isinstance(element, dict)
        )

        created = call(
            module,
            tmp_path,
            "POST",
            "/sessions",
            {"agent_id": "local"},
        )
        session_id = created["session"]["session_id"]
        for content in ("first", "second", "third"):
            call(
                module,
                tmp_path,
                "POST",
                f"/sessions/{session_id}/messages",
                {"role": "user", "content": content},
            )

        session_ui = call(
            module,
            tmp_path,
            "GET",
            f"/sessions/{session_id}/application/ui-schema",
        )["elements"]
        assert any(
            element.get("plugin") == "session_actions"
            and element.get("id") == "fork_session_at_message"
            for element in session_ui
            if isinstance(element, dict)
        )

        title_result = call(
            module,
            tmp_path,
            "POST",
            f"/sessions/{session_id}/actions",
            {
                "plugin": "session_title",
                "action_id": "set_session_title",
                "inputs": {
                    "session_id": session_id,
                    "title": "Embedded route matrix",
                },
            },
        )
        assert title_result["status"] == "ok"
        archive_result = call(
            module,
            tmp_path,
            "POST",
            f"/sessions/{session_id}/actions",
            {
                "plugin": "session_archive",
                "action_id": "toggle_session_archived",
                "inputs": {"session_id": session_id},
            },
        )
        assert archive_result["status"] == "ok"
        pin_result = call(
            module,
            tmp_path,
            "POST",
            f"/sessions/{session_id}/actions",
            {
                "plugin": "session_pinned",
                "action_id": "toggle_session_pinned",
                "inputs": {"session_id": session_id},
            },
        )
        assert pin_result["status"] == "ok"
        status_result = call(
            module,
            tmp_path,
            "POST",
            f"/sessions/{session_id}/actions",
            {
                "plugin": "session_status",
                "action_id": "set_session_status",
                "inputs": {
                    "session_id": session_id,
                        "status": "in_progress",
                },
            },
        )
        assert status_result["status"] == "ok"

        summaries = call(module, tmp_path, "GET", "/sessions")["sessions"]
        summary = next(
            entry for entry in summaries if entry["session_id"] == session_id
        )
        assert summary["presentation"]["title"] == "Embedded route matrix"
        assert summary["metadata"]["archived"] is True
        assert summary["metadata"]["pinned"] is True
        assert summary["metadata"]["status"] == "in_progress"
        assert summary["message_count"] == 3

        manual_snapshot = call(
            module,
            tmp_path,
            "POST",
            f"/sessions/{session_id}/snapshots",
            {"reason": "route matrix manual"},
        )["snapshot"]
        deleted = call(
            module,
            tmp_path,
            "DELETE",
            f"/sessions/{session_id}/messages",
            {"range": {"start": 2}},
        )
        assert deleted["deleted_indices"] == [2]
        snapshots = call(
            module,
            tmp_path,
            "GET",
            f"/sessions/{session_id}/snapshots",
        )["snapshots"]
        assert len(snapshots) == 2
        assert any(
            snapshot["reason"].startswith("Before deleting messages")
            for snapshot in snapshots
        )

        call(
            module,
            tmp_path,
            "POST",
            (
                f"/sessions/{session_id}/snapshots/"
                f"{manual_snapshot['snapshot_id']}/select"
            ),
        )
        selected_messages = call(
            module,
            tmp_path,
            "GET",
            f"/sessions/{session_id}/messages",
        )
        assert selected_messages["readonly"] is True
        assert selected_messages["snapshot_id"] == manual_snapshot["snapshot_id"]
        assert len(selected_messages["messages"]) == 3
        call(
            module,
            tmp_path,
            "DELETE",
            f"/sessions/{session_id}/snapshots/selected",
        )
        restored = call(
            module,
            tmp_path,
            "POST",
            (
                f"/sessions/{session_id}/snapshots/"
                f"{manual_snapshot['snapshot_id']}/restore"
            ),
        )
        assert len(restored["session"]["messages"]) == 3

        forked = call(
            module,
            tmp_path,
            "POST",
            f"/sessions/{session_id}/fork",
            {"index": 1},
        )
        assert forked["source_session_id"] == session_id
        assert forked["fork_upto_index"] == 1
        assert len(forked["session"]["messages"]) == 2

        copied = call(
            module,
            tmp_path,
            "POST",
            f"/sessions/{session_id}/actions",
            {
                "plugin": "session_actions",
                "action_id": "copy_session",
                "inputs": {"session_id": session_id},
            },
        )
        copied_ids = copied["result"]["mutations"]["created_session_ids"]
        assert len(copied_ids) == 1
        deleted_copy = call(
            module,
            tmp_path,
            "POST",
            "/actions",
            {
                "plugin": "session_actions",
                "action_id": "delete_session",
                "inputs": {"session_id": copied_ids[0]},
            },
        )
        assert deleted_copy["status"] == "ok"
        assert copied_ids[0] in deleted_copy["result"]["mutations"][
            "deleted_session_ids"
        ]

        plugins = call(
            module,
            tmp_path,
            "GET",
            f"/sessions/{session_id}/plugins",
        )["plugins"]
        enabled_ids = [
            entry["id"]
            for entry in plugins
            if entry.get("enabled") and isinstance(entry.get("id"), str)
        ]
        updated_plugins = call(
            module,
            tmp_path,
            "PUT",
            f"/sessions/{session_id}/plugins",
            {"enabled": enabled_ids},
        )
        assert updated_plugins["session"]["metadata"]["plugins"] == enabled_ids
        reset_plugins = call(
            module,
            tmp_path,
            "DELETE",
            f"/sessions/{session_id}/plugins",
        )
        assert "plugins" not in reset_plugins["session"]["metadata"]

        patched_settings = call(
            module,
            tmp_path,
            "PATCH",
            "/server/settings",
            {
                "values": {
                    "session_status_show_in_session_list_footer": False
                }
            },
        )
        assert (
            patched_settings["settings"][
                "session_status_show_in_session_list_footer"
            ]
            is False
        )
        assert call(
            module,
            tmp_path,
            "GET",
            "/server/settings",
        )["settings"]["session_status_show_in_session_list_footer"] is False
        assert call(
            module,
            tmp_path,
            "GET",
            "/server/settings/ui-schema",
        )["elements"]
        deleted_settings = call(
            module,
            tmp_path,
            "DELETE",
            "/server/settings/session_status_show_in_session_list_footer",
        )
        assert (
            "session_status_show_in_session_list_footer"
            not in deleted_settings["settings"]
        )

        runtime = module._get_runtime(str(tmp_path))
        asset = runtime.application.get_session_asset_store().store_base64(
            session_id=session_id,
            attachment_type="text",
            filename="note.txt",
            mime_type="text/plain",
            data_base64=base64.b64encode(b"embedded attachment").decode("ascii"),
        )
        downloaded = call(
            module,
            tmp_path,
            "POST",
            "/actions",
            {
                "plugin": "session_asset_attachments",
                "action_id": "download_attachment",
                "inputs": {
                    "session_id": session_id,
                    "asset_id": asset.asset_id,
                },
            },
        )
        assert downloaded["status"] == "ok"
        assert base64.b64decode(
            downloaded["result"]["data_base64"]
        ) == b"embedded attachment"
    finally:
        module.shutdown_runtime()
