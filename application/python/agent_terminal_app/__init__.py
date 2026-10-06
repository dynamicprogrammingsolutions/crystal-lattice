"""agent_terminal_app: FastAPI + terminal UI example.

This package provides a minimal application that builds on the
``agent_app.AgentApplication`` API from the core SDK. It exposes:

- a FastAPI-based JSON API for sessions and requests
- an in-process terminal client built with ``prompt_toolkit``
- a context-managed local runtime for one-shot Python and CLI agent runs

The server and terminal share an in-memory event store so that multiple frontends can
observe the same request/response streams for a given session.

The implementation is intentionally small and focused on structure
rather than features. It is meant as a starting point for richer
applications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent_app import CompactHistory, CompactMessage

    from .local_runtime import (
        AgentRunResult,
        LocalAgentRuntime,
        RunError,
        RunProgress,
        RunProgressKind,
        RunPersistence,
        RunStatus,
        open_runtime,
    )
    from .server import app, run_api
    from .terminal import run_terminal

__all__ = [
    "AgentRunResult",
    "CompactHistory",
    "CompactMessage",
    "LocalAgentRuntime",
    "RunError",
    "RunProgress",
    "RunProgressKind",
    "RunPersistence",
    "RunStatus",
    "app",
    "open_runtime",
    "run_api",
    "run_terminal",
]


def __getattr__(name: str):
    if name in {
        "AgentRunResult",
        "CompactHistory",
        "CompactMessage",
        "LocalAgentRuntime",
        "RunError",
        "RunProgress",
        "RunProgressKind",
        "RunPersistence",
        "RunStatus",
        "open_runtime",
    }:
        from agent_app import CompactHistory, CompactMessage

        from .local_runtime import (
            AgentRunResult,
            LocalAgentRuntime,
            RunError,
            RunProgress,
            RunProgressKind,
            RunPersistence,
            RunStatus,
            open_runtime,
        )

        return {
            "AgentRunResult": AgentRunResult,
            "CompactHistory": CompactHistory,
            "CompactMessage": CompactMessage,
            "LocalAgentRuntime": LocalAgentRuntime,
            "RunError": RunError,
            "RunProgress": RunProgress,
            "RunProgressKind": RunProgressKind,
            "RunPersistence": RunPersistence,
            "RunStatus": RunStatus,
            "open_runtime": open_runtime,
        }[name]
    if name in {"app", "run_api"}:
        from .server import app, run_api

        return {"app": app, "run_api": run_api}[name]
    if name == "run_terminal":
        from .terminal import run_terminal

        return run_terminal
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
