from __future__ import annotations

import json
import os
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple

import pytest

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[3] / ".env")
except Exception:
    pass

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


REPO_ROOT = Path(__file__).resolve().parents[3]
BUILTIN_PLUGINS = REPO_ROOT / "plugins"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL_GEMINI_TOOLS", "google/gemini-2.5-flash-lite")

pytestmark = [pytest.mark.integration, pytest.mark.openrouter]


@pytest.fixture(scope="module")
def ensure_openrouter_api_key() -> str:
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set; skipping Gemini application integration tests")
    return OPENROUTER_API_KEY


def _write_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "plugin_policy": {"install_deps": True},
        "plugins": [
            "openrouter_plugins.openrouter_provider.OpenRouterProvider",
            "openrouter_plugins.openrouter_tools_extension.OpenRouterToolsExtension",
            "plugins.request_options_feature.RequestOptionsFeature",
        ],
        "providers": {
            "openrouter_gemini_tools": {
                "provider": "openrouter",
                "model": MODEL,
                "api_key": "${env:OPENROUTER_API_KEY}",
                "base_url": "https://openrouter.ai/api/v1",
                "timeout": 300,
                "temperature": 0.0,
                "working_directory": str(tmp_path),
                "allowed_paths": [str(tmp_path)],
                "project_temp_dir": str(tmp_path / ".temp"),
                "enable_reasoning": False,
                "system_message_enabled": False,
                "plugins": [
                    "path:${env:BUILTIN_PLUGINS}/gemini-tools",
                ],
            }
        },
        "agents": {
            "gemini": {
                "provider": "openrouter_gemini_tools",
            }
        },
    }

    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")
    return config_path


def _build_app(tmp_path: Path) -> AgentApplication:
    (tmp_path / ".temp").mkdir()
    config_path = _write_config(tmp_path)
    return AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides={
            "BUILTIN_PLUGINS": str(BUILTIN_PLUGINS),
            "OPENROUTER_API_KEY": OPENROUTER_API_KEY or "",
        },
    )


def _tool_messages(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tool_results = [event for event in events if event.get("type") == "tool_results"]
    assert tool_results, "expected tool_results event"

    messages: List[Dict[str, Any]] = []
    for event in tool_results:
        messages.extend(event.get("messages") or [])
    assert messages, "expected tool result messages"
    return messages


def _event_types(events: List[Dict[str, Any]]) -> List[str]:
    return [str(event.get("type") or "") for event in events]


def _first_tool_call(events: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
    final_events = [event for event in events if event.get("type") == "final"]
    assert final_events, "expected final events"

    tool_calls: List[Dict[str, Any]] = []
    for final_event in final_events:
        messages = final_event.get("messages") or []
        assistants = [message for message in messages if message.get("role") == "assistant"]
        for assistant in reversed(assistants):
            metadata = assistant.get("metadata") or {}
            tool_calls = metadata.get("tool_calls") or []
            if tool_calls:
                break
        if tool_calls:
            break
    assert tool_calls, "expected tool call metadata"

    function = tool_calls[0].get("function") or {}
    arguments = function.get("arguments") or {}
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    assert isinstance(arguments, dict), "expected JSON object tool arguments"
    return str(function.get("name") or ""), arguments


def _send_request_until_tool_call(
    app: AgentApplication,
    *,
    prepare_session: Any,
    overrides: Dict[str, Any] | None = None,
    expected_tool: str,
    max_attempts: int = 3,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    last_events: List[Dict[str, Any]] = []

    for _ in range(max_attempts):
        core, base_config, session = app.create_session("gemini")
        session = prepare_session(core, base_config, session)
        events = list(app.send_request(core, session, base_config, overrides=overrides, stream=False))
        last_events = events
        try:
            tool_name, tool_args = _first_tool_call(events)
        except AssertionError:
            continue
        if tool_name == expected_tool:
            return events, tool_args

    raise AssertionError(
        f"expected tool call for {expected_tool!r}; saw event types { _event_types(last_events) }"
    )


def _last_assistant_text(events: List[Dict[str, Any]]) -> str:
    final_events = [event for event in events if event.get("type") == "final"]
    assert final_events, "expected final events"

    for final_event in reversed(final_events):
        messages = final_event.get("messages") or []
        assistants = [message for message in messages if message.get("role") == "assistant"]
        for assistant in reversed(assistants):
            content = assistant.get("content")
            if isinstance(content, str) and content.strip():
                return content
    raise AssertionError("expected non-empty assistant message")


def _plugin_class_paths(app: AgentApplication) -> List[str]:
    return [entry["class_path"] for entry in app.list_plugins_for_agent("gemini")]


@contextmanager
def _local_html_server(body: str) -> Iterator[str]:
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            payload = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: Any) -> None:  # pragma: no cover
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}/story"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_agent_application_path_loaded_gemini_web_fetch_fallback_summarizes_local_content(
    ensure_openrouter_api_key: str,
    tmp_path: Path,
) -> None:
    del ensure_openrouter_api_key

    app = _build_app(tmp_path)
    assert app.get_config_errors() == []
    assert "gemini_tools.gemini_web_fetch_tool.GeminiWebFetchTool" in _plugin_class_paths(app)

    with _local_html_server(
        """
        <html>
          <head><title>Fallback Regression Page</title></head>
          <body>
            <h1>Local Fallback Headline</h1>
            <p>This page exists to verify Gemini web_fetch fallback summarization.</p>
          </body>
        </html>
        """
    ) as url:
        def _prepare_session(core: Any, base_config: Dict[str, Any], session: Any) -> Any:
            session = core.add_message(
                session,
                "system",
                (
                    "You are running a regression test. "
                    "Use the web_fetch tool exactly once when the user gives a URL. "
                    "Do not alter the URL and do not call web_fetch again after receiving the tool result."
                ),
                config=base_config,
            )
            session = core.add_message(
                session,
                "user",
                (
                    f"Use web_fetch on {url}. "
                    "After the single tool call, stop using tools and extract the heading from the fetched content."
                ),
                config=base_config,
            )
            return session

        events, tool_args = _send_request_until_tool_call(
            app,
            prepare_session=_prepare_session,
            overrides={
                "web_fetch_direct_mode": True,
                "web_fetch_rate_limit_requests": 100,
            },
            expected_tool="web_fetch",
        )
    assert tool_args.get("url") == url

    tool_messages = _tool_messages(events)
    assert tool_messages[0].get("metadata", {}).get("tool_name") == "web_fetch"
    assert "stream_request" not in tool_messages[0]["content"]
    assert "Error:" not in tool_messages[0]["content"]
    assert "Local Fallback Headline" in tool_messages[0]["content"]
    assert any(event.get("type") == "request_completed" for event in events)


