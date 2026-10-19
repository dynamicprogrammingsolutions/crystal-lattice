from __future__ import annotations

import io
import json
import ssl
import threading
import time
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.error import HTTPError
from urllib.parse import parse_qs

import chatgpt_auth_app
import pytest
from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from chatgpt_auth_app import ChatGPTAuthAppPlugin, _verified_ssl_context


REPO_ROOT = Path(__file__).resolve().parents[3]
APPLICATION_PY = REPO_ROOT / "application" / "python"
if str(APPLICATION_PY) not in sys.path:
    sys.path.insert(0, str(APPLICATION_PY))


def test_verified_ssl_context_requires_certificate_validation() -> None:
    context = _verified_ssl_context()

    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
    assert context.get_ca_certs()


def test_cloudflare_route_error_retries_with_in_process_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    route_error = json.dumps(
        {"error": {"type": "cf_route_error", "message": "retry"}}
    ).encode("utf-8")

    def fake_urlopen(*args: Any, **kwargs: Any) -> Any:
        _ = (args, kwargs)
        raise HTTPError(
            "https://auth.openai.com/device",
            530,
            "route error",
            None,
            io.BytesIO(route_error),
        )

    class FakeResponse:
        status_code = 200
        text = json.dumps(
            {
                "device_auth_id": "device-auth-1",
                "user_code": "ABCD-EFGH",
            }
        )

    request_calls: list[dict[str, Any]] = []

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        request_calls.append({"url": url, **kwargs})
        return FakeResponse()

    monkeypatch.setattr(chatgpt_auth_app, "urlopen", fake_urlopen)
    monkeypatch.setattr(chatgpt_auth_app.requests, "post", fake_post)

    status, payload = ChatGPTAuthAppPlugin()._request_payload(
        url="https://auth.openai.com/device",
        payload={"client_id": "client"},
        headers={},
        encoding="json",
        timeout=20,
    )

    assert status == 200
    assert payload["device_auth_id"] == "device-auth-1"
    assert request_calls[0]["verify"] == chatgpt_auth_app.certifi.where()


class _FakeDeviceCodeHandler(BaseHTTPRequestHandler):
    server_version = "FakeDeviceCode/1.0"

    def do_POST(self) -> None:  # noqa: N802
        server = self.server
        state = getattr(server, "state")
        length = int(self.headers.get("Content-Length") or "0")
        body = self.rfile.read(length).decode("utf-8")
        if body:
            try:
                payload = json.loads(body)
            except Exception:
                parsed = parse_qs(body, keep_blank_values=True)
                payload = {
                    key: values[0] if len(values) == 1 else values
                    for key, values in parsed.items()
                }
        else:
            payload = {}

        if self.path == "/device":
            state["device_requests"].append(payload)
            response = {
                "device_code": "device-code-1",
                "user_code": "ABCD-EFGH",
                "verification_uri": f"http://{server.server_address[0]}:{server.server_address[1]}/verify",
                "expires_in": 60,
                "interval": 1,
            }
            self._write_json(200, response)
            return

        if self.path == "/token":
            state["token_requests"].append(payload)
            state["poll_count"] += 1
            succeed_after = state.get("succeed_after_polls", 1)
            if state.get("always_pending") or state["poll_count"] <= succeed_after:
                self._write_json(
                    400,
                    {
                        "error": "authorization_pending",
                        "error_description": "still waiting",
                    },
                )
                return
            self._write_json(
                200,
                {
                    "access_token": "chatgpt-access-token",
                    "refresh_token": "refresh-token",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "account_email": "user@example.com",
                    "plan_type": "plus",
                },
            )
            return

        if self.path == "/api/accounts/deviceauth/usercode":
            state["device_requests"].append(payload)
            self._write_json(
                200,
                {
                    "device_auth_id": "device-auth-1",
                    "user_code": "WXYZ-1234",
                    "interval": "1",
                },
            )
            return

        if self.path == "/api/accounts/deviceauth/token":
            state["token_requests"].append(payload)
            state["poll_count"] += 1
            succeed_after = state.get("succeed_after_polls", 1)
            if state.get("always_pending") or state["poll_count"] <= succeed_after:
                self._write_json(404, {"error": "pending"})
                return
            self._write_json(
                200,
                {
                    "authorization_code": "auth-code-1",
                    "code_verifier": "code-verifier-1",
                    "code_challenge": "code-challenge-1",
                },
            )
            return

        if self.path == "/oauth/token":
            self._write_json(
                200,
                {
                    "id_token": _make_jwt(
                        {
                            "https://api.openai.com/auth": {
                                "chatgpt_account_id": "acct-123",
                                "chatgpt_plan_type": "plus",
                                "email": "codex@example.com",
                            }
                        }
                    ),
                    "access_token": "codex-access-token",
                    "refresh_token": "codex-refresh-token",
                },
            )
            return

        self._write_json(404, {"error": "not_found"})

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        _ = (format, args)

    def _write_json(self, status: int, payload: Dict[str, Any]) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def _start_fake_server(
    *, succeed_after_polls: int = 1, always_pending: bool = False
) -> Tuple[Any, Dict[str, Any]]:
    state = {
        "device_requests": [],
        "token_requests": [],
        "poll_count": 0,
        "succeed_after_polls": succeed_after_polls,
        "always_pending": always_pending,
    }
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeDeviceCodeHandler)
    server.state = state  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, state


