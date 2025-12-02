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
    ) -> None:
        self._core = core
        self._config = config
        self._request_id = request_id
        self._tool_loop_cfg = tool_loop_cfg

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


    def run(self, session: Session, *, stream: bool) -> Iterator[Dict[str, Any]]:
        """Execute the full tool loop, yielding application-layer events.

        The logic here is a direct extraction of the previous
        :meth:`AgentApplication.send_request` implementation so that the
        behaviour remains unchanged while being factored into a dedicated
        helper class.
        """

        core = self._core
        config = self._config
        rid = self._request_id

        if stream:
            # Streaming tool loop using core.send_request_stream
            current_session = session
            loops = 0

            # Handle any pending tool_calls already in the session before
            # initiating streaming.
            pending = self._extract_pending_tool_calls_from_session(current_session)
            if pending:
                loops += 1
                if loops > self._tool_loop_cfg.max_loops:
                    yield {
                        "type": "error",
                        "session_id": current_session.session_id,
                        "request_id": rid,
                        "detail": "Max tool loop depth exceeded",
                    }
                    yield {
                        "type": "request_completed",
                        "session_id": current_session.session_id,
                        "request_id": rid,
                    }
                    return

                yield {
                    "type": "tool_calls",
                    "session_id": current_session.session_id,
                    "request_id": rid,
                    "tool_calls": list(pending),
                }
                tool_messages = core.execute_tool_calls(pending, config)
                # Append tool messages to the session and emit tool_results with
                # the updated session snapshot.
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

                yield {
                    "type": "tool_results",
                    "session_id": current_session.session_id,
                    "request_id": rid,
                    "messages": list(tool_messages),
                    "session": current_session.to_dict(),
                }

            while True:
                # One streaming LLM phase
                final_session = current_session
                final_messages: List[Dict[str, Any]] = []

                for chunk in core.send_request_stream(current_session, config):
                    if chunk.get("type") == "partial":
                        yield {
                            "type": "partial",
                            "session_id": current_session.session_id,
                            "request_id": rid,
                            "message": chunk["message"],
                        }
                    elif chunk.get("type") == "final":
                        final_session = chunk["session"]
                        final_messages = list(chunk.get("messages") or [])
                        yield {
                            "type": "final",
                            "session_id": final_session.session_id,
                            "request_id": rid,
                            "messages": list(final_messages),
                            "session": final_session.to_dict(),
                        }

                current_session = final_session

                tool_calls = self._extract_tool_calls(final_messages)
                if not tool_calls:
                    break

                loops += 1
                if loops > self._tool_loop_cfg.max_loops:
                    yield {
                        "type": "error",
                        "session_id": current_session.session_id,
                        "request_id": rid,
                        "detail": "Max tool loop depth exceeded",
                    }
                    break

                yield {
                    "type": "tool_calls",
                    "session_id": current_session.session_id,
                    "request_id": rid,
                    "tool_calls": list(tool_calls),
                }

                tool_messages = core.execute_tool_calls(tool_calls, config)
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

                yield {
                    "type": "tool_results",
                    "session_id": current_session.session_id,
                    "request_id": rid,
                    "messages": list(tool_messages),
                    "session": current_session.to_dict(),
                }

            yield {
                "type": "request_completed",
                "session_id": current_session.session_id,
                "request_id": rid,
            }
            return

        # Non-streaming tool loop
        current_session = session
        final_messages: List[Dict[str, Any]] = []
        loops = 0

        # Handle any pending tool_calls already present in the session history
        # before issuing the first LLM call.
        pending = self._extract_pending_tool_calls_from_session(current_session)
        if pending:
            loops += 1
            if loops > self._tool_loop_cfg.max_loops:
                yield {
                    "type": "error",
                    "session_id": current_session.session_id,
                    "request_id": rid,
                    "detail": "Max tool loop depth exceeded",
                }
                yield {
                    "type": "request_completed",
                    "session_id": current_session.session_id,
                    "request_id": rid,
                }
                return

            yield {
                "type": "tool_calls",
                "session_id": current_session.session_id,
                "request_id": rid,
                "tool_calls": list(pending),
            }
            tool_messages = core.execute_tool_calls(pending, config)
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

            yield {
                "type": "tool_results",
                "session_id": current_session.session_id,
                "request_id": rid,
                "messages": list(tool_messages),
                "session": current_session.to_dict(),
            }

        while True:
            current_session, final_messages = core.send_request(current_session, config)

            yield {
                "type": "final",
                "session_id": current_session.session_id,
                "request_id": rid,
                "messages": list(final_messages),
                "session": current_session.to_dict(),
            }

            tool_calls = self._extract_tool_calls(final_messages)
            if not tool_calls:
                break

            loops += 1
            if loops > self._tool_loop_cfg.max_loops:
                yield {
                    "type": "error",
                    "session_id": current_session.session_id,
                    "request_id": rid,
                    "detail": "Max tool loop depth exceeded",
                }
                break

            yield {
                "type": "tool_calls",
                "session_id": current_session.session_id,
                "request_id": rid,
                "tool_calls": list(tool_calls),
            }

            tool_messages = core.execute_tool_calls(tool_calls, config)
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

            yield {
                "type": "tool_results",
                "session_id": current_session.session_id,
                "request_id": rid,
                "messages": list(tool_messages),
                "session": current_session.to_dict(),
            }

        yield {
            "type": "request_completed",
            "session_id": current_session.session_id,
            "request_id": rid,
        }
