"""Unit tests for ApplyPatchTool plugin (Codex-style apply_patch)."""

from __future__ import annotations

from textwrap import dedent

from agent_core import AgentCore
from agent_core.plugin import ToolWrapper
from agent_core.tool_interop import (
    OpenAIChatToolSchemaAccessor,
    OpenAIResponsesCustomToolSchemaAccessor,
    OpenAIResponsesFunctionToolSchemaAccessor,
)

from codex_tools.apply_patch_tool import ApplyPatchTool


def _build_wrapper(tmp_path, extra_config=None):
    wrapper = ToolWrapper(ApplyPatchTool)
    config = {
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
    }
    if extra_config:
        config.update(extra_config)
    state = wrapper.init(config)
    return wrapper, state


def _sample_patch() -> str:
    return dedent(
        """\
        *** Begin Patch
        *** Add File: new.txt
        +hello
        +world
        *** Update File: foo.txt
        @@
         line1
        -line2
        +line2-updated
         line3
        *** Delete File: delete_me.txt
        *** End Patch
        """
    )


def test_apply_patch_exposes_function_fallback_schema_by_default(tmp_path):
    wrapper, state = _build_wrapper(tmp_path)

    schemas = wrapper.get_tool_schemas(state)

    assert len(schemas) == 1
    schema = schemas[0]
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "apply_patch"
    assert list(schema["function"]["parameters"]["properties"].keys()) == ["input"]
    assert schema["function"]["parameters"]["required"] == ["input"]
    assert schema["function"]["parameters"]["additionalProperties"] is False


def test_apply_patch_exposes_custom_schema_for_responses_targets(tmp_path):
    wrapper, state = _build_wrapper(
        tmp_path,
        extra_config={
            "_tool_schema_target_formats": [
                OpenAIResponsesCustomToolSchemaAccessor.format_id,
            ]
        },
    )

    schemas = wrapper.get_tool_schemas(state)

    assert len(schemas) == 1
    schema = schemas[0]
    assert schema["type"] == "custom"
    assert schema["name"] == "apply_patch"
    assert schema["format"]["type"] == "grammar"
    assert schema["format"]["syntax"] == "lark"
    assert "FREEFORM" in schema["description"]


def test_apply_patch_prefers_custom_over_function_when_both_supported(tmp_path):
    wrapper, state = _build_wrapper(
        tmp_path,
        extra_config={
            "_tool_schema_target_formats": [
                OpenAIChatToolSchemaAccessor.format_id,
                OpenAIResponsesCustomToolSchemaAccessor.format_id,
            ]
        },
    )

    schemas = wrapper.get_tool_schemas(state)

    assert len(schemas) == 1
    assert schemas[0]["type"] == "custom"


def test_apply_patch_add_update_and_delete_via_function_input(tmp_path):
    wrapper, state = _build_wrapper(tmp_path)

    target = tmp_path / "foo.txt"
    target.write_text("line1\nline2\nline3\n", encoding="utf-8")
    to_delete = tmp_path / "delete_me.txt"
    to_delete.write_text("delete me\n", encoding="utf-8")

    patch = _sample_patch()
    result = wrapper.execute_tool("apply_patch", {"input": patch}, state)

    assert result["success"] is True
    changes = result.get("changes") or {}
    assert changes["new.txt"]["type"] == "add"
    assert changes["foo.txt"]["type"] == "update"
    assert changes["delete_me.txt"]["type"] == "delete"

    assert (tmp_path / "new.txt").read_text(encoding="utf-8") == "hello\nworld"
    assert target.read_text(encoding="utf-8") == "line1\nline2-updated\nline3\n"
    assert not to_delete.exists()

    formatted = wrapper.format_tool_result(result, state)
    display = wrapper.to_display_format(formatted, result, state)
    assert display.get("type") == "text"
    assert "Patch:" in display.get("content", "")
    assert "add: new.txt" in display.get("single_line", "")


def test_apply_patch_add_update_and_delete_via_freeform_text(tmp_path):
    wrapper, state = _build_wrapper(tmp_path)

    target = tmp_path / "foo.txt"
    target.write_text("line1\nline2\nline3\n", encoding="utf-8")
    to_delete = tmp_path / "delete_me.txt"
    to_delete.write_text("delete me\n", encoding="utf-8")

    patch = _sample_patch()
    result = wrapper.execute_tool("apply_patch", patch, state, payload_kind="text")

    assert result["success"] is True
    assert (tmp_path / "new.txt").exists()
    assert target.read_text(encoding="utf-8") == "line1\nline2-updated\nline3\n"
    assert not to_delete.exists()


def test_apply_patch_preview_supports_both_payload_forms(tmp_path):
    wrapper, state = _build_wrapper(tmp_path)
    patch = _sample_patch()

    dict_preview = wrapper.format_tool_call_preview("apply_patch", {"input": patch}, state)
    text_preview = wrapper.format_tool_call_preview(
        "apply_patch", patch, state, payload_kind="text"
    )

    assert "add: new.txt" in dict_preview
    assert "update: foo.txt" in dict_preview
    assert dict_preview == text_preview


