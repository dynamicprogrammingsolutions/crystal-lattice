from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parents[3]
    path = root / "scripts" / "openai_responses_tier_matrix_store.py"
    spec = importlib.util.spec_from_file_location("openai_responses_tier_matrix_store", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_aggregate_records_groups_by_profile_model_and_case() -> None:
    module = _load_module()

    summaries = module.aggregate_records(
        [
            {
                "profile": "standard-3k-500",
                "model": "gpt-5.4",
                "case_name": "api-default",
                "auth_mode": "api",
                "status": "ok",
                "turn_tps": 80.0,
                "duration_seconds": 7.0,
            },
            {
                "profile": "standard-3k-500",
                "model": "gpt-5.4",
                "case_name": "api-default",
                "auth_mode": "api",
                "status": "ok",
                "turn_tps": 100.0,
                "duration_seconds": 5.0,
            },
            {
                "profile": "standard-3k-500",
                "model": "gpt-5.4",
                "case_name": "api-default",
                "auth_mode": "api",
                "status": "error",
                "turn_tps": None,
                "duration_seconds": None,
            },
        ]
    )

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary["profile"] == "standard-3k-500"
    assert summary["model"] == "gpt-5.4"
    assert summary["case_name"] == "api-default"
    assert summary["runs"] == 3
    assert summary["successes"] == 2
    assert summary["errors"] == 1
    assert summary["mean_tps"] == 90.0
    assert summary["min_tps"] == 80.0
    assert summary["max_tps"] == 100.0


def test_parse_text_artifact_reads_run_blocks(tmp_path: Path) -> None:
    module = _load_module()

    artifact = tmp_path / "artifact.txt"
    artifact.write_text(
        "\n".join(
            [
                "models=gpt-5.4",
                "started_at=2026-01-01T00:00:00+00:00",
                "repeat=1",
                "execution_mode=sequential",
                "max_workers=2",
                "run_scope=api",
                "desired_input_tokens=3000",
                "desired_output_tokens=500",
                "",
                "[model=gpt-5.4 case=api-default repeat=1]",
                "auth_mode=api",
                "status=ok",
                "reported_service_tier=default",
                "effective_auth_mode=api",
                "duration_seconds=7.5",
                "input_tokens=4000",
                "output_tokens=590",
                "tps=78.6",
                "output_chars=1700",
                "approx_input_tokens_target=3015",
                "approx_output_tokens_target=521",
                "approx_context_tokens=2365",
                "",
                "[summary]",
                "ignored=true",
            ]
        ),
        encoding="utf-8",
    )

    records = module.parse_text_artifact(artifact, profile="standard-3k-500")

    assert len(records) == 1
    record = records[0]
    assert record["profile"] == "standard-3k-500"
    assert record["model"] == "gpt-5.4"
    assert record["case_name"] == "api-default"
    assert record["requested_tier"] == "default"
    assert record["duration_seconds"] == 7.5
    assert record["turn_tps"] == 78.6