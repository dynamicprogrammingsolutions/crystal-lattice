"""Integration tests for cost tracking through the public request path.

These tests run a real ``AgentApplication`` request against a local stub
OpenAI Responses endpoint using the production provider, usage extension, and
cost tracking extension — no test-only bypasses. They assert that cost rows
land in the SQLite store with the provider-defined bucket and that the
store-backed session total reaches the assistant message metadata that the
chat status bar renders.
"""

from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
OPENAI_RESPONSES_SRC = ROOT / "plugins/openai_responses/src"
if str(OPENAI_RESPONSES_SRC) not in sys.path:
    sys.path.insert(0, str(OPENAI_RESPONSES_SRC))

import pytest  # noqa: E402

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_core import Session  # noqa: E402

pytestmark = [pytest.mark.integration]


class _QuietServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address) -> None:
        _ = request, client_address


class _ResponsesHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    response_id = "resp_cost_tracking_1"
    stream_mode = False

    def log_message(self, format, *args) -> None:
        _ = format, args

    def do_POST(self) -> None:
        length = int(self.headers.get("content-length", "0"))
        if length:
            self.rfile.read(length)
        response_obj = {
            "id": type(self).response_id,
            "object": "response",
            "created_at": 1,
            "status": "completed",
            "model": "gpt-5-mini",
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "id": "msg_1",
                    "content": [{"type": "output_text", "text": "hello from the stub"}],
                }
            ],
            "usage": {
                "input_tokens": 100,
                "input_tokens_details": {"cached_tokens": 10},
                "output_tokens": 20,
                "output_tokens_details": {"reasoning_tokens": 5},
                "total_tokens": 120,
            },
        }
        if type(self).stream_mode:
            payload = (
                "event: response.completed\n"
                f'data: {json.dumps({"type": "response.completed", "response": response_obj})}\n\n'
                "data: [DONE]\n\n"
            ).encode()
            content_type = "text/event-stream"
        else:
            payload = json.dumps(response_obj).encode()
            content_type = "application/json"
        self.send_response(200)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def _write_config(tmp_path: Path, base_url: str, db_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openai_responses": {
                "provider": "openai_responses",
                "model": "gpt-5-mini",
                "api_key": "test_key",
                "base_url": base_url,
                "timeout": 60,
                "working_directory": str(tmp_path / "workspace"),
                "cost_tracking_db_path": str(db_path),
            }
        },
        "plugins": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider",
            "openai_responses_plugins.openai_responses_usage_extension.OpenAIResponsesUsageExtension",
            "cost_tracking_plugins.cost_tracking_extension.CostTrackingExtension",
        ],
        "agents": {"default": {"provider": "openai_responses"}},
        "application": {
            "cost_tracking": {"db_path": str(db_path)},
        },
    }
    path = tmp_path / "config_cost_tracking.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _run_request(
    app: AgentApplication,
    core: Any,
    session: Session,
    base_config: Dict[str, Any],
    *,
    stream: bool,
) -> Session:
    events = list(
        app.send_request(core, session, base_config, overrides=None, stream=stream)
    )
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert checkpoints, "expected at least one session checkpoint"
    final_session = checkpoints[-1]["session"]
    assert isinstance(final_session, Session)
    app.save_session(final_session)
    return final_session


def _assistant_messages(session: Session) -> List[Any]:
    return [message for message in session.messages if message.role == "assistant"]


def _assert_cost_tracking(
    tmp_path: Path,
    final_session: Session,
    db_path: Path,
    *,
    expected_bucket: str,
) -> None:
    from cost_tracking_plugins import cost_store

    assistants = _assistant_messages(final_session)
    assert assistants, "expected assistant messages in final session"
    metadata = assistants[-1].metadata or {}
    assert metadata.get("usage_bucket") == expected_bucket
    assert metadata.get("cost_session_total_formatted"), metadata
    assert metadata.get("cost_session_requests") == 1

    report = cost_store.bucket_report(db_path)
    assert report["request_count"] == 1
    buckets = {entry["bucket"]: entry for entry in report["buckets"]}
    assert expected_bucket in buckets
    assert buckets[expected_bucket]["request_count"] == 1
    assert buckets[expected_bucket]["total_cost"] > 0.0

    session_totals = cost_store.session_totals(
        db_path,
        working_directory=str(tmp_path / "workspace"),
        session_id=final_session.session_id,
    )
    assert session_totals["request_count"] == 1
    assert session_totals["total_cost"] == pytest.approx(
        buckets[expected_bucket]["total_cost"]
    )

    # The per-item cost breakdown reaches the footer metadata and the store.
    assert metadata.get("cost_session_breakdown_formatted", "").startswith("Total: $")
    assert metadata.get("cost_session_input_cost", 0.0) > 0.0
    assert metadata.get("cost_session_cached_cost", 0.0) > 0.0
    assert metadata.get("cost_session_output_cost", 0.0) > 0.0
    assert session_totals["input_cost"] == pytest.approx(
        metadata["cost_session_input_cost"]
    )
    assert session_totals["cached_cost"] == pytest.approx(
        metadata["cost_session_cached_cost"]
    )
    assert session_totals["output_cost"] == pytest.approx(
        metadata["cost_session_output_cost"]
    )

    # The growing summary CSV beside the store carries the per-request row
    # with rolling session and reset-aware bucket totals.
    import csv

    csv_path = db_path.with_name("cost-tracking-summary.csv")
    with open(csv_path, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["bucket"] == expected_bucket
    assert rows[0]["session_id"] == final_session.session_id
    assert float(rows[0]["cost"]) == pytest.approx(
        buckets[expected_bucket]["total_cost"]
    )
    assert float(rows[0]["session_total_cost"]) == pytest.approx(
        session_totals["total_cost"]
    )
    assert float(rows[0]["bucket_total_cost"]) == pytest.approx(
        buckets[expected_bucket]["total_cost"]
    )


@pytest.mark.parametrize("stream", [False, True])
def test_cost_tracking_records_through_public_request_path(
    tmp_path: Path, stream: bool
) -> None:
    _ResponsesHandler.stream_mode = stream
    _ResponsesHandler.response_id = (
        f"resp_cost_tracking_stream_{stream}"
        if stream
        else "resp_cost_tracking_nonstream"
    )
    server = _QuietServer(("127.0.0.1", 0), _ResponsesHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        base_url = f"http://127.0.0.1:{server.server_port}/v1"
        db_path = tmp_path / "costs.sqlite3"
        config_path = _write_config(tmp_path, base_url, db_path)
        app = AgentApplication(
            str(config_path),
            str(tmp_path / "sessions"),
            event_store=InMemoryEventStore(),
        )

        core, base_config, session = app.create_session("default")
        session = core.add_message(session, "user", "Say hello.", config=base_config)
        app.save_session(session)

        final_session = _run_request(app, core, session, base_config, stream=stream)

        _assert_cost_tracking(
            tmp_path,
            final_session,
            db_path,
            expected_bucket="openai-responses-api",
        )
    finally:
        server.shutdown()
        server.server_close()
