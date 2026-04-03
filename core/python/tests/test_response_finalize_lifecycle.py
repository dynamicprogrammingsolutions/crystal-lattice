from __future__ import annotations

from typing import Any, Dict, Iterator, List, Tuple

from agent_core import AgentCore

from plugins.tool_call_preview_feature import ToolCallPreviewFeature


def _raw_echo_call() -> Dict[str, Any]:
    return {
        "type": "custom_tool_call",
        "call_id": "call_raw_1",
        "name": "raw_echo",
        "input": "hello preview",
    }


class RawEchoTool:
    name = "raw_echo_tool"
    version = "1.0.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "custom",
                "name": "raw_echo",
                "description": "Echo a raw text payload",
                "format": {
                    "type": "grammar",
                    "syntax": "lark",
                    "definition": "start: /.+/",
                },
            }
        ]

    def format_tool_call_preview(
        self,
        tool_name: str,
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: str | None = None,
        payload_format: str | None = None,
        payload_metadata: Dict[str, Any] | None = None,
        tool_call: Dict[str, Any] | None = None,
    ) -> str:
        _ = tool_name, state, payload_format, payload_metadata, tool_call
        return f"preview:{payload_kind}:{payload}"

    def execute_tool(
        self,
        tool_name: str,
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: str | None = None,
        payload_format: str | None = None,
        payload_metadata: Dict[str, Any] | None = None,
        tool_call: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        _ = tool_name, state, payload_kind, payload_format, payload_metadata, tool_call
        return {"success": True, "result": str(payload).upper()}


class ToolCallNativeProvider:
    name = "tool_call_native_provider"
    version = "1.0.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config, "stream_final": None}

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            native = {
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            }
            metadata = msg.get("metadata")
            if isinstance(metadata, dict) and metadata:
                native["_metadata"] = dict(metadata)
            out.append(native)
        return out

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for msg in native_messages:
            if not isinstance(msg, dict):
                continue
            metadata = msg.get("_metadata")
            out.append(
                {
                    "role": msg.get("role", "assistant"),
                    "content": msg.get("content", ""),
                    "metadata": dict(metadata) if isinstance(metadata, dict) else {},
                }
            )
        return out

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        assistant = {
            "role": "assistant",
            "content": "",
            "_metadata": {"tool_calls": [_raw_echo_call()]},
        }
        return [], [assistant], [*native_messages, assistant], state

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        yield {"emit": "tool_call"}

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        _ = native_chunk
        assistant = {
            "role": "assistant",
            "content": "",
            "_metadata": {"tool_calls": [_raw_echo_call()]},
        }
        return [], [], list(native_messages), {**state, "stream_final": assistant}

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        assistant = state.get("stream_final")
        if isinstance(assistant, dict):
            return [assistant], [*native_messages, assistant], {**state, "stream_final": None}
        return [], list(native_messages), state


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(ToolCallNativeProvider)
    core.register_feature(ToolCallPreviewFeature)
    core.register_tool(RawEchoTool)
    return core


def test_response_finalize_adds_tool_call_previews_to_send_request() -> None:
    core = _build_core()

    session = core.create_session()
    session = core.add_message(session, "user", "preview please", config={})

    next_session, finals = core.send_request(session, {})

    assert len(finals) == 1
    metadata = finals[0].get("metadata") or {}
    assert metadata.get("tool_call_previews") == [
        {"id": "call_raw_1", "preview": "preview:text:hello preview"}
    ]

    native_messages = next_session.metadata.get("native_messages") or []
    preview_anchors = [
        item.get("_metadata")
        for item in native_messages
        if isinstance(item, dict)
        and isinstance(item.get("_metadata"), dict)
        and "tool_call_previews" in item.get("_metadata", {})
    ]
    assert len(preview_anchors) == 1
    assert preview_anchors[0].get("tool_call_previews") == [
        {"id": "call_raw_1", "preview": "preview:text:hello preview"}
    ]


def test_response_finalize_preview_persists_through_rebuild_from_native() -> None:
    core = _build_core()

    session = core.create_session()
    session = core.add_message(session, "user", "preview please", config={})
    next_session, _finals = core.send_request(session, {})

    rebuilt_messages, _post_init_native = core._rebuild_core_from_native(
        next_session.metadata.get("native_messages") or [],
        {},
    )
    rebuilt = [msg.to_dict() for msg in rebuilt_messages]
    assistant_metadata = rebuilt[-1].get("metadata") or {}
    assert assistant_metadata.get("tool_call_previews") == [
        {"id": "call_raw_1", "preview": "preview:text:hello preview"}
    ]


def test_response_finalize_adds_tool_call_previews_to_streaming_final_event() -> None:
    core = _build_core()

    session = core.create_session()
    session = core.add_message(session, "user", "preview please", config={})

    events = list(core.send_request_stream(session, {}))
    final_event = next(event for event in events if event.get("type") == "final")

    messages = final_event.get("messages") or []
    assert len(messages) == 1
    metadata = messages[0].get("metadata") or {}
    assert metadata.get("tool_call_previews") == [
        {"id": "call_raw_1", "preview": "preview:text:hello preview"}
    ]


def test_preview_restore_only_patches_first_assistant_for_shared_native_index() -> None:
    feature = ToolCallPreviewFeature()
    native_messages = [
        {
            "role": "assistant",
            "content": "",
            "_metadata": {
                "tool_call_previews": [
                    {"id": "call_raw_1", "preview": "preview:text:hello preview"}
                ]
            },
        }
    ]
    messages = [
        {"role": "assistant", "content": "", "metadata": {"native_indices": [0]}},
        {"role": "tool", "content": "result", "metadata": {"native_indices": [0]}},
        {"role": "assistant", "content": "later", "metadata": {"native_indices": [0]}},
    ]

    rebuilt = feature.from_native_messages(native_messages, messages)

    assert (rebuilt[0].get("metadata") or {}).get("tool_call_previews") == [
        {"id": "call_raw_1", "preview": "preview:text:hello preview"}
    ]
    assert "tool_call_previews" not in ((rebuilt[1].get("metadata") or {}))
    assert "tool_call_previews" not in ((rebuilt[2].get("metadata") or {}))