from __future__ import annotations

from typing import Any, Dict, List

import pytest

from agent_core import AgentCore, Message, Session
from feature_system_message.system_message_feature import SystemMessageFeature

from openai_responses_plugins.openai_responses_native_compaction_extension import (
    OpenAIResponsesNativeCompactionExtension,
)
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider


class _ScriptedResponse:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self, mode: str = "python") -> Dict[str, Any]:
        _ = mode
        return self._payload


class _ScriptedResponsesResource:
    def __init__(
        self,
        create_payloads: List[Dict[str, Any]],
        compact_payload: Dict[str, Any],
    ) -> None:
        self._create_payloads = list(create_payloads)
        self._compact_payload = compact_payload
        self.create_calls: List[Dict[str, Any]] = []
        self.compact_calls: List[Dict[str, Any]] = []
        self._create_cursor = 0

    def create(self, **kwargs: Any) -> _ScriptedResponse:
        self.create_calls.append(kwargs)
        if self._create_cursor >= len(self._create_payloads):
            raise RuntimeError("no scripted create payload remaining")
        payload = self._create_payloads[self._create_cursor]
        self._create_cursor += 1
        return _ScriptedResponse(payload)

    def compact(self, **kwargs: Any) -> _ScriptedResponse:
        self.compact_calls.append(kwargs)
        return _ScriptedResponse(self._compact_payload)


class _ScriptedClient:
    def __init__(
        self,
        create_payloads: List[Dict[str, Any]],
        compact_payload: Dict[str, Any],
    ) -> None:
        self.responses = _ScriptedResponsesResource(create_payloads, compact_payload)


class _ScriptedCompactionProvider(OpenAIResponsesProvider):
    scripted_client: _ScriptedClient | None = None

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        state = super().init(config)
        if type(self).scripted_client is None:
            raise RuntimeError("scripted_client must be configured before init")
        state["client"] = type(self).scripted_client
        return state


def _config() -> Dict[str, Any]:
    return {
        "provider": "openai_responses",
        "model": "gpt-5-mini",
        "api_key": "test_key",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30,
    }


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        _ScriptedCompactionProvider,
        [OpenAIResponsesNativeCompactionExtension],
    )
    return core


def _patch_extension_client(
    monkeypatch: pytest.MonkeyPatch,
    captured: Dict[str, Any] | None = None,
) -> None:
    def _fake_build_client(
        self: OpenAIResponsesNativeCompactionExtension,
        config: Dict[str, Any],
    ) -> _ScriptedClient:
        _ = self
        if captured is not None:
            captured["config"] = dict(config)
        client = _ScriptedCompactionProvider.scripted_client
        if client is None:
            raise RuntimeError("scripted_client must be configured before use")
        return client

    monkeypatch.setattr(
        OpenAIResponsesNativeCompactionExtension,
        "_build_client",
        _fake_build_client,
    )


def test_compaction_action_uses_sdk_and_sanitizes_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ScriptedCompactionProvider.scripted_client = _ScriptedClient(
        create_payloads=[],
        compact_payload={
            "id": "cmp_1",
            "created_at": 1,
            "object": "response.compaction",
            "output": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "hello"}],
                },
                {
                    "id": "comp_1",
                    "type": "compaction",
                    "encrypted_content": "opaque",
                    "created_by": "openai",
                },
            ],
            "usage": {"total_tokens": 10},
        },
    )
    _patch_extension_client(monkeypatch)

    extension = OpenAIResponsesNativeCompactionExtension()
    session = Session(
        session_id="session-1",
        messages=[
            Message(
                role="assistant",
                content="hello",
                metadata={"native_indices": [0]},
            )
        ],
    )
    state = {
        "config": _config(),
        "request": {"instructions": "Compiled system instructions"},
        "client": _ScriptedCompactionProvider.scripted_client,
    }
    native_messages = [
        {
            "type": "message",
            "role": "assistant",
            "id": "msg_1",
            "status": "completed",
            "content": [{"type": "output_text", "text": "hello"}],
            "_metadata": {"response_id": "resp_1"},
        }
    ]

    result = extension.execute_action(
        "compact_native_history",
        session=session,
        native_messages=native_messages,
        params={},
        state=state,
    )

    assert result["message"] == "Compacted the full visible history."

    calls = _ScriptedCompactionProvider.scripted_client.responses.compact_calls
    assert len(calls) == 1
    assert calls[0]["model"] == "gpt-5-mini"
    assert calls[0]["instructions"] == "Compiled system instructions"
    assert calls[0]["timeout"] == 30.0
    assert calls[0]["input"] == [
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "hello"}],
        }
    ]


