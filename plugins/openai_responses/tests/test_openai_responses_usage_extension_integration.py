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
from openai_responses_plugins.openai_responses_usage_extension import (
    OpenAIResponsesUsageExtension,
)


pytestmark = pytest.mark.api
_PROBE_SEED = 20260912


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
        mutation = mutate_response_objects(payload, seed=_PROBE_SEED)
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
    return api_key


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
        extensions=[OpenAIResponsesUsageExtension],
    )

    config = {
        "model": "gpt-5-mini",
        "api_key": ensure_openai_api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: OPENAI_RESPONSE_MUTATION_PROBE_OK",
    )

    new_session, responses = core.send_request(session, config)

    assert responses
    assert "OPENAI_RESPONSE_MUTATION_PROBE_OK" in str(responses[-1].get("content"))
    assert len(_MutatingOpenAIResponsesProvider.probe_mutations) == 1
    mutation = _MutatingOpenAIResponsesProvider.probe_mutations[0]
    serialized_session = core.export_session(new_session)
    retained = detect_probe_markers_in_json(serialized_session, mutation)

    retained_ids = {detection.marker.marker_id for detection in retained}
    response_root_ids = {
        marker.marker_id
        for marker in mutation.markers
        if marker.response_path.startswith("$.__probe_")
    }
    usage_root_ids = {
        marker.marker_id
        for marker in mutation.markers
        if marker.response_path.startswith("$.usage.__probe_")
    }
    assert retained_ids.isdisjoint(response_root_ids)
    assert retained_ids.isdisjoint(usage_root_ids)

    if retained:
        pytest.xfail(format_probe_detections(retained, mutation))


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
