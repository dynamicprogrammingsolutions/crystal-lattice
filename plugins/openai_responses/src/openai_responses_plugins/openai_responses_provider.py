"""OpenAI Responses provider implementation.

Provider scope for subtask 030:
- provider identity/config/tags
- request initialization for /responses
- generic core <-> Responses-native conversion
- non-streaming SDK call path

Extension-owned business logic (tools/reasoning/usage/verbosity shaping and
extraction) is intentionally out of scope here.
"""

from __future__ import annotations

import hashlib
import io
import json
import queue
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from openai import OpenAI

from agent_core.tool_result_payloads import openai_responses_tool_result_output
from agent_core.types import ProviderPlugin, ProviderRequestCancelled
from agent_core.utils import get_logger
from .openai_responses_attachment_assets import (
    build_openai_provider_ref,
    merge_openai_provider_ref,
    openai_provider_ref,
    openai_provider_ref_is_usable,
)
from .openai_responses_attachment_parts import (
    decode_base64_bytes,
    decode_data_url,
    default_filename_for_mime,
    image_content_to_input_image,
    pdf_content_to_input_file,
)
from .openai_responses_attachment_policy import (
    ATTACHMENT_SOURCES_METADATA_KEY as _ATTACHMENT_SOURCES_METADATA_KEY,
    ATTACHMENT_UPLOAD_MODE_UPLOAD as _ATTACHMENT_UPLOAD_MODE_UPLOAD,
    IMAGE_ATTACHMENT_MODE_UPLOAD as _IMAGE_ATTACHMENT_MODE_UPLOAD,
    UPLOADED_ATTACHMENTS_METADATA_KEY as _UPLOADED_ATTACHMENTS_METADATA_KEY,
    attachment_source_map,
    normalized_multipart_part,
    resolve_attachment_upload_mode,
    resolve_image_attachment_mode,
    uploaded_attachment_map,
)
from .openai_responses_attachment_assets import session_asset_ref_from_content
from .chatgpt_credentials import (
    ChatGPTRefreshPermanentError,
    ChatGPTRefreshTransientError,
    credentials_are_valid as _chatgpt_credentials_are_valid_shared,
    credentials_have_access_token,
    load_credentials as _load_chatgpt_credentials_shared,
    refresh_chatgpt_credentials,
    resolve_credentials_path as _resolve_chatgpt_credentials_path_shared,
)
from .chatgpt_rate_limits import (
    parse_all_rate_limit_headers,
    persist_rate_limit_snapshots,
    resolve_rate_limits_path as _resolve_chatgpt_rate_limits_path_shared,
)
from .openai_responses_runtime import (
    DEFAULT_API_BASE_URL as _DEFAULT_BASE_URL,
    DEFAULT_CHATGPT_BASE_URL as _DEFAULT_CHATGPT_BASE_URL,
    DEFAULT_TIMEOUT as _DEFAULT_TIMEOUT,
    authorization_header_value as _authorization_header_value_shared,
    build_openai_sdk_client as _build_openai_sdk_client_shared,
    chatgpt_default_headers as _chatgpt_default_headers_shared,
    effective_auth_mode as _effective_auth_mode_shared,
    normalize_auth_mode as _normalize_auth_mode_shared,
    prepare_input_and_instructions_for_endpoint as _prepare_input_and_instructions_shared,
    resolve_api_key as _resolve_api_key_shared,
    resolve_base_url as _resolve_base_url_shared,
    should_strip_leading_system_or_developer_message as _should_strip_leading_shared,
    strip_leading_system_or_developer_message as _strip_leading_shared,
)
from .openai_responses_codex_models import (
    fetch_codex_models as _fetch_codex_models_shared,
)
from .openai_responses_codex_models import (
    load_manual_chatgpt_model_descriptors as _load_manual_chatgpt_model_descriptors_shared,
    load_snapshot_model_descriptors as _load_snapshot_model_descriptors_shared,
    merge_model_descriptors as _merge_model_descriptors_shared,
)

log = get_logger("openai_responses_provider")

JsonObject = Dict[str, Any]
_DEFAULT_CHATGPT_CLIENT_VERSION = "0.1.0"
_RAW_USAGE_METADATA_KEY = "_openai_responses_usage_raw"
_RAW_SERVICE_TIER_METADATA_KEY = "_openai_responses_service_tier"
_IMAGE_ATTACHMENT_TYPES = ["png", "jpg", "jpeg", "webp", "gif"]
_PDF_ATTACHMENT_TYPES = ["pdf"]
_COMPACTION_ITEM_TYPES = {"compaction", "compaction_summary"}


@dataclass
class _InflightRequest:
    cancelled: threading.Event = field(default_factory=threading.Event)
    done: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)
    closers: List[Callable[[], None]] = field(default_factory=list)

    def add_closer(self, closer: Callable[[], None]) -> None:
        with self.lock:
            self.closers.append(closer)
            already_cancelled = self.cancelled.is_set()
        if already_cancelled:
            try:
                closer()
            except Exception:
                pass

    def cancel(self) -> None:
        self.cancelled.set()
        with self.lock:
            closers = list(self.closers)
        for closer in closers:
            try:
                closer()
            except Exception:
                continue


