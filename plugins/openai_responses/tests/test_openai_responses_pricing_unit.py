from __future__ import annotations

import json

import pytest

from openai_responses_plugins.openai_responses_pricing import (
    build_snapshot_payload,
    estimate_usage_cost,
    extract_visible_text_token_tier_pricing_from_page_html,
    merge_pricing_entry,
    normalize_model_name,
    normalize_pricing_table_model_name,
    resolve_pricing_entry,
)
from scripts.refresh_openai_responses_pricing import refresh_snapshot


def test_extract_visible_text_token_tier_pricing_from_page_html_parses_tiers() -> None:
    html = """
    <astro-island component-export="TextTokenPricingTables"
      props="{&quot;tier&quot;:[0,&quot;standard&quot;],&quot;rows&quot;:[1,[[1,[[0,&quot;gpt-5.4 (&lt;272K context length)&quot;],[0,2.5],[0,0.25],[0,15]]],[1,[[0,&quot;gpt-5-mini&quot;],[0,0.25],[0,0.025],[0,2]]]]]}" ssr></astro-island>
    <astro-island component-export="TextTokenPricingTables"
      props="{&quot;tier&quot;:[0,&quot;flex&quot;],&quot;rows&quot;:[1,[[1,[[0,&quot;gpt-5.4 (&lt;272K context length)&quot;],[0,1.25],[0,0.13],[0,7.5]]],[1,[[0,&quot;gpt-5.4-pro (&lt;272K context length)&quot;],[0,15],[0,&quot;&quot;],[0,90]]],[1,[[0,&quot;gpt-5-mini&quot;],[0,0.125],[0,0.0125],[0,1]]]]]}" ssr></astro-island>
    """

    entries = extract_visible_text_token_tier_pricing_from_page_html(
        html=html,
        source_url="https://developers.openai.com/api/docs/pricing?latest-pricing=flex",
    )

    assert normalize_pricing_table_model_name("gpt-5.4 (<272K context length)") == "gpt-5.4"
    assert entries["gpt-5.4"]["service_tiers"]["standard"] == {
        "input_per_1m": 2.5,
        "cached_input_per_1m": 0.25,
        "output_per_1m": 15.0,
    }
    assert entries["gpt-5.4"]["service_tiers"]["flex"] == {
        "input_per_1m": 1.25,
        "cached_input_per_1m": 0.13,
        "output_per_1m": 7.5,
    }
    assert entries["gpt-5-mini"]["service_tiers"]["flex"]["output_per_1m"] == 1.0
    assert entries["gpt-5.4-pro"]["service_tiers"]["flex"] == {
        "input_per_1m": 15.0,
        "output_per_1m": 90.0,
    }


def test_estimate_usage_cost_prefers_requested_service_tier() -> None:
    snapshot = build_snapshot_payload(
        fetched_at="2026-03-11T00:00:00+00:00",
        model_entries=[
            {
                "model": "gpt-5-mini",
                "pricing": {
                    "input_per_1m": 0.25,
                    "cached_input_per_1m": 0.025,
                    "output_per_1m": 2.0,
                },
                "service_tiers": {
                    "flex": {
                        "input_per_1m": 0.125,
                        "cached_input_per_1m": 0.0125,
                        "output_per_1m": 1.0,
                    }
                },
            }
        ],
    )
    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cached_tokens": 200},
        "output_tokens": 100,
    }

    default_estimated = estimate_usage_cost(usage, model="gpt-5-mini", snapshot=snapshot)
    flex_estimated = estimate_usage_cost(
        usage,
        model="gpt-5-mini",
        service_tier="flex",
        snapshot=snapshot,
    )

    assert default_estimated == 0.000405
    assert flex_estimated == 0.0002025


