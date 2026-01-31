from __future__ import annotations

from typing import Any, Dict, Iterator, List

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
    ) -> Iterator[Dict[str, Any]]:
        """Run a single LLM phase, yielding events as they occur.

        For non-streaming requests a single ``final`` event is yielded.
        For streaming requests, ``partial`` events are yielded as chunks
        arrive from :meth:`AgentCore.send_request_stream`, along with
        a per-phase assistant message lifecycle signal:

        - ``{"type": "assistant_message", "phase": "start", ...}``
        - ``{"type": "assistant_message", "phase": "end", ...}``

        The updated session and final assistant messages for the phase
        are returned via ``StopIteration.value`` as
        ``(final_session, final_messages)``.
        """

        core = self._core
        config = self._config
        rid = self._request_id
        start_index = len(session.messages)

        if not stream:
            if self._is_cancelled():
                yield {
                    "type": "request_cancelled",
                    "session_id": session.session_id,
                    "request_id": rid,
                }
                return session, []

            next_session, final_messages = core.send_request(session, config)

            # Emit the public final event first so that external
            # consumers see the completed assistant reply before any
            # internal checkpoint markers.
            yield {
                "type": "final",
                "session_id": next_session.session_id,
                "request_id": rid,
                "start_index": start_index,
                "messages": final_messages,
            }

            # Internal checkpoint is emitted *after* the final event so
            # that session persistence and checkpoint cursors align with
            # the visible assistant messages.
            yield {
                "type": "session_checkpoint",
                "session_id": next_session.session_id,
                "request_id": rid,
                "session": next_session,
            }
            return next_session, final_messages

        # Streaming: yield partial and final events directly from
        # send_request_stream so that callers see true streaming
        # behaviour without per-phase buffering.
        current_session = session
        final_session = session
        final_messages: List[Dict[str, Any]] = []
        started = False

        for chunk in core.send_request_stream(session, config):
            if self._is_cancelled():
                yield {
                    "type": "request_cancelled",
                    "session_id": current_session.session_id,
                    "request_id": rid,
                }
                return current_session, []

            ctype = chunk.get("type")

            if ctype == "partial":
                if not started:
                    started = True
                    # Signal the beginning of a streamed assistant message
                    # so renderers can emit headers before reasoning/content.
                    yield {
                        "type": "assistant_message",
                        "session_id": current_session.session_id,
                        "request_id": rid,
                        "phase": "start",
                    }
                yield {
                    "type": "partial",
                    "session_id": current_session.session_id,
                    "request_id": rid,
                    "message": chunk["message"],
                }
            elif ctype == "final":
                final_session = chunk["session"]
                final_messages = chunk.get("messages") or []

                # If no partials were seen, still emit a synthetic
                # assistant_message start so UIs can treat this as a
                # regular assistant reply.
                if final_messages and not started:
                    started = True
                    yield {
                        "type": "assistant_message",
                        "session_id": current_session.session_id,
                        "request_id": rid,
                        "phase": "start",
                    }

                # Emit the public final event describing the completed
                # assistant reply.
                yield {
                    "type": "final",
                    "session_id": final_session.session_id,
                    "request_id": rid,
                    "start_index": start_index,
                    "messages": final_messages,
                }

                if started:
                    # Signal end-of-message so renderers can close any
                    # open streaming state before footers are printed.
                    yield {
                        "type": "assistant_message",
                        "session_id": final_session.session_id,
                        "request_id": rid,
                        "phase": "end",
                    }

                # Internal checkpoint is emitted *after* the final
                # event so that persistence and checkpoint cursors align
                # with the visible assistant messages.
                yield {
                    "type": "session_checkpoint",
                    "session_id": final_session.session_id,
                    "request_id": rid,
                    "session": final_session,
                }

        return final_session, final_messages

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
        start_index = len(session.messages)

        current_session = session

        # Record the tool_calls event first
        yield {
            "type": "tool_calls",
            "session_id": current_session.session_id,
            "request_id": rid,
            "tool_calls": tool_calls,
        }

        tool_messages: List[Dict[str, Any]] = []

        for call in tool_calls:
            call_id = call.get("id") or call.get("tool_call_id")
            last_final: Dict[str, Any] | None = None

            saw_partial = False
            for item in core.iter_tool_messages([call], config):
                if not isinstance(item, dict):
                    continue
                if "part" in item:
                    if stream_tools:
                        phase = "start" if not saw_partial else "stream"
                        saw_partial = True
                        yield {
                            "type": "tool_partial",
                            "session_id": current_session.session_id,
                            "request_id": rid,
                            "tool_call_id": call_id,
                            "phase": phase,
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

            if stream_tools and last_final is not None:
                # Emit an explicit end event so UIs can render headers/footers
                # around streamed tool output without re-parsing tool_results.
                yield {
                    "type": "tool_partial",
                    "session_id": current_session.session_id,
                    "request_id": rid,
                    "tool_call_id": call_id,
                    "phase": "end",
                    "payload": {"result": last_final},
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
            current_session = core.add_message(
                current_session,
                role,
                content,
                metadata,
                config=config,
            )

        # Summarise final tool messages appended to the session.
        yield {
            "type": "tool_results",
            "session_id": current_session.session_id,
            "request_id": rid,
            "start_index": start_index,
            "messages": tool_messages,
        }

        # Emit a single checkpoint *after* tool_results so that
        # external consumers can align snapshots with the final tool
        # messages for this phase.
        yield {
            "type": "session_checkpoint",
            "session_id": current_session.session_id,
            "request_id": rid,
            "session": current_session,
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

                # Run a single LLM phase, yielding events as they arrive
                # and capturing the resulting session and messages via
                # StopIteration.value from the generator.
                gen_phase = self._run_llm_phase(current_session, stream=stream)
                final_session = current_session
                final_messages: List[Dict[str, Any]] = []

                while True:
                    try:
                        ev = next(gen_phase)
                    except StopIteration as stop:
                        try:
                            final_session, final_messages = stop.value  # type: ignore[misc]
                        except Exception:
                            final_session, final_messages = current_session, []
                        break
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
