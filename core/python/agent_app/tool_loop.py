from __future__ import annotations

from typing import Any, Dict, Iterator, List, Tuple

from agent_core import AgentCore, MessageRole, Session


class ToolLoopRunner:
    """Run the application-layer tool loop for a single request.

    A new instance is created for each request/loop and discarded once the
    loop finishes, either successfully or with an error. The implementation
    is extracted from :meth:`AgentApplication.send_request` so that the
    application class can delegate tool-handling concerns to this helper.
    """

    def __init__(
        self,
        *,
        core: AgentCore,
        config: Dict[str, Any],
        request_id: str,
        tool_loop_cfg: Any,
    ) -> None:
        self._core = core
        self._config = config
        self._request_id = request_id
        self._tool_loop_cfg = tool_loop_cfg

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

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

        last_tc_index: int | None = None
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

    def _run_llm_phase(
        self,
        session: Session,
        *,
        stream: bool,
    ) -> Tuple[Session, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Run a single LLM phase and return (session, messages, events).

        The outer tool loop is shared for streaming and non-streaming; this
        helper handles the per-phase differences in how events are produced.
        """

        core = self._core
        config = self._config
        rid = self._request_id

        if not stream:
            next_session, final_messages = core.send_request(session, config)
            events = [
                {
                    "type": "final",
                    "session_id": next_session.session_id,
                    "request_id": rid,
                    "messages": list(final_messages),
                    "session": next_session.to_dict(),
                }
            ]
            return next_session, list(final_messages), events

        # Streaming: accumulate partial and final events from send_request_stream
        current_session = session
        final_session = session
        final_messages: List[Dict[str, Any]] = []
        events: List[Dict[str, Any]] = []

        for chunk in core.send_request_stream(session, config):
            if chunk.get("type") == "partial":
                events.append(
                    {
                        "type": "partial",
                        "session_id": current_session.session_id,
                        "request_id": rid,
                        "message": chunk["message"],
                    }
                )
            elif chunk.get("type") == "final":
                final_session = chunk["session"]
                final_messages = list(chunk.get("messages") or [])
                events.append(
                    {
                        "type": "final",
                        "session_id": final_session.session_id,
                        "request_id": rid,
                        "messages": list(final_messages),
                        "session": final_session.to_dict(),
                    }
                )

        return final_session, final_messages, events

    def _apply_tool_calls(
        self,
        session: Session,
        tool_calls: List[Dict[str, Any]],
    ) -> Tuple[Session, List[Dict[str, Any]]]:
        """Execute tool calls and return (new_session, events)."""

        core = self._core
        config = self._config
        rid = self._request_id

        # Record the tool_calls event first
        events: List[Dict[str, Any]] = [
            {
                "type": "tool_calls",
                "session_id": session.session_id,
                "request_id": rid,
                "tool_calls": list(tool_calls),
            }
        ]

        tool_messages = core.execute_tool_calls(tool_calls, config)
        current_session = session
        for msg in tool_messages:
            raw_role = msg.get("role", "tool")
            role: MessageRole
            if raw_role in ("system", "user", "assistant", "tool"):
                role = raw_role  # type: ignore[assignment]
            else:
                role = "tool"  # type: ignore[assignment]
            content = msg.get("content", "")
            metadata = msg.get("metadata")
            current_session = core.add_message(current_session, role, content, metadata)

        events.append(
            {
                "type": "tool_results",
                "session_id": current_session.session_id,
                "request_id": rid,
                "messages": list(tool_messages),
                "session": current_session.to_dict(),
            }
        )

        return current_session, events

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, session: Session, *, stream: bool) -> Iterator[Dict[str, Any]]:
        """Execute the full tool loop, yielding application-layer events.

        Streaming and non-streaming follow the same outer control flow; the
        per-phase differences are handled by :meth:`_run_llm_phase`.
        """

        current_session = session
        loops = 0
        max_loops = int(getattr(self._tool_loop_cfg, "max_loops", 8))

        # Handle any pending tool_calls already present in the session history
        # before issuing the first LLM call.
        pending = self._extract_pending_tool_calls_from_session(current_session)
        if pending:
            loops += 1
            if loops > max_loops:
                yield {
                    "type": "error",
                    "session_id": current_session.session_id,
                    "request_id": self._request_id,
                    "detail": "Max tool loop depth exceeded",
                }
                yield {
                    "type": "request_completed",
                    "session_id": current_session.session_id,
                    "request_id": self._request_id,
                }
                return

            current_session, events = self._apply_tool_calls(current_session, pending)
            for ev in events:
                yield ev

        # Main LLM + tool loop
        while True:
            final_session, final_messages, phase_events = self._run_llm_phase(
                current_session, stream=stream
            )
            for ev in phase_events:
                yield ev

            current_session = final_session

            tool_calls = self._extract_tool_calls(final_messages)
            if not tool_calls:
                break

            loops += 1
            if loops > max_loops:
                yield {
                    "type": "error",
                    "session_id": current_session.session_id,
                    "request_id": self._request_id,
                    "detail": "Max tool loop depth exceeded",
                }
                break

            current_session, events = self._apply_tool_calls(current_session, tool_calls)
            for ev in events:
                yield ev

        yield {
            "type": "request_completed",
            "session_id": current_session.session_id,
            "request_id": self._request_id,
        }
