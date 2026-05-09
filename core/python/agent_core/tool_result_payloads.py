"""Helpers for explicit provider-native tool result payloads."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .tool_interop import (
    ANTHROPIC_MESSAGES_TOOL_RESULT_FORMAT,
    CORE_TOOL_RESULT_TYPE,
    DEFAULT_TOOL_INTEROP_REGISTRY,
    OPENAI_CHAT_TOOL_RESULT_FORMAT,
    OPENAI_CHAT_TOOL_RESULT_FORMAT_ID,
    OPENAI_RESPONSES_TOOL_RESULT_FORMAT,
    OPENAI_RESPONSES_TOOL_RESULT_FORMAT_ID,
    PROVIDER_NATIVE_TOOL_RESULT_TYPE,
    SESSION_ASSET_DOWNLOAD_PLUGIN_ID,
    ToolInteropError,
    ToolInteropTarget,
)

FORMAT_OPENAI_CHAT_COMPLETIONS = OPENAI_CHAT_TOOL_RESULT_FORMAT
FORMAT_OPENAI_RESPONSES = OPENAI_RESPONSES_TOOL_RESULT_FORMAT
FORMAT_ANTHROPIC_MESSAGES = ANTHROPIC_MESSAGES_TOOL_RESULT_FORMAT
TOOL_RESULT_FIELD = "toolResult"


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


def is_core_tool_result(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("type") == CORE_TOOL_RESULT_TYPE
        and isinstance(value.get("text"), str)
    )


def make_text_tool_result(*, text: str) -> Dict[str, Any]:
    return {"type": CORE_TOOL_RESULT_TYPE, "text": text}


def openai_chat_tool_result_content(value: Any) -> Optional[List[Dict[str, Any]]]:
    try:
        converted = DEFAULT_TOOL_INTEROP_REGISTRY.convert_tool_result(
            value,
            target=ToolInteropTarget("openai.chat_completions"),
            target_formats=[OPENAI_CHAT_TOOL_RESULT_FORMAT_ID],
        )
        inspected = DEFAULT_TOOL_INTEROP_REGISTRY.inspect_result(converted)
    except ToolInteropError:
        return None
    payload = inspected.payload
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    return None


def openai_responses_tool_result_output(value: Any) -> Optional[List[Dict[str, Any]]]:
    try:
        converted = DEFAULT_TOOL_INTEROP_REGISTRY.convert_tool_result(
            value,
            target=ToolInteropTarget("openai.responses"),
            target_formats=[OPENAI_RESPONSES_TOOL_RESULT_FORMAT_ID],
        )
        inspected = DEFAULT_TOOL_INTEROP_REGISTRY.inspect_result(converted)
    except ToolInteropError:
        return None
    payload = inspected.payload
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    return None


def _chat_image_url_to_responses_image_url(value: Any) -> Any:
    if isinstance(value, dict):
        url = value.get("url")
        if isinstance(url, str) and url:
            return url
        return dict(value)
    return value if isinstance(value, str) and value else None


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
            converted = _chat_image_url_to_responses_image_url(image_url)
            if converted is not None:
                output.append({"type": "input_image", "image_url": converted})
            continue
        if part_type in {"input_text", "input_image"}:
            output.append(dict(part))
    return output


def openai_responses_output_to_chat_content(
    output: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    content: List[Dict[str, Any]] = []
    for part in output:
        part_type = part.get("type")
        if part_type in {"input_text", "output_text", "text"}:
            text = part.get("text")
            if isinstance(text, str) and text:
                content.append({"type": "text", "text": text})
            continue
        if part_type == "input_image":
            image_url = part.get("image_url")
            if isinstance(image_url, str) and image_url:
                content.append({"type": "image_url", "image_url": {"url": image_url}})
                continue
            if isinstance(image_url, dict) and image_url:
                content.append({"type": "image_url", "image_url": dict(image_url)})
            continue
        if part_type == "image_url":
            image_url = part.get("image_url")
            if isinstance(image_url, dict):
                content.append({"type": "image_url", "image_url": dict(image_url)})
            elif isinstance(image_url, str) and image_url:
                content.append({"type": "image_url", "image_url": {"url": image_url}})
    return content


def _text_from_openai_chat_content(content: Any) -> str:
    if not isinstance(content, list):
        return ""
    text_parts: List[str] = []
    for part in content:
        if not isinstance(part, dict) or part.get("type") != "text":
            continue
        text = part.get("text")
        if isinstance(text, str) and text:
            text_parts.append(text)
    return "\n".join(text_parts)


def _text_from_openai_responses_output(output: Any) -> str:
    if not isinstance(output, list):
        return ""
    text_parts: List[str] = []
    for part in output:
        if not isinstance(part, dict):
            continue
        if part.get("type") not in {"input_text", "output_text", "text"}:
            continue
        text = part.get("text")
        if isinstance(text, str) and text:
            text_parts.append(text)
    return "\n".join(text_parts)


def _anthropic_image_block_to_openai_chat_content(
    part: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    source = part.get("source")
    if not isinstance(source, dict):
        return None
    media_type = source.get("media_type")
    data = source.get("data")
    if not isinstance(media_type, str) or not media_type:
        return None
    if not isinstance(data, str) or not data:
        return None
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{media_type};base64,{data}"},
    }


def _anthropic_content_parts_to_openai_chat_content(
    content: Any,
) -> List[Dict[str, Any]]:
    parts: List[Dict[str, Any]] = []
    if isinstance(content, str):
        if content:
            parts.append({"type": "text", "text": content})
        return parts
    if not isinstance(content, list):
        return parts
    for part in content:
        if not isinstance(part, dict):
            continue
        part_type = part.get("type")
        if part_type == "text":
            text = part.get("text")
            if isinstance(text, str) and text:
                parts.append({"type": "text", "text": text})
            continue
        if part_type == "image":
            converted = _anthropic_image_block_to_openai_chat_content(part)
            if converted is not None:
                parts.append(converted)
            continue
        if part_type == "tool_result":
            parts.extend(
                _anthropic_content_parts_to_openai_chat_content(part.get("content"))
            )
    return parts


def anthropic_messages_content_to_openai_chat_content(
    content: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    payload = make_provider_native_tool_result(
        format=FORMAT_ANTHROPIC_MESSAGES,
        content=content,
    )
    return openai_chat_tool_result_content(payload) or []


def _text_from_anthropic_messages_content(content: Any) -> str:
    converted = (
        anthropic_messages_content_to_openai_chat_content(content)
        if isinstance(content, list)
        else []
    )
    text_parts: List[str] = []
    for part in converted:
        if not isinstance(part, dict) or part.get("type") != "text":
            continue
        text = part.get("text")
        if isinstance(text, str) and text:
            text_parts.append(text)
    return "\n".join(text_parts)


def _provider_native_tool_result_text(value: Dict[str, Any]) -> str:
    explicit_text = value.get("text")
    if isinstance(explicit_text, str):
        return explicit_text

    fmt = provider_native_tool_result_format(value)
    if fmt == FORMAT_OPENAI_CHAT_COMPLETIONS:
        return _text_from_openai_chat_content(value.get("content"))
    if fmt == FORMAT_ANTHROPIC_MESSAGES:
        return _text_from_anthropic_messages_content(value.get("content"))
    if fmt == FORMAT_OPENAI_RESPONSES:
        return _text_from_openai_responses_output(value.get("output"))
    return ""


def provider_native_tool_result_text(value: Any) -> str:
    if not is_provider_native_tool_result(value):
        return ""
    try:
        return DEFAULT_TOOL_INTEROP_REGISTRY.inspect_result(value).text
    except ToolInteropError:
        return ""


def provider_native_tool_result_image_content(value: Any) -> Optional[Dict[str, Any]]:
    content = openai_chat_tool_result_content(value)
    if content is None:
        return None
    for part in content:
        if not isinstance(part, dict) or part.get("type") != "image_url":
            continue
        image_url = part.get("image_url")
        if isinstance(image_url, dict) and image_url:
            return dict(image_url)
        if isinstance(image_url, str) and image_url:
            return {"url": image_url}
    return None


def provider_native_tool_result_display(
    value: Any,
    *,
    tool_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    image_content = provider_native_tool_result_image_content(value)
    if image_content is None:
        return None

    text = provider_native_tool_result_text(value)
    filename = image_content.get("filename")
    single_line = None
    if isinstance(tool_name, str) and tool_name:
        label = tool_name
        if isinstance(filename, str) and filename:
            single_line = f"{label}: {filename}"
        else:
            single_line = label

    display: Dict[str, Any] = {
        "type": "image",
        "content": image_content,
    }
    if isinstance(image_content.get("asset_ref"), dict):
        display["metadata"] = {
            "download_plugin_id": SESSION_ASSET_DOWNLOAD_PLUGIN_ID,
        }
    if isinstance(text, str) and text:
        display["content_text"] = text
        display["text_fallback"] = text
    if isinstance(single_line, str) and single_line:
        display["single_line"] = single_line
    return display


def make_provider_native_tool_result(
    *,
    format: str,
    content: Optional[List[Dict[str, Any]]] = None,
    output: Optional[List[Dict[str, Any]]] = None,
    text: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "type": PROVIDER_NATIVE_TOOL_RESULT_TYPE,
        "format": format,
    }
    if content is not None:
        payload["content"] = content
    if output is not None:
        payload["output"] = output
    if text is not None:
        payload["text"] = text
    return payload
