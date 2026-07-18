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

    assert (
        normalize_pricing_table_model_name("gpt-5.4 (<272K context length)")
        == "gpt-5.4"
    )
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

    default_estimated = estimate_usage_cost(
        usage, model="gpt-5-mini", snapshot=snapshot
    )
    flex_estimated = estimate_usage_cost(
        usage,
        model="gpt-5-mini",
        service_tier="flex",
        snapshot=snapshot,
    )

    assert default_estimated == 0.000405
    assert flex_estimated == 0.0002025


def test_estimate_usage_cost_uses_manual_priority_service_tier_when_snapshot_is_missing_model() -> (
    None
):
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


def test_estimate_usage_cost_allows_missing_cached_tier_price_when_no_cached_tokens() -> (
    None
):
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


def test_estimate_usage_cost_does_not_fallback_when_requested_service_tier_missing() -> (
    None
):
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


def test_resolve_pricing_entry_uses_manual_fallback_when_snapshot_is_missing_model() -> (
    None
):
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

    monkeypatch.setattr(
        "scripts.refresh_openai_responses_pricing._fetch_text", fake_fetch
    )

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
    assert (
        payload["models"]["gpt-5-mini"]["service_tiers"]["standard"]["output_per_1m"]
        == 2.0
    )


# ---------------------------------------------------------------------------
# GPT-5.6 four-price-row parser and estimator tests.
# ---------------------------------------------------------------------------


_GPT_5_6_HTML = """
<astro-island component-export="TextTokenPricingTables"
  props="{&quot;tier&quot;:[0,&quot;standard&quot;],&quot;rows&quot;:[1,[[1,[[0,&quot;gpt-5.6-sol&quot;],[0,5.0],[0,0.5],[0,6.25],[0,30.0]]],[1,[[0,&quot;gpt-5.6-terra&quot;],[0,2.5],[0,0.25],[0,3.125],[0,15.0]]],[1,[[0,&quot;gpt-5.6-luna&quot;],[0,1.0],[0,0.1],[0,1.25],[0,6.0]]]]]}" ssr></astro-island>
<astro-island component-export="TextTokenPricingTables"
  props="{&quot;tier&quot;:[0,&quot;flex&quot;],&quot;rows&quot;:[1,[[1,[[0,&quot;gpt-5.6-sol&quot;],[0,2.5],[0,0.25],[0,3.125],[0,15.0]]],[1,[[0,&quot;gpt-5.6-terra&quot;],[0,1.25],[0,0.125],[0,1.5625],[0,7.5]]],[1,[[0,&quot;gpt-5.6-luna&quot;],[0,0.5],[0,0.05],[0,0.625],[0,3.0]]]]]}" ssr></astro-island>
<astro-island component-export="TextTokenPricingTables"
  props="{&quot;tier&quot;:[0,&quot;batch&quot;],&quot;rows&quot;:[1,[[1,[[0,&quot;gpt-5.6-sol&quot;],[0,2.5],[0,0.25],[0,3.125],[0,15.0]]],[1,[[0,&quot;gpt-5.6-terra&quot;],[0,1.25],[0,0.125],[0,1.5625],[0,7.5]]],[1,[[0,&quot;gpt-5.6-luna&quot;],[0,0.5],[0,0.05],[0,0.625],[0,3.0]]]]]}" ssr></astro-island>
<astro-island component-export="TextTokenPricingTables"
  props="{&quot;tier&quot;:[0,&quot;priority&quot;],&quot;rows&quot;:[1,[[1,[[0,&quot;gpt-5.6-sol&quot;],[0,10.0],[0,1.0],[0,12.5],[0,60.0]]],[1,[[0,&quot;gpt-5.6-terra&quot;],[0,5.0],[0,0.5],[0,6.25],[0,30.0]]],[1,[[0,&quot;gpt-5.6-luna&quot;],[0,2.0],[0,0.2],[0,2.5],[0,12.0]]]]]}" ssr></astro-island>
"""


def _gpt_5_6_snapshot() -> dict:
    entries = extract_visible_text_token_tier_pricing_from_page_html(
        html=_GPT_5_6_HTML,
        source_url="https://developers.openai.com/api/docs/pricing?latest-pricing=standard",
    )
    merged: dict = {}
    for model, entry in entries.items():
        merged[model] = merge_pricing_entry(merged.get(model), entry)
    return build_snapshot_payload(
        fetched_at="2026-07-13T00:00:00+00:00",
        model_entries=merged.values(),
    )


