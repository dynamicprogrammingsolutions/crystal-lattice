from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore

from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_websearch_extension import (
    OpenAIResponsesWebSearchExtension,
)


class _ScriptedResponse:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self, mode: str = "python") -> Dict[str, Any]:
        _ = mode
        return self._payload


class _ScriptedResponsesResource:
    def __init__(self, payloads: List[Dict[str, Any]]) -> None:
        self._payloads = list(payloads)
        self.calls: List[Dict[str, Any]] = []
        self._cursor = 0

    def create(self, **kwargs: Any) -> _ScriptedResponse:
        self.calls.append(kwargs)
        if self._cursor >= len(self._payloads):
            raise RuntimeError("no scripted response remaining")
        payload = self._payloads[self._cursor]
        self._cursor += 1
        return _ScriptedResponse(payload)


class _ScriptedClient:
    def __init__(self, payloads: List[Dict[str, Any]]) -> None:
        self.responses = _ScriptedResponsesResource(payloads)


class _ScriptedWebSearchProvider(OpenAIResponsesProvider):
    scripted_payloads: List[Dict[str, Any]] = []
    last_client: _ScriptedClient | None = None

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        state = super().init(config)
        if type(self).last_client is None:
            type(self).last_client = _ScriptedClient(list(type(self).scripted_payloads))
        state["client"] = type(self).last_client
        return state


def _load_openai_env() -> None:
    worktree_root = Path(__file__).resolve().parents[3]
    repo_root = Path(__file__).resolve().parents[5]
    load_dotenv(repo_root / ".env")
    if repo_root != worktree_root:
        load_dotenv(worktree_root / ".env")


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    _load_openai_env()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI web search integration tests")
    return api_key


def _config(*, include_full_sources: bool = False) -> Dict[str, Any]:
    return {
        "model": "gpt-5-mini",
        "api_key": "test_key",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30,
        "provider": "openai_responses",
        "enable_web_search": True,
        "include_full_web_search_sources": include_full_sources,
    }


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(_ScriptedWebSearchProvider, extensions=[OpenAIResponsesWebSearchExtension])
    return core


def _build_live_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(OpenAIResponsesProvider, extensions=[OpenAIResponsesWebSearchExtension])
    return core


def test_provider_surfaces_citations_and_sources_on_canonical_assistant_message() -> None:
    provider = OpenAIResponsesProvider()
    native_messages = [
        {
            "type": "web_search_call",
            "action": {
                "sources": [
                    {"url": "https://example.com/a", "title": "Example A"},
                    {"url": "https://example.com/a", "title": "Example A"},
                    {"url": "https://example.com/b", "title": "Example B", "snippet": "Consulted"},
                ]
            },
            "_metadata": {"response_id": "resp_1"},
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "output_text",
                    "text": "Answer with citations.",
                    "annotations": [
                        {
                            "type": "url_citation",
                            "url": "https://example.com/a",
                            "title": "Example A",
                            "start_index": 0,
                            "end_index": 6,
                        },
                        {
                            "type": "url_citation",
                            "url_citation": {
                                "url": "https://example.com/b",
                                "title": "Example B",
                                "start_index": 7,
                                "end_index": 16,
                            },
                        },
                    ],
                }
            ],
            "_metadata": {"response_id": "resp_1"},
        },
    ]

    messages = provider.from_native_messages(native_messages, {})

    assert len(messages) == 1
    assistant = messages[0]
    metadata = assistant.get("metadata") or {}
    assert assistant["role"] == "assistant"
    assert assistant["content"] == "Answer with citations."
    assert metadata["url_citations"] == [
        {
            "url": "https://example.com/a",
            "title": "Example A",
            "start_index": 0,
            "end_index": 6,
        },
        {
            "url": "https://example.com/b",
            "title": "Example B",
            "start_index": 7,
            "end_index": 16,
        },
    ]
    assert metadata["web_search_sources"] == [
        {"url": "https://example.com/a", "title": "Example A"},
        {"url": "https://example.com/b", "title": "Example B", "snippet": "Consulted"},
    ]


def test_provider_omits_web_search_metadata_for_non_web_search_segments() -> None:
    provider = OpenAIResponsesProvider()
    native_messages = [
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Plain answer."}],
            "_metadata": {"response_id": "resp_plain"},
        }
    ]

    messages = provider.from_native_messages(native_messages, {})

    metadata = messages[0].get("metadata") or {}
    assert "url_citations" not in metadata
    assert "web_search_sources" not in metadata