def _plugin_entry(repo_name: str, entry: str) -> Dict[str, str]:
    return {"path": str(REPO_ROOT / "plugins" / repo_name), "entry": entry}


def _make_jwt(payload: Dict[str, Any]) -> str:
    import base64

    def _b64(obj: Dict[str, Any]) -> str:
        raw = json.dumps(obj).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    return f"{_b64({'alg': 'none', 'typ': 'JWT'})}.{_b64(payload)}.sig"


def _write_config(tmp_path: Path, *, port: int) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {"echo": {"provider": "echo_openai_like", "model": "test-model"}},
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            _plugin_entry(
                "chatgpt-auth-app",
                "chatgpt_auth_app.ChatGPTAuthAppPlugin",
            ),
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "chatgpt_auth": {
                "protocol": "oauth_device_code",
                "credentials_path": "${env:CONFIG_DIR}/auth/chatgpt-auth.json",
                "device_code_endpoint": f"http://127.0.0.1:{port}/device",
                "token_endpoint": f"http://127.0.0.1:{port}/token",
                "client_id": "chatgpt-client",
                "request_encoding": "json",
                "device_code_poll_interval_seconds": 1,
                "login_timeout_seconds": 30,
                "http_timeout_seconds": 5,
            }
        },
    }
    path = tmp_path / "config_chatgpt_auth.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _write_openai_responses_config(
    tmp_path: Path,
    *,
    auth_mode: str = "auto",
    provider_extras: Dict[str, Any] | None = None,
) -> Path:
    provider_cfg: Dict[str, Any] = {
        "provider": "openai_responses",
        "model": "gpt-5",
        "auth_mode": auth_mode,
        "chatgpt_base_url": "https://chatgpt.example.test/backend-api/codex",
    }
    if provider_extras:
        provider_cfg.update(provider_extras)
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {"chatgpt": provider_cfg},
        "plugins": [
            _plugin_entry("chatgpt-auth-app", "chatgpt_auth_app.ChatGPTAuthAppPlugin"),
            _plugin_entry(
                "openai_responses", "openai_responses_plugins.OpenAIResponsesProvider"
            ),
            _plugin_entry(
                "openai_responses",
                "openai_responses_plugins.OpenAIResponsesUsageExtension",
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
    path = tmp_path / f"config_chatgpt_auth_openai_responses_{auth_mode}.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path, *, port: int) -> AgentApplication:
    config_path = _write_config(tmp_path, port=port)
    return AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides={"CONFIG_DIR": str(tmp_path)},
    )


def _build_openai_responses_app(
    tmp_path: Path,
    *,
    auth_mode: str = "auto",
    provider_extras: Dict[str, Any] | None = None,
) -> AgentApplication:
    config_path = _write_openai_responses_config(
        tmp_path, auth_mode=auth_mode, provider_extras=provider_extras
    )
    return AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides={"CONFIG_DIR": str(tmp_path)},
    )