class OpenAIResponsesProvider(ProviderPlugin):
    name: str = "openai_responses"
    version: str = "0.1.0"

    def __init__(self) -> None:
        self._inflight_lock = threading.Lock()
        self._inflight_requests: Dict[str, _InflightRequest] = {}

    def _register_inflight(self, request_id: str | None) -> _InflightRequest:
        runtime = _InflightRequest()
        if isinstance(request_id, str) and request_id:
            with self._inflight_lock:
                self._inflight_requests[request_id] = runtime
        return runtime

    def _clear_inflight(
        self, request_id: str | None, runtime: _InflightRequest
    ) -> None:
        runtime.done.set()
        if isinstance(request_id, str) and request_id:
            with self._inflight_lock:
                current = self._inflight_requests.get(request_id)
                if current is runtime:
                    self._inflight_requests.pop(request_id, None)

    def cancel_request(self, request_id: str) -> bool:
        if not isinstance(request_id, str) or not request_id:
            return False
        with self._inflight_lock:
            runtime = self._inflight_requests.get(request_id)
        if runtime is None:
            return False
        runtime.cancel()
        return True

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "model": {"type": "string", "required": True},
            "auth_mode": {
                "type": "string",
                "required": False,
                "default": "api",
                "description": "Authentication mode: api, chatgpt, or auto.",
            },
            "api_key": {
                "type": "string",
                "required": False,
                "description": "OpenAI API key (defaults to OPENAI_API_KEY env var).",
            },
            "base_url": {
                "type": "string",
                "required": False,
                "default": _DEFAULT_BASE_URL,
            },
            "api_base_url": {
                "type": "string",
                "required": False,
                "default": _DEFAULT_BASE_URL,
            },
            "chatgpt_base_url": {
                "type": "string",
                "required": False,
                "default": _DEFAULT_CHATGPT_BASE_URL,
            },
            "chatgpt_account_id": {
                "type": "string",
                "required": False,
                "description": "ChatGPT account id used for ChatGPT-backed requests.",
            },
            "chatgpt_credentials_path": {
                "type": "string",
                "required": False,
                "description": "Path to saved ChatGPT credentials for chatgpt/auto auth mode.",
            },
            "chatgpt_rate_limits_path": {
                "type": "string",
                "required": False,
                "description": "Path to the persisted ChatGPT/Codex rate-limit snapshot sidecar.",
            },
            "chatgpt_client_version": {
                "type": "string",
                "required": False,
                "default": _DEFAULT_CHATGPT_CLIENT_VERSION,
                "description": "Client version query parameter used for ChatGPT-backed /models discovery.",
            },
            "strip_leading_system_or_developer_message": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": (
                    "When true, drop the first provider-native message if it is "
                    "a system or developer message before sending the request. "
                    "Useful when top-level instructions replace older persisted "
                    "system/developer messages."
                ),
            },
            "timeout": {
                "type": "number",
                "required": False,
                "default": _DEFAULT_TIMEOUT,
            },
            "enable_terminal_error_retries": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": (
                    "Enable automatic retries when a terminal error event is received "
                    "in the streaming response. Only retries when no visible output has "
                    "been emitted yet."
                ),
            },
            "terminal_error_max_retries": {
                "type": "integer",
                "required": False,
                "default": 2,
                "description": "Maximum retry attempts for terminal stream error events.",
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        model_options: List[Dict[str, str]] = []
        for model in models or []:
            if not isinstance(model, dict):
                continue
            model_id = model.get("id")
            if model_id is None:
                continue
            model_name = model.get("name")
            model_options.append(
                {
                    "label": (
                        str(model_name) if model_name is not None else str(model_id)
                    ),
                    "value": str(model_id),
                }
            )

        use_dropdown = len(model_options) > 0
        return [
            {
                "ui_type": "config",
                "type": "dropdown" if use_dropdown else "text",
                "key": "model",
                "label": "OpenAI Model",
                **({"options": model_options} if use_dropdown else {}),
            },
            {
                "ui_type": "config",
                "type": "select",
                "key": "auth_mode",
                "label": "OpenAI auth mode",
                "options": [
                    {"value": "api", "label": "API"},
                    {"value": "chatgpt", "label": "ChatGPT"},
                    {"value": "auto", "label": "Auto"},
                ],
                "default": "api",
            },
            {
                "ui_type": "config",
                "type": "checkbox",
                "key": "enable_terminal_error_retries",
                "label": "Retry on terminal stream errors",
            },
            {
                "ui_type": "config",
                "type": "number",
                "key": "terminal_error_max_retries",
                "label": "Terminal error max retries",
            },
            {
                "ui_type": "model_picker",
                "key": "model",
                "attachment_type": "dropdown",
                "display_placement": "left",
                "options": model_options,
                "label": "model",
            },
            {
                "ui_type": "composer_attachment",
                "key": "openai_responses:attachment:image",
                "attachment_type": "image",
                "attachment_action_plugin": "openai_responses_attachments",
                "supports_url": True,
                "supported_file_types": _IMAGE_ATTACHMENT_TYPES,
                "display_placement": "below",
                "label": "Image",
                "icon": "image",
            },
        ]

    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            raw_result = self._fetch_models_raw(config)
            return self._normalize_model_descriptors(raw_result)
        except Exception as exc:
            get_logger("openai_responses_provider").warning(
                "Failed to fetch models from OpenAI",
                error=str(exc),
                base_url=(config.get("base_url") or _DEFAULT_BASE_URL),
            )
            return []

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        tags = [
            "provider:openai_responses",
            "openai_responses",
            "supports_streaming",
            "supports_reasoning",
            "supports_reasoning_effort",
            "supports_tools",
        ]

        model = config.get("model")
        if isinstance(model, str) and "gpt-5" in model:
            tags.append("supports_verbosity")

        return tags

    def _coerce_timeout(self, raw: Any) -> float:
        try:
            timeout = float(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "[openai_responses_provider] timeout must be numeric"
            ) from exc
        if timeout <= 0:
            raise ValueError("[openai_responses_provider] timeout must be > 0")
        return timeout

    def _coerce_max_retries(self, raw: Any) -> int:
        try:
            max_retries = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "[openai_responses_provider] max_retries must be an integer"
            ) from exc
        if max_retries < 0:
            raise ValueError("[openai_responses_provider] max_retries must be >= 0")
        return max_retries

    def _config_terminal_error_retries_enabled(self, config: Dict[str, Any]) -> bool:
        raw = config.get("enable_terminal_error_retries")
        return raw is True

    def _config_terminal_error_max_retries(self, config: Dict[str, Any]) -> int:
        raw = config.get("terminal_error_max_retries")
        try:
            retries = int(raw)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 2
        return retries if retries > 0 else 0

    def _resolve_api_key(self, config: Dict[str, Any]) -> str:
        return _resolve_api_key_shared(config)

    def _normalize_auth_mode(self, raw: Any) -> str:
        return _normalize_auth_mode_shared(raw)

    def _effective_auth_mode(self, config: Dict[str, Any]) -> str:
        return _effective_auth_mode_shared(config)

    def _resolve_model(self, config: Dict[str, Any]) -> str:
        model = config.get("model")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("[openai_responses_provider] model is required")
        return model.strip()

    def _resolve_base_url(self, config: Dict[str, Any]) -> str:
        return _resolve_base_url_shared(config)

    def _create_sdk_client(self, config: Dict[str, Any]) -> OpenAI:
        timeout = self._coerce_timeout(config.get("timeout", _DEFAULT_TIMEOUT))
        return self._create_sdk_client_with_options(
            config, timeout=timeout, max_retries=None
        )

    def _chatgpt_default_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        return _chatgpt_default_headers_shared(config)

    def _create_sdk_client_with_options(
        self,
        config: Dict[str, Any],
        *,
        timeout: float,
        max_retries: Optional[int],
    ) -> OpenAI:
        return _build_openai_sdk_client_shared(
            config,
            timeout=timeout,
            max_retries=max_retries,
        )

    def _authorization_header_value(self, config: Dict[str, Any], token: str) -> str:
        return _authorization_header_value_shared(config, token)

    def _request_max_retries(self, request: Dict[str, Any]) -> Optional[int]:
        if "max_retries" not in request:
            return None
        return self._coerce_max_retries(request.get("max_retries"))

    def _request_instructions(self, request: Dict[str, Any]) -> Optional[str]:
        raw = request.get("instructions")
        if not isinstance(raw, str):
            return None
        text = raw.strip()
        return text or None

    def _should_strip_leading_system_or_developer_message(
        self,
        config: Dict[str, Any],
    ) -> bool:
        return _should_strip_leading_shared(config)

    def _strip_leading_system_or_developer_message(
        self,
        native_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return _strip_leading_shared(native_messages)

    def _request_client(
        self, client: Any, *, timeout: float, max_retries: Optional[int]
    ) -> Any:
        if max_retries is None:
            return client

        with_options = getattr(client, "with_options", None)
        if callable(with_options):
            return with_options(timeout=timeout, max_retries=max_retries)
        return client

    def _request_stream_recovery_mode(self, request: Dict[str, Any]) -> str:
        mode = request.get("stream_recovery_mode")
        if not isinstance(mode, str):
            return "disabled"
        normalized = mode.strip().lower()
        if normalized not in {"disabled", "early_only", "aggressive"}:
            return "disabled"
        return normalized

    def _request_stream_recovery_retries(self, request: Dict[str, Any]) -> int:
        raw = request.get("stream_recovery_retries")
        try:
            retries = int(raw)
        except (TypeError, ValueError):
            return 0
        return retries if retries > 0 else 0

    def _stream_event_has_visible_output(self, event: Dict[str, Any]) -> bool:
        event_type = event.get("type")
        if event_type == "response.output_text.delta":
            return isinstance(event.get("delta"), str) and bool(event.get("delta"))
        if event_type in (
            "response.reasoning_summary_text.delta",
            "response.reasoning_summary.delta",
            "response.reasoning.delta",
        ):
            delta = event.get("delta")
            if isinstance(delta, str):
                return bool(delta)
            if isinstance(delta, dict):
                return isinstance(delta.get("text"), str) and bool(delta.get("text"))
        return False

    def _create_sdk_client_for_discovery(self, config: Dict[str, Any]) -> OpenAI:
        if not isinstance(config, dict):
            raise TypeError("[openai_responses_provider] config must be a dict")
        return self._create_sdk_client(config)

    def _fetch_models_raw(self, config: Dict[str, Any]) -> Any:
        mode = self._discovery_auth_mode(config)
        if mode == "chatgpt":
            return self._fetch_chatgpt_discovery_models(config)
        client = self._create_sdk_client_for_discovery(config)
        return client.models.list()

    def _discovery_auth_mode(self, config: Dict[str, Any]) -> str:
        requested = self._normalize_auth_mode(config.get("auth_mode"))
        if requested == "chatgpt":
            self._chatgpt_discovery_credentials(config)
            return "chatgpt"
        if requested == "auto":
            credentials = self._chatgpt_discovery_credentials(config, require=False)
            if credentials is not None:
                return "chatgpt"
        return "api"

    def _chatgpt_discovery_credentials(
        self,
        config: Dict[str, Any],
        *,
        require: bool = True,
    ) -> Optional[Dict[str, Any]]:
        access_token = config.get("chatgpt_access_token")
        if isinstance(access_token, str) and access_token.strip():
            token_type = config.get("chatgpt_token_type")
            account_id = config.get("chatgpt_account_id")
            return {
                "access_token": access_token.strip(),
                "token_type": token_type if isinstance(token_type, str) else "Bearer",
                "account_id": account_id if isinstance(account_id, str) else None,
            }

        path = self._chatgpt_credentials_path(config)
        payload = self._load_json_file(path)
        if isinstance(payload, dict) and self._chatgpt_credentials_are_valid(payload):
            return payload
        if require:
            raise ValueError(
                "[openai_responses_provider] chatgpt auth_mode requires a valid saved ChatGPT login"
            )
        return None

    def _chatgpt_credentials_path(self, config: Dict[str, Any]) -> Path:
        return _resolve_chatgpt_credentials_path_shared(config)

    def _chatgpt_rate_limits_path(self, config: Dict[str, Any]) -> Path:
        return _resolve_chatgpt_rate_limits_path_shared(config)

    def _load_json_file(self, path: Path) -> Dict[str, Any]:
        return _load_chatgpt_credentials_shared(path)

    def _chatgpt_credentials_are_valid(self, credentials: Dict[str, Any]) -> bool:
        return _chatgpt_credentials_are_valid_shared(credentials)

    def _chatgpt_credentials_can_attempt_request(
        self, credentials: Dict[str, Any]
    ) -> bool:
        return credentials_have_access_token(credentials)

    def _capture_chatgpt_rate_limits(
        self,
        config: Dict[str, Any],
        headers: Any,
    ) -> None:
        if self._effective_auth_mode(config) != "chatgpt" or headers is None:
            return
        try:
            header_map = {
                str(key).lower(): value for key, value in dict(headers).items()
            }
        except Exception:
            return
        snapshots = parse_all_rate_limit_headers(header_map)
        if not snapshots:
            return
        persist_rate_limit_snapshots(
            self._chatgpt_rate_limits_path(config),
            snapshots,
            plan_type=config.get("chatgpt_plan_type"),
        )

    def _capture_chatgpt_rate_limits_from_stream(
        self,
        config: Dict[str, Any],
        stream: Any,
    ) -> None:
        response = getattr(stream, "_response", None)
        headers = getattr(response, "headers", None)
        self._capture_chatgpt_rate_limits(config, headers)

    def _chatgpt_config_with_credentials(
        self,
        config: Dict[str, Any],
        credentials: Dict[str, Any],
    ) -> Dict[str, Any]:
        updated = dict(config)
        updated["chatgpt_access_token"] = credentials.get("access_token")
        updated["chatgpt_token_type"] = credentials.get("token_type") or "Bearer"
        account_id = credentials.get("account_id") or config.get("chatgpt_account_id")
        if isinstance(account_id, str) and account_id.strip():
            updated["chatgpt_account_id"] = account_id.strip()
        else:
            updated.pop("chatgpt_account_id", None)
        updated["chatgpt_credentials_path"] = str(
            self._chatgpt_credentials_path(config)
        )
        updated["_openai_responses_effective_auth_mode"] = "chatgpt"
        updated["base_url"] = self._resolve_base_url(updated)
        return updated

    def _exception_status_code(self, exc: Exception) -> Optional[int]:
        status_code = getattr(exc, "status_code", None)
        if isinstance(status_code, int):
            return status_code
        response = getattr(exc, "response", None)
        response_status = getattr(response, "status_code", None)
        if isinstance(response_status, int):
            return response_status
        if isinstance(exc, HTTPError):
            return exc.code
        message = str(exc)
        if "Error code: 401" in message or "status 401" in message:
            return 401
        return None

    def _is_unauthorized_error(self, exc: Exception) -> bool:
        return self._exception_status_code(exc) == 401

    def _reload_chatgpt_credentials_if_changed(
        self,
        config: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        path = self._chatgpt_credentials_path(config)
        credentials = self._load_json_file(path)
        if not self._chatgpt_credentials_can_attempt_request(credentials):
            return None
        current_token = config.get("chatgpt_access_token")
        next_token = credentials.get("access_token")
        if not isinstance(next_token, str) or not next_token.strip():
            return None
        if (
            isinstance(current_token, str)
            and current_token.strip() == next_token.strip()
        ):
            return None
        return self._chatgpt_config_with_credentials(config, credentials)

    def _refresh_chatgpt_config(
        self,
        config: Dict[str, Any],
        *,
        timeout: float,
    ) -> Dict[str, Any]:
        path = self._chatgpt_credentials_path(config)
        credentials = refresh_chatgpt_credentials(path, timeout=timeout)
        return self._chatgpt_config_with_credentials(config, credentials)

    def _rebuild_request_client(
        self,
        config: Dict[str, Any],
        *,
        timeout: float,
        max_retries: Optional[int],
    ) -> Any:
        client = self._create_sdk_client_with_options(
            config,
            timeout=timeout,
            max_retries=max_retries,
        )
        return self._request_client(client, timeout=timeout, max_retries=max_retries)

    def _chatgpt_client_version(self, config: Dict[str, Any]) -> str:
        raw = config.get("chatgpt_client_version") or _DEFAULT_CHATGPT_CLIENT_VERSION
        if not isinstance(raw, str) or not raw.strip():
            return _DEFAULT_CHATGPT_CLIENT_VERSION
        return raw.strip()

    def _chatgpt_models_base_url(self, config: Dict[str, Any]) -> str:
        raw = config.get("chatgpt_base_url") or _DEFAULT_CHATGPT_BASE_URL
        if not isinstance(raw, str) or not raw.strip():
            return _DEFAULT_CHATGPT_BASE_URL
        return raw.rstrip("/")

    def _chatgpt_manual_models(self) -> List[Dict[str, Any]]:
        return _load_manual_chatgpt_model_descriptors_shared()

    def _chatgpt_snapshot_models(self) -> List[Dict[str, Any]]:
        try:
            return _load_snapshot_model_descriptors_shared()
        except Exception:
            return []

    def _merge_model_descriptors(
        self,
        *descriptor_lists: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return _merge_model_descriptors_shared(*descriptor_lists)

    def _fetch_codex_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        timeout = self._coerce_timeout(config.get("timeout", _DEFAULT_TIMEOUT))
        return _fetch_codex_models_shared(timeout=timeout)

    def _fetch_chatgpt_models(self, config: Dict[str, Any]) -> Dict[str, Any]:
        credentials = self._chatgpt_discovery_credentials(config)
        token = credentials.get("access_token")
        if not isinstance(token, str) or not token.strip():
            raise ValueError(
                "[openai_responses_provider] chatgpt auth_mode requires a valid saved ChatGPT login"
            )
        headers = {
            "Authorization": self._authorization_header_value(config, token.strip()),
            "Accept": "application/json",
        }
        account_id = credentials.get("account_id")
        if isinstance(account_id, str) and account_id.strip():
            headers["ChatGPT-Account-Id"] = account_id.strip()
        url = "{}?{}".format(
            f"{self._chatgpt_models_base_url(config)}/models",
            urlencode({"client_version": self._chatgpt_client_version(config)}),
        )
        request = Request(url, headers=headers, method="GET")
        timeout = self._coerce_timeout(config.get("timeout", _DEFAULT_TIMEOUT))
        try:
            with urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"chatgpt models discovery failed with status {exc.code}: {body}"
            ) from exc
        except URLError as exc:
            raise RuntimeError(f"chatgpt models discovery failed: {exc}") from exc
        try:
            payload = json.loads(body)
        except Exception as exc:
            raise RuntimeError(
                "chatgpt models discovery returned invalid JSON"
            ) from exc
        if not isinstance(payload, dict):
            raise RuntimeError(
                "chatgpt models discovery returned an unexpected payload"
            )
        return payload

    def _fetch_chatgpt_discovery_models(
        self, config: Dict[str, Any]
    ) -> List[Dict[str, Any]] | Dict[str, Any]:
        # Validate credentials up front so ChatGPT mode still requires a valid login.
        self._chatgpt_discovery_credentials(config)

        manual_models = self._chatgpt_manual_models()
        snapshot_models = self._chatgpt_snapshot_models()
        codex_error: Exception | None = None
        try:
            codex_models = self._fetch_codex_models(config)
            return self._merge_model_descriptors(
                manual_models, snapshot_models, codex_models
            )
        except Exception as exc:
            codex_error = exc

        if snapshot_models:
            if codex_error is not None:
                log.warning(
                    "Falling back to checked-in Codex models snapshot after live fetch failed",
                    error=str(codex_error),
                )
            return self._merge_model_descriptors(manual_models, snapshot_models)

        fallback_models = self._normalize_model_descriptors(
            self._fetch_chatgpt_models(config)
        )
        merged = self._merge_model_descriptors(manual_models, fallback_models)
        if codex_error is not None:
            log.warning(
                "Falling back to ChatGPT /models discovery after Codex catalog fetch failed",
                error=str(codex_error),
            )
        return merged

    def _normalize_model_descriptors(self, raw_result: Any) -> List[Dict[str, Any]]:
        data = getattr(raw_result, "data", raw_result)
        if isinstance(data, dict) and isinstance(data.get("models"), list):
            data = data.get("models")
        if not isinstance(data, list):
            raise ValueError(
                "[openai_responses_provider] models list response missing data list"
            )

        normalized: List[Dict[str, Any]] = []
        for item in data:
            model_id = None
            model_name = None

            if isinstance(item, dict):
                model_id = item.get("id") or item.get("slug")
                model_name = item.get("name") or item.get("display_name")
            else:
                model_id = getattr(item, "id", None)
                model_name = getattr(item, "name", None)

            if not isinstance(model_id, str) or not model_id.strip():
                continue

            descriptor: Dict[str, Any] = {"id": model_id.strip()}
            if isinstance(model_name, str) and model_name.strip():
                descriptor["name"] = model_name.strip()
            normalized.append(descriptor)

        return normalized

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(config, dict):
            raise TypeError("[openai_responses_provider] config must be a dict")

        model = self._resolve_model(config)
        base_url = self._resolve_base_url(config)
        timeout = self._coerce_timeout(config.get("timeout", _DEFAULT_TIMEOUT))
        auth_mode = self._normalize_auth_mode(config.get("auth_mode"))

        normalized_config = {
            **config,
            "model": model,
            "base_url": base_url,
            "auth_mode": auth_mode,
            "timeout": timeout,
        }
        if auth_mode == "api":
            normalized_config["api_key"] = self._resolve_api_key(config)
        client: Any = None
        try:
            client = self._create_sdk_client(normalized_config)
        except ValueError:
            if auth_mode == "api":
                raise
        return {"config": normalized_config, "client": client}

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        _ = request_id
        cfg = state.get("config") or {}

        model = self._resolve_model(cfg)
        api_key = self._resolve_api_key(cfg)
        base_url = self._resolve_base_url(cfg)
        timeout = self._coerce_timeout(cfg.get("timeout", _DEFAULT_TIMEOUT))

        payload: Dict[str, Any] = {"model": model}
        if self._effective_auth_mode(cfg) == "chatgpt":
            payload["store"] = False

        request = {
            "url": f"{base_url}/responses",
            "payload": payload,
            "headers": {
                "Content-Type": "application/json",
                "Authorization": self._authorization_header_value(cfg, api_key),
            },
            "timeout": timeout,
        }
        request["headers"].update(self._chatgpt_default_headers(cfg))

        return list(native_messages), {**state, "request": request}

    def _native_internal_from_core_metadata(self, metadata: Any) -> Dict[str, Any]:
        if not isinstance(metadata, dict):
            return {}
        out = dict(metadata)
        out.pop("native_indices", None)
        return out

    def _core_metadata_from_native_internal(self, internal: Any) -> Dict[str, Any]:
        if not isinstance(internal, dict):
            return {}
        out = {
            key: value
            for key, value in internal.items()
            if key != "native_indices" and not str(key).startswith("_openai_responses_")
        }
        return out

    def _extract_text_and_images_from_content(
        self,
        content: Any,
        raw_internal_metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        text_parts: List[str] = []
        multipart_parts: List[Dict[str, Any]] = []
        source_map = self._attachment_source_map(raw_internal_metadata)

        if not isinstance(content, list):
            return "", multipart_parts

        for index, part in enumerate(content):
            if not isinstance(part, dict):
                continue

            ptype = part.get("type")
            if ptype in ("input_text", "output_text", "text"):
                text = part.get("text")
                if isinstance(text, str) and text:
                    text_parts.append(text)
                continue

            source_override = source_map.get(index)
            if isinstance(source_override, dict):
                multipart_parts.append(source_override)
                continue

            if ptype in ("input_image", "image_url"):
                image_url = part.get("image_url")
                if isinstance(image_url, dict):
                    image_url = image_url.get("url")
                if isinstance(image_url, str) and image_url:
                    multipart_parts.append(
                        {"type": "image", "content": {"url": image_url}, "metadata": {}}
                    )
                    continue

                file_id = part.get("file_id")
                if isinstance(file_id, str) and file_id:
                    multipart_parts.append(
                        {
                            "type": "image",
                            "content": {"file_id": file_id},
                            "metadata": {},
                        }
                    )
                continue

            if ptype == "input_file":
                file_url = part.get("file_url")
                file_id = part.get("file_id")
                file_data = part.get("file_data")
                filename = part.get("filename")
                payload: Dict[str, Any] = {}
                if isinstance(file_url, str) and file_url:
                    payload["url"] = file_url
                if isinstance(file_id, str) and file_id:
                    payload["file_id"] = file_id
                if isinstance(file_data, str) and file_data:
                    payload["data_base64"] = file_data
                if isinstance(filename, str) and filename:
                    payload["filename"] = filename
                if payload:
                    multipart_parts.append(
                        {"type": "pdf", "content": payload, "metadata": {}}
                    )

        return "\n".join(text_parts).strip(), multipart_parts

    def _attachment_upload_mode(self, state: Dict[str, Any]) -> str:
        return resolve_attachment_upload_mode(state)

    def _image_attachment_mode(self, state: Dict[str, Any]) -> str:
        return resolve_image_attachment_mode(state)

    def _normalized_multipart_part(
        self, part: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        return normalized_multipart_part(part)

    def _attachment_source_map(
        self, raw_internal_metadata: Optional[Dict[str, Any]]
    ) -> Dict[int, Dict[str, Any]]:
        return attachment_source_map(raw_internal_metadata)

    def _uploaded_attachment_map(
        self,
        raw_internal_metadata: Optional[Dict[str, Any]],
    ) -> Dict[int, Dict[str, Any]]:
        return uploaded_attachment_map(raw_internal_metadata)

    def _request_context(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        value = state.get("_request_context")
        return value if isinstance(value, dict) else None

    def _session_asset_store(
        self,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        resolved_context = (
            context if isinstance(context, dict) else self._request_context(state)
        )
        store = (
            resolved_context.get("session_asset_store")
            if isinstance(resolved_context, dict)
            else None
        )
        if store is None:
            config = state.get("config")
            if isinstance(config, dict):
                store = config.get("_session_asset_store")
        if store is None:
            raise RuntimeError(
                "[openai_responses_provider] session asset attachment requires session_asset_store in context"
            )
        return store

    def _session_asset_record_and_bytes(
        self,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        *,
        asset_ref: Dict[str, Any],
        expected_attachment_type: str,
    ) -> Tuple[Any, bytes]:
        store = self._session_asset_store(state, context)
        session_id = asset_ref.get("session_id")
        asset_id = asset_ref.get("asset_id")
        if not isinstance(session_id, str) or not isinstance(asset_id, str):
            raise ValueError(
                "[openai_responses_provider] invalid session asset reference"
            )
        record = store.load(session_id, asset_id)
        if record.attachment_type != expected_attachment_type:
            raise ValueError(
                f"[openai_responses_provider] session asset {asset_id!r} is not a {expected_attachment_type} attachment"
            )
        return record, store.load_bytes(session_id, asset_id)

    def _resolve_session_asset(
        self,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        asset_ref: Dict[str, Any],
        expected_attachment_type: str,
    ) -> Tuple[str, str, bytes]:
        record, payload_bytes = self._session_asset_record_and_bytes(
            state,
            context,
            asset_ref=asset_ref,
            expected_attachment_type=expected_attachment_type,
        )
        return record.filename, record.mime_type, payload_bytes

    def _image_part_to_input_image(
        self,
        content: Any,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return image_content_to_input_image(
            content,
            resolve_session_asset=(
                lambda asset_ref, expected_attachment_type: self._resolve_session_asset(
                    state,
                    context,
                    asset_ref,
                    expected_attachment_type,
                )
            ),
        )

    def _pdf_part_to_input_file(
        self,
        content: Any,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return pdf_content_to_input_file(
            content,
            resolve_session_asset=(
                lambda asset_ref, expected_attachment_type: self._resolve_session_asset(
                    state,
                    context,
                    asset_ref,
                    expected_attachment_type,
                )
            ),
        )

    def _attachment_upload_cache_key(
        self,
        *,
        purpose: str,
        filename: str,
        mime_type: str,
        payload_bytes: bytes,
    ) -> str:
        digest = hashlib.sha256(payload_bytes).hexdigest()
        return f"{purpose}:{filename}:{mime_type}:{digest}"

    def _file_object_id(self, upload_response: Any) -> str:
        response_obj = self._safe_dict_payload(upload_response)
        file_id = response_obj.get("id")
        if not isinstance(file_id, str) or not file_id:
            raise RuntimeError(
                "[openai_responses_provider] file upload response missing id"
            )
        return file_id

    def _file_object_reference(
        self,
        upload_response: Any,
        *,
        purpose: str,
        filename: str,
        mime_type: str,
    ) -> Dict[str, Any]:
        response_obj = self._safe_dict_payload(upload_response)
        file_id = response_obj.get("id")
        if not isinstance(file_id, str) or not file_id:
            raise RuntimeError(
                "[openai_responses_provider] file upload response missing id"
            )
        return build_openai_provider_ref(
            file_id=file_id,
            purpose=purpose,
            filename=filename,
            mime_type=mime_type,
            expires_at=response_obj.get("expires_at"),
        )

    def _upload_attachment_bytes(
        self,
        *,
        client: Any,
        filename: str,
        mime_type: str,
        payload_bytes: bytes,
        purpose: str,
        timeout: float,
        upload_cache: Dict[str, str],
    ) -> Dict[str, Any]:
        cache_key = self._attachment_upload_cache_key(
            purpose=purpose,
            filename=filename,
            mime_type=mime_type,
            payload_bytes=payload_bytes,
        )
        cached_id = upload_cache.get(cache_key)
        if isinstance(cached_id, str) and cached_id:
            return build_openai_provider_ref(
                file_id=cached_id,
                purpose=purpose,
                filename=filename,
                mime_type=mime_type,
            )

        upload_handle = io.BytesIO(payload_bytes)
        upload_handle.name = filename
        try:
            upload_response = client.files.create(  # type: ignore[union-attr]
                file=(filename, upload_handle.read(), mime_type),
                purpose=purpose,
                timeout=timeout,
            )
        except Exception as exc:
            raise RuntimeError(f"OpenAI file upload failed: {exc}") from exc

        upload_ref = self._file_object_reference(
            upload_response,
            purpose=purpose,
            filename=filename,
            mime_type=mime_type,
        )
        file_id = upload_ref["file_id"]
        upload_cache[cache_key] = file_id
        return upload_ref

    def _upload_state_cache(self, state: Dict[str, Any]) -> Dict[str, str]:
        raw_cache = state.get("_openai_responses_upload_cache")
        return raw_cache if isinstance(raw_cache, dict) else {}

    def _uploaded_content_part(
        self,
        part: Dict[str, Any],
        *,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        source_override: Optional[Dict[str, Any]],
        uploaded_override: Optional[Dict[str, Any]],
        client: Any,
        timeout: float,
        upload_cache: Dict[str, str],
        force_reupload: bool = False,
    ) -> Dict[str, Any]:
        part_type = part.get("type")
        source_content = (
            source_override.get("content") if isinstance(source_override, dict) else {}
        )
        asset_ref = session_asset_ref_from_content(source_content)
        detail = (
            part.get("detail")
            if isinstance(part.get("detail"), str) and part.get("detail")
            else None
        )

        if (
            part_type == "input_image"
            and self._image_attachment_mode(state) != _IMAGE_ATTACHMENT_MODE_UPLOAD
        ):
            return dict(part)

        if asset_ref is not None:
            expected_attachment_type = "image" if part_type == "input_image" else "pdf"
            purpose = "vision" if part_type == "input_image" else "user_data"
            record, payload_bytes = self._session_asset_record_and_bytes(
                state,
                context,
                asset_ref=asset_ref,
                expected_attachment_type=expected_attachment_type,
            )
            provider_ref = openai_provider_ref(record.provider_refs)
            if not force_reupload and openai_provider_ref_is_usable(provider_ref):
                uploaded = {"type": part_type, "file_id": provider_ref["file_id"]}
                if detail is not None:
                    uploaded["detail"] = detail
                return uploaded

            upload_ref = self._upload_attachment_bytes(
                client=client,
                filename=record.filename,
                mime_type=record.mime_type,
                payload_bytes=payload_bytes,
                purpose=purpose,
                timeout=timeout,
                upload_cache=upload_cache,
            )
            self._session_asset_store(state, context).update_manifest(
                record.session_id,
                record.asset_id,
                provider_refs=merge_openai_provider_ref(
                    record.provider_refs, upload_ref
                ),
                metadata=record.metadata,
            )
            uploaded = {"type": part_type, "file_id": upload_ref["file_id"]}
            if detail is not None:
                uploaded["detail"] = detail
            return uploaded

        if (
            not force_reupload
            and isinstance(uploaded_override, dict)
            and uploaded_override
        ):
            return dict(uploaded_override)

        if part_type == "input_image":
            if isinstance(part.get("file_id"), str) and part.get("file_id"):
                return dict(part)

            image_url = part.get("image_url")
            if not isinstance(image_url, str) or not image_url.startswith("data:"):
                return dict(part)

            mime_type, data_base64 = decode_data_url(image_url)
            payload_bytes = decode_base64_bytes(
                data_base64, field_name="input_image.image_url"
            )
            filename = (
                source_content.get("filename")
                if isinstance(source_content, dict)
                else None
            )
            if not isinstance(filename, str) or not filename:
                filename = default_filename_for_mime(mime_type, "attachment-image")

            upload_ref = self._upload_attachment_bytes(
                client=client,
                filename=filename,
                mime_type=mime_type,
                payload_bytes=payload_bytes,
                purpose="vision",
                timeout=timeout,
                upload_cache=upload_cache,
            )
            uploaded = {
                "type": "input_image",
                "file_id": upload_ref["file_id"],
            }
            if detail is not None:
                uploaded["detail"] = detail
            return uploaded

        if part_type == "input_file":
            if isinstance(part.get("file_id"), str) and part.get("file_id"):
                return dict(part)

            filename = part.get("filename")
            if not isinstance(filename, str) or not filename:
                raise ValueError(
                    "[openai_responses_provider] input_file attachment requires filename for upload"
                )

            payload_bytes: Optional[bytes] = None
            mime_type = "application/pdf"
            file_data = part.get("file_data")
            file_url = part.get("file_url")
            if isinstance(file_data, str) and file_data:
                payload_bytes = decode_base64_bytes(
                    file_data, field_name="input_file.file_data"
                )
            elif isinstance(file_url, str) and file_url.startswith("data:"):
                mime_type, data_base64 = decode_data_url(file_url)
                payload_bytes = decode_base64_bytes(
                    data_base64, field_name="input_file.file_url"
                )
            elif isinstance(file_url, str) and file_url:
                return dict(part)
            else:
                raise ValueError(
                    "[openai_responses_provider] input_file attachment requires file_data or data URL for upload"
                )

            upload_ref = self._upload_attachment_bytes(
                client=client,
                filename=filename,
                mime_type=mime_type,
                payload_bytes=payload_bytes,
                purpose="user_data",
                timeout=timeout,
                upload_cache=upload_cache,
            )
            uploaded = {
                "type": "input_file",
                "file_id": upload_ref["file_id"],
            }
            if detail is not None:
                uploaded["detail"] = detail
            return uploaded

        return dict(part)

    def _prepare_uploaded_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        *,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        client: Any,
        timeout: float,
        upload_cache: Dict[str, str],
        persist_uploaded_refs: bool = False,
        force_reupload: bool = False,
    ) -> List[Dict[str, Any]]:
        rewritten: List[Dict[str, Any]] = []
        for item in native_messages:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                rewritten.append(dict(item))
                continue

            raw_metadata = (
                item.get("_metadata") if isinstance(item.get("_metadata"), dict) else {}
            )
            source_map = self._attachment_source_map(raw_metadata)
            uploaded_map = self._uploaded_attachment_map(raw_metadata)
            next_content: List[Dict[str, Any]] = []
            changed = False
            uploaded_entries: List[Dict[str, Any]] = []
            for index, part in enumerate(content):
                if not isinstance(part, dict):
                    continue
                next_part = self._uploaded_content_part(
                    part,
                    state=state,
                    context=context,
                    source_override=source_map.get(index),
                    uploaded_override=uploaded_map.get(index),
                    client=client,
                    timeout=timeout,
                    upload_cache=upload_cache,
                    force_reupload=force_reupload,
                )
                changed = changed or next_part != part
                next_content.append(next_part)
                if next_part != part or index in uploaded_map:
                    uploaded_entries.append(
                        {
                            "content_index": index,
                            "uploaded_part": dict(next_part),
                        }
                    )

            if persist_uploaded_refs:
                if uploaded_entries:
                    merged_metadata = {
                        **raw_metadata,
                        _UPLOADED_ATTACHMENTS_METADATA_KEY: uploaded_entries,
                    }
                    item["_metadata"] = merged_metadata
                rewritten.append(item)
                continue

            if changed:
                rewritten.append({**item, "content": next_content})
            else:
                rewritten.append(dict(item))
        return rewritten

    def _is_attachment_reference_error(self, exc: Exception) -> bool:
        message = str(exc).lower()
        patterns = (
            "no such file",
            "file not found",
            "file has expired",
            "expired file",
            "invalid file",
        )
        return any(pattern in message for pattern in patterns)

    def _extract_url_citations(
        self,
        output_items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        citations: List[Dict[str, Any]] = []

        for item in output_items:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue

            content = item.get("content")
            if not isinstance(content, list):
                continue

            for part in content:
                if not isinstance(part, dict) or part.get("type") != "output_text":
                    continue
                annotations = part.get("annotations")
                if not isinstance(annotations, list):
                    continue

                for annotation in annotations:
                    if (
                        not isinstance(annotation, dict)
                        or annotation.get("type") != "url_citation"
                    ):
                        continue

                    payload = (
                        annotation.get("url_citation")
                        if isinstance(annotation.get("url_citation"), dict)
                        else annotation
                    )
                    if not isinstance(payload, dict):
                        continue

                    entry: Dict[str, Any] = {}
                    for key in ("url", "title", "content"):
                        value = payload.get(key)
                        if isinstance(value, str) and value:
                            entry[key] = value

                    for key in ("start_index", "end_index"):
                        value = payload.get(key)
                        if isinstance(value, int):
                            entry[key] = value

                    if not entry:
                        continue

                    already_seen = any(
                        entry.get("url") == existing.get("url")
                        and entry.get("start_index") == existing.get("start_index")
                        and entry.get("end_index") == existing.get("end_index")
                        for existing in citations
                    )
                    if not already_seen:
                        citations.append(entry)

        return citations

    def _extract_web_search_sources(
        self,
        output_items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        sources: List[Dict[str, Any]] = []

        for item in output_items:
            if not isinstance(item, dict) or item.get("type") != "web_search_call":
                continue

            action = item.get("action")
            if not isinstance(action, dict):
                continue

            action_sources = action.get("sources")
            if not isinstance(action_sources, list):
                continue

            for source in action_sources:
                if not isinstance(source, dict):
                    continue

                entry: Dict[str, Any] = {}
                for key in ("url", "title", "content", "snippet"):
                    value = source.get(key)
                    if isinstance(value, str) and value:
                        entry[key] = value

                if not entry:
                    continue

                already_seen = any(
                    entry.get("url") == existing.get("url")
                    and entry.get("title") == existing.get("title")
                    for existing in sources
                )
                if not already_seen:
                    sources.append(entry)

        return sources

    def _assistant_candidate_from_response_item(
        self,
        item: Dict[str, Any],
        *,
        native_index: int,
        internal_md: Dict[str, Any],
        raw_internal_md: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if item.get("type") != "message":
            return None

        role = item.get("role") if isinstance(item.get("role"), str) else "assistant"
        if role != "assistant":
            return None

        text, images = self._extract_text_and_images_from_content(
            item.get("content"),
            raw_internal_md if isinstance(raw_internal_md, dict) else None,
        )
        metadata = dict(internal_md)
        phase = item.get("phase")
        if isinstance(phase, str) and phase:
            metadata["phase"] = phase

        candidate: Dict[str, Any] = {
            "role": "assistant",
            "content": text,
            "metadata": metadata,
            "_segment_native_index": native_index,
        }
        if images:
            candidate["multipartContent"] = images
        return candidate

    def _build_response_segment_assistant(
        self,
        segment: List[Tuple[int, Dict[str, Any], Dict[str, Any]]],
    ) -> Dict[str, Any]:
        response_id: Optional[str] = None
        segment_indices: List[int] = []
        assistant_candidates: List[Dict[str, Any]] = []
        segment_output_items: List[Dict[str, Any]] = []

        for native_index, item, internal_md in segment:
            raw_internal_md = (
                item.get("_metadata")
                if isinstance(item.get("_metadata"), dict)
                else None
            )
            segment_indices.append(native_index)
            segment_output_items.append(item)
            if response_id is None:
                rid = internal_md.get("response_id")
                if isinstance(rid, str) and rid:
                    response_id = rid

            candidate = self._assistant_candidate_from_response_item(
                item,
                native_index=native_index,
                internal_md=internal_md,
                raw_internal_md=raw_internal_md,
            )
            if candidate is not None:
                assistant_candidates.append(candidate)

        canonical: Optional[Dict[str, Any]] = None
        for candidate in reversed(assistant_candidates):
            content = candidate.get("content")
            if isinstance(content, str) and content.strip():
                canonical = candidate
                break
        if canonical is None and assistant_candidates:
            for candidate in reversed(assistant_candidates):
                phase = (candidate.get("metadata") or {}).get("phase")
                if phase == "final_answer":
                    canonical = candidate
                    break
        if canonical is None and assistant_candidates:
            canonical = assistant_candidates[-1]

        phase_messages: List[Dict[str, Any]] = []
        for candidate in assistant_candidates:
            candidate_md = candidate.get("metadata") or {}
            phase_entry: Dict[str, Any] = {
                "content": (
                    candidate.get("content")
                    if isinstance(candidate.get("content"), str)
                    else ""
                ),
                "native_index": candidate.get("_segment_native_index"),
            }
            phase = candidate_md.get("phase")
            if isinstance(phase, str) and phase:
                phase_entry["phase"] = phase
            multipart = candidate.get("multipartContent")
            if isinstance(multipart, list) and multipart:
                phase_entry["multipartContent"] = multipart
            extra_md = {
                k: v
                for k, v in candidate_md.items()
                if k not in {"phase", "response_id"}
            }
            if extra_md:
                phase_entry["metadata"] = extra_md
            phase_messages.append(phase_entry)

        if canonical is None:
            metadata: Dict[str, Any] = {}
            if response_id:
                metadata["response_id"] = response_id
            url_citations = self._extract_url_citations(segment_output_items)
            if url_citations:
                metadata["url_citations"] = url_citations
            web_search_sources = self._extract_web_search_sources(segment_output_items)
            if web_search_sources:
                metadata["web_search_sources"] = web_search_sources
            metadata["native_indices"] = sorted(set(segment_indices))
            if phase_messages:
                metadata["phase_messages"] = phase_messages
            return {"role": "assistant", "content": "", "metadata": metadata}

        canonical_md_raw = canonical.get("metadata") or {}
        canonical_md = (
            dict(canonical_md_raw) if isinstance(canonical_md_raw, dict) else {}
        )
        if response_id:
            canonical_md["response_id"] = response_id
        url_citations = self._extract_url_citations(segment_output_items)
        if url_citations:
            canonical_md["url_citations"] = url_citations
        web_search_sources = self._extract_web_search_sources(segment_output_items)
        if web_search_sources:
            canonical_md["web_search_sources"] = web_search_sources
        canonical_md["native_indices"] = sorted(set(segment_indices))
        if phase_messages:
            canonical_md["phase_messages"] = phase_messages

        out: Dict[str, Any] = {
            "role": "assistant",
            "content": (
                canonical.get("content")
                if isinstance(canonical.get("content"), str)
                else ""
            ),
            "metadata": canonical_md,
        }
        multipart = canonical.get("multipartContent")
        if isinstance(multipart, list) and multipart:
            out["multipartContent"] = multipart
        return out

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        native: List[Dict[str, Any]] = []

        for msg in messages:
            if not isinstance(msg, dict):
                continue

            # Allow explicit provider-native pass-through.
            if isinstance(msg.get("type"), str):
                native.append(msg)
                continue

            role = msg.get("role")
            metadata = msg.get("metadata")
            internal_md = self._native_internal_from_core_metadata(metadata)

            if role in ("system", "user", "assistant", "developer"):
                content = msg.get("content", "")
                text = content if isinstance(content, str) else ""

                parts: List[Dict[str, Any]] = []
                attachment_sources: List[Dict[str, Any]] = []
                if text:
                    text_part_type = (
                        "output_text" if role == "assistant" else "input_text"
                    )
                    parts.append({"type": text_part_type, "text": text})

                multipart = msg.get("multipartContent")
                if isinstance(multipart, list):
                    for part in multipart:
                        if not isinstance(part, dict):
                            continue
                        normalized_part = self._normalized_multipart_part(part)
                        if normalized_part is None:
                            continue

                        if normalized_part.get("type") == "image":
                            native_part = self._image_part_to_input_image(
                                part.get("content"),
                                state,
                                context,
                            )
                        else:
                            native_part = self._pdf_part_to_input_file(
                                part.get("content"),
                                state,
                                context,
                            )

                        parts.append(native_part)
                        attachment_sources.append(
                            {
                                "content_index": len(parts) - 1,
                                "multipart_part": normalized_part,
                            }
                        )

                item: Dict[str, Any] = {
                    "type": "message",
                    "role": role,
                    "content": parts,
                }

                if role == "assistant" and isinstance(metadata, dict):
                    phase = metadata.get("phase")
                    if isinstance(phase, str) and phase:
                        item["phase"] = phase

                if internal_md:
                    item["_metadata"] = internal_md
                if attachment_sources:
                    base_metadata = (
                        item.get("_metadata")
                        if isinstance(item.get("_metadata"), dict)
                        else {}
                    )
                    item["_metadata"] = {
                        **base_metadata,
                        _ATTACHMENT_SOURCES_METADATA_KEY: attachment_sources,
                    }
                native.append(item)
                continue

            if role == "tool":
                tool_call_id = None
                if isinstance(metadata, dict):
                    tool_call_id = metadata.get("tool_call_id")
                if not isinstance(tool_call_id, str) or not tool_call_id:
                    raise ValueError(
                        "[openai_responses_provider] tool message requires metadata.tool_call_id"
                    )

                output: Any = openai_responses_tool_result_output(msg.get("content"))
                if isinstance(metadata, dict):
                    structured_output = metadata.get("tool_output_content")
                    if (
                        output is None
                        and isinstance(structured_output, list)
                        and all(isinstance(item, dict) for item in structured_output)
                    ):
                        output = structured_output

                if output is None:
                    output = msg.get("content", "")
                    if not isinstance(output, str):
                        try:
                            output = json.dumps(output, ensure_ascii=False)
                        except Exception:
                            output = ""

                item = {
                    "type": "function_call_output",
                    "call_id": tool_call_id,
                    "output": output,
                }

                internal_tool_md = dict(internal_md)
                internal_tool_md.pop("tool_call_id", None)
                if internal_tool_md:
                    item["_metadata"] = internal_tool_md

                native.append(item)
                continue

            raise ValueError(f"[openai_responses_provider] unsupported role: {role}")

        return native

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        owned_native_indices: set[int] = set()
        current_segment: List[Tuple[int, Dict[str, Any], Dict[str, Any]]] = []
        current_response_id: Optional[str] = None

        def _append_core_message(
            core_msg: Dict[str, Any], *, owned_indices: List[int]
        ) -> None:
            out.append(core_msg)
            owned_native_indices.update(i for i in owned_indices if isinstance(i, int))

        def _merge_native_indices(core_index: int, indices: List[int]) -> None:
            raw_md = out[core_index].get("metadata") or {}
            md = dict(raw_md) if isinstance(raw_md, dict) else {}
            existing = md.get("native_indices")
            existing_indices = (
                [i for i in existing if isinstance(i, int)]
                if isinstance(existing, list)
                else []
            )
            merged = sorted(
                set(existing_indices + [i for i in indices if isinstance(i, int)])
            )
            md["native_indices"] = merged
            out[core_index] = {**out[core_index], "metadata": md}
            owned_native_indices.update(merged)

        def _flush_response_segment() -> None:
            nonlocal current_segment, current_response_id
            if not current_segment:
                current_response_id = None
                return

            assistant_message = self._build_response_segment_assistant(current_segment)
            assistant_md = assistant_message.get("metadata") or {}
            assistant_indices = assistant_md.get("native_indices")
            _append_core_message(
                assistant_message,
                owned_indices=(
                    assistant_indices if isinstance(assistant_indices, list) else []
                ),
            )

            for native_index, item, internal_md in current_segment:
                if item.get("type") != "function_call_output":
                    continue

                call_id = item.get("call_id")
                if not isinstance(call_id, str) or not call_id:
                    continue

                output = item.get("output")
                if not isinstance(output, str):
                    try:
                        output = json.dumps(output, ensure_ascii=False)
                    except Exception:
                        output = ""

                tool_md = dict(internal_md)
                tool_md.setdefault("tool_call_id", call_id)
                tool_md["native_indices"] = [native_index]
                _append_core_message(
                    {"role": "tool", "content": output, "metadata": tool_md},
                    owned_indices=[native_index],
                )

            current_segment = []
            current_response_id = None

        for native_index, item in enumerate(native_messages):
            if not isinstance(item, dict):
                continue

            raw_internal_md = (
                item.get("_metadata") if isinstance(item.get("_metadata"), dict) else {}
            )
            internal_md = self._core_metadata_from_native_internal(
                item.get("_metadata")
            )
            response_id = (
                internal_md.get("response_id")
                if isinstance(internal_md.get("response_id"), str)
                else None
            )

            if response_id:
                if current_segment and response_id != current_response_id:
                    _flush_response_segment()
                current_response_id = response_id
                current_segment.append((native_index, item, internal_md))
                continue

            _flush_response_segment()

            # Streaming partial compatibility: allow chat-like shape.
            if "type" not in item and ("role" in item or "content" in item):
                role = (
                    item.get("role")
                    if isinstance(item.get("role"), str)
                    else "assistant"
                )
                content = (
                    item.get("content") if isinstance(item.get("content"), str) else ""
                )
                md = dict(internal_md)
                md["native_indices"] = [native_index]
                _append_core_message(
                    {"role": role, "content": content, "metadata": md},
                    owned_indices=[native_index],
                )
                continue

            item_type = item.get("type")

            if item_type == "message":
                role = (
                    item.get("role")
                    if isinstance(item.get("role"), str)
                    else "assistant"
                )
                text, images = self._extract_text_and_images_from_content(
                    item.get("content"),
                    raw_internal_md,
                )

                md = dict(internal_md)
                phase = item.get("phase")
                if isinstance(phase, str) and phase:
                    md.setdefault("phase", phase)
                md["native_indices"] = [native_index]

                core_msg: Dict[str, Any] = {
                    "role": role,
                    "content": text,
                    "metadata": md,
                }
                if images:
                    core_msg["multipartContent"] = images

                _append_core_message(
                    core_msg,
                    owned_indices=[native_index],
                )
                continue

            if item_type == "function_call_output":
                call_id = item.get("call_id")
                if not isinstance(call_id, str) or not call_id:
                    continue

                output = item.get("output")
                if not isinstance(output, str):
                    try:
                        output = json.dumps(output, ensure_ascii=False)
                    except Exception:
                        output = ""

                md = dict(internal_md)
                md.setdefault("tool_call_id", call_id)
                md["native_indices"] = [native_index]

                _append_core_message(
                    {
                        "role": "tool",
                        "content": output,
                        "metadata": md,
                    },
                    owned_indices=[native_index],
                )

        _flush_response_segment()

        dict_native_indices = {
            idx for idx, item in enumerate(native_messages) if isinstance(item, dict)
        }
        orphan_indices = sorted(dict_native_indices.difference(owned_native_indices))
        if not orphan_indices:
            return out

        owner_index: Optional[int] = None
        for core_index in range(len(out) - 1, -1, -1):
            if out[core_index].get("role") == "assistant":
                owner_index = core_index
                break
        if owner_index is None and out:
            owner_index = len(out) - 1

        if owner_index is None:
            out.append(
                {
                    "role": "assistant",
                    "content": "",
                    "metadata": {"native_indices": orphan_indices},
                }
            )
            return out

        _merge_native_indices(owner_index, orphan_indices)
        return out

    def _validate_native_item_list(self, items: List[Dict[str, Any]]) -> None:
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                raise RuntimeError(
                    f"[openai_responses_provider] invalid input item at index {idx}: expected dict"
                )
            item_type = item.get("type")
            if not isinstance(item_type, str) or not item_type:
                raise RuntimeError(
                    f"[openai_responses_provider] invalid input item at index {idx}: missing 'type'"
                )

    def _strip_internal_metadata(self, item: JsonObject) -> JsonObject:
        if "_metadata" not in item:
            return item
        return {k: v for k, v in item.items() if k != "_metadata"}

    def _sanitize_input_item(self, item: JsonObject) -> JsonObject:
        sanitized = dict(self._strip_internal_metadata(item))
        item_type = sanitized.get("type")

        if item_type in _COMPACTION_ITEM_TYPES:
            compacted: JsonObject = {
                "type": str(item_type),
                "encrypted_content": sanitized.get("encrypted_content", ""),
            }
            if isinstance(sanitized.get("id"), str) and sanitized.get("id"):
                compacted["id"] = sanitized["id"]
            return compacted

        for key in ("id", "status", "namespace", "phase"):
            sanitized.pop(key, None)

        content = sanitized.get("content")
        if isinstance(content, list):
            cleaned_content: List[Dict[str, Any]] = []
            role = (
                sanitized.get("role")
                if isinstance(sanitized.get("role"), str)
                else None
            )
            for part in content:
                if not isinstance(part, dict):
                    continue
                cleaned_part = dict(part)
                cleaned_part.pop("annotations", None)
                cleaned_part.pop("logprobs", None)
                if role == "assistant" and cleaned_part.get("type") == "input_text":
                    cleaned_part["type"] = "output_text"
                cleaned_content.append(cleaned_part)
            sanitized["content"] = cleaned_content

        return sanitized

    def _response_to_dict(self, response: Any) -> Dict[str, Any]:
        if isinstance(response, dict):
            return response
        if hasattr(response, "model_dump"):
            dumped = response.model_dump(mode="python")
            if isinstance(dumped, dict):
                return dumped
        raise RuntimeError("[openai_responses_provider] invalid SDK response payload")

    def _stream_event_to_dict(self, event: Any) -> Dict[str, Any]:
        if isinstance(event, dict):
            return event
        if hasattr(event, "model_dump"):
            dumped = event.model_dump(mode="python")
            if isinstance(dumped, dict):
                return dumped
        raise RuntimeError(
            "[openai_responses_provider] invalid SDK stream event payload"
        )

    def _iter_raw_sse_event_dicts(self, response: Any) -> Iterator[Dict[str, Any]]:
        iter_lines = getattr(response, "iter_lines", None)
        if not callable(iter_lines):
            raise RuntimeError(
                "[openai_responses_provider] raw streaming response is missing iter_lines()"
            )

        data_lines: List[str] = []
        for raw_line in iter_lines():
            line = raw_line if isinstance(raw_line, str) else str(raw_line)
            if not line:
                if not data_lines:
                    continue
                payload_text = "\n".join(data_lines).strip()
                data_lines = []
                if not payload_text or payload_text == "[DONE]":
                    continue
                try:
                    payload = json.loads(payload_text)
                except Exception as exc:
                    raise RuntimeError(
                        "[openai_responses_provider] invalid JSON event in raw streaming response"
                    ) from exc
                if isinstance(payload, dict):
                    yield payload
                continue
            if line.startswith(":"):
                continue
            if line.startswith("data:"):
                data_lines.append(line[5:].lstrip())

        if data_lines:
            payload_text = "\n".join(data_lines).strip()
            if payload_text and payload_text != "[DONE]":
                try:
                    payload = json.loads(payload_text)
                except Exception as exc:
                    raise RuntimeError(
                        "[openai_responses_provider] invalid trailing JSON event in raw streaming response"
                    ) from exc
                if isinstance(payload, dict):
                    yield payload

    def _safe_dict_payload(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return payload
        if hasattr(payload, "model_dump"):
            dumped = payload.model_dump(mode="python")
            if isinstance(dumped, dict):
                return dumped
        return {}

    def _terminal_stream_error_message(self, event: Dict[str, Any]) -> Optional[str]:
        event_type = event.get("type")
        if not isinstance(event_type, str):
            return None

        if event_type == "error":
            message = (
                event.get("message")
                if isinstance(event.get("message"), str)
                else "unknown error"
            )
            code = event.get("code") if isinstance(event.get("code"), str) else None
            details = f" code={code}" if code else ""
            return f"OpenAI Responses stream failed: terminal event error{details}: {message}"

        if event_type == "response.failed":
            response_obj = self._safe_dict_payload(event.get("response"))
            response_id = (
                response_obj.get("id")
                if isinstance(response_obj.get("id"), str)
                else None
            )
            error_obj = (
                response_obj.get("error")
                if isinstance(response_obj.get("error"), dict)
                else {}
            )
            code = (
                error_obj.get("code")
                if isinstance(error_obj.get("code"), str)
                else None
            )
            message = (
                error_obj.get("message")
                if isinstance(error_obj.get("message"), str)
                else "response failed"
            )
            context: List[str] = []
            if isinstance(response_id, str) and response_id:
                context.append(f"response_id={response_id}")
            if isinstance(code, str) and code:
                context.append(f"code={code}")
            suffix = f" ({', '.join(context)})" if context else ""
            return f"OpenAI Responses stream failed: terminal event response.failed{suffix}: {message}"

        if event_type == "response.incomplete":
            response_obj = self._safe_dict_payload(event.get("response"))
            response_id = (
                response_obj.get("id")
                if isinstance(response_obj.get("id"), str)
                else None
            )
            details_obj = (
                response_obj.get("incomplete_details")
                if isinstance(response_obj.get("incomplete_details"), dict)
                else {}
            )
            reason = (
                details_obj.get("reason")
                if isinstance(details_obj.get("reason"), str)
                else None
            )
            context: List[str] = []
            if isinstance(response_id, str) and response_id:
                context.append(f"response_id={response_id}")
            if isinstance(reason, str) and reason:
                context.append(f"reason={reason}")
            suffix = f" ({', '.join(context)})" if context else ""
            return f"OpenAI Responses stream failed: terminal event response.incomplete{suffix}"

        return None

    def _response_internal_metadata(
        self, response_obj: Dict[str, Any]
    ) -> Dict[str, Any]:
        md: Dict[str, Any] = {}

        response_id = response_obj.get("id")
        if isinstance(response_id, str) and response_id:
            md["response_id"] = response_id

        # Keep raw usage available to extensions without exposing provider-owned
        # usage fields directly in core message metadata.
        usage = self._safe_dict_payload(response_obj.get("usage"))
        if usage:
            md[_RAW_USAGE_METADATA_KEY] = usage

        service_tier = response_obj.get("service_tier")
        if isinstance(service_tier, str) and service_tier:
            md[_RAW_SERVICE_TIER_METADATA_KEY] = service_tier

        return md

    def _attach_internal_metadata_to_output(
        self,
        output_items: List[JsonObject],
        response_md: Dict[str, Any],
    ) -> List[JsonObject]:
        if not output_items:
            return list(output_items)

        annotated: List[JsonObject] = []
        for item in output_items:
            if not isinstance(item, dict):
                annotated.append(item)
                continue

            base_internal = item.get("_metadata")
            base_internal_dict = (
                base_internal if isinstance(base_internal, dict) else {}
            )

            if response_md:
                annotated.append(
                    {**item, "_metadata": {**base_internal_dict, **response_md}}
                )
                continue

            annotated.append(item)
        return annotated

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        request = state.get("request")
        if not isinstance(request, dict):
            raise RuntimeError("[openai_responses_provider] missing request in state")
        context = self._request_context(state)
        cfg = state.get("config") or {}
        if self._effective_auth_mode(cfg) == "chatgpt":
            raise RuntimeError(
                "[openai_responses_provider] chatgpt auth_mode requires streaming requests; use send_request_stream or switch auth_mode to api/auto"
            )

        override = request.get("messages")
        base_history = override if isinstance(override, list) else native_messages
        self._validate_native_item_list(base_history)
        prepared_input = _prepare_input_and_instructions_shared(
            base_history,
            self._request_instructions(request),
            cfg,
        )
        self._validate_native_item_list(prepared_input.input_items)

        payload = dict(request.get("payload") or {})
        if prepared_input.instructions is not None:
            payload["instructions"] = prepared_input.instructions

        request_history = list(prepared_input.input_items)

        timeout = self._coerce_timeout(request.get("timeout", _DEFAULT_TIMEOUT))
        max_retries = self._request_max_retries(request)
        extra_headers = dict(request.get("headers") or {})

        client = state.get("client")
        if client is None:
            client = self._create_sdk_client_with_options(
                cfg,
                timeout=timeout,
                max_retries=max_retries,
            )
        request_client = self._request_client(
            client, timeout=timeout, max_retries=max_retries
        )

        upload_cache = self._upload_state_cache(state)
        if self._attachment_upload_mode(state) == _ATTACHMENT_UPLOAD_MODE_UPLOAD:
            request_history = self._prepare_uploaded_native_messages(
                request_history,
                state=state,
                context=context,
                client=client,
                timeout=timeout,
                upload_cache=upload_cache,
            )
            self._prepare_uploaded_native_messages(
                native_messages,
                state=state,
                context=context,
                client=client,
                timeout=timeout,
                upload_cache=upload_cache,
                persist_uploaded_refs=True,
            )

        input_items = [self._sanitize_input_item(item) for item in request_history]
        runtime = self._register_inflight(request_id)
        results: queue.Queue[Tuple[str, Any]] = queue.Queue()

        def _close_client(candidate: Any) -> None:
            close = getattr(candidate, "close", None)
            if callable(close):
                close()

        def _worker() -> None:
            local_request_client = request_client
            runtime.add_closer(lambda: _close_client(local_request_client))
            try:
                if runtime.cancelled.is_set():
                    raise ProviderRequestCancelled(request_id)
                try:
                    sdk_response = local_request_client.responses.create(  # type: ignore[union-attr]
                        **{**payload, "input": input_items, "stream": False},
                        extra_headers=extra_headers,
                        timeout=timeout,
                    )
                except Exception as exc:
                    if self._attachment_upload_mode(
                        state
                    ) == _ATTACHMENT_UPLOAD_MODE_UPLOAD and self._is_attachment_reference_error(
                        exc
                    ):
                        retry_history = self._prepare_uploaded_native_messages(
                            request_history,
                            state=state,
                            context=context,
                            client=client,
                            timeout=timeout,
                            upload_cache=upload_cache,
                            force_reupload=True,
                        )
                        self._prepare_uploaded_native_messages(
                            native_messages,
                            state=state,
                            context=context,
                            client=client,
                            timeout=timeout,
                            upload_cache=upload_cache,
                            persist_uploaded_refs=True,
                            force_reupload=True,
                        )
                        retry_input_items = [
                            self._sanitize_input_item(item) for item in retry_history
                        ]
                        log.warning(
                            "attachment_upload_retrying",
                            action="call_api",
                            attempt=1,
                        )
                        sdk_response = local_request_client.responses.create(  # type: ignore[union-attr]
                            **{**payload, "input": retry_input_items, "stream": False},
                            extra_headers=extra_headers,
                            timeout=timeout,
                        )
                    else:
                        raise
                results.put(("result", self._response_to_dict(sdk_response)))
            except Exception as exc:
                results.put(("error", exc))
            finally:
                runtime.done.set()

        worker = threading.Thread(target=_worker, daemon=True)
        worker.start()

        try:
            while True:
                try:
                    kind, value = results.get(timeout=0.1)
                except queue.Empty:
                    if runtime.cancelled.is_set():
                        raise ProviderRequestCancelled(request_id)
                    if runtime.done.is_set() and results.empty():
                        raise RuntimeError(
                            "OpenAI Responses call failed: request ended without result"
                        )
                    continue
                if kind == "result":
                    response_obj = value
                    break
                exc = value
                if runtime.cancelled.is_set():
                    raise ProviderRequestCancelled(request_id) from exc
                raise RuntimeError(f"OpenAI Responses call failed: {exc}") from exc
        finally:
            self._clear_inflight(request_id, runtime)
            worker.join(timeout=1.0)

        output = response_obj.get("output")
        if not isinstance(output, list):
            raise RuntimeError(
                "OpenAI Responses call failed: missing output list in response"
            )

        output_items = [item for item in output if isinstance(item, dict)]

        response_md = self._response_internal_metadata(response_obj)
        annotated_output = self._attach_internal_metadata_to_output(
            output_items, response_md
        )

        new_state = {**state, "_openai_responses_upload_cache": upload_cache}
        return [], annotated_output, [*native_messages, *annotated_output], new_state

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Iterator[Dict[str, Any]]:
        request = state.get("request")
        if not isinstance(request, dict):
            raise RuntimeError("[openai_responses_provider] missing request in state")
        context = self._request_context(state)

        override = request.get("messages")
        base_history = override if isinstance(override, list) else native_messages
        cfg = state.get("config") or {}
        self._validate_native_item_list(base_history)
        prepared_input = _prepare_input_and_instructions_shared(
            base_history,
            self._request_instructions(request),
            cfg,
        )
        self._validate_native_item_list(prepared_input.input_items)

        payload = dict(request.get("payload") or {})
        if prepared_input.instructions is not None:
            payload["instructions"] = prepared_input.instructions

        request_history = list(prepared_input.input_items)

        timeout = self._coerce_timeout(request.get("timeout", _DEFAULT_TIMEOUT))
        max_retries = self._request_max_retries(request)
        stream_recovery_mode = self._request_stream_recovery_mode(request)
        stream_recovery_retries = self._request_stream_recovery_retries(request)
        extra_headers = dict(request.get("headers") or {})

        local_cfg = dict(cfg)
        client = state.get("client")
        if client is None:
            client = self._create_sdk_client_with_options(
                local_cfg,
                timeout=timeout,
                max_retries=max_retries,
            )
        request_client = self._request_client(
            client, timeout=timeout, max_retries=max_retries
        )

        upload_cache = self._upload_state_cache(state)
        if self._attachment_upload_mode(state) == _ATTACHMENT_UPLOAD_MODE_UPLOAD:
            request_history = self._prepare_uploaded_native_messages(
                request_history,
                state=state,
                context=context,
                client=client,
                timeout=timeout,
                upload_cache=upload_cache,
            )
            self._prepare_uploaded_native_messages(
                native_messages,
                state=state,
                context=context,
                client=client,
                timeout=timeout,
                upload_cache=upload_cache,
                persist_uploaded_refs=True,
            )
            state = {**state, "_openai_responses_upload_cache": upload_cache}

        input_items = [self._sanitize_input_item(item) for item in request_history]
        runtime = self._register_inflight(request_id)
        results: queue.Queue[Tuple[str, Any]] = queue.Queue()

        def _close_candidate(candidate: Any) -> None:
            close = getattr(candidate, "close", None)
            if callable(close):
                close()

        def _worker() -> None:
            local_request_client = request_client
            runtime.add_closer(
                lambda candidate=local_request_client: _close_candidate(candidate)
            )
            auth_recovery_used = False

            def _attempt_chatgpt_auth_recovery(exc: Exception) -> bool:
                nonlocal local_cfg, local_request_client, auth_recovery_used
                if (
                    auth_recovery_used
                    or self._effective_auth_mode(local_cfg) != "chatgpt"
                ):
                    return False
                if not self._is_unauthorized_error(exc):
                    return False

                reloaded_cfg = self._reload_chatgpt_credentials_if_changed(local_cfg)
                if reloaded_cfg is not None:
                    local_cfg = reloaded_cfg
                    local_request_client = self._rebuild_request_client(
                        local_cfg,
                        timeout=timeout,
                        max_retries=max_retries,
                    )
                    runtime.add_closer(
                        lambda candidate=local_request_client: _close_candidate(
                            candidate
                        )
                    )
                    log.warning(
                        "chatgpt_auth_recovery_retrying",
                        action="stream_api",
                        attempt=1,
                        source="reloaded_credentials",
                    )
                    auth_recovery_used = True
                    return True

                try:
                    refreshed_cfg = self._refresh_chatgpt_config(
                        local_cfg, timeout=timeout
                    )
                except ChatGPTRefreshPermanentError as refresh_exc:
                    raise RuntimeError(str(refresh_exc)) from refresh_exc
                except ChatGPTRefreshTransientError as refresh_exc:
                    raise RuntimeError(str(refresh_exc)) from refresh_exc

                local_cfg = refreshed_cfg
                local_request_client = self._rebuild_request_client(
                    local_cfg,
                    timeout=timeout,
                    max_retries=max_retries,
                )
                runtime.add_closer(
                    lambda candidate=local_request_client: _close_candidate(candidate)
                )
                log.warning(
                    "chatgpt_auth_recovery_retrying",
                    action="stream_api",
                    attempt=1,
                    source="refreshed_config",
                )
                auth_recovery_used = True
                return True

            recovery_attempts = 0
            terminal_error_attempts = 0
            try:
                while True:
                    if runtime.cancelled.is_set():
                        raise ProviderRequestCancelled(request_id)
                    responses_resource = getattr(
                        local_request_client, "responses", None
                    )
                    raw_stream_resource = (
                        getattr(responses_resource, "with_streaming_response", None)
                        if responses_resource is not None
                        and self._effective_auth_mode(local_cfg) == "chatgpt"
                        else None
                    )
                    use_raw_streaming = bool(
                        raw_stream_resource is not None
                        and hasattr(raw_stream_resource, "create")
                    )
                    try:
                        if use_raw_streaming:
                            sdk_stream = raw_stream_resource.create(  # type: ignore[union-attr]
                                **{**payload, "input": input_items, "stream": True},
                                extra_headers=extra_headers,
                                timeout=timeout,
                            )
                        else:
                            sdk_stream = local_request_client.responses.create(  # type: ignore[union-attr]
                                **{**payload, "input": input_items, "stream": True},
                                extra_headers=extra_headers,
                                timeout=timeout,
                            )
                    except Exception as exc:
                        if self._attachment_upload_mode(
                            state
                        ) == _ATTACHMENT_UPLOAD_MODE_UPLOAD and self._is_attachment_reference_error(
                            exc
                        ):
                            retry_history = self._prepare_uploaded_native_messages(
                                request_history,
                                state=state,
                                context=context,
                                client=client,
                                timeout=timeout,
                                upload_cache=upload_cache,
                                force_reupload=True,
                            )
                            self._prepare_uploaded_native_messages(
                                native_messages,
                                state=state,
                                context=context,
                                client=client,
                                timeout=timeout,
                                upload_cache=upload_cache,
                                persist_uploaded_refs=True,
                                force_reupload=True,
                            )
                            retry_input_items = [
                                self._sanitize_input_item(item)
                                for item in retry_history
                            ]
                            log.warning(
                                "attachment_upload_retrying",
                                action="stream_api",
                                attempt=1,
                            )
                            if use_raw_streaming:
                                sdk_stream = raw_stream_resource.create(  # type: ignore[union-attr]
                                    **{
                                        **payload,
                                        "input": retry_input_items,
                                        "stream": True,
                                    },
                                    extra_headers=extra_headers,
                                    timeout=timeout,
                                )
                            else:
                                sdk_stream = local_request_client.responses.create(  # type: ignore[union-attr]
                                    **{
                                        **payload,
                                        "input": retry_input_items,
                                        "stream": True,
                                    },
                                    extra_headers=extra_headers,
                                    timeout=timeout,
                                )
                        else:
                            if _attempt_chatgpt_auth_recovery(exc):
                                continue
                            raise

                    runtime.add_closer(
                        lambda stream=sdk_stream: _close_candidate(stream)
                    )
                    saw_completed = False
                    emitted_visible_output = False
                    stream_error: Exception | None = None

                    try:
                        if hasattr(sdk_stream, "__enter__") and hasattr(
                            sdk_stream, "__exit__"
                        ):
                            with sdk_stream as stream:
                                runtime.add_closer(
                                    lambda active_stream=stream: _close_candidate(
                                        active_stream
                                    )
                                )
                                if use_raw_streaming:
                                    self._capture_chatgpt_rate_limits(
                                        local_cfg,
                                        getattr(stream, "headers", None),
                                    )
                                    event_iter = self._iter_raw_sse_event_dicts(stream)
                                else:
                                    self._capture_chatgpt_rate_limits_from_stream(
                                        local_cfg, stream
                                    )
                                    event_iter = stream
                                for event in event_iter:
                                    if runtime.cancelled.is_set():
                                        raise ProviderRequestCancelled(request_id)
                                    event_dict = self._stream_event_to_dict(event)
                                    if event_dict.get("type") == "response.completed":
                                        saw_completed = True
                                    if self._stream_event_has_visible_output(
                                        event_dict
                                    ):
                                        emitted_visible_output = True
                                    if event_dict.get("type") == "error":
                                        if (
                                            self._config_terminal_error_retries_enabled(
                                                local_cfg
                                            )
                                            and not emitted_visible_output
                                        ):
                                            terminal_msg = (
                                                self._terminal_stream_error_message(
                                                    event_dict
                                                )
                                            )
                                            if terminal_msg is not None:
                                                stream_error = RuntimeError(
                                                    terminal_msg
                                                )
                                                break
                                    results.put(("chunk", event_dict))
                        else:
                            for event in sdk_stream:
                                if runtime.cancelled.is_set():
                                    raise ProviderRequestCancelled(request_id)
                                event_dict = self._stream_event_to_dict(event)
                                if event_dict.get("type") == "response.completed":
                                    saw_completed = True
                                if self._stream_event_has_visible_output(event_dict):
                                    emitted_visible_output = True
                                if event_dict.get("type") == "error":
                                    if (
                                        self._config_terminal_error_retries_enabled(
                                            local_cfg
                                        )
                                        and not emitted_visible_output
                                    ):
                                        terminal_msg = (
                                            self._terminal_stream_error_message(
                                                event_dict
                                            )
                                        )
                                        if terminal_msg is not None:
                                            stream_error = RuntimeError(terminal_msg)
                                            break
                                results.put(("chunk", event_dict))
                    except Exception as exc:
                        stream_error = exc

                    if (
                        stream_error is not None
                        and not emitted_visible_output
                        and _attempt_chatgpt_auth_recovery(stream_error)
                    ):
                        continue

                    if saw_completed:
                        results.put(("done", None))
                        return

                    if (
                        stream_error is not None
                        and not emitted_visible_output
                        and self._config_terminal_error_retries_enabled(local_cfg)
                        and terminal_error_attempts
                        < self._config_terminal_error_max_retries(local_cfg)
                    ):
                        terminal_error_attempts += 1
                        log.warning(
                            "terminal_error_retrying",
                            action="stream_api",
                            attempt=terminal_error_attempts,
                            error=str(stream_error),
                        )
                        continue

                    should_recover = (
                        stream_recovery_mode != "disabled"
                        and recovery_attempts < stream_recovery_retries
                        and (
                            stream_recovery_mode == "aggressive"
                            or not emitted_visible_output
                        )
                    )
                    if should_recover:
                        recovery_attempts += 1
                        log.warning(
                            "stream_recovery_retrying",
                            action="stream_api",
                            attempt=recovery_attempts,
                            mode=stream_recovery_mode,
                        )
                        continue

                    if stream_error is not None:
                        raise stream_error
                    results.put(("done", None))
                    return
            except Exception as exc:
                results.put(("error", exc))
            finally:
                runtime.done.set()

        worker = threading.Thread(target=_worker, daemon=True)
        worker.start()

        try:
            while True:
                try:
                    kind, value = results.get(timeout=0.1)
                except queue.Empty:
                    if runtime.cancelled.is_set():
                        raise ProviderRequestCancelled(request_id)
                    if runtime.done.is_set() and results.empty():
                        return
                    continue
                if kind == "chunk":
                    yield value
                    continue
                if kind == "done":
                    return
                exc = value
                if runtime.cancelled.is_set():
                    raise ProviderRequestCancelled(request_id) from exc
                raise RuntimeError(f"OpenAI Responses stream failed: {exc}") from exc
        finally:
            self._clear_inflight(request_id, runtime)
            worker.join(timeout=1.0)

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        event = native_chunk if isinstance(native_chunk, dict) else {}
        event_type = event.get("type")

        new_state: Dict[str, Any] = {
            **state,
            "_openai_responses_stream_started": True,
        }

        terminal_error_message = self._terminal_stream_error_message(event)
        if terminal_error_message is not None:
            raise RuntimeError(terminal_error_message)

        emitted_partials: List[Dict[str, Any]] = []
        emitted_finals: List[Dict[str, Any]] = []
        accumulated_output_items = state.get("_openai_responses_stream_output_items")
        output_items_state = (
            [item for item in accumulated_output_items if isinstance(item, dict)]
            if isinstance(accumulated_output_items, list)
            else []
        )

        if event_type == "response.output_text.delta":
            delta = event.get("delta")
            if isinstance(delta, str) and delta:
                emitted_partials.append({"role": "assistant", "content": delta})

        if event_type in (
            "response.reasoning_summary_text.delta",
            "response.reasoning_summary.delta",
            "response.reasoning.delta",
        ):
            delta = event.get("delta")
            if not isinstance(delta, str) and isinstance(delta, dict):
                raw_text = delta.get("text")
                delta = raw_text if isinstance(raw_text, str) else None
            if isinstance(delta, str) and delta:
                emitted_partials.append(
                    {
                        "role": "assistant",
                        "content": "",
                        "_metadata": {"reasoning": delta},
                    }
                )

        if event_type == "response.output_item.done":
            item = event.get("item")
            if isinstance(item, dict):
                output_items_state = [*output_items_state, item]
                new_state["_openai_responses_stream_output_items"] = output_items_state

        if event_type == "response.completed":
            response_payload = event.get("response")
            response_obj = self._response_to_dict(response_payload)

            output = response_obj.get("output")
            if not isinstance(output, list):
                raise RuntimeError(
                    "OpenAI Responses stream failed: missing output list in response.completed event"
                )

            output_items = [item for item in output if isinstance(item, dict)]
            if not output_items and output_items_state:
                output_items = list(output_items_state)
            response_md = self._response_internal_metadata(response_obj)
            emitted_finals = self._attach_internal_metadata_to_output(
                output_items, response_md
            )

            new_state = {
                **new_state,
                "_openai_responses_stream_completed": True,
                "_openai_responses_stream_output_items": [],
            }

            if emitted_finals:
                return (
                    emitted_partials,
                    emitted_finals,
                    [*native_messages, *emitted_finals],
                    new_state,
                )

        return emitted_partials, emitted_finals, list(native_messages), new_state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        started = bool(state.get("_openai_responses_stream_started"))
        completed = bool(state.get("_openai_responses_stream_completed"))
        if started and not completed:
            raise RuntimeError(
                "OpenAI Responses stream failed: stream ended without response.completed terminal event"
            )
        return [], list(native_messages), state