def test_estimate_usage_cost_uses_manual_priority_service_tier_when_snapshot_is_missing_model() -> None:
    snapshot = build_snapshot_payload(
        fetched_at="2026-03-11T00:00:00+00:00",
        model_entries=[],
    )
    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cached_tokens": 200},
        "output_tokens": 100,
    }

    estimated = estimate_usage_cost(
        usage,
        model="gpt-5.5",
        service_tier="priority",
        snapshot=snapshot,
        manual_entries={
            "gpt-5.5": {
                "model": "gpt-5.5",
                "pricing": {
                    "input_per_1m": 5.0,
                    "cached_input_per_1m": 0.5,
                    "output_per_1m": 30.0,
                },
                "service_tiers": {
                    "priority": {
                        "input_per_1m": 6.0,
                        "cached_input_per_1m": 0.6,
                        "output_per_1m": 36.0,
                    }
                },
            }
        },
    )

    assert estimated == pytest.approx(0.00852, rel=1e-9)


def test_estimate_usage_cost_allows_missing_cached_tier_price_when_no_cached_tokens() -> None:
    snapshot = build_snapshot_payload(
        fetched_at="2026-03-11T00:00:00+00:00",
        model_entries=[
            {
                "model": "gpt-5.4-pro",
                "service_tiers": {
                    "flex": {
                        "input_per_1m": 15.0,
                        "output_per_1m": 90.0,
                    }
                },
            }
        ],
    )
    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cached_tokens": 0},
        "output_tokens": 100,
    }

    estimated = estimate_usage_cost(
        usage,
        model="gpt-5.4-pro",
        service_tier="flex",
        snapshot=snapshot,
    )

    assert estimated == 0.024


def test_estimate_usage_cost_does_not_fallback_when_requested_service_tier_missing() -> None:
    snapshot = build_snapshot_payload(
        fetched_at="2026-03-11T00:00:00+00:00",
        model_entries=[
            {
                "model": "gpt-5-mini",
                "pricing": {
                    "input_per_1m": 0.25,
                    "cached_input_per_1m": 0.025,
                    "output_per_1m": 2.0,
                },
            }
        ],
    )
    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cached_tokens": 200},
        "output_tokens": 100,
    }

    estimated = estimate_usage_cost(
        usage,
        model="gpt-5-mini",
        service_tier="flex",
        snapshot=snapshot,
    )

    assert estimated is None


def test_resolve_pricing_entry_normalizes_snapshot_suffix_models() -> None:
    snapshot = build_snapshot_payload(
        fetched_at="2026-03-11T00:00:00+00:00",
        model_entries=[
            {
                "model": "gpt-5-mini",
                "pricing": {
                    "input_per_1m": 0.25,
                    "cached_input_per_1m": 0.025,
                    "output_per_1m": 2.0,
                },
            }
        ],
    )

    assert normalize_model_name("gpt-5-mini-2025-08-07") == "gpt-5-mini"
    entry = resolve_pricing_entry("gpt-5-mini-2025-08-07", snapshot=snapshot)
    assert entry is not None
    assert entry["model"] == "gpt-5-mini"


def test_resolve_pricing_entry_prefers_snapshot_entries_over_manual_fallbacks() -> None:
    snapshot = build_snapshot_payload(
        fetched_at="2026-03-11T00:00:00+00:00",
        model_entries=[
            {
                "model": "gpt-5.5",
                "pricing": {
                    "input_per_1m": 4.0,
                    "cached_input_per_1m": 0.4,
                    "output_per_1m": 20.0,
                },
            }
        ],
    )

    entry = resolve_pricing_entry(
        "gpt-5.5",
        snapshot=snapshot,
        manual_entries={
            "gpt-5.5": {
                "model": "gpt-5.5",
                "pricing": {
                    "input_per_1m": 5.0,
                    "cached_input_per_1m": 0.5,
                    "output_per_1m": 30.0,
                },
            }
        },
    )

    assert entry is not None
    assert entry["pricing"]["input_per_1m"] == 4.0