def _build_default_codex_app(tmp_path: Path, *, issuer: str) -> AgentApplication:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {"echo": {"provider": "echo_openai_like", "model": "test-model"}},
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            _plugin_entry(
                "chatgpt-auth-app",
                "chatgpt_auth_app.ChatGPTAuthAppPlugin",
            ),
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "chatgpt_auth": {
                "issuer": issuer,
                "credentials_path": "${env:CONFIG_DIR}/auth/chatgpt-auth.json",
                "http_timeout_seconds": 5,
            }
        },
    }
    config_path = tmp_path / "config_chatgpt_auth_codex_defaults.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")
    return AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides={"CONFIG_DIR": str(tmp_path)},
    )


def test_login_start_polls_in_background_and_persists_credentials(
    tmp_path: Path,
) -> None:
    server, state = _start_fake_server(succeed_after_polls=1)
    try:
        app = _build_app(tmp_path, port=server.server_address[1])

        result = app.execute_application_action("chatgpt_auth", "login_start", {})
        auth_status = result["auth_status"]
        assert auth_status["state"] == "pending"
        assert auth_status["user_code"] == "ABCD-EFGH"
        assert auth_status["verification_url"].endswith("/verify")
        assert result["display"]["format"] == "markdown"
        assert "ABCD-EFGH" in result["display"]["body"]
        assert auth_status["verification_url"] in result["display"]["body"]
        assert result["display"]["presentation"] == "inline"
        assert result["display"]["dismissible"] is True
        assert result["display"]["display_id"] == "chatgpt-auth-login"
        action_kinds = [entry["kind"] for entry in result["display"]["actions"]]
        assert action_kinds == ["open_url", "copy_text", "run_action"]

        deadline = time.time() + 3.5
        status = auth_status
        while time.time() < deadline:
            status = app.execute_application_action("chatgpt_auth", "check_status", {})[
                "auth_status"
            ]
            if status["state"] == "authenticated":
                break
            time.sleep(0.1)

        assert status["state"] == "authenticated"
        assert status["account_email"] == "user@example.com"
        assert state["poll_count"] >= 2

        credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
        saved = json.loads(credentials_path.read_text(encoding="utf-8"))
        assert saved["access_token"] == "chatgpt-access-token"
        assert saved["account_email"] == "user@example.com"

        ui_elements = app.get_application_ui_schema(
            config={"provider": "openai_responses", "auth_mode": "auto"},
            tags=["provider:openai_responses"],
        )
        labels = {element.get("label") for element in ui_elements}
        assert "Show ChatGPT login status" in labels
        assert "Show ChatGPT account status" in labels
    finally:
        server.shutdown()
        server.server_close()


def test_codex_cli_command_runs_complete_foreground_device_flow(
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
) -> None:
    from agent_terminal_app.__main__ import _run_standalone_command_element

    server, _state = _start_fake_server(succeed_after_polls=0)
    try:
        app = _build_app(tmp_path, port=server.server_address[1])
        command = next(
            element
            for element in app.get_application_command_ui_elements("cli_command")
            if element["path"] == ["auth", "login", "codex"]
        )

        _run_standalone_command_element(app, command, {})

        output = capfd.readouterr().out
        assert "ABCD-EFGH" in output
        assert "/verify" in output
        assert "login is active" in output.lower()
        saved = json.loads(
            (tmp_path / "auth" / "chatgpt-auth.json").read_text(encoding="utf-8")
        )
        assert saved["access_token"] == "chatgpt-access-token"
    finally:
        server.shutdown()
        server.server_close()


