from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Optional

from .plugin.context_helper import merge_context_layers


class CoreContext:
    """Concrete layered context builder for AgentCore-owned paths."""

    def __init__(
        self,
        *,
        core: Any,
    ) -> None:
        self._core = core

    def build_request_context(
        self,
        *,
        config: Mapping[str, Any],
        plugin_context: Mapping[str, Any],
        session: Any,
        request_id: str | None,
        stream: bool | None = None,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        specific = {
            "config": dict(config),
            "request_id": request_id,
            "session": session.to_dict(),
            "session_id": session.session_id,
        }
        if stream is not None:
            specific["stream"] = bool(stream)
        specific.update(
            self._without_keys(plugin_context, {"core", "config", "request_id"})
        )
        return merge_context_layers(
            builder="core",
            call_path="request",
            generic_layer={"core": self._core},
            specific_layer=specific,
            extra=extra,
        )

    def build_rebuild_context(
        self,
        *,
        config: Mapping[str, Any],
        plugin_context: Mapping[str, Any],
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        specific = {
            "config": dict(config),
            **self._without_keys(plugin_context, {"core", "config"}),
        }
        return merge_context_layers(
            builder="core",
            call_path="rebuild",
            generic_layer={"core": self._core},
            specific_layer=specific,
            extra=extra,
        )

    def build_session_action_context(
        self,
        *,
        config: Mapping[str, Any],
        session: Any,
        request_context: Mapping[str, Any],
        request_runtime: Mapping[str, Any],
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        specific = {
            "config": dict(config),
            "trigger_source": "core",
            "session": session.to_dict(),
            "session_id": session.session_id,
            "request_context": dict(request_context),
            "request_runtime": dict(request_runtime),
        }
        return merge_context_layers(
            builder="core",
            call_path="session_action",
            generic_layer={"core": self._core},
            specific_layer=specific,
            extra=extra,
        )

    def build_lifecycle_action_context(
        self,
        *,
        config: Mapping[str, Any],
        session: Any,
        lifecycle: str,
        request_context: Mapping[str, Any],
        request_runtime: Mapping[str, Any],
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        specific = {
            "config": dict(config),
            "trigger_source": "core",
            "lifecycle": lifecycle,
            "session": session.to_dict(),
            "session_id": session.session_id,
            "request_context": dict(request_context),
            "request_runtime": dict(request_runtime),
        }
        return merge_context_layers(
            builder="core",
            call_path="lifecycle_action",
            generic_layer={"core": self._core},
            specific_layer=specific,
            extra=extra,
        )

    def build_response_lifecycle_context(
        self,
        *,
        config: Mapping[str, Any],
        session: Any,
        lifecycle: str,
        request_context: Mapping[str, Any],
        request_runtime: Mapping[str, Any],
        final_messages: list[dict[str, Any]],
        native_final_messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        stream: bool,
        turn_native_start_index: int,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        specific = {
            "config": dict(config),
            "trigger_source": "core",
            "lifecycle": lifecycle,
            "session": session.to_dict(),
            "session_id": session.session_id,
            "request_context": dict(request_context),
            "request_runtime": dict(request_runtime),
            "final_messages": list(final_messages),
            "native_final_messages": list(native_final_messages),
            "native_messages": list(native_messages),
            "stream": bool(stream),
            "turn_native_start_index": turn_native_start_index,
        }
        return merge_context_layers(
            builder="core",
            call_path="response_lifecycle",
            generic_layer={"core": self._core},
            specific_layer=specific,
            extra=extra,
        )

    def build_tool_context(
        self,
        *,
        config: Mapping[str, Any],
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return merge_context_layers(
            builder="core",
            call_path="tool",
            generic_layer={"core": self._core},
            specific_layer={"config": dict(config)},
            extra=extra,
        )

    @staticmethod
    def _without_keys(
        mapping: Mapping[str, Any],
        keys: Iterable[str],
    ) -> Dict[str, Any]:
        blocked = set(keys)
        return {
            key: value
            for key, value in mapping.items()
            if isinstance(key, str) and key not in blocked
        }