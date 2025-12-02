from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple
import uuid

from agent_core import AgentCore, MessageRole, Session

from .config import (
    build_agent_config,
    load_plugins,
    load_raw_config,
    resolve_placeholders,
    resolve_request_config,
)
from .sessions import FilesystemSessionStore
from .tool_loop import ToolLoopRunner


@dataclass(frozen=True)
class _ToolLoopConfig:
    """Configuration for the built-in tool loop.

    Kept aligned with the original application-layer behaviour so that
    implementations can be compared side-by-side with a diff.
    """

    max_loops: int = 8


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
    ) -> None:
        # Core factory is stored so that per-session cores can be created
        # without sharing state across requests.
        self._core_factory = core_factory

        # A single core instance is still used for import/export with the
        # filesystem session store; inference uses fresh cores created via
        # ``_new_core``.
        core = core_factory()
        self._core = core

        raw_config = load_raw_config(config_path)
        resolved_config, placeholder_errors = resolve_placeholders(raw_config)
        self._config: Dict[str, Any] = resolved_config
        self._config_errors: List[Dict[str, Any]] = list(placeholder_errors)

        plugins_cfg = resolved_config.get("plugins") or {}
        plugin_classes, plugin_errors = load_plugins(plugins_cfg)
        self._plugin_classes: Dict[str, List[type[Any]]] = plugin_classes
        self._config_errors.extend(plugin_errors)

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

        self._session_store = FilesystemSessionStore(Path(session_root), core)
        self._tool_loop_cfg = _ToolLoopConfig()

        # Cache per-agent base configs to avoid recomputing on every call.
        agents = resolved_config.get("agents") or {}
        self._agent_base_configs: Dict[str, Dict[str, Any]] = {}
        for agent_id in agents.keys():
            self._agent_base_configs[agent_id] = build_agent_config(resolved_config, agent_id)

    # ------------------------------------------------------------------
    # Helper methods (kept in the same order as application.AgentApplication)
    # ------------------------------------------------------------------

    def _new_request_id(self) -> str:
        return str(uuid.uuid4())

    def _get_agent_base_config(self, agent_id: str) -> Dict[str, Any]:
        cfg = self._agent_base_configs.get(agent_id)
        if cfg is None:
            cfg = build_agent_config(self._config, agent_id)
            self._agent_base_configs[agent_id] = cfg
        return cfg

    def _new_core(self) -> AgentCore:
        """Construct a fresh :class:`AgentCore` instance with all plugins.

        This mirrors the original application-layer implementation but is
        used exclusively by the typed helpers and the new request API in
        this module.
        """

        core = self._core_factory()
        provider_exts = self._plugin_classes.get("extensions") or []
        for provider_cls in self._plugin_classes.get("providers") or []:
            core.register_provider(provider_cls, extensions=provider_exts)
        for feature_cls in self._plugin_classes.get("features") or []:
            core.register_feature(feature_cls)
        for tool_cls in self._plugin_classes.get("tools") or []:
            core.register_tool(tool_cls)
        return core

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
        """Return a copy of configuration and plugin loading errors."""

        return list(self._config_errors)

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
        core = self._new_core()
        return core, base_cfg, session

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

        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("agent_id must be a non-empty string")

        base_cfg = self._get_agent_base_config(agent_id)
        core = self._new_core()

        base = core.create_session()
        session = Session(
            session_id=base.session_id,
            messages=list(base.messages),
            metadata={"agent_id": agent_id},
        )
        self._session_store.save(session)
        return core, base_cfg, session

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
        )

        yield from loop_runner.run(session=session, stream=stream)