def test_cancel_login_stops_pending_flow_and_keeps_credentials_absent(
    tmp_path: Path,
) -> None:
    server, state = _start_fake_server(always_pending=True)
    try:
        app = _build_app(tmp_path, port=server.server_address[1])
        start = app.execute_application_action("chatgpt_auth", "login_start", {})
        assert start["auth_status"]["state"] == "pending"

        canceled = app.execute_application_action("chatgpt_auth", "cancel_login", {})
        assert canceled["auth_status"]["state"] == "canceled"
        assert canceled["display"]["variant"] == "warning"
        attempt = app._app_plugins["chatgpt_auth"].state["active_attempt"]
        assert not attempt["worker"].is_alive()

        time.sleep(0.2)
        status = app.execute_application_action("chatgpt_auth", "check_status", {})[
            "auth_status"
        ]
        assert status["state"] == "canceled"
        assert state["poll_count"] <= 1
        assert not (tmp_path / "auth" / "chatgpt-auth.json").exists()
    finally:
        server.shutdown()
        server.server_close()


def test_codex_default_endpoints_and_exchange_flow_work_from_issuer_only(
    tmp_path: Path,
) -> None:
    server, state = _start_fake_server(succeed_after_polls=1)
    try:
        issuer = f"http://127.0.0.1:{server.server_address[1]}"
        app = _build_default_codex_app(tmp_path, issuer=issuer)

        result = app.execute_application_action("chatgpt_auth", "login_start", {})
        auth_status = result["auth_status"]
        assert auth_status["state"] == "pending"
        assert auth_status["verification_url"] == f"{issuer}/codex/device"
        assert auth_status["user_code"] == "WXYZ-1234"
        assert result["display"]["title"] == "ChatGPT Login"
        assert f"{issuer}/codex/device" in result["display"]["body"]
        assert result["display"]["presentation"] == "inline"

        deadline = time.time() + 3.5
        status = auth_status
        while time.time() < deadline:
            status = app.execute_application_action("chatgpt_auth", "check_status", {})[
                "auth_status"
            ]
            if status["state"] == "authenticated":
                break
            time.sleep(0.1)

        assert status["state"] == "authenticated"
        assert status["account_email"] == "codex@example.com"
        credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
        saved = json.loads(credentials_path.read_text(encoding="utf-8"))
        assert saved["access_token"] == "codex-access-token"
        assert saved["refresh_token"] == "codex-refresh-token"
        assert saved["account_id"] == "acct-123"
        assert saved["plan_type"] == "plus"
        assert (
            state["device_requests"][0]["client_id"] == "app_EMoamEEZ73f0CkXaXp7hrann"
        )
    finally:
        server.shutdown()
        server.server_close()


def test_session_ui_elements_are_gated_by_provider_and_auth_mode(
    tmp_path: Path,
) -> None:
    app = _build_openai_responses_app(tmp_path, auth_mode="auto")
    visible = app.get_application_ui_schema(
        config={"provider": "openai_responses", "auth_mode": "auto"},
        tags=["provider:openai_responses"],
    )
    labels = {element.get("label") for element in visible}
    assert "Sign in with ChatGPT" in labels
    assert "Show ChatGPT account status" in labels

    hidden_for_api = app.get_application_ui_schema(
        config={"provider": "openai_responses", "auth_mode": "api"},
        tags=["provider:openai_responses"],
    )
    assert [
        (element["ui_type"], element["path"])
        for element in hidden_for_api
    ] == [("cli_command", ["auth", "login", "codex"])]

    hidden_for_other_provider = app.get_application_ui_schema(
        config={"provider": "echo_openai_like", "auth_mode": "chatgpt"},
        tags=["provider:echo_openai_like"],
    )
    assert [
        (element["ui_type"], element["path"])
        for element in hidden_for_other_provider
    ] == [("cli_command", ["auth", "login", "codex"])]

    assert [
        (element["ui_type"], element["path"])
        for element in app.get_application_ui_schema()
    ] == [("cli_command", ["auth", "login", "codex"])]


