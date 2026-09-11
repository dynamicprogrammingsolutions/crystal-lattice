from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import time


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
    assert legacy_config["agents"]["reviewer-claude"]["plugins"] == [
        "embedded_claude_tools.read_tool.ClaudeLikeReadTool",
        "embedded_claude_tools.write_tool.ClaudeLikeWriteTool",
        "embedded_claude_tools.edit_tool.ClaudeLikeEditTool",
        "embedded_claude_tools.glob_tool.ClaudeLikeGlobTool",
        "embedded_claude_tools.grep_tool.ClaudeLikeGrepTool",
        "embedded_claude_tools.web_fetch_tool.ClaudeLikeWebFetchTool",
    ]

    full_configuration = {
        "version": 2,
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
    assert runtime_config["providers"]["reviewer"]["provider"] == (
        "reference_openai_compatible"
    )
    assert runtime_config["providers"]["openai"]["provider"] == "openai_responses"
    assert runtime_config["providers"]["openai"]["provider_transport"] == "requests"
    assert runtime_config["providers"]["openrouter"]["provider"] == "openrouter"
    assert runtime_config["providers"]["anthropic"]["provider"] == "anthropic"
    assert runtime_config["providers"]["anthropic"]["provider_transport"] == (
        "requests"
    )
    assert runtime_config["agents"]["openai-codex"]["plugins"] == (
        module.CODEX_TOOL_PLUGINS
    )
    for agent_id in (
        "reviewer-claude",
        "openrouter-claude",
        "anthropic-claude",
    ):
        assert runtime_config["agents"][agent_id]["plugins"] == (
            module.CLAUDE_TOOL_PLUGINS
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
            "openai-codex",
            "openrouter-claude",
            "reviewer-claude",
        ]
        default_session = runtime.create_session()
        assert default_session.metadata["agent_id"] == "openai-codex"
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
