from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


class ClaudeCachingExtension(ProviderExtensionPlugin):
    """Provider extension that injects Anthropic cache_control via OpenRouter.

    This extension only applies when:
    - The selected provider is OpenRouter (provider tag: ``"openrouter"``)
    - The configured model id starts with ``"anthropic/"``

    Behavior:
    - During :meth:`initialize_request`, wraps the *last* provider-native
      message in an Anthropic-style text block list and attaches
      ``{"cache_control": {"type": "ephemeral"}}``. The resulting shape
      matches the Claude caching API when used through OpenRouter's
      ``/chat/completions`` endpoint.
    - During :meth:`process_chunk`, reads ``cached_tokens`` from
      ``usage.prompt_tokens_details.cached_tokens`` on streaming chunks and
      stores it in the shared provider state.
    - During :meth:`finalize`, strips any ``cache_control`` annotations from
      the retained provider-native history so that ephemeral cache markers are
      not persisted in ``session.metadata["native_messages"]`` and attaches
      a ``cached_tokens`` field to the last assistant message in the
      provider-native history under its internal ``_metadata`` key.
    - During :meth:`from_native_messages`, mirrors this information into
      core-message ``metadata["cached_tokens"]``.

    The actual cache hit behavior is handled by OpenRouter/Anthropic. This
    extension only shapes the outbound payload, surfaces usage metadata, and
    cleans up the stored provider-native history.
    """

    name: str = "claude_caching_extension"
    version: str = "0.1.0"

    # ---- Config / UI ----
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enable_claude_caching": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": (
                    "Enable Anthropic-style caching for models whose id "
                    "starts with 'anthropic/'. Applies only when using the "
                    "OpenRouter provider."
                ),
            }
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Return configuration and footer UI elements for this extension.

        The returned list contains both a ``"config"`` element (implicit
        ``ui_type``) for toggling the feature and a ``"message_footer"``
        element so UIs can display ``metadata.cached_tokens`` in
        per-message footers.
        """

        return [
            {
                "type": "checkbox",
                "key": "enable_claude_caching",
                "label": "Enable Claude Caching (Anthropic via OpenRouter)",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.cached_tokens",
                "template": "cached: {{data}}",
            },
        ]

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        return ["ext:claude_caching"]

    def required_tags(self) -> List[str]:
        # Only meaningful for the OpenRouter provider; the provider already
        # advertises the "openrouter" tag.
        return ["openrouter"]

    # ---- Helpers ----
    def _should_enable_for_state(self, state: Dict[str, Any]) -> bool:
        config = state.get("config", {})
        if not isinstance(config, dict):
            return False

        if not config.get("enable_claude_caching", True):
            return False

        model = config.get("model")
        if not isinstance(model, str) or not model.startswith("anthropic/"):
            return False

        return True

    def _inject_cache_breakpoint(
        self, native_messages: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], bool]:
        if not native_messages:
            return native_messages, False

        last = native_messages[-1]
        content = last.get("content")

        # Skip if content is already a list of blocks; avoid double-wrapping.
        if isinstance(content, list):
            return native_messages, False

        if not isinstance(content, str) or not content:
            return native_messages, False

        blocks: List[Dict[str, Any]] = [
            {
                "type": "text",
                "text": content,
                "cache_control": {"type": "ephemeral"},
            },
        ]

        new_last = {**last, "content": blocks}
        new_messages = [*native_messages[:-1], new_last]
        return new_messages, True

    def _strip_cache_control(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(msg, dict):
            return msg
        content = msg.get("content")
        if not isinstance(content, list):
            return msg
        new_blocks: List[Dict[str, Any]] = []
        for block in content:
            if not isinstance(block, dict):
                new_blocks.append(block)
                continue
            if "cache_control" in block:
                cleaned = {k: v for k, v in block.items() if k != "cache_control"}
                new_blocks.append(cleaned)
            else:
                new_blocks.append(block)
        return {**msg, "content": new_blocks}

    # ---- Stateless transforms ----
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # This extension operates during initialize_request/finalize only.
        return list(native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Mirror cached_tokens out of provider-native _metadata into
        # core message metadata. This preserves cached_tokens added
        # during streaming chunk processing as well as in non-streaming
        # responses.

        enhanced: List[Dict[str, Any]] = []

        if len(messages) == len(native_messages):
            for msg, native in zip(messages, native_messages):
                core_md = dict(msg.get("metadata") or {})
                internal_md = native.get("_metadata") or {}
                if isinstance(internal_md, dict) and "cached_tokens" in internal_md:
                    core_md["cached_tokens"] = internal_md.get("cached_tokens")
                enhanced.append({**msg, "metadata": core_md})
            return enhanced

        # When lengths differ (e.g. streaming combined finals), fall
        # back to copying only onto the last core message.
        enhanced.extend(messages)
        if native_messages and messages:
            internal_md = native_messages[-1].get("_metadata") or {}
            if isinstance(internal_md, dict) and "cached_tokens" in internal_md:
                cached = internal_md.get("cached_tokens")
                last_msg = dict(messages[-1])
                core_md = dict(last_msg.get("metadata") or {})
                core_md["cached_tokens"] = cached
                enhanced[-1] = {**last_msg, "metadata": core_md}

        return enhanced

    # ---- Lifecycle hooks ----
    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        # Merge config into shared provider state for later checks.
        return {**state, "config": {**state.get("config", {}), **config}}

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if not self._should_enable_for_state(state):
            return list(native_messages), state

        adjusted, injected = self._inject_cache_breakpoint(native_messages)
        if not injected:
            return list(native_messages), state

        # Track that we injected cache_control so finalize can strip it
        # from retained native history.
        new_state = {**state, "_claude_cache_injected": True}
        return adjusted, new_state

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        if not self._should_enable_for_state(state):
            return partial_messages, final_messages, native_messages, state

        # Follow the same pattern as OpenRouterReasoningExtension: use
        # the shared provider "partial" accumulator for any extra
        # metadata we want to attach to the assistant message. The
        # provider's process_chunk() maintains state["partial"] as the
        # latest provider-native assistant message; we enrich that with
        # cached_tokens when available. We only care about cached_tokens
        # on the final messages, so we avoid changing the shape of
        # streaming partials and only decorate the provider's internal
        # accumulator in state.

        cached_tokens = None
        if isinstance(native_chunk, dict):
            usage = native_chunk.get("usage") or {}
            if isinstance(usage, dict):
                details = usage.get("prompt_tokens_details") or {}
                if isinstance(details, dict) and "cached_tokens" in details:
                    cached_tokens = details.get("cached_tokens")
        if cached_tokens is None:
            return partial_messages, final_messages, native_messages, state

        accumulated = state.get("partial")
        if isinstance(accumulated, dict):
            internal_md = dict(accumulated.get("_metadata") or {})
            internal_md["cached_tokens"] = cached_tokens
            accumulated = {**accumulated, "_metadata": internal_md}
            new_state = {**state, "partial": accumulated}
        else:
            new_state = state

        # Do not alter the provider's partial/final messages; we only
        # enrich the internal native accumulator so finalize() and
        # from_native_messages() can expose cached_tokens on the
        # retained history and final core messages.
        return partial_messages, final_messages, native_messages, new_state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        if not self._should_enable_for_state(state):
            return final_messages, native_messages, state

        # Strip any cache_control markers from retained provider-native
        # history so that ephemeral cache hints are not persisted on the
        # session. Cached token counts remain attached via _metadata on
        # the assistant messages accumulated during streaming or
        # returned from non-streaming calls.
        cleaned_history = [self._strip_cache_control(m) for m in native_messages]
        return final_messages, cleaned_history, state
