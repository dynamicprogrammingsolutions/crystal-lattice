from __future__ import annotations

from agent_core.tool_interop import OpenAIChatToolCallAccessor, OpenAIChatToolSchemaAccessor
from plugins.openai_tools_extension import OpenAIToolsExtension


def test_openai_tools_extension_declares_chat_tool_formats() -> None:
    ext = OpenAIToolsExtension()
    assert ext.accepted_tool_schema_formats({}, None) == [OpenAIChatToolSchemaAccessor.format_id]
    assert ext.emitted_tool_call_formats({}, None) == [OpenAIChatToolCallAccessor.format_id]