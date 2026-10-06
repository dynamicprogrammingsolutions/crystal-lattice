"""OpenAI Responses native compaction session action."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

from agent_core.types import ProviderExtensionPlugin, Session
from .openai_responses_runtime import (
    DEFAULT_API_BASE_URL,
    DEFAULT_TIMEOUT,
    build_openai_sdk_client,
    effective_auth_mode,
    prepare_input_and_instructions_for_endpoint,
)
from .openai_responses_native_compaction import (
    COMPACTION_TRANSPORT_CONTEXT_KEY,
    OpenAIResponsesNativeCompactionBackend,
    OpenAIResponsesCompactionTransport,
    SyncOpenAIResponsesCompactionTransport,
)

_USE_CHATGPT_AUTH_FOR_COMPACTION_KEY = "use_chatgpt_auth_for_compaction"
_COMPACTION_MODEL_KEY = "compaction_model"
_USE_PLACEHOLDER_TRANSCRIPT_KEY = "use_compaction_placeholder_transcript"
_ENABLE_AUTOMATIC_COMPACTION_KEY = "enable_openai_automatic_compaction"
_AUTOMATIC_COMPACTION_TRIGGER_KEY = "openai_compaction_trigger_tokens"
_DEFAULT_AUTOMATIC_COMPACTION_TRIGGER = 200_000
_COMPACTION_ITEM_TYPES = {"compaction", "compaction_summary"}
_COMPACTION_METADATA_KEY = "openai_responses_compaction"
_COMPACTION_PLACEHOLDER_TEXT = "Earlier conversation compacted to reduce context size."
_PLACEHOLDER_TRANSCRIPT_STATE_KEY = (
    "_openai_responses_use_compaction_placeholder_transcript"
)
_SYNC_COMPACTION_ACTION_ID = "compact_native_history_sync"


class OpenAIResponsesNativeCompactionExtension(ProviderExtensionPlugin):
    name = "openai_responses_native_compaction"
    version = "0.1.0"
    priority = 90

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            _ENABLE_AUTOMATIC_COMPACTION_KEY: {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": (
                    "When true, ordinary Responses requests ask OpenAI to compact "
                    "the active context automatically at the configured token "
                    "threshold."
                ),
            },
            _AUTOMATIC_COMPACTION_TRIGGER_KEY: {
                "type": "integer",
                "required": False,
                "default": _DEFAULT_AUTOMATIC_COMPACTION_TRIGGER,
                "minimum": 1,
                "description": (
                    "Input-token threshold passed to OpenAI automatic context "
                    "compaction."
                ),
            },
            _USE_CHATGPT_AUTH_FOR_COMPACTION_KEY: {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": (
                    "When true, native compaction uses the same effective ChatGPT/API "
                    "endpoint and credentials as normal OpenAI Responses requests. "
                    "When false, compaction is forced onto the normal API endpoint."
                ),
            },
            _USE_PLACEHOLDER_TRANSCRIPT_KEY: {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": (
                    "When true, compacted native segments are shown in the visible "
                    "transcript as a single placeholder message instead of rebuilding "
                    "the compacted native output directly."
                ),
            },
            _COMPACTION_MODEL_KEY: {
                "type": "string",
                "required": False,
                "default": "",
                "description": (
                    "Optional model used for native compaction. Leave empty to use "
                    "the normal request model."
                ),
            },
        }

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            **state,
            _PLACEHOLDER_TRANSCRIPT_STATE_KEY: bool(
                config.get(_USE_PLACEHOLDER_TRANSCRIPT_KEY, False)
            ),
        }

    def _automatic_compaction_trigger(
        self,
        config: Optional[Dict[str, Any]],
    ) -> int:
        raw = (
            config.get(_AUTOMATIC_COMPACTION_TRIGGER_KEY)
            if isinstance(config, dict)
            else None
        )
        if raw is None:
            return _DEFAULT_AUTOMATIC_COMPACTION_TRIGGER
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < 1:
            raise ValueError(
                "[openai_responses_native_compaction] "
                "openai_compaction_trigger_tokens must be a positive integer"
            )
        return raw

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = tags, models
        if (
            isinstance(config, dict)
            and config.get("native_compaction_enabled") is False
        ):
            return []
        placeholder_enabled = self._placeholder_transcript_enabled_for_config(config)
        return [
            {
                "ui_type": "config",
                "type": "checkbox",
                "key": _ENABLE_AUTOMATIC_COMPACTION_KEY,
                "label": "Enable automatic OpenAI compaction",
                "default": bool(
                    isinstance(config, dict)
                    and config.get(_ENABLE_AUTOMATIC_COMPACTION_KEY, False)
                ),
            },
            {
                "ui_type": "config",
                "type": "number",
                "key": _AUTOMATIC_COMPACTION_TRIGGER_KEY,
                "label": "Automatic OpenAI compaction trigger tokens",
                "default": self._automatic_compaction_trigger(config),
                "minimum": 1,
            },
            {
                "ui_type": "config",
                "type": "checkbox",
                "key": _USE_CHATGPT_AUTH_FOR_COMPACTION_KEY,
                "label": "Use ChatGPT auth for native compaction",
                "default": True,
            },
            {
                "ui_type": "config",
                "type": "checkbox",
                "key": _USE_PLACEHOLDER_TRANSCRIPT_KEY,
                "label": "Show compacted history as placeholder transcript",
                "default": False,
            },
            {
                "ui_type": "config",
                "type": "text",
                "key": _COMPACTION_MODEL_KEY,
                "label": "Compaction model",
                "placeholder": "Use current model",
            },
            {
                "ui_type": "session_action",
                "id": "toggle_compaction_transcript_mode",
                "label": (
                    "Expand compacted messages"
                    if placeholder_enabled
                    else "Collapse compacted messages"
                ),
                "icon": "rows-3",
                "order": 45,
                "action_id": "toggle_compaction_transcript_mode",
                "action_owner": "provider_extension",
                "condition": {
                    "path": "metadata.openai_responses_compaction",
                    "exists": True,
                },
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                },
            },
        ]

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        _ = context
        config = state.get("config")
        config = config if isinstance(config, dict) else {}
        if not bool(config.get(_ENABLE_AUTOMATIC_COMPACTION_KEY, False)):
            return list(native_messages), state

        request = state.get("request")
        request = request if isinstance(request, dict) else {}
        payload = request.get("payload")
        payload = dict(payload) if isinstance(payload, dict) else {}
        payload["context_management"] = [
            {
                "type": "compaction",
                "compact_threshold": self._automatic_compaction_trigger(config),
            }
        ]
        return list(native_messages), {
            **state,
            "request": {
                **request,
                "payload": payload,
            },
        }

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        _ = config, models
        return ["ext:openai_responses_native_compaction"]

    def required_tags(self) -> List[str]:
        return ["openai_responses"]

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        config = state.get("config") if isinstance(state.get("config"), dict) else {}
        if config.get("native_compaction_enabled") is False:
            return []
        placeholder_enabled = self._placeholder_transcript_enabled_for_config(config)
        return [
            {
                "id": "toggle_compaction_transcript_mode",
                "label": (
                    "Expand compacted messages"
                    if placeholder_enabled
                    else "Collapse compacted messages"
                ),
                "description": (
                    "Toggle whether compacted native history is shown as a single "
                    "placeholder message or expanded rebuilt messages."
                ),
                "inputs": {},
            },
            {
                "id": _SYNC_COMPACTION_ACTION_ID,
                "label": "Compact native history synchronously",
                "description": (
                    "Synchronous compatibility adapter for OpenAI Responses "
                    "native compaction."
                ),
                "inputs": {
                    "end_index": {"type": "integer", "required": False},
                },
            },
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

    def _resolve_compaction_model(self, config: Dict[str, Any]) -> str:
        compaction_model = config.get(_COMPACTION_MODEL_KEY)
        if isinstance(compaction_model, str) and compaction_model.strip():
            return compaction_model.strip()
        return self._resolve_model(config)

    def _use_chatgpt_auth_for_compaction(self, config: Dict[str, Any]) -> bool:
        raw = config.get(_USE_CHATGPT_AUTH_FOR_COMPACTION_KEY, True)
        return False if raw is False else True

    def _compaction_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        if self._use_chatgpt_auth_for_compaction(config):
            return dict(config)

        forced = dict(config)
        forced["auth_mode"] = "api"
        forced["_openai_responses_effective_auth_mode"] = "api"
        forced["base_url"] = config.get("api_base_url") or DEFAULT_API_BASE_URL
        forced.pop("chatgpt_access_token", None)
        forced.pop("chatgpt_token_type", None)
        forced.pop("chatgpt_account_id", None)
        return forced

    def _build_client(self, config: Dict[str, Any]) -> OpenAI:
        return build_openai_sdk_client(
            config,
            timeout=self._coerce_timeout(config.get("timeout", DEFAULT_TIMEOUT)),
        )

    def _sanitize_input_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        metadata = item.get("_metadata")
        if isinstance(metadata, dict):
            sanitized = {
                key: value for key, value in item.items() if key != "_metadata"
            }
        else:
            sanitized = dict(item)

        item_type = sanitized.get("type")
        if item_type in _COMPACTION_ITEM_TYPES:
            compacted: Dict[str, Any] = {
                "type": str(item_type),
                "encrypted_content": sanitized.get("encrypted_content", ""),
            }
            if isinstance(sanitized.get("id"), str) and sanitized.get("id"):
                compacted["id"] = sanitized["id"]
            return compacted

        # Compaction replays web-search results under the same input schema.
        response_only_fields = (
            ("namespace", "phase")
            if item_type == "web_search_call"
            else ("id", "status", "namespace", "phase")
        )
        for key in response_only_fields:
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

    def _sanitize_compacted_output_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = dict(item)
        content = sanitized.get("content")
        if not isinstance(content, list):
            return sanitized

        cleaned_content: List[Dict[str, Any]] = []
        for part in content:
            if not isinstance(part, dict):
                continue
            cleaned_part = dict(part)
            cleaned_part.pop("annotations", None)
            cleaned_part.pop("logprobs", None)

            part_type = cleaned_part.get("type")
            if part_type in {"input_text", "output_text", "text"}:
                next_part: Dict[str, Any] = {"type": str(part_type)}
                if isinstance(cleaned_part.get("text"), str):
                    next_part["text"] = cleaned_part["text"]
                cleaned_content.append(next_part)
                continue

            if part_type in {"input_image", "image_url"}:
                next_part = {"type": str(part_type)}
                if isinstance(cleaned_part.get("image_url"), (str, dict)):
                    next_part["image_url"] = cleaned_part["image_url"]
                if isinstance(cleaned_part.get("file_id"), str) and cleaned_part.get(
                    "file_id"
                ):
                    next_part["file_id"] = cleaned_part["file_id"]
                if isinstance(cleaned_part.get("detail"), str) and cleaned_part.get(
                    "detail"
                ):
                    next_part["detail"] = cleaned_part["detail"]
                cleaned_content.append(next_part)
                continue

            if part_type == "input_file":
                next_part = {"type": "input_file"}
                if isinstance(cleaned_part.get("file_url"), str) and cleaned_part.get(
                    "file_url"
                ):
                    next_part["file_url"] = cleaned_part["file_url"]
                if isinstance(cleaned_part.get("file_id"), str) and cleaned_part.get(
                    "file_id"
                ):
                    next_part["file_id"] = cleaned_part["file_id"]
                if isinstance(cleaned_part.get("file_data"), str) and cleaned_part.get(
                    "file_data"
                ):
                    next_part["file_data"] = cleaned_part["file_data"]
                if isinstance(cleaned_part.get("filename"), str) and cleaned_part.get(
                    "filename"
                ):
                    next_part["filename"] = cleaned_part["filename"]
                cleaned_content.append(next_part)
                continue

            cleaned_part.pop("text", None)
            cleaned_content.append(cleaned_part)

        sanitized["content"] = cleaned_content
        return sanitized

    def _placeholder_transcript_enabled_for_config(
        self,
        config: Optional[Dict[str, Any]],
    ) -> bool:
        return bool(
            isinstance(config, dict)
            and config.get(_USE_PLACEHOLDER_TRANSCRIPT_KEY, False)
        )

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

    def _segment_from_placeholder_message(
        self,
        message: Dict[str, Any],
    ) -> Optional[List[Dict[str, Any]]]:
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
        state: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        has_placeholder = any(
            self._segment_from_placeholder_message(message) is not None
            for message in messages
            if isinstance(message, dict)
        )
        if not has_placeholder:
            _ = state
            return list(native_messages)

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
        state: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        if not self._use_placeholder_transcript_enabled(state):
            return self._surface_compaction_items_as_placeholders(
                native_messages,
                messages,
            )

        segments: List[tuple[int, int]] = []
        segment_start = 0
        for native_index, item in enumerate(native_messages):
            if not isinstance(item, dict):
                continue
            if item.get("type") not in _COMPACTION_ITEM_TYPES:
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
                if indices
                and any(start <= native_index <= end for native_index in indices)
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
                    native_index
                    for native_index in indices
                    if native_index not in segment_index_set
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

    def _use_placeholder_transcript_enabled(
        self,
        state: Dict[str, Any] | None,
    ) -> bool:
        return bool(
            isinstance(state, dict)
            and state.get(_PLACEHOLDER_TRANSCRIPT_STATE_KEY, False)
        )

    def _build_toggle_placeholder_transcript_result(
        self,
        session: Session,
        native_messages: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides = metadata.get("overrides")
        next_overrides = dict(overrides) if isinstance(overrides, dict) else {}
        currently_enabled = self._placeholder_transcript_enabled_for_config(config)
        next_enabled = not currently_enabled
        next_overrides[_USE_PLACEHOLDER_TRANSCRIPT_KEY] = next_enabled
        return {
            "native_messages": native_messages,
            "session_metadata": {
                "overrides": next_overrides,
            },
            "message": (
                "Collapsed compacted messages."
                if next_enabled
                else "Expanded compacted messages."
            ),
        }

    def _is_system_or_developer_message(self, item: Any) -> bool:
        return (
            isinstance(item, dict)
            and item.get("type") == "message"
            and item.get("role") in {"system", "developer"}
        )

    def _copy_message_with_native_indices(
        self,
        message: Dict[str, Any],
        native_indices: List[int],
    ) -> Optional[Dict[str, Any]]:
        raw_metadata = message.get("metadata")
        metadata = dict(raw_metadata) if isinstance(raw_metadata, dict) else {}
        remaining = [index for index in native_indices if isinstance(index, int)]
        if remaining:
            metadata["native_indices"] = remaining
        else:
            metadata.pop("native_indices", None)
        updated = dict(message)
        if metadata:
            updated["metadata"] = metadata
        else:
            updated.pop("metadata", None)
        return updated

    def _surface_compaction_items_as_placeholders(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        compaction_indices = [
            native_index
            for native_index, item in enumerate(native_messages)
            if isinstance(item, dict) and item.get("type") == "compaction_summary"
        ]
        if not compaction_indices:
            return list(messages)

        working_messages = [
            dict(message) for message in messages if isinstance(message, dict)
        ]
        working_indices: List[List[int]] = []
        for message in working_messages:
            raw_metadata = message.get("metadata")
            metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
            raw_indices = metadata.get("native_indices")
            if isinstance(raw_indices, list):
                working_indices.append(
                    [index for index in raw_indices if isinstance(index, int)]
                )
            else:
                working_indices.append([])

        for compaction_index in compaction_indices:
            for idx, native_index_list in enumerate(working_indices):
                if compaction_index not in native_index_list:
                    continue
                remaining = [
                    value for value in native_index_list if value != compaction_index
                ]
                working_indices[idx] = remaining
                updated = self._copy_message_with_native_indices(
                    working_messages[idx],
                    remaining,
                )
                if updated is not None:
                    working_messages[idx] = updated

            insertion_index = len(working_messages)
            for idx, native_index_list in enumerate(working_indices):
                if native_index_list and min(native_index_list) > compaction_index:
                    insertion_index = idx
                    break

            placeholder = self._placeholder_message_for_segment(
                [native_messages[compaction_index]],
                [compaction_index],
            )
            working_messages.insert(insertion_index, placeholder)
            working_indices.insert(insertion_index, [compaction_index])

        return working_messages

    def _effective_prefix_end(
        self,
        prepared_native_messages: List[Dict[str, Any]],
        effective_messages: List[Dict[str, Any]],
        prefix_native_end: int,
    ) -> int:
        if prefix_native_end <= 0:
            return 0
        if len(effective_messages) == len(prepared_native_messages):
            return min(prefix_native_end, len(effective_messages))
        if len(effective_messages) < len(prepared_native_messages):
            return min(prefix_native_end, len(effective_messages))

        delta = len(effective_messages) - len(prepared_native_messages)
        leading = effective_messages[:delta]
        if leading and all(
            self._is_system_or_developer_message(item) for item in leading
        ):
            return min(prefix_native_end + delta, len(effective_messages))
        return min(prefix_native_end, len(effective_messages))

    def _build_compaction_input(
        self,
        prepared_native_messages: List[Dict[str, Any]],
        prefix_native_end: int,
        request: Dict[str, Any],
        config: Dict[str, Any],
        instructions: Optional[str],
    ) -> Tuple[
        List[Dict[str, Any]],
        Optional[str],
        Optional[Dict[str, Any]],
        List[Dict[str, Any]],
        Optional[Dict[str, Any]],
    ]:
        override = request.get("messages")
        effective_messages = (
            [item for item in override if isinstance(item, dict)]
            if isinstance(override, list)
            else list(prepared_native_messages)
        )
        effective_prefix_end = self._effective_prefix_end(
            prepared_native_messages,
            effective_messages,
            prefix_native_end,
        )
        prefix_native = list(prepared_native_messages[:prefix_native_end])
        prefix_input = list(effective_messages[:effective_prefix_end])
        prepared_input = prepare_input_and_instructions_for_endpoint(
            prefix_input,
            instructions,
            config,
        )
        input_items = [
            self._sanitize_input_item(item)
            for item in prepared_input.input_items
            if isinstance(item, dict)
        ]
        original_first = prefix_native[0] if prefix_native else None
        restore_first = (
            dict(original_first)
            if self._is_system_or_developer_message(original_first)
            else None
        )
        suffix_native = list(prepared_native_messages[prefix_native_end:])
        return (
            input_items,
            prepared_input.instructions,
            restore_first,
            suffix_native,
            prepared_input.stripped_leading_message,
        )

    def _restore_leading_system_or_developer_message(
        self,
        compacted_output: List[Dict[str, Any]],
        restore_first: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not compacted_output or not isinstance(restore_first, dict):
            return compacted_output
        first = compacted_output[0]
        if not self._is_system_or_developer_message(first):
            return compacted_output
        if first.get("role") != restore_first.get("role"):
            return compacted_output
        restored = list(compacted_output)
        restored[0] = dict(restore_first)
        return restored

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
        native_messages: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        prefix_messages = list(session.messages[:end_index])
        if not prefix_messages:
            raise ValueError("compaction prefix cannot be empty")

        native_indices: List[int] = []
        for message in prefix_messages:
            raw_metadata = (
                message.metadata if isinstance(message.metadata, dict) else {}
            )
            raw_indices = raw_metadata.get("native_indices")
            if not isinstance(raw_indices, list) or not raw_indices:
                raise RuntimeError(
                    "visible message range cannot be compacted because native history mapping is missing"
                )
            native_indices.extend(
                index for index in raw_indices if isinstance(index, int)
            )

        if not native_indices:
            raise RuntimeError(
                "visible message range cannot be compacted because native history mapping is empty"
            )

        unique_indices = sorted(set(native_indices))
        if unique_indices[0] != 0:
            raise RuntimeError(
                "compaction range must start at the beginning of native history"
            )
        expected = list(range(unique_indices[-1] + 1))
        if unique_indices != expected:
            missing = sorted(set(expected).difference(unique_indices))
            if missing and isinstance(native_messages, list):
                if all(
                    0 <= missing_index < len(native_messages)
                    and isinstance(native_messages[missing_index], dict)
                    and native_messages[missing_index].get("type")
                    in _COMPACTION_ITEM_TYPES
                    for missing_index in missing
                ):
                    return unique_indices[-1] + 1
            raise RuntimeError(
                "selected visible prefix does not map to a contiguous native prefix for compaction"
            )
        return unique_indices[-1] + 1

    def execute_action(
        self,
        action_id: str,
        session: Session,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        config = state.get("config") if isinstance(state.get("config"), dict) else {}
        if action_id == "toggle_compaction_transcript_mode":
            return self._build_toggle_placeholder_transcript_result(
                session,
                native_messages,
                config,
            )

        if action_id != _SYNC_COMPACTION_ACTION_ID:
            raise ValueError(
                f"Unknown action_id {action_id!r} for OpenAIResponsesNativeCompactionExtension"
            )

        current_native_messages = native_messages
        current_state = state
        if isinstance(context, dict):
            core = context.get("core")
            request_runtime = context.get("request_runtime")
            request_context = context.get("request_context")
            if (
                core is not None
                and isinstance(request_runtime, dict)
                and isinstance(request_context, dict)
            ):
                current_native_messages, current_state = core.initialize_action_request(
                    current_native_messages,
                    current_state,
                    request_runtime,
                    request_context,
                )

        config = (
            current_state.get("config")
            if isinstance(current_state.get("config"), dict)
            else {}
        )
        compaction_config = self._compaction_config(config)
        model = self._resolve_compaction_model(compaction_config)
        timeout = self._coerce_timeout(
            compaction_config.get("timeout", DEFAULT_TIMEOUT)
        )
        end_index = self._resolve_end_index(session, params)
        prefix_native_end = self._resolve_prefix_native_end(
            session,
            end_index,
            current_native_messages,
        )
        request = (
            current_state.get("request")
            if isinstance(current_state.get("request"), dict)
            else {}
        )
        raw_instructions = request.get("instructions")
        instructions_value = (
            raw_instructions.strip()
            if isinstance(raw_instructions, str) and raw_instructions.strip()
            else None
        )
        request_payload = (
            request.get("payload") if isinstance(request.get("payload"), dict) else {}
        )

        (
            input_items,
            instructions_value,
            restore_first,
            suffix_native,
            stripped_leading_message,
        ) = self._build_compaction_input(
            current_native_messages,
            prefix_native_end,
            request,
            compaction_config,
            instructions_value,
        )

        transport: OpenAIResponsesCompactionTransport
        raw_transport = (
            context.get(COMPACTION_TRANSPORT_CONTEXT_KEY)
            if isinstance(context, dict)
            else None
        )
        if raw_transport is not None and callable(
            getattr(raw_transport, "compact", None)
        ):
            configure_transport = getattr(raw_transport, "configure", None)
            if callable(configure_transport):
                configure_transport(compaction_config)
            transport = raw_transport
        else:
            try:
                client = self._build_client(compaction_config)
            except ValueError as exc:
                if effective_auth_mode(
                    config
                ) == "chatgpt" and not self._use_chatgpt_auth_for_compaction(config):
                    raise RuntimeError(
                        "OpenAI Responses native compaction is configured to use the API endpoint, "
                        "but no OpenAI API key is available. Set config.api_key / OPENAI_API_KEY "
                        "or re-enable use_chatgpt_auth_for_compaction."
                    ) from exc
                raise
            transport = SyncOpenAIResponsesCompactionTransport(
                client,
                config=compaction_config,
            )

        try:
            response_obj = OpenAIResponsesNativeCompactionBackend().compact(
                transport,
                model=model,
                input_items=input_items,
                instructions=instructions_value,
                request_options=request_payload,
                timeout=timeout,
            )
        except Exception as exc:
            if effective_auth_mode(compaction_config) == "chatgpt":
                raise RuntimeError(
                    "OpenAI Responses native compaction failed on the ChatGPT endpoint. "
                    "Remote compaction v2 failed: "
                    f"{exc}"
                ) from exc
            raise RuntimeError(f"OpenAI Responses compact failed: {exc}") from exc

        output = response_obj.get("output")
        if not isinstance(output, list):
            raise RuntimeError(
                "OpenAI Responses compact failed: missing output list in response"
            )

        new_native_messages = [
            self._sanitize_compacted_output_item(item)
            for item in output
            if isinstance(item, dict)
        ]
        if not new_native_messages:
            raise RuntimeError(
                "OpenAI Responses compact failed: empty compacted output"
            )
        new_native_messages = self._restore_leading_system_or_developer_message(
            new_native_messages,
            restore_first,
        )
        if stripped_leading_message is not None:
            preserved_first = restore_first or stripped_leading_message
            new_native_messages = [preserved_first, *new_native_messages]

        return {
            "native_messages": [*new_native_messages, *suffix_native],
            "message": (
                f"Compacted visible messages [:{end_index}]"
                if end_index < len(session.messages)
                else "Compacted the full visible history."
            ),
        }
