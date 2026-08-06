from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterator

from agent_core.types import ProviderPlugin, ToolPlugin


@dataclass
class EvaluationProvider(ProviderPlugin):
    name: str = "agent_eval_test_provider"
    version: str = "1.0.0"

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "model": {"type": "string", "required": True},
            "response_mode": {"type": "string", "required": False},
            "response_text": {"type": "string", "required": False},
        }

    def get_ui_elements(
        self,
        config: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        models: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        return []

    def get_tags(
        self,
        config: dict[str, Any],
        models: list[dict[str, Any]],
    ) -> list[str]:
        return ["provider:openai_compatible", "supports_tools"]

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {
            "config": dict(config),
            "runtime_state": {"content": ""},
        }

    def to_native_messages(
        self,
        messages: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return list(messages)

    def from_native_messages(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return list(native_messages)

    def initialize_request(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        return list(native_messages), {
            **state,
            "runtime_state": {"content": ""},
        }

    def call_api(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        dict[str, Any],
    ]:
        config = state.get("config") or {}
        mode = config.get("response_mode") or "echo"
        last = native_messages[-1] if native_messages else {}

        if mode == "tool_once" and last.get("role") != "tool":
            assistant = {
                "role": "assistant",
                "content": "",
                "metadata": {
                    "tool_calls": [
                        {
                            "id": "eval_call_1",
                            "type": "function",
                            "function": {
                                "name": "add",
                                "arguments": json.dumps({"a": 2, "b": 3}),
                            },
                        }
                    ]
                },
            }
        elif mode == "tool_once":
            assistant = {
                "role": "assistant",
                "content": f"Tool completed: {last.get('content', '')}",
                "metadata": {},
            }
        else:
            response_text = config.get("response_text")
            if response_text is None:
                response_text = f"Echo: {last.get('content', '')}"
            assistant = {
                "role": "assistant",
                "content": str(response_text),
                "metadata": {},
            }

        return (
            [],
            [assistant],
            [*native_messages, assistant],
            state,
        )

    def stream_api(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> Iterator[dict[str, Any]]:
        config = state.get("config") or {}
        last = native_messages[-1] if native_messages else {}
        response_text = config.get("response_text")
        if response_text is None:
            response_text = f"Echo: {last.get('content', '')}"
        for character in str(response_text):
            yield {"content": character}

    def process_chunk(
        self,
        native_chunk: dict[str, Any],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        dict[str, Any],
    ]:
        content = str(native_chunk.get("content") or "")
        accumulated = str(
            (state.get("runtime_state") or {}).get("content") or ""
        )
        new_state = {
            **state,
            "runtime_state": {"content": accumulated + content},
        }
        partial = {"role": "assistant", "content": content, "metadata": {}}
        return (
            [partial] if content else [],
            [],
            list(native_messages),
            new_state,
        )

    def finalize(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        dict[str, Any],
    ]:
        content = str(
            (state.get("runtime_state") or {}).get("content") or ""
        )
        if not content:
            return [], list(native_messages), state
        assistant = {
            "role": "assistant",
            "content": content,
            "metadata": {},
        }
        return [assistant], [*native_messages, assistant], state


@dataclass
class AddTool(ToolPlugin):
    name: str = "agent_eval_add_tool"
    version: str = "1.0.0"

    def get_config_schema(self) -> dict[str, Any]:
        return {}

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"config": config}

    def get_tool_schemas(
        self,
        state: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "add",
                    "description": "Add two numbers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number"},
                            "b": {"type": "number"},
                        },
                        "required": ["a", "b"],
                    },
                },
            }
        ]

    def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        if tool_name != "add":
            return {"success": False, "error": f"unknown tool {tool_name}"}
        return {
            "success": True,
            "result": arguments.get("a", 0) + arguments.get("b", 0),
        }

    def format_tool_result(
        self,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> str:
        if result.get("success"):
            return f"Result: {result.get('result')}"
        return f"Error: {result.get('error')}"