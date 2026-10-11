#!/usr/bin/env python3
"""Generate sanitized website action-display fixtures through real plugins."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
CORE_PYTHON = REPO_ROOT / "core" / "python"
COST_TRACKING_SRC = REPO_ROOT / "plugins" / "cost-tracking" / "src"
for source_root in (CORE_PYTHON, COST_TRACKING_SRC):
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))

from agent_app.application_future import AgentApplication  # noqa: E402
from cost_tracking_plugins import cost_store  # noqa: E402


DEFAULT_OUTPUT = (
    REPO_ROOT
    / "mobile"
    / "crystal-lattice-control-rn"
    / "src"
    / "testing"
    / "fixtures"
    / "websiteActionDisplays.json"
)

COMPILED_SYSTEM_MESSAGE = """# Research and operations agent

Use the configured source-reading, web-research, and structured-output tools.

Before recommending a launch approach:

1. inspect the supplied files and notes;
2. verify time-sensitive facts against cited external sources;
3. separate evidence, assumptions, risks, and open questions;
4. compare viable alternatives using explicit criteria;
5. produce a concise recommendation and a two-week validation plan.

Preserve citations and identify any conclusion that depends on incomplete
evidence."""

GENERIC_PROJECTS = {
    "Research brief": {"name": "Research brief"},
    "Operations plan": {"name": "Operations plan"},
}

def prepare_report_runtime(root: Path) -> dict[str, Any]:
    """Seed owned report inputs; production actions calculate their output."""
    root.mkdir(parents=True, exist_ok=True)
    auth = root / "auth"
    auth.mkdir(exist_ok=True)
    (root / "projects.json").write_text(
        json.dumps({"projects": GENERIC_PROJECTS}), encoding="utf-8"
    )
    now = datetime.now(timezone.utc).replace(microsecond=0)
    db_path = root / "costs.sqlite3"
    records = [
        ("OpenAI-api", "Research brief", 1.27, 4),
        ("OpenAI-api", "Research brief", 0.63, 2),
        ("OpenRouter", "Operations plan", 0.84, 1),
        ("OpenRouter", "Operations plan", 0.42, 0),
    ]
    for index, (bucket, project, amount, days) in enumerate(records):
        cost_store.record_request_usage(
            db_path,
            time=(now - timedelta(days=days)).isoformat(),
            bucket=bucket,
            session_id="research-brief" if project == "Research brief" else "operations-plan",
            working_directory=project,
            model="sample-model",
            response_id=f"website-proof-{index}",
            input_tokens=4200 + index * 600,
            cached_tokens=1200,
            output_tokens=350 + index * 50,
            **({"actual_cost": amount} if index < 2 else {"estimated_cost": amount}),
        )
    journal = [{
        "type": "usage_reset",
        "timestamp": (now - timedelta(days=5)).isoformat(),
        "source": "chatgpt_auth_app",
    }]
    for index, percent in enumerate((12, 24, 35)):
        moment = now - timedelta(hours=2 - index)
        journal.append({
            "type": "request_usage",
            "timestamp": moment.isoformat(),
            "response_id": f"website-chatgpt-{index}",
            "session_id": "research-brief",
            "working_directory": "Research brief",
            "model": "sample-model",
            "input_tokens": 8400 + index * 1800,
            "cached_tokens": 2400,
            "cache_write_tokens": 0,
            "output_tokens": 650 + index * 100,
            "reasoning_tokens": 300 + index * 50,
            "estimated_cost": (0.42, 0.63, 0.77)[index],
            "rate_limits": {
                "captured_at": moment.isoformat(),
                "snapshots": [{
                    "limit_id": "codex",
                    "primary": {
                        "used_percent": percent,
                        "window_minutes": 300,
                        "resets_at": int((now + timedelta(hours=3)).timestamp()),
                    },
                    "secondary": {
                        "used_percent": 18 + index * 3,
                        "window_minutes": 10080,
                        "resets_at": int((now + timedelta(days=4)).timestamp()),
                    },
                }],
            },
        })
    journal_path = auth / "chatgpt-usage-journal.ndjson"
    journal_path.write_text(
        "".join(json.dumps(record) + "\n" for record in journal), encoding="utf-8"
    )
    limits_path = auth / "chatgpt-rate-limits.json"
    limits_path.write_text(json.dumps(journal[-1]["rate_limits"]), encoding="utf-8")
    result = {
        "captured_at": now.isoformat(),
        "cost_total": sum(record[2] for record in records),
        "cost_requests": len(records),
        "chatgpt_estimated_cost": 1.82,
        "chatgpt_requests": 3,
        "chatgpt_input_tokens": 30600,
        "journal": journal,
    }
    (root / "seed-contract.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def _response(
    *,
    plugin: str,
    action_id: str,
    action_owner: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": "ok",
        "plugin": plugin,
        "action_id": action_id,
        "action_owner": action_owner,
        "result": result,
    }


def _find_action(
    elements: list[dict[str, Any]],
    *,
    action_id: str,
    action_owner: str | None = None,
) -> dict[str, Any]:
    for element in elements:
        if element.get("action_id") != action_id:
            continue
        if action_owner is not None and element.get("action_owner") != action_owner:
            continue
        return element
    raise RuntimeError(f"Action UI element not found: {action_id}")


def _seed_costs(db_path: Path) -> None:
    today = datetime.now().astimezone().date()
    rows = [
        {
            "bucket": "openai-responses-chatgpt",
            "session_id": "launch-research",
            "working_directory": "Research brief",
            "model": "gpt-5.4-mini",
            "response_id": "fixture-response-1",
            "actual_cost": 0.018577,
            "days_ago": 2,
        },
        {
            "bucket": "openai-responses-chatgpt",
            "session_id": "launch-research",
            "working_directory": "Research brief",
            "model": "gpt-5.4-mini",
            "response_id": "fixture-response-2",
            "actual_cost": 0.024316,
            "days_ago": 1,
        },
        {
            "bucket": "openrouter-api",
            "session_id": "source-review",
            "working_directory": "Operations plan",
            "model": "z-ai/glm-5.3",
            "response_id": "fixture-response-3",
            "estimated_cost": 0.011204,
            "days_ago": 0,
        },
    ]
    for row in rows:
        moment = datetime.combine(
            today - timedelta(days=int(row.pop("days_ago"))),
            datetime.min.time().replace(hour=12),
            tzinfo=timezone.utc,
        )
        cost_store.record_request_usage(
            db_path,
            time=moment.isoformat(),
            **row,
        )


def build_fixture() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="crystal-lattice-website-actions-") as tmp:
        root = Path(tmp)
        data_dir = root / "crystal-data"
        data_dir.mkdir(parents=True)
        (data_dir / "projects.json").write_text(
            json.dumps({"projects": GENERIC_PROJECTS}),
            encoding="utf-8",
        )
        db_path = root / "costs.sqlite3"
        config_path = root / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "plugin_cache_dir": str(root / "plugin-cache"),
                    "providers": {
                        "echo": {
                            "provider": "echo_openai_like",
                            "model": "fixture-model",
                            "system_message_as_instructions": True,
                            "system_message": {
                                "template": COMPILED_SYSTEM_MESSAGE,
                            },
                        }
                    },
                    "plugins": [
                        "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
                        f"path:{REPO_ROOT / 'plugins' / 'feature-system-message'}",
                        f"path:{REPO_ROOT / 'plugins' / 'cost-tracking'}",
                    ],
                    "agents": {
                        "default": {
                            "provider": "echo",
                            "cost_tracking_db_path": str(db_path),
                        }
                    },
                    "application": {"cost_tracking": {}},
                }
            ),
            encoding="utf-8",
        )

        previous_data_dir = os.environ.get("CRYSTAL_DATA_DIR")
        os.environ["CRYSTAL_DATA_DIR"] = str(data_dir)
        app = AgentApplication(str(config_path), str(root / "sessions"))
        try:
            core, base_config, session = app.create_session("default")
            compiled_element = _find_action(
                core.get_ui_schema(config=base_config),
                action_id="show_compiled_system_message",
                action_owner="feature",
            )
            compiled_result = app.execute_action(
                "system_message",
                "show_compiled_system_message",
                {"session_id": session.session_id},
                action_owner="feature",
                context={"session_id": session.session_id},
            )

            _seed_costs(db_path)
            session_app_elements = app.get_session_application_ui_schema(
                session.session_id
            )
            cost_element = _find_action(
                session_app_elements,
                action_id="show_cost_report",
            )
            cost_definition = next(
                action
                for action in app.get_application_actions()
                if action.get("plugin") == "cost_tracking_app"
                and action.get("id") == "show_cost_report"
            )
            cost_result = app.execute_action(
                "cost_tracking_app",
                "show_cost_report",
                {"session_id": session.session_id},
                action_owner="application",
                context={"session_id": session.session_id},
            )
        finally:
            app.close()
            if previous_data_dir is None:
                os.environ.pop("CRYSTAL_DATA_DIR", None)
            else:
                os.environ["CRYSTAL_DATA_DIR"] = previous_data_dir

    fixture = {
        "schema_version": 1,
        "synthetic_cost_notice": (
            "Illustrative values generated from deterministic generic records; "
            "not company spending or provider invoices."
        ),
        "compiled_system_message": {
            "ui_element": compiled_element,
            "response": _response(
                plugin="system_message",
                action_id="show_compiled_system_message",
                action_owner="feature",
                result=compiled_result,
            ),
        },
        "cost_report": {
            "action_definition": cost_definition,
            "ui_element": cost_element,
            "response": _response(
                plugin="cost_tracking_app",
                action_id="show_cost_report",
                action_owner="application",
                result=cost_result,
            ),
        },
    }
    encoded = json.dumps(fixture, sort_keys=True)
    forbidden = [tmp, str(Path.home()), "api_key", "token", "secret"]
    for value in forbidden:
        if value and value in encoded:
            raise RuntimeError(f"Generated fixture contains forbidden value: {value}")
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--prepare-runtime", type=Path)
    args = parser.parse_args()
    if args.prepare_runtime is not None:
        prepare_report_runtime(args.prepare_runtime.resolve())
        return 0

    fixture = build_fixture()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(fixture, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())