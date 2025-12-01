from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple, Iterator
import threading
import time
import uuid


from agent_core import AgentCore, Session, MessageRole

from .config import (
    load_raw_config,
    resolve_placeholders,
    build_agent_config,
    resolve_request_config,
    load_plugins,
)
from .sessions import FilesystemSessionStore
from .events import EventStore, InMemoryEventStore


@dataclass(frozen=True)
class _ToolLoopConfig:
    max_loops: int = 8


class AgentApplication:
    """High-level application layer around :class:`agent_core.AgentCore`.

    This class owns a single :class:`AgentCore` instance, filesystem-backed
    session persistence, and an event store used for streaming and tool
    execution events. All public methods are dict-based to mirror typical
    HTTP/JSON APIs.
    """

    def __init__(
        self,
        config_path: str | Path,
        session_root: str | Path,
        core_factory: Callable[[], AgentCore] = AgentCore,
        *,
        event_store: Optional[EventStore] = None,
    ) -> None:
        self._core = core_factory()

        raw_config = load_raw_config(config_path)
        resolved_config, placeholder_errors = resolve_placeholders(raw_config)
        self._config: Dict[str, Any] = resolved_config
        self._config_errors: List[Dict[str, Any]] = list(placeholder_errors)

        plugins_cfg = resolved_config.get("plugins") or {}
        plugin_classes, plugin_errors = load_plugins(plugins_cfg)
        self._config_errors.extend(plugin_errors)

        # Manual registration from config: providers with shared extensions,
        # then features and tools.
        provider_exts = plugin_classes.get("extensions") or []
        for provider_cls in plugin_classes.get("providers") or []:
            self._core.register_provider(provider_cls, extensions=provider_exts)
        for feature_cls in plugin_classes.get("features") or []:
            self._core.register_feature(feature_cls)
        for tool_cls in plugin_classes.get("tools") or []:
            self._core.register_tool(tool_cls)

        self._session_store = FilesystemSessionStore(Path(session_root), self._core)
        self._event_store: EventStore = event_store or InMemoryEventStore()
        self._tool_loop_cfg = _ToolLoopConfig()

        # Cache per-agent base configs to avoid recomputing on every call.
        agents = resolved_config.get("agents") or {}
        self._agent_base_configs: Dict[str, Dict[str, Any]] = {}
        for agent_id in agents.keys():
            self._agent_base_configs[agent_id] = build_agent_config(resolved_config, agent_id)

        self._bg_lock = threading.Lock()
        self._bg_threads: Dict[str, threading.Thread] = {}

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _new_request_id(self) -> str:
        return str(uuid.uuid4())

    def _get_agent_base_config(self, agent_id: str) -> Dict[str, Any]:
        cfg = self._agent_base_configs.get(agent_id)
        if cfg is None:
            cfg = build_agent_config(self._config, agent_id)
            self._agent_base_configs[agent_id] = cfg
        return cfg

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

    def _append_tool_messages(self, session: Session, tool_messages: List[Dict[str, Any]]) -> Session:
        current = session
        for msg in tool_messages:
            raw_role = msg.get("role", "tool")
            # Coerce arbitrary roles to the allowed MessageRole literals.
            role: MessageRole
            if raw_role in ("system", "user", "assistant", "tool"):
                role = raw_role  # type: ignore[assignment]
            else:
                role = "tool"  # type: ignore[assignment]
            content = msg.get("content", "")
            metadata = msg.get("metadata")
            current = self._core.add_message(current, role, content, metadata)
        return current

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
    # Public helpers for tests: manual registration
    # ------------------------------------------------------------------

    def register_provider(self, plugin_class: type, extensions: Optional[List[type]] = None) -> None:
        self._core.register_provider(plugin_class, extensions=extensions or [])

    def register_feature(self, plugin_class: type) -> None:
        self._core.register_feature(plugin_class)

    def register_tool(self, plugin_class: type) -> None:
        self._core.register_tool(plugin_class)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_session(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new session for a given agent and persist it.

        Payload:
            {"agent_id": str}

        Returns:
            {"session": Session.to_dict(), "errors": list[dict]}
        """

        agent_id = payload.get("agent_id")
        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("payload must include non-empty 'agent_id' string")

        # Validate agent exists
        _ = self._get_agent_base_config(agent_id)

        base = self._core.create_session()
        session = Session(session_id=base.session_id, messages=list(base.messages), metadata={"agent_id": agent_id})
        self._session_store.save(session)
        return {"session": session.to_dict(), "errors": list(self._config_errors)}

    def add_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Append a message to an existing session and persist it.

        Payload:
            {
                "session_id": str,
                "message": {"role": str, "content": str, "metadata"?: dict},
            }
        """

        session_id = payload.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("payload must include non-empty 'session_id' string")

        raw_msg = payload.get("message") or {}
        role_value = raw_msg.get("role")
        content = raw_msg.get("content")
        metadata = raw_msg.get("metadata")
        if not isinstance(role_value, str) or not isinstance(content, str):
            raise ValueError("message must include 'role' and 'content' strings")

        # Coerce to a valid MessageRole literal; default to "user".
        if role_value not in ("system", "user", "assistant", "tool"):
            role_value = "user"
        role: MessageRole = role_value  # type: ignore[assignment]

        session = self._load_session_required(session_id)
        new_session = self._core.add_message(session, role, content, metadata)
        self._session_store.save(new_session)
        return {"session": new_session.to_dict()}

    def send_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request using the current session state.

        Payload keys:
            - "session_id": str (required)
            - "config_overrides"?: dict
            - "stream"?: bool (default False)

        Non-streaming:
            Returns {"session": ..., "messages": [...], "request_id": str}
        Streaming:
            Starts a background task and returns immediately with
            {"session_id": ..., "request_id": str, "stream": true, "status": "started"}.
        """

        session_id = payload.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("payload must include non-empty 'session_id' string")

        stream = bool(payload.get("stream"))
        overrides = payload.get("config_overrides") or {}
        if overrides is not None and not isinstance(overrides, dict):
            raise ValueError("config_overrides must be a mapping if provided")

        request_id = self._new_request_id()
        session = self._load_session_required(session_id)
        agent_id = session.metadata.get("agent_id")
        if not isinstance(agent_id, str) or not agent_id:
            raise RuntimeError("session.metadata must contain non-empty 'agent_id'")

        base_cfg = self._get_agent_base_config(agent_id)
        config = resolve_request_config(base_cfg, overrides)

        if not stream:
            self._event_store.publish(
                {
                    "type": "request_started",
                    "session_id": session_id,
                    "request_id": request_id,
                    "stream": False,
                }
            )
            final_session, final_messages = self._run_non_streaming_request(session, config, request_id)
            return {
                "session": final_session.to_dict(),
                "messages": final_messages,
                "request_id": request_id,
            }

        # Streaming: run in background
        self._event_store.publish(
            {
                "type": "request_started",
                "session_id": session_id,
                "request_id": request_id,
                "stream": True,
            }
        )
        thread = threading.Thread(
            target=self._run_streaming_request,
            args=(session_id, config, request_id),
            daemon=True,
        )
        with self._bg_lock:
            self._bg_threads[request_id] = thread
        thread.start()
        return {
            "session_id": session_id,
            "request_id": request_id,
            "stream": True,
            "status": "started",
        }

    def get_events(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """List events for polling-based consumers.

        Payload keys (all optional):
            - "since_id"?: str
            - "request_id"?: str
            - "session_id"?: str
            - "limit"?: int
        """

        since_id = payload.get("since_id")
        request_id = payload.get("request_id")
        session_id = payload.get("session_id")
        limit = payload.get("limit")
        if limit is None:
            limit = 100
        return {
            "events": self._event_store.list(
                since_id=str(since_id) if since_id is not None else None,
                request_id=request_id,
                session_id=session_id,
                limit=int(limit),
            )
        }

    def stream_events(self, payload: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Stream events from the store, optionally following new ones.

        This is a convenience wrapper around :meth:`get_events` that turns the
        polling API into a streaming-style iterator for consumers.

        Payload keys:
            - "since_id"?: str
            - "request_id"?: str
            - "session_id"?: str
            - "limit"?: int (per batch, default 100)
            - "follow"?: bool (default False). When True, the iterator will
              continue polling for new events until the caller breaks.
            - "poll_interval"?: float (seconds between polls when following,
              default 0.05).
        """

        since_id = payload.get("since_id")
        request_id = payload.get("request_id")
        session_id = payload.get("session_id")
        limit = payload.get("limit")
        follow = bool(payload.get("follow"))
        poll_interval = float(payload.get("poll_interval", 0.05))

        if limit is None:
            limit = 100

        def _next_batch(current_since: Optional[str]) -> tuple[Optional[str], List[Dict[str, Any]]]:
            batch = self.get_events(
                {
                    "since_id": current_since,
                    "request_id": request_id,
                    "session_id": session_id,
                    "limit": limit,
                }
            )["events"]
            if not batch:
                return current_since, []
            return batch[-1]["event_id"], batch

        # Single-shot mode: fetch one batch and yield it.
        if not follow:
            _new_since, batch = _next_batch(since_id)
            for ev in batch:
                yield ev
            return

        # Follow mode: keep polling until caller stops iteration.
        current_since = since_id
        while True:
            current_since, batch = _next_batch(current_since)
            if batch:
                for ev in batch:
                    yield ev
            else:
                time.sleep(poll_interval)

    # ------------------------------------------------------------------
    # Internal request runners
    # ------------------------------------------------------------------

    def _run_non_streaming_request(
        self,
        session: Session,
        config: Dict[str, Any],
        request_id: str,
    ) -> Tuple[Session, List[Dict[str, Any]]]:
        """Run a full non-streaming request including tool loop."""

        current_session = session
        final_messages: List[Dict[str, Any]] = []
        loops = 0

        # Handle any pending tool_calls already present in the session history
        # before issuing the first LLM call.
        pending = self._extract_pending_tool_calls_from_session(current_session)
        if pending:
            loops += 1
            if loops > self._tool_loop_cfg.max_loops:
                self._event_store.publish(
                    {
                        "type": "error",
                        "session_id": current_session.session_id,
                        "request_id": request_id,
                        "detail": "Max tool loop depth exceeded",
                    }
                )
            else:
                self._event_store.publish(
                    {
                        "type": "tool_calls",
                        "session_id": current_session.session_id,
                        "request_id": request_id,
                        "tool_calls": list(pending),
                    }
                )
                tool_messages = self._core.execute_tool_calls(pending, config)
                self._event_store.publish(
                    {
                        "type": "tool_results",
                        "session_id": current_session.session_id,
                        "request_id": request_id,
                        "messages": list(tool_messages),
                    }
                )
                current_session = self._append_tool_messages(current_session, tool_messages)
                self._session_store.save(current_session)

        while True:
            current_session, final_messages = self._core.send_request(current_session, config)
            self._session_store.save(current_session)

            self._event_store.publish(
                {
                    "type": "final",
                    "session_id": current_session.session_id,
                    "request_id": request_id,
                    "messages": list(final_messages),
                    "session": current_session.to_dict(),
                }
            )

            tool_calls = self._extract_tool_calls(final_messages)
            if not tool_calls:
                break

            loops += 1
            if loops > self._tool_loop_cfg.max_loops:
                self._event_store.publish(
                    {
                        "type": "error",
                        "session_id": current_session.session_id,
                        "request_id": request_id,
                        "detail": "Max tool loop depth exceeded",
                    }
                )
                break

            self._event_store.publish(
                {
                    "type": "tool_calls",
                    "session_id": current_session.session_id,
                    "request_id": request_id,
                    "tool_calls": list(tool_calls),
                }
            )

            tool_messages = self._core.execute_tool_calls(tool_calls, config)
            self._event_store.publish(
                {
                    "type": "tool_results",
                    "session_id": current_session.session_id,
                    "request_id": request_id,
                    "messages": list(tool_messages),
                }
            )

            current_session = self._append_tool_messages(current_session, tool_messages)
            self._session_store.save(current_session)

        self._event_store.publish(
            {
                "type": "request_completed",
                "session_id": current_session.session_id,
                "request_id": request_id,
            }
        )
        return current_session, final_messages

    def _stream_llm_phase(
        self,
        session: Session,
        config: Dict[str, Any],
        request_id: str,
    ) -> Tuple[Session, List[Dict[str, Any]]]:
        """Stream one LLM phase and publish partial/final events."""

        final_session = session
        final_messages: List[Dict[str, Any]] = []

        for chunk in self._core.send_request_stream(session, config):
            if chunk.get("type") == "partial":
                self._event_store.publish(
                    {
                        "type": "partial",
                        "session_id": session.session_id,
                        "request_id": request_id,
                        "message": chunk["message"],
                    }
                )
            elif chunk.get("type") == "final":
                final_session = chunk["session"]
                final_messages = list(chunk.get("messages") or [])
                self._session_store.save(final_session)
                self._event_store.publish(
                    {
                        "type": "final",
                        "session_id": final_session.session_id,
                        "request_id": request_id,
                        "messages": list(final_messages),
                        "session": final_session.to_dict(),
                    }
                )

        return final_session, final_messages

    def _run_streaming_request(
        self,
        session_id: str,
        config: Dict[str, Any],
        request_id: str,
    ) -> None:
        """Background worker for streaming send_request with tool loop."""

        try:
            session = self._load_session_required(session_id)
            current_session = session
            loops = 0

            # Handle any pending tool_calls already in the session before
            # initiating streaming.
            pending = self._extract_pending_tool_calls_from_session(current_session)
            if pending:
                loops += 1
                if loops > self._tool_loop_cfg.max_loops:
                    self._event_store.publish(
                        {
                            "type": "error",
                            "session_id": current_session.session_id,
                            "request_id": request_id,
                            "detail": "Max tool loop depth exceeded",
                        }
                    )
                else:
                    self._event_store.publish(
                        {
                            "type": "tool_calls",
                            "session_id": current_session.session_id,
                            "request_id": request_id,
                            "tool_calls": list(pending),
                        }
                    )
                    tool_messages = self._core.execute_tool_calls(pending, config)
                    self._event_store.publish(
                        {
                            "type": "tool_results",
                            "session_id": current_session.session_id,
                            "request_id": request_id,
                            "messages": list(tool_messages),
                        }
                    )
                    current_session = self._append_tool_messages(current_session, tool_messages)
                    self._session_store.save(current_session)

            current_session, final_messages = self._stream_llm_phase(current_session, config, request_id)

            while True:
                tool_calls = self._extract_tool_calls(final_messages)
                if not tool_calls:
                    break

                loops += 1
                if loops > self._tool_loop_cfg.max_loops:
                    self._event_store.publish(
                        {
                            "type": "error",
                            "session_id": current_session.session_id,
                            "request_id": request_id,
                            "detail": "Max tool loop depth exceeded",
                        }
                    )
                    break

                self._event_store.publish(
                    {
                        "type": "tool_calls",
                        "session_id": current_session.session_id,
                        "request_id": request_id,
                        "tool_calls": list(tool_calls),
                    }
                )

                tool_messages = self._core.execute_tool_calls(tool_calls, config)
                self._event_store.publish(
                    {
                        "type": "tool_results",
                        "session_id": current_session.session_id,
                        "request_id": request_id,
                        "messages": list(tool_messages),
                    }
                )

                current_session = self._append_tool_messages(current_session, tool_messages)
                self._session_store.save(current_session)

                current_session, final_messages = self._stream_llm_phase(
                    current_session, config, request_id
                )

        except Exception as exc:  # pragma: no cover - defensive
            self._event_store.publish(
                {
                    "type": "error",
                    "session_id": session_id,
                    "request_id": request_id,
                    "detail": str(exc),
                }
            )
        finally:
            self._event_store.publish(
                {
                    "type": "request_completed",
                    "session_id": session_id,
                    "request_id": request_id,
                }
            )
            with self._bg_lock:
                self._bg_threads.pop(request_id, None)
