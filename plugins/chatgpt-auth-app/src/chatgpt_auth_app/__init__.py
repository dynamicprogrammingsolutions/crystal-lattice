from __future__ import annotations

import json
import os
import tempfile
import threading
import uuid
import base64
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode
from urllib.request import Request, urlopen

from . import usage_journal


_DEFAULT_HTTP_TIMEOUT_SECONDS = 20.0
_DEFAULT_LOGIN_TIMEOUT_SECONDS = 900
_DEFAULT_POLL_INTERVAL_SECONDS = 5
_DEFAULT_ISSUER = "https://auth.openai.com"
_DEFAULT_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
_DEVICE_CODE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
_DEFAULT_CHATGPT_CREDENTIALS_RELATIVE_PATH = "auth/chatgpt-auth.json"
_DEFAULT_CHATGPT_RATE_LIMITS_RELATIVE_PATH = "auth/chatgpt-rate-limits.json"
_NON_FATAL_TOKEN_ERRORS = {"authorization_pending", "slow_down"}
_TERMINAL_TOKEN_ERRORS = {"access_denied", "expired_token", "invalid_grant"}
_RATE_LIMIT_STALE_THRESHOLD_MINUTES = 15


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _isoformat_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_iso8601(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _coerce_positive_int(value: Any, default: int) -> int:
    try:
        out = int(value)
    except (TypeError, ValueError):
        return default
    return out if out > 0 else default


def _coerce_positive_float(value: Any, default: float) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if out > 0 else default


def _normalized_token_type(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return "Bearer"
    normalized = value.strip()
    if normalized.lower() == "bearer":
        return "Bearer"
    return normalized


def _jwt_claims(jwt: Any) -> Dict[str, Any]:
    if not isinstance(jwt, str) or not jwt:
        return {}
    parts = jwt.split(".")
    if len(parts) != 3:
        return {}
    payload = parts[1]
    padding = "=" * (-len(payload) % 4)
    try:
        decoded = base64.urlsafe_b64decode(payload + padding)
        parsed = json.loads(decoded.decode("utf-8"))
    except Exception:
        return {}
    if not isinstance(parsed, dict):
        return {}
    nested = parsed.get("https://api.openai.com/auth")
    return nested if isinstance(nested, dict) else parsed


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    _ensure_parent_dir(path)
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _remove_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return


def _normalize_auth_mode(value: Any) -> str:
    if not isinstance(value, str):
        return "api"
    normalized = value.strip().lower()
    if normalized == "api_key":
        return "api"
    if normalized in {"api", "chatgpt", "auto"}:
        return normalized
    return "api"


def _resolve_rate_limits_path(config: Dict[str, Any]) -> Path:
    raw = config.get("chatgpt_rate_limits_path")
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()
    credentials_path = config.get("chatgpt_credentials_path")
    if isinstance(credentials_path, str) and credentials_path.strip():
        return Path(credentials_path).expanduser().with_name("chatgpt-rate-limits.json")
    config_dir = os.environ.get("CONFIG_DIR")
    if isinstance(config_dir, str) and config_dir:
        return (
            Path(config_dir).expanduser() / _DEFAULT_CHATGPT_RATE_LIMITS_RELATIVE_PATH
        )
    return Path.cwd() / _DEFAULT_CHATGPT_RATE_LIMITS_RELATIVE_PATH


def _format_limit_duration(window_minutes: int) -> str:
    minutes_per_hour = 60
    minutes_per_day = 24 * minutes_per_hour
    minutes_per_week = 7 * minutes_per_day
    minutes_per_month = 30 * minutes_per_day
    rounding_bias = 3

    window_minutes = max(0, int(window_minutes))
    if window_minutes <= minutes_per_day + rounding_bias:
        adjusted = window_minutes + rounding_bias
        hours = max(1, adjusted // minutes_per_hour)
        return f"{hours}h"
    if window_minutes <= minutes_per_week + rounding_bias:
        return "weekly"
    if window_minutes <= minutes_per_month + rounding_bias:
        return "monthly"
    return "annual"


def _format_limit_label(window: Dict[str, Any], fallback: str) -> str:
    minutes = window.get("window_minutes")
    if isinstance(minutes, int):
        text = _format_limit_duration(minutes)
        if text == "weekly":
            return "Weekly limit"
        if text == "monthly":
            return "Monthly limit"
        if text == "annual":
            return "Annual limit"
        return f"{text} limit"
    return fallback


def _format_reset_time(
    resets_at: Any, *, now: Optional[datetime] = None
) -> Optional[str]:
    if not isinstance(resets_at, int):
        return None
    observed_at = now or _utcnow()
    try:
        reset_dt = datetime.fromtimestamp(resets_at, tz=timezone.utc).astimezone()
    except Exception:
        return None
    local_now = observed_at.astimezone(reset_dt.tzinfo)
    text = reset_dt.strftime("%H:%M")
    if reset_dt.date() != local_now.date():
        text = f"{text} on {reset_dt.day} {reset_dt.strftime('%b')}"
    return text


def _format_credit_balance(raw: Any) -> Optional[str]:
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    try:
        int_value = int(text)
    except ValueError:
        try:
            float_value = float(text)
        except ValueError:
            return None
        if float_value <= 0:
            return None
        return str(int(round(float_value)))
    if int_value <= 0:
        return None
    return str(int_value)


class ChatGPTAuthAppPlugin:
    """Application plugin implementing a minimal device-code login flow."""

    name = "chatgpt_auth"
    version = "0.1.0"

    def __init__(self) -> None:
        self._lock = threading.RLock()

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "chatgpt_auth": {
                "type": "object",
                "description": "Device-code login settings for ChatGPT-style auth.",
            }
        }

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = (state, models)
        if not self._should_show_session_actions(config, tags):
            return []
        return [
            {
                "ui_type": "session_action",
                "id": "chatgpt_auth_login_start",
                "label": "Sign in with ChatGPT",
                "icon": "log-in",
                "order": 5,
                "action_id": "login_start",
                "dialog": {"kind": "none"},
            },
            {
                "ui_type": "session_action",
                "id": "chatgpt_auth_check_status",
                "label": "Show ChatGPT login status",
                "icon": "shield",
                "order": 6,
                "action_id": "check_status",
                "dialog": {"kind": "none"},
            },
            {
                "ui_type": "session_action",
                "id": "chatgpt_auth_show_account_status",
                "label": "Show ChatGPT account status",
                "icon": "gauge",
                "order": 7,
                "action_id": "show_account_status",
                "param_map": {"session_id": "$session.session_id"},
                "dialog": {"kind": "none"},
            },
            {
                "ui_type": "session_action",
                "id": "chatgpt_auth_show_usage_report",
                "label": "Show ChatGPT usage report",
                "icon": "bar-chart",
                "order": 8,
                "action_id": "show_usage_report",
                "param_map": {"session_id": "$session.session_id"},
                "dialog": {"kind": "none"},
            },
            {
                "ui_type": "session_action",
                "id": "chatgpt_auth_reset_usage_tracking",
                "label": "Reset ChatGPT usage tracking",
                "icon": "rotate-ccw",
                "order": 9,
                "action_id": "reset_usage_tracking",
                "param_map": {"session_id": "$session.session_id"},
                "dialog": {
                    "kind": "confirm",
                    "title": "Reset usage tracking",
                    "message": (
                        "Append a reset marker so usage totals start from now? "
                        "Previous journal history stays inspectable."
                    ),
                },
            },
            {
                "ui_type": "session_action",
                "id": "chatgpt_auth_cancel_login",
                "label": "Cancel ChatGPT login",
                "icon": "x-circle",
                "order": 10,
                "action_id": "cancel_login",
                "dialog": {"kind": "none"},
            },
            {
                "ui_type": "session_action",
                "id": "chatgpt_auth_logout",
                "label": "Log out of ChatGPT",
                "icon": "log-out",
                "order": 11,
                "action_id": "logout",
                "dialog": {"kind": "none"},
            },
        ]

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        application_cfg = app_config.get("application")
        if not isinstance(application_cfg, dict):
            application_cfg = {}
        auth_cfg = application_cfg.get("chatgpt_auth")
        if not isinstance(auth_cfg, dict):
            auth_cfg = {}

        config_dir = os.environ.get("CONFIG_DIR")
        config_root = (
            Path(config_dir)
            if isinstance(config_dir, str) and config_dir
            else Path.cwd()
        )

        credentials_path = auth_cfg.get("credentials_path")
        if isinstance(credentials_path, str) and credentials_path.strip():
            credentials_file = Path(credentials_path).expanduser()
        else:
            credentials_file = config_root / _DEFAULT_CHATGPT_CREDENTIALS_RELATIVE_PATH
        rate_limits_path = auth_cfg.get("rate_limits_path")
        if isinstance(rate_limits_path, str) and rate_limits_path.strip():
            rate_limits_file = Path(rate_limits_path).expanduser()
        else:
            rate_limits_file = credentials_file.with_name("chatgpt-rate-limits.json")

        normalized_config = {
            "credentials_path": str(credentials_file),
            "rate_limits_path": str(rate_limits_file),
            "protocol": (
                auth_cfg.get("protocol").strip().lower()
                if isinstance(auth_cfg.get("protocol"), str)
                and auth_cfg.get("protocol").strip()
                else "codex_deviceauth"
            ),
            "issuer": (
                auth_cfg.get("issuer").strip().rstrip("/")
                if isinstance(auth_cfg.get("issuer"), str)
                and auth_cfg.get("issuer").strip()
                else _DEFAULT_ISSUER
            ),
            "device_code_endpoint": auth_cfg.get("device_code_endpoint"),
            "token_endpoint": auth_cfg.get("token_endpoint"),
            "token_exchange_endpoint": auth_cfg.get("token_exchange_endpoint"),
            "verification_url": auth_cfg.get("verification_url"),
            "redirect_uri": auth_cfg.get("redirect_uri"),
            "client_id": auth_cfg.get("client_id") or _DEFAULT_CLIENT_ID,
            "client_secret": auth_cfg.get("client_secret"),
            "scope": auth_cfg.get("scope"),
            "audience": auth_cfg.get("audience"),
            "device_code_request": (
                dict(auth_cfg.get("device_code_request") or {})
                if isinstance(auth_cfg.get("device_code_request"), dict)
                else {}
            ),
            "token_request": (
                dict(auth_cfg.get("token_request") or {})
                if isinstance(auth_cfg.get("token_request"), dict)
                else {}
            ),
            "headers": (
                dict(auth_cfg.get("headers") or {})
                if isinstance(auth_cfg.get("headers"), dict)
                else {}
            ),
            "request_encoding": (
                auth_cfg.get("request_encoding").strip().lower()
                if isinstance(auth_cfg.get("request_encoding"), str)
                and auth_cfg.get("request_encoding").strip()
                else "json"
            ),
            "http_timeout_seconds": _coerce_positive_float(
                auth_cfg.get("http_timeout_seconds"),
                _DEFAULT_HTTP_TIMEOUT_SECONDS,
            ),
            "device_code_poll_interval_seconds": _coerce_positive_int(
                auth_cfg.get("device_code_poll_interval_seconds"),
                _DEFAULT_POLL_INTERVAL_SECONDS,
            ),
            "login_timeout_seconds": _coerce_positive_int(
                auth_cfg.get("login_timeout_seconds"),
                _DEFAULT_LOGIN_TIMEOUT_SECONDS,
            ),
        }
        return {
            "config": normalized_config,
            "active_attempt": None,
            "last_status": None,
        }

    def _should_show_session_actions(
        self,
        config: Optional[Dict[str, Any]],
        tags: Optional[List[str]],
    ) -> bool:
        if not isinstance(config, dict):
            return False
        provider_name = config.get("provider")
        provider_match = provider_name == "openai_responses"
        tag_match = any(tag == "provider:openai_responses" for tag in tags or [])
        if not (provider_match or tag_match):
            return False
        requested_mode = _normalize_auth_mode(config.get("auth_mode"))
        return requested_mode in {"auto", "chatgpt"}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "login_start",
                "label": "Sign in with ChatGPT",
                "description": "Start a device-code login flow and return the verification URL.",
                "inputs": {},
            },
            {
                "id": "check_status",
                "label": "Show ChatGPT login status",
                "description": "Return the current login status.",
                "inputs": {},
            },
            {
                "id": "show_account_status",
                "label": "Show ChatGPT account status",
                "description": "Return the current ChatGPT account and usage-limit status for a session.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                },
            },
            {
                "id": "show_usage_report",
                "label": "Show ChatGPT usage report",
                "description": (
                    "Return estimated ChatGPT usage totals since the last reset "
                    "(or within a date range) with usage-percent history."
                ),
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "from": {
                        "type": "string",
                        "required": False,
                        "description": (
                            "Optional inclusive start date or date+time "
                            "(server timezone), e.g. 2026-09-19 or 2026-09-19 14:30."
                        ),
                    },
                    "to": {
                        "type": "string",
                        "required": False,
                        "description": (
                            "Optional inclusive end date or date+time "
                            "(server timezone), e.g. 2026-09-19 or 2026-09-19 14:30."
                        ),
                    },
                },
            },
            {
                "id": "reset_usage_tracking",
                "label": "Reset ChatGPT usage tracking",
                "description": (
                    "Append a manual reset marker so usage totals start from now. "
                    "Journal history is preserved."
                ),
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                },
            },
            {
                "id": "cancel_login",
                "label": "Cancel ChatGPT login",
                "description": "Cancel the active background login poller.",
                "inputs": {},
            },
            {
                "id": "logout",
                "label": "Log out of ChatGPT",
                "description": "Delete saved ChatGPT credentials.",
                "inputs": {},
            },
        ]

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = (params, context)
        if action_id == "login_start":
            return self._start_login(app, state)
        if action_id == "check_status":
            auth_status = self._current_status(state)
            return {
                "display": self._status_display_payload(
                    auth_status, action="check_status"
                ),
                "auth_status": auth_status,
            }
        if action_id == "show_account_status":
            return self._show_account_status(app, state, params)
        if action_id == "show_usage_report":
            return self._show_usage_report(app, state, params)
        if action_id == "reset_usage_tracking":
            return self._reset_usage_tracking(app, state, params)
        if action_id == "cancel_login":
            auth_status = self._cancel_login(app, state)
            return {
                "display": self._status_display_payload(
                    auth_status, action="cancel_login"
                ),
                "auth_status": auth_status,
            }
        if action_id == "logout":
            auth_status = self._logout(app, state)
            return {
                "display": self._status_display_payload(auth_status, action="logout"),
                "auth_status": auth_status,
            }
        raise KeyError(f"Unknown action_id {action_id!r}")

    def _config(self, state: Dict[str, Any]) -> Dict[str, Any]:
        raw = state.get("config")
        return raw if isinstance(raw, dict) else {}

    def _credentials_path(self, state: Dict[str, Any]) -> Path:
        cfg = self._config(state)
        raw = cfg.get("credentials_path")
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("[chatgpt_auth] credentials_path must be configured")
        return Path(raw).expanduser()

    def _rate_limits_path(self, state: Dict[str, Any]) -> Path:
        return _resolve_rate_limits_path(
            {
                "chatgpt_rate_limits_path": self._config(state).get("rate_limits_path"),
                "chatgpt_credentials_path": str(self._credentials_path(state)),
            }
        )

    def _session_config(self, app: Any, session_id: str) -> Dict[str, Any]:
        ctx = app.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")
        core, base_config, session = ctx
        _ = core
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides = metadata.get("overrides")
        if not isinstance(overrides, dict):
            overrides = {}
        resolve_effective = getattr(app, "resolve_effective_config", None)
        if callable(resolve_effective):
            return resolve_effective(base_config, session, overrides)
        return dict(base_config)

    def _effective_auth_mode(
        self, config: Dict[str, Any], auth_status: Dict[str, Any]
    ) -> str:
        raw = config.get("_openai_responses_effective_auth_mode")
        if isinstance(raw, str) and raw.strip().lower() in {"api", "chatgpt"}:
            return raw.strip().lower()
        requested = _normalize_auth_mode(config.get("auth_mode"))
        if requested == "chatgpt":
            return "chatgpt"
        if requested == "auto":
            status_state = auth_status.get("state")
            if status_state == "authenticated":
                return "chatgpt"
        return "api"

    def _render_rate_limit_lines(self, rate_limits_state: Dict[str, Any]) -> List[str]:
        snapshots = rate_limits_state.get("snapshots")
        if not isinstance(snapshots, list) or not snapshots:
            return []

        lines: List[str] = []
        captured_at = _parse_iso8601(rate_limits_state.get("captured_at"))
        if captured_at is not None and _utcnow() - captured_at > timedelta(
            minutes=_RATE_LIMIT_STALE_THRESHOLD_MINUTES
        ):
            lines.append(
                "_Latest known usage limits may be stale. Run a ChatGPT-backed request to refresh._"
            )

        for snapshot in snapshots:
            if not isinstance(snapshot, dict):
                continue
            limit_id = snapshot.get("limit_id")
            bucket = (
                str(limit_id) if isinstance(limit_id, str) and limit_id else "codex"
            )
            primary = snapshot.get("primary")
            secondary = snapshot.get("secondary")
            credits = snapshot.get("credits")
            window_count = int(isinstance(primary, dict)) + int(
                isinstance(secondary, dict)
            )
            prefix_non_codex_single = bucket != "codex" and window_count == 1

            if bucket != "codex" and window_count > 1:
                lines.append(f"- `{bucket}`")

            if isinstance(primary, dict):
                label = _format_limit_label(primary, "5h limit")
                if prefix_non_codex_single:
                    label = f"{bucket} {label}"
                percent_used = primary.get("used_percent")
                percent_remaining = (
                    100.0 - float(percent_used)
                    if isinstance(percent_used, (int, float))
                    else None
                )
                reset_text = _format_reset_time(primary.get("resets_at"))
                line = f"- {label}: "
                if percent_remaining is not None:
                    line += f"`{percent_remaining:.0f}% left`"
                else:
                    line += "`usage available`"
                if isinstance(reset_text, str) and reset_text:
                    line += f" (resets `{reset_text}`)"
                lines.append(line)

            if isinstance(secondary, dict):
                label = _format_limit_label(secondary, "Weekly limit")
                if prefix_non_codex_single:
                    label = f"{bucket} {label}"
                percent_used = secondary.get("used_percent")
                percent_remaining = (
                    100.0 - float(percent_used)
                    if isinstance(percent_used, (int, float))
                    else None
                )
                reset_text = _format_reset_time(secondary.get("resets_at"))
                line = f"- {label}: "
                if percent_remaining is not None:
                    line += f"`{percent_remaining:.0f}% left`"
                else:
                    line += "`usage available`"
                if isinstance(reset_text, str) and reset_text:
                    line += f" (resets `{reset_text}`)"
                lines.append(line)

            if isinstance(credits, dict) and credits.get("has_credits") is True:
                if credits.get("unlimited") is True:
                    lines.append("- Credits: `Unlimited`")
                else:
                    balance = _format_credit_balance(credits.get("balance"))
                    if isinstance(balance, str):
                        lines.append(f"- Credits: `{balance} credits`")

        return lines

    def _request_payload(
        self,
        *,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, Any],
        encoding: str,
        timeout: float,
    ) -> tuple[int, Dict[str, Any]]:
        if encoding == "json":
            body = json.dumps(payload).encode("utf-8")
            content_type = "application/json"
        else:
            body = urlencode(
                {key: value for key, value in payload.items() if value is not None}
            ).encode("utf-8")
            content_type = "application/x-www-form-urlencoded"

        request_headers = {str(key): str(value) for key, value in headers.items()}
        request_headers.setdefault("Content-Type", content_type)
        request_headers.setdefault("Accept", "application/json")
        request = Request(url, data=body, headers=request_headers, method="POST")
        try:
            with urlopen(request, timeout=timeout) as response:
                status = int(getattr(response, "status", 200) or 200)
                raw_text = response.read().decode("utf-8")
        except HTTPError as exc:
            status = exc.code
            raw_text = exc.read().decode("utf-8")
            if self._should_retry_with_curl(status, raw_text):
                return self._request_payload_with_curl(
                    url=url,
                    body=body,
                    headers=request_headers,
                    timeout=timeout,
                )
        except URLError as exc:
            raise RuntimeError(f"HTTP request failed: {exc}") from exc

        parsed: Dict[str, Any]
        try:
            payload_obj = json.loads(raw_text)
        except Exception:
            parsed_qs = parse_qs(raw_text, keep_blank_values=True)
            parsed = {
                key: values[0] if len(values) == 1 else values
                for key, values in parsed_qs.items()
            }
        else:
            parsed = payload_obj if isinstance(payload_obj, dict) else {}
        return status, parsed

    def _should_retry_with_curl(self, status: int, raw_text: str) -> bool:
        if status != 530:
            return False
        try:
            parsed = json.loads(raw_text)
        except Exception:
            return False
        if not isinstance(parsed, dict):
            return False
        error = parsed.get("error")
        if isinstance(error, dict):
            return error.get("type") == "cf_route_error"
        return False

    def _request_payload_with_curl(
        self,
        *,
        url: str,
        body: bytes,
        headers: Dict[str, str],
        timeout: float,
    ) -> tuple[int, Dict[str, Any]]:
        command = [
            "curl",
            "-sS",
            "-X",
            "POST",
            url,
            "--max-time",
            str(int(timeout) if timeout >= 1 else 1),
            "--write-out",
            "\n__STATUS__:%{http_code}",
            "--data-binary",
            "@-",
        ]
        for key, value in headers.items():
            command.extend(["-H", f"{key}: {value}"])
        try:
            completed = subprocess.run(
                command,
                input=body,
                capture_output=True,
                check=False,
            )
        except Exception as exc:
            raise RuntimeError(f"curl fallback failed: {exc}") from exc

        output = completed.stdout.decode("utf-8", errors="replace")
        marker = "\n__STATUS__:"
        if marker not in output:
            stderr = completed.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(
                f"curl fallback returned unexpected output: {stderr or output}"
            )
        raw_text, _, status_text = output.rpartition(marker)
        try:
            status = int(status_text.strip())
        except ValueError as exc:
            raise RuntimeError(
                "curl fallback did not return a valid HTTP status"
            ) from exc
        try:
            parsed = json.loads(raw_text)
        except Exception:
            parsed_qs = parse_qs(raw_text, keep_blank_values=True)
            parsed = {
                key: values[0] if len(values) == 1 else values
                for key, values in parsed_qs.items()
            }
        if not isinstance(parsed, dict):
            parsed = {}
        return status, parsed

    def _start_device_code(self, state: Dict[str, Any]) -> Dict[str, Any]:
        cfg = self._config(state)
        protocol = cfg.get("protocol") or "codex_deviceauth"
        issuer = str(cfg.get("issuer") or _DEFAULT_ISSUER).rstrip("/")
        device_code_endpoint = cfg.get("device_code_endpoint") or (
            f"{issuer}/api/accounts/deviceauth/usercode"
            if protocol == "codex_deviceauth"
            else None
        )
        token_endpoint = cfg.get("token_endpoint") or (
            f"{issuer}/api/accounts/deviceauth/token"
            if protocol == "codex_deviceauth"
            else None
        )
        client_id = cfg.get("client_id")
        if (
            not isinstance(device_code_endpoint, str)
            or not device_code_endpoint.strip()
        ):
            raise ValueError(
                "[chatgpt_auth] application.chatgpt_auth.device_code_endpoint is required"
            )
        if not isinstance(token_endpoint, str) or not token_endpoint.strip():
            raise ValueError(
                "[chatgpt_auth] application.chatgpt_auth.token_endpoint is required"
            )
        if not isinstance(client_id, str) or not client_id.strip():
            raise ValueError(
                "[chatgpt_auth] application.chatgpt_auth.client_id is required"
            )

        payload: Dict[str, Any] = {"client_id": client_id.strip()}
        if isinstance(cfg.get("client_secret"), str) and cfg.get("client_secret"):
            payload["client_secret"] = cfg["client_secret"]
        if isinstance(cfg.get("scope"), str) and cfg.get("scope"):
            payload["scope"] = cfg["scope"]
        if isinstance(cfg.get("audience"), str) and cfg.get("audience"):
            payload["audience"] = cfg["audience"]
        payload.update(cfg.get("device_code_request") or {})

        status_code, response = self._request_payload(
            url=device_code_endpoint.strip(),
            payload=payload,
            headers=cfg.get("headers") or {},
            encoding=str(cfg.get("request_encoding") or "json"),
            timeout=_coerce_positive_float(
                cfg.get("http_timeout_seconds"), _DEFAULT_HTTP_TIMEOUT_SECONDS
            ),
        )
        if status_code >= 400:
            error = (
                response.get("error")
                if isinstance(response.get("error"), str)
                else "device_code_start_failed"
            )
            message = (
                response.get("error_description")
                if isinstance(response.get("error_description"), str)
                else f"device code start failed with status {status_code}"
            )
            raise RuntimeError(f"{error}: {message}")
        return response

    def _normalized_attempt(
        self, device_code_response: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        cfg = self._config(state)
        protocol = cfg.get("protocol") or "codex_deviceauth"
        issuer = str(cfg.get("issuer") or _DEFAULT_ISSUER).rstrip("/")
        device_code = device_code_response.get("device_code")
        device_auth_id = device_code_response.get("device_auth_id")
        verification_url = (
            device_code_response.get("verification_uri_complete")
            or device_code_response.get("verification_uri")
            or device_code_response.get("verification_url")
            or cfg.get("verification_url")
            or (f"{issuer}/codex/device" if protocol == "codex_deviceauth" else None)
        )
        user_code = device_code_response.get("user_code")
        if protocol == "codex_deviceauth":
            if not isinstance(device_auth_id, str) or not device_auth_id:
                raise RuntimeError(
                    "[chatgpt_auth] device code response missing device_auth_id"
                )
        elif not isinstance(device_code, str) or not device_code:
            raise RuntimeError(
                "[chatgpt_auth] device code response missing device_code"
            )
        if not isinstance(verification_url, str) or not verification_url:
            raise RuntimeError(
                "[chatgpt_auth] device code response missing verification URL"
            )
        if not isinstance(user_code, str) or not user_code:
            raise RuntimeError("[chatgpt_auth] device code response missing user_code")

        started_at = _utcnow()
        expires_in = _coerce_positive_int(
            device_code_response.get("expires_in"),
            self._config(state).get("login_timeout_seconds"),
        )
        poll_interval = _coerce_positive_int(
            device_code_response.get("interval"),
            self._config(state).get("device_code_poll_interval_seconds"),
        )
        return {
            "login_id": str(uuid.uuid4()),
            "state": "pending",
            "device_code": device_code,
            "device_auth_id": device_auth_id,
            "verification_url": verification_url,
            "user_code": user_code,
            "started_at": _isoformat_utc(started_at),
            "expires_at": _isoformat_utc(started_at + timedelta(seconds=expires_in)),
            "poll_interval_seconds": poll_interval,
            "cancel_event": threading.Event(),
            "error": None,
            "account_email": None,
            "plan_type": None,
        }

    def _start_login(self, app: Any, state: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            current_attempt = state.get("active_attempt")
            if (
                isinstance(current_attempt, dict)
                and current_attempt.get("state") == "pending"
            ):
                auth_status = self._attempt_status(current_attempt)
                return {
                    "display": self._status_display_payload(
                        auth_status, action="login_start"
                    ),
                    "auth_status": auth_status,
                }

            device_code_response = self._start_device_code(state)
            attempt = self._normalized_attempt(device_code_response, state)
            state["active_attempt"] = attempt
            state["last_status"] = self._attempt_status(attempt)
            worker = threading.Thread(
                target=self._poll_for_completion,
                args=(app, state, attempt),
                daemon=True,
            )
            attempt["worker"] = worker
            worker.start()
            auth_status = self._attempt_status(attempt)
            return {
                "display": self._status_display_payload(
                    auth_status, action="login_start"
                ),
                "auth_status": auth_status,
            }

    def _poll_for_completion(
        self, app: Any, state: Dict[str, Any], attempt: Dict[str, Any]
    ) -> None:
        cfg = self._config(state)
        protocol = cfg.get("protocol") or "codex_deviceauth"
        issuer = str(cfg.get("issuer") or _DEFAULT_ISSUER).rstrip("/")
        token_endpoint = cfg.get("token_endpoint") or (
            f"{issuer}/api/accounts/deviceauth/token"
            if protocol == "codex_deviceauth"
            else None
        )
        token_exchange_endpoint = (
            cfg.get("token_exchange_endpoint") or f"{issuer}/oauth/token"
        )
        client_id = cfg.get("client_id")
        if not isinstance(token_endpoint, str) or not token_endpoint:
            return
        if not isinstance(client_id, str) or not client_id:
            return

        login_id = attempt.get("login_id")
        poll_interval = _coerce_positive_int(
            attempt.get("poll_interval_seconds"),
            cfg.get("device_code_poll_interval_seconds"),
        )
        cancel_event = attempt.get("cancel_event")
        if not isinstance(cancel_event, threading.Event):
            return

        while True:
            if cancel_event.wait(timeout=poll_interval):
                with self._lock:
                    attempt["state"] = "canceled"
                    state["last_status"] = self._attempt_status(attempt)
                self._publish_auth_event(app, state["last_status"])
                return

            expires_at = _parse_iso8601(attempt.get("expires_at"))
            if expires_at is not None and _utcnow() >= expires_at:
                with self._lock:
                    attempt["state"] = "failed"
                    attempt["error"] = "device_code_expired"
                    state["last_status"] = self._attempt_status(attempt)
                self._publish_auth_event(app, state["last_status"])
                return

            if protocol == "codex_deviceauth":
                payload = {
                    "device_auth_id": attempt.get("device_auth_id"),
                    "user_code": attempt.get("user_code"),
                }
            else:
                payload = {
                    "grant_type": _DEVICE_CODE_GRANT_TYPE,
                    "device_code": attempt.get("device_code"),
                    "client_id": client_id,
                }
                if isinstance(cfg.get("client_secret"), str) and cfg.get(
                    "client_secret"
                ):
                    payload["client_secret"] = cfg["client_secret"]
                payload.update(cfg.get("token_request") or {})

            try:
                status_code, token_response = self._request_payload(
                    url=token_endpoint,
                    payload=payload,
                    headers=cfg.get("headers") or {},
                    encoding=str(cfg.get("request_encoding") or "json"),
                    timeout=_coerce_positive_float(
                        cfg.get("http_timeout_seconds"),
                        _DEFAULT_HTTP_TIMEOUT_SECONDS,
                    ),
                )
            except Exception as exc:
                with self._lock:
                    attempt["state"] = "failed"
                    attempt["error"] = str(exc)
                    state["last_status"] = self._attempt_status(attempt)
                self._publish_auth_event(app, state["last_status"])
                return

            error_code = (
                token_response.get("error")
                if isinstance(token_response.get("error"), str)
                else None
            )
            if protocol == "codex_deviceauth" and status_code in {403, 404}:
                continue
            if error_code in _NON_FATAL_TOKEN_ERRORS:
                if error_code == "slow_down":
                    poll_interval += 1
                    attempt["poll_interval_seconds"] = poll_interval
                continue

            if (
                protocol == "codex_deviceauth"
                and status_code < 400
                and isinstance(token_response.get("authorization_code"), str)
            ):
                try:
                    exchanged = self._exchange_authorization_code(
                        token_exchange_endpoint,
                        authorization_code=str(
                            token_response.get("authorization_code")
                        ),
                        code_verifier=str(token_response.get("code_verifier") or ""),
                        client_id=client_id,
                        redirect_uri=str(
                            cfg.get("redirect_uri") or f"{issuer}/deviceauth/callback"
                        ),
                        timeout=_coerce_positive_float(
                            cfg.get("http_timeout_seconds"),
                            _DEFAULT_HTTP_TIMEOUT_SECONDS,
                        ),
                    )
                except Exception as exc:
                    with self._lock:
                        attempt["state"] = "failed"
                        attempt["error"] = str(exc)
                        state["last_status"] = self._attempt_status(attempt)
                    self._publish_auth_event(app, state["last_status"])
                    return
                credentials = self._normalized_credentials(exchanged, login_id=login_id)
                credentials["id_token"] = exchanged.get("id_token")
                if exchanged.get("account_id") is not None:
                    credentials["account_id"] = exchanged.get("account_id")
                if exchanged.get("account_email") is not None:
                    credentials["account_email"] = exchanged.get("account_email")
                if exchanged.get("plan_type") is not None:
                    credentials["plan_type"] = exchanged.get("plan_type")
                credentials["provider"] = "chatgpt_codex_deviceauth"
                credentials["issuer"] = issuer
                credentials["client_id"] = client_id
                credentials["credentials_path"] = str(self._credentials_path(state))
                credentials_path = self._credentials_path(state)
                _write_json_atomic(credentials_path, credentials)
                with self._lock:
                    attempt["state"] = "authenticated"
                    attempt["account_email"] = credentials.get("account_email")
                    attempt["plan_type"] = credentials.get("plan_type")
                    state["last_status"] = self._credentials_status(credentials)
                self._publish_auth_event(app, state["last_status"])
                return

            if status_code < 400 and isinstance(
                token_response.get("access_token"), str
            ):
                credentials = self._normalized_credentials(
                    token_response, login_id=login_id
                )
                credentials["issuer"] = issuer
                credentials["client_id"] = client_id
                credentials["credentials_path"] = str(self._credentials_path(state))
                credentials_path = self._credentials_path(state)
                _write_json_atomic(credentials_path, credentials)
                with self._lock:
                    attempt["state"] = "authenticated"
                    attempt["account_email"] = credentials.get("account_email")
                    attempt["plan_type"] = credentials.get("plan_type")
                    state["last_status"] = self._credentials_status(credentials)
                self._publish_auth_event(app, state["last_status"])
                return

            error_detail = (
                token_response.get("error_description")
                if isinstance(token_response.get("error_description"), str)
                else error_code
            )
            if error_code in _TERMINAL_TOKEN_ERRORS or status_code >= 400:
                with self._lock:
                    attempt["state"] = "failed"
                    attempt["error"] = (
                        error_detail
                        or f"token polling failed with status {status_code}"
                    )
                    state["last_status"] = self._attempt_status(attempt)
                self._publish_auth_event(app, state["last_status"])
                return

    def _exchange_authorization_code(
        self,
        token_exchange_endpoint: str,
        *,
        authorization_code: str,
        code_verifier: str,
        client_id: str,
        redirect_uri: str,
        timeout: float,
    ) -> Dict[str, Any]:
        if not authorization_code:
            raise RuntimeError(
                "[chatgpt_auth] token poll response missing authorization_code"
            )
        if not code_verifier:
            raise RuntimeError(
                "[chatgpt_auth] token poll response missing code_verifier"
            )
        status_code, response = self._request_payload(
            url=token_exchange_endpoint,
            payload={
                "grant_type": "authorization_code",
                "code": authorization_code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "code_verifier": code_verifier,
            },
            headers={},
            encoding="form",
            timeout=timeout,
        )
        if status_code >= 400:
            detail = (
                response.get("error_description")
                if isinstance(response.get("error_description"), str)
                else response.get("error")
            )
            raise RuntimeError(
                f"authorization code exchange failed: {detail or status_code}"
            )
        return response

    def _normalized_credentials(
        self, token_response: Dict[str, Any], *, login_id: Any
    ) -> Dict[str, Any]:
        obtained_at = _utcnow()
        expires_in = token_response.get("expires_in")
        expires_at = None
        if expires_in is not None:
            expires_at = _isoformat_utc(
                obtained_at
                + timedelta(
                    seconds=_coerce_positive_int(
                        expires_in, _DEFAULT_LOGIN_TIMEOUT_SECONDS
                    )
                )
            )
        id_token = token_response.get("id_token")
        claims = _jwt_claims(id_token)
        return {
            "provider": "chatgpt_device_code",
            "login_id": str(login_id) if login_id is not None else None,
            "access_token": token_response.get("access_token"),
            "refresh_token": token_response.get("refresh_token"),
            "id_token": id_token,
            "token_type": _normalized_token_type(token_response.get("token_type")),
            "scope": token_response.get("scope"),
            "obtained_at": _isoformat_utc(obtained_at),
            "expires_at": expires_at,
            "account_email": token_response.get("account_email")
            or token_response.get("email")
            or claims.get("email"),
            "account_id": token_response.get("account_id")
            or claims.get("chatgpt_account_id")
            or claims.get("sub"),
            "plan_type": token_response.get("plan_type")
            or claims.get("chatgpt_plan_type"),
        }

    def _credentials_status(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        state = (
            "authenticated"
            if self._credentials_are_valid(credentials)
            else "logged_out"
        )
        return {
            "state": state,
            "login_id": credentials.get("login_id"),
            "account_email": credentials.get("account_email"),
            "account_id": credentials.get("account_id"),
            "plan_type": credentials.get("plan_type"),
            "credentials_path": (
                str(credentials.get("credentials_path"))
                if isinstance(credentials.get("credentials_path"), Path)
                else credentials.get("credentials_path")
            ),
            "error": (
                "saved credentials have expired" if state != "authenticated" else None
            ),
        }

    def _credentials_are_valid(self, credentials: Dict[str, Any]) -> bool:
        token = credentials.get("access_token")
        if not isinstance(token, str) or not token.strip():
            return False
        expires_at = _parse_iso8601(credentials.get("expires_at"))
        if expires_at is None:
            return True
        return _utcnow() < expires_at

    def _attempt_status(self, attempt: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "state": attempt.get("state") or "pending",
            "login_id": attempt.get("login_id"),
            "verification_url": attempt.get("verification_url"),
            "user_code": attempt.get("user_code"),
            "started_at": attempt.get("started_at"),
            "expires_at": attempt.get("expires_at"),
            "account_email": attempt.get("account_email"),
            "plan_type": attempt.get("plan_type"),
            "error": attempt.get("error"),
        }

    def _current_status(self, state: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            active_attempt = state.get("active_attempt")
            if (
                isinstance(active_attempt, dict)
                and active_attempt.get("state") == "pending"
            ):
                return self._attempt_status(active_attempt)
            credentials_path = self._credentials_path(state)
            credentials = _read_json(credentials_path)
            if isinstance(credentials, dict):
                credentials["credentials_path"] = str(credentials_path)
                status = self._credentials_status(credentials)
                state["last_status"] = status
                return status
            last_status = state.get("last_status")
            if isinstance(last_status, dict):
                return dict(last_status)
            return {"state": "logged_out", "login_id": None, "error": None}

    def _show_account_status(
        self,
        app: Any,
        state: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id is required")

        config = self._session_config(app, session_id)
        auth_status = self._current_status(state)
        requested_mode = _normalize_auth_mode(config.get("auth_mode"))
        effective_mode = self._effective_auth_mode(config, auth_status)
        supported = self._should_show_session_actions(
            config, [f"provider:{config.get('provider')}"]
        )

        rate_limits_path = _resolve_rate_limits_path(config)
        rate_limits_state = _read_json(rate_limits_path) or {}
        rate_limit_lines = self._render_rate_limit_lines(rate_limits_state)
        endpoint = (
            config.get("chatgpt_base_url")
            if effective_mode == "chatgpt"
            else config.get("api_base_url") or config.get("base_url")
        )

        lines: List[str] = []
        variant = "success" if auth_status.get("state") == "authenticated" else "info"
        if not supported:
            variant = "warning"
            lines.append(
                "ChatGPT account status is only available for OpenAI Responses sessions with `auth_mode` set to `auto` or `chatgpt`."
            )
        else:
            lines.append(f"Requested auth mode: `{requested_mode}`")
            lines.append(f"Effective auth mode: `{effective_mode}`")
            lines.append(f"Login state: `{auth_status.get('state') or 'unknown'}`")
            account_email = auth_status.get("account_email")
            account_id = auth_status.get("account_id")
            plan_type = auth_status.get("plan_type") or rate_limits_state.get(
                "plan_type"
            )
            if isinstance(account_email, str) and account_email:
                lines.append(f"Account: `{account_email}`")
            if isinstance(account_id, str) and account_id:
                lines.append(f"Account ID: `{account_id}`")
            if isinstance(plan_type, str) and plan_type:
                lines.append(f"Plan: `{plan_type}`")
            if isinstance(endpoint, str) and endpoint:
                lines.append(f"Endpoint: `{endpoint}`")
            lines.append("")
            lines.append("Usage limits:")
            if rate_limit_lines:
                lines.extend(rate_limit_lines)
            else:
                lines.append(
                    "- Not available yet. Run a ChatGPT-backed request to refresh."
                )

            journal_path = self._usage_journal_path(state, config)
            report = usage_journal.build_usage_report(journal_path)
            totals = (
                report.get("totals") if isinstance(report.get("totals"), dict) else {}
            )
            if totals.get("request_count"):
                lines.append("")
                lines.append("Estimated usage since reset:")
                lines.append(f"- Requests: `{totals.get('request_count', 0):,}`")
                lines.append(f"- Input tokens: `{totals.get('input_tokens', 0):,}`")
                lines.append(f"- Output tokens: `{totals.get('output_tokens', 0):,}`")
                lines.append(
                    f"- Estimated cost: `${float(totals.get('estimated_cost', 0.0)):.6f}`"
                )

        display = {
            "format": "markdown",
            "title": "ChatGPT Account Status",
            "body": "\n".join(lines),
            "variant": variant,
        }
        return {
            "display": display,
            "auth_status": auth_status,
            "rate_limits": rate_limits_state,
            "requested_auth_mode": requested_mode,
            "effective_auth_mode": effective_mode,
        }

    def _usage_journal_path(
        self,
        state: Dict[str, Any],
        session_config: Dict[str, Any],
    ) -> Path:
        app_cfg = self._config(state)
        candidates: List[Path] = []
        seen = set()
        for cfg in (
            session_config,
            {
                "chatgpt_rate_limits_path": app_cfg.get("rate_limits_path"),
                "chatgpt_credentials_path": app_cfg.get("credentials_path"),
            },
        ):
            try:
                path = usage_journal.resolve_usage_journal_path(cfg)
            except Exception:
                continue
            if str(path) not in seen:
                seen.add(str(path))
                candidates.append(path)
        for path in candidates:
            if path.exists():
                return path
        return (
            candidates[0]
            if candidates
            else usage_journal.resolve_usage_journal_path(session_config)
        )

    def _usage_summary_csv_path(
        self,
        config: Dict[str, Any],
        journal_path: Path,
    ) -> Path:
        """Resolve the simplified usage summary CSV path for the reset marker.

        Mirrors the openai_responses journal writer: an explicit
        ``chatgpt_usage_summary_csv_path`` override wins; otherwise the CSV
        lives next to the resolved journal file.
        """

        raw = config.get("chatgpt_usage_summary_csv_path")
        if isinstance(raw, str) and raw.strip():
            try:
                return Path(raw).expanduser()
            except Exception:
                return journal_path.with_name(
                    usage_journal.DEFAULT_CHATGPT_USAGE_SUMMARY_CSV_FILENAME
                )
        return journal_path.with_name(
            usage_journal.DEFAULT_CHATGPT_USAGE_SUMMARY_CSV_FILENAME
        )

    def _append_usage_summary_reset_row(
        self,
        config: Dict[str, Any],
        journal_path: Path,
    ) -> None:
        """Append a reset row to the simplified usage summary CSV. Best-effort.

        Gated by ``track_chatgpt_usage_summary_csv`` (default enabled), the
        same key the openai_responses journal writer honors.
        """

        if config.get("track_chatgpt_usage_summary_csv") is False:
            return
        try:
            usage_journal.append_summary_reset_row(
                self._usage_summary_csv_path(config, journal_path)
            )
        except Exception:
            return

    def _render_report_limit_lines(
        self,
        latest_rate_limits: Optional[Dict[str, Any]],
    ) -> List[str]:
        if not isinstance(latest_rate_limits, dict):
            return []
        snapshots = latest_rate_limits.get("snapshots")
        if not isinstance(snapshots, list):
            return []
        lines: List[str] = []
        for snapshot in snapshots:
            if not isinstance(snapshot, dict):
                continue
            limit_id = snapshot.get("limit_id")
            bucket = (
                str(limit_id) if isinstance(limit_id, str) and limit_id else "codex"
            )
            window_count = int(isinstance(snapshot.get("primary"), dict)) + int(
                isinstance(snapshot.get("secondary"), dict)
            )
            prefix_non_codex_single = bucket != "codex" and window_count == 1
            if bucket != "codex" and window_count > 1:
                lines.append(f"- `{bucket}`")
            for window_kind, fallback in (
                ("primary", "5h limit"),
                ("secondary", "Weekly limit"),
            ):
                window = snapshot.get(window_kind)
                if not isinstance(window, dict):
                    continue
                label = _format_limit_label(window, fallback)
                if prefix_non_codex_single:
                    label = f"{bucket} {label}"
                percent_used = window.get("used_percent")
                percent_remaining = (
                    100.0 - float(percent_used)
                    if isinstance(percent_used, (int, float))
                    else None
                )
                reset_text = _format_reset_time(window.get("resets_at"))
                line = f"- {label}: "
                if percent_remaining is not None:
                    line += f"`{percent_remaining:.0f}% left`"
                else:
                    line += "`usage available`"
                if isinstance(reset_text, str) and reset_text:
                    line += f" (resets `{reset_text}`)"
                lines.append(line)
        return lines

    def _render_report_percent_history(
        self,
        percent_summary: List[Dict[str, Any]],
    ) -> List[str]:
        lines: List[str] = []
        for summary in percent_summary:
            if not isinstance(summary, dict):
                continue
            limit_id = summary.get("limit_id")
            bucket = (
                str(limit_id) if isinstance(limit_id, str) and limit_id else "codex"
            )
            label = _format_limit_label(
                summary,
                "5h limit" if summary.get("window") == "primary" else "Weekly limit",
            )
            if bucket != "codex":
                label = f"{bucket} {label}"
            first = summary.get("first_used_percent")
            last = summary.get("last_used_percent")
            minimum = summary.get("min_used_percent")
            maximum = summary.get("max_used_percent")
            if not all(
                isinstance(value, (int, float))
                for value in (first, last, minimum, maximum)
            ):
                continue
            line = (
                f"- {label}: `{first:.0f}%` → `{last:.0f}%` "
                f"(min `{minimum:.0f}%`, max `{maximum:.0f}%`)"
            )
            lines.append(line)
        return lines

    def _show_usage_report(
        self,
        app: Any,
        state: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = app
        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id is required")

        config = self._session_config(app, session_id)
        supported = self._should_show_session_actions(
            config, [f"provider:{config.get('provider')}"]
        )
        if not supported:
            display = {
                "format": "markdown",
                "title": "ChatGPT Usage Report",
                "body": (
                    "ChatGPT usage reports are only available for OpenAI Responses "
                    "sessions with `auth_mode` set to `auto` or `chatgpt`."
                ),
                "variant": "warning",
            }
            return {"display": display}

        raw_from = params.get("from")
        raw_to = params.get("to")
        from_dt = None
        to_dt = None
        invalid_inputs: List[str] = []
        if isinstance(raw_from, str) and raw_from.strip():
            from_dt = usage_journal.parse_report_datetime(raw_from)
            if from_dt is None:
                invalid_inputs.append(f"from (`{raw_from.strip()}`)")
        if isinstance(raw_to, str) and raw_to.strip():
            to_dt = usage_journal.parse_report_datetime(raw_to)
            if to_dt is None:
                invalid_inputs.append(f"to (`{raw_to.strip()}`)")
        if invalid_inputs:
            body_lines = [
                "Could not read the requested date range:",
            ]
            body_lines.extend(f"- {item}" for item in invalid_inputs)
            body_lines.append("")
            body_lines.append(
                "Use a date like `2026-09-19` or a date and time like "
                "`2026-09-19 14:30` (interpreted in the server's timezone)."
            )
            return {
                "display": {
                    "format": "markdown",
                    "title": "ChatGPT Usage Report",
                    "body": "\n".join(body_lines),
                    "variant": "error",
                    "form": self._report_range_form(raw_from, raw_to),
                    "actions": self._report_range_actions(session_id),
                }
            }
        if from_dt is not None and to_dt is not None and from_dt > to_dt:
            return {
                "display": {
                    "format": "markdown",
                    "title": "ChatGPT Usage Report",
                    "body": "The `from` date must not be after the `to` date.",
                    "variant": "error",
                    "form": self._report_range_form(raw_from, raw_to),
                    "actions": self._report_range_actions(session_id),
                }
            }

        journal_path = self._usage_journal_path(state, config)
        report = usage_journal.build_usage_report(
            journal_path, from_dt=from_dt, to_dt=to_dt
        )
        totals = report.get("totals") if isinstance(report.get("totals"), dict) else {}

        lines: List[str] = []
        if from_dt is None and to_dt is None:
            reset_at = report.get("reset_at")
            if isinstance(reset_at, str) and reset_at:
                lines.append(f"Tracking since reset: `{reset_at}`")
            else:
                lines.append("Tracking since: `journal start (no reset marker yet)`")
        else:
            from_text = (
                from_dt.strftime("%Y-%m-%d %H:%M") if from_dt is not None else "start"
            )
            to_text = to_dt.strftime("%Y-%m-%d %H:%M") if to_dt is not None else "now"
            lines.append(f"Date range: `{from_text}` → `{to_text}`")
        lines.append("")
        lines.append("Estimated usage:")
        lines.append(f"- Requests: `{totals.get('request_count', 0):,}`")
        lines.append(f"- Input tokens: `{totals.get('input_tokens', 0):,}`")
        lines.append(f"- Cached tokens: `{totals.get('cached_tokens', 0):,}`")
        lines.append(f"- Cache write tokens: `{totals.get('cache_write_tokens', 0):,}`")
        lines.append(f"- Output tokens: `{totals.get('output_tokens', 0):,}`")
        lines.append(f"- Reasoning tokens: `{totals.get('reasoning_tokens', 0):,}`")
        lines.append(
            f"- Estimated cost: `${float(totals.get('estimated_cost', 0.0)):.6f}`"
        )

        limit_lines = self._render_report_limit_lines(report.get("latest_rate_limits"))
        lines.append("")
        lines.append("Current usage limits:")
        if limit_lines:
            lines.extend(limit_lines)
        else:
            lines.append(
                "- Not available yet. Run a ChatGPT-backed request to refresh."
            )

        percent_lines = self._render_report_percent_history(
            report.get("percent_summary") or []
        )
        lines.append("")
        lines.append("Usage percent history:")
        if percent_lines:
            lines.extend(percent_lines)
        else:
            lines.append("- No usage percentages recorded yet.")

        return {
            "display": {
                "format": "markdown",
                "title": "ChatGPT Usage Report",
                "body": "\n".join(lines),
                "variant": "info",
                "form": self._report_range_form(raw_from, raw_to),
                "actions": self._report_range_actions(session_id),
            },
            "usage_report": report,
        }

    def _report_range_form(self, raw_from: Any, raw_to: Any) -> Dict[str, Any]:
        inputs = [
            {
                "name": "from",
                "type": "string",
                "label": "From",
                "placeholder": "2026-09-19 or 2026-09-19 14:30",
                "required": False,
                "submit_empty": True,
            },
            {
                "name": "to",
                "type": "string",
                "label": "To",
                "placeholder": "2026-09-20 or 2026-09-20 09:00",
                "required": False,
                "submit_empty": True,
            },
        ]
        if isinstance(raw_from, str) and raw_from.strip():
            inputs[0]["default"] = raw_from.strip()
        if isinstance(raw_to, str) and raw_to.strip():
            inputs[1]["default"] = raw_to.strip()
        return {"kind": "form", "inputs": inputs}

    def _report_range_actions(self, session_id: str) -> List[Dict[str, Any]]:
        return [
            {
                "kind": "run_action",
                "id": "chatgpt-usage-apply-range",
                "label": "Apply date range",
                "plugin": self.name,
                "action_id": "show_usage_report",
                "fixed_params": {"session_id": session_id},
                "param_map": {
                    "from": "$form.from",
                    "to": "$form.to",
                },
            },
            {
                "kind": "dismiss",
                "id": "chatgpt-usage-close-report",
                "label": "Close",
            },
        ]

    def _reset_usage_tracking(
        self,
        app: Any,
        state: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = app
        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id is required")

        config = self._session_config(app, session_id)
        supported = self._should_show_session_actions(
            config, [f"provider:{config.get('provider')}"]
        )
        if not supported:
            return {
                "display": {
                    "format": "markdown",
                    "title": "ChatGPT Usage Tracking",
                    "body": (
                        "ChatGPT usage tracking is only available for OpenAI Responses "
                        "sessions with `auth_mode` set to `auto` or `chatgpt`."
                    ),
                    "variant": "warning",
                }
            }

        journal_path = self._usage_journal_path(state, config)
        appended = usage_journal.append_usage_reset(journal_path)
        if appended:
            self._append_usage_summary_reset_row(config, journal_path)
            body = (
                "Usage tracking was reset. New usage reports start counting from now.\n\n"
                "Previous journal history is preserved and stays inspectable by date."
            )
            variant = "success"
        else:
            body = (
                "Could not append the reset marker to the usage journal. "
                "Check server logs for details."
            )
            variant = "error"
        return {
            "display": {
                "format": "markdown",
                "title": "ChatGPT Usage Tracking Reset",
                "body": body,
                "variant": variant,
                "actions": [
                    {
                        "kind": "run_action",
                        "id": "chatgpt-usage-open-report",
                        "label": "Show usage report",
                        "plugin": self.name,
                        "action_id": "show_usage_report",
                        "fixed_params": {"session_id": session_id},
                    },
                    {
                        "kind": "dismiss",
                        "id": "chatgpt-usage-close-reset",
                        "label": "Close",
                    },
                ],
            },
            "reset_appended": appended,
        }

    def _cancel_login(self, app: Any, state: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            active_attempt = state.get("active_attempt")
            if (
                not isinstance(active_attempt, dict)
                or active_attempt.get("state") != "pending"
            ):
                status = self._current_status(state)
                return status
            cancel_event = active_attempt.get("cancel_event")
            if isinstance(cancel_event, threading.Event):
                cancel_event.set()
            active_attempt["state"] = "canceled"
            status = self._attempt_status(active_attempt)
            state["last_status"] = status
        self._publish_auth_event(app, status)
        return status

    def _logout(self, app: Any, state: Dict[str, Any]) -> Dict[str, Any]:
        status = self._cancel_login(app, state)
        _ = status
        with self._lock:
            _remove_file(self._credentials_path(state))
            _remove_file(self._rate_limits_path(state))
            active_attempt = state.get("active_attempt")
            if (
                isinstance(active_attempt, dict)
                and active_attempt.get("state") == "canceled"
            ):
                state["active_attempt"] = None
            state["last_status"] = {
                "state": "logged_out",
                "login_id": None,
                "error": None,
            }
            status = dict(state["last_status"])
        self._publish_auth_event(app, status)
        return status

    def _publish_auth_event(self, app: Any, auth_status: Dict[str, Any]) -> None:
        publish = getattr(app, "publish_event", None)
        if not callable(publish):
            return
        try:
            publish(
                {
                    "type": "chatgpt_auth_status",
                    "auth_status": dict(auth_status),
                    "timestamp": _isoformat_utc(_utcnow()),
                }
            )
        except Exception:
            return

    def _status_display_payload(
        self, auth_status: Dict[str, Any], *, action: str
    ) -> Dict[str, Any]:
        state = str(auth_status.get("state") or "unknown")
        title = "ChatGPT Login"
        variant = "info"
        lines: List[str] = []
        actions: List[Dict[str, Any]] = []
        checked_at = _isoformat_utc(_utcnow())

        if action == "logout":
            title = "ChatGPT Logout"
        elif action == "cancel_login":
            title = "ChatGPT Login Canceled"
        elif action == "check_status":
            title = "ChatGPT Login Status"

        if state == "pending":
            variant = "info"
            verification_url = auth_status.get("verification_url")
            user_code = auth_status.get("user_code")
            if isinstance(verification_url, str) and verification_url:
                lines.append(f"1. Open [ChatGPT device login]({verification_url})")
                actions.append(
                    {
                        "kind": "open_url",
                        "id": "open-chatgpt-login-link",
                        "label": "Open link",
                        "url": verification_url,
                    }
                )
            else:
                lines.append("1. Open the ChatGPT device login page in your browser.")
            if isinstance(user_code, str) and user_code:
                lines.append(f"2. Enter code `{user_code}`")
                actions.append(
                    {
                        "kind": "copy_text",
                        "id": "copy-chatgpt-login-code",
                        "label": "Copy code",
                        "text": user_code,
                        "copied_label": "Copied",
                    }
                )
            lines.append("")
            lines.append(
                "When you are done, return here and run **Show ChatGPT login status**."
            )
            expires_at = auth_status.get("expires_at")
            if isinstance(expires_at, str) and expires_at:
                lines.append("")
                lines.append(f"Code expires at: `{expires_at}`")
            if action == "check_status":
                lines.append("")
                lines.append(f"Last checked at: `{checked_at}`")
            actions.append(
                {
                    "kind": "run_action",
                    "id": "check-chatgpt-login-status",
                    "label": "Check status",
                    "plugin": self.name,
                    "action_id": "check_status",
                    "fixed_params": {},
                    "preserve_display": True,
                }
            )
        elif state == "authenticated":
            variant = "success"
            lines.append("ChatGPT login is active.")
            account_email = auth_status.get("account_email")
            account_id = auth_status.get("account_id")
            plan_type = auth_status.get("plan_type")
            if isinstance(account_email, str) and account_email:
                lines.append(f"Account: `{account_email}`")
            if isinstance(account_id, str) and account_id:
                lines.append(f"Account ID: `{account_id}`")
            if isinstance(plan_type, str) and plan_type:
                lines.append(f"Plan: `{plan_type}`")
        elif state == "canceled":
            variant = "warning"
            lines.append("The background ChatGPT login attempt was canceled.")
        elif state == "failed":
            variant = "error"
            lines.append("ChatGPT login failed.")
            error = auth_status.get("error")
            if isinstance(error, str) and error:
                lines.append("")
                lines.append(f"Error: `{error}`")
        elif state == "logged_out":
            variant = "info"
            if action == "logout":
                lines.append("Saved ChatGPT credentials were removed.")
            else:
                lines.append("No active ChatGPT login was found.")
        else:
            lines.append(f"Current ChatGPT auth state: `{state}`")

        payload = {
            "format": "markdown",
            "title": title,
            "body": "\n".join(lines),
            "variant": variant,
        }
        if state == "pending":
            payload["presentation"] = "inline"
            payload["dismissible"] = True
            payload["display_id"] = "chatgpt-auth-login"
            payload["actions"] = actions
        return payload


__all__ = ["ChatGPTAuthAppPlugin"]