def test_multi_turn_follow_up_preserves_native_web_search_history() -> None:
    _ScriptedWebSearchProvider.last_client = None
    _ScriptedWebSearchProvider.scripted_payloads = [
        {
            "id": "resp_search_1",
            "output": [
                {
                    "type": "web_search_call",
                    "action": {
                        "sources": [
                            {"url": "https://example.com/a", "title": "Example A"},
                            {"url": "https://example.com/b", "title": "Example B"},
                        ]
                    },
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "First answer.",
                            "annotations": [
                                {
                                    "type": "url_citation",
                                    "url": "https://example.com/a",
                                    "title": "Example A",
                                    "start_index": 0,
                                    "end_index": 5,
                                }
                            ],
                        }
                    ],
                },
            ],
        },
        {
            "id": "resp_search_2",
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Follow-up answer."}],
                }
            ],
        },
    ]

    core = _build_core()
    config = _config(include_full_sources=True)

    session = core.create_session()
    session = core.add_message(session, "user", "Search for something.", config=config)
    session, first_responses = core.send_request(session, config)

    first_assistant = first_responses[-1]
    first_metadata = first_assistant.get("metadata") or {}
    assert first_metadata["url_citations"][0]["url"] == "https://example.com/a"
    assert len(first_metadata["web_search_sources"]) == 2

    session = core.add_message(session, "user", "Follow up.", config=config)
    _session_after_follow_up, second_responses = core.send_request(session, config)

    assert second_responses[-1]["content"] == "Follow-up answer."

    client = _ScriptedWebSearchProvider.last_client
    assert client is not None
    assert len(client.responses.calls) == 2

    first_payload = client.responses.calls[0]
    assert first_payload["tools"] == [{"type": "web_search"}]
    assert first_payload["include"] == ["web_search_call.action.sources"]

    second_input = client.responses.calls[1]["input"]
    assert any(
        isinstance(item, dict)
        and item.get("type") == "web_search_call"
        and isinstance(item.get("action"), dict)
        and isinstance(item["action"].get("sources"), list)
        for item in second_input
    )


@pytest.mark.integration
@pytest.mark.openai
def test_openai_websearch_non_streaming_real_api_with_full_sources(
    ensure_openai_api_key: str,
) -> None:
    core = _build_live_core()
    config = {
        "model": "gpt-5-mini",
        "api_key": ensure_openai_api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 180,
        "enable_web_search": True,
        "include_full_web_search_sources": True,
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        (
            "Use web search to find one recent news item about OpenAI from the last 30 days. "
            "Respond in one short paragraph and rely on at least one cited web source."
        ),
        config=config,
    )

    session, responses = core.send_request(session, config)

    assert responses
    assistant = responses[-1]
    assert assistant.get("role") == "assistant"
    assert isinstance(assistant.get("content"), str) and assistant["content"].strip()

    metadata = assistant.get("metadata") or {}
    citations = metadata.get("url_citations")
    sources = metadata.get("web_search_sources")

    assert isinstance(citations, list) and citations
    assert all(isinstance(item, dict) and isinstance(item.get("url"), str) for item in citations)
    assert isinstance(sources, list) and sources
    assert all(isinstance(item, dict) and isinstance(item.get("url"), str) for item in sources)

    native_history = (session.metadata or {}).get("native_messages") or []
    assert any(
        isinstance(item, dict) and item.get("type") == "web_search_call"
        for item in native_history
    )


@pytest.mark.integration
@pytest.mark.openai
def test_openai_websearch_streaming_real_api_default_sources_disabled(
    ensure_openai_api_key: str,
) -> None:
    core = _build_live_core()
    config = {
        "model": "gpt-5-mini",
        "api_key": ensure_openai_api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 180,
        "enable_web_search": True,
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        (
            "Use web search to find a recent OpenAI-related article and summarize it in one sentence. "
            "Include enough detail that a citation is appropriate."
        ),
        config=config,
    )

    partial_count = 0
    final_session = None
    final_message = None

    for event in core.send_request_stream(session, config):
        if event["type"] == "partial":
            content = (event.get("message") or {}).get("content")
            if isinstance(content, str) and content:
                partial_count += 1
        elif event["type"] == "final":
            final_session = event.get("session")
            messages = event.get("messages") or []
            if messages:
                final_message = messages[-1]

    assert partial_count > 0
    assert final_session is not None
    assert final_message is not None
    assert final_message.get("role") == "assistant"
    assert isinstance(final_message.get("content"), str) and final_message["content"].strip()

    metadata = final_message.get("metadata") or {}
    citations = metadata.get("url_citations")
    assert isinstance(citations, list) and citations
    assert all(isinstance(item, dict) and isinstance(item.get("url"), str) for item in citations)
    assert "web_search_sources" not in metadata

    native_history = (final_session.metadata or {}).get("native_messages") or []
    assert any(
        isinstance(item, dict) and item.get("type") == "web_search_call"
        for item in native_history
    )