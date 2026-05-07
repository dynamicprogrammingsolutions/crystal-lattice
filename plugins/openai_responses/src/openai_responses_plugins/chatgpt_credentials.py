from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_CHATGPT_CREDENTIALS_RELATIVE_PATH = "auth/chatgpt-auth.json"
DEFAULT_CHATGPT_REFRESH_ENDPOINT = "https://auth.openai.com/oauth/token"
DEFAULT_CHATGPT_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"


class ChatGPTRefreshError(RuntimeError):
    """Base class for managed ChatGPT token refresh failures."""


class ChatGPTRefreshPermanentError(ChatGPTRefreshError):
    """Raised when the saved login is no longer refreshable."""


class ChatGPTRefreshTransientError(ChatGPTRefreshError):
    """Raised when refresh failed due to a transient network or service issue."""


def parse_iso8601(value: Any) -> Optional[datetime]:
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


def isoformat_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalized_token_type(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return "Bearer"
    normalized = value.strip()
    if normalized.lower() == "bearer":
        return "Bearer"
    return normalized


def jwt_claims(jwt: Any) -> Dict[str, Any]:
    if not isinstance(jwt, str) or not jwt:
        return {}
    parts = jwt.split(".")
    if len(parts) != 3:
        return {}
    payload = parts[1]
    padding = "=" * (-len(payload) % 4)
    try:
        import base64

        decoded = base64.urlsafe_b64decode(payload + padding)
        parsed = json.loads(decoded.decode("utf-8"))
    except Exception:
        return {}
    if not isinstance(parsed, dict):
        return {}
    nested = parsed.get("https://api.openai.com/auth")
    return nested if isinstance(nested, dict) else parsed


def resolve_credentials_path(config: Dict[str, Any]) -> Path:
    raw = config.get("chatgpt_credentials_path")
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()
    config_dir = os.environ.get("CONFIG_DIR")
    if isinstance(config_dir, str) and config_dir:
        return Path(config_dir).expanduser() / DEFAULT_CHATGPT_CREDENTIALS_RELATIVE_PATH
    return Path.cwd() / DEFAULT_CHATGPT_CREDENTIALS_RELATIVE_PATH


def load_credentials(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    ensure_parent_dir(path)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def credentials_are_valid(credentials: Dict[str, Any]) -> bool:
    token = credentials.get("access_token")
    if not isinstance(token, str) or not token.strip():
        return False
    expires_at = parse_iso8601(credentials.get("expires_at"))
    if expires_at is None:
        return True
    return datetime.now(timezone.utc) < expires_at


def credentials_have_access_token(credentials: Dict[str, Any]) -> bool:
    token = credentials.get("access_token")
    return isinstance(token, str) and bool(token.strip())


def credentials_from_token_response(
    token_response: Dict[str, Any],
    *,
    previous_credentials: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    previous = dict(previous_credentials or {})
    now = datetime.now(timezone.utc)
    access_token = token_response.get("access_token")
    refresh_token = token_response.get("refresh_token")
    id_token = token_response.get("id_token")
    expires_in = token_response.get("expires_in")

    claims = jwt_claims(id_token if isinstance(id_token, str) and id_token else previous.get("id_token"))

    next_credentials: Dict[str, Any] = {
        **previous,
        "access_token": access_token if isinstance(access_token, str) and access_token else previous.get("access_token"),
        "refresh_token": (
            refresh_token if isinstance(refresh_token, str) and refresh_token else previous.get("refresh_token")
        ),
        "id_token": id_token if isinstance(id_token, str) and id_token else previous.get("id_token"),
        "token_type": normalized_token_type(token_response.get("token_type") or previous.get("token_type")),
        "scope": token_response.get("scope") or previous.get("scope"),
        "obtained_at": isoformat_utc(now),
        "account_email": (
            token_response.get("account_email")
            or token_response.get("email")
            or claims.get("email")
            or previous.get("account_email")
        ),
        "account_id": (
            token_response.get("account_id")
            or claims.get("chatgpt_account_id")
            or claims.get("sub")
            or previous.get("account_id")
        ),
        "plan_type": (
            token_response.get("plan_type")
            or claims.get("chatgpt_plan_type")
            or previous.get("plan_type")
        ),
    }

    if expires_in is not None:
        try:
            expires_in_seconds = int(expires_in)
        except (TypeError, ValueError):
            expires_in_seconds = 0
        if expires_in_seconds > 0:
            next_credentials["expires_at"] = isoformat_utc(now + timedelta(seconds=expires_in_seconds))
        else:
            next_credentials.pop("expires_at", None)
    elif "access_token" in token_response:
        next_credentials.pop("expires_at", None)

    return next_credentials


def _extract_error_code(payload: Dict[str, Any]) -> Optional[str]:
    error_value = payload.get("error")
    if isinstance(error_value, dict):
        code = error_value.get("code")
        if isinstance(code, str) and code:
            return code
    if isinstance(error_value, str) and error_value:
        return error_value
    code = payload.get("code")
    if isinstance(code, str) and code:
        return code
    return None


def _classify_refresh_failure(payload: Dict[str, Any], fallback_body: str) -> ChatGPTRefreshError:
    code = _extract_error_code(payload)
    normalized = code.lower() if isinstance(code, str) else None
    if normalized in {"refresh_token_expired", "refresh_token_reused", "refresh_token_invalidated"}:
        return ChatGPTRefreshPermanentError(
            "Saved ChatGPT login expired or was revoked. Please sign in again."
        )
    if normalized in {"invalid_grant", "access_denied", "expired_token"}:
        return ChatGPTRefreshPermanentError(
            "Saved ChatGPT login cannot be refreshed. Please sign in again."
        )
    detail = payload.get("error_description")
    if not isinstance(detail, str) or not detail.strip():
        detail = fallback_body.strip() or "unknown refresh error"
    return ChatGPTRefreshTransientError(f"Failed to refresh ChatGPT credentials: {detail}")


def refresh_chatgpt_credentials(
    path: Path,
    *,
    timeout: float,
    refresh_endpoint: str = DEFAULT_CHATGPT_REFRESH_ENDPOINT,
    client_id: str = DEFAULT_CHATGPT_CLIENT_ID,
) -> Dict[str, Any]:
    current_credentials = load_credentials(path)
    refresh_token = current_credentials.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token.strip():
        raise ChatGPTRefreshPermanentError(
            "Saved ChatGPT login cannot be refreshed. Please sign in again."
        )

    body = json.dumps(
        {
            "client_id": client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token.strip(),
        }
    ).encode("utf-8")
    request = Request(
        refresh_endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8")
    except HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw_body) if raw_body else {}
        except Exception:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        if exc.code == 401:
            raise _classify_refresh_failure(payload, raw_body) from exc
        raise ChatGPTRefreshTransientError(
            f"Failed to refresh ChatGPT credentials: HTTP {exc.code}"
        ) from exc
    except URLError as exc:
        raise ChatGPTRefreshTransientError(
            f"Failed to refresh ChatGPT credentials: {exc}"
        ) from exc

    try:
        token_response = json.loads(raw_body)
    except Exception as exc:
        raise ChatGPTRefreshTransientError(
            "Failed to refresh ChatGPT credentials: auth service returned invalid JSON"
        ) from exc
    if not isinstance(token_response, dict):
        raise ChatGPTRefreshTransientError(
            "Failed to refresh ChatGPT credentials: auth service returned an unexpected payload"
        )

    next_credentials = credentials_from_token_response(
        token_response,
        previous_credentials=current_credentials,
    )
    write_json_atomic(path, next_credentials)
    return next_credentials


__all__ = [
    "ChatGPTRefreshError",
    "ChatGPTRefreshPermanentError",
    "ChatGPTRefreshTransientError",
    "DEFAULT_CHATGPT_CLIENT_ID",
    "DEFAULT_CHATGPT_CREDENTIALS_RELATIVE_PATH",
    "DEFAULT_CHATGPT_REFRESH_ENDPOINT",
    "credentials_are_valid",
    "credentials_from_token_response",
    "credentials_have_access_token",
    "isoformat_utc",
    "jwt_claims",
    "load_credentials",
    "normalized_token_type",
    "parse_iso8601",
    "refresh_chatgpt_credentials",
    "resolve_credentials_path",
    "write_json_atomic",
]