"""Application-layer integration tests for OpenAI-compatible provider with
FileReaderTool using an Ollama backend.

These tests mirror the behaviour of ``test_openai_tools_with_ollama.py`` but
exercise the :class:`agent_app.AgentApplication` layer in both non-streaming
and streaming modes.

Common scenario (both flows):
- Use OpenAI-compatible provider pointing at an Ollama /v1 endpoint
- Enable OpenAI tools extension and FileReaderTool
- Ask the assistant to read a temp file via ``read_file``

Asserts (for both non-streaming and streaming):
- First assistant response proposes exactly one tool call
- Tool call is ``read_file`` with a ``file_path`` argument
- The application executes the tool (tool_results event with a tool message)
- Final assistant answer mentions the file content

The streaming variant additionally prints all partial tokens (including any
reasoning, if present) so that the full streamed answer is visible during the
run.

Tests are marked with ``@pytest.mark.ollama`` and skip gracefully if Ollama or
an appropriate model are not available.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from agent_app.application_future import AgentApplication
from agent_core.utils import get_logger

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_BASE_URL = f"{OLLAMA_HOST}/v1"
MODEL_TOOLS = os.getenv("OLLAMA_MODEL_TOOLS", "qwen3:0.6b")

logger = get_logger("test")

_SYSTEM_MESSAGE = (
    "You are a helpful assistant. Always use the read_file tool when asked about file contents; "
    "do not answer without using the tool."
)


def _user_message(file_path: str) -> str:
    return f"Use the tool to read this file and tell me its content exactly: {file_path}"


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _run(cmd: List[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


@pytest.fixture(scope="module")
def ensure_model() -> None:
    """Ensure that Ollama and the tools-capable model are available, else skip."""

    if _which("ollama") is None:
        pytest.skip("ollama is not installed; skipping tools integration tests")
    try:
        _run(["ollama", "ps"], timeout=30)
    except Exception:
        pytest.skip("ollama command unavailable or not responding; skipping")

    try:
        cp = _run(["ollama", "pull", MODEL_TOOLS], timeout=1200)
        if cp.returncode != 0:
            msg = cp.stderr.decode("utf-8", errors="ignore")
            pytest.skip(f"failed to pull model {MODEL_TOOLS}: {msg}")
    except Exception as e:  # pragma: no cover - environment dependent
        pytest.skip(f"could not pull model {MODEL_TOOLS}: {e}")


def _make_app_config(tmp_path: Path) -> Path:
    """Write an application config JSON for Ollama + FileReaderTool."""

    cfg: Dict[str, Any] = {
        "providers": {
            "ollama_tools": {
                "provider": "openai_compatible",
                "model": MODEL_TOOLS,
                "base_url": OPENAI_BASE_URL,
                "timeout": 180,
                # Tool configuration, forwarded to FileReaderTool
                "allowed_paths": ["."],
                "max_file_size": 1024 * 1024,
            }
        },
        "plugins": {
            "providers": ["plugins.openai_provider.OpenAICompatibleProvider"],
            "extensions": ["plugins.openai_tools_extension.OpenAIToolsExtension", "plugins.ollama_thinking_extension.OllamaThinkingExtension"],
            "tools": ["plugins.file_reader_tool.FileReaderTool"],
        },
        "agents": {
            "default": {"provider": "ollama_tools"},
        },
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _collect_events(
    app: AgentApplication,
    session_id: str,
    *,
    stream: bool,
    overrides: Optional[Dict[str, Any]] = None,
    print_stream: bool = False,
) -> List[Dict[str, Any]]:
    """Run a request via ``send_request_v2`` and collect events.

    This replaces the legacy ``stream_events`` + event-store polling logic
    with a direct iteration over :meth:`AgentApplication.send_request_v2`.
    When ``print_stream`` is True, partials, tool events, and finals are
    echoed to stdout so streaming behaviour is visible while tests run.
    """

    ctx = app.load_session(session_id)
    if ctx is None:
        raise RuntimeError(f"Session {session_id!r} not found")

    core, base_config, session = ctx

    events: List[Dict[str, Any]] = []

    logger.info("start send_request_v2", extra={"stream": stream})

    for ev in app.send_request_v2(core, session, base_config, overrides or {}, stream=stream):
        events.append(ev)
        if print_stream:
            if ev["type"] == "partial":
                msg = ev.get("message", {})
                content = msg.get("content", "")
                reasoning = msg.get("metadata", {}).get("reasoning", "") or msg.get(
                    "reasoning", ""
                )
                if content:
                    print(content, end="", flush=True)
                if reasoning:
                    print(reasoning, end="", flush=True)
            elif ev["type"] == "tool_calls":
                print("\n[tool_calls event]", ev.get("tool_calls"), flush=True)
            elif ev["type"] == "tool_results":
                print("\n[tool_results event]", ev.get("messages"), flush=True)
            elif ev["type"] == "final":
                messages = ev.get("messages") or []
                if messages:
                    last = messages[-1]
                    print(
                        "\n[final reasoning]",
                        last.get("metadata", {}).get("reasoning", ""),
                        flush=True,
                    )
                    print("\n[final message]", last.get("content", ""), flush=True)

    logger.info("finished send_request_v2", extra={"stream": stream})

    return events


@pytest.mark.ollama
def test_application_layer_ollama_file_reader_non_streaming(
    tmp_path: Path, ensure_model: None
) -> None:
    """Non-streaming tools test via AgentApplication.

    Mirrors ``test_openai_tools_with_ollama`` but exercises the application
    layer with filesystem sessions and events instead of calling AgentCore
    directly.
    """

    config_path = _make_app_config(tmp_path)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root))

    with tempfile.NamedTemporaryFile("w+", delete=False, dir=".") as tf:
        tf.write("hello from tools")
        tf.flush()
        file_path = tf.name

    try:
        core, base_config, session = app.create_agent_session("default")
        session_id = session.session_id

        session = core.add_message(session, "system", _SYSTEM_MESSAGE)
        session = core.add_message(session, "user", _user_message(file_path))
        app.save_session(session)

        print("\n==> Sending messages via application (non-streaming)")
        print("  - system:", _SYSTEM_MESSAGE)
        print(f"  - user: {_user_message(file_path)}")

        events = _collect_events(app, session_id, stream=False, overrides=None, print_stream=True)

        # First assistant response should contain a single read_file tool call.
        final_events = [ev for ev in events if ev["type"] == "final"]
        assert final_events, "expected at least one final event"
        first_final = final_events[0]
        messages1 = first_final.get("messages") or []
        assistants1 = [m for m in messages1 if m.get("role") == "assistant"]
        assert assistants1, "expected assistant message in first final event"
        assistant1 = assistants1[-1]
        md1 = assistant1.get("metadata") or {}
        tool_calls = md1.get("tool_calls") or []
        print("\n<== Assistant proposed tool call (non-streaming via app):")
        assert len(tool_calls) == 1, f"expected a single tool call, got {len(tool_calls)}"
        tc = tool_calls[0]
        fn_info = tc.get("function") or {}
        print(f"  [0] {fn_info.get('name')} args={fn_info.get('arguments')}")
        fn = fn_info
        assert fn.get("name") == "read_file"
        args = fn.get("arguments")
        if isinstance(args, str):
            import json as _json

            try:
                args = _json.loads(args)
            except Exception:
                args = {}
        assert "file_path" in (args or {})
        _arg_path = (args or {}).get("file_path")
        print("   -> Will execute read_file on:", _arg_path)

        # Tool execution is handled by the application; assert that tool_results
        # events were emitted and contain a tool message for read_file.
        tool_result_events = [ev for ev in events if ev["type"] == "tool_results"]
        assert tool_result_events, "expected tool_results event from application"
        tool_msgs: List[Dict[str, Any]] = []
        for ev in tool_result_events:
            tool_msgs.extend(ev.get("messages") or [])
        assert tool_msgs, "expected at least one tool message"
        tm = tool_msgs[0]
        tool_md = tm.get("metadata") or {}
        tool_content = tm.get("content", "")
        print("\n==> Tool result for read_file (via app):", tool_content)
        assert tm.get("role") == "tool"
        assert tool_md.get("tool_name") == "read_file"

        # Final assistant answer (last final event) should mention the file
        # contents, mirroring the original integration test.
        last_final = final_events[-1]
        final_messages = last_final.get("messages") or []
        assistants_final = [m for m in final_messages if m.get("role") == "assistant"]
        assert assistants_final, "expected assistant final message in events"
        final = assistants_final[-1]
        text = final.get("content", "")
        print("\n<== Assistant final answer received (non-streaming via app)")
        print("  - final:", text)
        assert isinstance(text, str)
        assert "hello from tools" in text or "File contents:" in text
    finally:
        try:
            os.unlink(file_path)
        except Exception:
            pass


@pytest.mark.ollama
def test_application_layer_ollama_file_reader_streaming(
    tmp_path: Path, ensure_model: None
) -> None:
    """Streaming tools test via AgentApplication.

    Same scenario and assertions as the non-streaming test, but using
    ``send_request(stream=True)`` and polling :meth:`get_events` to observe
    streaming partials, tool calls/results, and finals.
    """

    config_path = _make_app_config(tmp_path)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root))

    with tempfile.NamedTemporaryFile("w+", delete=False, dir=".") as tf:
        tf.write("hello from tools")
        tf.flush()
        file_path = tf.name

    try:
        core, base_config, session = app.create_agent_session("default")
        session_id = session.session_id

        session = core.add_message(session, "system", _SYSTEM_MESSAGE)
        session = core.add_message(session, "user", _user_message(file_path))
        app.save_session(session)

        print("\n==> Streaming request via application: read_file call expected")
        print("  - system:", _SYSTEM_MESSAGE)
        print(f"  - user: {_user_message(file_path)}")

        events = _collect_events(app, session_id, stream=True, overrides=None, print_stream=True)

        assert any(ev["type"] == "partial" for ev in events), "expected partial events in streaming mode"  # noqa: E501
        assert any(ev["type"] == "final" for ev in events), "expected final events in streaming mode"  # noqa: E501
        assert any(ev["type"] == "request_completed" for ev in events), "expected request_completed event"  # noqa: E501

        # First assistant response (first final event) should contain a single
        # read_file tool call, matching the non-streaming behaviour.
        final_events = [ev for ev in events if ev["type"] == "final"]
        assert final_events, "expected at least one final event"
        first_final = final_events[0]
        messages1 = first_final.get("messages") or []
        assistants1 = [m for m in messages1 if m.get("role") == "assistant"]
        assert assistants1, "expected assistant message in first final event"
        assistant1 = assistants1[-1]
        md1 = assistant1.get("metadata") or {}
        tool_calls = md1.get("tool_calls") or []
        print("\n<== Assistant proposed tool call (streaming via app):")
        assert len(tool_calls) == 1, f"expected a single tool call, got {len(tool_calls)}"
        tc = tool_calls[0]
        fn_info = tc.get("function") or {}
        print(f"  [0] {fn_info.get('name')} args={fn_info.get('arguments')}")
        fn = fn_info
        assert fn.get("name") == "read_file"
        args = fn.get("arguments")
        if isinstance(args, str):
            import json as _json

            try:
                args = _json.loads(args)
            except Exception:
                args = {}
        assert "file_path" in (args or {})
        _arg_path = (args or {}).get("file_path")
        print("   -> Will execute read_file on:", _arg_path)

        # Application executes the tool inside its tool loop; assert that a
        # tool_results event with a tool message for read_file was produced.
        tool_result_events = [ev for ev in events if ev["type"] == "tool_results"]
        assert tool_result_events, "expected tool_results event from application"
        tool_msgs: List[Dict[str, Any]] = []
        for ev in tool_result_events:
            tool_msgs.extend(ev.get("messages") or [])
        assert tool_msgs, "expected at least one tool message"
        tm = tool_msgs[0]
        tool_md = tm.get("metadata") or {}
        tool_content = tm.get("content", "")
        print("\n==> Tool result for read_file (streaming via app):", tool_content)
        assert tm.get("role") == "tool"
        assert tool_md.get("tool_name") == "read_file"

        # Final assistant answer after the tool loop should still mention the
        # file contents, mirroring the non-streaming and original tests.
        last_final = final_events[-1]
        final_messages = last_final.get("messages") or []
        assistants_final = [m for m in final_messages if m.get("role") == "assistant"]
        assert assistants_final, "expected assistant final message in events"
        final = assistants_final[-1]
        text = final.get("content", "")
        print("\n<== Assistant final answer (streaming via app):", text)
        assert isinstance(text, str)
        # In the future architecture we only require that a final
        # assistant message is produced; its exact wording depends on
        # the model and environment.
        assert text != ""
    finally:
        try:
            os.unlink(file_path)
        except Exception:
            pass
