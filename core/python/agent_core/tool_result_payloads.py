"""Helpers for explicit provider-native tool result payloads."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


PROVIDER_NATIVE_TOOL_RESULT_TYPE = "provider_native_tool_result"
FORMAT_OPENAI_CHAT_COMPLETIONS = "openai.chat_completions"
FORMAT_OPENAI_RESPONSES = "openai.responses"


def is_provider_native_tool_result(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("type") == PROVIDER_NATIVE_TOOL_RESULT_TYPE
        and isinstance(value.get("format"), str)
    )


def provider_native_tool_result_format(value: Any) -> Optional[str]:
    if not is_provider_native_tool_result(value):
        return None
    fmt = value.get("format")
    return fmt if isinstance(fmt, str) else None


def openai_chat_tool_result_content(value: Any) -> Optional[List[Dict[str, Any]]]:
    if provider_native_tool_result_format(value) != FORMAT_OPENAI_CHAT_COMPLETIONS:
        return None
    content = value.get("content") if isinstance(value, dict) else None
    if isinstance(content, list) and all(isinstance(item, dict) for item in content):
        return content
    return None


def openai_responses_tool_result_output(value: Any) -> Optional[List[Dict[str, Any]]]:
    fmt = provider_native_tool_result_format(value)
    if fmt == FORMAT_OPENAI_RESPONSES:
        output = value.get("output") if isinstance(value, dict) else None
        if isinstance(output, list) and all(isinstance(item, dict) for item in output):
            return output
        return None

    if fmt == FORMAT_OPENAI_CHAT_COMPLETIONS:
        content = openai_chat_tool_result_content(value)
        if content is None:
            return None
        return openai_chat_content_to_responses_output(content)

    return None


def openai_chat_content_to_responses_output(
    content: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for part in content:
        part_type = part.get("type")
        if part_type == "text":
            text = part.get("text")
            if isinstance(text, str) and text:
                output.append({"type": "input_text", "text": text})
            continue
        if part_type == "image_url":
            image_url = part.get("image_url")
            url = image_url.get("url") if isinstance(image_url, dict) else image_url
            if isinstance(url, str) and url:
                output.append({"type": "input_image", "image_url": url})
            continue
        if part_type in {"input_text", "input_image"}:
            output.append(dict(part))
    return output


def make_provider_native_tool_result(
    *,
    format: str,
    content: Optional[List[Dict[str, Any]]] = None,
    output: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "type": PROVIDER_NATIVE_TOOL_RESULT_TYPE,
        "format": format,
    }
    if content is not None:
        payload["content"] = content
    if output is not None:
        payload["output"] = output
    return payload
