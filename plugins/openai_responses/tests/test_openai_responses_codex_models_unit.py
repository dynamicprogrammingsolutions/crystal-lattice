from __future__ import annotations

import json
from pathlib import Path

import pytest

from openai_responses_plugins.openai_responses_codex_models import (
    build_snapshot_payload,
    load_manual_chatgpt_model_pricing,
    load_snapshot_model_descriptors,
    merge_model_descriptors,
    normalize_model_descriptor,
    normalize_models_payload,
)
from refresh_openai_responses_models import refresh_snapshot


def test_merge_model_descriptors_applies_later_source_precedence() -> None:
    merged = merge_model_descriptors(
        [{"id": "gpt-5.4", "name": "manual", "description": "manual"}],
        [{"id": "gpt-5.4", "name": "snapshot"}],
        [{"id": "gpt-5.4", "name": "live"}],
    )

    assert merged == [{"id": "gpt-5.4", "name": "live", "description": "manual"}]


def test_load_snapshot_model_descriptors_reads_snapshot_mapping(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "models.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "version": 1,
                "fetched_at": "2026-03-15T00:00:00+00:00",
                "source_base_url": "https://raw.githubusercontent.com/openai/codex",
                "models": {
                    "gpt-5.4": {
                        "id": "gpt-5.4",
                        "name": "gpt-5.4",
                        "description": "Latest frontier agentic coding model.",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    models = load_snapshot_model_descriptors(str(snapshot_path))

    assert models == [
        {
            "id": "gpt-5.4",
            "name": "gpt-5.4",
            "description": "Latest frontier agentic coding model.",
        }
    ]


def test_load_manual_chatgpt_model_pricing_preserves_service_tiers(
    tmp_path: Path,
) -> None:
    manual_path = tmp_path / "manual_models.json"
    manual_path.write_text(
        json.dumps(
            {
                "version": 1,
                "models": {
                    "gpt-5.5": {
                        "id": "gpt-5.5",
                        "pricing": {
                            "input_per_1m": 5.0,
                            "cached_input_per_1m": 0.5,
                            "output_per_1m": 30.0,
                        },
                        "service_tiers": {
                            "fast": {
                                "input_per_1m": 5.0,
                                "cached_input_per_1m": 0.5,
                                "output_per_1m": 30.0,
                            }
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    pricing = load_manual_chatgpt_model_pricing(str(manual_path))

    assert pricing["gpt-5.5"]["pricing"]["output_per_1m"] == 30.0
    assert pricing["gpt-5.5"]["service_tiers"]["fast"]["output_per_1m"] == 30.0


def test_checked_in_manual_chatgpt_models_are_empty() -> None:
    """The stale gpt-5.5 manual fallback was removed; the checked-in manual
    models file no longer publishes any model (upstream catalogs cover them)."""
    from openai_responses_plugins.openai_responses_codex_models import (
        default_manual_models_path,
    )

    payload = json.loads(default_manual_models_path().read_text(encoding="utf-8"))
    assert payload["models"] == {}


def test_checked_in_codex_snapshot_lists_gpt_6_family_and_daybreak() -> None:
    """The refreshed snapshot includes the GPT-6 family (astra, sol, luna)
    and both daybreak models, and no longer lists the retired gpt-5.2,
    gpt-5.4-mini, or gpt-5.4 entries."""
    from openai_responses_plugins.openai_responses_codex_models import (
        default_snapshot_path,
    )

    payload = json.loads(default_snapshot_path().read_text(encoding="utf-8"))
    models = payload["models"]
    for model in (
        "gpt-6-astra",
        "gpt-6-sol",
        "gpt-6-luna",
        "gpt-daybreak-blue-latest",
        "gpt-daybreak-red-latest",
        "gpt-5.6-sol",
        "gpt-5.6-terra",
        "gpt-5.6-luna",
        "gpt-5.5",
    ):
        assert model in models, f"missing {model} in checked-in snapshot"
    assert "gpt-5.2" not in models
    assert "gpt-5.4-mini" not in models
    # gpt-5.4 was retired upstream 2026-09-24 (694d8d45bd3d, #47932).
    assert "gpt-5.4" not in models
    assert models["gpt-6-astra"]["name"] == "GPT-6-Astra"
    assert models["gpt-6-sol"]["name"] == "GPT-6-Sol"
    assert models["gpt-6-luna"]["name"] == "GPT-6-Luna"


def test_build_snapshot_payload_writes_sorted_model_mapping() -> None:
    payload = build_snapshot_payload(
        fetched_at="2026-03-15T00:00:00+00:00",
        source_commit="abc123",
        model_entries=[
            {"id": "gpt-5.6", "name": "gpt-5.6"},
            {"id": "gpt-5.4", "name": "gpt-5.4"},
        ],
    )

    assert list(payload["models"]) == ["gpt-5.4", "gpt-5.6"]
    assert payload["source_commit"] == "abc123"


def test_refresh_models_snapshot_writes_payload(monkeypatch, tmp_path: Path) -> None:
    output_path = tmp_path / "models.json"

    monkeypatch.setattr(
        "refresh_openai_responses_models.build_live_snapshot_payload",
        lambda timeout: {
            "version": 1,
            "fetched_at": "2026-03-15T00:00:00+00:00",
            "source_base_url": "https://raw.githubusercontent.com/openai/codex",
            "source_commit": "abc123",
            "models": {
                "gpt-5.4": {
                    "id": "gpt-5.4",
                    "name": "gpt-5.4",
                }
            },
        },
    )

    refresh_snapshot(output_path, timeout=5.0)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["models"]["gpt-5.4"]["name"] == "gpt-5.4"
    assert payload["source_commit"] == "abc123"


def test_normalize_model_descriptor_maps_slug_and_display_name() -> None:
    descriptor = normalize_model_descriptor(
        {
            "slug": "gpt-5.6-sol",
            "display_name": "GPT-5.6-Sol",
            "description": "Latest frontier agentic coding model.",
        }
    )

    assert descriptor == {
        "id": "gpt-5.6-sol",
        "name": "GPT-5.6-Sol",
        "description": "Latest frontier agentic coding model.",
    }


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "not-a-dict",
        {"name": "missing id"},
        {"slug": "   "},
        {"id": ""},
    ],
)
def test_normalize_model_descriptor_drops_blank_or_missing_id(raw: object) -> None:
    assert normalize_model_descriptor(raw) is None


def test_normalize_models_payload_rejects_non_list_models() -> None:
    with pytest.raises(RuntimeError, match="missing models list"):
        normalize_models_payload({"models": {"gpt-5.6": {}}})


def test_merge_model_descriptors_preserves_earlier_only_ids_and_sorts() -> None:
    merged = merge_model_descriptors(
        [{"id": "gpt-5.5", "name": "manual 5.5"}],
        [{"id": "gpt-5.6-sol", "name": "snapshot sol"}],
        [{"id": "gpt-5.6-sol", "name": "live sol"}],
    )

    assert merged == [
        {"id": "gpt-5.5", "name": "manual 5.5"},
        {"id": "gpt-5.6-sol", "name": "live sol"},
    ]


def test_build_snapshot_payload_records_source_commit_and_sorts() -> None:
    payload = build_snapshot_payload(
        fetched_at="2026-07-13T00:00:00+00:00",
        source_commit="2f7d89b1419bf7064346855b0acde23514b1ebc5",
        model_entries=[
            {
                "slug": "gpt-5.6-terra",
                "display_name": "GPT-5.6-Terra",
                "description": "Balanced agentic coding model for everyday work.",
            },
            {
                "slug": "gpt-5.6-sol",
                "display_name": "GPT-5.6-Sol",
                "description": "Latest frontier agentic coding model.",
            },
            {
                "slug": "gpt-5.6-luna",
                "display_name": "GPT-5.6-Luna",
                "description": "Fast and affordable agentic coding model.",
            },
            {
                "slug": "gpt-5.5",
                "display_name": "GPT-5.5",
                "description": "Frontier model for complex coding, research, and real-world work.",
            },
        ],
    )

    assert payload["source_commit"] == "2f7d89b1419bf7064346855b0acde23514b1ebc5"
    assert list(payload["models"]) == [
        "gpt-5.5",
        "gpt-5.6-luna",
        "gpt-5.6-sol",
        "gpt-5.6-terra",
    ]
    assert payload["models"]["gpt-5.6-sol"] == {
        "id": "gpt-5.6-sol",
        "name": "GPT-5.6-Sol",
        "description": "Latest frontier agentic coding model.",
    }
    assert payload["models"]["gpt-5.6-terra"] == {
        "id": "gpt-5.6-terra",
        "name": "GPT-5.6-Terra",
        "description": "Balanced agentic coding model for everyday work.",
    }
    assert payload["models"]["gpt-5.6-luna"] == {
        "id": "gpt-5.6-luna",
        "name": "GPT-5.6-Luna",
        "description": "Fast and affordable agentic coding model.",
    }


def test_build_snapshot_payload_omits_source_commit_when_absent() -> None:
    payload = build_snapshot_payload(
        fetched_at="2026-07-13T00:00:00+00:00",
        source_commit=None,
        model_entries=[{"id": "gpt-5.4", "name": "gpt-5.4"}],
    )

    assert "source_commit" not in payload


def test_refresh_models_snapshot_preserves_gpt_5_6_family(
    monkeypatch, tmp_path: Path
) -> None:
    output_path = tmp_path / "models.json"

    monkeypatch.setattr(
        "refresh_openai_responses_models.build_live_snapshot_payload",
        lambda timeout: {
            "version": 1,
            "fetched_at": "2026-07-13T00:00:00+00:00",
            "source_base_url": "https://raw.githubusercontent.com/openai/codex",
            "source_commit": "2f7d89b1419bf7064346855b0acde23514b1ebc5",
            "models": {
                "gpt-5.6-luna": {
                    "id": "gpt-5.6-luna",
                    "name": "GPT-5.6-Luna",
                    "description": "Fast and affordable agentic coding model.",
                },
                "gpt-5.6-sol": {
                    "id": "gpt-5.6-sol",
                    "name": "GPT-5.6-Sol",
                    "description": "Latest frontier agentic coding model.",
                },
                "gpt-5.6-terra": {
                    "id": "gpt-5.6-terra",
                    "name": "GPT-5.6-Terra",
                    "description": "Balanced agentic coding model for everyday work.",
                },
            },
        },
    )

    refresh_snapshot(output_path, timeout=5.0)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["source_commit"] == "2f7d89b1419bf7064346855b0acde23514b1ebc5"
    assert list(payload["models"]) == ["gpt-5.6-luna", "gpt-5.6-sol", "gpt-5.6-terra"]
    for model_id in ("gpt-5.6-luna", "gpt-5.6-sol", "gpt-5.6-terra"):
        entry = payload["models"][model_id]
        assert entry["id"] == model_id
        assert isinstance(entry["name"], str) and entry["name"]
        assert isinstance(entry["description"], str) and entry["description"]
