from __future__ import annotations

"""Terminal rendering integration test with Ollama tools and timestamp footer.

This test mirrors the core application-layer Ollama tools integration but
focuses on the terminal rendering pipeline:

- Configure AgentApplication with Ollama + tools + reasoning + timestamp
  provider extension.
- Drive a streaming request via TerminalApplication.
- Collect emitted events from the shared event store.
- Feed events into TerminalRenderContext with a capture-based writer.
- Assert that assistant and tool headers appear, and that a timestamp added
  by the TimestampExtension is rendered via the footer UI schema.

The test is marked `@pytest.mark.ollama` and skips gracefully when the
prerequisites are not met.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest


# Reduce noisy structlog output during tests unless explicitly overridden.
os.environ.setdefault("LOG_LEVEL", "WARNING")


def _json_size_bytes(value: Any) -> int:
    return len(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _assert_events_within_size_budget(
    *,
    events: List[Dict[str, Any]],
    app: Any,
    multiplier: int = 2,
    overhead_bytes: int = 4096,
) -> None:
    session_ids = {
        ev.get("session_id")
        for ev in events
        if isinstance(ev, dict) and isinstance(ev.get("session_id"), str)
    }

    max_message_sizes: Dict[str, int] = {}
    for session_id in session_ids:
        ctx = app.load_session(session_id)
        assert ctx is not None
        _core, _base_config, session = ctx
        session_dict = session.to_dict()
        raw_messages = session_dict.get("messages") or []
        messages = [m for m in raw_messages if isinstance(m, dict)]
        assert messages
        max_message_sizes[session_id] = max(_json_size_bytes(m) for m in messages)

    failures: List[str] = []
    for ev in events:
        session_id = ev.get("session_id")
        if not isinstance(session_id, str):
            continue
        budget = max_message_sizes[session_id] * multiplier + overhead_bytes
        size = _json_size_bytes(ev)
        if size > budget:
            failures.append(
                f"event too large: type={ev.get('type')!r} id={ev.get('event_id')!r} "
                f"size={size}B budget={budget}B session_id={session_id}"
            )

    assert not failures, "\n".join(failures[:10])


def _assert_events_within_single_message_budget(
    *,
    events: List[Dict[str, Any]],
    app: Any,
    overhead_bytes: int = 2048,
) -> None:
    session_ids = {
        ev.get("session_id")
        for ev in events
        if isinstance(ev, dict) and isinstance(ev.get("session_id"), str)
    }

    max_message_sizes: Dict[str, int] = {}
    for session_id in session_ids:
        ctx = app.load_session(session_id)
        assert ctx is not None
        _core, _base_config, session = ctx
        session_dict = session.to_dict()
        raw_messages = session_dict.get("messages") or []
        messages = [m for m in raw_messages if isinstance(m, dict)]
        assert messages
        max_message_sizes[session_id] = max(_json_size_bytes(m) for m in messages)

    failures: List[str] = []
    for ev in events:
        session_id = ev.get("session_id")
        if not isinstance(session_id, str):
            continue
        budget = max_message_sizes[session_id] + overhead_bytes
        size = _json_size_bytes(ev)
        if size > budget:
            failures.append(
                f"event too large: type={ev.get('type')!r} id={ev.get('event_id')!r} "
                f"size={size}B budget={budget}B session_id={session_id}"
            )

    assert not failures, "\n".join(failures[:10])

ROOT = Path(__file__).resolve().parents[3]
REPO_TMP_DIR = ROOT / "tmp"
REPO_TMP_DIR.mkdir(parents=True, exist_ok=True)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))

# Fallback imports using explicit file paths so that the test
# can run even when the application and core packages are not
# installed in the runtime environment.
import importlib.util

# AgentApplication
_app_path = Path(CORE_PY) / "agent_app" / "application_future.py"
_app_spec = importlib.util.spec_from_file_location("agent_app.application_future", str(_app_path))
if _app_spec is None or _app_spec.loader is None:  # pragma: no cover - defensive
    raise ImportError("cannot load AgentApplication module")
_app_mod = importlib.util.module_from_spec(_app_spec)
_app_spec.loader.exec_module(_app_mod)
AgentApplication = getattr(_app_mod, "AgentApplication")

# TerminalApplication
_term_app_path = Path(APP_PY) / "agent_terminal_app" / "terminal_app.py"
_term_app_spec = importlib.util.spec_from_file_location("agent_terminal_app.terminal_app", str(_term_app_path))
if _term_app_spec is None or _term_app_spec.loader is None:  # pragma: no cover - defensive
    raise ImportError("cannot load TerminalApplication module")
_term_app_mod = importlib.util.module_from_spec(_term_app_spec)
_term_app_spec.loader.exec_module(_term_app_mod)
TerminalApplication = getattr(_term_app_mod, "TerminalApplication")

# TerminalRenderContext
_event_render_path = Path(APP_PY) / "agent_terminal_app" / "event_rendering.py"
_event_spec = importlib.util.spec_from_file_location("agent_terminal_app.event_rendering", str(_event_render_path))
if _event_spec is None or _event_spec.loader is None:  # pragma: no cover - defensive
    raise ImportError("cannot load event_rendering module")
_event_mod = importlib.util.module_from_spec(_event_spec)
_event_spec.loader.exec_module(_event_mod)
TerminalRenderContext = getattr(_event_mod, "TerminalRenderContext")


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OPENAI_BASE_URL = f"{OLLAMA_HOST}/v1"
MODEL_TOOLS = os.getenv("OLLAMA_MODEL_QWEN3", "qwen3:0.6b")


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _run(cmd: List[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


@pytest.fixture(scope="module")
def ensure_model() -> None:
    """Ensure Ollama and the configured tools model are available."""

    if _which("ollama") is None:
        pytest.skip("ollama is not installed; skipping terminal Ollama tools test")
    try:
        _run(["ollama", "ps"], timeout=30)
    except Exception:
        pytest.skip("ollama command unavailable or not responding; skipping")

    try:
        cp = _run(["ollama", "pull", MODEL_TOOLS], timeout=1200)
        if cp.returncode != 0:
            msg = cp.stderr.decode("utf-8", errors="ignore")
            pytest.skip(f"failed to pull model {MODEL_TOOLS}: {msg}")
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"could not pull model {MODEL_TOOLS}: {exc}")


def _make_terminal_app_config(tmp_path: Path) -> Path:
    """Create an application-layer config with tools, reasoning, and timestamp.

    The config mirrors the core application-layer Ollama tools integration but
    adds the TimestampExtension so that message metadata includes a
    `timestamp` field and a corresponding `message_footer` UI element.
    """

    cfg: Dict[str, Any] = {
        "providers": {
            "ollama_tools": {
                "provider": "openai_compatible",
                "model": MODEL_TOOLS,
                "base_url": OPENAI_BASE_URL,
                "timeout": 180,
                "allowed_paths": ["."],
                "max_file_size": 1024 * 1024,
            }
        },
        "plugins": [
            "plugins.openai_provider.OpenAICompatibleProvider",
            "plugins.openai_tools_extension.OpenAIToolsExtension",
            "plugins.ollama_thinking_extension.OllamaThinkingExtension",
            "plugins.timestamp_extension.TimestampExtension",
            "plugins.file_reader_tool.FileReaderTool",
            "plugins.file_writer_tool.FileWriterTool",
        ],
        "agents": {
            "default": {"provider": "ollama_tools"},
        },
    }

    path = tmp_path / "terminal_ollama_tools_config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


@pytest.mark.ollama
def test_terminal_rendering_with_ollama_tools_and_timestamp(tmp_path: Path, ensure_model: None) -> None:
    """End-to-end smoke test for TerminalRenderContext with Ollama tools.

    Ensures that:
    - Events produced by AgentApplication + tool loop can be rendered
      by TerminalRenderContext without exceptions.
    - Assistant and Tool headers appear in the rendered output.
    - The timestamp injected by TimestampExtension is rendered via
      footer helpers (either directly or via the message_footer UI schema).
    """

    config_path = _make_terminal_app_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root))
    term_app = TerminalApplication(config_path=str(config_path), session_root=str(session_root), agent_app=app)

    # Create a temporary file to exercise FileReaderTool via tools extension.
    # Use a repository-local temporary directory (under ROOT / "tmp") so that
    # paths remain within the default allowed_paths configuration (["."]).
    import tempfile

    file_path = None
    try:
        with tempfile.NamedTemporaryFile("w+", delete=False, dir=str(REPO_TMP_DIR)) as tf:
            tf.write("hello from tools via terminal test")
            tf.flush()
            file_path = tf.name

        # Start a session and append a user message that should trigger tools.
        session = term_app.start_new_session(agent_id="default")
        term_app.append_user_message(
            f"Use read_file to read the contents of this file and summarise it: {file_path}",
            metadata=None,
        )

        # Run a streaming request; this will publish events into the shared event store.
        final_session, final_messages, request_id = term_app.send_request(stream=True)
        assert final_session is not None
        assert request_id is not None

    finally:
        if file_path is not None:
            try:
                os.unlink(file_path)
            except Exception:
                pass

    # Collect all events for this session.
    events = term_app.list_events(session_id=session.session_id, limit=1000)
    assert any(ev.get("type") == "partial" for ev in events)
    assert any(ev.get("type") == "tool_results" for ev in events)
    assert any(ev.get("type") == "final" for ev in events)

    # Build a fresh renderer context and capture output via a custom writer.
    lines: List[str] = []

    def write(text: str) -> None:
        lines.append(text)

    renderer = TerminalRenderContext(
        app=term_app,
        footer_elements_supplier=lambda: term_app.message_footer_elements(),
    )

    for ev in events:
        renderer.render_event(ev, write)

    rendered = "\n".join(lines)

    # Basic sanity checks on headers.
    assert "Assistant:" in rendered
    assert "Tool:" in rendered
    assert "thinking:" in rendered or "thinking: " in rendered

    # Find a timestamp from events (added by TimestampExtension).
    ts_value: Optional[str] = None
    for ev in events:
        for msg in ev.get("messages") or []:
            if not isinstance(msg, dict):
                continue
            md = msg.get("metadata") or {}
            if isinstance(md, dict) and isinstance(md.get("timestamp"), str):
                ts_value = md["timestamp"]
                break
        if ts_value:
            break

    assert isinstance(ts_value, str) and ts_value
    # Assert that the timestamp from metadata appears in the rendered output.
    # The terminal renderer formats datetime footer values using the local
    # locale/clock.
    try:
        from datetime import datetime, timezone

        dt = datetime.fromisoformat(ts_value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        formatted = dt.astimezone().strftime("%c")
    except Exception:  # pragma: no cover - defensive
        formatted = None

    assert (ts_value in rendered) or (isinstance(formatted, str) and formatted in rendered)


@pytest.mark.ollama
def test_events_are_lean_in_tool_loop_session(tmp_path: Path, ensure_model: None) -> None:
    """Guard against embedding full sessions in published events.

    The tool loop itself already yields incremental events. This test
    ensures that all events published to the shared event store remain
    small relative to the size of an individual message, even when the
    session history is large.
    """

    config_path = _make_terminal_app_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root))
    term_app = TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
        agent_app=app,
    )

    import tempfile

    file_a = None
    file_out = None
    try:
        big_payload = "A" * 4096

        with tempfile.NamedTemporaryFile("w+", delete=False, dir=str(REPO_TMP_DIR)) as tf_a:
            tf_a.write("file A\n" + big_payload)
            tf_a.flush()
            file_a = tf_a.name

        with tempfile.NamedTemporaryFile("w+", delete=False, dir=str(REPO_TMP_DIR)) as tf_out:
            tf_out.write("placeholder")
            tf_out.flush()
            file_out = tf_out.name

        session = term_app.start_new_session(agent_id="default")

        system_message = (
            "You are a helpful assistant. When asked about file operations, ALWAYS use the tools. "
            "Do not answer without using the tools first."
        )
        term_app.add_message(
            session.session_id,
            role="system",
            content=system_message,
            metadata=None,
        )

        term_app.append_user_message(
            "Follow these steps exactly:\n"
            f"1) Use read_file to read this file: {file_a}\n"
            f"2) Use write_file to write 'ok' into this file: {file_out}\n"
            "3) Reply with the exact contents of file (1) only.",
            metadata=None,
        )

        _final_session, _final_messages, request_id = term_app.send_request(stream=True)
        assert request_id is not None

        # Append one more message so we exercise post-tool-loop event publishing.
        term_app.append_user_message("thanks", metadata=None)

    finally:
        for path in (file_a, file_out):
            if path is None:
                continue
            try:
                os.unlink(path)
            except Exception:
                pass

    events = term_app.list_events(session_id=session.session_id, limit=20000)
    assert any(ev.get("type") == "tool_results" for ev in events)
    assert any(ev.get("type") == "final" for ev in events)

    _assert_events_within_single_message_budget(events=events, app=app)
