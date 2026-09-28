from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional, Tuple

from agent_core.types import ToolPlugin
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider


class DateSessionFilterAppPlugin:
    name = "date_session_filter_fixture"
    version = "0.1.0"

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        _ = app_config
        return {}

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state, config, context
        return [
            {
                "ui_type": "session_list_filter",
                "id": "modified_after",
                "label": "Modified after",
                "data": "modified",
                "type": "datetime",
                "match": "on_or_after",
                "default": None,
            }
        ]

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return []


class DeterministicLongToolProvider(EchoOpenAILikeProvider):
    name = "deterministic_long_tool_provider"
    version = "0.1.0"

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        if any(message.get("role") == "tool" for message in native_messages):
            final = {
                "role": "assistant",
                "content": "Long tool workflow completed",
            }
        else:
            final = {
                "role": "assistant",
                "content": "",
                "_metadata": {
                    "tool_calls": [
                        {
                            "id": "long-tool-call",
                            "type": "function",
                            "function": {
                                "name": "generate_long_output",
                                "arguments": "{}",
                            },
                        }
                    ]
                },
            }
        return [], [final], [*native_messages, final], state

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        _ = native_messages, state
        raise NotImplementedError
        yield  # pragma: no cover


class DeterministicLongOutputTool(ToolPlugin):
    name = "deterministic_long_output_tool"
    version = "0.1.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def get_tool_schemas(
        self,
        state: Dict[str, Any],
        *,
        prepared: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state, prepared
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_long_output",
                    "description": "Generate deterministic long test output",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            }
        ]

    def execute_tool(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        **_kwargs: Any,
    ) -> Dict[str, Any]:
        _ = payload, state
        if tool_name != "generate_long_output":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        return {
            "success": True,
            "result": "long-result-" * 2000,
        }

    def format_tool_result(
        self,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> str:
        _ = state
        return str(result.get("result", ""))

    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = result, state
        return {
            "type": "text",
            "content": text,
            "single_line": "Generated deterministic long output",
        }


class DeterministicFailureProvider(EchoOpenAILikeProvider):
    name = "deterministic_failure_provider"
    version = "0.1.0"

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        _ = native_messages, state
        raise RuntimeError("deterministic provider failure")

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        _ = native_messages, state
        raise RuntimeError("deterministic provider failure")
        yield  # pragma: no cover


__all__ = [
    "DateSessionFilterAppPlugin",
    "DeterministicFailureProvider",
    "DeterministicLongOutputTool",
    "DeterministicLongToolProvider",
]
