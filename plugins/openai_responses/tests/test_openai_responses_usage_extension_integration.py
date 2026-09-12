from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from openai_response_mutation_probe import (
    ProbeMutationResult,
    detect_probe_markers_in_json,
    format_probe_detections,
    mutate_response_objects,
)
from openai_responses_plugins.openai_responses_flex_processing_extension import (
    OpenAIResponsesFlexProcessingExtension,
)
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_tools_extension import (
    OpenAIResponsesToolsExtension,
)
from openai_responses_plugins.openai_responses_usage_extension import (
    OpenAIResponsesUsageExtension,
)
from plugins.math_tools import MathTools


pytestmark = pytest.mark.api
_PROBE_SEED = 20260912


class _RedactedApiKey(str):
    def __repr__(self) -> str:
        return "<redacted OpenAI API key>"


class _MutatingResponseProxy:
    def __init__(self, target: Any, recorder: list[ProbeMutationResult]) -> None:
        self._target = target
        self._recorder = recorder

    def model_dump(self, mode: str = "python") -> dict[str, Any]:
        payload = self._target.model_dump(mode=mode)
        if not isinstance(payload, dict):
            raise AssertionError(
                "OpenAI response model_dump did not return a dictionary"
            )
        mutation = mutate_response_objects(
            payload,
            seed=_PROBE_SEED + len(self._recorder),
        )
        self._recorder.append(mutation)
        return mutation.payload

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


class _MutatingResponsesProxy:
    def __init__(self, target: Any, recorder: list[ProbeMutationResult]) -> None:
        self._target = target
        self._recorder = recorder

    def create(self, **kwargs: Any) -> Any:
        response = self._target.create(**kwargs)
        if kwargs.get("stream") is True:
            return response
        return _MutatingResponseProxy(response, self._recorder)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


