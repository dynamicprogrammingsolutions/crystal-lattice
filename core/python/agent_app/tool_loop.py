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
        cancel_callback: Any | None = None,
    ) -> None:
        self._core = core
        self._config = config
        self._request_id = request_id
        self._tool_loop_cfg = tool_loop_cfg
        self._cancel_callback = cancel_callback


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

    def _is_cancelled(self) -> bool:
        cb = getattr(self, "_cancel_callback", None)
        if cb is None:
            return False
        try:
            return bool(cb())
        except Exception:
            return False

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
            if self._is_cancelled():
                events = [
                    {
                        "type": "request_cancelled",
                        "session_id": session.session_id,
                        "request_id": rid,
                    }
                ]
                return session, [], events

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
            if self._is_cancelled():
                events.append(
                    {
                        "type": "request_cancelled",
                        "session_id": current_session.session_id,
                        "request_id": rid,
                    }
                )
                return current_session, [], events

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
        *,
        stream_tools: bool,
    ) -> Iterator[Dict[str, Any]]:
        """Execute tool calls and yield events.

        Uses :meth:`AgentCore.iter_tool_messages` as the underlying API.
        When ``stream_tools`` is True, partial payloads are emitted as
        ``tool_partial`` events before the final ``tool_results`` summary.
        The updated session is returned via ``StopIteration.value``.
        """

        core = self._core
        config = self._config
        rid = self._request_id

        current_session = session

        # Record the tool_calls event first
        yield {
            "type": "tool_calls",
            "session_id": current_session.session_id,
            "request_id": rid,
            "tool_calls": list(tool_calls),
        }

        tool_messages: List[Dict[str, Any]] = []

        for call in tool_calls:
            call_id = call.get("id") or call.get("tool_call_id")
            last_final: Dict[str, Any] | None = None

            for item in core.iter_tool_messages([call], config):
                if not isinstance(item, dict):
                    continue
                if "part" in item:
                    if stream_tools:
                        yield {
                            "type": "tool_partial",
                            "session_id": current_session.session_id,
                            "request_id": rid,
                            "tool_call_id": call_id,
                            "payload": item,
                        }
                    continue
                last_final = item

            if last_final is None:
                # iter_tool_messages already synthesizes errors for missing tools,
                # but guard defensively in case it yields nothing.
                func = call.get("function") or {}
                name = call.get("name") or (
                    func.get("name") if isinstance(func, dict) else None
                )
                metadata: Dict[str, Any] = {
                    "tool_call_id": call_id,
                    "tool_name": name,
                }
                last_final = {
                    "role": "tool",
                    "content": f"Error: no tool handled '{name}'",
                    "metadata": metadata,
                }

            tool_messages.append(last_final)

            raw_role = last_final.get("role", "tool")
            role: MessageRole
            if raw_role in ("system", "user", "assistant", "tool"):
                role = raw_role  # type: ignore[assignment]
            else:
                role = "tool"  # type: ignore[assignment]
            content = last_final.get("content", "")
            metadata = last_final.get("metadata")
            current_session = core.add_message(current_session, role, content, metadata)

        yield {
            "type": "tool_results",
            "session_id": current_session.session_id,
            "request_id": rid,
            "messages": list(tool_messages),
            "session": current_session.to_dict(),
        }

        return current_session

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

        try:
            if self._is_cancelled():
                yield {
                    "type": "request_cancelled",
                    "session_id": current_session.session_id,
                    "request_id": self._request_id,
                }
                return

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
                    return

                gen = self._apply_tool_calls(
                    current_session, pending, stream_tools=stream
                )
                while True:
                    try:
                        ev = next(gen)
                    except StopIteration as stop:
                        current_session = stop.value
                        break
                    yield ev



            # Main LLM + tool loop
            while True:
                if self._is_cancelled():
                    yield {
                        "type": "request_cancelled",
                        "session_id": current_session.session_id,
                        "request_id": self._request_id,
                    }
                    break

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

                gen = self._apply_tool_calls(
                    current_session, tool_calls, stream_tools=stream
                )
                while True:
                    try:
                        ev = next(gen)
                    except StopIteration as stop:
                        current_session = stop.value
                        break
                    yield ev

        except Exception as exc:
            yield {
                "type": "error",
                "session_id": current_session.session_id,
                "request_id": self._request_id,
                "detail": str(exc),
            }

        yield {
            "type": "request_completed",
            "session_id": current_session.session_id,
            "request_id": self._request_id,
        }
