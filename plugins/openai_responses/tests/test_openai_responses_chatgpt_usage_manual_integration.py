from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from cost_tracking_plugins import cost_store
from cost_tracking_plugins.cost_tracking_extension import CostTrackingExtension
from feature_system_message.system_message_feature import SystemMessageFeature
from openai_responses_plugins import (
    OpenAIResponsesChatGPTAuthFeature,
    OpenAIResponsesProvider,
    OpenAIResponsesToolsExtension,
    OpenAIResponsesUsageExtension,
)
from plugins.math_tools import MathTools


REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CHATGPT_AUTH_STATE_DIR = (
    REPO_ROOT / "plugins" / "chatgpt-auth-app" / "tests" / ".manual-state"
)
pytestmark = pytest.mark.api


def _manual_state_dir() -> Path:
    raw = os.getenv("CHATGPT_TEST_STATE_DIR")
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()
    return _DEFAULT_CHATGPT_AUTH_STATE_DIR


def _credentials_path() -> Path:
    return _manual_state_dir() / "auth" / "chatgpt-auth.json"


def _usage_journal_path() -> Path:
    return _manual_state_dir() / "auth" / "chatgpt-usage-journal.ndjson"


def _usage_summary_csv_path() -> Path:
    return _manual_state_dir() / "auth" / "chatgpt-usage-summary.csv"


def _cost_db_path() -> Path:
    return _manual_state_dir() / "cost-tracking" / "cost-tracking.sqlite3"


def _journal_records() -> list[dict[str, Any]]:
    path = _usage_journal_path()
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _load_saved_credentials() -> dict[str, object]:
    path = _credentials_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        pytest.skip(f"saved ChatGPT login not found at {path}")
    if not isinstance(payload, dict):
        pytest.skip(f"saved ChatGPT login at {path} is not a JSON object")
    return payload


def _chatgpt_config(credentials_path: Path) -> dict[str, object]:
    model = os.getenv("OPENAI_RESPONSES_CHATGPT_MODEL") or "gpt-5.6-luna"
    return {
        "model": model,
        "auth_mode": "chatgpt",
        "chatgpt_credentials_path": str(credentials_path),
        "chatgpt_base_url": os.getenv("OPENAI_CHATGPT_BASE_URL")
        or "https://chatgpt.com/backend-api/codex",
        "system_message_as_instructions": True,
        "system_message": (
            "You are a precise assistant. "
            "When the user explicitly tells you to use a tool, you must call the tool before answering."
        ),
        "show_estimated_cached_tokens": True,
        "show_openai_auth_mode": True,
        "timeout": 180,
        "working_directory": ".",
        "cost_tracking_db_path": str(_cost_db_path()),
    }


def _send_streaming_request(
    core: AgentCore,
    session: Any,
    config: Dict[str, Any],
) -> Tuple[Any, List[Dict[str, Any]]]:
    final_session = None
    final_messages = None
    for chunk in core.send_request_stream(session, config):
        if chunk.get("type") == "final":
            final_session = chunk.get("session")
            final_messages = chunk.get("messages")
    assert final_session is not None, "expected final session from streaming request"
    assert (
        isinstance(final_messages, list) and final_messages
    ), "expected final messages from stream"
    return final_session, final_messages


def _response_native_items(session: Any, response_id: str) -> List[Dict[str, Any]]:
    native_history = (session.metadata or {}).get("native_messages") or []
    return [
        item
        for item in native_history
        if isinstance(item, dict)
        and isinstance(item.get("_metadata"), dict)
        and item["_metadata"].get("response_id") == response_id
    ]