def test_agent_application_path_loaded_gemini_replace_allows_empty_instruction(
    ensure_openrouter_api_key: str,
    tmp_path: Path,
) -> None:
    del ensure_openrouter_api_key

    target = tmp_path / "note.txt"
    target.write_text("alpha\n", encoding="utf-8")

    app = _build_app(tmp_path)
    assert app.get_config_errors() == []
    assert "gemini_tools.gemini_replace_tool.GeminiReplaceTool" in _plugin_class_paths(app)

    def _prepare_session(core: Any, base_config: Dict[str, Any], session: Any) -> Any:
        target.write_text("alpha\n", encoding="utf-8")
        session = core.add_message(
            session,
            "system",
            (
                "You are running a tool-call regression test. "
                "The test specifically verifies that the replace tool accepts an empty instruction field. "
                "You must use the replace tool exactly once. "
                "When the user gives exact tool arguments, copy them literally. "
                "The instruction field must be the empty string. "
                "After the tool runs successfully, reply with exactly OK and do not call more tools."
            ),
            config=base_config,
        )
        session = core.add_message(
            session,
            "user",
            (
                "Use the replace tool exactly once with these exact arguments and no substitutions: "
                '{"file_path":"note.txt","instruction":"","old_string":"alpha","new_string":"beta"}. '
                "The instruction field must stay the empty string. "
                "After the tool runs successfully, reply with exactly OK."
            ),
            config=base_config,
        )
        return session

    events, tool_args = _send_request_until_tool_call(
        app,
        prepare_session=_prepare_session,
        expected_tool="replace",
    )

    assert tool_args.get("file_path") == "note.txt"
    assert tool_args.get("old_string") == "alpha"
    assert tool_args.get("new_string") == "beta"
    assert tool_args.get("instruction", "") == ""

    tool_messages = _tool_messages(events)
    assert tool_messages[0].get("metadata", {}).get("tool_name") == "replace"
    assert "Error:" not in tool_messages[0]["content"]
    assert "Successfully modified file:" in tool_messages[0]["content"]
    assert target.read_text(encoding="utf-8") == "beta\n"
    assert _last_assistant_text(events).strip() == "OK"
    assert any(event.get("type") == "request_completed" for event in events)