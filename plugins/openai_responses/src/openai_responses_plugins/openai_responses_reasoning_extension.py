"""OpenAI Responses reasoning extension.

Extension responsibilities:
- prepare reasoning request options for RequestOptionsFeature
- accumulate streaming reasoning deltas/items
- attach reasoning metadata to final assistant messages
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


_REASONING_STATE_KEY = "_openai_responses_reasoning"
_STREAM_STATE_KEY = "_openai_responses_reasoning_stream"
_RAW_REASONING_METADATA_KEY = "openai_responses_reasoning"
_REASONING_FALLBACK_TEXT = "Reasoning present but not exposed by model."
_REASONING_EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh")
_REASONING_SUMMARIES = ("auto", "concise", "detailed")


class OpenAIResponsesReasoningExtension(ProviderExtensionPlugin):
    name: str = "openai_responses_reasoning"
    version: str = "0.1.0"
    priority: int = 50

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        return ["ext:openai_responses_reasoning"]

    def required_tags(self) -> List[str]:
        return ["openai_responses", "supports_reasoning", "feature:request_options"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enable_reasoning": {
                "type": "boolean",
                "required": False,
                "description": "Enable model reasoning when supported.",
            },
            "reasoning_effort": {
                "type": "string",
                "required": False,
                "enum": list(_REASONING_EFFORTS),
            },
            "reasoning_summary": {
                "type": "string",
                "required": False,
                "enum": list(_REASONING_SUMMARIES),
            },
            "reasoning_max_tokens": {
                "type": "number",
                "required": False,
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = models
        if tags is not None and "supports_reasoning" not in tags:
            return []

        return [
            {
                "type": "checkbox",
                "key": "enable_reasoning",
                "label": "Enable Reasoning",
            },
            {
                "type": "select",
                "key": "reasoning_effort",
                "label": "Reasoning Effort",
                "options": [{"value": value, "label": value} for value in _REASONING_EFFORTS],
            },
            {
                "type": "select",
                "key": "reasoning_summary",
                "label": "Reasoning Summary",
                "options": [{"value": value, "label": value} for value in _REASONING_SUMMARIES],
            },
            {
                "type": "number",
                "key": "reasoning_max_tokens",
                "label": "Reasoning Max Tokens",
            },
        ]

    def _empty_stream_state(self) -> Dict[str, Any]:
        return {
            "reasoning": "",
            "reasoning_items": [],
            "reasoning_summary": [],
            "reasoning_summary_text": "",
            "reasoning_content_text": "",
            "reasoning_encrypted_content": [],
        }

    def _normalize_reasoning_config(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        reasoning: Dict[str, Any] = {}

        enabled = config.get("enable_reasoning") if "enable_reasoning" in config else None

        effort = config.get("reasoning_effort")
        if isinstance(effort, str) and effort in _REASONING_EFFORTS:
            reasoning["effort"] = effort
        elif enabled is True:
            reasoning["effort"] = "minimal"
        elif enabled is False:
            reasoning["effort"] = "none"

        summary = config.get("reasoning_summary")
        if isinstance(summary, str) and summary in _REASONING_SUMMARIES:
            reasoning["summary"] = summary

        max_tokens = config.get("reasoning_max_tokens")
        if isinstance(max_tokens, (int, float)):
            reasoning["max_tokens"] = int(max_tokens)

        return reasoning or None

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        next_state = {**state, _STREAM_STATE_KEY: self._empty_stream_state()}
        reasoning = self._normalize_reasoning_config(config)
        if reasoning is None:
            return next_state
        return {**next_state, _REASONING_STATE_KEY: reasoning}

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        _ = messages
        return list(native_messages)

    def _summary_text_from_entries(self, summary: Any) -> str:
        if not isinstance(summary, list):
            return ""
        fragments: List[str] = []
        for item in summary:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str) and text:
                fragments.append(text)
        return "\n".join(fragments).strip()

    def _reasoning_text_from_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content.strip()
        if not isinstance(content, list):
            return ""

        fragments: List[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str) and text:
                fragments.append(text)
        return "\n".join(fragments).strip()

    def _extract_reasoning_metadata(self, native_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        reasoning_items: List[Dict[str, Any]] = []
        reasoning_summary: List[Dict[str, Any]] = []
        encrypted_content: List[Any] = []
        reasoning_fragments: List[str] = []
        summary_fragments: List[str] = []

        for native_item in native_messages:
            if not isinstance(native_item, dict) or native_item.get("type") != "reasoning":
                continue

            cleaned_item = {k: v for k, v in native_item.items() if k != "_metadata"}
            reasoning_items.append(cleaned_item)

            summary = native_item.get("summary")
            if isinstance(summary, list) and summary:
                reasoning_summary.extend([entry for entry in summary if isinstance(entry, dict)])
                summary_text = self._summary_text_from_entries(summary)
                if summary_text:
                    summary_fragments.append(summary_text)

            content_text = self._reasoning_text_from_content(native_item.get("content"))
            if content_text:
                reasoning_fragments.append(content_text)

            encrypted = native_item.get("encrypted_content")
            if encrypted is not None:
                encrypted_content.append(encrypted)

        if not reasoning_items:
            return {}

        reasoning_summary_text = "\n".join(part for part in summary_fragments if part).strip()
        reasoning_content_text = "\n".join(
            part for part in reasoning_fragments if part
        ).strip()
        reasoning_text = reasoning_summary_text or reasoning_content_text or _REASONING_FALLBACK_TEXT

        raw_metadata: Dict[str, Any] = {"items": reasoning_items}
        if reasoning_summary:
            raw_metadata["summary"] = reasoning_summary
        if reasoning_summary_text:
            raw_metadata["summary_text"] = reasoning_summary_text
        if reasoning_content_text:
            raw_metadata["content_text"] = reasoning_content_text
        if encrypted_content:
            raw_metadata["encrypted_content"] = encrypted_content

        metadata: Dict[str, Any] = {_RAW_REASONING_METADATA_KEY: raw_metadata}
        if reasoning_text:
            metadata["reasoning"] = reasoning_text
        return metadata

    def _merge_reasoning_metadata(
        self,
        base: Dict[str, Any],
        extra: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not extra:
            return dict(base)

        merged = dict(base)
        existing_raw = merged.get(_RAW_REASONING_METADATA_KEY)
        merged_raw = dict(existing_raw) if isinstance(existing_raw, dict) else {}
        incoming_raw = extra.get(_RAW_REASONING_METADATA_KEY)
        incoming_raw = incoming_raw if isinstance(incoming_raw, dict) else {}

        for source_key, target_key in (
            ("items", "items"),
            ("summary", "summary"),
            ("encrypted_content", "encrypted_content"),
        ):
            existing = merged_raw.get(target_key)
            incoming = incoming_raw.get(source_key)
            if isinstance(existing, list) and isinstance(incoming, list) and incoming:
                deduped = list(existing)
                for item in incoming:
                    if item not in deduped:
                        deduped.append(item)
                merged_raw[target_key] = deduped
            elif target_key not in merged_raw and isinstance(incoming, list) and incoming:
                merged_raw[target_key] = list(incoming)

        for source_key, target_key in (
            ("summary_text", "summary_text"),
            ("content_text", "content_text"),
        ):
            existing = merged_raw.get(target_key)
            incoming = incoming_raw.get(source_key)
            if isinstance(existing, str) and isinstance(incoming, str) and incoming:
                existing_clean = existing.strip()
                incoming_clean = incoming.strip()
                if not existing_clean:
                    merged_raw[target_key] = incoming_clean
                elif not incoming_clean:
                    merged_raw[target_key] = existing_clean
                elif existing_clean == incoming_clean or incoming_clean in existing_clean:
                    merged_raw[target_key] = existing_clean
                elif existing_clean in incoming_clean:
                    merged_raw[target_key] = incoming_clean
                else:
                    merged_raw[target_key] = f"{existing_clean}\n{incoming_clean}"
            elif target_key not in merged_raw and isinstance(incoming, str) and incoming:
                merged_raw[target_key] = incoming.strip()

        if merged_raw:
            merged[_RAW_REASONING_METADATA_KEY] = merged_raw

        reasoning_value = extra.get("reasoning")
        if isinstance(reasoning_value, str) and reasoning_value.strip():
            merged["reasoning"] = reasoning_value.strip()
        elif "reasoning" not in merged and isinstance(merged_raw.get("summary_text"), str):
            summary_text = merged_raw["summary_text"].strip()
            if summary_text:
                merged["reasoning"] = summary_text
        elif "reasoning" not in merged and isinstance(merged_raw.get("content_text"), str):
            content_text = merged_raw["content_text"].strip()
            if content_text:
                merged["reasoning"] = content_text

        return merged

    def _current_stream_metadata(self, stream_state: Dict[str, Any]) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {}

        reasoning = stream_state.get("reasoning")
        if isinstance(reasoning, str) and reasoning:
            metadata["reasoning"] = reasoning

        raw_metadata: Dict[str, Any] = {}
        summary_text = stream_state.get("reasoning_summary_text")
        if isinstance(summary_text, str) and summary_text:
            raw_metadata["summary_text"] = summary_text
            metadata.setdefault("reasoning", summary_text)

        content_text = stream_state.get("reasoning_content_text")
        if isinstance(content_text, str) and content_text:
            raw_metadata["content_text"] = content_text

        reasoning_items = stream_state.get("reasoning_items")
        if isinstance(reasoning_items, list) and reasoning_items:
            raw_metadata["items"] = list(reasoning_items)

        reasoning_summary = stream_state.get("reasoning_summary")
        if isinstance(reasoning_summary, list) and reasoning_summary:
            raw_metadata["summary"] = list(reasoning_summary)

        encrypted = stream_state.get("reasoning_encrypted_content")
        if isinstance(encrypted, list) and encrypted:
            raw_metadata["encrypted_content"] = list(encrypted)

        if raw_metadata:
            metadata[_RAW_REASONING_METADATA_KEY] = raw_metadata

        return metadata

    def _patch_partial_messages(
        self,
        partial_messages: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        if not partial_messages or not metadata:
            return list(partial_messages)

        last = partial_messages[-1]
        existing_metadata = last.get("metadata") if isinstance(last.get("metadata"), dict) else {}
        patched_last = {
            **last,
            "metadata": {**existing_metadata, **metadata},
            "_metadata": {
                **(last.get("_metadata") if isinstance(last.get("_metadata"), dict) else {}),
                **metadata,
            },
        }
        return [*partial_messages[:-1], patched_last]

    def _patch_final_native_messages(
        self,
        final_messages: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        if not final_messages or not metadata:
            return list(final_messages)

        patched: List[Dict[str, Any]] = []
        for native_item in final_messages:
            if not isinstance(native_item, dict):
                patched.append(native_item)
                continue
            if native_item.get("type") != "message" or native_item.get("role") != "assistant":
                patched.append(native_item)
                continue

            existing_metadata = (
                native_item.get("_metadata") if isinstance(native_item.get("_metadata"), dict) else {}
            )
            patched.append(
                {
                    **native_item,
                    "_metadata": self._merge_reasoning_metadata(existing_metadata, metadata),
                }
            )

        return patched

    def _append_stream_text(self, stream_state: Dict[str, Any], key: str, text: str) -> Dict[str, Any]:
        if not text:
            return stream_state
        current = stream_state.get(key)
        current_text = current if isinstance(current, str) else ""
        return {**stream_state, key: f"{current_text}{text}"}

    def _update_stream_state_from_reasoning_item(
        self,
        stream_state: Dict[str, Any],
        item: Dict[str, Any],
    ) -> Dict[str, Any]:
        metadata = self._extract_reasoning_metadata([item])
        if not metadata:
            return stream_state
        return self._merge_reasoning_metadata(stream_state, metadata)

    def _update_stream_state_from_event(
        self,
        native_chunk: Dict[str, Any],
        stream_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        event_type = native_chunk.get("type")
        if not isinstance(event_type, str):
            return stream_state

        if event_type in (
            "response.reasoning_summary_text.delta",
            "response.reasoning_summary.delta",
            "response.reasoning.delta",
        ):
            delta = native_chunk.get("delta")
            text = delta if isinstance(delta, str) else ""
            if not text and isinstance(delta, dict):
                raw_text = delta.get("text")
                text = raw_text if isinstance(raw_text, str) else ""

            updated = stream_state
            if event_type != "response.reasoning.delta":
                updated = self._append_stream_text(updated, "reasoning_summary_text", text)
            else:
                updated = self._append_stream_text(updated, "reasoning_content_text", text)

            summary_text = updated.get("reasoning_summary_text")
            if isinstance(summary_text, str) and summary_text.strip():
                updated["reasoning"] = summary_text
            else:
                updated = self._append_stream_text(updated, "reasoning", text)
            return updated

        if event_type in ("response.output_item.added", "response.output_item.done"):
            item = native_chunk.get("item")
            if isinstance(item, dict) and item.get("type") == "reasoning":
                return self._update_stream_state_from_reasoning_item(stream_state, item)

        return stream_state

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []

        for message in messages:
            if not isinstance(message, dict) or message.get("role") != "assistant":
                out.append(message)
                continue

            metadata = message.get("metadata") if isinstance(message.get("metadata"), dict) else {}
            native_indices = metadata.get("native_indices") if isinstance(metadata, dict) else None
            if not isinstance(native_indices, list):
                out.append(message)
                continue

            relevant_native = [
                native_messages[index]
                for index in native_indices
                if isinstance(index, int) and 0 <= index < len(native_messages)
            ]
            reasoning_metadata = self._extract_reasoning_metadata(relevant_native)
            if not reasoning_metadata:
                out.append(message)
                continue

            out.append(
                {
                    **message,
                    "metadata": self._merge_reasoning_metadata(metadata, reasoning_metadata),
                }
            )

        return out

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        reasoning = state.get(_REASONING_STATE_KEY)
        if not isinstance(reasoning, dict) or not reasoning:
            return list(native_messages), state

        config = state.get("config")
        config_dict = dict(config) if isinstance(config, dict) else {}
        request_options = config_dict.get("request_options")
        merged_request_options = dict(request_options) if isinstance(request_options, dict) else {}

        existing_reasoning = merged_request_options.get("reasoning")
        merged_request_options["reasoning"] = {
            **(existing_reasoning if isinstance(existing_reasoning, dict) else {}),
            **reasoning,
        }

        return list(native_messages), {
            **state,
            "config": {**config_dict, "request_options": merged_request_options},
        }

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        stream_state = state.get(_STREAM_STATE_KEY)
        current_stream_state = dict(stream_state) if isinstance(stream_state, dict) else self._empty_stream_state()

        if isinstance(native_chunk, dict):
            current_stream_state = self._update_stream_state_from_event(native_chunk, current_stream_state)

        partial_metadata = self._current_stream_metadata(current_stream_state)
        new_partials = self._patch_partial_messages(partial_messages, partial_metadata)

        final_reasoning_metadata = self._merge_reasoning_metadata(
            partial_metadata,
            self._extract_reasoning_metadata(final_messages),
        )
        new_finals = self._patch_final_native_messages(final_messages, final_reasoning_metadata)

        return new_partials, new_finals, list(native_messages), {
            **state,
            _STREAM_STATE_KEY: current_stream_state,
        }

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        stream_state = state.get(_STREAM_STATE_KEY)
        current_stream_state = dict(stream_state) if isinstance(stream_state, dict) else self._empty_stream_state()

        final_reasoning_metadata = self._merge_reasoning_metadata(
            self._current_stream_metadata(current_stream_state),
            self._extract_reasoning_metadata(final_messages),
        )
        patched_finals = self._patch_final_native_messages(final_messages, final_reasoning_metadata)
        return patched_finals, list(native_messages), state