from __future__ import annotations

import json

from openai_responses_plugins.openai_responses_pricing import (
    build_snapshot_payload,
    estimate_usage_cost,
    extract_pricing_from_model_doc_html,
    normalize_model_name,
    resolve_pricing_entry,
)
from scripts.refresh_openai_responses_pricing import refresh_snapshot


def test_extract_pricing_from_model_doc_html_parses_input_cached_and_output() -> None:
    html = """
    <div>Text tokens</div>
    <div><div>Input</div><div class="text-2xl font-semibold">$0.25</div></div>
    <div><div>Cached input</div><div class="text-2xl font-semibold">$0.025</div></div>
    <div><div>Output</div><div class="text-2xl font-semibold">$2.00</div></div>
    <div>Modalities</div>
    """

    entry = extract_pricing_from_model_doc_html(
        html=html,
        model="gpt-5-mini",
        source_url="https://developers.openai.com/api/docs/models/gpt-5-mini",
    )

    assert entry == {
        "model": "gpt-5-mini",
        "source_url": "https://developers.openai.com/api/docs/models/gpt-5-mini",
        "pricing": {
            "input_per_1m": 0.25,
            "cached_input_per_1m": 0.025,
            "output_per_1m": 2.0,
        },
    }


def test_estimate_usage_cost_uses_cached_and_uncached_token_rates() -> None:
    snapshot = build_snapshot_payload(
        fetched_at="2026-03-11T00:00:00+00:00",
        model_entries=[
            {
                "model": "gpt-5-mini",
                "source_url": "https://developers.openai.com/api/docs/models/gpt-5-mini",
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

    estimated = estimate_usage_cost(usage, model="gpt-5-mini", snapshot=snapshot)

    assert estimated == 0.000405


def test_resolve_pricing_entry_normalizes_snapshot_suffix_models() -> None:
    snapshot = build_snapshot_payload(
        fetched_at="2026-03-11T00:00:00+00:00",
        model_entries=[
            {
                "model": "gpt-5-mini",
                "source_url": "https://developers.openai.com/api/docs/models/gpt-5-mini",
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


def test_refresh_snapshot_writes_json_from_official_model_doc_fetches(
    monkeypatch, tmp_path
) -> None:
    html = """
    <div>Text tokens</div>
    <div><div>Input</div><div>$1.25</div></div>
    <div><div>Cached input</div><div>$0.125</div></div>
    <div><div>Output</div><div>$10.00</div></div>
    <div>Quick comparison</div>
    """

    def fake_fetch(url: str) -> str:
        assert url.endswith("/gpt-5")
        return html

    monkeypatch.setattr("scripts.refresh_openai_responses_pricing._fetch_text", fake_fetch)

    output_path = tmp_path / "pricing.json"
    written = refresh_snapshot(models=["gpt-5"], output_path=output_path)

    assert written == output_path
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["models"]["gpt-5"]["pricing"] == {
        "cached_input_per_1m": 0.125,
        "input_per_1m": 1.25,
        "output_per_1m": 10.0,
    }


def test_refresh_snapshot_preserves_models_not_explicitly_refreshed(
    monkeypatch, tmp_path
) -> None:
    html = """
    <div>Text tokens</div>
    <div><div>Input</div><div>$1.25</div></div>
    <div><div>Cached input</div><div>$0.125</div></div>
    <div><div>Output</div><div>$10.00</div></div>
    <div>Quick comparison</div>
    """

    def fake_fetch(url: str) -> str:
        assert url.endswith("/gpt-5")
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
                        "source_url": "https://developers.openai.com/api/docs/models/gpt-4o",
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

    refresh_snapshot(models=["gpt-5"], output_path=output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["models"]["gpt-4o"]["pricing"] == {
        "cached_input_per_1m": 1.25,
        "input_per_1m": 2.5,
        "output_per_1m": 10.0,
    }
    assert payload["models"]["gpt-5"]["pricing"] == {
        "cached_input_per_1m": 0.125,
        "input_per_1m": 1.25,
        "output_per_1m": 10.0,
    }