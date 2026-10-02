"""OpenAI Responses reasoning extension.

Extension responsibilities:
- prepare reasoning request options for RequestOptionsFeature
- attach reasoning metadata to final assistant messages
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin

from .openai_responses_runtime import (
    effective_auth_mode as _effective_auth_mode,
    normalize_auth_mode as _normalize_auth_mode,
)


_REASONING_STATE_KEY = "_openai_responses_reasoning"
_RAW_REASONING_METADATA_KEY = "openai_responses_reasoning"
_RAW_REASONING_CONTEXT_METADATA_KEY = "_openai_responses_reasoning_context"
_REASONING_FALLBACK_TEXT = "Reasoning present but not exposed by model."
_REASONING_EFFORTS = (
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
    "ultra",
)
_UNKNOWN_MODEL_REASONING_EFFORTS = (
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
)
_REASONING_SUMMARIES = ("auto", "concise", "detailed")
_REASONING_INCLUDE_VALUE = "reasoning.encrypted_content"
_REASONING_MODES = ("pro",)
_REASONING_CONTEXTS = ("auto", "current_turn", "all_turns")
_REASONING_CONTEXT_INJECT_VALUES = ("current_turn", "all_turns")

_MODEL_REASONING_EFFORT_PATTERNS: Tuple[
    Tuple[re.Pattern[str], Tuple[str, ...]], ...
] = (
    (re.compile(r"^gpt-5-pro(?:-|$)"), ("high",)),
    (
        re.compile(r"^gpt-6\.1-sol(?:-|$)"),
        ("low", "medium", "high", "xhigh", "max", "ultra"),
    ),
    (
        re.compile(r"^gpt-6-(?:astra|sol)(?:-|$)"),
        ("low", "medium", "high", "xhigh", "max", "ultra"),
    ),
    (
        re.compile(r"^gpt-6-luna(?:-|$)"),
        ("low", "medium", "high", "xhigh", "max"),
    ),
    (
        re.compile(r"^gpt-5\.6-(?:sol|terra)(?:-|$)"),
        ("low", "medium", "high", "xhigh", "max", "ultra"),
    ),
    (
        re.compile(r"^gpt-5\.6-luna(?:-|$)"),
        ("low", "medium", "high", "xhigh", "max"),
    ),
    (
        re.compile(r"^gpt-5\.6(?:-|$)"),
        ("low", "medium", "high", "xhigh", "max", "ultra"),
    ),
    (re.compile(r"^gpt-5\.(?:2|4)(?:-|$)"), ("none", "low", "medium", "high", "xhigh")),
    (re.compile(r"^gpt-5\.1(?:-|$)"), ("none", "low", "medium", "high")),
    (re.compile(r"^gpt-5(?:-|$)"), ("minimal", "low", "medium", "high")),
)

# Effort tuples produced by the GPT-5.6 and GPT-6 family patterns above.
# Used to gate Pro reasoning mode without re-scanning the patterns. Kept in
# sync with the ``_MODEL_REASONING_EFFORT_PATTERNS`` entries that offer the
# ``max``/``ultra`` efforts.
_GPT_5_6_REASONING_EFFORTS = frozenset(
    {
        ("low", "medium", "high", "xhigh", "max", "ultra"),
        ("low", "medium", "high", "xhigh", "max"),
    }
)
_REASONING_CONTEXT_MODEL_PATTERN = re.compile(
    r"^gpt-(?:5\.(?:[6-9]|[1-9][0-9]+)|" r"(?:[6-9]|[1-9][0-9]+))(?:\.[0-9]+)*(?:$|-)"
)


class OpenAIResponsesReasoningExtension(ProviderExtensionPlugin):
    name: str = "openai_responses_reasoning"
    version: str = "0.1.0"
    priority: int = 50

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return ["ext:openai_responses_reasoning"]

    def required_tags(self) -> List[str]:
        return ["openai_responses", "supports_reasoning", "feature:request_options"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "reasoning_effort": {
                "type": "string",
                "required": False,
                "enum": list(_REASONING_EFFORTS),
                "description": "Reasoning effort for supported models.",
            },
            "reasoning_summary": {
                "type": "string",
                "required": False,
                "enum": list(_REASONING_SUMMARIES),
            },
            "reasoning_mode": {
                "type": "string",
                "required": False,
                "enum": list(_REASONING_MODES),
                "description": (
                    "Reasoning mode for supported models. 'pro' enables Pro "
                    "mode (GPT-5.6 family only). Absence means standard mode."
                ),
            },
            "reasoning_context": {
                "type": "string",
                "required": False,
                "enum": list(_REASONING_CONTEXTS),
                "description": (
                    "Reasoning context for supported models. 'current_turn' "
                    "makes reasoning from the active turn available without "
                    "rendering earlier-turn reasoning. 'all_turns' renders "
                    "compatible reasoning items from earlier turns into the "
                    "next sample (GPT-5.6 and later numeric GPT families). "
                    "'auto' and absence "
                    "both normalize to omission (the API default applies)."
                ),
            },
            "show_reasoning_context_footer": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": (
                    "Show the effective reasoning context in assistant message footers."
                ),
            },
        }

    def _resolve_model_id(
        self,
        config: Optional[Dict[str, Any]],
        models: Optional[List[Dict[str, Any]]],
    ) -> str:
        model = None
        if isinstance(config, dict):
            raw_model = config.get("model")
            if isinstance(raw_model, str) and raw_model.strip():
                model = raw_model.strip()

        if model is None and isinstance(models, list):
            for entry in models:
                if not isinstance(entry, dict):
                    continue
                raw_id = entry.get("id")
                if isinstance(raw_id, str) and raw_id.strip():
                    model = raw_id.strip()
                    break

        return model or ""

    def _supported_reasoning_efforts_for_model(self, model: str) -> Tuple[str, ...]:
        normalized = model.strip().lower()
        for pattern, efforts in _MODEL_REASONING_EFFORT_PATTERNS:
            if pattern.search(normalized):
                return efforts
        return _UNKNOWN_MODEL_REASONING_EFFORTS

    def _model_supports_pro_reasoning(self, model: str) -> bool:
        return (
            self._supported_reasoning_efforts_for_model(model)
            in _GPT_5_6_REASONING_EFFORTS
        )

    def _model_supports_reasoning_context(self, model: str) -> bool:
        # Model discovery does not currently publish a dedicated
        # reasoning-context capability. GPT-5.6 and GPT-6 Astra establish the
        # persisted-reasoning contract, so carry that behavior forward across
        # later numeric GPT families. Pro mode and effort options retain their
        # separate, narrower model rules.
        return (
            _REASONING_CONTEXT_MODEL_PATTERN.search(model.strip().lower()) is not None
        )

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        if tags is not None and "supports_reasoning" not in tags:
            return []

        model_id = self._resolve_model_id(config, models)
        supported_efforts = self._supported_reasoning_efforts_for_model(model_id)
        effort_options = [
            {"value": value, "label": value} for value in supported_efforts
        ]

        elements: List[Dict[str, Any]] = [
            {
                "ui_type": "config",
                "type": "select",
                "key": "reasoning_effort",
                "label": "Reasoning Effort",
                "icon": "sliders",
                "options": effort_options,
                "rich_ui": {
                    "kind": "dropdown",
                    "label": "Reasoning effort",
                    "show_label": False,
                    "show_icon": False,
                    "options": effort_options,
                    "placements": ["composer"],
                    "default_pinned": True,
                },
            },
            {
                "type": "select",
                "key": "reasoning_summary",
                "label": "Reasoning Summary",
                "options": [
                    {"value": value, "label": value} for value in _REASONING_SUMMARIES
                ],
            },
        ]

        if self._model_supports_pro_reasoning(model_id) and (
            not isinstance(config, dict)
            or _normalize_auth_mode(config.get("auth_mode")) != "chatgpt"
        ):
            elements.append(
                {
                    "type": "select",
                    "key": "reasoning_mode",
                    "label": "Reasoning Mode",
                    "options": [
                        {"value": value, "label": value} for value in _REASONING_MODES
                    ],
                }
            )

        if self._model_supports_reasoning_context(model_id):
            elements.append(
                {
                    "type": "select",
                    "key": "reasoning_context",
                    "label": "Reasoning retention",
                    "options": [
                        {"value": "auto", "label": "Auto"},
                        {"value": "current_turn", "label": "Current turn only"},
                        {"value": "all_turns", "label": "All turns"},
                    ],
                }
            )

        # Message footer for the effective reasoning context. Unconditional
        # (not model-gated) because the ``condition`` handles per-message
        # visibility: the footer only renders when
        # ``metadata.openai_responses_reasoning.context`` is present, so it
        # does not fabricate a value for models or responses that do not
        # report an effective context. Mirrors the usage extension's
        # ``message_footer`` pattern for ``usage_service_tier``.
        if (
            not isinstance(config, dict)
            or config.get("show_reasoning_context_footer") is not False
        ):
            elements.append(
                {
                    "ui_type": "message_footer",
                    "data": "metadata.openai_responses_reasoning.context",
                    "template": "context: {{data}}",
                    "condition": {
                        "path": "metadata.openai_responses_reasoning.context",
                        "exists": True,
                    },
                }
            )

        return elements

    def _normalize_reasoning_config(
        self, config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        reasoning: Dict[str, Any] = {}
        model = self._resolve_model_id(config, None)
        supported_efforts = self._supported_reasoning_efforts_for_model(model)

        effort = config.get("reasoning_effort")
        if isinstance(effort, str) and effort in supported_efforts:
            reasoning["effort"] = effort

        summary = config.get("reasoning_summary")
        if isinstance(summary, str) and summary in _REASONING_SUMMARIES:
            reasoning["summary"] = summary

        mode = config.get("reasoning_mode")
        if (
            isinstance(mode, str)
            and mode in _REASONING_MODES
            and self._model_supports_pro_reasoning(model)
            and _effective_auth_mode(config) != "chatgpt"
        ):
            reasoning["mode"] = mode

        context = config.get("reasoning_context")
        if (
            isinstance(context, str)
            and context in _REASONING_CONTEXT_INJECT_VALUES
            and self._model_supports_reasoning_context(model)
        ):
            reasoning["context"] = context
        # ``auto`` normalizes to omission (do not inject ``context``). This
        # matches the official semantics ("omitting reasoning.context has the
        # same effect as auto") and the existing ``reasoning_mode`` precedent
        # (omit ``standard``, the API default). Both ``absent`` and ``auto``
        # produce the same outbound request: no ``context`` key. An invalid
        # value or a non-GPT-5.6 model is silently dropped (no error, no
        # injection), matching the existing silent-drop behavior for
        # unsupported ``reasoning_effort`` and ``reasoning_mode``.

        return reasoning or None

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        reasoning = self._normalize_reasoning_config(config)
        if reasoning is None:
            return state
        return {**state, _REASONING_STATE_KEY: reasoning}

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

    def _extract_reasoning_metadata(
        self, native_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        reasoning_items: List[Dict[str, Any]] = []
        reasoning_summary: List[Dict[str, Any]] = []
        encrypted_content: List[Any] = []
        reasoning_fragments: List[str] = []
        summary_fragments: List[str] = []
        effective_context: Optional[str] = None

        for native_item in native_messages:
            if not isinstance(native_item, dict):
                continue

            # Extract the effective reasoning context from the first relevant
            # native item's internal metadata. The provider attaches the same
            # ``_metadata._openai_responses_reasoning_context`` to every output
            # item of a response, so reading from any item (reasoning or
            # otherwise) is sufficient. This handles responses that report
            # an effective context but produce no reasoning items.
            if effective_context is None:
                internal_md = native_item.get("_metadata")
                if isinstance(internal_md, dict):
                    context_value = internal_md.get(_RAW_REASONING_CONTEXT_METADATA_KEY)
                    if isinstance(context_value, str) and context_value:
                        effective_context = context_value

            if native_item.get("type") != "reasoning":
                continue

            cleaned_item = {k: v for k, v in native_item.items() if k != "_metadata"}
            reasoning_items.append(cleaned_item)

            summary = native_item.get("summary")
            if isinstance(summary, list) and summary:
                reasoning_summary.extend(
                    [entry for entry in summary if isinstance(entry, dict)]
                )
                summary_text = self._summary_text_from_entries(summary)
                if summary_text:
                    summary_fragments.append(summary_text)

            content_text = self._reasoning_text_from_content(native_item.get("content"))
            if content_text:
                reasoning_fragments.append(content_text)

            encrypted = native_item.get("encrypted_content")
            if encrypted is not None:
                encrypted_content.append(encrypted)

        if not reasoning_items and effective_context is None:
            return {}

        reasoning_summary_text = "\n".join(
            part for part in summary_fragments if part
        ).strip()
        reasoning_content_text = "\n".join(
            part for part in reasoning_fragments if part
        ).strip()
        reasoning_text = (
            reasoning_summary_text or reasoning_content_text or _REASONING_FALLBACK_TEXT
        )

        raw_metadata: Dict[str, Any] = {"items": reasoning_items}
        if reasoning_summary:
            raw_metadata["summary"] = reasoning_summary
        if reasoning_summary_text:
            raw_metadata["summary_text"] = reasoning_summary_text
        if reasoning_content_text:
            raw_metadata["content_text"] = reasoning_content_text
        if encrypted_content:
            raw_metadata["encrypted_content"] = encrypted_content
        if effective_context is not None:
            raw_metadata["context"] = effective_context

        metadata: Dict[str, Any] = {_RAW_REASONING_METADATA_KEY: raw_metadata}
        if reasoning_items and reasoning_text:
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
            elif (
                target_key not in merged_raw and isinstance(incoming, list) and incoming
            ):
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
                elif (
                    existing_clean == incoming_clean or incoming_clean in existing_clean
                ):
                    merged_raw[target_key] = existing_clean
                elif existing_clean in incoming_clean:
                    merged_raw[target_key] = incoming_clean
                else:
                    merged_raw[target_key] = f"{existing_clean}\n{incoming_clean}"
            elif (
                target_key not in merged_raw and isinstance(incoming, str) and incoming
            ):
                merged_raw[target_key] = incoming.strip()

        # Effective reasoning context: latest non-empty string wins. All
        # output items from one response share the same effective context, so
        # across response segments in a tool-loop the latest non-empty value
        # reflects the most recent response's effective mode.
        incoming_context = incoming_raw.get("context")
        if isinstance(incoming_context, str) and incoming_context.strip():
            merged_raw["context"] = incoming_context.strip()
        elif "context" not in merged_raw and isinstance(incoming_context, str):
            cleaned = incoming_context.strip()
            if cleaned:
                merged_raw["context"] = cleaned

        if merged_raw:
            merged[_RAW_REASONING_METADATA_KEY] = merged_raw

        reasoning_value = extra.get("reasoning")
        if isinstance(reasoning_value, str) and reasoning_value.strip():
            merged["reasoning"] = reasoning_value.strip()
        elif "reasoning" not in merged and isinstance(
            merged_raw.get("summary_text"), str
        ):
            summary_text = merged_raw["summary_text"].strip()
            if summary_text:
                merged["reasoning"] = summary_text
        elif "reasoning" not in merged and isinstance(
            merged_raw.get("content_text"), str
        ):
            content_text = merged_raw["content_text"].strip()
            if content_text:
                merged["reasoning"] = content_text

        return merged

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

            metadata = (
                message.get("metadata")
                if isinstance(message.get("metadata"), dict)
                else {}
            )
            native_indices = (
                metadata.get("native_indices") if isinstance(metadata, dict) else None
            )
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
                    "metadata": self._merge_reasoning_metadata(
                        metadata, reasoning_metadata
                    ),
                }
            )

        return out

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        config = state.get("config")
        config_dict = dict(config) if isinstance(config, dict) else {}
        request_options = config_dict.get("request_options")
        merged_request_options = (
            dict(request_options) if isinstance(request_options, dict) else {}
        )

        include_values: List[str] = []
        raw_include = merged_request_options.get("include")
        if isinstance(raw_include, list):
            include_values = [
                item for item in raw_include if isinstance(item, str) and item
            ]
        elif isinstance(raw_include, tuple):
            include_values = [
                item for item in raw_include if isinstance(item, str) and item
            ]
        if _REASONING_INCLUDE_VALUE not in include_values:
            include_values.append(_REASONING_INCLUDE_VALUE)
        merged_request_options["include"] = include_values

        reasoning = state.get(_REASONING_STATE_KEY)
        if not isinstance(reasoning, dict) or not reasoning:
            return list(native_messages), {
                **state,
                "config": {**config_dict, "request_options": merged_request_options},
            }

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
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        _ = native_chunk
        return (
            list(partial_messages),
            list(final_messages),
            list(native_messages),
            state,
        )

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return list(final_messages), list(native_messages), state
