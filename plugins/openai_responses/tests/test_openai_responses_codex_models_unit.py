from __future__ import annotations

import json
from pathlib import Path

from openai_responses_plugins.openai_responses_codex_models import (
    build_snapshot_payload,
    load_snapshot_model_descriptors,
    merge_model_descriptors,
)
from scripts.refresh_openai_responses_models import refresh_snapshot


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
        "scripts.refresh_openai_responses_models.build_live_snapshot_payload",
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