from __future__ import annotations

import json
from pathlib import Path

from agent_core import AgentCore
from agent_core.tool_interop import OpenAIResponsesCustomToolSchemaAccessor
from embedded_tools_shared import FetchedPage

from embedded_codex_tools import (
    CodexLikeApplyPatchTool,
    CodexLikeCurlTool,
    CodexLikeFindTool,
    CodexLikeRgTool,
    CodexLikeSedTool,
)
from embedded_codex_tools import curl_tool as curl_module


def _function_call(
    name: str,
    arguments: dict[str, object],
    call_id: str,
) -> dict[str, object]:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(arguments),
        },
    }


def test_schema_names_are_lowercase_and_command_shaped(tmp_path: Path) -> None:
    config = {"working_directory": str(tmp_path)}
    tools = [
        CodexLikeSedTool(),
        CodexLikeRgTool(),
        CodexLikeFindTool(),
        CodexLikeCurlTool(),
        CodexLikeApplyPatchTool(),
    ]
    schemas = [tool.get_tool_schemas(tool.init(config))[0] for tool in tools]
    names = [
        schema.get("name") or schema.get("function", {}).get("name")
        for schema in schemas
    ]
    assert names == ["sed", "rg", "find", "curl", "apply_patch"]
    assert "sed -n" in schemas[0]["function"]["description"]
    assert "rg -n" in schemas[1]["function"]["description"]
    assert "find <path>" in schemas[2]["function"]["description"]
    assert "curl -L" in schemas[3]["function"]["description"]


def test_sed_rg_and_find_return_bash_like_results(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "docs/nested").mkdir(parents=True)
    (workspace / "notes.txt").write_text(
        "one\ntwo\nORBITAL\nfour\n",
        encoding="utf-8",
    )
    (workspace / "docs/a.md").write_text("ORBITAL alpha\n", encoding="utf-8")
    (workspace / "docs/nested/b.md").write_text("beta\n", encoding="utf-8")
    config = {"working_directory": str(workspace)}
    core = AgentCore()
    core.register_tool(CodexLikeSedTool)
    core.register_tool(CodexLikeRgTool)
    core.register_tool(CodexLikeFindTool)

    sed = core.execute_tool_calls(
        [
            _function_call(
                "sed",
                {
                    "path": "notes.txt",
                    "from_line": 2,
                    "to_line": 3,
                    "show_line_numbers": True,
                },
                "sed-1",
            )
        ],
        config,
    )[0]
    assert "Command: sed -n '2,3p' notes.txt" in sed["content"]
    assert "Exit code: 0" in sed["content"]
    assert "2\ttwo\n3\tORBITAL" in sed["content"]

    rg = core.execute_tool_calls(
        [
            _function_call(
                "rg",
                {
                    "pattern": "ORBITAL",
                    "path": ".",
                    "fixed_strings": True,
                    "max_results": 10_000,
                },
                "rg-1",
            )
        ],
        config,
    )[0]
    assert "Exit code: 0" in rg["content"]
    assert "docs/a.md:1:ORBITAL alpha" in rg["content"]
    assert "notes.txt:3:ORBITAL" in rg["content"]

    no_match = core.execute_tool_calls(
        [
            _function_call(
                "rg",
                {"pattern": "missing", "path": "."},
                "rg-2",
            )
        ],
        config,
    )[0]
    assert "Exit code: 1" in no_match["content"]

    found = core.execute_tool_calls(
        [
            _function_call(
                "find",
                {
                    "path": "docs",
                    "name": "*.md",
                    "type": "file",
                    "sort": True,
                },
                "find-1",
            )
        ],
        config,
    )[0]
    assert "Command: find docs -type f -name '*.md' -print | sort" in found[
        "content"
    ]
    assert "docs/a.md\ndocs/nested/b.md" in found["content"]


def test_apply_patch_uses_freeform_responses_schema_and_shared_guard(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "settings.txt").write_text("mode=old\n", encoding="utf-8")
    tool = CodexLikeApplyPatchTool()
    state = tool.init(
        {
            "working_directory": str(workspace),
            "_tool_schema_target_formats": [
                OpenAIResponsesCustomToolSchemaAccessor.format_id
            ],
        }
    )
    schema = tool.get_tool_schemas(state)[0]
    assert schema["type"] == "custom"
    assert schema["name"] == "apply_patch"

    result = tool.execute_tool(
        "apply_patch",
        """*** Begin Patch
*** Update File: settings.txt
@@
-mode=old
+mode=new
*** Add File: added.txt
+created
*** End Patch
""",
        state,
        payload_kind="text",
    )
    assert result["success"]
    assert (workspace / "settings.txt").read_text(encoding="utf-8") == "mode=new\n"
    assert (workspace / "added.txt").read_text(encoding="utf-8") == "created"
    assert "Patch applied successfully" in tool.format_tool_result(result, state)

    escaped = tool.execute_tool(
        "apply_patch",
        """*** Begin Patch
*** Add File: ../outside.txt
+blocked
*** End Patch
""",
        state,
        payload_kind="text",
    )
    assert not escaped["success"]
    assert not (tmp_path / "outside.txt").exists()


def test_curl_uses_shared_fetch_and_bash_like_output(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _ = tmp_path

    def fake_fetch(url: str, *, policy):
        assert policy.max_bytes == 4096
        return FetchedPage(
            requested_url=url,
            final_url=url,
            status_code=200,
            reason="OK",
            headers=(("Content-Type", "text/html"), ("X-Test", "yes")),
            content_type="text/html",
            body_text="<html><title>Example</title></html>",
            extracted_text="Example",
            title="Example",
            truncated_bytes=False,
            truncated_text=False,
            duration_seconds=0.01,
        )

    monkeypatch.setattr(curl_module, "fetch_public_url", fake_fetch)
    tool = CodexLikeCurlTool()
    state = tool.init({})
    result = tool.execute_tool(
        "curl",
        {
            "url": "https://example.com",
            "max_bytes": 4096,
            "include_headers": True,
        },
        state,
    )
    assert result["success"]
    assert (
        result["command"]
        == "curl -L --fail --silent --show-error https://example.com"
    )
    assert "Exit code: 0" in result["output"]
    assert "X-Test: yes" in result["output"]
    assert "<html><title>Example</title></html>" in result["output"]