def test_core_session_action_rebuilds_to_compaction_placeholder_and_keeps_future_turns_working(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ScriptedCompactionProvider.scripted_client = _ScriptedClient(
        create_payloads=[
            {
                "id": "resp_1",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "First answer"}],
                    }
                ],
            },
            {
                "id": "resp_2",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "Second answer"}],
                    }
                ],
            },
        ],
        compact_payload={
            "id": "cmp_2",
            "created_at": 2,
            "object": "response.compaction",
            "output": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "first turn"}],
                },
                {
                    "id": "comp_2",
                    "type": "compaction",
                    "encrypted_content": "opaque-compacted",
                    "created_by": "openai",
                },
            ],
            "usage": {"total_tokens": 12},
        },
    )
    _patch_extension_client(monkeypatch)

    core = _build_core()
    config = _config()

    session = core.create_session()
    session = core.add_message(session, "user", "first turn", config=config)
    session, first_finals = core.send_request(session, config)
    assert first_finals[-1]["content"] == "First answer"

    compacted_session, result = core.execute_session_action(
        session,
        config,
        plugin_id="openai_responses_native_compaction",
        action_id="compact_native_history",
        params={},
    )

    assert result["message"] == "Compacted the full visible history."
    assert [message.content for message in compacted_session.messages] == [
        "Earlier conversation compacted to reduce context size.",
    ]
    placeholder_metadata = compacted_session.messages[0].metadata or {}
    assert placeholder_metadata["native_indices"] == [0, 1]
    assert "openai_responses_compaction" in placeholder_metadata
    compacted_native = (compacted_session.metadata or {}).get("native_messages")
    assert isinstance(compacted_native, list)
    assert compacted_native[-1]["type"] == "compaction"

    compacted_session = core.add_message(compacted_session, "user", "second turn", config=config)
    session_after_second, second_finals = core.send_request(compacted_session, config)

    assert second_finals[-1]["content"] == "Second answer"
    assert [message.content for message in session_after_second.messages] == [
        "Earlier conversation compacted to reduce context size.",
        "second turn",
        "Second answer",
    ]
    create_calls = _ScriptedCompactionProvider.scripted_client.responses.create_calls
    assert len(create_calls) == 2
    second_input = create_calls[1]["input"]
    assert any(item.get("type") == "compaction" for item in second_input if isinstance(item, dict))
    assert all(
        item.get("content") != "Earlier conversation compacted to reduce context size."
        for item in second_input
        if isinstance(item, dict)
    )


