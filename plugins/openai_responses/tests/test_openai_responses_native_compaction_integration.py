from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from openai_responses_plugins.openai_responses_native_compaction_extension import (
    OpenAIResponsesNativeCompactionExtension,
)
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider


class _SecretValue(str):
    def __repr__(self) -> str:
        return "<redacted secret>"


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI integration tests")
    return _SecretValue(api_key)


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider, [OpenAIResponsesNativeCompactionExtension]
    )
    return core


def _config(
    api_key: str,
    *,
    model: str = "gpt-5-mini",
    compaction_model: str | None = None,
) -> dict[str, object]:
    config: dict[str, object] = {
        "provider": "openai_responses",
        "model": model,
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
    }
    if compaction_model is not None:
        config["compaction_model"] = compaction_model
    return config


def _compaction_model_request_model() -> str:
    return os.getenv("OPENAI_RESPONSES_COMPACTION_REQUEST_MODEL") or "gpt-5.5"


def _compaction_model_compaction_model() -> str:
    return os.getenv("OPENAI_RESPONSES_COMPACTION_MODEL") or "gpt-5.4-mini"


def _native_history(session) -> list[dict[str, Any]]:
    native_history = (session.metadata or {}).get("native_messages")
    if not isinstance(native_history, list):
        return []
    return [item for item in native_history if isinstance(item, dict)]


def _native_history_debug(session) -> list[dict[str, Any]]:
    debug: list[dict[str, Any]] = []
    for index, item in enumerate(_native_history(session)):
        content = item.get("content")
        content_shape: Any = None
        if isinstance(content, list):
            content_shape = [
                {
                    "type": part.get("type"),
                    **(
                        {"text": part.get("text")}
                        if isinstance(part, dict) and isinstance(part.get("text"), str)
                        else {}
                    ),
                }
                for part in content
                if isinstance(part, dict)
            ]
        debug.append(
            {
                "index": index,
                "type": item.get("type"),
                "role": item.get("role"),
                "phase": item.get("phase"),
                "content": _redacted_compact_shape(content_shape),
                "has_encrypted_content": isinstance(item.get("encrypted_content"), str),
            }
        )
    return debug


def _compacted_prefix_has_assistant_message(session) -> bool:
    for item in _native_history(session):
        if item.get("type") in {"compaction", "compaction_summary"}:
            return False
        if item.get("type") == "message" and item.get("role") == "assistant":
            return True
    return False


