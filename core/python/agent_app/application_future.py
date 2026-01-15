from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple, cast
import uuid
from contextlib import contextmanager
from datetime import datetime
from threading import Lock

from agent_core import AgentCore, MessageRole, Session

from .app_plugins import ApplicationPluginWrapper
from .config import (
    build_agent_config,
    load_plugins,
    load_application_plugins,
    load_raw_config,
    resolve_placeholders,
    resolve_request_config,
)
from .events import EventStore, InMemoryEventStore
from .sessions import FilesystemSessionStore
from .tool_loop import ToolLoopRunner
from .plugin_manager import PluginManager


@dataclass(frozen=True)
class _ToolLoopConfig:
    """Configuration for the built-in tool loop.

    Kept aligned with the original application-layer behaviour so that
    implementations can be compared side-by-side with a diff.
    """

    max_loops: int = 50


class AgentApplication:
    """Future application-layer API around :class:`agent_core.AgentCore`.

    This variant focuses on the *core-first* architecture used by
    Example 13. It exposes only the typed helpers and the
    :meth:`send_request` event generator.

    The original dict-based HTTP-style API
    (``create_session``, ``add_message``, ``send_request``,
    ``get_events``, ``stream_events``) has been replaced by this
    implementation.

    Structure and helper method names intentionally mirror the original
    application-layer implementation so it can be compared easily.
    """

    def __init__(
        self,
        config_path: str | Path,
        session_root: str | Path,
        core_factory: Callable[[], AgentCore] = AgentCore,
        event_store: Optional[EventStore] = None,
    ) -> None:
        # Core factory is stored so that per-session cores can be created
        # without sharing state across requests.
        self._core_factory = core_factory
        self._event_store: EventStore = event_store or InMemoryEventStore()

        # A single core instance is still used for import/export with the
        # filesystem session store; inference uses fresh cores created via
        # ``_new_core``.
        core = core_factory()
        self._core = core

        raw_config = load_raw_config(config_path)
        resolved_config, placeholder_errors = resolve_placeholders(raw_config)
        self._config: Dict[str, Any] = resolved_config
        self._config_errors: List[Dict[str, Any]] = placeholder_errors

        plugins_cfg = resolved_config.get("plugins") or {}
        plugin_cache_dir = resolved_config.get("plugin_cache_dir")
        plugin_policy = resolved_config.get("plugin_policy") or {}
        if isinstance(plugin_cache_dir, str) and plugin_cache_dir:
            mgr = PluginManager(cache_dir=Path(plugin_cache_dir), policy=plugin_policy)
            plugin_classes, plugin_errors = mgr.load_plugins_config(plugins_cfg)
        else:
            plugin_classes, plugin_errors = load_plugins(plugins_cfg)
        self._plugin_classes: Dict[str, List[type[Any]]] = plugin_classes
        self._config_errors.extend(plugin_errors)

        # Build a catalog of plugins keyed by kind and plugin id (name attribute).
        self._plugins_by_kind_and_id: Dict[str, Dict[str, type[Any]]] = {}
        for kind, classes in self._plugin_classes.items():
            kind_mapping: Dict[str, type[Any]] = {}
            for plugin_cls in classes or []:
                plugin_id = self._plugin_id_for_class(plugin_cls)
                # First registration for a given id wins to preserve config order.
                if plugin_id not in kind_mapping:
                    kind_mapping[plugin_id] = plugin_cls
            self._plugins_by_kind_and_id[kind] = kind_mapping

        # Manual registration from config: providers with shared extensions,
        # then features and tools. This mirrors ``application.AgentApplication``
        # so the two versions can be compared easily.
        provider_exts = plugin_classes.get("extensions") or []
        for provider_cls in plugin_classes.get("providers") or []:
            core.register_provider(provider_cls, extensions=provider_exts)
        for feature_cls in plugin_classes.get("features") or []:
            core.register_feature(feature_cls)
        for tool_cls in plugin_classes.get("tools") or []:
            core.register_tool(tool_cls)

        # Application-level plugins are configured separately from core
        # provider/feature/tool plugins. They operate on the
        # :class:`AgentApplication` level (sessions, storage, actions).
        raw_app_plugins = resolved_config.get("application_plugins") or []
        if isinstance(plugin_cache_dir, str) and plugin_cache_dir:
            mgr = PluginManager(cache_dir=Path(plugin_cache_dir), policy=plugin_policy)
            app_plugin_classes, app_plugin_errors = mgr.load_application_plugins(raw_app_plugins)
        else:
            app_plugin_classes, app_plugin_errors = load_application_plugins(raw_app_plugins)
        self._app_plugin_classes: List[type[Any]] = app_plugin_classes
        self._config_errors.extend(app_plugin_errors)

        self._app_plugins: Dict[str, ApplicationPluginWrapper] = {}
        for plugin_class in self._app_plugin_classes:
            plugin_id = self._plugin_id_for_class(plugin_class)
            # First registration for a given id wins to preserve config order.
            if plugin_id in self._app_plugins:
                continue
            wrapper = ApplicationPluginWrapper(plugin_id=plugin_id, plugin_class=plugin_class)
            wrapper.init(resolved_config)
            self._app_plugins[plugin_id] = wrapper

        self._session_store = FilesystemSessionStore(Path(session_root), core)
        self._tool_loop_cfg = _ToolLoopConfig()
        self._cancelled_requests: set[str] = set()

        # Event compaction controls. These are primarily intended for
        # debugging and tests; in normal operation they remain enabled
        # so that HTTP and terminal polling see compacted batches.
        self._enable_event_compaction: bool = True
        self._enable_drop_redundant_partials: bool = True
        self._enable_merge_consecutive_partials: bool = True

        # Cache per-agent base configs to avoid recomputing on every call.
        agents = resolved_config.get("agents") or {}
        self._agent_base_configs: Dict[str, Dict[str, Any]] = {}
        self._agent_plugin_ids: Dict[str, Optional[List[str]]] = {}
        for agent_id, agent_cfg in agents.items():
            self._agent_base_configs[agent_id] = build_agent_config(resolved_config, agent_id)
            raw_plugins = agent_cfg.get("plugins") if isinstance(agent_cfg, dict) else None
            if isinstance(raw_plugins, list):
                self._agent_plugin_ids[agent_id] = [
                    p for p in raw_plugins if isinstance(p, str)
                ]
            else:
                # None means "all plugins enabled" for this agent.
                self._agent_plugin_ids[agent_id] = None

    # ------------------------------------------------------------------
    # Helper methods (kept in the same order as application.AgentApplication)
    # ------------------------------------------------------------------

    @contextmanager
    def acquire_session_lock(self, session_id: str) -> Iterator[None]:
        """Yield under the event store's lock for ``session_id``."""

        with self._event_store.acquire_session_lock(session_id):
            yield

    def _new_request_id(self) -> str:
        return str(uuid.uuid4())

    def _get_agent_base_config(self, agent_id: str) -> Dict[str, Any]:
        cfg = self._agent_base_configs.get(agent_id)
        if cfg is None:
            cfg = build_agent_config(self._config, agent_id)
            self._agent_base_configs[agent_id] = cfg
        return cfg

    def _plugin_id_for_class(self, plugin_class: type[Any]) -> str:
        """Return the stable plugin id for a plugin class.

        Uses the class-level ``name`` attribute when present, falling back
        to the class name. This matches the identity used by the core and
        the terminal application.
        """

        plugin_id = getattr(plugin_class, "name", None)
        if not isinstance(plugin_id, str) or not plugin_id:
            plugin_id = plugin_class.__name__
        return plugin_id

    def _build_core_with_enabled_ids(
        self,
        enabled_ids: Optional[List[str]],
    ) -> AgentCore:
        """Construct a fresh AgentCore with only selected plugins enabled.

        When ``enabled_ids`` is ``None``, all available plugins are
        registered. Unknown plugin ids are ignored.

        Raises:
            RuntimeError: If no provider plugins are enabled.
        """

        core = self._core_factory()

        enabled_set: Optional[Set[str]]
        if enabled_ids is None:
            enabled_set = None
        else:
            enabled_set = {p for p in enabled_ids if isinstance(p, str)}

        def _filter_plugins(kind: str) -> List[type[Any]]:
            all_for_kind = self._plugins_by_kind_and_id.get(kind, {})
            if enabled_set is None:
                return list(all_for_kind.values())
            return [cls for pid, cls in all_for_kind.items() if pid in enabled_set]

        enabled_providers = _filter_plugins("providers")
        if not enabled_providers:
            raise RuntimeError("No provider plugins enabled")

        enabled_extensions = _filter_plugins("extensions")
        enabled_features = _filter_plugins("features")
        enabled_tools = _filter_plugins("tools")

        for provider_cls in enabled_providers:
            core.register_provider(provider_cls, extensions=enabled_extensions)
        for feature_cls in enabled_features:
            core.register_feature(feature_cls)
        for tool_cls in enabled_tools:
            core.register_tool(tool_cls)

        return core

    def _new_core(self) -> AgentCore:
        """Construct a fresh :class:`AgentCore` instance with all plugins.

        This mirrors the original application-layer implementation but is
        used exclusively by the typed helpers and the new request API in
        this module.
        """

        return self._build_core_with_enabled_ids(None)

    def _load_session_required(self, session_id: str) -> Session:
        session = self._session_store.load(session_id)
        if session is None:
            raise KeyError(f"Session {session_id!r} not found")
        return session

    def _extract_tool_calls(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tool_calls: List[Dict[str, Any]] = []
        for msg in messages:
            if msg.get("role") != "assistant":
                continue
            metadata = msg.get("metadata") or {}
            calls = metadata.get("tool_calls") or []
            if isinstance(calls, list):
                tool_calls.extend([c for c in calls if isinstance(c, dict)])
        return tool_calls

    def _extract_pending_tool_calls_from_session(self, session: Session) -> List[Dict[str, Any]]:
        """Return tool_calls from the last assistant message, if not yet answered.

        A simple heuristic is used: if there is any tool message after the last
        assistant-with-tool_calls, we treat the calls as already handled.
        """

        last_tc_index: Optional[int] = None
        last_tc_calls: List[Dict[str, Any]] = []

        for idx, message in enumerate(session.messages):
            if message.role != "assistant":
                continue
            metadata = message.metadata or {}
            calls = metadata.get("tool_calls") or []
            if isinstance(calls, list) and calls:
                last_tc_index = idx
                last_tc_calls = [c for c in calls if isinstance(c, dict)]

        if last_tc_index is None or not last_tc_calls:
            return []

        # If there is any tool message after this index, assume the calls have
        # already been processed.
        for msg in session.messages[last_tc_index + 1 :]:
            if msg.role == "tool":
                return []

        return last_tc_calls

    # ------------------------------------------------------------------
    # Public helpers for tests / applications (manual registration)
    # ------------------------------------------------------------------

    def register_provider(self, plugin_class: type, extensions: Optional[List[type]] = None) -> None:
        self._core.register_provider(plugin_class, extensions=extensions or [])

    def register_feature(self, plugin_class: type) -> None:
        self._core.register_feature(plugin_class)

    def register_tool(self, plugin_class: type) -> None:
        self._core.register_tool(plugin_class)

    # ------------------------------------------------------------------
    # Typed helpers for applications (core-first API)
    # ------------------------------------------------------------------

    def get_config_errors(self) -> List[Dict[str, Any]]:
        """Return configuration and plugin loading errors."""

        return self._config_errors

    def get_event_store(self) -> EventStore:
        """Return the configured event store for this application."""

        return self._event_store

    def compact_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return a compacted view of ``events``.

        This helper removes redundant ``partial`` and ``tool_partial``
        events that precede terminal events (``final`` or
        ``tool_results``) for the same ``session_id``/``request_id``
        pair within a single batch. It does not modify the underlying
        event store and preserves the order of all kept events.
        """

        if not events or not self._enable_event_compaction:
            return events

        # ------------------------------------------------------------------
        # Pass 1: drop redundant partials that precede terminal events
        # ------------------------------------------------------------------

        if self._enable_drop_redundant_partials:
            keep_flags: List[bool] = [True] * len(events)
            seen_final: Dict[Tuple[Optional[str], Optional[str]], bool] = {}
            seen_tool_results: Dict[Tuple[Optional[str], Optional[str]], bool] = {}

            for idx in range(len(events) - 1, -1, -1):
                ev = events[idx]
                etype = ev.get("type")
                session_id = ev.get("session_id")
                request_id = ev.get("request_id")
                key = (session_id, request_id)

                if etype == "final":
                    seen_final[key] = True
                    keep_flags[idx] = True
                elif etype == "tool_results":
                    seen_tool_results[key] = True
                    keep_flags[idx] = True
                elif etype == "partial":
                    if seen_final.get(key):
                        keep_flags[idx] = False
                    else:
                        keep_flags[idx] = True
                elif etype == "tool_partial":
                    if seen_tool_results.get(key):
                        keep_flags[idx] = False
                    else:
                        keep_flags[idx] = True
                else:
                    keep_flags[idx] = True

            if all(keep_flags):
                dropped = events
            else:
                dropped = [ev for idx, ev in enumerate(events) if keep_flags[idx]]
        else:
            dropped = events

        # ------------------------------------------------------------------
        # Pass 2: merge consecutive partial/tool_partial events where possible
        # ------------------------------------------------------------------

        def _merge_two(a: Dict[str, Any], b: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """Return a merged event for ``a`` and ``b`` or ``None``.

            Only consecutive events of type ``partial`` or
            ``tool_partial`` with matching ``session_id`` and
            ``request_id`` are considered for merging.
            """

            atype = a.get("type")
            btype = b.get("type")
            if atype != btype:
                return None

            session_id_a = a.get("session_id")
            session_id_b = b.get("session_id")
            request_id_a = a.get("request_id")
            request_id_b = b.get("request_id")
            if session_id_a != session_id_b or request_id_a != request_id_b:
                return None

            if atype == "partial":
                msg_a = a.get("message") or {}
                msg_b = b.get("message") or {}
                if not isinstance(msg_a, dict) or not isinstance(msg_b, dict):
                    return None

                md_a = msg_a.get("metadata") or {}
                md_b = msg_b.get("metadata") or {}
                if not isinstance(md_a, dict) or not isinstance(md_b, dict):
                    md_a = {}
                    md_b = {}

                reasoning_a = md_a.get("reasoning")
                reasoning_b = md_b.get("reasoning")
                content_a = msg_a.get("content")
                content_b = msg_b.get("content")

                has_reasoning = isinstance(reasoning_a, str) or isinstance(reasoning_b, str)
                has_content = isinstance(content_a, str) or isinstance(content_b, str)
                if not (has_reasoning or has_content):
                    return None

                merged_event = dict(b)
                merged_msg = dict(msg_b)
                merged_md = dict(md_b)

                if has_reasoning:
                    ra = reasoning_a if isinstance(reasoning_a, str) else ""
                    rb = reasoning_b if isinstance(reasoning_b, str) else ""
                    merged_md["reasoning"] = ra + rb

                if has_content:
                    ca = content_a if isinstance(content_a, str) else ""
                    cb = content_b if isinstance(content_b, str) else ""
                    merged_msg["content"] = ca + cb

                merged_msg["metadata"] = merged_md
                merged_event["message"] = merged_msg
                return merged_event

            if atype == "tool_partial":
                # Tool partials stream tool output via payload.part.
                tool_id_a = a.get("tool_call_id")
                tool_id_b = b.get("tool_call_id")
                if tool_id_a != tool_id_b:
                    return None

                phase_a = a.get("phase")
                phase_b = b.get("phase")
                # Do not merge "end" events carrying the final result.
                if phase_a == "end" or phase_b == "end":
                    return None

                payload_a = a.get("payload") or {}
                payload_b = b.get("payload") or {}
                if not isinstance(payload_a, dict) or not isinstance(payload_b, dict):
                    return None

                part_a = payload_a.get("part")
                part_b = payload_b.get("part")
                if not (isinstance(part_a, str) or isinstance(part_b, str)):
                    return None

                merged_event = dict(b)
                merged_payload = dict(payload_b)
                pa = part_a if isinstance(part_a, str) else ""
                pb = part_b if isinstance(part_b, str) else ""
                merged_payload["part"] = pa + pb
                merged_event["payload"] = merged_payload
                return merged_event

            return None

        if not self._enable_merge_consecutive_partials:
            return dropped

        merged: List[Dict[str, Any]] = []
        current: Optional[Dict[str, Any]] = None

        for ev in dropped:
            if current is None:
                current = ev
                continue

            combined = _merge_two(current, ev)
            if combined is not None:
                current = combined
            else:
                merged.append(current)
                current = ev

        if current is not None:
            merged.append(current)

        return merged

    def advance_session_cursor(self, session_id: str, event_id: str) -> None:
        """Advance the per-session event cursor to ``event_id``.

        The cursor represents the latest event id whose effects are
        known to be reflected in the persisted session state for the
        given ``session_id``.
        """

        self._event_store.advance_session_cursor(session_id, event_id)

    def get_session_cursor_event_id(self, session_id: str) -> Optional[str]:
        """Return the latest cursor event id for ``session_id``."""
        return self._event_store.get_session_cursor_event_id(session_id)

    # Backwards-compatible alias; prefer get_session_cursor_event_id.
    def get_checkpoint_event_id(self, session_id: str) -> Optional[str]:
        return self.get_session_cursor_event_id(session_id)

    def record_checkpoint(
        self,
        session_id: str,
        request_id: Optional[str],
    ) -> Optional[str]:
        """Publish a lightweight checkpoint marker for ``session_id``.

        The marker is written to the shared event store and the session
        cursor is advanced to the checkpoint event's own ``event_id``.
        """

        marker = self._event_store.publish(
            {
                "type": "checkpoint",
                "session_id": session_id,
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )
        marker_id = marker.get("event_id")
        if isinstance(marker_id, str):
            self.advance_session_cursor(session_id, marker_id)
            return marker_id
        return None

    def publish_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Publish an event to the underlying event store.

        This helper is intentionally low-level: it does not emit
        checkpoint markers or advance session cursors. Callers that
        need to track persistence boundaries should combine this with
        :meth:`record_checkpoint` or :meth:`advance_session_cursor` as
        appropriate.
        """

        stored = self._event_store.publish(event)
        return stored

    def get_application_config(self) -> Dict[str, Any]:
        """Return application-level configuration section.

        This helper exposes the top-level "application" config subtree used
        for frontend-specific settings such as rendering limits.
        """

        cfg = self._config if isinstance(self._config, dict) else {}
        raw_app_cfg = cfg.get("application") if isinstance(cfg.get("application"), dict) else {}
        return cast(Dict[str, Any], raw_app_cfg)

    def cancel_request(self, request_id: str) -> None:
        """Request cooperative cancellation for an in-flight request.

        Cancellation is best-effort and affects only send_request calls that
        observe this ``request_id``. Providers and tool loops must periodically
        check for cancellation; long-running non-streaming calls may not stop
        immediately.
        """

        if not isinstance(request_id, str) or not request_id:
            raise ValueError("request_id must be a non-empty string")

        self._cancelled_requests.add(request_id)

    def list_agents(self) -> List[str]:
        """Return the configured agent identifiers.

        The list is derived from the resolved configuration and sorted
        for stable ordering.
        """

        return sorted(self._agent_base_configs.keys())

    def get_agent_plugins(self, agent_id: str) -> Optional[List[str]]:
        """Return the configured plugin id list for an agent.

        Returns the configured list, or ``None`` to indicate that all
        plugins are enabled for this agent.
        """

        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("agent_id must be a non-empty string")
        if agent_id not in self._agent_base_configs:
            raise KeyError(f"Unknown agent_id {agent_id!r}")

        value = self._agent_plugin_ids.get(agent_id)
        return value if value is not None else None

    def list_plugins(self) -> List[Dict[str, Any]]:
        """Return metadata for all available plugins.

        Entries are ordered by kind and then by configuration order.
        """

        result: List[Dict[str, Any]] = []
        for kind in ("providers", "extensions", "features", "tools"):
            for plugin_class in self._plugin_classes.get(kind) or []:
                plugin_id = self._plugin_id_for_class(plugin_class)
                entry: Dict[str, Any] = {
                    "kind": kind,
                    "id": plugin_id,
                    "class_path": f"{plugin_class.__module__}.{plugin_class.__qualname__}",
                    "class_name": plugin_class.__name__,
                }
                name_attr = getattr(plugin_class, "name", None)
                if isinstance(name_attr, str) and name_attr:
                    entry["name"] = name_attr
                result.append(entry)
        return result

    # ------------------------------------------------------------------
    # Application-level plugins (actions + UI schema)
    # ------------------------------------------------------------------

    def list_application_plugins(self) -> List[Dict[str, Any]]:
        """Return metadata for all registered application-level plugins.

        Entries are ordered by configuration order.
        """

        result: List[Dict[str, Any]] = []
        for plugin_id, wrapper in self._app_plugins.items():
            plugin_class = wrapper.plugin_class
            entry: Dict[str, Any] = {
                "id": plugin_id,
                "class_path": f"{plugin_class.__module__}.{plugin_class.__qualname__}",
                "class_name": plugin_class.__name__,
            }
            name_attr = getattr(plugin_class, "name", None)
            if isinstance(name_attr, str) and name_attr:
                entry["name"] = name_attr
            result.append(entry)
        return result

    def get_application_actions(self) -> List[Dict[str, Any]]:
        """Return all application-level action definitions.

        Each returned action dictionary includes a ``"plugin"`` field naming
        the contributing plugin.
        """

        actions: List[Dict[str, Any]] = []
        for plugin_id, wrapper in self._app_plugins.items():
            for raw_action in wrapper.get_actions():
                if not isinstance(raw_action, dict):
                    continue
                if "plugin" in raw_action and isinstance(raw_action["plugin"], str):
                    actions.append(raw_action)
                else:
                    action = dict(raw_action)
                    action["plugin"] = plugin_id
                    actions.append(action)
        return actions

    def get_application_ui_schema(self) -> List[Dict[str, Any]]:
        """Return flattened UI schema elements from application plugins.

        Each element is normalized to include a ``"plugin"`` field naming
        the contributing plugin.
        """

        elements: List[Dict[str, Any]] = []
        for plugin_id, wrapper in self._app_plugins.items():
            for raw_element in wrapper.get_ui_elements():
                if not isinstance(raw_element, dict):
                    continue
                if "plugin" in raw_element and isinstance(raw_element["plugin"], str):
                    elements.append(raw_element)
                else:
                    element = dict(raw_element)
                    element["plugin"] = plugin_id
                    elements.append(element)
        return elements

    # Internal helpers for action validation ---------------------------------

    class _ApplicationActionValidationError(Exception):
        """Internal exception used for application action input validation.

        Carries a ``details`` mapping suitable for surfacing in higher-level
        error envelopes.
        """

        def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
            super().__init__(message)
            self.details: Dict[str, Any] = details or {}

    def _find_application_action_definition(
        self,
        plugin_id: str,
        action_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Return the action definition for ``(plugin_id, action_id)`` if present."""

        for action in self.get_application_actions():
            if not isinstance(action, dict):
                continue
            if action.get("plugin") == plugin_id and action.get("id") == action_id:
                return action
        return None

    @staticmethod
    def _action_param_type_matches(value: Any, expected_type: str) -> bool:
        """Return True when ``value`` matches the declared primitive type.

        Supported types are ``string``, ``integer``, ``number``, and
        ``boolean``. Unknown types are treated as "accept any" so that
        application plugins can experiment with richer parameter types
        without breaking validation.
        """

        if expected_type == "string":
            return isinstance(value, str)
        if expected_type == "integer":
            # ``bool`` is a subclass of ``int``; treat it separately.
            return isinstance(value, int) and not isinstance(value, bool)
        if expected_type == "number":
            return (isinstance(value, (int, float)) and not isinstance(value, bool))
        if expected_type == "boolean":
            return isinstance(value, bool)
        return True

    def _validate_action_inputs(
        self,
        action_def: Dict[str, Any],
        raw_inputs: Any,
    ) -> Dict[str, Any]:
        """Validate and normalize inputs for an application-level action.

        Returns the validated mapping or raises
        :class:`_ApplicationActionValidationError`.
        """

        schema = action_def.get("inputs") or {}
        if not isinstance(schema, dict):
            schema = {}

        if raw_inputs is None:
            inputs: Dict[str, Any] = {}
        elif isinstance(raw_inputs, dict):
            inputs = raw_inputs
        else:
            raise self._ApplicationActionValidationError(
                "inputs must be an object mapping parameter names to values",
                {"reason": "inputs_type", "actual_type": type(raw_inputs).__name__},
            )

        validated: Dict[str, Any] = {}
        missing: List[str] = []
        invalid_types: Dict[str, Dict[str, Any]] = {}

        for name, spec in schema.items():
            if not isinstance(spec, dict):
                continue

            param_type = spec.get("type")
            required = bool(spec.get("required", False))
            has_value = name in inputs
            value = inputs.get(name)

            if not has_value or value is None:
                if "default" in spec:
                    validated[name] = spec["default"]
                elif required:
                    missing.append(name)
                continue

            if isinstance(param_type, str):
                if not self._action_param_type_matches(value, param_type):
                    invalid_types[name] = {
                        "expected": param_type,
                        "actual_type": type(value).__name__,
                    }
                else:
                    validated[name] = value
            else:
                validated[name] = value

        extra = [name for name in inputs.keys() if name not in schema]

        if missing or invalid_types or extra:
            details: Dict[str, Any] = {}
            if missing:
                details["missing_params"] = missing
            if invalid_types:
                details["invalid_types"] = invalid_types
            if extra:
                details["extra_params"] = extra

            raise self._ApplicationActionValidationError(
                "action input validation failed", details
            )

        return validated

    def execute_application_action(
        self,
        plugin_id: str,
        action_id: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute an application-level action.

        This helper validates that the plugin, action id, and inputs are
        valid and then delegates execution to the corresponding application
        plugin wrapper.
        """

        if not isinstance(plugin_id, str) or not plugin_id:
            raise ValueError("plugin_id must be a non-empty string")
        if not isinstance(action_id, str) or not action_id:
            raise ValueError("action_id must be a non-empty string")
        if not isinstance(params, dict):
            raise ValueError("params must be a mapping of action inputs")

        wrapper = self._app_plugins.get(plugin_id)
        if wrapper is None:
            raise KeyError(f"Unknown application plugin {plugin_id!r}")

        action_def = self._find_application_action_definition(plugin_id, action_id)
        if action_def is None:
            raise KeyError(f"Unknown action_id {action_id!r} for plugin {plugin_id!r}")

        validated_inputs = self._validate_action_inputs(action_def, params)

        return wrapper.execute_action(self, action_id, validated_inputs)

    def load_session(
        self, session_id: str
    ) -> Optional[Tuple[AgentCore, Dict[str, Any], Session]]:
        """Load a session and return ``(core, base_config, session)`` or ``None``.

        A fresh :class:`AgentCore` instance is constructed for each call so
        that per-agent plugin configuration can be applied cleanly.
        """

        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        session = self._session_store.load(session_id)
        if session is None:
            return None

        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        agent_id = metadata.get("agent_id")
        if not isinstance(agent_id, str) or not agent_id:
            raise RuntimeError("session.metadata must contain non-empty 'agent_id'")

        base_cfg = self._get_agent_base_config(agent_id)

        plugins_from_session = metadata.get("plugins")
        if isinstance(plugins_from_session, list):
            enabled_ids = [p for p in plugins_from_session if isinstance(p, str)]
        else:
            enabled_ids = self._agent_plugin_ids.get(agent_id)

        # TODO: Instead of bulding a new core, add the enabled_ids to the config
        core = self._build_core_with_enabled_ids(enabled_ids)
        return core, base_cfg, session

    def load_session_record(self, session_id: str) -> Optional[Session]:
        """Load a session from the underlying store.

        Unlike :meth:`load_session`, this does not require resolving the
        session's ``agent_id`` to a configured agent.
        """

        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        return self._session_store.load(session_id)

    def save_session(self, session: Session) -> None:
        """Persist a session using the configured session store."""

        self._session_store.save(session)

    def delete_session(self, session_id: str) -> None:
        """Delete a session from the store (no-op if missing)."""

        self._session_store.delete(session_id)

    def create_session(self, agent_id: str) -> Tuple[AgentCore, Dict[str, Any], Session]:
        """Create and persist a new empty session for the given agent.

        Returns a tuple of ``(core, base_config, session)`` where ``core`` is a
        freshly configured :class:`AgentCore` instance and ``base_config`` is
        the provider configuration for the agent before per-request overrides.
        """

        core, base_cfg, session = self.create_session_ephemeral(agent_id)
        self._session_store.save(session)
        return core, base_cfg, session

    def create_session_ephemeral(self, agent_id: str) -> Tuple[AgentCore, Dict[str, Any], Session]:
        """Create a new empty session for the given agent without persisting it.

        This helper mirrors :meth:`create_session` but does not write the
        session to the configured session store. Callers are responsible for
        explicitly persisting the session via :meth:`save_session` once
        meaningful content has been added.
        """

        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("agent_id must be a non-empty string")

        base_cfg = self._get_agent_base_config(agent_id)
        enabled_ids = self._agent_plugin_ids.get(agent_id)
        core = self._build_core_with_enabled_ids(enabled_ids)

        base = core.create_session()
        session = Session(
            session_id=base.session_id,
            messages=base.messages,
            metadata={"agent_id": agent_id},
        )

        return core, base_cfg, session

    def update_agent(self, agent_id: str, session: Session) -> Tuple[AgentCore, Dict[str, Any], Session]:
        """Reconfigure core/base_config for ``agent_id`` and update session metadata.

        This does not persist the session; callers are responsible for deciding
        when to save. The returned session keeps the same ``session_id`` and
        ``messages`` as the input, with only ``metadata['agent_id']`` updated.
        """

        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("agent_id must be a non-empty string")

        base_cfg = self._get_agent_base_config(agent_id)
        enabled_ids = self._agent_plugin_ids.get(agent_id)
        core = self._build_core_with_enabled_ids(enabled_ids)

        metadata = session.metadata or {}
        new_metadata = {**metadata, "agent_id": agent_id}
        new_session = Session(
            session_id=session.session_id,
            messages=session.messages,
            metadata=new_metadata,
        )
        return core, base_cfg, new_session

    # ------------------------------------------------------------------
    # Core-first request API (new architecture)
    # ------------------------------------------------------------------

    def send_request(
        self,
        core: AgentCore,
        session: Session,
        base_config: Dict[str, Any],
        overrides: Optional[Dict[str, Any]] = None,
        *,
        stream: bool = False,
        request_id: Optional[str] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Core-first request API that yields events.

        This method is the *new* request entry point, corresponding to the
        original :meth:`send_request` method in
        the original application-layer ``send_request`` implementation but implemented as a
        generator over typed events instead of a dict-based one-shot call.

        Key differences from the legacy API:

        - Persistence is the responsibility of the caller
        - The caller decides whether and how to expose events externally
        - Tool loops are handled internally, with a configurable maximum
          depth (:class:`_ToolLoopConfig`).
        """

        config = resolve_request_config(base_config, overrides or {})
        rid = request_id or self._new_request_id()

        def _is_cancelled() -> bool:
            return rid in self._cancelled_requests

        # Initial request_started event
        yield {
            "type": "request_started",
            "session_id": session.session_id,
            "request_id": rid,
            "stream": bool(stream),
        }

        loop_runner = ToolLoopRunner(
            core=core,
            config=config,
            request_id=rid,
            tool_loop_cfg=self._tool_loop_cfg,
            cancel_callback=_is_cancelled,
        )

        try:
            yield from loop_runner.run(session=session, stream=stream)
        finally:
            self._cancelled_requests.discard(rid)