def test_show_account_status_reads_saved_rate_limits(tmp_path: Path) -> None:
    app = _build_openai_responses_app(tmp_path, auth_mode="auto")
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "chatgpt-access-token",
                "refresh_token": "chatgpt-refresh-token",
                "token_type": "Bearer",
                "account_email": "user@example.com",
                "account_id": "acct-123",
                "plan_type": "plus",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "auth" / "chatgpt-rate-limits.json").write_text(
        json.dumps(
            {
                "captured_at": "2026-04-12T10:00:00Z",
                "plan_type": "plus",
                "snapshots": [
                    {
                        "limit_id": "codex",
                        "primary": {
                            "used_percent": 45.0,
                            "window_minutes": 300,
                            "resets_at": 1775995500,
                        },
                        "secondary": {
                            "used_percent": 30.0,
                            "window_minutes": 10080,
                            "resets_at": 1776500000,
                        },
                        "credits": {
                            "has_credits": True,
                            "unlimited": False,
                            "balance": "13",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    _core, _base_config, session = app.create_session("default")
    app.save_session(session)

    result = app.execute_application_action(
        "chatgpt_auth",
        "show_account_status",
        {"session_id": session.session_id},
    )

    assert result["requested_auth_mode"] == "auto"
    assert result["effective_auth_mode"] == "chatgpt"
    body = result["display"]["body"]
    assert "Requested auth mode: `auto`" in body
    assert "Effective auth mode: `chatgpt`" in body
    assert "Account: `user@example.com`" in body
    assert "Plan: `plus`" in body
    assert "5h limit: `55% left`" in body
    assert "Weekly limit: `70% left`" in body
    assert "Credits: `13 credits`" in body


def test_show_account_status_reports_missing_limits_when_no_snapshot_exists(
    tmp_path: Path,
) -> None:
    app = _build_openai_responses_app(tmp_path, auth_mode="chatgpt")
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "chatgpt-access-token",
                "refresh_token": "chatgpt-refresh-token",
                "token_type": "Bearer",
                "account_email": "user@example.com",
                "account_id": "acct-123",
                "plan_type": "plus",
            }
        ),
        encoding="utf-8",
    )

    _core, _base_config, session = app.create_session("default")
    app.save_session(session)

    result = app.execute_application_action(
        "chatgpt_auth",
        "show_account_status",
        {"session_id": session.session_id},
    )

    assert (
        "- Not available yet. Run a ChatGPT-backed request to refresh."
        in result["display"]["body"]
    )


def _journal_path(tmp_path: Path) -> Path:
    return tmp_path / "auth" / "chatgpt-usage-journal.ndjson"


def _write_journal_record(tmp_path: Path, record: Dict[str, Any]) -> None:
    journal = _journal_path(tmp_path)
    journal.parent.mkdir(parents=True, exist_ok=True)
    with open(journal, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def _request_usage_record(
    *,
    input_tokens: int,
    output_tokens: int = 10,
    estimated_cost: float = 0.01,
    timestamp: str,
    used_percent: float = 30.0,
) -> Dict[str, Any]:
    return {
        "type": "request_usage",
        "timestamp": timestamp,
        "response_id": "resp",
        "model": "gpt-5",
        "input_tokens": input_tokens,
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "output_tokens": output_tokens,
        "reasoning_tokens": 0,
        "estimated_cost": estimated_cost,
        "rate_limits": {
            "captured_at": timestamp,
            "snapshots": [
                {
                    "limit_id": "codex",
                    "primary": {
                        "used_percent": used_percent,
                        "window_minutes": 300,
                        "resets_at": 1775995500,
                    },
                    "secondary": None,
                    "credits": None,
                }
            ],
        },
    }


def _create_chatgpt_session(app: AgentApplication):
    _core, _base_config, session = app.create_session("default")
    app.save_session(session)
    return session


def test_show_usage_report_totals_since_reset(tmp_path: Path) -> None:
    app = _build_openai_responses_app(tmp_path, auth_mode="auto")
    _write_journal_record(
        tmp_path,
        _request_usage_record(
            input_tokens=100,
            timestamp="2026-09-18T10:00:00Z",
            used_percent=10.0,
        ),
    )
    _write_journal_record(
        tmp_path,
        {
            "type": "usage_reset",
            "timestamp": "2026-09-18T11:00:00Z",
            "source": "chatgpt_auth_app",
        },
    )
    _write_journal_record(
        tmp_path,
        _request_usage_record(
            input_tokens=200,
            output_tokens=20,
            estimated_cost=0.02,
            timestamp="2026-09-19T10:00:00Z",
            used_percent=45.0,
        ),
    )
    _write_journal_record(
        tmp_path,
        _request_usage_record(
            input_tokens=50,
            output_tokens=5,
            estimated_cost=0.01,
            timestamp="2026-09-19T11:00:00Z",
            used_percent=60.0,
        ),
    )

    session = _create_chatgpt_session(app)
    result = app.execute_application_action(
        "chatgpt_auth",
        "show_usage_report",
        {"session_id": session.session_id},
    )

    body = result["display"]["body"]
    assert "Tracking since reset: `2026-09-18T11:00:00Z`" in body
    assert "Requests: `2`" in body
    assert "Input tokens: `250`" in body
    assert "Output tokens: `25`" in body
    assert "Estimated cost: `$0.030000`" in body
    assert "5h limit: `40% left`" in body
    # Percent history is scoped to the same since-reset window.
    assert "`45%` → `60%`" in body
    assert "(min `45%`, max `60%`)" in body

    display = result["display"]
    assert display["form"]["kind"] == "form"
    form_names = [entry["name"] for entry in display["form"]["inputs"]]
    assert form_names == ["from", "to"]
    assert all(entry["type"] == "string" for entry in display["form"]["inputs"])
    followup = display["actions"][0]
    assert followup["kind"] == "run_action"
    assert followup["action_id"] == "show_usage_report"
    assert followup["fixed_params"] == {"session_id": session.session_id}
    assert followup["param_map"] == {"from": "$form.from", "to": "$form.to"}


def test_show_usage_report_narrows_by_date_range(tmp_path: Path) -> None:
    from datetime import datetime, timedelta, timezone

    app = _build_openai_responses_app(tmp_path, auth_mode="auto")
    early_dt = datetime(2026, 9, 18, 6, 0, tzinfo=timezone.utc)
    late_dt = datetime(2026, 9, 19, 18, 0, tzinfo=timezone.utc)
    _write_journal_record(
        tmp_path,
        _request_usage_record(
            input_tokens=100,
            timestamp=early_dt.isoformat().replace("+00:00", "Z"),
            used_percent=5.0,
        ),
    )
    _write_journal_record(
        tmp_path,
        _request_usage_record(
            input_tokens=500,
            timestamp=late_dt.isoformat().replace("+00:00", "Z"),
            used_percent=80.0,
        ),
    )

    session = _create_chatgpt_session(app)
    # Express the range in the server's own timezone text format.
    from_text = (early_dt + timedelta(hours=1)).astimezone().strftime("%Y-%m-%d %H:%M")
    to_text = (late_dt + timedelta(hours=1)).astimezone().strftime("%Y-%m-%d %H:%M")

    result = app.execute_application_action(
        "chatgpt_auth",
        "show_usage_report",
        {"session_id": session.session_id, "from": from_text, "to": to_text},
    )

    body = result["display"]["body"]
    assert f"Date range: `{from_text}` → `{to_text}`" in body
    assert "Requests: `1`" in body
    assert "Input tokens: `500`" in body
    assert "Input tokens: `100`" not in body
    # The narrowed report keeps the range form so the user can adjust it.
    assert result["display"]["form"]["inputs"][0].get("default") == from_text
    assert result["display"]["form"]["inputs"][1].get("default") == to_text


def test_show_usage_report_accepts_date_only_input(tmp_path: Path) -> None:
    from datetime import datetime, timezone

    app = _build_openai_responses_app(tmp_path, auth_mode="auto")
    record_dt = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
    _write_journal_record(
        tmp_path,
        _request_usage_record(
            input_tokens=42,
            timestamp=record_dt.isoformat().replace("+00:00", "Z"),
        ),
    )

    session = _create_chatgpt_session(app)
    local_date = record_dt.astimezone().strftime("%Y-%m-%d")

    result = app.execute_application_action(
        "chatgpt_auth",
        "show_usage_report",
        {"session_id": session.session_id, "from": local_date},
    )

    body = result["display"]["body"]
    assert "Requests: `1`" in body
    assert "Input tokens: `42`" in body


def test_show_usage_report_invalid_date_shows_friendly_error(tmp_path: Path) -> None:
    app = _build_openai_responses_app(tmp_path, auth_mode="auto")
    session = _create_chatgpt_session(app)

    result = app.execute_application_action(
        "chatgpt_auth",
        "show_usage_report",
        {"session_id": session.session_id, "from": "not-a-date"},
    )

    display = result["display"]
    assert display["variant"] == "error"
    assert "Could not read the requested date range" in display["body"]
    assert "`not-a-date`" in display["body"]
    # The form is retained so the user can retry.
    assert display["form"]["kind"] == "form"


def test_reset_usage_tracking_appends_marker_and_report_follows(tmp_path: Path) -> None:
    app = _build_openai_responses_app(tmp_path, auth_mode="auto")
    _write_journal_record(
        tmp_path,
        _request_usage_record(
            input_tokens=100,
            timestamp="2026-09-18T10:00:00Z",
        ),
    )

    session = _create_chatgpt_session(app)
    result = app.execute_application_action(
        "chatgpt_auth",
        "reset_usage_tracking",
        {"session_id": session.session_id},
    )

    assert result["reset_appended"] is True
    assert result["display"]["variant"] == "success"
    journal_text = _journal_path(tmp_path).read_text(encoding="utf-8")
    reset_lines = [
        line for line in journal_text.splitlines() if '"type": "usage_reset"' in line
    ]
    assert len(reset_lines) == 1

    # The reset also appends a zeroed-total row to the summary CSV.
    summary_path = tmp_path / "auth" / "chatgpt-usage-summary.csv"
    assert summary_path.exists()
    summary_lines = summary_path.read_text(encoding="utf-8").splitlines()
    assert summary_lines[0] == (
        "time,working_directory,session_id,estimated_cost,total_cost,used_percent"
    )
    assert len(summary_lines) == 2
    assert summary_lines[1].endswith(",,,0.0,")

    report = app.execute_application_action(
        "chatgpt_auth",
        "show_usage_report",
        {"session_id": session.session_id},
    )
    assert "Requests: `0`" in report["display"]["body"]
    assert "Tracking since reset: " in report["display"]["body"]


def test_reset_usage_tracking_can_skip_summary_csv(tmp_path: Path) -> None:
    app = _build_openai_responses_app(
        tmp_path,
        auth_mode="auto",
        provider_extras={"track_chatgpt_usage_summary_csv": False},
    )
    session = _create_chatgpt_session(app)

    result = app.execute_application_action(
        "chatgpt_auth",
        "reset_usage_tracking",
        {"session_id": session.session_id},
    )

    assert result["reset_appended"] is True
    assert not (tmp_path / "auth" / "chatgpt-usage-summary.csv").exists()


def test_show_account_status_includes_since_reset_usage(tmp_path: Path) -> None:
    app = _build_openai_responses_app(tmp_path, auth_mode="auto")
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "chatgpt-access-token",
                "refresh_token": "chatgpt-refresh-token",
                "token_type": "Bearer",
                "account_email": "user@example.com",
                "account_id": "acct-123",
                "plan_type": "plus",
            }
        ),
        encoding="utf-8",
    )
    _write_journal_record(
        tmp_path,
        _request_usage_record(
            input_tokens=1000,
            output_tokens=100,
            estimated_cost=0.123456,
            timestamp="2026-09-19T10:00:00Z",
        ),
    )

    session = _create_chatgpt_session(app)
    result = app.execute_application_action(
        "chatgpt_auth",
        "show_account_status",
        {"session_id": session.session_id},
    )

    body = result["display"]["body"]
    assert "Estimated usage since reset:" in body
    assert "Requests: `1`" in body
    assert "Input tokens: `1,000`" in body
    assert "Output tokens: `100`" in body
    assert "Estimated cost: `$0.123456`" in body


def test_usage_report_actions_gated_to_chatgpt_sessions(tmp_path: Path) -> None:
    # A non-openai_responses provider session must not expose usage actions.
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {"echo": {"provider": "echo_openai_like", "model": "test-model"}},
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            _plugin_entry(
                "chatgpt-auth-app",
                "chatgpt_auth_app.ChatGPTAuthAppPlugin",
            ),
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "chatgpt_auth": {
                "credentials_path": "${env:CONFIG_DIR}/auth/chatgpt-auth.json",
                "rate_limits_path": "${env:CONFIG_DIR}/auth/chatgpt-rate-limits.json",
            }
        },
    }
    config_path = tmp_path / "config_chatgpt_auth_echo.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides={"CONFIG_DIR": str(tmp_path)},
    )
    _core, _base_config, session = app.create_session("default")
    app.save_session(session)

    report = app.execute_application_action(
        "chatgpt_auth",
        "show_usage_report",
        {"session_id": session.session_id},
    )
    assert report["display"]["variant"] == "warning"

    reset = app.execute_application_action(
        "chatgpt_auth",
        "reset_usage_tracking",
        {"session_id": session.session_id},
    )
    assert reset["display"]["variant"] == "warning"
    assert not _journal_path(tmp_path).exists()