class _MutatingClientProxy:
    def __init__(self, target: Any, recorder: list[ProbeMutationResult]) -> None:
        self._target = target
        self._recorder = recorder
        self.responses = _MutatingResponsesProxy(target.responses, recorder)

    def with_options(self, **kwargs: Any) -> "_MutatingClientProxy":
        return _MutatingClientProxy(
            self._target.with_options(**kwargs),
            self._recorder,
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


class _MutatingOpenAIResponsesProvider(OpenAIResponsesProvider):
    probe_mutations: list[ProbeMutationResult] = []

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
        return _MutatingClientProxy(client, type(self).probe_mutations)


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI usage integration tests")
    return _RedactedApiKey(api_key)


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_nonstreaming_usage_metadata_real_api(
    ensure_openai_api_key: str,
) -> None:
    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[OpenAIResponsesUsageExtension],
    )

    config = {
        "model": "gpt-5-mini",
        "api_key": ensure_openai_api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly: OPENAI_USAGE_OK")

    new_session, responses = core.send_request(session, config)

    assert new_session is not None
    assert responses

    final = responses[-1]
    assert final.get("role") == "assistant"
    assert "OPENAI_USAGE_OK" in str(final.get("content"))

    metadata = final.get("metadata") or {}
    usage = metadata.get("usage")

    assert isinstance(usage, dict)
    assert "attribution" not in usage
    assert set(usage) == {
        "input_tokens",
        "input_tokens_details",
        "output_tokens",
        "output_tokens_details",
        "total_tokens",
    }
    assert set(usage["input_tokens_details"]) <= {
        "cached_tokens",
        "cache_write_tokens",
    }
    assert "cached_tokens" in usage["input_tokens_details"]
    assert set(usage["output_tokens_details"]) <= {"reasoning_tokens"}
    assert "reasoning_tokens" in usage["output_tokens_details"]
    assert isinstance(usage["total_tokens"], int)
    assert isinstance(metadata.get("usage_prompt_tokens_formatted"), str)
    assert isinstance(metadata.get("usage_completion_tokens_formatted"), str)
    assert isinstance(metadata.get("usage_total_cost"), (int, float))
    assert isinstance(metadata.get("usage_total_cost_formatted"), str)
    assert isinstance(metadata.get("usage_total_cost_cumulative"), (int, float))
    assert isinstance(metadata.get("usage_total_cost_cumulative_formatted"), str)
    assert isinstance(metadata.get("usage_turn_cost_cumulative"), (int, float))
    assert isinstance(metadata.get("usage_turn_cost_cumulative_formatted"), str)
    assert isinstance(metadata.get("usage_turn_reasoning_tokens_cumulative"), int)
    assert isinstance(
        metadata.get("usage_turn_reasoning_tokens_cumulative_formatted"), str
    )
    assert "usage_estimated_cost" not in metadata
    assert "usage_cost_source" not in metadata
    assert "usage_pricing_model" not in metadata

    native_history = (new_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert any(
        isinstance(item, dict)
        and isinstance(item.get("_metadata"), dict)
        and isinstance(item["_metadata"].get("usage"), dict)
        for item in native_history
    )
    assert all(
        "attribution" not in item["_metadata"]["usage"]
        for item in native_history
        if isinstance(item, dict)
        and isinstance(item.get("_metadata"), dict)
        and isinstance(item["_metadata"].get("usage"), dict)
    )


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_real_api_response_mutation_probe(
    ensure_openai_api_key: str,
) -> None:
    _MutatingOpenAIResponsesProvider.probe_mutations = []
    core = AgentCore()
    core.register_provider(
        _MutatingOpenAIResponsesProvider,
        extensions=[
            OpenAIResponsesToolsExtension,
            OpenAIResponsesUsageExtension,
        ],
    )
    core.register_tool(MathTools)

    config = {
        "model": "gpt-5.6-luna",
        "api_key": ensure_openai_api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        (
            "You must call the add tool exactly once with a=123 and b=456. "
            "Do not calculate the result yourself and do not answer before the "
            "tool returns. After receiving the tool result, reply with exactly: "
            "OPENAI_RESPONSE_MUTATION_PROBE_OK 579"
        ),
    )

    session, first_responses = core.send_request(session, config)

    assert first_responses
    first_metadata = first_responses[-1].get("metadata") or {}
    tool_calls = first_metadata.get("tool_calls")
    assert isinstance(tool_calls, list) and tool_calls
    assert len(tool_calls) == 1
    tool_call = tool_calls[0]
    function = tool_call.get("function") or {}
    assert function.get("name") == "add"

    tool_messages = core.execute_tool_calls(tool_calls, config)
    assert len(tool_messages) == 1
    assert tool_messages[0].get("content") == "579"
    for tool_message in tool_messages:
        session = core.add_message(
            session,
            role=tool_message.get("role", "tool"),
            content=tool_message.get("content", ""),
            metadata=tool_message.get("metadata"),
            config=config,
            tool_result=tool_message.get("toolResult"),
        )

    final_session, final_responses = core.send_request(session, config)

    assert final_responses
    final_content = str(final_responses[-1].get("content"))
    assert "OPENAI_RESPONSE_MUTATION_PROBE_OK" in final_content
    assert "579" in final_content
    assert len(_MutatingOpenAIResponsesProvider.probe_mutations) == 2

    serialized_session = core.export_session(final_session)
    retained_reports: list[str] = []
    for mutation in _MutatingOpenAIResponsesProvider.probe_mutations:
        assert all(
            not marker.response_path.startswith("$.output")
            for marker in mutation.markers
        )
        assert any(
            marker.response_path.startswith("$.usage") for marker in mutation.markers
        )
        retained = detect_probe_markers_in_json(serialized_session, mutation)
        if retained:
            retained_reports.append(format_probe_detections(retained, mutation))

    assert not retained_reports, "\n\n".join(retained_reports)


def _maybe_skip_flex_unavailable(exc: Exception) -> None:
    message = str(exc).lower()
    skip_markers = (
        "service_tier",
        "flex",
        "unsupported",
        "not available",
        "not enabled",
        "permission",
        "entitlement",
        "invalid value",
    )
    if any(marker in message for marker in skip_markers):
        pytest.skip(f"OpenAI flex processing unavailable for this account/model: {exc}")


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_nonstreaming_usage_metadata_surfaces_flex_tier_real_api(
    ensure_openai_api_key: str,
) -> None:
    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[
            OpenAIResponsesFlexProcessingExtension,
            OpenAIResponsesUsageExtension,
        ],
    )

    config = {
        "model": "gpt-5-mini",
        "api_key": ensure_openai_api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
        "enable_flex_processing": True,
        "flex_timeout_seconds": 300,
        "enable_flex_retries": True,
        "flex_max_retries": 2,
    }

    session = core.create_session()
    session = core.add_message(
        session, "user", "Reply with exactly: OPENAI_USAGE_FLEX_OK"
    )

    try:
        _new_session, responses = core.send_request(session, config)
    except Exception as exc:
        _maybe_skip_flex_unavailable(exc)
        raise

    assert responses
    final = responses[-1]
    assert final.get("role") == "assistant"
    assert "OPENAI_USAGE_FLEX_OK" in str(final.get("content"))

    metadata = final.get("metadata") or {}
    assert metadata.get("usage_service_tier") == "flex"
    assert isinstance(metadata.get("usage_total_cost"), (int, float))
    assert isinstance(metadata.get("usage_total_cost_formatted"), str)
