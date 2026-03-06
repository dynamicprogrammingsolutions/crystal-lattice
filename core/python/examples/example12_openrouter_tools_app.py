"""
PROJECT_PLAN Example 12: OpenRouter + tools application layer.

This example shows how to build a small application around
``agent_core.AgentCore`` using the OpenRouter provider with tools and
reasoning enabled.

The responsibilities mirror Example 10 but add a simple non-streaming
tool loop on the application side:

- the application owns a single AgentCore instance
- the application owns provider and tool configuration
- the application owns session storage (in memory here)
- HTTP handlers translate HTTP JSON into core ``Session`` / messages
- the /send route runs a tool loop around ``AgentCore.send_request``
- a console client reuses the same helpers in-process

Out of the box the app is configured to use
``openrouter_plugins.openrouter_provider.OpenRouterProvider`` with
``openai/gpt-5-mini`` on OpenRouter. Tools are provided by
``FileReaderTool`` (read_file) and ``FileWriterTool`` (write_file).

This example requires the OpenRouter plugin bundle to be installed:

    $ python -m pip install -e plugins/openrouter

Environment variables (optional, but OPENROUTER_API_KEY is required for real calls):
- OPENROUTER_API_KEY (no default)
- OPENROUTER_MODEL (default: openai/gpt-5-mini)
- OPENROUTER_BASE_URL (default: https://openrouter.ai/api/v1)

Usage (API server):

    $ python core/python/examples/example12_openrouter_tools_app.py

This starts a FastAPI app on http://127.0.0.1:8000.

Usage (console client):

    $ python core/python/examples/example12_openrouter_tools_app.py --console

The console client talks to the same in-process helpers and runs the
same non-streaming tool loop as the HTTP API.

Tool loop behaviour (/sessions/{session_id}/send):

- merges application config with optional ``config_overrides``
- calls ``AgentCore.send_request`` once per loop
- inspects the last assistant message for ``metadata.tool_calls``
- executes tool calls via ``AgentCore.execute_tool_calls``
- appends tool results as ``role="tool"`` messages
- repeats until there are no more tool calls or ``max_loops`` is hit

The Example 12 test configures ``allowed_paths`` and
``working_directory`` per request so tools can safely read and write
Python files in a temporary directory when solving a coding puzzle.
"""

from __future__ import annotations

import argparse
import json
import os
import uuid
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv  # type: ignore[import-not-found]
    load_dotenv()
except Exception:  # pragma: no cover - optional dependency
    pass

from fastapi import FastAPI, HTTPException  # type: ignore[reportMissingImports]

from agent_core import AgentCore, Session
from openrouter_plugins.openrouter_provider import OpenRouterProvider
from openrouter_plugins.openrouter_reasoning_extension import OpenRouterReasoningExtension
from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
from plugins.file_reader_tool import FileReaderTool
from plugins.file_writer_tool import FileWriterTool
from plugins.request_options_feature import RequestOptionsFeature


# ---------------------------------------------------------------------------
# Application wiring: core, config, and in-memory sessions
# ---------------------------------------------------------------------------

_OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
_OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-5-mini")
_OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")

app = FastAPI(title="AgentCore Example 12 - OpenRouter tools app")

# A single AgentCore instance holds the processing pipeline.
_core = AgentCore()
_core.register_provider(
    OpenRouterProvider,
    extensions=[OpenRouterReasoningExtension, OpenRouterToolsExtension],
)
_core.register_feature(RequestOptionsFeature)
_core.register_tool(FileReaderTool)
_core.register_tool(FileWriterTool)

# Application-managed provider and tool configuration.
_APP_CONFIG: Dict[str, Any] = {
    "provider": "openrouter",
    "model": _OPENROUTER_MODEL,
    "api_key": _OPENROUTER_API_KEY,
    "base_url": _OPENROUTER_BASE_URL,
    "timeout": 300,
    # Tool configuration defaults; callers may override per request via
    # config_overrides.
    "allowed_paths": ["."],
    "max_file_size": 5 * 1024 * 1024,
    "working_directory": ".",
    # Reasoning configuration; OpenRouterReasoningExtension reads these.
    "enable_reasoning": True,
    "reasoning_effort": "low",
}

# Very small in-memory session store. The application, not the core,
# owns persistence.
_SESSIONS: Dict[str, Session] = {}


def _get_session_required(session_id: str) -> Session:
    session = _SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return session


