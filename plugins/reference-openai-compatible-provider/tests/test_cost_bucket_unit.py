"""Unit tests for the reference provider's cost bucket helper."""

from __future__ import annotations

from reference_openai_compatible_provider.cost_bucket import (
    DEFAULT_OPENAI_COMPATIBLE_COST_BUCKET,
    cost_bucket_base,
    endpoint_host_slug,
    resolve_cost_bucket,
)


def test_default_bucket_base() -> None:
    assert DEFAULT_OPENAI_COMPATIBLE_COST_BUCKET == "openai-compatible"
    assert cost_bucket_base({}) == "openai-compatible"
    assert cost_bucket_base(None) == "openai-compatible"
    assert cost_bucket_base({"cost_bucket": "   "}) == "openai-compatible"


def test_bucket_base_honors_config_override() -> None:
    assert cost_bucket_base({"cost_bucket": "fireworks"}) == "fireworks"


def test_endpoint_host_slug_slugs_the_url_host() -> None:
    assert endpoint_host_slug("https://api.fireworks.ai/v1") == "api-fireworks-ai"
    assert endpoint_host_slug("http://localhost:11434/v1") == "localhost"
    assert endpoint_host_slug("https://user@host.example:8080/v1") == ("host-example")
    assert endpoint_host_slug("") == ""
    assert endpoint_host_slug(None) == ""
    # No parseable host (no netloc) → empty slug; the bucket falls back to the
    # configured base only.
    assert endpoint_host_slug("not-a-url") == ""


def test_final_bucket_appends_endpoint_host_slug() -> None:
    assert resolve_cost_bucket({"base_url": "https://api.fireworks.ai/v1"}) == (
        "openai-compatible-api-fireworks-ai"
    )
    assert resolve_cost_bucket(
        {"base_url": "http://localhost:11434/v1", "cost_bucket": "local"}
    ) == ("local-localhost")


def test_final_bucket_falls_back_to_base_without_host() -> None:
    assert resolve_cost_bucket({}) == "openai-compatible"
