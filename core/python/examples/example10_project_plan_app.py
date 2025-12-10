"""
PROJECT_PLAN Example 10: FastAPI App + Console Client (Ollama)

This example shows how to wrap ``agent_core.AgentCore`` in a small
HTTP JSON application and pair it with a tiny console client.

The responsibilities mirror ``agent_app.AgentApplication`` in a
simplified way but stay on the core API level:

- the application owns a single AgentCore instance
- the application owns provider configuration
- the application owns session storage (in memory here)
- HTTP handlers translate HTTP JSON into core ``Session`` / messages
- a console client runs in-process and calls the same helpers as the HTTP routes

Out of the box the app is configured to use
``plugins.openai_provider.OpenAICompatibleProvider`` against a local
Ollama /v1 endpoint.

Environment variables (optional):
- OLLAMA_HOST (default: http://localhost:11434)
- OLLAMA_MODEL (default: llama3.2:1b)
- EXAMPLE10_PROVIDER (default: "openai_compatible"; can be set to
  "echo_openai_like" for offline/testing use)

Usage (API server):
- Run directly with the example script:

    $ python core/python/examples/example10_project_plan_app.py

  This will start a FastAPI app on http://127.0.0.1:8000.

- Or run with uvicorn explicitly:

    $ uvicorn examples.example10_project_plan_app:app --reload

Usage (console client):
- Run in a terminal:

    $ python core/python/examples/example10_project_plan_app.py --console

  This mode does not require the HTTP server; it calls the same
  helper functions that the FastAPI routes use.

Provider selection:
- By default the app uses the OpenAI-compatible provider with Ollama.
- For offline/testing use you can either:

  * set ``EXAMPLE10_PROVIDER=echo_openai_like`` in the environment, or
  * pass ``{"config_overrides": {"provider": "echo_openai_like"}}``
    in the JSON body of ``POST /sessions/{session_id}/send``.
"""

from __future__ import annotations

import argparse
import os
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException  # type: ignore[reportMissingImports]

from agent_core import AgentCore, Session
from plugins.openai_provider import OpenAICompatibleProvider
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider


# ---------------------------------------------------------------------------
# Application wiring: core, config, and in-memory sessions
# ---------------------------------------------------------------------------

_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
_OLLAMA_BASE_URL = f"{_OLLAMA_HOST}/v1"
_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
_DEFAULT_PROVIDER = os.getenv("EXAMPLE10_PROVIDER", "openai_compatible")

app = FastAPI(title="AgentCore Example 10")

# A single AgentCore instance holds the processing pipeline.
_core = AgentCore()
_core.register_provider(OpenAICompatibleProvider)
_core.register_provider(EchoOpenAILikeProvider)

# Application-managed provider configuration. Real applications would load
# this from a file or database; here we keep it inline for clarity.
_APP_CONFIG: Dict[str, Any] = {
    "provider": _DEFAULT_PROVIDER,
    "model": _OLLAMA_MODEL,
    "base_url": _OLLAMA_BASE_URL,
    "timeout": 60,
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


# ---------------------------------------------------------------------------
# HTTP routes
# ---------------------------------------------------------------------------


@app.post("/sessions")
def create_session(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a new session and optionally add a system message.

    Request JSON body (all fields optional):

        {"system_message": "You are a helpful assistant."}

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
    """Run the model for the current session and return the reply.

    Request JSON body (all fields optional):

        {"config_overrides": {...}}

    Response JSON:

        {
            "session": Session-as-dict,
            "messages": [assistant messages for this turn],
            "request_id": str,
        }
    """

    session = _get_session_required(session_id)

    overrides = (payload or {}).get("config_overrides") or {}
    if overrides is not None and not isinstance(overrides, dict):
        raise HTTPException(status_code=400, detail="config_overrides must be an object")

    config = _build_config(overrides)
    request_id = str(uuid.uuid4())

    final_session, final_messages = _core.send_request(session, config)
    _SESSIONS[session_id] = final_session

    return {
        "session": final_session.to_dict(),
        "messages": final_messages,
        "request_id": request_id,
    }



# ---------------------------------------------------------------------------
# Console client utilities
# ---------------------------------------------------------------------------


def run_console() -> None:  # pragma: no cover - manual usage
    """Very small console client that talks to the application in-process.

    Typical usage::

        $ python core/python/examples/example10_project_plan_app.py --console

    This does not require the HTTP server to be running; it calls the
    same helper functions that the FastAPI routes use.
    """

    created = create_session({"system_message": "You are a helpful assistant."})
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

    Intended usage:

        uvicorn examples.example10_project_plan_app:app --reload
    """

    return app


def _run_server(host: str = "127.0.0.1", port: int = 8000) -> None:  # pragma: no cover
    """Run the FastAPI app with uvicorn on the given host/port.

    This helper is used by the module's ``__main__`` block. It is
    equivalent to invoking::

        uvicorn examples.example10_project_plan_app:app --host HOST --port PORT

    from the command line.
    """

    try:
        import uvicorn  # type: ignore[import-not-found]
    except Exception:
        import sys as _sys

        print(
            "Uvicorn is not installed. Run with: "
            "`pip install uvicorn[standard]` and then "
            "`uvicorn examples.example10_project_plan_app:app`.",
            file=_sys.stderr,
        )
        return

    uvicorn.run(
        "examples.example10_project_plan_app:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":  # pragma: no cover - manual execution only
    parser = argparse.ArgumentParser(description="Example 10: FastAPI app + console client")
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