def _assert_chatgpt_usage_metadata(message: Dict[str, Any], session: Any) -> int:
    metadata = message.get("metadata") or {}
    response_id = metadata.get("response_id")

    assert message.get("role") == "assistant"
    assert isinstance(response_id, str) and response_id
    assert isinstance(metadata.get("usage"), dict)
    assert metadata.get("usage_effective_auth_mode") == "chatgpt"
    assert metadata.get("usage_effective_auth_mode_label") == "ChatGPT"
    assert (
        metadata.get("usage_bucket") == "openai-responses-chatgpt"
    ), "expected the provider-defined ChatGPT cost bucket in usage metadata"
    assert isinstance(metadata.get("usage_estimated_cached_tokens"), int)
    assert isinstance(metadata.get("usage_estimated_cached_tokens_formatted"), str)
    assert "usage_cached_tokens_formatted" not in metadata
    assert isinstance(metadata.get("usage_total_cost"), (int, float))
    assert isinstance(metadata.get("usage_total_cost_formatted"), str)
    assert isinstance(metadata.get("usage_turn_cost_cumulative"), (int, float))
    assert isinstance(metadata.get("usage_turn_cost_cumulative_formatted"), str)

    response_native = _response_native_items(session, response_id)
    assert response_native, "expected persisted native items for assistant response"
    assert any(
        isinstance((item.get("_metadata") or {}).get("usage"), dict)
        for item in response_native
    ), "expected at least one native response item to carry usage metadata"

    return int(metadata["usage_estimated_cached_tokens"])


