from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


_DEFAULT_CHATGPT_BASE_URL = "https://chatgpt.com/backend-api/codex"
_DEFAULT_CHATGPT_CREDENTIALS_RELATIVE_PATH = "auth/chatgpt-auth.json"


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


class OpenAIResponsesChatGPTAuthFeature:
    """Feature that loads saved ChatGPT credentials for OpenAI Responses."""

    name = "openai_responses_chatgpt_auth"
    version = "0.1.0"
    priority = 10

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "auth_mode": {
                "type": "string",
                "default": "api",
                "description": "Authentication mode: api, chatgpt, or auto.",
            },
            "api_base_url": {
                "type": "string",
                "default": "https://api.openai.com/v1",
                "description": "Base URL for normal OpenAI API mode.",
            },
            "chatgpt_base_url": {
                "type": "string",
                "default": _DEFAULT_CHATGPT_BASE_URL,
                "description": "Base URL used when ChatGPT auth mode is active.",
            },
            "chatgpt_account_id": {
                "type": "string",
                "description": "Optional ChatGPT account id override for ChatGPT-backed requests.",
            },
            "chatgpt_credentials_path": {
                "type": "string",
                "description": "Path to the saved ChatGPT credential file.",
            },
        }

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = context
        requested_mode = self._normalize_auth_mode(config.get("auth_mode"))
        credentials_path = self._credentials_path(config)
        credentials = self._load_credentials(credentials_path)
        has_valid_chatgpt = self._credentials_are_valid(credentials)
        if requested_mode == "chatgpt":
            effective_mode = "chatgpt"
        elif requested_mode == "auto" and has_valid_chatgpt:
            effective_mode = "chatgpt"
        else:
            effective_mode = "api"

        if effective_mode == "chatgpt":
            config_path = "chatgpt_base_url"
            default_value = self._chatgpt_base_url(config)
            description = "Effective endpoint URL used for ChatGPT-backed OpenAI Responses requests."
        else:
            config_path = "api_base_url" if config.get("api_base_url") else "base_url"
            default_value = self._api_base_url(config)
            description = "Effective endpoint URL used for normal OpenAI API requests."

        return [
            {
                "ui_type": "config",
                "type": "readonly",
                "key": "effective_base_url",
                "config_path": config_path,
                "label": "OpenAI endpoint URL",
                "description": description,
                "default": default_value,
            }
        ]

    def required_tags(self) -> List[str]:
        return ["provider:openai_responses"]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        requested_mode = self._normalize_auth_mode(config.get("auth_mode"))
        credentials_path = self._credentials_path(config)
        credentials = self._load_credentials(credentials_path)
        has_valid_chatgpt = self._credentials_are_valid(credentials)

        if requested_mode == "chatgpt":
            effective_mode = "chatgpt"
        elif requested_mode == "auto" and has_valid_chatgpt:
            effective_mode = "chatgpt"
        else:
            effective_mode = "api"

        api_base_url = self._api_base_url(config)
        chatgpt_base_url = self._chatgpt_base_url(config)
        runtime_config = dict(state.get("config") or config)
        runtime_config["auth_mode"] = requested_mode
        runtime_config["api_base_url"] = api_base_url
        runtime_config["chatgpt_base_url"] = chatgpt_base_url
        runtime_config["chatgpt_credentials_path"] = str(credentials_path)
        runtime_config["_openai_responses_effective_auth_mode"] = effective_mode

        if effective_mode == "chatgpt" and has_valid_chatgpt:
            runtime_config["chatgpt_access_token"] = credentials.get("access_token")
            runtime_config["chatgpt_token_type"] = credentials.get("token_type") or "Bearer"
            runtime_config["chatgpt_account_id"] = credentials.get("account_id") or config.get(
                "chatgpt_account_id"
            )
            runtime_config["base_url"] = chatgpt_base_url
        else:
            runtime_config.pop("chatgpt_access_token", None)
            runtime_config.pop("chatgpt_token_type", None)
            runtime_config.pop("chatgpt_account_id", None)
            runtime_config["base_url"] = api_base_url

        auth_state = {
            "requested_mode": requested_mode,
            "effective_mode": effective_mode,
            "credentials_path": str(credentials_path),
            "logged_in": has_valid_chatgpt,
            "account_email": credentials.get("account_email") if isinstance(credentials, dict) else None,
            "plan_type": credentials.get("plan_type") if isinstance(credentials, dict) else None,
        }
        return {
            **state,
            "config": runtime_config,
            "client": None,
            "_openai_responses_chatgpt_auth": auth_state,
        }

    def _normalize_auth_mode(self, raw: Any) -> str:
        if not isinstance(raw, str):
            return "api"
        normalized = raw.strip().lower()
        if normalized == "api_key":
            return "api"
        if normalized in {"api", "chatgpt", "auto"}:
            return normalized
        return "api"

    def _api_base_url(self, config: Dict[str, Any]) -> str:
        raw = config.get("api_base_url") or config.get("base_url") or "https://api.openai.com/v1"
        if not isinstance(raw, str) or not raw.strip():
            return "https://api.openai.com/v1"
        return raw.rstrip("/")

    def _chatgpt_base_url(self, config: Dict[str, Any]) -> str:
        raw = config.get("chatgpt_base_url") or _DEFAULT_CHATGPT_BASE_URL
        if not isinstance(raw, str) or not raw.strip():
            return _DEFAULT_CHATGPT_BASE_URL
        return raw.rstrip("/")

    def _credentials_path(self, config: Dict[str, Any]) -> Path:
        raw = config.get("chatgpt_credentials_path")
        if isinstance(raw, str) and raw.strip():
            return Path(raw).expanduser()
        config_dir = os.environ.get("CONFIG_DIR")
        if isinstance(config_dir, str) and config_dir:
            return Path(config_dir).expanduser() / _DEFAULT_CHATGPT_CREDENTIALS_RELATIVE_PATH
        return Path.cwd() / _DEFAULT_CHATGPT_CREDENTIALS_RELATIVE_PATH

    def _load_credentials(self, path: Path) -> Dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _credentials_are_valid(self, credentials: Dict[str, Any]) -> bool:
        token = credentials.get("access_token")
        if not isinstance(token, str) or not token.strip():
            return False
        expires_at = _parse_iso8601(credentials.get("expires_at"))
        if expires_at is None:
            return True
        return datetime.now(timezone.utc) < expires_at


__all__ = ["OpenAIResponsesChatGPTAuthFeature"]