from __future__ import annotations

import hashlib
from typing import Any


GUIDANCE_CONFIG_KEY = "_documentation_standard_guidance"


def _message_role(message: object) -> str | None:
    if not isinstance(message, dict):
        return None
    role = message.get("role")
    if role not in {"system", "developer"}:
        return None
    message_type = message.get("type")
    if message_type is not None and message_type != "message":
        return None
    return str(role)


def _message_text(message: object) -> str | None:
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, str):
        text = content.strip()
        return text or None
    if not isinstance(content, list):
        return None

    parts: list[str] = []
    for part in content:
        if not isinstance(part, dict):
            continue
        if part.get("type") not in {None, "input_text", "text"}:
            continue
        text = part.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    joined = "\n".join(parts).strip()
    return joined or None


def _append_distinct(parts: list[str], value: object) -> None:
    if not isinstance(value, str):
        return
    text = value.strip()
    if text and text not in parts:
        parts.append(text)


class DocumentationStandardGuidanceFeature:
    """Deliver candidate guidance after normal request compilation.

    ChatGPT account mode accepts a top-level Responses API ``instructions``
    value but rejects historical system/developer messages in the request
    input. This late suite-owned feature preserves the normal compiled agent
    instruction, appends the exact selected guidance, and strips only the
    request override's leading instruction item. Persistent native history is
    left unchanged.
    """

    name = "documentation_standard_guidance"
    version = "0.1.0"
    priority = 900

    def initialize_request(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        _ = context
        config = state.get("config")
        guidance = (
            config.get(GUIDANCE_CONFIG_KEY) if isinstance(config, dict) else None
        )
        if not isinstance(guidance, str) or not guidance.strip():
            return native_messages, state

        request = state.get("request")
        if not isinstance(request, dict):
            return native_messages, state

        raw_messages = request.get("messages")
        request_messages = (
            raw_messages if isinstance(raw_messages, list) else native_messages
        )
        leading_text = None
        stripped_messages = list(request_messages)
        if stripped_messages and _message_role(stripped_messages[0]) is not None:
            leading_text = _message_text(stripped_messages[0])
            stripped_messages = stripped_messages[1:]

        payload = request.get("payload")
        payload_value = dict(payload) if isinstance(payload, dict) else {}

        instruction_parts: list[str] = []
        _append_distinct(instruction_parts, request.get("instructions"))
        _append_distinct(instruction_parts, payload_value.pop("instructions", None))
        _append_distinct(instruction_parts, leading_text)
        _append_distinct(instruction_parts, guidance)
        combined = "\n\n".join(instruction_parts)

        new_request = {
            **request,
            "payload": payload_value,
            "messages": stripped_messages,
            "instructions": combined,
        }
        injection = {
            "strategy": "late_feature_endpoint_instructions",
            "guidance_sha256": hashlib.sha256(guidance.encode("utf-8")).hexdigest(),
            "combined_sha256": hashlib.sha256(combined.encode("utf-8")).hexdigest(),
            "leading_instruction_preserved": leading_text is not None,
            "request_message_stripped": len(stripped_messages) != len(request_messages),
        }
        return native_messages, {
            **state,
            "request": new_request,
            "_documentation_standard_guidance_injection": injection,
        }