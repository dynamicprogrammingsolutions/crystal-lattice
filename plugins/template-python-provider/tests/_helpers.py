from __future__ import annotations

import importlib
from typing import Any, Dict, List, Optional, Sequence, Tuple

from agent_core import AgentCore, Session


def import_symbol(dotted_path: str) -> Any:
    """Import and return ``"package.module:Symbol"`` by dotted path."""

    if not isinstance(dotted_path, str) or not dotted_path.strip():
        raise ImportError("dotted_path must be a non-empty string")

    module_path, sep, attr = dotted_path.rpartition(".")
    if not sep:
        raise ImportError(f"Invalid import path {dotted_path!r}; expected 'package.module.Symbol'")

    module = importlib.import_module(module_path)
    try:
        return getattr(module, attr)
    except AttributeError as exc:
        raise ImportError(f"Module {module_path!r} has no attribute {attr!r}") from exc


def build_core(
    provider_cls: type,
    *,
    extensions: Optional[Sequence[type]] = None,
    features: Optional[Sequence[type]] = None,
    tools: Optional[Sequence[type]] = None,
) -> AgentCore:
    core = AgentCore()
    core.register_provider(provider_cls, extensions=list(extensions or []))
    for feature_cls in features or []:
        core.register_feature(feature_cls)
    for tool_cls in tools or []:
        core.register_tool(tool_cls)
    return core


def run_non_streaming(
    core: AgentCore,
    session: Session,
    config: Dict[str, Any],
) -> Tuple[Session, List[Dict[str, Any]]]:
    new_session, finals = core.send_request(session, config)
    return new_session, finals


def run_streaming(
    core: AgentCore,
    session: Session,
    config: Dict[str, Any],
) -> Tuple[Session, List[Dict[str, Any]], str]:
    partial_parts: List[str] = []
    final_event: Optional[Dict[str, Any]] = None

    for event in core.send_request_stream(session, config):
        if not isinstance(event, dict):
            continue
        ev_type = event.get("type")
        if ev_type == "partial":
            msg = event.get("message") or {}
            content = msg.get("content", "") if isinstance(msg, dict) else ""
            if isinstance(content, str) and content:
                partial_parts.append(content)
        elif ev_type == "final":
            final_event = event

    partial_text = "".join(partial_parts)
    if final_event is None:
        return session, [], partial_text

    new_session = final_event.get("session")
    if not isinstance(new_session, Session):
        new_session = session
    messages = final_event.get("messages")
    finals = list(messages) if isinstance(messages, list) else []
    return new_session, finals, partial_text


def extract_tool_calls(messages: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tool_calls: List[Dict[str, Any]] = []
    for msg in messages:
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        md = msg.get("metadata") or {}
        calls = md.get("tool_calls") if isinstance(md, dict) else None
        if isinstance(calls, list):
            tool_calls.extend([c for c in calls if isinstance(c, dict)])
    return tool_calls


def run_tool_loop(
    core: AgentCore,
    session: Session,
    config: Dict[str, Any],
    *,
    stream: bool = False,
    max_iters: int = 5,
) -> Tuple[Session, List[Dict[str, Any]]]:
    """Run a basic tool loop: request -> tool_calls -> tool results -> repeat."""

    if max_iters < 1:
        raise ValueError("max_iters must be >= 1")

    finals: List[Dict[str, Any]] = []

    for _ in range(max_iters):
        if stream:
            session, finals, _partial_text = run_streaming(core, session, config)
        else:
            session, finals = run_non_streaming(core, session, config)

        calls = extract_tool_calls(finals)
        if not calls:
            break

        tool_messages = core.execute_tool_calls(calls, config)
        for tm in tool_messages:
            if not isinstance(tm, dict):
                continue
            session = core.add_message(
                session,
                role=tm.get("role", "tool"),
                content=str(tm.get("content", "")),
                metadata=tm.get("metadata"),
                config=config,
            )

    return session, finals
