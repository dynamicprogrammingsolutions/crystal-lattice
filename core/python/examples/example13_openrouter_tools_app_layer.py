"""
PROJECT_PLAN Example 13: Application-layer OpenRouter + tools app.

This example mirrors Example 12 (OpenRouter + tools coding puzzle) but
is built on top of the higher-level :class:`agent_app.AgentApplication`
API instead of calling :class:`agent_core.AgentCore` directly.

Key points compared to Example 12:

- Uses a JSON config file to declare providers, plugins, and agents
- Uses filesystem-backed sessions via ``FilesystemSessionStore``
- Uses the application-layer non-streaming tool loop
- Exposes a thin FastAPI wrapper with the same basic routes:
  - ``POST /sessions`` – create session for an agent
  - ``POST /sessions/{session_id}/messages`` – append message
  - ``POST /sessions/{session_id}/send`` – send request (non-streaming by default)
- Supports per-request ``config_overrides`` and an optional ``max_loops``
  parameter that limits tool loop depth by temporarily overriding the
  application tool-loop configuration.

Configuration is loaded from the JSON file next to this module:

- ``example13_openrouter_tools_app_layer_config.json``

That config declares:

- Provider ``openrouter_tools`` with:
  - provider: ``"openrouter"`` (OpenRouterProvider)
  - model: ``"openai/gpt-5-mini"`` (can be changed in the file)
  - api_key: ``${env:OPENROUTER_API_KEY}`` (loaded via python-dotenv)
  - base_url: ``"https://openrouter.ai/api/v1"``
  - tools config: ``allowed_paths``, ``max_file_size``, ``working_directory``
  - reasoning config: ``enable_reasoning=True``, ``reasoning_effort="low"``
- Plugins:
  - ``plugins.openrouter_provider.OpenRouterProvider``
  - ``plugins.openrouter_reasoning_extension.OpenRouterReasoningExtension``
  - ``plugins.openrouter_tools_extension.OpenRouterToolsExtension``
  - ``plugins.file_reader_tool.FileReaderTool``
  - ``plugins.file_writer_tool.FileWriterTool``
- Agent ``default`` bound to provider ``openrouter_tools``

Environment variables (via .env at repo root):
- OPENROUTER_API_KEY (required for real calls)
- OPENROUTER_MODEL / OPENROUTER_BASE_URL: can be set by editing the
  config file or by using per-request ``config_overrides``.

Usage (API server):

    $ python core/python/examples/example13_openrouter_tools_app_layer.py

Usage (console client):

    $ python core/python/examples/example13_openrouter_tools_app_layer.py --console

Console mode uses the same application-layer tool loop as the HTTP API.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv  # type: ignore[import-not-found]

    load_dotenv()
except Exception:  # pragma: no cover - optional dependency
    pass

from fastapi import FastAPI, HTTPException  # type: ignore[reportMissingImports]

from agent_app import AgentApplication


# ---------------------------------------------------------------------------
# Application wiring: AgentApplication, config, and FastAPI
# ---------------------------------------------------------------------------

_EXAMPLES_DIR = Path(__file__).resolve().parent
_CONFIG_PATH = _EXAMPLES_DIR / "example13_openrouter_tools_app_layer_config.json"
_SESSION_ROOT = _EXAMPLES_DIR / "example13_sessions"

_app = AgentApplication(str(_CONFIG_PATH), str(_SESSION_ROOT))

app = FastAPI(title="AgentApplication Example 13 - OpenRouter tools app-layer")


# ---------------------------------------------------------------------------
# HTTP routes
# ---------------------------------------------------------------------------


@app.post("/sessions")
def create_session(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a new session for the default agent and optional system message.

    Request JSON body (all fields optional):

        {"agent_id": "default", "system_message": "..."}

    Response JSON:

        {"session": Session-as-dict, "errors": list[dict]}
    """

    data = payload or {}
    agent_id = data.get("agent_id") or "default"

    try:
        core, base_config, session = _app.create_agent_session(agent_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    system_message = data.get("system_message")
    if isinstance(system_message, str) and system_message:
        session = core.add_message(session, "system", system_message)
        _app.save_session(session)

    return {"session": session.to_dict(), "errors": _app.get_config_errors()}


@app.post("/sessions/{session_id}/messages")
def add_message(session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Append a message to an existing session via AgentApplication.

    Request JSON body:

        {"role": "user", "content": "...", "metadata"?: {...}}

    Response JSON:

        {"session": Session-as-dict}
    """

    role = payload.get("role")
    content = payload.get("content")
    metadata = payload.get("metadata")

    if not isinstance(role, str) or not isinstance(content, str):
        raise HTTPException(status_code=400, detail="role and content must be strings")

    if role not in ("system", "user", "assistant", "tool"):
        role = "user"

    ctx = _app.load_session(session_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="session not found")

    core, base_config, session = ctx

    try:
        new_session = core.add_message(session, role, content, metadata)
        _app.save_session(new_session)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"session": new_session.to_dict()}


@app.post("/sessions/{session_id}/send")
def send_request(session_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run the model for the current session using a non-streaming tool loop.

    Request JSON body (all fields optional):

        {
            "config_overrides": {...},  # merged into agent config
            "max_loops": 4,             # optional int, per-request tool loop cap
            "stream": false             # optional bool, default false
        }

    Non-streaming response JSON:

        {
            "session": Session-as-dict,
            "messages": [assistant messages for the final loop],
            "request_id": str,
            "loops": int,
        }

    Streaming response JSON (stream=true):

        {
            "session_id": str,
            "request_id": str,
            "stream": true,
            "status": "started",
        }
    """

    data = payload or {}

    overrides = data.get("config_overrides") or {}
    if overrides is not None and not isinstance(overrides, dict):
        raise HTTPException(status_code=400, detail="config_overrides must be an object")

    raw_max_loops = data.get("max_loops")
    max_loops: Optional[int]
    if raw_max_loops is None:
        max_loops = None
    elif isinstance(raw_max_loops, int) and raw_max_loops > 0:
        max_loops = raw_max_loops
    else:
        raise HTTPException(status_code=400, detail="max_loops must be a positive integer")

    stream = bool(data.get("stream"))

    if stream:
        raise HTTPException(status_code=400, detail="streaming is not implemented in this example")

    ctx = _app.load_session(session_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="session not found")

    core, base_config, session = ctx

    try:
        config = {**base_config, **(overrides or {})}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    loops = 0
    final_messages: list[Dict[str, Any]] = []

    while True:
        session, responses = core.send_request(session, config)
        _app.save_session(session)
        final_messages = list(responses)

        if not responses:
            break

        last = responses[-1]
        if last.get("role") != "assistant":
            break

        metadata = last.get("metadata") or {}
        tool_calls = metadata.get("tool_calls") or []
        if not tool_calls:
            break

        loops += 1
        if max_loops is not None and loops > max_loops:
            break

        tool_messages = core.execute_tool_calls(tool_calls, config)
        if not tool_messages:
            break

        for tm in tool_messages:
            session = core.add_message(
                session,
                role=tm.get("role", "tool"),
                content=tm.get("content", ""),
                metadata=tm.get("metadata"),
            )
        _app.save_session(session)

    return {
        "session": session.to_dict(),
        "messages": final_messages,
        "request_id": None,
        "loops": loops,
    }


# ---------------------------------------------------------------------------
# Console client utilities
# ---------------------------------------------------------------------------


def run_console() -> None:  # pragma: no cover - manual usage
    """Tiny console client that uses AgentApplication in-process.

    Typical usage::

        $ python core/python/examples/example13_openrouter_tools_app_layer.py --console
    """

    created = create_session(
        {
            "agent_id": "default",
            "system_message": "You are a coding assistant. Use tools to inspect and edit files when helpful.",
        }
    )
    session = created.get("session") or {}
    session_id = session.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        print("[error] could not create session")
        return

    print("Session started. Type 'exit' or 'quit' to leave.")

    while True:
        try:
            user = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):  # pragma: no cover - console UX
            print()
            break

        if not user:
            continue
        if user.lower() in {"exit", "quit"}:
            break

        add_message(session_id, {"role": "user", "content": user})
        result = send_request(session_id, {})

        messages = result.get("messages") or []
        text = ""
        if messages:
            text = messages[-1].get("content", "") or ""
        print(f"Assistant: {text}")


# ---------------------------------------------------------------------------
# Helper for running under a server (used by tests or uvicorn)
# ---------------------------------------------------------------------------


def run_example() -> FastAPI:  # pragma: no cover
    """Return the FastAPI app instance for uvicorn usage.

    Intended usage::

        uvicorn examples.example13_openrouter_tools_app_layer:app --reload
    """

    return app


def _run_server(host: str = "127.0.0.1", port: int = 8000) -> None:  # pragma: no cover
    """Run the FastAPI app with uvicorn on the given host/port."""

    try:
        import uvicorn  # type: ignore[import-not-found]
    except Exception:
        import sys as _sys

        print(
            "Uvicorn is not installed. Run with: "
            "`pip install uvicorn[standard]` and then "
            "`uvicorn examples.example13_openrouter_tools_app_layer:app`.",
            file=_sys.stderr,
        )
        return

    uvicorn.run(
        "examples.example13_openrouter_tools_app_layer:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":  # pragma: no cover - manual execution only
    parser = argparse.ArgumentParser(
        description="Example 13: AgentApplication OpenRouter + tools app-layer",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="run an interactive console client instead of the API server",
    )
    parser.add_argument("--host", default="127.0.0.1", help="host to bind the API server to")
    parser.add_argument("--port", type=int, default=8000, help="port to bind the API server to")

    args = parser.parse_args()

    if args.console:
        run_console()
    else:
        _run_server(host=args.host, port=args.port)
