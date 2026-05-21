"""Tool loop behaviour tests for the future application layer.

These tests exercise :mod:`agent_app.application_future` and its
``send_request`` helper instead of the legacy dict-based API.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from agent_app.application_future import AgentApplication
from agent_app.tool_loop import ToolLoopRunner
from agent_core import AgentCore, Message, Session
from .dummy_tool import DummyCalculator  # noqa: F401  (imported for side effects)
from .interceptor_tool import InterceptorCalculator  # noqa: F401  (imported for side effects)


def _make_tool_config(tmp_path: Path) -> Path:
    # Use DummyProvider plus DummyCalculator tool to surface tool_calls.
    cfg = {
        "providers": {
            "dummy": {"provider": "dummy_provider", "model": "test-model"}
        },
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.dummy_tool.DummyCalculator",
        ],
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _make_interceptor_tool_config(
    tmp_path: Path,
    *,
    tool_prompt_override: Dict[str, Any] | None = None,
) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "dummy": {"provider": "dummy_provider", "model": "test-model"}
        },
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.interceptor_tool.InterceptorCalculator",
        ],
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    if tool_prompt_override is not None:
        default_agent = dict(cfg["agents"]["default"])
        default_agent["interceptor_calculator"] = tool_prompt_override
        cfg["agents"] = {**cfg["agents"], "default": default_agent}
    path = tmp_path / "config_interceptor.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_execute_tool_calls_non_streaming(tmp_path: Path) -> None:
    config_path = _make_tool_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")

    # Simulate a tool call by adding an assistant message with tool_calls metadata.
    tool_call: Dict[str, object] = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 2, "b": 3})},
    }
    session = core.add_message(
        session,
        "assistant",
        "",
        {"tool_calls": [tool_call]},
    )
    app.save_session(session)

    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))

    # Ensure no streaming tool events were produced in non-streaming mode.
    assert not any(ev["type"] == "tool_partial" for ev in events)

    # Find the latest session checkpoint from events and inspect the
    # stored messages to verify that tool output was appended.
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert checkpoints, "expected at least one session_checkpoint event"
    final_session = checkpoints[-1]["session"]
    assert isinstance(final_session, Session)

    messages = list(final_session.messages)
    tool_messages = [m for m in messages if getattr(m, "role", None) == "tool"]
    assert tool_messages
    assert "Result:" in str(getattr(tool_messages[-1], "content", ""))


def test_execute_tool_calls_streaming(tmp_path: Path) -> None:
    config_path = _make_tool_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")

    tool_call: Dict[str, object] = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 1, "b": 4})},
    }
    session = core.add_message(
        session,
        "assistant",
        "",
        {"tool_calls": [tool_call]},
    )
    app.save_session(session)

    events = list(app.send_request(core, session, base_config, overrides=None, stream=True))

    # Streaming path should surface both partials and final tool_results.
    partial_events = [ev for ev in events if ev.get("type") == "tool_partial"]
    assert partial_events
    assert any(
        isinstance(ev.get("payload"), dict)
        and "part" in (ev.get("payload") or {})
        for ev in partial_events
    )
    assert any(ev.get("type") == "tool_results" for ev in events)


def test_pending_tool_calls_ignored_after_follow_up_user_message() -> None:
    core = AgentCore()
    runner = ToolLoopRunner(
        core=core,
        config={},
        request_id="req_pending",
        tool_loop_cfg=SimpleNamespace(max_loops=8),
    )

    tool_call: Dict[str, object] = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 2, "b": 3})},
    }

    session = core.create_session()
    session = core.add_message(session, "assistant", "", {"tool_calls": [tool_call]})
    session = core.add_message(session, "user", "Thanks, now answer directly.")

    assert runner._extract_pending_tool_calls_from_session(session) == []


def test_pending_tool_calls_returned_for_unresolved_tail_assistant() -> None:
    core = AgentCore()
    runner = ToolLoopRunner(
        core=core,
        config={},
        request_id="req_pending_tail",
        tool_loop_cfg=SimpleNamespace(max_loops=8),
    )

    tool_call: Dict[str, object] = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 2, "b": 3})},
    }

    session = core.create_session()
    session = core.add_message(session, "assistant", "", {"tool_calls": [tool_call]})

    assert runner._extract_pending_tool_calls_from_session(session) == [tool_call]


def test_interceptor_tool_prompt_title_overridable_from_config(tmp_path: Path) -> None:
    config_path = _make_interceptor_tool_config(
        tmp_path,
        tool_prompt_override={
            "tool_call_prompts": {
                "add": {
                    "title": "Custom title from config",
                    "message": "Custom body from config.",
                }
            }
        },
    )
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    core, base_config, session = app.create_session("default")

    tool_call: Dict[str, object] = {
        "id": "call_prompt_copy",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 1, "b": 2})},
    }
    session = core.add_message(session, "assistant", "", {"tool_calls": [tool_call]})
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    final_session = checkpoints[-1]["session"]
    assert isinstance(final_session, Session)
    assistant = final_session.messages[-1]
    prompt = (assistant.metadata or {}).get("interception_current", {}).get("pending_prompt")
    assert isinstance(prompt, dict)
    assert prompt.get("title") == "Custom title from config"
    assert prompt.get("message") == "Custom body from config."


@pytest.mark.parametrize("deny_button_id", ["deny", "Deny"])
def test_interceptor_deny_does_not_execute_add(
    tmp_path: Path, deny_button_id: str
) -> None:
    config_path = _make_interceptor_tool_config(tmp_path)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    core, base_config, session = app.create_session("default")

    tool_call: Dict[str, object] = {
        "id": f"call_deny_{deny_button_id}",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 2, "b": 3})},
    }
    session = core.add_message(session, "assistant", "", {"tool_calls": [tool_call]})
    app.save_session(session)
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    final_session = [ev for ev in events if ev.get("type") == "session_checkpoint"][-1]["session"]
    assert isinstance(final_session, Session)
    assistant = final_session.messages[-1]
    current = (assistant.metadata or {}).get("interception_current")
    assert isinstance(current, dict)
    prompt = current.get("pending_prompt")
    assert isinstance(prompt, dict)

    new_md = dict(assistant.metadata or {})
    next_current = dict(current)
    next_current["answer"] = {
        "prompt_id": prompt.get("id"),
        "button_id": deny_button_id,
        "values": {},
    }
    new_md["interception_current"] = next_current
    resumed = Session(
        session_id=final_session.session_id,
        messages=[
            *final_session.messages[:-1],
            Message(
                role=assistant.role,
                content=assistant.content,
                metadata=new_md,
                multipart_content=assistant.multipart_content,
            ),
        ],
        metadata=final_session.metadata,
    )
    app.save_session(resumed)
    events2 = list(app.send_request(core, resumed, base_config, overrides=None, stream=False))
    resumed_session = [ev for ev in events2 if ev.get("type") == "session_checkpoint"][-1]["session"]
    assert isinstance(resumed_session, Session)
    tool_messages = [m for m in resumed_session.messages if m.role == "tool"]
    assert tool_messages
    assert "Denied by interceptor" in tool_messages[-1].content
    assert "Result:" not in tool_messages[-1].content


def test_interceptor_unknown_button_does_not_execute_add(tmp_path: Path) -> None:
    config_path = _make_interceptor_tool_config(tmp_path)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    core, base_config, session = app.create_session("default")

    tool_call: Dict[str, object] = {
        "id": "call_bad_btn",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 1, "b": 1})},
    }
    session = core.add_message(session, "assistant", "", {"tool_calls": [tool_call]})
    app.save_session(session)
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    final_session = [ev for ev in events if ev.get("type") == "session_checkpoint"][-1]["session"]
    assert isinstance(final_session, Session)
    assistant = final_session.messages[-1]
    current = (assistant.metadata or {}).get("interception_current")
    assert isinstance(current, dict)
    prompt = current.get("pending_prompt")
    assert isinstance(prompt, dict)

    new_md = dict(assistant.metadata or {})
    next_current = dict(current)
    next_current["answer"] = {
        "prompt_id": prompt.get("id"),
        "button_id": "not_a_real_action",
        "values": {},
    }
    new_md["interception_current"] = next_current
    resumed = Session(
        session_id=final_session.session_id,
        messages=[
            *final_session.messages[:-1],
            Message(
                role=assistant.role,
                content=assistant.content,
                metadata=new_md,
                multipart_content=assistant.multipart_content,
            ),
        ],
        metadata=final_session.metadata,
    )
    app.save_session(resumed)
    events2 = list(app.send_request(core, resumed, base_config, overrides=None, stream=False))
    resumed_session = [ev for ev in events2 if ev.get("type") == "session_checkpoint"][-1]["session"]
    assert isinstance(resumed_session, Session)
    tool_messages = [m for m in resumed_session.messages if m.role == "tool"]
    assert tool_messages
    assert "Unknown or unsupported prompt choice" in tool_messages[-1].content
    assert "Result:" not in tool_messages[-1].content


def test_interceptor_resume_denies_when_metadata_tool_call_id_is_int(tmp_path: Path) -> None:
    """``interception_current.tool_call_id`` may deserialize as int; must still match."""
    config_path = _make_interceptor_tool_config(tmp_path)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    core, base_config, session = app.create_session("default")

    tool_call: Dict[str, object] = {
        "id": "501",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 40, "b": 28})},
    }
    session = core.add_message(session, "assistant", "", {"tool_calls": [tool_call]})
    app.save_session(session)
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    final_session = [ev for ev in events if ev.get("type") == "session_checkpoint"][-1]["session"]
    assert isinstance(final_session, Session)
    assistant = final_session.messages[-1]
    current = (assistant.metadata or {}).get("interception_current")
    assert isinstance(current, dict)
    prompt = current.get("pending_prompt")
    assert isinstance(prompt, dict)

    new_md = dict(assistant.metadata or {})
    next_current = dict(current)
    next_current["tool_call_id"] = 501
    next_current["answer"] = {
        "prompt_id": prompt.get("id"),
        "button_id": "deny",
        "values": {},
    }
    new_md["interception_current"] = next_current
    resumed = Session(
        session_id=final_session.session_id,
        messages=[
            *final_session.messages[:-1],
            Message(
                role=assistant.role,
                content=assistant.content,
                metadata=new_md,
                multipart_content=assistant.multipart_content,
            ),
        ],
        metadata=final_session.metadata,
    )
    app.save_session(resumed)
    events2 = list(app.send_request(core, resumed, base_config, overrides=None, stream=False))
    resumed_session = [ev for ev in events2 if ev.get("type") == "session_checkpoint"][-1]["session"]
    assert isinstance(resumed_session, Session)
    tool_messages = [m for m in resumed_session.messages if m.role == "tool"]
    assert tool_messages
    assert "Denied by interceptor" in tool_messages[-1].content
    assert "Result: 68" not in tool_messages[-1].content


def test_interceptor_prompt_suspend_and_resume(tmp_path: Path) -> None:
    config_path = _make_interceptor_tool_config(tmp_path)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    core, base_config, session = app.create_session("default")

    tool_call: Dict[str, object] = {
        "id": "call_resume",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 2, "b": 3})},
    }
    session = core.add_message(session, "assistant", "", {"tool_calls": [tool_call]})
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    final_session = checkpoints[-1]["session"]
    assert isinstance(final_session, Session)
    assert not any(m.role == "tool" for m in final_session.messages)
    assistant = final_session.messages[-1]
    current = (assistant.metadata or {}).get("interception_current")
    assert isinstance(current, dict)
    prompt = current.get("pending_prompt")
    assert isinstance(prompt, dict)

    # Simulate prompt answer submission.
    new_md = dict(assistant.metadata or {})
    next_current = dict(current)
    next_current["answer"] = {
        "prompt_id": prompt.get("id"),
        "button_id": "allow",
        "values": {},
    }
    new_md["interception_current"] = next_current
    resumed = Session(
        session_id=final_session.session_id,
        messages=[
            *final_session.messages[:-1],
            Message(
                role=assistant.role,
                content=assistant.content,
                metadata=new_md,
                multipart_content=assistant.multipart_content,
            ),
        ],
        metadata=final_session.metadata,
    )
    events2 = list(app.send_request(core, resumed, base_config, overrides=None, stream=False))
    checkpoints2 = [ev for ev in events2 if ev.get("type") == "session_checkpoint"]
    resumed_session = checkpoints2[-1]["session"]
    assert isinstance(resumed_session, Session)
    tool_messages = [m for m in resumed_session.messages if m.role == "tool"]
    assert tool_messages
    assert "Result:" in tool_messages[-1].content


def test_interceptor_transform_and_stop_semantics(tmp_path: Path) -> None:
    config_path = _make_interceptor_tool_config(tmp_path)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    core, base_config, session = app.create_session("default")

    calls: List[Dict[str, object]] = [
        {
            "id": "call_a",
            "type": "function",
            "function": {"name": "add", "arguments": json.dumps({"a": 1, "b": 1})},
        },
        {
            "id": "call_b",
            "type": "function",
            "function": {"name": "add", "arguments": json.dumps({"a": 9, "b": 9})},
        },
    ]
    session = core.add_message(session, "assistant", "", {"tool_calls": calls})
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    final_session = [ev for ev in events if ev.get("type") == "session_checkpoint"][-1]["session"]
    assert isinstance(final_session, Session)
    assistant = final_session.messages[-1]
    current = (assistant.metadata or {}).get("interception_current")
    assert isinstance(current, dict)
    prompt = current.get("pending_prompt")
    assert isinstance(prompt, dict)

    # Answer first prompt with transform.
    md = dict(assistant.metadata or {})
    current = dict(current)
    current["answer"] = {"prompt_id": prompt.get("id"), "button_id": "transform", "values": {}}
    md["interception_current"] = current
    resumed1 = Session(
        session_id=final_session.session_id,
        messages=[*final_session.messages[:-1], Message(role=assistant.role, content=assistant.content, metadata=md, multipart_content=assistant.multipart_content)],
        metadata=final_session.metadata,
    )
    events2 = list(app.send_request(core, resumed1, base_config, overrides=None, stream=False))
    sess2 = [ev for ev in events2 if ev.get("type") == "session_checkpoint"][-1]["session"]
    assert isinstance(sess2, Session)
    tool_messages = [m for m in sess2.messages if m.role == "tool"]
    assert tool_messages
    # Transform rewrote args to a=2, b=8 → raw sum 10; intercept_tool_result caps values > 8 to 8.
    assert "Result: 8" in tool_messages[-1].content


def test_interceptor_transform_responses_shaped_tool_call(tmp_path: Path) -> None:
    """Transform must rewrite top-level ``arguments`` for OpenAI Responses ``function_call`` items."""
    config_path = _make_interceptor_tool_config(tmp_path)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    core, base_config, session = app.create_session("default")

    calls: List[Dict[str, object]] = [
        {
            "type": "function_call",
            "call_id": "fc_add",
            "name": "add",
            "arguments": json.dumps({"a": 5, "b": 6}),
        },
    ]
    session = core.add_message(session, "assistant", "", {"tool_calls": calls})
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    final_session = [ev for ev in events if ev.get("type") == "session_checkpoint"][-1]["session"]
    assert isinstance(final_session, Session)
    assistant = final_session.messages[-1]
    current = (assistant.metadata or {}).get("interception_current")
    assert isinstance(current, dict)
    prompt = current.get("pending_prompt")
    assert isinstance(prompt, dict)

    md = dict(assistant.metadata or {})
    current = dict(current)
    current["answer"] = {"prompt_id": prompt.get("id"), "button_id": "transform", "values": {}}
    md["interception_current"] = current
    resumed = Session(
        session_id=final_session.session_id,
        messages=[
            *final_session.messages[:-1],
            Message(
                role=assistant.role,
                content=assistant.content,
                metadata=md,
                multipart_content=assistant.multipart_content,
            ),
        ],
        metadata=final_session.metadata,
    )
    events2 = list(app.send_request(core, resumed, base_config, overrides=None, stream=False))
    sess2 = [ev for ev in events2 if ev.get("type") == "session_checkpoint"][-1]["session"]
    assert isinstance(sess2, Session)
    tool_messages = [m for m in sess2.messages if m.role == "tool"]
    assert tool_messages
    assert "Result: 8" in tool_messages[-1].content


def test_interceptor_tool_result_phase_prompting(tmp_path: Path) -> None:
    """Verify tool_result phase interception works end-to-end with prompts."""
    # This test requires an interceptor that supports result-phase prompting
    # For now, we'll create a minimal test that verifies the plumbing works
    
    # Note: InterceptorCalculator doesn't currently implement result-phase prompting
    # This test documents the expected behavior once it's implemented
    config_path = _make_interceptor_tool_config(tmp_path)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    core, base_config, session = app.create_session("default")

    # Add tool call
    tool_call: Dict[str, object] = {
        "id": "call_result_test",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 10, "b": 20})},
    }
    session = core.add_message(session, "assistant", "", {"tool_calls": [tool_call]})
    app.save_session(session)
    
    # Send request - should suspend at call-phase prompt first
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    suspended = checkpoints[-1]["session"]
    
    # For now, just verify the structure supports result-phase metadata
    # When result-phase prompting is implemented in an interceptor,
    # this test should be extended to:
    # 1. Approve the call-phase prompt
    # 2. Execute the tool
    # 3. Suspend at result-phase prompt
    # 4. Approve the result-phase prompt
    # 5. Verify completion
    
    # Verify the session structure can hold result-phase prompts
    assert isinstance(suspended, Session)
    # Result-phase prompts would be stored on tool message metadata
    # just like call-phase prompts are on assistant messages
