from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

import pytest
from dotenv import load_dotenv

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_MANUAL_STATE_DIR = Path(__file__).resolve().parent / ".manual-state"


def _plugin_entry(repo_name: str, entry: str) -> Dict[str, str]:
    return {"path": str(REPO_ROOT / "plugins" / repo_name), "entry": entry}


def _manual_state_dir() -> Path:
    raw = os.getenv("CHATGPT_TEST_STATE_DIR")
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()
    return _DEFAULT_MANUAL_STATE_DIR


def _credentials_path() -> Path:
    return _manual_state_dir() / "auth" / "chatgpt-auth.json"


def _rate_limits_path() -> Path:
    return _manual_state_dir() / "auth" / "chatgpt-rate-limits.json"


def _usage_journal_path() -> Path:
    return _manual_state_dir() / "auth" / "chatgpt-usage-journal.ndjson"


def _load_saved_credentials() -> dict[str, object]:
    path = _credentials_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        pytest.skip(f"saved ChatGPT login not found at {path}")
    if not isinstance(payload, dict):
        pytest.skip(f"saved ChatGPT login at {path} is not a JSON object")
    return payload


def _write_config(state_dir: Path) -> Path:
    model = os.getenv("OPENAI_RESPONSES_CHATGPT_MODEL") or "gpt-5.6-luna"
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(state_dir / ".plugin_cache"),
        "providers": {
            "chatgpt": {
                "provider": "openai_responses",
                "model": model,
                "auth_mode": "chatgpt",
                "chatgpt_credentials_path": "${env:CONFIG_DIR}/auth/chatgpt-auth.json",
                "chatgpt_rate_limits_path": "${env:CONFIG_DIR}/auth/chatgpt-rate-limits.json",
                "chatgpt_base_url": os.getenv("OPENAI_CHATGPT_BASE_URL")
                or "https://chatgpt.com/backend-api/codex",
                "system_message_as_instructions": True,
                "strip_leading_system_or_developer_message": True,
                "system_message": "You are a precise assistant. Reply exactly with the requested text.",
                "timeout": 120,
                "working_directory": ".",
                "cost_tracking_db_path": str(
                    state_dir / "cost-tracking" / "cost-tracking.sqlite3"
                ),
            }
        },
        "plugins": [
            _plugin_entry("chatgpt-auth-app", "chatgpt_auth_app.ChatGPTAuthAppPlugin"),
            _plugin_entry(
                "openai_responses", "openai_responses_plugins.OpenAIResponsesProvider"
            ),
            _plugin_entry(
                "openai_responses",
                "openai_responses_plugins.OpenAIResponsesUsageExtension",
            ),
            _plugin_entry(
                "cost-tracking",
                "cost_tracking_plugins.cost_tracking_extension.CostTrackingExtension",
            ),
            _plugin_entry(
                "openai_responses",
                "openai_responses_plugins.OpenAIResponsesChatGPTAuthFeature",
            ),
            _plugin_entry(
                "feature-system-message",
                "feature_system_message.system_message_feature.SystemMessageFeature",
            ),
        ],
        "agents": {
            "default": {"provider": "chatgpt"},
        },
        "application": {
            "chatgpt_auth": {
                "credentials_path": "${env:CONFIG_DIR}/auth/chatgpt-auth.json",
                "rate_limits_path": "${env:CONFIG_DIR}/auth/chatgpt-rate-limits.json",
            }
        },
    }
    path = state_dir / "config_chatgpt_account_status_manual.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_chatgpt_account_status_after_real_request() -> None:
    load_dotenv(REPO_ROOT / ".env")

    state_dir = _manual_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    _load_saved_credentials()

    rate_limits_path = _rate_limits_path()
    rate_limits_path.unlink(missing_ok=True)

    config_path = _write_config(state_dir)
    app = AgentApplication(
        str(config_path),
        str(state_dir / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides={"CONFIG_DIR": str(state_dir)},
    )

    core, base_config, session = app.create_session("default")
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: CHATGPT_ACCOUNT_STATUS_OK",
        config=base_config,
    )
    app.save_session(session)

    final_seen = False
    final_messages = None
    for event in app.send_request(core, session, base_config, stream=True):
        if event.get("type") == "final":
            final_seen = True
            final_messages = event.get("messages")

    assert final_seen, "expected final event from real ChatGPT-backed request"
    assert (
        rate_limits_path.exists()
    ), "expected ChatGPT rate-limit sidecar to be captured"

    saved_limits = json.loads(rate_limits_path.read_text(encoding="utf-8"))
    snapshots = saved_limits.get("snapshots")
    assert (
        isinstance(snapshots, list) and snapshots
    ), "expected non-empty rate-limit snapshots"

    result = app.execute_application_action(
        "chatgpt_auth",
        "show_account_status",
        {"session_id": session.session_id},
    )
    body = result["display"]["body"]
    assert "Effective auth mode: `chatgpt`" in body
    assert "Usage limits:" in body
    assert (
        "5h limit:" in body
        or "Weekly limit:" in body
        or "Monthly limit:" in body
        or "Credits:" in body
    )

    # The append-only usage journal must have grown end to end and the
    # account status must show the since-reset estimated usage.
    journal_path = _usage_journal_path()
    assert journal_path.exists(), "expected ChatGPT usage journal to be created"
    journal_records = [
        json.loads(line)
        for line in journal_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    request_records = [
        record for record in journal_records if record.get("type") == "request_usage"
    ]
    snapshot_records = [
        record
        for record in journal_records
        if record.get("type") == "rate_limit_snapshot"
    ]
    assert request_records, "expected request usage records in the journal"
    assert snapshot_records, "expected rate-limit snapshot records in the journal"
    assert isinstance(
        request_records[-1].get("rate_limits"), dict
    ), "expected the request record to carry the rate-limit snapshot"
    assert "Estimated usage since reset:" in body
    assert "Requests: `" in body

    # The simplified summary CSV is appended alongside the journal and the
    # request rows carry the session id and absolute working directory. The
    # journal is shared with other live sessions, so look for this session's
    # own rows rather than the last row.
    summary_path = state_dir / "auth" / "chatgpt-usage-summary.csv"
    assert summary_path.exists(), "expected the ChatGPT usage summary CSV"
    import csv

    with open(summary_path, encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))
    request_rows = [row for row in summary_rows if row["estimated_cost"] != ""]
    assert request_rows, "expected request rows in the summary CSV"
    own_rows = [row for row in request_rows if row["session_id"] == session.session_id]
    assert own_rows, "expected this session's rows in the summary CSV"
    assert own_rows[-1]["working_directory"].startswith("/")

    # The generic cost tracking store records this session's request under
    # the provider-defined ChatGPT bucket, and the store-backed session total
    # reaches the assistant message metadata for the chat status bar.
    cost_db_path = state_dir / "cost-tracking" / "cost-tracking.sqlite3"
    assert cost_db_path.exists(), "expected the cost tracking SQLite store"
    import sqlite3

    conn = sqlite3.connect(str(cost_db_path))
    try:
        cost_rows = conn.execute(
            "SELECT bucket, session_id, working_directory FROM cost_requests "
            "WHERE session_id = ?",
            (session.session_id,),
        ).fetchall()
    finally:
        conn.close()
    assert cost_rows, "expected this session's rows in the cost store"
    workspace = os.path.abspath(".")
    for bucket, _row_session_id, row_wd in cost_rows:
        assert bucket == "openai-responses-chatgpt"
        assert row_wd == workspace
    # The application event stream serializes final messages as plain dicts.
    assistants = [
        message
        for message in (final_messages or [])
        if isinstance(message, dict) and message.get("role") == "assistant"
    ]
    assert assistants, "expected an assistant message in the final event messages"
    final_metadata = assistants[-1].get("metadata") or {}
    assert isinstance(final_metadata.get("cost_session_total_formatted"), str)
    assert final_metadata.get("cost_session_requests", 0) >= 1

    # The usage report action must render totals and keep the date-range
    # follow-up form wired to the same action.
    report = app.execute_application_action(
        "chatgpt_auth",
        "show_usage_report",
        {"session_id": session.session_id},
    )
    report_body = report["display"]["body"]
    assert "Estimated usage:" in report_body
    assert "Requests: `" in report_body
    assert "Usage percent history:" in report_body
    form = report["display"].get("form") or {}
    assert form.get("kind") == "form"
    assert [entry["name"] for entry in form.get("inputs", [])] == ["from", "to"]
    followup = (report["display"].get("actions") or [{}])[0]
    assert followup.get("kind") == "run_action"
    assert followup.get("action_id") == "show_usage_report"
    assert followup.get("param_map") == {"from": "$form.from", "to": "$form.to"}
