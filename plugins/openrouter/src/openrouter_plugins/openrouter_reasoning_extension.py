"""OpenRouter reasoning extension for OpenRouter provider.

Adds reasoning/thinking support to OpenRouter models that support it.
Extracts reasoning content from responses and exposes it in metadata.
Properly handles reasoning_details for preservation across tool calling rounds.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin

from .model_capabilities import (
    REASONING_EFFORT_ALL_VALUES,
    get_reasoning_effort_options_and_default,
)

class OpenRouterReasoningExtension(ProviderExtensionPlugin):
    """Provider extension to enable OpenRouter reasoning.

    Responsibilities:
    - Add "reasoning_effort" or "include_reasoning" to request payload when enabled.
    - Accumulate reasoning text from streaming chunks.
    - Attach reasoning into metadata on final assistant messages.
    - Preserve and accumulate reasoning_details for tool calling continuity.
    - Handle provider-specific reasoning_details formats (OpenAI, Anthropic, Gemini, xAI).
    """

    name: str = "openrouter_reasoning"
    version: str = "0.2.0"
    priority: int = 50  # Run before RequestOptionsFeature

    def get_tags(
            self,
            config: Dict[str, Any],
            models: List[Dict[str, Any]],
    ) -> List[str]:
        """Identify this extension for dependency resolution."""
        return ["ext:openrouter_reasoning"]

    def required_tags(self) -> List[str]:
        """Require OpenRouter provider and reasoning support."""
        return ["openrouter", "supports_reasoning", "feature:request_options"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "reasoning_effort": {
                "type": "string",
                "required": False,
                "enum": list(REASONING_EFFORT_ALL_VALUES),
                "description": "Control reasoning depth (model-specific)",
            },
            "enable_reasoning": {
                "type": "boolean",
                "required": False,
                "description": "Enable reasoning/thinking for models that support it",
            },
            "reasoning_max_tokens": {
                "type": "boolean",
                "required": False,
                "description": "Specific token limit (Anthropic-style)",
            }
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        if tags is not None and "supports_reasoning" not in tags:
            return []
        selected_id = config.get("model") if isinstance(config, dict) else None
        options, default = get_reasoning_effort_options_and_default(selected_id)

        ui_elements: List[Dict[str, Any]] = [
            {
                "ui_type": "config",
                "type": "checkbox",
                "key": "enable_reasoning",
                "label": "Enable Reasoning",
            }
        ]
        if config and config.get("enable_reasoning") is False:
            return ui_elements
        if tags is not None and "supports_reasoning_effort" in tags and options:
            ui_elements.append({
                "type": "select",
                "key": "reasoning_effort",
                "label": "Reasoning Effort",
                "options": options,
                "default": default,
            })
        return ui_elements

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if config.get("enable_reasoning") is False:
            return state

        reasoning_config = {
            "reasoning": {}
        }

        selected_model = config.get("model")
        _options, default = get_reasoning_effort_options_and_default(selected_model)

        if "enable_reasoning" in config:
            reasoning_config["reasoning"]["enabled"] = config["enable_reasoning"]
        if "reasoning_effort" in config or default:
            reasoning_config["reasoning"]["effort"] = config.get("reasoning_effort", default)
        if "reasoning_max_tokens" in config:
            reasoning_config["reasoning"]["max_tokens"] = config["reasoning_max_tokens"]

        if not reasoning_config["reasoning"]:
            return state
    
        return {
            **state,
            "openrouter_reasoning": reasoning_config,
        }

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Return native messages unchanged.

        Reasoning and reasoning_details are treated as opaque provider-native
        metadata. This extension does not synthesize, strip, or otherwise
        transform these fields; they are preserved exactly as returned by the
        provider and carried across turns via AgentCore's native history
        retention.
        """
        return native_messages


    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract reasoning and reasoning_details into metadata.

        reasoning_details are preserved unchanged for API compatibility.
        """
        if len(messages) != len(native_messages):
            return messages

        enhanced_messages = []
        for message, native_msg in zip(messages, native_messages):
            metadata = dict(message.get("metadata", {}))

            # Extract reasoning text if present
            if "reasoning" in native_msg:
                metadata["reasoning"] = native_msg["reasoning"]

            # Preserve reasoning_details unchanged if present
            if "reasoning_details" in native_msg:
                metadata["reasoning_details"] = native_msg["reasoning_details"]

            enhanced_messages.append({**message, "metadata": metadata})

        return enhanced_messages

    def initialize_request(
            self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        reasoning_config = state.get("openrouter_reasoning")
        if not reasoning_config:
            return native_messages, state

        config = state.get("config", {})
        request_options = dict(config.get("request_options", {}))
        request_options["reasoning"] = {
            **request_options.get("reasoning", {}),
            **reasoning_config["reasoning"]
        }

        new_state = {
            **state,
            "config": {
                **config,
                "request_options": request_options,
            },
        }
        return native_messages, new_state

    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract a provider-native delta dictionary from a streaming chunk.
        Return the first choice if present.
        """
        if "choices" in native_chunk and native_chunk["choices"]:
            return native_chunk["choices"][0]

        return {}

    def _accumulate_reasoning_details(
        self,
        current_details: Optional[List[Dict[str, Any]]],
        delta_details: Optional[List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Accumulate reasoning_details arrays across streaming chunks.

        Handles all provider formats uniformly:
        - Metadata fields (type, format, index, id): use latest value
        - Content fields (text, data, summary, signature): accumulate by
          concatenation, with a special case for Gemini encrypted blobs.

        This ensures that any content field that arrives incrementally across
        multiple chunks is properly accumulated, not overridden.
        """
        if not delta_details:
            return current_details or []

        if not current_details:
            return list(delta_details)

        accumulated = list(current_details)

        # Define which fields should be accumulated vs overridden
        CONTENT_FIELDS = {"text", "data", "summary", "signature"}
        METADATA_FIELDS = {"type", "format", "index", "id"}

        for delta_detail in delta_details:
            detail_type = delta_detail.get("type")
            detail_index = delta_detail.get("index", 0)
            detail_id = delta_detail.get("id")

            # Find matching detail in accumulated list
            matching_idx = None

            if detail_id:
                # If the incoming delta has an id, ONLY match on that id.
                # Do not fall back to (index, type), because providers can reuse
                # index values across different ids (e.g. multiple encrypted
                # blobs), and merging those corrupts the data.
                for idx, acc_detail in enumerate(accumulated):
                    if acc_detail.get("id") == detail_id:
                        matching_idx = idx
                        break

                # If we didn't find a match by id, we still allow a single
                # upgrade path: match a prior entry that has no id yet but
                # shares (type, index). This supports providers that emit id
                # later in the stream.
                if matching_idx is None:
                    for idx, acc_detail in enumerate(accumulated):
                        if (
                            acc_detail.get("id") is None
                            and acc_detail.get("index") == detail_index
                            and acc_detail.get("type") == detail_type
                        ):
                            matching_idx = idx
                            break
            else:
                # No id available: best-effort match by (type, index).
                for idx, acc_detail in enumerate(accumulated):
                    if (
                        acc_detail.get("index") == detail_index
                        and acc_detail.get("type") == detail_type
                    ):
                        matching_idx = idx
                        break

            if matching_idx is not None:
                # Update existing detail
                acc_detail = dict(accumulated[matching_idx])

                # Accumulate content fields, override metadata fields
                for key, value in delta_detail.items():
                    if key in CONTENT_FIELDS:
                        # Accumulate content fields
                        if isinstance(value, str):
                            acc_detail[key] = (acc_detail.get(key, "") or "") + value
                        else:
                            acc_detail[key] = value
                    elif key in METADATA_FIELDS:
                        # Override metadata fields with latest value
                        acc_detail[key] = value
                    else:
                        # Unknown field - accumulate to be safe
                        if isinstance(value, str):
                            acc_detail[key] = (acc_detail.get(key, "") or "") + value
                        else:
                            acc_detail[key] = value

                accumulated[matching_idx] = acc_detail
            else:
                # New detail - append to list
                accumulated.append(dict(delta_detail))

        return accumulated


    def process_delta(
        self,
        delta: Dict[str, Any],
        current_partial: Optional[Dict[str, Any]] = None,
        accumulated: Optional[Dict[str, Any]] = None,
    ):
        """
        Enhance the partial or final message with reasoning information from delta.
        Accumulates reasoning_details correctly for all supported providers.
        Returns (partial_message, accumulated).
        """

        match delta, accumulated:
            case ({"delta": {"reasoning": reasoning, "reasoning_details": list(reasoning_details)}}, dict(acc)) | ({"message": {"reasoning": reasoning, "reasoning_details": list(reasoning_details)}}, dict(acc)):
                return current_partial, {
                    **acc,
                    "reasoning": acc.get("reasoning", "") + (reasoning or ""),
                    "reasoning_details": self._accumulate_reasoning_details(
                        acc.get("reasoning_details", []), reasoning_details
                    )
                }
            case ({"delta": {"reasoning": reasoning}}, dict(acc)) | ({"message": {"reasoning": reasoning}}, dict(acc)):
                return current_partial, {
                    **acc,
                    "reasoning": acc.get("reasoning", "") + (reasoning or "")
                }
            case _:
                return current_partial, accumulated



    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        accumulated=state.get("partial", {})
        partial, accumulated = self.process_delta(
            delta=self.extract_delta(native_chunk), current_partial=partial_messages[-1] if len(partial_messages) > 0 else None, accumulated=state.get("partial", {})
        )
        new_state = {**state, "partial": accumulated}
        return  [partial] if partial else [], [], native_messages, new_state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return final_messages, native_messages, state
