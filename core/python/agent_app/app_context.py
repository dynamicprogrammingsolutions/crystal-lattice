from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from agent_core.plugin.context_helper import merge_context_layers


class ApplicationContext:
    """Concrete layered context builder for AgentApplication-owned paths."""

    def __init__(
        self,
        *,
        app: Any,
        application: Any | None = None,
        session_asset_store: Any | None = None,
        runtime_store: Any | None = None,
        tool_runtime: Any | None = None,
    ) -> None:
        self._generic_layer = {
            "app": app,
            "application": application if application is not None else app,
            "session_asset_store": session_asset_store,
            "runtime_store": runtime_store,
            "tool_runtime": tool_runtime,
        }

    def build_core_extra(
        self,
        *,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return merge_context_layers(
            builder="application",
            call_path="core_handoff",
            generic_layer=self._generic_layer,
            specific_layer={},
            extra=extra,
        )

    def build_lifecycle_context(
        self,
        *,
        lifecycle: str,
        session: Any,
        config: Mapping[str, Any],
        base_config: Mapping[str, Any],
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return merge_context_layers(
            builder="application",
            call_path="lifecycle",
            generic_layer=self._generic_layer,
            specific_layer={
                "lifecycle": lifecycle,
                "trigger_source": "application",
                "session": session.to_dict(),
                "session_id": session.session_id,
                "config": dict(config),
                "base_config": dict(base_config),
            },
            extra=extra,
        )

    def build_session_action_context(
        self,
        *,
        session: Any,
        base_config: Mapping[str, Any],
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return merge_context_layers(
            builder="application",
            call_path="session_action",
            generic_layer=self._generic_layer,
            specific_layer={
                "trigger_source": "application",
                "session": session.to_dict(),
                "session_id": session.session_id,
                "base_config": dict(base_config),
            },
            extra=extra,
        )

    def build_tool_context(
        self,
        *,
        session: Any,
        request_id: str,
        base_config: Mapping[str, Any],
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return merge_context_layers(
            builder="application",
            call_path="tool",
            generic_layer=self._generic_layer,
            specific_layer={
                "trigger_source": "application",
                "session": session.to_dict(),
                "session_id": session.session_id,
                "request_id": request_id,
                "base_config": dict(base_config),
            },
            extra=extra,
        )