def test_codex_command_elements_bind_device_flow_without_method_or_logout() -> None:
    plugin = ChatGPTAuthAppPlugin()
    state = plugin.init({})

    global_elements = plugin.get_ui_elements(state, {}, [], [])
    assert [
        (element["ui_type"], element["path"], element["action_id"])
        for element in global_elements
    ] == [("cli_command", ["auth", "login", "codex"], "login_start")]

    session_elements = plugin.get_ui_elements(
        state,
        {"provider": "openai_responses", "auth_mode": "auto"},
        ["provider:openai_responses"],
        [],
    )
    command_paths = {
        element["ui_type"]: element["path"]
        for element in session_elements
        if element["ui_type"] in {"cli_command", "slash_command"}
    }
    assert command_paths == {
        "cli_command": ["auth", "login", "codex"],
        "slash_command": ["login", "codex"],
    }
    for element in session_elements:
        if element.get("ui_type") not in {"cli_command", "slash_command"}:
            continue
        assert element.get("dialog") == {"kind": "none"}
        assert "method" not in element
        assert "logout" not in element["path"]


def test_stale_attempt_cannot_commit_credentials(tmp_path: Path) -> None:
    plugin = ChatGPTAuthAppPlugin()
    state = plugin.init(
        {
            "application": {
                "chatgpt_auth": {
                    "credentials_path": str(tmp_path / "auth.json"),
                }
            }
        }
    )
    old_attempt = {
        "login_id": "old",
        "state": "pending",
        "cancel_event": threading.Event(),
    }
    new_attempt = {
        "login_id": "new",
        "state": "pending",
        "cancel_event": threading.Event(),
    }
    state["active_attempt"] = new_attempt

    committed = plugin._update_current_attempt(
        state,
        old_attempt,
        attempt_state="authenticated",
        credentials={
            "login_id": "old",
            "access_token": "stale-token",
            "credentials_path": str(tmp_path / "auth.json"),
        },
    )

    assert committed is None
    assert state["active_attempt"] is new_attempt
    assert not (tmp_path / "auth.json").exists()