def _assert_has_compaction_native_items(session) -> None:
    native_history = (session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert any(
        isinstance(item, dict)
        and item.get("type") in {"compaction", "compaction_summary"}
        for item in native_history
    )


def _compact_investigation_models() -> list[str]:
    raw = os.getenv("OPENAI_RESPONSES_COMPACTION_INVESTIGATION_MODELS")
    if raw:
        models = [model.strip() for model in raw.split(",") if model.strip()]
        if models:
            return models
    return ["gpt-5-mini", "gpt-5.4-mini", "gpt-5.5"]


def _redacted_compact_shape(value: Any) -> Any:
    if isinstance(value, list):
        return [_redacted_compact_shape(item) for item in value]
    if not isinstance(value, dict):
        if isinstance(value, str):
            return f"<str len={len(value)}>"
        return value

    out: dict[str, Any] = {}
    for key, item_value in value.items():
        if key in {"encrypted_content", "image_url", "file_data", "file_id"}:
            out[key] = f"<redacted {key} len={len(str(item_value))}>"
            continue
        if key == "text" and isinstance(item_value, str):
            out[key] = item_value[:240]
            if len(item_value) > 240:
                out[key] += "...<truncated>"
            continue
        if key == "content":
            out[key] = _redacted_compact_shape(item_value)
            continue
        if isinstance(item_value, (dict, list)):
            out[key] = _redacted_compact_shape(item_value)
            continue
        if isinstance(item_value, str) and len(item_value) > 240:
            out[key] = item_value[:240] + "...<truncated>"
            continue
        out[key] = item_value
    return out


def _messages_debug(messages: Any) -> list[dict[str, Any]]:
    if not isinstance(messages, list):
        return []
    debug: list[dict[str, Any]] = []
    for index, message in enumerate(messages):
        role = getattr(message, "role", None)
        content = getattr(message, "content", None)
        metadata = getattr(message, "metadata", None)
        debug.append(
            {
                "index": index,
                "role": role,
                "content": content,
                "native_indices": (
                    metadata.get("native_indices")
                    if isinstance(metadata, dict)
                    else None
                ),
            }
        )
    return debug


@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.parametrize("model", _compact_investigation_models())
def test_openai_responses_compaction_shape_matrix_allows_followup_turn(
    ensure_openai_api_key: str,
    model: str,
) -> None:
    core = _build_core()
    config = _config(ensure_openai_api_key, model=model)
    first_marker = f"COMPACTION_SHAPE_{model.replace('.', '_').replace('-', '_')}_ONE"
    second_marker = f"COMPACTION_SHAPE_{model.replace('.', '_').replace('-', '_')}_TWO"
    third_marker = f"COMPACTION_SHAPE_{model.replace('.', '_').replace('-', '_')}_THREE"

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        f"Reply with exactly {first_marker}",
        config=config,
    )
    session, first_finals = core.send_request(session, config)
    assert first_marker in first_finals[-1]["content"]

    session = core.add_message(
        session,
        "user",
        f"Reply with exactly {second_marker}",
        config=config,
    )
    session, second_finals = core.send_request(session, config)
    assert second_marker in second_finals[-1]["content"]

    compacted_session, result = core.execute_session_action(
        session,
        config,
        plugin_id="openai_responses_native_compaction",
        action_id="compact_native_history",
        params={"end_index": 2},
    )

    shape = {
        "model": model,
        "action_result": result,
        "compacted_prefix_has_assistant_message": _compacted_prefix_has_assistant_message(
            compacted_session
        ),
        "compacted_native_messages": _native_history_debug(compacted_session),
        "rebuilt_messages": _messages_debug(compacted_session.messages),
    }
    shape_json = json.dumps(shape, indent=2, sort_keys=True)
    print(f"\n[openai_responses_compaction_shape]\n{shape_json}\n")

    _assert_has_compaction_native_items(compacted_session)
    assert any(
        message.role == "user" and second_marker in message.content
        for message in compacted_session.messages
    ), shape_json
    assert any(
        message.role == "assistant" and second_marker in message.content
        for message in compacted_session.messages
    ), shape_json

    compacted_session = core.add_message(
        compacted_session,
        "user",
        f"Reply with exactly {third_marker}",
        config=config,
    )
    session_after_third, third_finals = core.send_request(compacted_session, config)

    assert third_marker in third_finals[-1]["content"]
    _assert_has_compaction_native_items(session_after_third)


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_compaction_model_allows_followup_about_compacted_assistant_content(
    ensure_openai_api_key: str,
) -> None:
    core = _build_core()
    request_model = _compaction_model_request_model()
    compaction_model = _compaction_model_compaction_model()
    config = _config(
        ensure_openai_api_key,
        model=request_model,
        compaction_model=compaction_model,
    )

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        (
            "Reply with exactly this transformed code and no other text: "
            "take ZXQ-7429 and replace the hyphen with the word PINE."
        ),
        config=config,
    )
    session, first_finals = core.send_request(session, config)
    secret_answer = str(first_finals[-1]["content"]).strip()

    assert secret_answer
    assert "PINE" in secret_answer
    assert "-" not in secret_answer

    compacted_session, result = core.execute_session_action(
        session,
        config,
        plugin_id="openai_responses_native_compaction",
        action_id="compact_native_history",
        params={},
    )

    shape = {
        "request_model": request_model,
        "compaction_model": compaction_model,
        "action_result": result,
        "compacted_prefix_has_assistant_message": _compacted_prefix_has_assistant_message(
            compacted_session
        ),
        "compacted_native_messages": _native_history_debug(compacted_session),
        "rebuilt_messages": _messages_debug(compacted_session.messages),
        "secret_answer_length": len(secret_answer),
    }
    print(
        "\n[openai_responses_compaction_model_followup_shape]\n"
        f"{json.dumps(shape, indent=2, sort_keys=True)}\n"
    )

    _assert_has_compaction_native_items(compacted_session)
    compacted_session = core.add_message(
        compacted_session,
        "user",
        "What exact transformed code did you reply with earlier? Reply only that code.",
        config=config,
    )
    session_after_followup, followup_finals = core.send_request(
        compacted_session, config
    )

    assert secret_answer in str(followup_finals[-1]["content"])
    _assert_has_compaction_native_items(session_after_followup)


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_full_compaction_allows_followup_turn(
    ensure_openai_api_key: str,
) -> None:
    core = _build_core()
    config = _config(ensure_openai_api_key)

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly FULL_COMPACTION_TURN_ONE",
        config=config,
    )
    session, first_finals = core.send_request(session, config)

    assert "FULL_COMPACTION_TURN_ONE" in first_finals[-1]["content"]

    compacted_session, result = core.execute_session_action(
        session,
        config,
        plugin_id="openai_responses_native_compaction",
        action_id="compact_native_history",
        params={},
    )

    assert result["message"] == "Compacted the full visible history."
    _assert_has_compaction_native_items(compacted_session)
    assert all(
        message.content != "Earlier conversation compacted to reduce context size."
        for message in compacted_session.messages
    )

    compacted_session = core.add_message(
        compacted_session,
        "user",
        "Reply with exactly FULL_COMPACTION_TURN_TWO",
        config=config,
    )
    session_after_second, second_finals = core.send_request(compacted_session, config)

    assert "FULL_COMPACTION_TURN_TWO" in second_finals[-1]["content"]
    _assert_has_compaction_native_items(session_after_second)
    assert all(
        message.content != "Earlier conversation compacted to reduce context size."
        for message in session_after_second.messages
    )


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_partial_compaction_allows_followup_turn(
    ensure_openai_api_key: str,
) -> None:
    core = _build_core()
    config = _config(ensure_openai_api_key)

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly PARTIAL_COMPACTION_TURN_ONE",
        config=config,
    )
    session, first_finals = core.send_request(session, config)
    assert "PARTIAL_COMPACTION_TURN_ONE" in first_finals[-1]["content"]

    session = core.add_message(
        session,
        "user",
        "Reply with exactly PARTIAL_COMPACTION_TURN_TWO",
        config=config,
    )
    session, second_finals = core.send_request(session, config)
    assert "PARTIAL_COMPACTION_TURN_TWO" in second_finals[-1]["content"]

    compacted_session, result = core.execute_session_action(
        session,
        config,
        plugin_id="openai_responses_native_compaction",
        action_id="compact_native_history",
        params={"end_index": 2},
    )

    assert result["message"] == "Compacted visible messages [:2]"
    _assert_has_compaction_native_items(compacted_session)
    assert all(
        message.content != "Earlier conversation compacted to reduce context size."
        for message in compacted_session.messages
    )
    assert any(
        message.content == "PARTIAL_COMPACTION_TURN_TWO"
        for message in compacted_session.messages
    )

    compacted_session = core.add_message(
        compacted_session,
        "user",
        "Reply with exactly PARTIAL_COMPACTION_TURN_THREE",
        config=config,
    )
    session_after_third, third_finals = core.send_request(compacted_session, config)

    assert "PARTIAL_COMPACTION_TURN_THREE" in third_finals[-1]["content"]
    _assert_has_compaction_native_items(session_after_third)
    assert all(
        message.content != "Earlier conversation compacted to reduce context size."
        for message in session_after_third.messages
    )
