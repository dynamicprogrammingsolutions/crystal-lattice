from __future__ import annotations

import threading
import traceback  # Add this import at the beginning of your file
from typing import Any, Dict, Iterator, List, Optional

from agent_core import AgentCore, Message, MessageRole, Session
from agent_core.types import ProviderRequestCancelled


class RequestCancellation:
    """Thread-safe request cancellation controller with live callbacks."""

    def __init__(self, *, cancelled: bool = False) -> None:
        self._event = threading.Event()
        self._lock = threading.Lock()
        self._callbacks: Dict[int, Any] = {}
        self._next_token = 0
        if cancelled:
            self._event.set()

    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def cancel(self) -> None:
        self._event.set()
        with self._lock:
            callbacks = list(self._callbacks.values())
        for callback in callbacks:
            try:
                callback()
            except Exception:
                continue

    def add_callback(self, callback: Any) -> int:
        with self._lock:
            token = self._next_token
            self._next_token += 1
            self._callbacks[token] = callback
            already_cancelled = self._event.is_set()
        if already_cancelled:
            try:
                callback()
            except Exception:
                pass
        return token

    def remove_callback(self, token: int) -> None:
        with self._lock:
            self._callbacks.pop(token, None)


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
        cancellation: RequestCancellation | None = None,
        context: Dict[str, Any] | None = None,
    ) -> None:
        self._core = core
        self._config = config
        self._request_id = request_id
        self._tool_loop_cfg = tool_loop_cfg
        self._cancel_callback = cancel_callback
        self._cancellation = cancellation
        self._context = context
        self._suspended = False
        self._stop_after_tools = False


    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_tool_calls(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self._core.extract_tool_calls_from_messages(messages)

    def _extract_pending_tool_calls_from_session(self, session: Session) -> List[Dict[str, Any]]:
        """Return tool_calls from the last assistant message, if not yet answered.

        We only auto-resume the tool loop when the assistant-with-tool_calls is
        still the unresolved tail of the conversation. Any later tool, user, or
        assistant message means the conversation already moved on.
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

        for msg in session.messages[last_tc_index + 1 :]:
            if msg.role in {"tool", "user", "assistant"}:
                return []

        return last_tc_calls

    def _is_cancelled(self) -> bool:
        cancellation = getattr(self, "_cancellation", None)
        if cancellation is not None:
            try:
                return bool(cancellation.is_cancelled())
            except Exception:
                return False
        cb = getattr(self, "_cancel_callback", None)
        if cb is None:
            return False
        try:
            return bool(cb())
        except Exception:
            return False

    def _set_message_metadata(
        self,
        session: Session,
        index: int,
        metadata: Dict[str, Any],
    ) -> Session:
        messages = list(session.messages)
        if index < 0 or index >= len(messages):
            return session
        msg = messages[index]
        messages[index] = Message(
            role=msg.role,
            content=msg.content,
            metadata=metadata or None,
            multipart_content=msg.multipart_content,
        )
        return Session(
            session_id=session.session_id,
            messages=messages,
            metadata=session.metadata,
        )

    def _find_assistant_message_index_for_tool_call(
        self,
        session: Session,
        tool_call_id: Optional[str],
    ) -> Optional[int]:
        if not isinstance(tool_call_id, str) or not tool_call_id:
            return None
        for idx in range(len(session.messages) - 1, -1, -1):
            msg = session.messages[idx]
            if msg.role != "assistant":
                continue
            md = msg.metadata or {}
            calls = md.get("tool_calls") or []
            if not isinstance(calls, list):
                continue
            for call in calls:
                if not isinstance(call, dict):
                    continue
                cid = call.get("id")
                if isinstance(cid, str) and cid == tool_call_id:
                    return idx
        return None

    @staticmethod
    def _append_interception_phase_entry(
        metadata: Dict[str, Any],
        entry: Dict[str, Any],
    ) -> Dict[str, Any]:
        next_metadata = dict(metadata)
        phases = next_metadata.get("interception_phases")
        if isinstance(phases, list):
            next_metadata["interception_phases"] = [*phases, entry]
        else:
            next_metadata["interception_phases"] = [entry]
        return next_metadata

    @staticmethod
    def _validate_interceptor_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate a tool interceptor directive envelope."""
        kind = response.get("kind")
        if kind not in ("continue", "prompt", "respond"):
            return {"kind": "continue"}
        has_call = isinstance(response.get("tool_call"), dict)
        has_result = isinstance(response.get("tool_result"), dict)
        if has_call and has_result:
            return {
                "kind": "respond",
                "tool_result": {
                    "success": False,
                    "error": "invalid interceptor response: both tool_call and tool_result",
                },
                "continue_loop": False,
            }
        return response

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

            try:
                next_session, final_messages = core.send_request(
                    session,
                    config,
                    request_id=rid,
                    cancellation=self._cancellation,
                )
            except ProviderRequestCancelled:
                yield {
                    "type": "request_cancelled",
                    "session_id": session.session_id,
                    "request_id": rid,
                }
                return session, []

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

        try:
            for chunk in core.send_request_stream(
                session,
                config,
                request_id=rid,
                cancellation=self._cancellation,
            ):
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
        except ProviderRequestCancelled:
            yield {
                "type": "request_cancelled",
                "session_id": current_session.session_id,
                "request_id": rid,
            }
            return current_session, []

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

        provider, extensions, tool_states = core._get_enabled_tool_states_for_config(config)
        registry = core._get_tool_interop_registry_for_config(
            config,
            provider=provider,
            extensions=extensions,
            tool_states=tool_states,
        )

        # Resolve provider-shared state so extensions/features can optionally
        # participate in interception using the same hook names.
        _provider2, _extensions2, features, tools, _tags = core._resolve_plugins_for_config(config)
        _provider_config2, shared_state = core._init_provider_and_features_for_config(
            _provider2,
            features,
            tools,
            config,
        )

        raw_interceptors: List[tuple[int, Any, Dict[str, Any]]] = []
        reg_order = 0
        for tool_plugin, tool_state in tool_states:
            raw_interceptors.append((reg_order, tool_plugin, tool_state))
            reg_order += 1
        for ext in extensions:
            raw_interceptors.append((reg_order, ext, shared_state))
            reg_order += 1
        for feature in features:
            raw_interceptors.append((reg_order, feature, shared_state))
            reg_order += 1

        # Stable ordering by (priority asc, registration order).
        interceptors = sorted(
            raw_interceptors,
            key=lambda item: (int(getattr(item[1], "priority", 100)), item[0]),
        )

        current_session = session
        self._suspended = False
        self._stop_after_tools = False
        stop_loop = False

        # Record the tool_calls event first
        yield {
            "type": "tool_calls",
            "session_id": current_session.session_id,
            "request_id": rid,
            "tool_calls": tool_calls,
        }

        tool_messages: List[Dict[str, Any]] = []

        for call in tool_calls:
            try:
                inspected_call = registry.inspect_call(call)
                call_id = inspected_call.call_id
            except Exception:
                inspected_call = None
                call_id = None
            last_final: Dict[str, Any] | None = None

            if inspected_call is None:
                name = None
                missing_tool_metadata: Dict[str, Any] = {
                    "tool_call_id": call_id,
                    "tool_name": name,
                }
                last_final = {
                    "role": "tool",
                    "content": f"Error: no tool handled '{name}'",
                    "metadata": missing_tool_metadata,
                }
            else:
                name = inspected_call.tool_name
                effective_call = inspected_call.raw
                effective_payload = inspected_call.payload
                tool, state, matched_schema = core._resolve_tool_handler_for_call(
                    inspected_call,
                    tool_states,
                    registry,
                )
                synthetic_result: Dict[str, Any] | None = None
                assistant_idx = self._find_assistant_message_index_for_tool_call(
                    current_session,
                    call_id,
                )
                if assistant_idx is None:
                    # Fallback: if the call id could not be resolved, attach prompt
                    # metadata to the most recent assistant message that carries any
                    # tool_calls payload (typically the unresolved tail).
                    for idx in range(len(current_session.messages) - 1, -1, -1):
                        msg = current_session.messages[idx]
                        if msg.role != "assistant":
                            continue
                        md = msg.metadata or {}
                        calls = md.get("tool_calls") or []
                        if isinstance(calls, list) and any(isinstance(c, dict) for c in calls):
                            assistant_idx = idx
                            break
                resume_answer: Dict[str, Any] | None = None
                resume_prompt: Dict[str, Any] | None = None
                if assistant_idx is not None:
                    msg = current_session.messages[assistant_idx]
                    md = dict(msg.metadata or {})
                    current = md.get("interception_current")
                    if isinstance(current, dict):
                        if (
                            current.get("phase") == "tool_call"
                            and current.get("tool_call_id") == call_id
                            and isinstance(current.get("answer"), dict)
                        ):
                            resume_answer = dict(current.get("answer") or {})
                            rp = current.get("pending_prompt")
                            resume_prompt = dict(rp) if isinstance(rp, dict) else None
                            if resume_prompt is not None:
                                md = self._append_interception_phase_entry(
                                    md,
                                    {
                                        "entry_type": "prompt_response",
                                        "phase": "tool_call",
                                        "tool_call_id": call_id,
                                        "tool_name": name,
                                        "plugin": current.get("plugin"),
                                        "prompt": resume_prompt,
                                        "answer": resume_answer,
                                    },
                                )
                            current.pop("answer", None)
                            current.pop("pending_prompt", None)
                            current["resumed"] = True
                            md["interception_current"] = current
                            current_session = self._set_message_metadata(current_session, assistant_idx, md)

                # Call-phase interception
                for _order, interceptor, interceptor_state in interceptors:
                    response = interceptor.intercept_tool_call(
                        {
                            "tool_call_id": call_id,
                            "tool_name": name,
                            "arguments": effective_payload,
                            "raw_call": effective_call,
                        },
                        {
                            "request_id": rid,
                            "phase": "tool_call",
                            "session_id": current_session.session_id,
                            "prompt": resume_prompt,
                            "answer": resume_answer,
                        },
                        interceptor_state,
                    )
                    if not isinstance(response, dict):
                        response = {"kind": "continue"}
                    response = self._validate_interceptor_response(response)
                    kind = response.get("kind")
                    continue_loop = response.get("continue_loop")
                    if kind == "prompt":
                        prompt = response.get("prompt") or {}
                        sid_raw = response.get("schema_id")
                        if isinstance(sid_raw, str) and sid_raw.strip():
                            sp = response.get("schema_params")
                            params_dict = sp if isinstance(sp, dict) else {}
                            built = None
                            materialize_fn = getattr(
                                interceptor, "materialize_interception_prompt", None
                            )
                            if callable(materialize_fn):
                                built = materialize_fn(
                                    interceptor_state,
                                    schema_id=sid_raw.strip(),
                                    schema_params=params_dict,
                                    tool_call_id=call_id,
                                )
                            if isinstance(built, dict):
                                prompt = built
                        if (
                            not isinstance(prompt, dict)
                            or not isinstance(prompt.get("buttons"), list)
                            or not prompt.get("buttons")
                        ):
                            prompt = {
                                "id": f"prompt_{call_id or 'tool'}",
                                "title": "Tool confirmation",
                                "message": "Confirm tool action",
                                "buttons": [{"id": "ok", "label": "OK", "default": True}],
                            }
                        if assistant_idx is not None:
                            msg = current_session.messages[assistant_idx]
                            md = dict(msg.metadata or {})
                            md["interception_current"] = {
                                "phase": "tool_call",
                                "tool_call_id": call_id,
                                "tool_name": name,
                                "plugin": getattr(interceptor, "name", interceptor.__class__.__name__),
                                "pending_prompt": prompt,
                                "raw_call": effective_call,
                                "arguments": effective_payload,
                            }
                            current_session = self._set_message_metadata(current_session, assistant_idx, md)
                        yield {
                            "type": "tool_interceptor_prompt",
                            "session_id": current_session.session_id,
                            "request_id": rid,
                            "tool_call_id": call_id,
                            "phase": "tool_call",
                            "prompt": prompt,
                        }
                        self._suspended = True
                        break
                    if kind == "respond":
                        tool_result = response.get("tool_result")
                        if isinstance(tool_result, dict):
                            synthetic_result = tool_result
                        if assistant_idx is not None:
                            msg = current_session.messages[assistant_idx]
                            md = dict(msg.metadata or {})
                            md = self._append_interception_phase_entry(
                                md,
                                {
                                    "entry_type": "plugin_response",
                                    "phase": "tool_call",
                                    "tool_call_id": call_id,
                                    "tool_name": name,
                                    "plugin": getattr(interceptor, "name", interceptor.__class__.__name__),
                                    "plugin_response": {
                                        "kind": "respond",
                                        "continue_loop": continue_loop,
                                    },
                                },
                            )
                            md["interception_current"] = {
                                "phase": "tool_call",
                                "tool_call_id": call_id,
                                "tool_name": name,
                                "plugin": getattr(interceptor, "name", interceptor.__class__.__name__),
                                "completed": True,
                            }
                            current_session = self._set_message_metadata(current_session, assistant_idx, md)
                        if continue_loop is False:
                            stop_loop = True
                        break
                    transformed_call = response.get("tool_call")
                    if isinstance(transformed_call, dict):
                        try:
                            new_inspected = registry.inspect_call(transformed_call)
                            new_tool, new_state, new_matched_schema = core._resolve_tool_handler_for_call(
                                new_inspected,
                                tool_states,
                                registry,
                            )
                        except Exception:
                            pass
                        else:
                            effective_call = transformed_call
                            inspected_call = new_inspected
                            effective_payload = new_inspected.payload
                            name = new_inspected.tool_name
                            call_id = new_inspected.call_id
                            tool = new_tool
                            state = new_state
                            matched_schema = new_matched_schema
                            if assistant_idx is not None:
                                msg = current_session.messages[assistant_idx]
                                md = dict(msg.metadata or {})
                                md = self._append_interception_phase_entry(
                                    md,
                                    {
                                        "entry_type": "plugin_response",
                                        "phase": "tool_call",
                                        "tool_call_id": call_id,
                                        "tool_name": name,
                                        "plugin": getattr(interceptor, "name", interceptor.__class__.__name__),
                                        "plugin_response": {
                                            "kind": "continue",
                                            "tool_call": transformed_call,
                                            "continue_loop": continue_loop,
                                        },
                                    },
                                )
                                current_session = self._set_message_metadata(current_session, assistant_idx, md)
                    transformed_result = response.get("tool_result")
                    if isinstance(transformed_result, dict):
                        synthetic_result = transformed_result
                        if assistant_idx is not None:
                            msg = current_session.messages[assistant_idx]
                            md = dict(msg.metadata or {})
                            md = self._append_interception_phase_entry(
                                md,
                                {
                                    "entry_type": "plugin_response",
                                    "phase": "tool_call",
                                    "tool_call_id": call_id,
                                    "tool_name": name,
                                    "plugin": getattr(interceptor, "name", interceptor.__class__.__name__),
                                    "plugin_response": {
                                        "kind": "continue",
                                        "tool_result": transformed_result,
                                        "continue_loop": continue_loop,
                                    },
                                },
                            )
                            current_session = self._set_message_metadata(current_session, assistant_idx, md)
                    if continue_loop is False and not isinstance(transformed_call, dict) and not isinstance(transformed_result, dict):
                        # meaningful continue: loop control
                        if assistant_idx is not None:
                            msg = current_session.messages[assistant_idx]
                            md = dict(msg.metadata or {})
                            md = self._append_interception_phase_entry(
                                md,
                                {
                                    "entry_type": "plugin_response",
                                    "phase": "tool_call",
                                    "tool_call_id": call_id,
                                    "tool_name": name,
                                    "plugin": getattr(interceptor, "name", interceptor.__class__.__name__),
                                    "plugin_response": {"kind": "continue", "continue_loop": False},
                                },
                            )
                            current_session = self._set_message_metadata(current_session, assistant_idx, md)
                    if continue_loop is False:
                        stop_loop = True
                if self._suspended:
                    break

                if tool is None or state is None:
                    missing_handler_metadata: Dict[str, Any] = {
                        "tool_call_id": call_id,
                        "tool_name": name,
                    }
                    last_final = {
                        "role": "tool",
                        "content": f"Error: no tool handled '{name}'",
                        "metadata": missing_handler_metadata,
                    }
                else:
                    had_result = False
                    saw_partial = False
                    stream_error: str | None = None
                    last_result: Dict[str, Any] | None = synthetic_result
                    if synthetic_result is not None:
                        had_result = True
                    if not had_result:
                        tool_context: Dict[str, Any] = dict(self._context) if isinstance(self._context, dict) else {}
                        tool_context.setdefault("core", core)
                        tool_context.setdefault("config", config)
                        tool_context.setdefault("trigger_source", "application")
                        try:
                            iterator = tool.stream_tool(
                                name,
                                effective_payload,
                                state,
                                payload_kind=inspected_call.payload_kind if inspected_call is not None else None,
                                payload_format=inspected_call.payload_format if inspected_call is not None else None,
                                payload_metadata=inspected_call.payload_metadata if inspected_call is not None else None,
                                tool_call=effective_call if isinstance(effective_call, dict) else None,
                                cancellation=self._cancellation,
                                context=tool_context,
                            )
                            iterator = iter(iterator)
                        except Exception as exc:
                            iterator = None
                            stream_error = f"Tool error: {exc}"
                        if iterator is not None:
                            try:
                                for chunk in iterator:
                                    if not isinstance(chunk, dict):
                                        continue
                                    if "success" in chunk:
                                        last_result = chunk
                                        had_result = True
                                    elif "part" in chunk:
                                        if stream_tools:
                                            phase = "start" if not saw_partial else "stream"
                                            saw_partial = True
                                            yield {
                                                "type": "tool_partial",
                                                "session_id": current_session.session_id,
                                                "request_id": rid,
                                                "tool_call_id": call_id,
                                                "phase": phase,
                                                "payload": chunk,
                                            }
                            except Exception as exc:
                                stream_error = f"Tool error: {exc}"
                    if not had_result or not isinstance(last_result, dict):
                        metadata = {"tool_call_id": call_id, "tool_name": name}
                        last_final = {
                            "role": "tool",
                            "content": stream_error or f"Error: no tool handled '{name}'",
                            "metadata": metadata,
                        }
                    else:
                        # Result-phase interception (transform/respond only in 020)
                        final_result = last_result
                        tool_phase_md: Dict[str, Any] = {}
                        for _order, interceptor, interceptor_state in interceptors:
                            response = interceptor.intercept_tool_result(
                                {
                                    "tool_call_id": call_id,
                                    "tool_name": name,
                                    "arguments": effective_payload,
                                    "raw_call": effective_call,
                                    "tool_result": final_result,
                                },
                                {
                                    "request_id": rid,
                                    "phase": "tool_result",
                                    "session_id": current_session.session_id,
                                },
                                interceptor_state,
                            )
                            if not isinstance(response, dict):
                                response = {"kind": "continue"}
                            response = self._validate_interceptor_response(response)
                            kind = response.get("kind")
                            transformed = response.get("tool_result")
                            continue_loop = response.get("continue_loop")
                            if kind in ("continue", "respond") and isinstance(transformed, dict):
                                final_result = transformed
                            if kind in ("continue", "respond") and isinstance(transformed, dict):
                                tool_phase_md = self._append_interception_phase_entry(
                                    tool_phase_md,
                                    {
                                        "entry_type": "plugin_response",
                                        "phase": "tool_result",
                                        "tool_call_id": call_id,
                                        "tool_name": name,
                                        "plugin": getattr(interceptor, "name", interceptor.__class__.__name__),
                                        "plugin_response": {"kind": kind, "tool_result": transformed, "continue_loop": continue_loop},
                                    },
                                )
                            if continue_loop is False and not isinstance(transformed, dict):
                                tool_phase_md = self._append_interception_phase_entry(
                                    tool_phase_md,
                                    {
                                        "entry_type": "plugin_response",
                                        "phase": "tool_result",
                                        "tool_call_id": call_id,
                                        "tool_name": name,
                                        "plugin": getattr(interceptor, "name", interceptor.__class__.__name__),
                                        "plugin_response": {"kind": kind, "continue_loop": False},
                                    },
                                )
                            if continue_loop is False:
                                stop_loop = True
                            if kind == "respond":
                                break
                        try:
                            formatted_content = tool.format_tool_result(final_result, state)
                        except Exception as exc:
                            formatted_content = f"Tool formatting error: {exc}"
                        metadata = {
                            "tool_call_id": call_id,
                            "tool_name": name,
                        }
                        if tool_phase_md:
                            # For tool_result phase, persist lifecycle metadata on the tool message.
                            metadata.update(tool_phase_md)
                            metadata["interception_current"] = {
                                "phase": "tool_result",
                                "tool_call_id": call_id,
                                "tool_name": name,
                                "completed": True,
                            }
                        if matched_schema is not None:
                            metadata["tool_schema"] = matched_schema
                        plugin_name = getattr(tool, "name", None)
                        if isinstance(plugin_name, str) and plugin_name:
                            metadata["tool_plugin"] = plugin_name
                        try:
                            display_candidate = tool.to_display_format(
                                formatted_content or "",
                                final_result,
                                state,
                            )
                            if isinstance(display_candidate, dict):
                                metadata["display"] = display_candidate
                        except Exception:
                            pass
                        last_final = {
                            "role": "tool",
                            "content": formatted_content or "",
                            "metadata": metadata,
                        }

            if last_final is None and self._is_cancelled():
                break

            if last_final is None:
                # iter_tool_messages already synthesizes errors for missing tools,
                # but guard defensively in case it yields nothing.
                name = inspected_call.tool_name if inspected_call is not None else None
                fallback_metadata: Dict[str, Any] = {
                    "tool_call_id": call_id,
                    "tool_name": name,
                }
                last_final = {
                    "role": "tool",
                    "content": f"Error: no tool handled '{name}'",
                    "metadata": fallback_metadata,
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
            metadata = last_final.get("metadata") or {}
            current_session = core.add_message(
                current_session,
                role,
                content,
                metadata,
                config=config,
            )

            if self._is_cancelled():
                break
            if stop_loop:
                break

        # Summarise final tool messages appended to the session.
        if self._suspended:
            yield {
                "type": "session_checkpoint",
                "session_id": current_session.session_id,
                "request_id": rid,
                "session": current_session,
            }
            return current_session
        self._stop_after_tools = stop_loop

        if not tool_messages and self._is_cancelled():
            return current_session

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
                if self._suspended or self._stop_after_tools:
                    yield {
                        "type": "request_completed",
                        "session_id": current_session.session_id,
                        "request_id": self._request_id,
                    }
                    return



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
                if self._suspended or self._stop_after_tools:
                    break
        except Exception as exc:
            print(f"Error in ToolLoopRunner: {exc}")
            traceback.print_exc()  # Print the stack trace
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
