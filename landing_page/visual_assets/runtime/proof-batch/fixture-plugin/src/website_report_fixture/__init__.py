"""Capture-only report plugin; never included in product default configuration."""

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
from typing import Any


def render_report(data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    usage = data["chatgpt"]
    capacity = Decimal(usage["illustrative_weekly_capacity_usd"])
    current = Decimal(str(usage["current_percent"]))
    start = Decimal(str(usage["start_percent"]))
    estimated = capacity * (current - start) / 100
    lines = [
        "### Daily costs by bucket",
        "",
        "| Day | claude | zai |",
        "| --- | --- | --- |",
        *[
            f"| {row['day']} | ${Decimal(row['claude']):.2f} | ${Decimal(row['zai']):.2f} |"
            for row in data["daily_costs"]
        ],
        "",
        "### ChatGPT · since reset",
        "",
        usage["period_label"],
        "",
        f"Estimated total: **${estimated:.2f}**",
        "",
        f"Weekly usage: **{start:g}% → {current:g}%**",
        "",
        f"Change: **+{current - start:g} percentage points**",
    ]
    return "\n".join(lines), {
        "estimated_total_usd": f"{estimated:.2f}",
        "percentage_point_change": float(current - start),
        "weekly_capacity_assumption_usd": f"{capacity:.2f}",
        "days_since_reset": 3,
    }


class WebsiteReportFixturePlugin:
    name = "website_report_fixture"
    version = "0.1.0"

    def init(self, app_config: dict[str, Any]) -> dict[str, Any]:
        return {"data": json.loads(Path(__file__).with_name("reports.json").read_text())}

    def get_config_schema(self) -> dict[str, Any]:
        return {}

    def get_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        return [{
            "id": "show_illustrative_usage",
            "label": "Show illustrative usage",
            "inputs": {"session_id": {"type": "string", "required": True}},
        }]

    def get_ui_elements(self, state: dict[str, Any], config=None, context=None) -> list[dict[str, Any]]:
        return [{
            "ui_type": "session_action",
            "id": "website_show_usage",
            "label": "Costs and usage",
            "icon": "bar-chart-2",
            "order": 20,
            "action_id": "show_illustrative_usage",
            "param_map": {"session_id": "$session.session_id"},
            "dialog": {"kind": "none"},
        }]

    def execute_action(self, app, action_id: str, params, context, state: dict[str, Any]) -> dict[str, Any]:
        if action_id != "show_illustrative_usage":
            raise ValueError(f"Unknown fixture action: {action_id}")
        body, metrics = render_report(state["data"])
        return {
            "display": {
                "display_id": "website-illustrative-usage",
                "title": "Costs and ChatGPT usage",
                "format": "markdown",
                "body": body,
                "dismissible": True,
            },
            "illustrative_data": state["data"],
            "metrics": metrics,
            "sample_notice": state["data"]["sample_notice"],
        }