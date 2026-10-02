"""Lossless Anthropic content-block stream reduction."""

from __future__ import annotations

import json
from typing import Any


def object_to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {str(key): object_to_value(item) for key, item in value.items()}
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        result = dump(mode="json", exclude_none=True)
        return object_to_dict(result)
    return {}


def object_to_value(value: Any) -> Any:
    if isinstance(value, dict):
        return object_to_dict(value)
    if isinstance(value, list):
        return [object_to_value(item) for item in value]
    if isinstance(value, tuple):
        return [object_to_value(item) for item in value]
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        return object_to_dict(value)
    return value


def empty_assistant() -> dict[str, Any]:
    return {"role": "assistant", "content": []}


def _blocks(message: dict[str, Any]) -> list[dict[str, Any]]:
    content = message.get("content")
    if not isinstance(content, list):
        return []
    return [dict(block) for block in content if isinstance(block, dict)]


def _set_block(
    message: dict[str, Any], index: int, block: dict[str, Any]
) -> dict[str, Any]:
    blocks = _blocks(message)
    while len(blocks) <= index:
        blocks.append({"type": "unknown"})
    blocks[index] = dict(block)
    return {**message, "role": "assistant", "content": blocks}


def _update_block(
    message: dict[str, Any], index: int, delta: dict[str, Any]
) -> dict[str, Any]:
    blocks = _blocks(message)
    while len(blocks) <= index:
        blocks.append({"type": "unknown"})
    current = dict(blocks[index])
    delta_type = delta.get("type")

    if delta_type == "text_delta":
        current["type"] = current.get("type") or "text"
        current["text"] = str(current.get("text") or "") + str(delta.get("text") or "")
    elif delta_type == "thinking_delta":
        current["type"] = current.get("type") or "thinking"
        current["thinking"] = str(current.get("thinking") or "") + str(
            delta.get("thinking") or ""
        )
    elif delta_type == "signature_delta":
        current["signature"] = str(current.get("signature") or "") + str(
            delta.get("signature") or ""
        )
    elif delta_type == "input_json_delta":
        current["type"] = current.get("type") or "tool_use"
        current["_partial_json"] = str(current.get("_partial_json") or "") + str(
            delta.get("partial_json") or ""
        )
    elif delta_type == "compaction_delta":
        current["type"] = "compaction"
        for key in ("content", "encrypted_content"):
            if key in delta:
                current[key] = delta[key]
    else:
        unknown_deltas = current.get("_unknown_deltas")
        prior_unknown = unknown_deltas if isinstance(unknown_deltas, list) else []
        current["_unknown_deltas"] = [
            *prior_unknown,
            dict(delta),
        ]

    blocks[index] = current
    return {**message, "role": "assistant", "content": blocks}


def _finish_block(message: dict[str, Any], index: int) -> dict[str, Any]:
    blocks = _blocks(message)
    if index >= len(blocks):
        return message
    current = dict(blocks[index])
    partial_json = current.pop("_partial_json", None)
    if isinstance(partial_json, str):
        try:
            parsed = json.loads(partial_json or "{}")
        except json.JSONDecodeError:
            parsed = {}
        current["input"] = parsed if isinstance(parsed, dict) else {}
    blocks[index] = current
    return {**message, "content": blocks}


def reduce_event(
    accumulator: dict[str, Any] | None,
    event: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any], bool]:
    """Return chunk-local partial, updated assistant, and completion flag."""

    message = dict(accumulator) if isinstance(accumulator, dict) else empty_assistant()
    event_type = event.get("type")
    partial: dict[str, Any] | None = None
    completed = False

    if event_type == "message_start":
        raw_message = event.get("message")
        if isinstance(raw_message, dict):
            message = {
                "role": "assistant",
                "content": [
                    dict(block)
                    for block in raw_message.get("content", [])
                    if isinstance(block, dict)
                ],
                "_metadata": {
                    "anthropic": {
                        key: raw_message.get(key)
                        for key in (
                            "id",
                            "model",
                            "stop_reason",
                            "stop_sequence",
                            "context_management",
                        )
                        if raw_message.get(key) is not None
                    }
                },
            }
    elif event_type == "content_block_start":
        index = event.get("index")
        block = event.get("content_block")
        if isinstance(index, int) and isinstance(block, dict):
            message = _set_block(message, index, block)
            partial = {"role": "assistant", "content": ""}
    elif event_type == "content_block_delta":
        index = event.get("index")
        delta = event.get("delta")
        if isinstance(index, int) and isinstance(delta, dict):
            message = _update_block(message, index, delta)
            text = delta.get("text") if delta.get("type") == "text_delta" else ""
            partial = {"role": "assistant", "content": text or ""}
    elif event_type == "content_block_stop":
        index = event.get("index")
        if isinstance(index, int):
            message = _finish_block(message, index)
    elif event_type == "message_delta":
        delta = event.get("delta")
        metadata = dict(message.get("_metadata") or {})
        anthropic_metadata = dict(metadata.get("anthropic") or {})
        if isinstance(delta, dict):
            for key in ("stop_reason", "stop_sequence"):
                if delta.get(key) is not None:
                    anthropic_metadata[key] = delta[key]
        context_management = event.get("context_management")
        if isinstance(context_management, dict):
            anthropic_metadata["context_management"] = dict(context_management)
        message["_metadata"] = {
            **metadata,
            "anthropic": anthropic_metadata,
        }
    elif event_type == "message_stop":
        completed = True

    return partial, message, completed


def strip_runtime_fields(value: Any) -> Any:
    if isinstance(value, list):
        return [strip_runtime_fields(item) for item in value]
    if not isinstance(value, dict):
        return value
    return {
        key: strip_runtime_fields(item)
        for key, item in value.items()
        if key != "_metadata" and not key.startswith("_")
    }
