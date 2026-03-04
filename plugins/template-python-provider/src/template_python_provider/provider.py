from __future__ import annotations

"""Provider template (skeleton + shared streaming helpers).

This module intentionally contains **minimal placeholders**, not a complete
working provider integration.

The goal is that plugin authors can copy this template and only **add**
provider-specific logic (API calls, chunk parsing, conversion rules) without
needing to delete a pre-baked example.

Two supported streaming paths:

1) Accumulator pattern (recommended)
   - You implement: ``stream_api`` + ``extract_delta`` + ``process_delta``
   - Shared helpers implement: ``process_chunk`` + ``finalize``

2) Custom streaming
   - You implement: ``stream_api`` + ``process_chunk`` + ``finalize``

See also: `plugins/docs/provider-plugins.md`.
"""

from typing import Any, Dict, Iterator, List, Tuple

from agent_core.types import ProviderPlugin
from agent_core.utils import get_logger

logger = get_logger("template_provider")


def _truncate(value: Any, limit: int = 1000) -> str:
    """Best-effort string truncation for debug logging."""

    try:
        s = str(value)
    except Exception:
        return "<unprintable>"
    if len(s) > limit:
        return s[:limit] + "...<truncated>"
    return s


class AccumulatorStreamingMixin:
    """Shared implementation of the accumulator streaming pattern.

    Provider authors implement:
    - ``extract_delta(native_chunk) -> dict``
    - ``process_delta(delta, accumulated) -> (partial_fragment|None, new_accumulated)``

    Contract conventions used by this mixin:
    - ``state['partial']`` is the accumulator (a provider-native assistant message dict)
    - partial fragments emitted per chunk should be provider-native message-like dicts
      (at least ``{"role":"assistant","content":"..."}``) so the wrapper can
      convert them to core messages for UI streaming.
    - ``native_messages`` should remain a coherent full-history list; do not append
      per-chunk artifacts into native history.
    """

    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover
        raise NotImplementedError("extract_delta must be implemented by the provider")

    def process_delta(
        self,
        delta: Dict[str, Any],
        accumulated: Dict[str, Any] | None,
    ) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError("process_delta must be implemented by the provider")

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Default streaming chunk reducer.

        This generic implementation:
        - extracts a delta
        - merges it into ``state['partial']``
        - emits a single partial fragment per chunk when present
        """

        if state.get("debug_stream"):
            logger.info("native_chunk", chunk=_truncate(native_chunk, 2000))

        delta = self.extract_delta(native_chunk)
        if state.get("debug_stream"):
            logger.info("delta", delta=_truncate(delta, 2000))

        accumulated = state.get("partial") if isinstance(state.get("partial"), dict) else {}
        fragment, new_accumulated = self.process_delta(delta, accumulated)

        if state.get("debug_stream"):
            logger.info("accumulated", partial=_truncate(new_accumulated, 2000))

        partials = [fragment] if isinstance(fragment, dict) else []
        finals: List[Dict[str, Any]] = []
        # IMPORTANT: keep the baseline native history unchanged on hot path.
        full_history = list(native_messages)
        return partials, finals, full_history, {**state, "partial": new_accumulated}

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Default finalize for accumulator-based providers."""

        partial = state.get("partial")
        if isinstance(partial, dict) and partial.get("content"):
            final = dict(partial)
            full_history = [*native_messages, final]
            return [final], full_history, {**state, "partial": None}
        return [], list(native_messages), {**state, "partial": None}


class TemplateProvider(AccumulatorStreamingMixin, ProviderPlugin):
    """Template ProviderPlugin (skeleton).

    This class is intentionally incomplete. Implement the TODOs before using it
    in an application.

    Recommended development order:
    1) implement non-streaming `call_api` first + write a smoke test
    2) implement streaming `stream_api` + `extract_delta` + `process_delta`
    3) run the template tests and add your provider-specific tests
    """

    name: str = "template_provider"
    version: str = "0.1.0"

    # ---- Config/UI ----
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "model": {"type": "string", "required": True},
            "api_key": {"type": "string", "required": False},
            "base_url": {"type": "string", "required": False},
            "timeout": {"type": "number", "required": False, "default": 60},
            "debug_stream": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Log raw chunks/deltas while developing streaming.",
            },
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {"type": "text", "key": "model", "label": "Model"},
            {"type": "text", "key": "base_url", "label": "Base URL"},
            {"type": "text", "key": "api_key", "label": "API key"},
            {"type": "checkbox", "key": "debug_stream", "label": "Debug stream"},
        ]

    # ---- Tags / capabilities ----
    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        # TODO: define stable tags for dependency enablement.
        return ["provider:template_provider", "supports_streaming"]

    # ---- Lifecycle ----
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "config": config,
            "request": {},
            "partial": None,
            "debug_stream": bool(config.get("debug_stream")),
        }

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        # TODO: build state["request"] with url/payload/headers/timeout.
        # Also reset per-turn accumulators.
        return list(native_messages), {**state, "partial": None}

    # ---- Conversion ----
    # You may omit these and rely on adapter defaults if OpenAI-like role/content
    # mapping is sufficient. If you need to preserve metadata across rebuilds,
    # implement `_metadata` handling.

    # ---- Non-streaming I/O ----
    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Make a non-streaming API call.

        Recommended first step: implement this method to learn request/response
        shapes without chunk processing.
        """

        raise NotImplementedError("TODO: implement call_api")

    # ---- Streaming I/O ----
    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Make a streaming API call and yield provider-native chunk dicts."""

        raise NotImplementedError("TODO: implement stream_api")

    # ---- Accumulator hooks (streaming path 1) ----
    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a delta dict from a provider-native streaming chunk.

        TODO: parse your provider's chunk shape.

        Common shape for OpenAI-style streams:
        - ``chunk['choices'][0]['delta']``
        """

        raise NotImplementedError("TODO: implement extract_delta")

    def process_delta(
        self,
        delta: Dict[str, Any],
        accumulated: Dict[str, Any] | None,
    ) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:
        """Reduce one delta into an updated accumulator.

        TODO: merge the delta into a provider-native assistant message dict.

        Returns:
        - partial_fragment: a provider-native message-like dict for UI streaming (or None)
        - new_accumulated: the updated accumulator stored in ``state['partial']``
        """

        raise NotImplementedError("TODO: implement process_delta")


class TemplateCustomStreamingProvider(ProviderPlugin):
    """Template provider skeleton for *custom* streaming implementations.

    Implement this variant when the accumulator pattern does not fit your
    provider's streaming protocol.
    """

    name: str = "template_provider_custom"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {"model": {"type": "string", "required": True}}

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        raise NotImplementedError("TODO: implement call_api")

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        raise NotImplementedError("TODO: implement stream_api")

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        raise NotImplementedError("TODO: implement process_chunk")

    def finalize(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        raise NotImplementedError("TODO: implement finalize")


__all__ = [
    "AccumulatorStreamingMixin",
    "TemplateProvider",
    "TemplateCustomStreamingProvider",
]