def test_core_session_action_compacts_only_visible_prefix_slice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ScriptedCompactionProvider.scripted_client = _ScriptedClient(
        create_payloads=[
            {
                "id": "resp_1",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "First answer"}],
                    }
                ],
            },
            {
                "id": "resp_2",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "Second answer"}],
                    }
                ],
            },
            {
                "id": "resp_3",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "Third answer"}],
                    }
                ],
            },
        ],
        compact_payload={
            "id": "cmp_3",
            "created_at": 3,
            "object": "response.compaction",
            "output": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "first turn"}],
                },
                {
                    "id": "comp_3",
                    "type": "compaction",
                    "encrypted_content": "opaque-prefix",
                    "created_by": "openai",
                },
            ],
            "usage": {"total_tokens": 20},
        },
    )
    _patch_extension_client(monkeypatch)

    core = _build_core()
    config = _config()

    session = core.create_session()
    session = core.add_message(session, "user", "first turn", config=config)
    session, _ = core.send_request(session, config)
    session = core.add_message(session, "user", "second turn", config=config)
    session, _ = core.send_request(session, config)

    compacted_session, result = core.execute_session_action(
        session,
        config,
        plugin_id="openai_responses_native_compaction",
        action_id="compact_native_history",
        params={"end_index": 2},
    )

    assert result["message"] == "Compacted visible messages [:2]"
    assert [message.content for message in compacted_session.messages] == [
        "Earlier conversation compacted to reduce context size.",
        "second turn",
        "Second answer",
    ]

    compacted_session = core.add_message(compacted_session, "user", "third turn", config=config)
    session_after_third, third_finals = core.send_request(compacted_session, config)

    assert third_finals[-1]["content"] == "Third answer"
    assert [message.content for message in session_after_third.messages] == [
        "Earlier conversation compacted to reduce context size.",
        "second turn",
        "Second answer",
        "third turn",
        "Third answer",
    ]

    compact_calls = _ScriptedCompactionProvider.scripted_client.responses.compact_calls
    assert len(compact_calls) == 1
    assert compact_calls[0]["input"] == [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "first turn"}],
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "First answer"}],
        },
    ]

    create_calls = _ScriptedCompactionProvider.scripted_client.responses.create_calls
    assert len(create_calls) == 3
    third_input = create_calls[2]["input"]
    assert any(item.get("type") == "compaction" for item in third_input if isinstance(item, dict))
    assert any(
        item.get("type") == "message"
        and item.get("role") == "user"
        and item.get("content") == [{"type": "input_text", "text": "second turn"}]
        for item in third_input
        if isinstance(item, dict)
    )


def test_compaction_uses_chatgpt_effective_endpoint_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ScriptedCompactionProvider.scripted_client = _ScriptedClient(
        create_payloads=[],
        compact_payload={
            "id": "cmp_chatgpt",
            "output": [{"type": "compaction", "encrypted_content": "opaque"}],
        },
    )
    captured: Dict[str, Any] = {}
    _patch_extension_client(monkeypatch, captured)

    extension = OpenAIResponsesNativeCompactionExtension()
    session = Session(
        session_id="session-chatgpt",
        messages=[Message(role="assistant", content="hello", metadata={"native_indices": [0]})],
    )
    native_messages = [
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "hello"}],
        }
    ]
    state = {
        "config": {
            **_config(),
            "auth_mode": "auto",
            "_openai_responses_effective_auth_mode": "chatgpt",
            "base_url": "https://chatgpt.com/backend-api/codex",
            "api_base_url": "https://api.openai.com/v1",
            "chatgpt_base_url": "https://chatgpt.com/backend-api/codex",
            "chatgpt_access_token": "chatgpt_token",
            "chatgpt_account_id": "acct_123",
        }
    }

    extension.execute_action(
        "compact_native_history",
        session=session,
        native_messages=native_messages,
        params={},
        state=state,
    )

    assert captured["config"]["_openai_responses_effective_auth_mode"] == "chatgpt"
    assert captured["config"]["base_url"] == "https://chatgpt.com/backend-api/codex"
    assert captured["config"]["chatgpt_access_token"] == "chatgpt_token"


