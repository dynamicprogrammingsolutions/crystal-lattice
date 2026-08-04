from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from openai import AsyncOpenAI, OpenAI


DEFAULT_API_BASE_URL = "https://api.openai.com/v1"
DEFAULT_CHATGPT_BASE_URL = "https://chatgpt.com/backend-api/codex"
DEFAULT_TIMEOUT = 60.0


@dataclass(frozen=True)
class PreparedResponsesInput:
    input_items: list[Dict[str, Any]]
    instructions: Optional[str]
    stripped_leading_message: Optional[Dict[str, Any]] = None


def normalize_auth_mode(raw: Any) -> str:
    if not isinstance(raw, str):
        return "api"
    normalized = raw.strip().lower()
    if normalized == "api_key":
        return "api"
    if normalized in {"api", "chatgpt", "auto"}:
        return normalized
    return "api"


def effective_auth_mode(config: Dict[str, Any]) -> str:
    raw = config.get("_openai_responses_effective_auth_mode")
    if isinstance(raw, str) and raw.strip().lower() in {"api", "chatgpt"}:
        return raw.strip().lower()
    requested = normalize_auth_mode(config.get("auth_mode"))
    return "chatgpt" if requested == "chatgpt" else "api"


def resolve_api_key(config: Dict[str, Any]) -> str:
    mode = effective_auth_mode(config)
    if mode == "chatgpt":
        access_token = config.get("chatgpt_access_token")
        if isinstance(access_token, str) and access_token.strip():
            return access_token.strip()
        raise ValueError(
            "[openai_responses_provider] chatgpt auth_mode requires a valid saved ChatGPT login"
        )

    api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
    if not isinstance(api_key, str) or not api_key.strip():
        requested_mode = normalize_auth_mode(config.get("auth_mode"))
        if requested_mode == "auto":
            raise ValueError(
                "[openai_responses_provider] auto auth_mode requires either a saved ChatGPT login or config.api_key / OPENAI_API_KEY"
            )
        raise ValueError(
            "[openai_responses_provider] api_key is required (config.api_key or OPENAI_API_KEY)"
        )
    return api_key.strip()


def resolve_base_url(config: Dict[str, Any]) -> str:
    mode = effective_auth_mode(config)
    if mode == "chatgpt":
        base_url = (
            config.get("chatgpt_base_url")
            or config.get("base_url")
            or DEFAULT_CHATGPT_BASE_URL
        )
    else:
        base_url = (
            config.get("api_base_url") or config.get("base_url") or DEFAULT_API_BASE_URL
        )
    if not isinstance(base_url, str) or not base_url.strip():
        raise ValueError(
            "[openai_responses_provider] base_url must be a non-empty string"
        )
    return base_url.rstrip("/")


def chatgpt_default_headers(config: Dict[str, Any]) -> Dict[str, str]:
    if effective_auth_mode(config) != "chatgpt":
        return {}
    account_id = config.get("chatgpt_account_id")
    if isinstance(account_id, str) and account_id.strip():
        return {"ChatGPT-Account-Id": account_id.strip()}
    return {}


def authorization_header_value(config: Dict[str, Any], token: str) -> str:
    if effective_auth_mode(config) == "chatgpt":
        token_type = config.get("chatgpt_token_type")
        if isinstance(token_type, str) and token_type.strip():
            normalized = token_type.strip()
            if normalized.lower() == "bearer":
                normalized = "Bearer"
            return f"{normalized} {token}"
    return f"Bearer {token}"


def build_openai_sdk_client(
    config: Dict[str, Any],
    *,
    timeout: float,
    max_retries: Optional[int] = None,
) -> OpenAI:
    kwargs: Dict[str, Any] = {
        "api_key": resolve_api_key(config),
        "base_url": resolve_base_url(config),
        "timeout": timeout,
    }
    default_headers = chatgpt_default_headers(config)
    if default_headers:
        kwargs["default_headers"] = default_headers
    if max_retries is not None:
        kwargs["max_retries"] = max_retries
    return OpenAI(**kwargs)


def build_async_openai_sdk_client(
    config: Dict[str, Any],
    *,
    timeout: float,
    max_retries: Optional[int] = None,
) -> AsyncOpenAI:
    kwargs: Dict[str, Any] = {
        "api_key": resolve_api_key(config),
        "base_url": resolve_base_url(config),
        "timeout": timeout,
    }
    default_headers = chatgpt_default_headers(config)
    if default_headers:
        kwargs["default_headers"] = default_headers
    if max_retries is not None:
        kwargs["max_retries"] = max_retries
    return AsyncOpenAI(**kwargs)


def should_strip_leading_system_or_developer_message(
    config: Dict[str, Any],
) -> bool:
    return bool(config.get("strip_leading_system_or_developer_message", False))


def strip_leading_system_or_developer_message(
    native_messages: list[Dict[str, Any]],
) -> list[Dict[str, Any]]:
    if not native_messages:
        return native_messages
    first = native_messages[0]
    if not isinstance(first, dict):
        return native_messages
    item_type = first.get("type")
    if isinstance(item_type, str) and item_type and item_type != "message":
        return native_messages
    role = first.get("role")
    if role not in {"system", "developer"}:
        return native_messages
    return list(native_messages[1:])


def is_system_or_developer_message(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    item_type = item.get("type")
    if isinstance(item_type, str) and item_type and item_type != "message":
        return False
    return item.get("role") in {"system", "developer"}


def leading_system_or_developer_message_text(
    native_messages: list[Dict[str, Any]],
) -> Optional[str]:
    if not native_messages:
        return None
    first = native_messages[0]
    if not is_system_or_developer_message(first):
        return None

    content = first.get("content")
    if isinstance(content, str):
        text = content.strip()
        return text or None

    if not isinstance(content, list):
        return None

    parts: list[str] = []
    for part in content:
        if not isinstance(part, dict):
            continue
        if part.get("type") not in {"input_text", "output_text", "text"}:
            continue
        text = part.get("text")
        if isinstance(text, str) and text:
            parts.append(text)

    joined = "\n".join(parts).strip()
    return joined or None


def prepare_input_and_instructions_for_endpoint(
    native_messages: list[Dict[str, Any]],
    instructions: Optional[str],
    config: Dict[str, Any],
) -> PreparedResponsesInput:
    if should_strip_leading_system_or_developer_message(config):
        return PreparedResponsesInput(
            input_items=strip_leading_system_or_developer_message(native_messages),
            instructions=instructions,
        )

    if effective_auth_mode(config) != "chatgpt" or instructions is not None:
        return PreparedResponsesInput(
            input_items=native_messages,
            instructions=instructions,
        )

    leading_text = leading_system_or_developer_message_text(native_messages)
    if leading_text is None:
        return PreparedResponsesInput(
            input_items=native_messages,
            instructions=instructions,
        )

    return PreparedResponsesInput(
        input_items=list(native_messages[1:]),
        instructions=leading_text,
        stripped_leading_message=dict(native_messages[0]),
    )
