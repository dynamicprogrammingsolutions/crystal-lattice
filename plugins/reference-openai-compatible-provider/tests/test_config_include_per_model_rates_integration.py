"""End-to-end per-model rates via config ``$include`` through the public
request path.

Runs a real ``AgentApplication`` request against a local stub OpenAI-compatible
chat-completions endpoint using the production provider and usage extension.
The provider's ``token_rates`` are an ``$include`` of a pricing file with
per-model entries; the request uses a ``:cloud``-tagged model id so the
per-model lookup, tag stripping, and cost/breakdown stamping are all exercised
through the real config pipeline and provider request path.
"""

from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
COST_TRACKING_SRC = ROOT / "plugins/cost-tracking/src"
if str(COST_TRACKING_SRC) not in sys.path:
    sys.path.insert(0, str(COST_TRACKING_SRC))

import pytest  # noqa: E402

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_core import Session  # noqa: E402

pytestmark = [pytest.mark.integration]


class _QuietServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address) -> None:
        _ = request, client_address


class _ChatCompletionsHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args) -> None:
        _ = format, args

    def do_POST(self) -> None:
        length = int(self.headers.get("content-length", "0"))
        if length:
            self.rfile.read(length)
        payload_obj = {
            "id": "chatcmpl_include_1",
            "object": "chat.completion",
            "model": "glm-5.2:cloud",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "hello from the stub"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 1000,
                "completion_tokens": 500,
                "total_tokens": 1500,
                "prompt_tokens_details": {"cached_tokens": 200},
            },
        }
        payload = json.dumps(payload_obj).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def _write_config(tmp_path: Path, base_url: str, db_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "stub": {
                "provider": "reference_openai_compatible",
                "model": "glm-5.2:cloud",
                "api_key": "test_key",
                "base_url": base_url,
                "timeout": 60,
                "working_directory": str(tmp_path / "workspace"),
                "cost_tracking_db_path": str(db_path),
                "token_rates": {"$include": "${env:CONFIG_DIR}/pricing/rates.json"},
            }
        },
        "plugins": [
            "reference_openai_compatible_provider.provider.OpenAICompatibleProvider",
            (
                "reference_openai_compatible_provider.usage_extension."
                "OpenAICompatibleUsageExtension"
            ),
            "cost_tracking_plugins.cost_tracking_extension.CostTrackingExtension",
        ],
        "agents": {"default": {"provider": "stub"}},
        "application": {
            "cost_tracking": {"db_path": str(db_path)},
        },
    }
    path = tmp_path / "config_include_rates.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _write_pricing_file(tmp_path: Path) -> Path:
    pricing_dir = tmp_path / "pricing"
    pricing_dir.mkdir()
    rates = {
        "_source": "stub-pricing",
        "_generated_at": "2026-09-27",
        "models": {
            "glm-5.2": {"input": 1.4, "cached": 0.26, "completion": 4.4},
        },
    }
    path = pricing_dir / "rates.json"
    path.write_text(json.dumps(rates), encoding="utf-8")
    return path


def test_per_model_rates_from_included_pricing_file_reach_request_cost(
    tmp_path: Path,
) -> None:
    _write_pricing_file(tmp_path)
    server = _QuietServer(("127.0.0.1", 0), _ChatCompletionsHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        base_url = f"http://127.0.0.1:{server.server_port}/v1"
        db_path = tmp_path / "costs.sqlite3"
        config_path = _write_config(tmp_path, base_url, db_path)
        # Pin CONFIG_DIR to the temp config dir so the ``$include`` resolves
        # there even when the host process exports its own CONFIG_DIR.
        app = AgentApplication(
            str(config_path),
            str(tmp_path / "sessions"),
            event_store=InMemoryEventStore(),
            env_overrides={"CONFIG_DIR": str(tmp_path)},
        )

        core, base_config, session = app.create_session("default")
        session = core.add_message(session, "user", "Say hello.", config=base_config)
        app.save_session(session)

        events = list(
            app.send_request(core, session, base_config, overrides=None, stream=False)
        )
        checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
        assert checkpoints, "expected at least one session checkpoint"
        final_session = checkpoints[-1]["session"]
        assert isinstance(final_session, Session)
        app.save_session(final_session)

        assistants = [
            message for message in final_session.messages if message.role == "assistant"
        ]
        assert assistants, "expected assistant messages in final session"
        metadata = assistants[-1].metadata or {}

        # glm-5.2 per-model rates from the included pricing file:
        # 800 ordinary * 1.4/M + 200 cached * 0.26/M + 500 output * 4.4/M
        # = 0.00112 + 0.000052 + 0.0022 = 0.003372
        assert metadata.get("usage_total_cost") == pytest.approx(0.003372)

        # The per-item breakdown reaches the cost tracking store columns.
        from cost_tracking_plugins import cost_store

        totals = cost_store.session_totals(
            db_path,
            working_directory=str(tmp_path / "workspace"),
            session_id=final_session.session_id,
        )
        assert totals["request_count"] == 1
        assert totals["input_cost"] == pytest.approx(0.00112)
        assert totals["cached_cost"] == pytest.approx(0.000052)
        assert totals["output_cost"] == pytest.approx(0.0022)
        assert totals["total_cost"] == pytest.approx(0.003372)
    finally:
        server.shutdown()
        server.server_close()
