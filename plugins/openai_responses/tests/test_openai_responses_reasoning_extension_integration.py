from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_reasoning_extension import (
    OpenAIResponsesReasoningExtension,
)
from plugins.request_options_feature import RequestOptionsFeature


pytestmark = pytest.mark.api


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI integration tests")
    return api_key


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[OpenAIResponsesReasoningExtension],
    )
    core.register_feature(RequestOptionsFeature)
    return core


def _config(api_key: str) -> dict[str, object]:
    return {
        "model": "gpt-5-mini",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
        "reasoning_effort": "minimal",
        "reasoning_summary": "concise",
    }


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_non_streaming_reasoning_metadata_visible(
    ensure_openai_api_key: str,
) -> None:
    core = _build_core()
    session = core.create_session()
    session = core.add_message(
        session, "user", "Reply with exactly: OPENAI_REASONING_OK"
    )

    _new_session, responses = core.send_request(session, _config(ensure_openai_api_key))

    assert responses
    final = responses[-1]
    assert final.get("role") == "assistant"
    assert "OPENAI_REASONING_OK" in (final.get("content") or "")

    metadata = final.get("metadata") or {}
    reasoning = metadata.get("reasoning")
    assert isinstance(reasoning, str)
    assert reasoning.strip()

    raw_reasoning = metadata.get("openai_responses_reasoning")
    assert isinstance(raw_reasoning, dict)
    raw_items = raw_reasoning.get("items")
    assert isinstance(raw_items, list)
    assert raw_items
    assert raw_items[0].get("type") == "reasoning"


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_streaming_reasoning_metadata_visible(
    ensure_openai_api_key: str,
) -> None:
    core = _build_core()
    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: OPENAI_REASONING_STREAM_OK",
    )

    final_message = None
    for event in core.send_request_stream(session, _config(ensure_openai_api_key)):
        if event["type"] == "final":
            messages = event.get("messages") or []
            if messages:
                final_message = messages[-1]

    assert final_message is not None
    assert final_message.get("role") == "assistant"
    assert "OPENAI_REASONING_STREAM_OK" in (final_message.get("content") or "")

    metadata = final_message.get("metadata") or {}
    reasoning = metadata.get("reasoning")
    assert isinstance(reasoning, str)
    assert reasoning.strip()

    raw_reasoning = metadata.get("openai_responses_reasoning")
    assert isinstance(raw_reasoning, dict)
    raw_items = raw_reasoning.get("items")
    assert isinstance(raw_items, list)
    assert raw_items
    assert raw_items[0].get("type") == "reasoning"


class _RecordedResponsesCreateProxy:
    def __init__(self, target: Any, recorder: list[dict[str, Any]]) -> None:
        self._target = target
        self._recorder = recorder

    def create(self, **kwargs: Any) -> Any:
        self._recorder.append(dict(kwargs))
        return self._target.create(**kwargs)


class _RecordedResponsesProxy:
    def __init__(self, target: Any, recorder: list[dict[str, Any]]) -> None:
        self._target = target
        self._recorder = recorder
        streaming = getattr(target, "with_streaming_response", None)
        self.with_streaming_response = (
            _RecordedResponsesCreateProxy(streaming, recorder)
            if streaming is not None
            else None
        )

    def create(self, **kwargs: Any) -> Any:
        self._recorder.append(dict(kwargs))
        return self._target.create(**kwargs)


class _RecordedClientProxy:
    def __init__(self, target: Any, recorder: list[dict[str, Any]]) -> None:
        self._target = target
        self._recorder = recorder
        self.responses = _RecordedResponsesProxy(target.responses, recorder)
        files = getattr(target, "files", None)
        if files is not None:
            self.files = files

    def with_options(self, **kwargs: Any) -> "_RecordedClientProxy":
        return _RecordedClientProxy(self._target.with_options(**kwargs), self._recorder)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


class _RecordingApiProvider(OpenAIResponsesProvider):
    recorded_requests: list[dict[str, Any]] = []

    def _create_sdk_client_with_options(
        self,
        config: dict[str, Any],
        *,
        timeout: float,
        max_retries: int | None,
    ) -> Any:
        client = super()._create_sdk_client_with_options(
            config,
            timeout=timeout,
            max_retries=max_retries,
        )
        return _RecordedClientProxy(client, type(self).recorded_requests)