def test_extract_visible_text_token_tier_pricing_parses_legacy_three_price_rows() -> (
    None
):
    """Legacy rows with three price columns still parse (regression)."""
    html = """
    <astro-island component-export="TextTokenPricingTables"
      props="{&quot;tier&quot;:[0,&quot;standard&quot;],&quot;rows&quot;:[1,[[1,[[0,&quot;gpt-5-mini&quot;],[0,0.25],[0,0.025],[0,2]]]]]}" ssr></astro-island>
    """
    entries = extract_visible_text_token_tier_pricing_from_page_html(
        html=html,
        source_url="https://developers.openai.com/api/docs/pricing?latest-pricing=standard",
    )
    assert entries["gpt-5-mini"]["service_tiers"]["standard"] == {
        "input_per_1m": 0.25,
        "cached_input_per_1m": 0.025,
        "output_per_1m": 2.0,
    }
    assert (
        "cache_write_per_1m" not in entries["gpt-5-mini"]["service_tiers"]["standard"]
    )


def test_extract_visible_text_token_tier_pricing_parses_new_four_price_rows() -> None:
    """GPT-5.6 rows with four price columns parse and capture cache_write_per_1m."""
    entries = extract_visible_text_token_tier_pricing_from_page_html(
        html=_GPT_5_6_HTML,
        source_url="https://developers.openai.com/api/docs/pricing?latest-pricing=standard",
    )
    assert entries["gpt-5.6-sol"]["service_tiers"]["standard"] == {
        "input_per_1m": 5.0,
        "cached_input_per_1m": 0.5,
        "cache_write_per_1m": 6.25,
        "output_per_1m": 30.0,
    }
    assert (
        entries["gpt-5.6-luna"]["service_tiers"]["standard"]["cache_write_per_1m"]
        == 1.25
    )


def test_extract_visible_text_token_tier_pricing_parses_all_gpt_5_6_tiers() -> None:
    """Standard, batch, flex, and priority tiers all parse for GPT-5.6."""
    entries = extract_visible_text_token_tier_pricing_from_page_html(
        html=_GPT_5_6_HTML,
        source_url="https://developers.openai.com/api/docs/pricing?latest-pricing=standard",
    )
    for tier in ("standard", "batch", "flex", "priority"):
        assert tier in entries["gpt-5.6-sol"]["service_tiers"]
        assert tier in entries["gpt-5.6-terra"]["service_tiers"]
        assert tier in entries["gpt-5.6-luna"]["service_tiers"]
    assert (
        entries["gpt-5.6-sol"]["service_tiers"]["priority"]["cache_write_per_1m"]
        == 12.5
    )
    assert (
        entries["gpt-5.6-luna"]["service_tiers"]["flex"]["cache_write_per_1m"] == 0.625
    )


def test_merge_pricing_entry_preserves_cache_write_field_across_tiers() -> None:
    existing = {
        "model": "gpt-5.6-luna",
        "service_tiers": {
            "standard": {
                "input_per_1m": 1.0,
                "cached_input_per_1m": 0.1,
                "cache_write_per_1m": 1.25,
                "output_per_1m": 6.0,
            }
        },
    }
    incoming = {
        "model": "gpt-5.6-luna",
        "source_url": "https://developers.openai.com/api/docs/pricing?latest-pricing=flex",
        "service_tiers": {
            "flex": {
                "input_per_1m": 0.5,
                "cached_input_per_1m": 0.05,
                "cache_write_per_1m": 0.625,
                "output_per_1m": 3.0,
            }
        },
    }

    merged = merge_pricing_entry(existing, incoming)

    assert merged["service_tiers"]["standard"]["cache_write_per_1m"] == 1.25
    assert merged["service_tiers"]["flex"]["cache_write_per_1m"] == 0.625


def test_estimate_usage_cost_default_standard_gpt_5_6_luna() -> None:
    snapshot = _gpt_5_6_snapshot()
    usage = {
        "input_tokens": 1000,
        "output_tokens": 100,
    }
    estimated = estimate_usage_cost(usage, model="gpt-5.6-luna", snapshot=snapshot)
    # ordinary 1000 * 1.0 + 0 + 0 + 100 * 6.0 = 1600 / 1M
    assert estimated == pytest.approx(0.0016, rel=1e-9)


def test_estimate_usage_cost_flex_gpt_5_6_luna() -> None:
    snapshot = _gpt_5_6_snapshot()
    usage = {
        "input_tokens": 1000,
        "output_tokens": 100,
    }
    estimated = estimate_usage_cost(
        usage, model="gpt-5.6-luna", service_tier="flex", snapshot=snapshot
    )
    # ordinary 1000 * 0.5 + 0 + 0 + 100 * 3.0 = 800 / 1M
    assert estimated == pytest.approx(0.0008, rel=1e-9)


