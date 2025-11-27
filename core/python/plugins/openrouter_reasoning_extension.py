"""OpenRouter reasoning extension for OpenRouter provider.

Adds reasoning/thinking support to OpenRouter models that support it.
Extracts reasoning content from responses and exposes it in metadata.
Properly handles reasoning_details for preservation across tool calling rounds.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


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

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "reasoning_effort": {
                "type": "string",
                "required": False,
                "enum": ["low", "medium", "high"],
                "description": "Control reasoning depth (model-specific)",
            },
            "enable_reasoning": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Enable reasoning/thinking for models that support it",
            },
            "include_reasoning": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Include reasoning tokens in response",
            },
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
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
                "options": [
                    {"value": "low", "label": "Low"},
                    {"value": "medium", "label": "Medium"},
                    {"value": "high", "label": "High"},
                ],
            },
        ]

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Identify this extension for dependency resolution."""
        return ["ext:openrouter_reasoning"]

    def required_tags(self) -> List[str]:
        """Require OpenRouter provider and reasoning support."""
        return ["openrouter", "supports_reasoning"]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        enabled = bool(config.get("enable_reasoning"))
        if not enabled:
            return state

        reasoning_config = {
            "enabled": True,
            "effort": config.get("reasoning_effort"),
            "include": config.get("include_reasoning", True),
        }

        return {
            **state,
            "openrouter_reasoning": reasoning_config,
        }

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Pass through reasoning and reasoning_details to native format.

        reasoning_details must be preserved exactly as returned from the API
        for tool calling continuity.
        """
        if len(messages) != len(native_messages):
            return native_messages

        enhanced_native_messages = []
        for message, native_msg in zip(messages, native_messages):
            enhanced = dict(native_msg)
            metadata = message.get("metadata", {})

            # Pass through reasoning text if present
            if "reasoning" in metadata:
                enhanced["reasoning"] = metadata["reasoning"]

            # Pass through reasoning_details unchanged if present
            if "reasoning_details" in metadata:
                enhanced["reasoning_details"] = metadata["reasoning_details"]

            enhanced_native_messages.append(enhanced)

        return enhanced_native_messages

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
    ) -> Dict[str, Any]:
        reasoning_config = state.get("openrouter_reasoning")
        if not reasoning_config or not reasoning_config.get("enabled"):
            return state

        request = state.get("request") or {}
        payload = dict(request.get("payload", {}))

        # Add reasoning parameters based on configuration
        reasoning_effort = reasoning_config.get("effort")
        if reasoning_effort:
            payload["reasoning_effort"] = reasoning_effort

        # Include reasoning in response
        if reasoning_config.get("include"):
            payload["include_reasoning"] = True

        return {
            **state,
            "request": {
                **request,
                "payload": payload,
            },
        }

    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a provider-native delta dictionary from a streaming chunk."""
        if "choices" in native_chunk and native_chunk["choices"]:
            return dict(native_chunk["choices"][0])
        return {}

    def _accumulate_reasoning_details(
        self,
        current_details: Optional[List[Dict[str, Any]]],
        delta_details: Optional[List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Accumulate reasoning_details arrays across streaming chunks.

        Handles all provider formats uniformly:
        - Metadata fields (type, format, index, id): use latest value
        - Content fields (text, data, summary, signature): accumulate by concatenation

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
            for idx, acc_detail in enumerate(accumulated):
                # Match by id if present, otherwise by index and type
                if detail_id and acc_detail.get("id") == detail_id:
                    matching_idx = idx
                    break
                elif (
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
                        acc_detail[key] = acc_detail.get(key, "") + value
                    elif key in METADATA_FIELDS:
                        # Override metadata fields with latest value
                        acc_detail[key] = value
                    else:
                        # Unknown field - accumulate to be safe
                        if isinstance(value, str):
                            acc_detail[key] = acc_detail.get(key, "") + value
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
        current_final: Optional[Dict[str, Any]] = None,
        accumulated: Optional[Dict[str, Any]] = None,
    ):
        """
        Enhance the partial or final message with reasoning information from delta.
        Accumulates reasoning_details correctly for all supported providers.
        Returns (partial_message, final_message, accumulated).
        """
        if accumulated is None:
            accumulated = {}

        # Full message chunk
        if "message" in delta and current_final is not None:
            message = delta.get("message") or {}
            new_final = dict(current_final)

            if message.get("reasoning"):
                new_final["reasoning"] = message["reasoning"]

            if message.get("reasoning_details"):
                # Replace reasoning_details in full message mode
                new_final["reasoning_details"] = list(message["reasoning_details"])

            return current_partial, new_final, accumulated

        # Delta chunk
        if "delta" in delta:
            delta_content = delta.get("delta", {})
            new_partial = current_partial
            new_accumulated = dict(accumulated)

            # Handle reasoning text
            if delta_content.get("reasoning"):
                if current_partial:
                    new_partial = dict(current_partial)
                    new_partial["reasoning"] = (
                        new_partial.get("reasoning", "") + delta_content["reasoning"]
                    )

                new_accumulated["reasoning"] = (
                    new_accumulated.get("reasoning", "") + delta_content["reasoning"]
                )

            # Handle reasoning_details
            if delta_content.get("reasoning_details"):
                current_details = new_partial.get("reasoning_details") if new_partial else None
                new_details = self._accumulate_reasoning_details(
                    current_details, delta_content["reasoning_details"]
                )

                if new_partial:
                    new_partial["reasoning_details"] = new_details

                # Also accumulate in state
                acc_details = new_accumulated.get("reasoning_details")
                new_accumulated["reasoning_details"] = self._accumulate_reasoning_details(
                    acc_details, delta_content["reasoning_details"]
                )

            return new_partial, current_final, new_accumulated

        return current_partial, current_final, accumulated

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        delta = self.extract_delta(native_chunk or {})

        new_partial_messages = partial_messages
        new_final_messages = final_messages
        new_native_messages = native_messages
        accumulated = state.get("partial", {})

        if len(final_messages) > 0:
            new_partial_message, new_final_message, accumulated = self.process_delta(
                delta=delta, current_final=final_messages[-1], accumulated=accumulated
            )
            new_final_messages = [*(final_messages[:-1] or []), new_final_message]
            new_native_messages = [*(native_messages[:-1] or []), new_final_message]

        if len(partial_messages) > 0:
            new_partial_message, new_final_message, accumulated = self.process_delta(
                delta=delta,
                current_partial=partial_messages[-1],
                accumulated=accumulated,
            )
            new_partial_messages = [*(partial_messages[:-1] or []), new_partial_message]

        return (
            new_partial_messages,
            new_final_messages,
            new_native_messages,
            {**state, "partial": accumulated},
        )

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        reasoning_config = state.get("openrouter_reasoning")
        if not reasoning_config or not reasoning_config.get("enabled"):
            return final_messages, native_messages, state

        # If we accumulated reasoning during streaming, attach it to the last final
        accumulated = state.get("partial") or {}
        reasoning_text = accumulated.get("reasoning") if isinstance(accumulated, dict) else None
        reasoning_details = accumulated.get("reasoning_details")

        if reasoning_text or reasoning_details:
            if final_messages:
                last_final = dict(final_messages[-1])
                if reasoning_text:
                    last_final["reasoning"] = last_final.get("reasoning", "") + reasoning_text
                if reasoning_details:
                    last_final["reasoning_details"] = reasoning_details
                final_messages = [*final_messages[:-1], last_final]

            if native_messages:
                last_native = dict(native_messages[-1])
                if reasoning_text:
                    last_native["reasoning"] = last_native.get("reasoning", "") + reasoning_text
                if reasoning_details:
                    last_native["reasoning_details"] = reasoning_details
                native_messages = [*native_messages[:-1], last_native]

        return final_messages, native_messages, state