def _build_recording_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        _RecordingApiProvider,
        extensions=[OpenAIResponsesReasoningExtension],
    )
    core.register_feature(RequestOptionsFeature)
    return core


def _gpt_5_6_max_config(api_key: str) -> dict[str, object]:
    return {
        "model": "gpt-5.6-luna",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 180,
        "reasoning_effort": "max",
        "reasoning_summary": "concise",
    }


def _gpt_5_6_ultra_config(api_key: str) -> dict[str, object]:
    return {
        "model": "gpt-5.6-sol",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 240,
        "reasoning_effort": "ultra",
        "reasoning_summary": "concise",
    }


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_reasoning_effort_max_gpt_5_6_luna_real_api(
    ensure_openai_api_key: str,
) -> None:
    _RecordingApiProvider.recorded_requests = []
    core = _build_recording_core()
    config = _gpt_5_6_max_config(ensure_openai_api_key)

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly: GPT56_MAX_OK")

    final_message = None
    for event in core.send_request_stream(session, config):
        if event["type"] == "final":
            messages = event.get("messages") or []
            if messages:
                final_message = messages[-1]

    assert final_message is not None
    assert final_message.get("role") == "assistant"
    assert "GPT56_MAX_OK" in (final_message.get("content") or "")

    assert (
        _RecordingApiProvider.recorded_requests
    ), "expected at least one recorded request"
    reasoning = _RecordingApiProvider.recorded_requests[0].get("reasoning")
    assert isinstance(reasoning, dict)
    assert reasoning.get("effort") == "max"


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_reasoning_effort_ultra_gpt_5_6_sol_real_api(
    ensure_openai_api_key: str,
) -> None:
    _RecordingApiProvider.recorded_requests = []
    core = _build_recording_core()
    config = _gpt_5_6_ultra_config(ensure_openai_api_key)

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly: GPT56_ULTRA_OK")

    try:
        final_message = None
        for event in core.send_request_stream(session, config):
            if event["type"] == "final":
                messages = event.get("messages") or []
                if messages:
                    final_message = messages[-1]
    except (
        Exception
    ) as exc:  # noqa: BLE001 - capture exact API rejection for documentation
        pytest.xfail(
            f"Public OpenAI API rejected reasoning_effort=ultra for gpt-5.6-sol: "
            f"{type(exc).__name__}: {exc}"
        )

    assert final_message is not None
    assert final_message.get("role") == "assistant"
    assert "GPT56_ULTRA_OK" in (final_message.get("content") or "")

    assert (
        _RecordingApiProvider.recorded_requests
    ), "expected at least one recorded request"
    reasoning = _RecordingApiProvider.recorded_requests[0].get("reasoning")
    assert isinstance(reasoning, dict)
    assert reasoning.get("effort") == "ultra"


def _gpt_5_6_pro_mode_config(api_key: str) -> dict[str, object]:
    return {
        "model": "gpt-5.6-sol",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 240,
        "reasoning_mode": "pro",
        "reasoning_effort": "medium",
        "reasoning_summary": "concise",
    }


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_reasoning_mode_pro_gpt_5_6_sol_real_api(
    ensure_openai_api_key: str,
) -> None:
    _RecordingApiProvider.recorded_requests = []
    core = _build_recording_core()
    config = _gpt_5_6_pro_mode_config(ensure_openai_api_key)

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly: GPT56_PRO_OK")

    try:
        final_message = None
        for event in core.send_request_stream(session, config):
            if event["type"] == "final":
                messages = event.get("messages") or []
                if messages:
                    final_message = messages[-1]
    except (
        Exception
    ) as exc:  # noqa: BLE001 - capture exact API rejection for documentation
        pytest.xfail(
            f"Public OpenAI API rejected reasoning_mode=pro for gpt-5.6-sol: "
            f"{type(exc).__name__}: {exc}"
        )

    assert final_message is not None
    assert final_message.get("role") == "assistant"
    assert "GPT56_PRO_OK" in (final_message.get("content") or "")

    assert (
        _RecordingApiProvider.recorded_requests
    ), "expected at least one recorded request"
    reasoning = _RecordingApiProvider.recorded_requests[0].get("reasoning")
    assert isinstance(reasoning, dict)
    assert reasoning.get("mode") == "pro"
    assert reasoning.get("effort") == "medium"
    assert reasoning.get("summary") == "concise"