def test_resolve_pricing_entry_uses_manual_fallback_when_snapshot_is_missing_model() -> None:
    snapshot = build_snapshot_payload(
        fetched_at="2026-03-11T00:00:00+00:00",
        model_entries=[],
    )

    entry = resolve_pricing_entry(
        "gpt-5.5",
        snapshot=snapshot,
        manual_entries={
            "gpt-5.5": {
                "model": "gpt-5.5",
                "pricing": {
                    "input_per_1m": 5.0,
                    "cached_input_per_1m": 0.5,
                    "output_per_1m": 30.0,
                },
            }
        },
    )

    assert entry is not None
    assert entry["pricing"]["input_per_1m"] == 5.0


def test_merge_pricing_entry_preserves_existing_pricing_and_adds_tiers() -> None:
    existing = {
        "model": "gpt-5-mini",
        "pricing": {
            "input_per_1m": 0.25,
            "cached_input_per_1m": 0.025,
            "output_per_1m": 2.0,
        },
    }
    incoming = {
        "model": "gpt-5-mini",
        "source_url": "https://developers.openai.com/api/docs/pricing?latest-pricing=flex",
        "service_tiers": {
            "flex": {
                "input_per_1m": 0.125,
                "cached_input_per_1m": 0.0125,
                "output_per_1m": 1.0,
            }
        },
    }

    merged = merge_pricing_entry(existing, incoming)

    assert merged["pricing"]["input_per_1m"] == 0.25
    assert merged["service_tiers"]["flex"]["output_per_1m"] == 1.0


def test_refresh_snapshot_writes_visible_pricing_rows_and_preserves_existing_models(
    monkeypatch, tmp_path
) -> None:
    html = """
    <astro-island component-export="TextTokenPricingTables"
      props="{&quot;tier&quot;:[0,&quot;standard&quot;],&quot;rows&quot;:[1,[[1,[[0,&quot;gpt-5.4 (&lt;272K context length)&quot;],[0,2.5],[0,0.25],[0,15]]],[1,[[0,&quot;gpt-5-mini&quot;],[0,0.25],[0,0.025],[0,2]]]]]}" ssr></astro-island>
    <astro-island component-export="TextTokenPricingTables"
      props="{&quot;tier&quot;:[0,&quot;flex&quot;],&quot;rows&quot;:[1,[[1,[[0,&quot;gpt-5.4 (&lt;272K context length)&quot;],[0,1.25],[0,0.13],[0,7.5]]],[1,[[0,&quot;gpt-5.4-pro (&lt;272K context length)&quot;],[0,15],[0,&quot;&quot;],[0,90]]],[1,[[0,&quot;gpt-5-mini&quot;],[0,0.125],[0,0.0125],[0,1]]]]]}" ssr></astro-island>
    """

    def fake_fetch(url: str) -> str:
        assert "pricing" in url
        return html

    monkeypatch.setattr("scripts.refresh_openai_responses_pricing._fetch_text", fake_fetch)

    output_path = tmp_path / "pricing.json"
    output_path.write_text(
        json.dumps(
            {
                "version": 1,
                "fetched_at": "2026-03-10T00:00:00+00:00",
                "source_base_url": "https://developers.openai.com/api/docs/models",
                "models": {
                    "gpt-4o": {
                        "model": "gpt-4o",
                        "pricing": {
                            "input_per_1m": 2.5,
                            "cached_input_per_1m": 1.25,
                            "output_per_1m": 10.0,
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    refresh_snapshot(
        urls=["https://developers.openai.com/api/docs/pricing?latest-pricing=standard"],
        output_path=output_path,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["version"] == 2
    assert payload["models"]["gpt-4o"]["pricing"] == {
        "cached_input_per_1m": 1.25,
        "input_per_1m": 2.5,
        "output_per_1m": 10.0,
    }
    assert payload["models"]["gpt-5.4"]["service_tiers"]["flex"] == {
        "cached_input_per_1m": 0.13,
        "input_per_1m": 1.25,
        "output_per_1m": 7.5,
    }
    assert payload["models"]["gpt-5-mini"]["service_tiers"]["standard"]["output_per_1m"] == 2.0