def _build_config(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    base = dict(_APP_CONFIG)
    if overrides:
        base.update(overrides)
    return base


def _normalize_tool_calls_for_working_directory(
    tool_calls: List[Dict[str, Any]],
    working_directory: Optional[str],
) -> List[Dict[str, Any]]:
    """Adjust write_file tool calls to respect working_directory for relative paths.

    FileReaderTool already supports resolving relative paths via its own
    working_directory configuration. FileWriterTool currently interprets
    relative paths against the process working directory, so this helper
    rewrites write_file arguments to absolute paths under the configured
    working directory when needed.
    """
    if not working_directory or not isinstance(working_directory, str):
        return tool_calls

    normalized: List[Dict[str, Any]] = []
    for call in tool_calls:
        fn = call.get("function")
        if not isinstance(fn, dict):
            normalized.append(call)
            continue
        name = fn.get("name")
        if name != "write_file":
            normalized.append(call)
            continue

        args = fn.get("arguments")
        if not isinstance(args, str):
            normalized.append(call)
            continue

        try:
            parsed = json.loads(args)
        except Exception:
            normalized.append(call)
            continue

        file_path = parsed.get("file_path")
        if isinstance(file_path, str) and not os.path.isabs(file_path):
            parsed["file_path"] = os.path.join(working_directory, file_path)
            new_args = json.dumps(parsed, ensure_ascii=False)
            new_fn = {**fn, "arguments": new_args}
            normalized.append({**call, "function": new_fn})
        else:
            normalized.append(call)

    return normalized


# ---------------------------------------------------------------------------
# HTTP routes
# ---------------------------------------------------------------------------


@app.post("/sessions")
def create_session(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a new session and optionally add a system message.

    Request JSON body (all fields optional):

        {"system_message": "You are a coding assistant."}

    Response JSON:

        {"session": Session-as-dict}
    """

    base = _core.create_session()
    session = Session(
        session_id=base.session_id,
        messages=base.messages,
        metadata={},
    )


    system_message = (payload or {}).get("system_message")
    if isinstance(system_message, str) and system_message:
        session = _core.add_message(session, "system", system_message)

    _SESSIONS[session.session_id] = session
    return {"session": session.to_dict()}


@app.post("/sessions/{session_id}/messages")
def add_message(session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Append a message to an existing session.

    Request JSON body:

        {"role": "user", "content": "...", "metadata"?: {...}}

    Response JSON:

        {"session": Session-as-dict}
    """

    session = _get_session_required(session_id)

    role_value = payload.get("role")
    content = payload.get("content")
    metadata = payload.get("metadata")

    if not isinstance(role_value, str) or not isinstance(content, str):
        raise HTTPException(status_code=400, detail="role and content must be strings")

    if role_value not in ("system", "user", "assistant", "tool"):
        role_value = "user"

    new_session = _core.add_message(session, role_value, content, metadata)
    _SESSIONS[session_id] = new_session
    return {"session": new_session.to_dict()}


@app.post("/sessions/{session_id}/send")
def send_request(session_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run the model for the current session using a non-streaming tool loop.

    Request JSON body (all fields optional):

        {
            "config_overrides": {...},  # merged into application config
            "max_loops": 4              # optional int, default 4
        }

    Response JSON:

        {
            "session": Session-as-dict,
            "messages": [assistant messages for the final loop],
            "request_id": str,
            "loops": int,  # number of iterations executed
        }
    """

    session = _get_session_required(session_id)

    data = payload or {}
    overrides = data.get("config_overrides") or {}
    if overrides is not None and not isinstance(overrides, dict):
        raise HTTPException(status_code=400, detail="config_overrides must be an object")

    raw_max_loops = data.get("max_loops")
    if raw_max_loops is None:
        max_loops = 4
    elif isinstance(raw_max_loops, int) and raw_max_loops > 0:
        max_loops = raw_max_loops
    else:
        raise HTTPException(status_code=400, detail="max_loops must be a positive integer")

    config = _build_config(overrides)
    request_id = str(uuid.uuid4())

    loop_count = 0
    final_messages: List[Dict[str, Any]] = []

    while loop_count < max_loops:
        loop_count += 1

        session, responses = _core.send_request(session, config)
        _SESSIONS[session_id] = session
        final_messages = responses

        if not responses:
            break

        last = responses[-1]
        if last.get("role") != "assistant":
            break

        metadata = last.get("metadata") or {}
        tool_calls = metadata.get("tool_calls") or []
        if not tool_calls:
            break

        normalized_calls = _normalize_tool_calls_for_working_directory(
            tool_calls,
            config.get("working_directory"),
        )
        tool_msgs = _core.execute_tool_calls(normalized_calls, config)
        if not tool_msgs:
            break

        for tm in tool_msgs:
            session = _core.add_message(
                session,
                role=tm.get("role", "tool"),
                content=tm.get("content", ""),
                metadata=tm.get("metadata"),
                config=config,
            )
        _SESSIONS[session_id] = session

    return {
        "session": session.to_dict(),
        "messages": final_messages,
        "request_id": request_id,
        "loops": loop_count,
    }


# ---------------------------------------------------------------------------
# Console client utilities
# ---------------------------------------------------------------------------


def run_console() -> None:  # pragma: no cover - manual usage
    """Very small console client that talks to the application in-process.

    Typical usage::

        $ python core/python/examples/example12_openrouter_tools_app.py --console

    This does not require the HTTP server to be running; it calls the
    same helper functions that the FastAPI routes use and runs the same
    non-streaming tool loop.
    """

    created = create_session({"system_message": "You are a coding assistant. Use tools to inspect and edit files when helpful."})
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
# Helper for running under a server (used by tests too)
# ---------------------------------------------------------------------------


def run_example() -> FastAPI:  # pragma: no cover
    """Return the FastAPI app instance.

    Intended usage::

        uvicorn examples.example12_openrouter_tools_app:app --reload
    """

    return app


def _run_server(host: str = "127.0.0.1", port: int = 8000) -> None:  # pragma: no cover
    """Run the FastAPI app with uvicorn on the given host/port.

    This helper is used by the module's ``__main__`` block. It is
    equivalent to invoking::

        uvicorn examples.example12_openrouter_tools_app:app --host HOST --port PORT

    from the command line.
    """

    try:
        import uvicorn  # type: ignore[import-not-found]
    except Exception:
        import sys as _sys

        print(
            "Uvicorn is not installed. Run with: "
            "`pip install uvicorn[standard]` and then "
            "`uvicorn examples.example12_openrouter_tools_app:app`.",
            file=_sys.stderr,
        )
        return

    uvicorn.run(
        "examples.example12_openrouter_tools_app:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":  # pragma: no cover - manual execution only
    parser = argparse.ArgumentParser(description="Example 12: OpenRouter + tools application")
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
