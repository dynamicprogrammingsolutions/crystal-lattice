from __future__ import annotations

from agent_core.plugin import ToolWrapper

from template_python_tools.echo_tool import TemplateEchoTool


def test_template_echo_tool_executes_and_formats() -> None:
    wrapper = ToolWrapper(TemplateEchoTool)
    state = wrapper.init({})
    schemas = wrapper.get_tool_schemas(state)
    assert (schemas[0].get("function") or {}).get("name") == "template_echo"

    result = wrapper.execute_tool("template_echo", {"value": "hi"}, state)
    assert result["success"] is True

    text = wrapper.format_tool_result(result, state)
    assert text == "hi"