def test_estimate_usage_cost_priority_gpt_5_6_luna() -> None:
    snapshot = _gpt_5_6_snapshot()
    usage = {
        "input_tokens": 1000,
        "output_tokens": 100,
    }
    estimated = estimate_usage_cost(
        usage, model="gpt-5.6-luna", service_tier="priority", snapshot=snapshot
    )
    # ordinary 1000 * 2.0 + 0 + 0 + 100 * 12.0 = 3200 / 1M
    assert estimated == pytest.approx(0.0032, rel=1e-9)


def test_estimate_usage_cost_cached_read_uses_cached_input_rate() -> None:
    snapshot = _gpt_5_6_snapshot()
    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cached_tokens": 400},
        "output_tokens": 100,
    }
    estimated = estimate_usage_cost(usage, model="gpt-5.6-luna", snapshot=snapshot)
    # ordinary 600 * 1.0 + cached 400 * 0.1 + 0 + 100 * 6.0 = 1240 / 1M
    assert estimated == pytest.approx(0.00124, rel=1e-9)


def test_estimate_usage_cost_cache_write_uses_cache_write_rate() -> None:
    snapshot = _gpt_5_6_snapshot()
    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cache_write_tokens": 300},
        "output_tokens": 100,
    }
    estimated = estimate_usage_cost(usage, model="gpt-5.6-luna", snapshot=snapshot)
    # ordinary 700 * 1.0 + 0 + write 300 * 1.25 + 100 * 6.0 = 700 + 375 + 600 = 1675 / 1M
    assert estimated == pytest.approx(0.001675, rel=1e-9)


def test_estimate_usage_cost_ordinary_input_excludes_cached_and_write() -> None:
    snapshot = _gpt_5_6_snapshot()
    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cached_tokens": 300, "cache_write_tokens": 200},
        "output_tokens": 100,
    }
    estimated = estimate_usage_cost(usage, model="gpt-5.6-luna", snapshot=snapshot)
    # ordinary 500 * 1.0 + cached 300 * 0.1 + write 200 * 1.25 + 100 * 6.0
    # = 500 + 30 + 250 + 600 = 1380 / 1M
    assert estimated == pytest.approx(0.00138, rel=1e-9)


def test_estimate_usage_cost_mixed_buckets_gpt_5_6_sol_standard() -> None:
    """Mixed ordinary/read/write/output calculation for gpt-5.6-sol standard tier.

    input_tokens=10000, cached_tokens=3000, cache_write_tokens=2000, output=500
    ordinary = 10000 - 3000 - 2000 = 5000
    ordinary 5000 * 5.00 = 25000
    cached   3000 * 0.50 = 1500
    write    2000 * 6.25 = 12500
    output    500 * 30.0 = 15000
    total = 54000 / 1M = $0.054
    """
    snapshot = _gpt_5_6_snapshot()
    usage = {
        "input_tokens": 10000,
        "input_tokens_details": {"cached_tokens": 3000, "cache_write_tokens": 2000},
        "output_tokens": 500,
    }
    estimated = estimate_usage_cost(usage, model="gpt-5.6-sol", snapshot=snapshot)
    assert estimated == pytest.approx(0.054, rel=1e-9)


def test_estimate_usage_cost_missing_cache_write_tokens_defaults_to_zero() -> None:
    snapshot = _gpt_5_6_snapshot()
    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cached_tokens": 200},
        "output_tokens": 100,
    }
    estimated = estimate_usage_cost(usage, model="gpt-5.6-luna", snapshot=snapshot)
    # ordinary 800 * 1.0 + cached 200 * 0.1 + 0 + 100 * 6.0 = 800 + 20 + 600 = 1420 / 1M
    assert estimated == pytest.approx(0.00142, rel=1e-9)


def test_estimate_usage_cost_missing_cache_write_price_falls_back_to_input_rate() -> (
    None
):
    """When a model has no cache_write_per_1m but usage reports cache writes,
    the estimator falls back to the ordinary input rate so the model remains
    estimable instead of returning None.
    """
    snapshot = build_snapshot_payload(
        fetched_at="2026-07-13T00:00:00+00:00",
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
        "input_tokens_details": {"cached_tokens": 200, "cache_write_tokens": 300},
        "output_tokens": 100,
    }
    estimated = estimate_usage_cost(usage, model="gpt-5-mini", snapshot=snapshot)
    # ordinary 500 * 0.25 + cached 200 * 0.025 + write 300 * 0.25 (fallback) + 100 * 2.0
    # = 125 + 5 + 75 + 200 = 405 / 1M
    assert estimated == pytest.approx(0.000405, rel=1e-9)


