"""Unit tests for the provider-defined cost bucket helper."""

from __future__ import annotations

from openai_responses_plugins.cost_bucket import (
    DEFAULT_OPENAI_RESPONSES_COST_BUCKET,
    cost_bucket_base,
    resolve_cost_bucket,
)


def test_default_bucket_base() -> None:
    assert DEFAULT_OPENAI_RESPONSES_COST_BUCKET == "openai-responses"
    assert cost_bucket_base({}) == "openai-responses"
    assert cost_bucket_base(None) == "openai-responses"
    assert cost_bucket_base({"cost_bucket": "   "}) == "openai-responses"


def test_bucket_base_honors_config_override() -> None:
    assert cost_bucket_base({"cost_bucket": "openai"}) == "openai"
    assert cost_bucket_base({"cost_bucket": "  openai  "}) == "openai"


def test_final_bucket_appends_chatgpt_suffix_for_chatgpt_endpoint() -> None:
    assert resolve_cost_bucket({}, "chatgpt") == "openai-responses-chatgpt"
    assert resolve_cost_bucket({"cost_bucket": "openai"}, "chatgpt") == (
        "openai-chatgpt"
    )


def test_final_bucket_appends_api_suffix_for_api_endpoint() -> None:
    assert resolve_cost_bucket({}, "api") == "openai-responses-api"
    assert resolve_cost_bucket({"cost_bucket": "openai"}, "api") == "openai-api"


def test_final_bucket_defaults_to_api_for_unknown_mode() -> None:
    assert resolve_cost_bucket({}, None) == "openai-responses-api"
    assert resolve_cost_bucket({}, "auto") == "openai-responses-api"
    assert resolve_cost_bucket({}, "CHATGPT") == "openai-responses-chatgpt"
