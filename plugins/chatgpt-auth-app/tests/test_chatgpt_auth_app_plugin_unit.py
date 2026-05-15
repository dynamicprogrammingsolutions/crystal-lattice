from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import parse_qs

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


REPO_ROOT = Path(__file__).resolve().parents[3]


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
                    {"error": "authorization_pending", "error_description": "still waiting"},
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


def _start_fake_server(*, succeed_after_polls: int = 1, always_pending: bool = False) -> Tuple[Any, Dict[str, Any]]:
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
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
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


def _write_openai_responses_config(tmp_path: Path, *, auth_mode: str = "auto") -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "chatgpt": {
                "provider": "openai_responses",
                "model": "gpt-5",
                "auth_mode": auth_mode,
                "chatgpt_base_url": "https://chatgpt.example.test/backend-api/codex",
            }
        },
        "plugins": [
            _plugin_entry("chatgpt-auth-app", "chatgpt_auth_app.ChatGPTAuthAppPlugin"),
            _plugin_entry("openai_responses", "openai_responses_plugins.OpenAIResponsesProvider"),
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


def _build_openai_responses_app(tmp_path: Path, *, auth_mode: str = "auto") -> AgentApplication:
    config_path = _write_openai_responses_config(tmp_path, auth_mode=auth_mode)
    return AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides={"CONFIG_DIR": str(tmp_path)},
    )


def _build_default_codex_app(tmp_path: Path, *, issuer: str) -> AgentApplication:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
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


def test_login_start_polls_in_background_and_persists_credentials(tmp_path: Path) -> None:
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
            status = app.execute_application_action("chatgpt_auth", "check_status", {})["auth_status"]
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


def test_cancel_login_stops_pending_flow_and_keeps_credentials_absent(tmp_path: Path) -> None:
    server, state = _start_fake_server(always_pending=True)
    try:
        app = _build_app(tmp_path, port=server.server_address[1])
        start = app.execute_application_action("chatgpt_auth", "login_start", {})
        assert start["auth_status"]["state"] == "pending"

        canceled = app.execute_application_action("chatgpt_auth", "cancel_login", {})
        assert canceled["auth_status"]["state"] == "canceled"
        assert canceled["display"]["variant"] == "warning"

        time.sleep(0.2)
        status = app.execute_application_action("chatgpt_auth", "check_status", {})["auth_status"]
        assert status["state"] == "canceled"
        assert state["poll_count"] <= 1
        assert not (tmp_path / "auth" / "chatgpt-auth.json").exists()
    finally:
        server.shutdown()
        server.server_close()


def test_codex_default_endpoints_and_exchange_flow_work_from_issuer_only(tmp_path: Path) -> None:
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
            status = app.execute_application_action("chatgpt_auth", "check_status", {})["auth_status"]
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
        assert state["device_requests"][0]["client_id"] == "app_EMoamEEZ73f0CkXaXp7hrann"
    finally:
        server.shutdown()
        server.server_close()


def test_session_ui_elements_are_gated_by_provider_and_auth_mode(tmp_path: Path) -> None:
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
    assert hidden_for_api == []

    hidden_for_other_provider = app.get_application_ui_schema(
        config={"provider": "echo_openai_like", "auth_mode": "chatgpt"},
        tags=["provider:echo_openai_like"],
    )
    assert hidden_for_other_provider == []

    assert app.get_application_ui_schema() == []


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


def test_show_account_status_reports_missing_limits_when_no_snapshot_exists(tmp_path: Path) -> None:
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

    assert "- Not available yet. Run a ChatGPT-backed request to refresh." in result["display"]["body"]