def test_estimate_usage_cost_clamps_oversized_cached_tokens() -> None:
    snapshot = _gpt_5_6_snapshot()
    usage = {
        "input_tokens": 500,
        "input_tokens_details": {"cached_tokens": 800},
        "output_tokens": 100,
    }
    estimated = estimate_usage_cost(usage, model="gpt-5.6-luna", snapshot=snapshot)
    # cached clamped to 500, ordinary = 0
    # 0 + 500 * 0.1 + 0 + 100 * 6.0 = 650 / 1M
    assert estimated == pytest.approx(0.00065, rel=1e-9)


def test_estimate_usage_cost_clamps_oversized_cache_write_tokens() -> None:
    snapshot = _gpt_5_6_snapshot()
    usage = {
        "input_tokens": 500,
        "input_tokens_details": {"cache_write_tokens": 800},
        "output_tokens": 100,
    }
    estimated = estimate_usage_cost(usage, model="gpt-5.6-luna", snapshot=snapshot)
    # write clamped to 500, ordinary = 0
    # 0 + 0 + 500 * 1.25 + 100 * 6.0 = 1225 / 1M
    assert estimated == pytest.approx(0.001225, rel=1e-9)


def test_estimate_usage_cost_clamps_when_cached_plus_write_exceeds_input() -> None:
    """When cached + write > input, reduce the larger counter and clamp ordinary to 0."""
    snapshot = _gpt_5_6_snapshot()
    # cached=400, write=400, input=500 → cached is larger (equal), reduce cached to 100
    # ordinary = 0, cached = 100, write = 400
    usage = {
        "input_tokens": 500,
        "input_tokens_details": {"cached_tokens": 400, "cache_write_tokens": 400},
        "output_tokens": 100,
    }
    estimated = estimate_usage_cost(usage, model="gpt-5.6-luna", snapshot=snapshot)
    # 0 + 100 * 0.1 + 400 * 1.25 + 100 * 6.0 = 10 + 500 + 600 = 1110 / 1M
    assert estimated == pytest.approx(0.00111, rel=1e-9)

    # Now test the other direction: write is larger
    usage2 = {
        "input_tokens": 500,
        "input_tokens_details": {"cached_tokens": 100, "cache_write_tokens": 600},
        "output_tokens": 100,
    }
    estimated2 = estimate_usage_cost(usage2, model="gpt-5.6-luna", snapshot=snapshot)
    # write reduced to 400, cached = 100, ordinary = 0
    # 0 + 100 * 0.1 + 400 * 1.25 + 100 * 6.0 = 10 + 500 + 600 = 1110 / 1M
    assert estimated2 == pytest.approx(0.00111, rel=1e-9)


def test_resolve_pricing_entry_returns_gpt_5_6_luna_from_refreshed_snapshot() -> None:
    snapshot = _gpt_5_6_snapshot()
    entry = resolve_pricing_entry("gpt-5.6-luna", snapshot=snapshot)
    assert entry is not None
    assert entry["model"] == "gpt-5.6-luna"
    tiers = entry["service_tiers"]
    assert tiers["standard"]["cache_write_per_1m"] == 1.25
    assert tiers["flex"]["cache_write_per_1m"] == 0.625
    assert tiers["priority"]["cache_write_per_1m"] == 2.5


def test_refresh_snapshot_includes_gpt_5_6_family(monkeypatch, tmp_path) -> None:
    """Refresh from synthetic HTML with 4-column rows writes all three GPT-5.6
    models with all four tiers (regression for the parser fix).
    """
    html = _GPT_5_6_HTML

    def fake_fetch(url: str) -> str:
        return html

    monkeypatch.setattr(
        "scripts.refresh_openai_responses_pricing._fetch_text", fake_fetch
    )

    output_path = tmp_path / "pricing.json"
    output_path.write_text(
        json.dumps(
            {
                "version": 1,
                "fetched_at": "2026-03-10T00:00:00+00:00",
                "source_base_url": "https://developers.openai.com/api/docs/models",
                "models": {},
            }
        ),
        encoding="utf-8",
    )

    refresh_snapshot(
        urls=[
            "https://developers.openai.com/api/docs/pricing?latest-pricing=standard",
            "https://developers.openai.com/api/docs/pricing?latest-pricing=flex",
        ],
        output_path=output_path,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    for model in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"):
        assert model in payload["models"], f"missing {model} in refreshed snapshot"
        tiers = payload["models"][model]["service_tiers"]
        for tier in ("standard", "batch", "flex", "priority"):
            assert tier in tiers, f"missing {tier} tier for {model}"
            assert (
                "cache_write_per_1m" in tiers[tier]
            ), f"missing cache_write_per_1m for {model}/{tier}"
