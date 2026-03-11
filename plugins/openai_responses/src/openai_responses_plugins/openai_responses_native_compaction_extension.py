"""OpenAI Responses native compaction session action."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from openai import OpenAI

from agent_core.types import ProviderExtensionPlugin, Session


_DEFAULT_TIMEOUT = 60.0
_COMPACTION_METADATA_KEY = "openai_responses_compaction"
_COMPACTION_PLACEHOLDER_TEXT = "Earlier conversation compacted to reduce context size."


class OpenAIResponsesNativeCompactionExtension(ProviderExtensionPlugin):
    name = "openai_responses_native_compaction"
    version = "0.1.0"
    priority = 90

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
                    "end_index": "$dialog.end_index",
                    "instructions": "$dialog.instructions",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Compact native history",
                    "message": (
                        "Compact provider-native history for future Responses requests "
                        "and replace the compacted prefix with a visible placeholder message."
                    ),
                    "inputs": [
                        {
                            "name": "end_index",
                            "type": "number",
                            "label": "Compact visible messages [:end]",
                            "required": False,
                            "placeholder": "Leave empty to compact the full history",
                        },
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
                    "end_index": {"type": "integer", "required": False},
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
            sanitized = {key: value for key, value in item.items() if key != "_metadata"}
        else:
            sanitized = dict(item)

        item_type = sanitized.get("type")
        if item_type == "compaction":
            compacted: Dict[str, Any] = {
                "type": "compaction",
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
            for part in content:
                if not isinstance(part, dict):
                    continue
                cleaned_part = dict(part)
                cleaned_part.pop("annotations", None)
                cleaned_part.pop("logprobs", None)
                cleaned_content.append(cleaned_part)
            sanitized["content"] = cleaned_content

        return sanitized

    def _placeholder_metadata_from_segment(
        self,
        segment: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        response_id: Optional[str] = None
        for item in reversed(segment):
            if not isinstance(item, dict):
                continue
            internal = item.get("_metadata")
            if not isinstance(internal, dict):
                continue
            raw_response_id = internal.get("response_id")
            if isinstance(raw_response_id, str) and raw_response_id:
                response_id = raw_response_id
                break

        payload: Dict[str, Any] = {
            "native_segment": [item for item in segment if isinstance(item, dict)],
            "kind": "native_compaction",
        }
        if response_id is not None:
            payload["response_id"] = response_id
        return payload

    def _placeholder_message_for_segment(
        self,
        segment: List[Dict[str, Any]],
        native_indices: List[int],
    ) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {
            _COMPACTION_METADATA_KEY: self._placeholder_metadata_from_segment(segment),
            "native_indices": list(native_indices),
        }
        return {
            "role": "assistant",
            "content": _COMPACTION_PLACEHOLDER_TEXT,
            "metadata": metadata,
        }

    def _segment_from_placeholder_message(self, message: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        raw_metadata = message.get("metadata")
        metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
        raw_compaction = metadata.get(_COMPACTION_METADATA_KEY)
        compaction = raw_compaction if isinstance(raw_compaction, dict) else {}
        raw_segment = compaction.get("native_segment")
        if not isinstance(raw_segment, list):
            return None
        segment = [item for item in raw_segment if isinstance(item, dict)]
        return segment or None

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        rebuilt: List[Dict[str, Any]] = []
        native_cursor = 0

        for message in messages:
            segment = self._segment_from_placeholder_message(message)
            if segment is not None:
                rebuilt.extend(segment)
                if native_cursor < len(native_messages):
                    native_cursor += 1
                continue

            if native_cursor >= len(native_messages):
                break
            rebuilt.append(native_messages[native_cursor])
            native_cursor += 1

        if native_cursor < len(native_messages):
            rebuilt.extend(native_messages[native_cursor:])

        return rebuilt

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        segments: List[tuple[int, int]] = []
        segment_start = 0
        for native_index, item in enumerate(native_messages):
            if not isinstance(item, dict):
                continue
            if item.get("type") != "compaction":
                continue
            segments.append((segment_start, native_index))
            segment_start = native_index + 1

        if not segments:
            return list(messages)

        def _message_native_indices(message: Dict[str, Any]) -> List[int]:
            raw_metadata = message.get("metadata")
            metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
            raw_indices = metadata.get("native_indices")
            if not isinstance(raw_indices, list):
                return []
            return [index for index in raw_indices if isinstance(index, int)]

        msg_indices = [_message_native_indices(message) for message in messages]
        result: List[Dict[str, Any]] = []
        consumed_until = 0

        for start, end in segments:
            segment_indices = list(range(start, end + 1))
            segment_index_set = set(segment_indices)
            affected = [
                idx
                for idx, indices in enumerate(msg_indices)
                if indices and any(start <= native_index <= end for native_index in indices)
            ]

            if affected:
                insertion_index = affected[0]
            else:
                insertion_index = len(messages)
                for idx, indices in enumerate(msg_indices):
                    if indices and max(indices) >= start:
                        insertion_index = idx
                        break

            for idx in range(consumed_until, insertion_index):
                result.append(messages[idx])

            placeholder = self._placeholder_message_for_segment(
                native_messages[start : end + 1],
                segment_indices,
            )
            result.append(placeholder)

            affected_set = set(affected)
            affected_end = max(affected) if affected else insertion_index - 1
            for idx in range(insertion_index, affected_end + 1):
                if idx not in affected_set:
                    result.append(messages[idx])
                    continue

                message = messages[idx]
                indices = msg_indices[idx]
                remaining_indices = [
                    native_index for native_index in indices if native_index not in segment_index_set
                ]
                if not remaining_indices:
                    continue

                raw_metadata = message.get("metadata")
                metadata = dict(raw_metadata) if isinstance(raw_metadata, dict) else {}
                metadata["native_indices"] = remaining_indices
                result.append({**message, "metadata": metadata})

            consumed_until = affected_end + 1 if affected else insertion_index

        for idx in range(consumed_until, len(messages)):
            result.append(messages[idx])

        return result

    def _resolve_end_index(self, session: Session, params: Dict[str, Any]) -> int:
        visible_count = len(session.messages)
        raw_end_index = params.get("end_index")
        if raw_end_index is None:
            end_index = visible_count
        else:
            if not isinstance(raw_end_index, int) or isinstance(raw_end_index, bool):
                raise ValueError("end_index must be an integer")
            end_index = raw_end_index

        if end_index <= 0:
            raise ValueError("end_index must be greater than 0")
        if end_index > visible_count:
            raise ValueError("end_index cannot exceed the visible message count")
        return end_index

    def _resolve_prefix_native_end(
        self,
        session: Session,
        end_index: int,
    ) -> int:
        prefix_messages = list(session.messages[:end_index])
        if not prefix_messages:
            raise ValueError("compaction prefix cannot be empty")

        native_indices: List[int] = []
        for message in prefix_messages:
            raw_metadata = message.metadata if isinstance(message.metadata, dict) else {}
            raw_indices = raw_metadata.get("native_indices")
            if not isinstance(raw_indices, list) or not raw_indices:
                raise RuntimeError(
                    "visible message range cannot be compacted because native history mapping is missing"
                )
            native_indices.extend(index for index in raw_indices if isinstance(index, int))

        if not native_indices:
            raise RuntimeError(
                "visible message range cannot be compacted because native history mapping is empty"
            )

        unique_indices = sorted(set(native_indices))
        if unique_indices[0] != 0:
            raise RuntimeError("compaction range must start at the beginning of native history")
        expected = list(range(unique_indices[-1] + 1))
        if unique_indices != expected:
            raise RuntimeError(
                "selected visible prefix does not map to a contiguous native prefix for compaction"
            )
        return unique_indices[-1] + 1

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
        if action_id != "compact_native_history":
            raise ValueError(
                f"Unknown action_id {action_id!r} for OpenAIResponsesNativeCompactionExtension"
            )

        config = state.get("config") if isinstance(state.get("config"), dict) else {}
        model = self._resolve_model(config)
        timeout = self._coerce_timeout(config.get("timeout", _DEFAULT_TIMEOUT))
        end_index = self._resolve_end_index(session, params)
        prefix_native_end = self._resolve_prefix_native_end(session, end_index)
        instructions = params.get("instructions")
        instructions_value = instructions.strip() if isinstance(instructions, str) else None

        client = state.get("client")
        if client is None:
            client = self._build_client(state)

        prefix_native = list(native_messages[:prefix_native_end])
        suffix_native = list(native_messages[prefix_native_end:])
        input_items = [
            self._sanitize_input_item(item)
            for item in prefix_native
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
            "native_messages": [*new_native_messages, *suffix_native],
            "message": (
                f"Compacted visible messages [:{end_index}]"
                if end_index < len(session.messages)
                else "Compacted the full visible history."
            ),
        }