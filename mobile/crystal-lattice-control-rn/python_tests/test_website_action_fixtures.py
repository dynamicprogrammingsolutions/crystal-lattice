from __future__ import annotations

import json
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