from __future__ import annotations

import json
import importlib.util
from pathlib import Path


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "testing"
    / "fixtures"
    / "websiteActionDisplays.json"
)


def test_website_action_displays_are_real_sanitized_contracts() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    compiled = payload["compiled_system_message"]
    assert compiled["ui_element"]["action_owner"] == "feature"
    assert compiled["ui_element"]["action_id"] == "show_compiled_system_message"
    assert compiled["response"]["plugin"] == "system_message"
    assert compiled["response"]["result"]["display"]["display_id"] == (
        "compiled-system-message"
    )
    assert "two-week validation plan" in compiled["response"]["result"]["display"][
        "body"
    ]

    cost = payload["cost_report"]
    assert cost["ui_element"]["plugin"] == "cost_tracking_app"
    assert cost["ui_element"]["action_id"] == "show_cost_report"
    assert cost["response"]["action_owner"] == "application"
    result = cost["response"]["result"]
    assert result["display"]["display_id"] == "cost-tracking-report"
    assert result["report"]["request_count"] == 3
    assert result["report"]["total_cost"] == 0.054097
    assert "Research brief" in result["display"]["body"]
    assert "Operations plan" in result["display"]["body"]
    assert "not company spending" in payload["synthetic_cost_notice"]

    encoded = json.dumps(payload)
    assert "/Users/" not in encoded
    assert "/private/" not in encoded
    assert "api_key" not in encoded
    assert "secret" not in encoded


def test_report_runtime_is_synthetic_and_preserves_numeric_token_counts(tmp_path: Path) -> None:
    generator = Path(__file__).resolve().parents[1] / "scripts" / "generate_website_action_fixtures.py"
    spec = importlib.util.spec_from_file_location("website_action_generator", generator)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    contract = module.prepare_report_runtime(tmp_path)
    journal = [
        json.loads(line)
        for line in (tmp_path / "auth" / "chatgpt-usage-journal.ndjson").read_text().splitlines()
    ]
    assert journal[0]["type"] == "usage_reset"
    requests = journal[1:]
    assert sum(row["input_tokens"] for row in requests) == contract["chatgpt_input_tokens"]
    assert sum(row["estimated_cost"] for row in requests) == contract["chatgpt_estimated_cost"]
    assert all(isinstance(row["cached_tokens"], int) for row in requests)
    assert (tmp_path / "costs.sqlite3").exists()
    assert not (tmp_path / "auth" / "absent-credentials.json").exists()
    forbidden = {"access_token", "refresh_token", "id_token", "api_key", "password", "private_key"}

    def inspect(value: object) -> None:
        if isinstance(value, dict):
            assert not forbidden.intersection(value)
            for item in value.values():
                inspect(item)
        elif isinstance(value, list):
            for item in value:
                inspect(item)
        elif isinstance(value, str):
            assert "/Users/" not in value and "/private/" not in value

    inspect(contract)
    inspect(json.loads((tmp_path / "auth" / "chatgpt-rate-limits.json").read_text()))