def test_apply_patch_rejects_paths_outside_allowed(tmp_path):
    base_dir = tmp_path
    safe_dir = base_dir / "safe"
    safe_dir.mkdir(parents=True, exist_ok=True)

    wrapper = ToolWrapper(ApplyPatchTool)
    state = wrapper.init(
        {
            "working_directory": str(base_dir),
            "allowed_paths": [str(safe_dir)],
        }
    )

    patch = dedent(
        """\
        *** Begin Patch
        *** Add File: evil.txt
        +oops
        *** End Patch
        """
    )

    result = wrapper.execute_tool("apply_patch", {"input": patch}, state)

    assert result["success"] is False
    assert "Access denied" in str(result.get("error", ""))
    assert not (base_dir / "evil.txt").exists()


def test_apply_patch_rejects_absolute_path_outside_allowed(tmp_path):
    wrapper, state = _build_wrapper(tmp_path)

    from pathlib import Path

    outside = Path("/") / "tmp" / "not-allowed.txt"
    patch = dedent(
        f"""\
        *** Begin Patch
        *** Add File: {outside}
        +data
        *** End Patch
        """
    )

    result = wrapper.execute_tool("apply_patch", {"input": patch}, state)
    assert result["success"] is False
    assert "Access denied" in str(result.get("error", ""))


def test_apply_patch_invalid_format(tmp_path):
    wrapper, state = _build_wrapper(tmp_path)

    result = wrapper.execute_tool("apply_patch", {"input": "not a real patch"}, state)

    assert result["success"] is False
    assert "Patch failed" in str(result.get("error", "")) or "Invalid patch" in str(
        result.get("error", "")
    )


def test_apply_patch_respects_max_patch_bytes(tmp_path):
    wrapper, state = _build_wrapper(tmp_path)
    state["config"]["max_patch_bytes"] = 10

    patch = dedent(
        """\
        *** Begin Patch
        *** End Patch
        """
    )

    result = wrapper.execute_tool("apply_patch", {"input": patch}, state)

    assert result["success"] is False
    assert "Patch too large" in str(result.get("error", ""))


def test_apply_patch_reports_changes_and_fuzz(tmp_path):
    wrapper, state = _build_wrapper(tmp_path)

    target = tmp_path / "file.txt"
    target.write_text("alpha\nbeta\n", encoding="utf-8")

    patch = dedent(
        """\
        *** Begin Patch
        *** Update File: file.txt
        @@
         alpha
        -beta
        +beta-updated
        *** End Patch
        """
    )

    result = wrapper.execute_tool("apply_patch", {"input": patch}, state)

    assert result["success"] is True
    assert "file.txt" in (result.get("changes") or {})
    assert isinstance(result.get("fuzz"), int)
    assert target.read_text(encoding="utf-8") == "alpha\nbeta-updated\n"


def test_apply_patch_expands_tilde_in_allowed_paths(tmp_path):
    import uuid
    from pathlib import Path

    home = Path.home()
    unique_dir = f".test_apply_patch_{uuid.uuid4().hex[:8]}"
    test_dir = home / unique_dir
    test_dir.mkdir(exist_ok=True)

    try:
        wrapper = ToolWrapper(ApplyPatchTool)
        state = wrapper.init(
            {
                "working_directory": str(tmp_path),
                "allowed_paths": ["~/" + unique_dir],
            }
        )

        patch = dedent(
            f"""\
            *** Begin Patch
            *** Add File: ~/{unique_dir}/test.txt
            +hello from tilde
            *** End Patch
            """
        )

        result = wrapper.execute_tool("apply_patch", {"input": patch}, state)

        assert result["success"] is True
        assert f"~/{unique_dir}/test.txt" in (result.get("changes") or {})
        created_file = test_dir / "test.txt"
        assert created_file.exists()
        assert created_file.read_text(encoding="utf-8") == "hello from tilde"
    finally:
        import shutil

        if test_dir.exists():
            shutil.rmtree(test_dir)


def test_core_provider_capabilities_select_custom_apply_patch_schema() -> None:
    class ResponsesProvider:
        name = "responses_provider"
        version = "1.0.0"

        def init(self, config):
            return {"config": config}

        def get_tags(self, config, models):
            return ["supports_tools", "provider:responses"]

        def accepted_tool_schema_formats(self, config, state=None):
            return [
                OpenAIResponsesCustomToolSchemaAccessor.format_id,
                OpenAIResponsesFunctionToolSchemaAccessor.format_id,
            ]

    core = AgentCore()
    core.register_provider(ResponsesProvider)
    core.register_tool(ApplyPatchTool)

    schemas = core.get_tool_schemas({})

    assert len(schemas) == 1
    assert schemas[0]["type"] == "custom"


def test_core_provider_capabilities_select_function_fallback_schema() -> None:
    class ChatProvider:
        name = "chat_provider"
        version = "1.0.0"

        def init(self, config):
            return {"config": config}

        def get_tags(self, config, models):
            return ["supports_tools", "provider:chat"]

        def accepted_tool_schema_formats(self, config, state=None):
            return [OpenAIChatToolSchemaAccessor.format_id]

    core = AgentCore()
    core.register_provider(ChatProvider)
    core.register_tool(ApplyPatchTool)

    schemas = core.get_tool_schemas({})

    assert len(schemas) == 1
    assert schemas[0]["type"] == "function"
    assert list(schemas[0]["function"]["parameters"]["properties"].keys()) == ["input"]