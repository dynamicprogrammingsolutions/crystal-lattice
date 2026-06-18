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
        runtime_state_root: Any | None = None,
        runtime_store: Any | None = None,
        tool_runtime: Any | None = None,
    ) -> None:
        self._generic_layer = {
            "app": app,
            "application": application if application is not None else app,
            "session_asset_store": session_asset_store,
            "runtime_state_root": runtime_state_root,
            "runtime_store": runtime_store,
            "tool_runtime": tool_runtime,
        }

    def build_core_handoff_context(
        self,
        *,
        base_config: Mapping[str, Any],
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        blocked = {
            "core",
            "config",
            "session",
            "session_id",
            "request_id",
            "stream",
            "trigger_source",
            "lifecycle",
            "request_context",
            "request_runtime",
            "final_messages",
            "native_messages",
            "native_final_messages",
            "turn_native_start_index",
        }
        filtered_extra = (
            {
                key: value
                for key, value in extra.items()
                if isinstance(key, str) and key not in blocked
            }
            if isinstance(extra, Mapping)
            else {}
        )
        filtered_extra["base_config"] = dict(base_config)
        return merge_context_layers(
            builder="application",
            call_path="core_handoff",
            generic_layer=self._generic_layer,
            specific_layer={},
            extra=filtered_extra,
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

    def build_application_lifecycle_context(
        self,
        *,
        lifecycle: str,
        config: Mapping[str, Any],
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return merge_context_layers(
            builder="application",
            call_path="application_lifecycle",
            generic_layer=self._generic_layer,
            specific_layer={
                "lifecycle": lifecycle,
                "trigger_source": "application",
                "config": dict(config),
                "base_config": dict(config),
            },
            extra=extra,
        )

    def build_application_ui_context(
        self,
        *,
        ui_context: str,
        config: Mapping[str, Any],
        tags: Optional[list[Any]] = None,
        models: Optional[list[Mapping[str, Any]]] = None,
        session: Any | None = None,
        base_config: Optional[Mapping[str, Any]] = None,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        specific_layer: Dict[str, Any] = {
            "trigger_source": "application",
            "ui_context": ui_context,
            "config": dict(config),
            "tags": list(tags or []),
            "models": [dict(model) for model in (models or [])],
        }
        if base_config is not None:
            specific_layer["base_config"] = dict(base_config)
        if session is not None:
            specific_layer["session"] = session.to_dict()
            specific_layer["session_id"] = session.session_id

        return merge_context_layers(
            builder="application",
            call_path="application_ui",
            generic_layer=self._generic_layer,
            specific_layer=specific_layer,
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