def _run_tool_turn_streaming(
    core: AgentCore,
    session: Any,
    config: Dict[str, Any],
    *,
    prompt: str,
    expected_text: str,
    max_iterations: int = 5,
) -> Tuple[Any, List[Dict[str, Any]], List[int]]:
    session = core.add_message(session, "user", prompt, config=config)
    assistant_turns: List[Dict[str, Any]] = []
    estimates: List[int] = []
    saw_tool_call = False

    for _ in range(max_iterations):
        session, responses = _send_streaming_request(core, session, config)
        assistant = responses[-1]
        assistant_turns.append(assistant)
        estimates.append(_assert_chatgpt_usage_metadata(assistant, session))

        tool_calls = (assistant.get("metadata") or {}).get("tool_calls") or []
        if not isinstance(tool_calls, list) or not tool_calls:
            break

        saw_tool_call = True
        tool_messages = core.execute_tool_calls(tool_calls, config)
        assert tool_messages, "expected tool execution results"
        for tool_message in tool_messages:
            session = core.add_message(
                session,
                role=tool_message.get("role", "tool"),
                content=tool_message.get("content", ""),
                metadata=tool_message.get("metadata"),
                config=config,
            )
    else:
        pytest.fail(f"tool loop did not settle within {max_iterations} iterations")

    assert saw_tool_call, "expected at least one tool call in this ChatGPT turn"
    assert (
        len(assistant_turns) >= 2
    ), "expected multiple assistant turns for this user turn"
    final = assistant_turns[-1]
    assert final.get("role") == "assistant"
    assert isinstance(final.get("content"), str)
    assert expected_text in final["content"]
    return session, assistant_turns, estimates


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_saved_login_usage_multi_turn_tool_loop() -> None:
    load_dotenv(REPO_ROOT / ".env")

    credentials_path = _credentials_path()
    _load_saved_credentials()

    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[
            OpenAIResponsesToolsExtension,
            OpenAIResponsesUsageExtension,
            CostTrackingExtension,
        ],
    )
    core.register_feature(OpenAIResponsesChatGPTAuthFeature)
    core.register_feature(SystemMessageFeature)
    core.register_tool(MathTools)

    config = _chatgpt_config(credentials_path)

    session = core.create_session()

    session, turn1_responses, turn1_estimates = _run_tool_turn_streaming(
        core,
        session,
        config,
        prompt=(
            "Use the add tool exactly once to compute 123 + 456. "
            "After the tool result, reply with exactly: TURN1=579"
        ),
        expected_text="TURN1=579",
    )
    session, turn2_responses, turn2_estimates = _run_tool_turn_streaming(
        core,
        session,
        config,
        prompt=(
            "Use the add tool exactly once to compute 10 + 20. "
            "After the tool result, reply with exactly: TURN2=30"
        ),
        expected_text="TURN2=30",
    )

    assert len(turn1_responses) >= 2
    assert len(turn2_responses) >= 2
    assert turn1_estimates[0] == 0
    assert any(
        value > 0 for value in turn1_estimates[1:]
    ), "expected a later assistant response in turn 1 to have non-zero estimated cached tokens"
    assert (
        turn2_estimates[0] > 0
    ), "expected the first assistant response in turn 2 to reuse estimated cached tokens"

    # The append-only usage journal must have grown end to end: one
    # request_usage record per assistant response, each paired with the
    # rate-limit snapshot observed on that response, plus at least one
    # rate_limit_snapshot record.
    journal_records = _journal_records()
    request_records = [
        record for record in journal_records if record.get("type") == "request_usage"
    ]
    snapshot_records = [
        record
        for record in journal_records
        if record.get("type") == "rate_limit_snapshot"
    ]
    expected_requests = len(turn1_responses) + len(turn2_responses)
    assert (
        len(request_records) >= expected_requests
    ), "expected the usage journal to record every ChatGPT-backed response"
    assert snapshot_records, "expected rate-limit snapshots in the usage journal"
    for record in request_records[-expected_requests:]:
        assert isinstance(record.get("timestamp"), str)
        assert isinstance(record.get("input_tokens"), int)
        assert isinstance(record.get("output_tokens"), int)
        assert isinstance(record.get("estimated_cost"), (int, float))
        rate_limits = record.get("rate_limits")
        assert isinstance(rate_limits, dict), (
            "expected each request record to carry the rate-limit snapshot "
            "observed on the same response"
        )
        assert (
            isinstance(rate_limits.get("snapshots"), list) and rate_limits["snapshots"]
        )

    # The simplified summary CSV is appended at the same time as the journal
    # and carries the session id and absolute working directory per record.
    summary_path = _usage_summary_csv_path()
    assert summary_path.exists(), "expected the ChatGPT usage summary CSV"
    import csv

    with open(summary_path, encoding="utf-8", newline="") as handle:
        summary_rows = list(csv.DictReader(handle))
    assert len(summary_rows) >= expected_requests
    request_rows = [row for row in summary_rows if row["estimated_cost"] != ""]
    assert len(request_rows) >= expected_requests
    for row in request_rows[-expected_requests:]:
        assert row["session_id"], "expected the session id in summary CSV rows"
        assert row["working_directory"].startswith(
            "/"
        ), "expected an absolute working directory in summary CSV rows"
        assert float(row["estimated_cost"]) >= 0.0
        assert float(row["total_cost"]) >= float(row["estimated_cost"])

    # The generic cost tracking store records the same responses under the
    # provider-defined ChatGPT bucket, and the store-backed session total
    # reaches the assistant message metadata rendered by the chat status bar.
    db_path = _cost_db_path()
    assert db_path.exists(), "expected the cost tracking SQLite store"
    session_id = session.session_id
    workspace = os.path.abspath(os.path.expanduser(str(config["working_directory"])))
    own_cost_rows = 0
    import sqlite3

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT response_id, bucket, session_id, working_directory, estimated_cost "
            "FROM cost_requests"
        ).fetchall()
    finally:
        conn.close()
    own_response_ids = {
        (response.get("metadata") or {}).get("response_id")
        for response in turn1_responses + turn2_responses
    }
    own_response_ids.discard(None)
    for response_id, bucket, row_session_id, row_wd, estimated_cost in rows:
        if response_id in own_response_ids:
            own_cost_rows += 1
            assert bucket == "openai-responses-chatgpt"
            assert row_session_id, "expected the session id on cost store rows"
            assert row_wd == workspace
            assert isinstance(estimated_cost, (int, float))
    assert own_cost_rows >= expected_requests, (
        "expected every ChatGPT-backed response recorded in the cost store "
        "under the provider-defined bucket"
    )
    totals = cost_store.session_totals(
        db_path, working_directory=workspace, session_id=str(session_id)
    )
    assert totals["request_count"] >= expected_requests
    assert totals["total_cost"] > 0.0
    final_metadata = turn2_responses[-1].get("metadata") or {}
    assert isinstance(final_metadata.get("cost_session_total_formatted"), str)
    assert final_metadata.get("cost_session_requests", 0) >= expected_requests
