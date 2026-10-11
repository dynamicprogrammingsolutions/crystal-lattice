from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path

from website_report_fixture import WebsiteReportFixturePlugin

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "landing_page" / "visual_assets" / "runtime" / "proof-batch"


def test_illustrative_report_matches_approved_ranges_and_weekly_assumption() -> None:
    plugin = WebsiteReportFixturePlugin()
    state = plugin.init({})
    result = plugin.execute_action(None, "show_illustrative_usage", {}, None, state)
    data = result["illustrative_data"]
    assert len(data["daily_costs"]) == 3
    for row in data["daily_costs"]:
        assert Decimal("20") <= Decimal(row["claude"]) <= Decimal("50")
        assert Decimal("2") <= Decimal(row["zai"]) <= Decimal("10")
        assert f"${Decimal(row['claude']):.2f}" in result["display"]["body"]
        assert f"${Decimal(row['zai']):.2f}" in result["display"]["body"]
    usage = data["chatgpt"]
    start = datetime.fromisoformat(usage["since_reset"])
    current = datetime.fromisoformat(usage["captured_at"])
    end = datetime.fromisoformat(usage["weekly_resets_at"])
    assert (current - start).days == 3
    assert (end - start).days == 7
    assert result["metrics"]["estimated_total_usd"] == "220.00"
    assert result["metrics"]["weekly_capacity_assumption_usd"] == "550.00"
    assert result["metrics"]["percentage_point_change"] == 40
    assert "0% → 40%" in result["display"]["body"]
    assert "since reset" in result["display"]["body"]
    assert "illustrative" in result["sample_notice"].lower()


def test_codex_beginning_has_pinned_public_provenance_and_no_fixture_preamble() -> None:
    source = json.loads((FIXTURES / "codex-default-source.json").read_text())
    text = (FIXTURES / "codex-default-beginning.md").read_text()
    assert source["model"] == "gpt-6-astra"
    assert source["source_commit"] in source["source_url"]
    assert source["source_url"].startswith("https://github.com/openai/codex/")
    assert text.startswith("You are Codex, an agent based on GPT-6.")
    assert "# When to ask the user for permission" in text
    assert "Research and operations agent" not in text