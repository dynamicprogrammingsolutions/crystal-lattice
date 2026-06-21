from __future__ import annotations

# ruff: noqa: E402

import asyncio
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
for rel in (
    "core/python",
    "plugins/claude-tools/src",
    "plugins/mcp-shared/src",
):
    path = ROOT / rel
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from agent_core.tool_result_payloads import FORMAT_ANTHROPIC_MESSAGES  # noqa: E402
from claude_tools.claude_mcp_tool import ClaudeMCPTool  # noqa: E402
from mcp_shared import (  # noqa: E402
    MCPDiscoveredTool,
    MCPToolCallResult,
    save_persisted_oauth_tokens,
)


def _fixture(name: str) -> dict:
    path = ROOT / "plugins/claude-tools/investigation/fixtures/mcp" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _output_fixture(name: str) -> dict:
    path = (
        ROOT / "plugins/claude-tools/investigation/fixtures/mcp-output" / f"{name}.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _discovered_from_fixture(name: str) -> list[MCPDiscoveredTool]:
    fixture = _fixture(name)
    discovered = []
    for tool in fixture["mcp_tools"]:
        raw_name = str(tool["name"]).split("__", 2)[2]
        discovered.append(
            MCPDiscoveredTool(
                server_name="filesystem",
                raw_name=raw_name,
                description=tool["description"],
                input_schema=tool["input_schema"],
            )
        )
    return discovered


class _FakeRuntimeManager:
    discovered = _discovered_from_fixture("filesystem-read-file")
    result = MCPToolCallResult(
        is_error=False,
        content=[
            {"type": "text", "text": "CLAUDE_MCP_SENTINEL first line\nsecond line\n"}
        ],
    )
    calls: list[dict] = []
    last_config = None

    async def start(self, config) -> None:
        self.config = config
        type(self).last_config = config

    async def list_tools(self):
        if not self.config.servers["filesystem"].enabled:
            return []
        return list(self.discovered)

    def status_snapshot(self):
        return []

    async def close(self):
        return None

    async def call_tool(
        self,
        *,
        server_name: str,
        tool_name: str,
        arguments: dict,
        timeout_seconds=None,
    ):
        self.calls.append(
            {
                "server_name": server_name,
                "tool_name": tool_name,
                "arguments": arguments,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.result


class _RuntimeStore:
    def __init__(self) -> None:
        self.items = {}

    def get(self, key, default=None):
        return self.items.get(key, default)

    def set(self, key, value):
        self.items[key] = value

    def get_or_create(self, key, factory):
        if key not in self.items:
            self.items[key] = factory()
        return self.items[key]


def _config(tmp_path: Path) -> dict:
    return {
        "mcp_enabled": True,
        "mcp_reuse_runtime": True,
        "mcp_fail_on_startup_error": False,
        "mcp_servers": {
            "filesystem": {
                "enabled": True,
                "transport": "stdio",
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    str(tmp_path),
                ],
                "cwd": str(tmp_path),
                "startup_timeout_seconds": 30,
                "tool_timeout_seconds": 30,
            }
        },
    }


def test_claude_mcp_ui_elements_show_global_and_server_toggles(tmp_path: Path) -> None:
    tool = ClaudeMCPTool()

    elements = tool.get_ui_elements(_config(tmp_path))

    assert [item["key"] for item in elements] == [
        "mcp_enabled",
        "mcp_server__filesystem__enabled",
    ]


def test_prepare_builds_claude_mcp_schemas_from_fixture(tmp_path: Path) -> None:
    tool = ClaudeMCPTool()
    tool._runtime_manager_factory = _FakeRuntimeManager

    prepared = asyncio.run(
        tool.prepare_async(_config(tmp_path), {"config": _config(tmp_path)})
    )
    schemas = tool.get_tool_schemas({"config": _config(tmp_path)}, prepared=prepared)

    assert [schema["name"] for schema in schemas] == _fixture("filesystem-read-file")[
        "mcp_tool_names"
    ]
    assert schemas == _fixture("filesystem-read-file")["mcp_tools"]
    assert prepared["runtime_key"]


def test_prepare_loads_persisted_mcp_oauth_tokens(tmp_path: Path) -> None:
    save_persisted_oauth_tokens(
        tmp_path,
        {"filesystem": {"access_token": "persisted-access"}},
    )
    _FakeRuntimeManager.last_config = None
    tool = ClaudeMCPTool()
    tool._runtime_manager_factory = _FakeRuntimeManager

    asyncio.run(
        tool.prepare_async(
            _config(tmp_path),
            {"config": _config(tmp_path)},
            context={"runtime_store": _RuntimeStore(), "runtime_state_root": tmp_path},
        )
    )

    assert (
        _FakeRuntimeManager.last_config.servers["filesystem"].headers["Authorization"]
        == "Bearer persisted-access"
    )


def test_prepare_respects_global_disabled_toggle(tmp_path: Path) -> None:
    tool = ClaudeMCPTool()
    tool._runtime_manager_factory = _FakeRuntimeManager
    config = _config(tmp_path)
    config["mcp_enabled"] = False

    prepared = asyncio.run(tool.prepare_async(config, {"config": config}))

    assert prepared == {"runtime_key": None, "tools": []}
    assert tool.get_tool_schemas({"config": config}, prepared=prepared) == []


def test_prepare_respects_per_server_disabled_toggle(tmp_path: Path) -> None:
    tool = ClaudeMCPTool()
    tool._runtime_manager_factory = _FakeRuntimeManager
    config = _config(tmp_path)
    config["mcp_server__filesystem__enabled"] = False

    prepared = asyncio.run(tool.prepare_async(config, {"config": config}))

    assert prepared["tools"] == []


def test_prepare_treats_missing_server_enabled_as_disabled(tmp_path: Path) -> None:
    tool = ClaudeMCPTool()
    tool._runtime_manager_factory = _FakeRuntimeManager
    config = _config(tmp_path)
    config["mcp_servers"]["filesystem"].pop("enabled")

    prepared = asyncio.run(tool.prepare_async(config, {"config": config}))

    assert prepared["tools"] == []


def test_prepare_server_enabled_override_can_enable_missing_enabled(
    tmp_path: Path,
) -> None:
    tool = ClaudeMCPTool()
    tool._runtime_manager_factory = _FakeRuntimeManager
    config = _config(tmp_path)
    config["mcp_servers"]["filesystem"].pop("enabled")
    config["mcp_server__filesystem__enabled"] = True

    prepared = asyncio.run(tool.prepare_async(config, {"config": config}))

    assert prepared["tools"]


def test_execute_and_format_success_matches_fixture(tmp_path: Path) -> None:
    _FakeRuntimeManager.result = MCPToolCallResult(
        is_error=False,
        content=[
            {"type": "text", "text": "CLAUDE_MCP_SENTINEL first line\nsecond line\n"}
        ],
    )
    _FakeRuntimeManager.calls = []
    tool = ClaudeMCPTool()
    tool._runtime_manager_factory = _FakeRuntimeManager
    config = _config(tmp_path)
    prepared = asyncio.run(tool.prepare_async(config, {"config": config}))

    result = asyncio.run(
        tool.execute_tool_async(
            "mcp__filesystem__read_text_file",
            {"path": "<WORKSPACE>/note.txt"},
            {"config": config},
            tool_call={
                "id": "<TOOL_CALL_ID>",
                "name": "mcp__filesystem__read_text_file",
            },
            prepared=prepared,
        )
    )
    formatted = tool.format_tool_result(result, {"config": config})

    assert _FakeRuntimeManager.calls[-1] == {
        "server_name": "filesystem",
        "tool_name": "read_text_file",
        "arguments": {"path": "<WORKSPACE>/note.txt"},
        "timeout_seconds": None,
    }
    assert formatted["format"] == FORMAT_ANTHROPIC_MESSAGES
    assert formatted["content"] == _fixture("filesystem-read-file")["tool_results"]


def test_execute_and_format_error_matches_fixture(tmp_path: Path) -> None:
    _FakeRuntimeManager.result = MCPToolCallResult(
        is_error=True,
        content=[
            {
                "type": "text",
                "text": "ENOENT: no such file or directory, open '<WORKSPACE>/missing.txt'",
            }
        ],
    )
    tool = ClaudeMCPTool()
    tool._runtime_manager_factory = _FakeRuntimeManager
    config = _config(tmp_path)
    prepared = asyncio.run(tool.prepare_async(config, {"config": config}))

    result = asyncio.run(
        tool.execute_tool_async(
            "mcp__filesystem__read_text_file",
            {"path": "missing.txt"},
            {"config": config},
            tool_call={
                "id": "<TOOL_CALL_ID>",
                "name": "mcp__filesystem__read_text_file",
            },
            prepared=prepared,
        )
    )
    formatted = tool.format_tool_result(result, {"config": config})

    assert result["success"] is False
    assert formatted["format"] == FORMAT_ANTHROPIC_MESSAGES
    assert formatted["content"] == _fixture("filesystem-missing-file")["tool_results"]


def test_execute_and_format_truncates_large_text_output(tmp_path: Path) -> None:
    long_text = (
        "BEGIN_SENTINEL\n"
        + "".join(f"line {idx}\n" for idx in range(8_000))
        + "MIDDLE_SENTINEL\n"
        + "".join(f"tail {idx}\n" for idx in range(8_000))
        + "END_SENTINEL\n"
    )
    _FakeRuntimeManager.result = MCPToolCallResult(
        is_error=False,
        content=[{"type": "text", "text": long_text}],
    )
    tool = ClaudeMCPTool()
    tool._runtime_manager_factory = _FakeRuntimeManager
    config = _config(tmp_path)
    prepared = asyncio.run(tool.prepare_async(config, {"config": config}))

    result = asyncio.run(
        tool.execute_tool_async(
            "mcp__filesystem__read_text_file",
            {"path": "<WORKSPACE>/huge.txt"},
            {"config": config},
            tool_call={"id": "call_truncated_mcp"},
            prepared=prepared,
        )
    )
    formatted = tool.format_tool_result(result, {"config": config})

    content = formatted["content"][0]["content"]
    assert content.startswith("<persisted-output>\n")
    assert "Output too large (" in content
    assert "Full output saved to:" in content
    assert "Preview (first 2KB):" in content
    assert "BEGIN_SENTINEL" in content
    assert "MIDDLE_SENTINEL" not in content
    assert "END_SENTINEL" not in content

    saved_line = next(
        line for line in content.splitlines() if "Full output saved to:" in line
    )
    saved_path = Path(saved_line.split("Full output saved to:", 1)[1].strip())
    assert saved_path.exists()
    saved_text = saved_path.read_text(encoding="utf-8")
    assert "BEGIN_SENTINEL" in saved_text
    assert "MIDDLE_SENTINEL" in saved_text
    assert "END_SENTINEL" in saved_text


def test_large_output_fixture_records_claude_persisted_output_shape() -> None:
    success_32k = _output_fixture("success-32k")["tool_result_summaries"][0]
    success_64k = _output_fixture("success-64k")["tool_results"][0]["content"]
    error_64k = _output_fixture("error-64k")["tool_results"][0]["content"]

    assert success_32k["has_begin_sentinel"] is True
    assert success_32k["has_middle_sentinel"] is True
    assert success_32k["has_end_sentinel"] is True
    assert success_64k.startswith("<persisted-output>\n")
    assert "Output too large (" in success_64k
    assert "Preview (first 2KB):" in success_64k
    assert success_64k.endswith("\n</persisted-output>")
    assert "characters truncated" in error_64k


def test_execute_and_format_truncates_large_error_output(tmp_path: Path) -> None:
    long_error = (
        "DUMMY_ERROR_START\nBEGIN_SENTINEL\n"
        + "".join(f"line {idx}\n" for idx in range(5_000))
        + "MIDDLE_SENTINEL\n"
        + "".join(f"tail {idx}\n" for idx in range(5_000))
        + "END_SENTINEL\n"
    )
    _FakeRuntimeManager.result = MCPToolCallResult(
        is_error=True,
        content=[{"type": "text", "text": long_error}],
    )
    tool = ClaudeMCPTool()
    tool._runtime_manager_factory = _FakeRuntimeManager
    config = _config(tmp_path)
    prepared = asyncio.run(tool.prepare_async(config, {"config": config}))

    result = asyncio.run(
        tool.execute_tool_async(
            "mcp__filesystem__read_text_file",
            {"path": "<WORKSPACE>/huge-error.txt"},
            {"config": config},
            tool_call={"id": "call_truncated_mcp_error"},
            prepared=prepared,
        )
    )
    formatted = tool.format_tool_result(result, {"config": config})

    content = formatted["content"][0]["content"]
    assert formatted["content"][0]["is_error"] is True
    assert len(content) == 10_000
    assert "DUMMY_ERROR_START" in content
    assert "BEGIN_SENTINEL" in content
    assert "characters truncated" in content
    assert "MIDDLE_SENTINEL" not in content
    assert "END_SENTINEL" in content


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_filesystem_mcp_server_read(tmp_path: Path) -> None:
    if shutil.which("npx") is None:
        pytest.skip("npx not available")

    note = tmp_path / "note.txt"
    note.write_text("hello from claude mcp\nsecond line\n", encoding="utf-8")

    tool = ClaudeMCPTool()
    config = _config(tmp_path)
    config["mcp_fail_on_startup_error"] = True
    prepared = await tool.prepare_async(config, {"config": config})
    schemas = tool.get_tool_schemas({"config": config}, prepared=prepared)

    assert any(
        schema["name"] == "mcp__filesystem__read_text_file" for schema in schemas
    )

    result = await tool.execute_tool_async(
        "mcp__filesystem__read_text_file",
        {"path": str(note.resolve())},
        {"config": config},
        tool_call={"id": "call_real_mcp"},
        prepared=prepared,
    )
    formatted = tool.format_tool_result(result, {"config": config})

    assert result["success"] is True
    assert formatted["format"] == FORMAT_ANTHROPIC_MESSAGES
    assert formatted["content"][0]["tool_use_id"] == "call_real_mcp"
    assert json.loads(formatted["content"][0]["content"]) == {
        "content": "hello from claude mcp\nsecond line\n"
    }
