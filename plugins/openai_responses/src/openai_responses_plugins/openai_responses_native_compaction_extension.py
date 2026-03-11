"""OpenAI Responses native compaction session action."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from openai import OpenAI

from agent_core.types import ProviderExtensionPlugin, Session


_DEFAULT_TIMEOUT = 60.0


class OpenAIResponsesNativeCompactionExtension(ProviderExtensionPlugin):
    name = "openai_responses_native_compaction"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = config, tags, models
        return [
            {
                "ui_type": "session_action",
                "id": "compact_native_history",
                "label": "Compact native history",
                "icon": "archive",
                "order": 46,
                "action_id": "compact_native_history",
                "action_owner": "provider_extension",
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                    "instructions": "$dialog.instructions",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Compact native history",
                    "message": (
                        "Compact provider-native history for future Responses requests "
                        "without replacing the visible transcript."
                    ),
                    "inputs": [
                        {
                            "name": "instructions",
                            "type": "multiline",
                            "label": "Instructions",
                            "required": False,
                            "placeholder": "Optional compaction instructions",
                        }
                    ],
                },
            }
        ]

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        _ = config, models
        return ["ext:openai_responses_native_compaction"]

    def required_tags(self) -> List[str]:
        return ["openai_responses"]

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "compact_native_history",
                "label": "Compact native history",
                "description": "Compact provider-native history with the OpenAI Responses compact API.",
                "inputs": {
                    "instructions": {"type": "string", "required": False},
                },
            }
        ]

    def _coerce_timeout(self, raw: Any) -> float:
        try:
            timeout = float(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "[openai_responses_native_compaction] timeout must be numeric"
            ) from exc
        if timeout <= 0:
            raise ValueError("[openai_responses_native_compaction] timeout must be > 0")
        return timeout

    def _resolve_model(self, config: Dict[str, Any]) -> str:
        model = config.get("model")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("[openai_responses_native_compaction] model is required")
        return model.strip()

    def _resolve_base_url(self, config: Dict[str, Any]) -> str:
        base_url = config.get("base_url") or "https://api.openai.com/v1"
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("[openai_responses_native_compaction] base_url must be a string")
        return base_url.rstrip("/")

    def _resolve_api_key(self, config: Dict[str, Any]) -> str:
        api_key = config.get("api_key")
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("[openai_responses_native_compaction] api_key is required")
        return api_key.strip()

    def _build_client(self, state: Dict[str, Any]) -> OpenAI:
        config = state.get("config") if isinstance(state.get("config"), dict) else {}
        return OpenAI(
            api_key=self._resolve_api_key(config),
            base_url=self._resolve_base_url(config),
            timeout=self._coerce_timeout(config.get("timeout", _DEFAULT_TIMEOUT)),
        )

    def _sanitize_input_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        metadata = item.get("_metadata")
        if isinstance(metadata, dict):
            sanitized = {
                key: value
                for key, value in item.items()
                if key != "_metadata"
            }
        else:
            sanitized = dict(item)

        for key in ("id", "status", "namespace"):
            sanitized.pop(key, None)
        return sanitized

    def _response_to_dict(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return payload
        if hasattr(payload, "model_dump"):
            dumped = payload.model_dump(mode="python")
            if isinstance(dumped, dict):
                return dumped
        raise RuntimeError("[openai_responses_native_compaction] invalid SDK compaction payload")

    def execute_action(
        self,
        action_id: str,
        session: Session,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = session
        if action_id != "compact_native_history":
            raise ValueError(
                f"Unknown action_id {action_id!r} for OpenAIResponsesNativeCompactionExtension"
            )

        config = state.get("config") if isinstance(state.get("config"), dict) else {}
        model = self._resolve_model(config)
        timeout = self._coerce_timeout(config.get("timeout", _DEFAULT_TIMEOUT))
        instructions = params.get("instructions")
        instructions_value = instructions.strip() if isinstance(instructions, str) else None

        client = state.get("client")
        if client is None:
            client = self._build_client(state)

        input_items = [
            self._sanitize_input_item(item)
            for item in native_messages
            if isinstance(item, dict)
        ]

        try:
            sdk_response = client.responses.compact(  # type: ignore[union-attr]
                model=model,
                input=input_items,
                instructions=instructions_value,
                timeout=timeout,
            )
        except Exception as exc:
            raise RuntimeError(f"OpenAI Responses compact failed: {exc}") from exc

        response_obj = self._response_to_dict(sdk_response)
        output = response_obj.get("output")
        if not isinstance(output, list):
            raise RuntimeError("OpenAI Responses compact failed: missing output list in response")

        new_native_messages = [item for item in output if isinstance(item, dict)]
        if not new_native_messages:
            raise RuntimeError("OpenAI Responses compact failed: empty compacted output")

        return {
            "native_messages": new_native_messages,
            "rebuild_messages_from_native": False,
            "message": "Compacted provider-native history.",
        }