def test_compaction_can_force_api_endpoint_when_chatgpt_compaction_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ScriptedCompactionProvider.scripted_client = _ScriptedClient(
        create_payloads=[],
        compact_payload={
            "id": "cmp_api",
            "output": [{"type": "compaction", "encrypted_content": "opaque"}],
        },
    )
    captured: Dict[str, Any] = {}
    _patch_extension_client(monkeypatch, captured)

    extension = OpenAIResponsesNativeCompactionExtension()
    session = Session(
        session_id="session-api",
        messages=[Message(role="assistant", content="hello", metadata={"native_indices": [0]})],
    )
    native_messages = [
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "hello"}],
        }
    ]
    state = {
        "config": {
            **_config(),
            "auth_mode": "chatgpt",
            "_openai_responses_effective_auth_mode": "chatgpt",
            "base_url": "https://chatgpt.com/backend-api/codex",
            "api_base_url": "https://api.openai.com/v1",
            "chatgpt_base_url": "https://chatgpt.com/backend-api/codex",
            "chatgpt_access_token": "chatgpt_token",
            "use_chatgpt_auth_for_compaction": False,
        }
    }

    extension.execute_action(
        "compact_native_history",
        session=session,
        native_messages=native_messages,
        params={},
        state=state,
    )

    assert captured["config"]["_openai_responses_effective_auth_mode"] == "api"
    assert captured["config"]["base_url"] == "https://api.openai.com/v1"
    assert "chatgpt_access_token" not in captured["config"]


def test_core_session_action_uses_compiled_request_instructions_and_strips_leading_system(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ScriptedCompactionProvider.scripted_client = _ScriptedClient(
        create_payloads=[],
        compact_payload={
            "id": "cmp_strip",
            "output": [{"id": "comp_strip", "type": "compaction", "encrypted_content": "opaque"}],
        },
    )
    _patch_extension_client(monkeypatch)

    core = AgentCore()
    core.register_provider(
        _ScriptedCompactionProvider,
        [OpenAIResponsesNativeCompactionExtension],
    )
    core.register_feature(SystemMessageFeature)

    config = {
        **_config(),
        "system_message_as_instructions": True,
        "strip_leading_system_or_developer_message": True,
        "system_message": "Configured instructions",
    }
    session = Session(
        session_id="session-strip",
        messages=[
            Message(role="system", content="Old persisted system", metadata={"native_indices": [0]}),
            Message(role="user", content="hello", metadata={"native_indices": [1]}),
            Message(role="assistant", content="world", metadata={"native_indices": [2]}),
        ],
        metadata={
            "native_messages": [
                {
                    "type": "message",
                    "role": "system",
                    "content": [{"type": "input_text", "text": "Old persisted system"}],
                },
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "hello"}],
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "world"}],
                },
            ],
            "native_messages_integrity": core._compute_native_integrity(  # type: ignore[attr-defined]
                [
                    Message(role="system", content="Old persisted system", metadata={"native_indices": [0]}),
                    Message(role="user", content="hello", metadata={"native_indices": [1]}),
                    Message(role="assistant", content="world", metadata={"native_indices": [2]}),
                ]
            ),
        },
    )

    core.execute_session_action(
        session,
        config,
        plugin_id="openai_responses_native_compaction",
        action_id="compact_native_history",
        params={},
    )

    calls = _ScriptedCompactionProvider.scripted_client.responses.compact_calls
    assert len(calls) == 1
    assert calls[0]["instructions"] == "Old persisted system"
    assert calls[0]["input"] == [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "hello"}],
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "world"}],
        },
    ]


def test_compaction_disabled_chatgpt_mode_requires_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    extension = OpenAIResponsesNativeCompactionExtension()
    session = Session(
        session_id="session-error",
        messages=[Message(role="assistant", content="hello", metadata={"native_indices": [0]})],
    )
    native_messages = [
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "hello"}],
        }
    ]
    state = {
        "config": {
            "provider": "openai_responses",
            "model": "gpt-5-mini",
            "auth_mode": "chatgpt",
            "_openai_responses_effective_auth_mode": "chatgpt",
            "api_base_url": "https://api.openai.com/v1",
            "chatgpt_base_url": "https://chatgpt.com/backend-api/codex",
            "chatgpt_access_token": "chatgpt_token",
            "use_chatgpt_auth_for_compaction": False,
        }
    }

    with pytest.raises(RuntimeError) as excinfo:
        extension.execute_action(
            "compact_native_history",
            session=session,
            native_messages=native_messages,
            params={},
            state=state,
        )

    assert "use the API endpoint" in str(excinfo.value)
    assert "re-enable use_chatgpt_auth_for_compaction" in str(excinfo.value)