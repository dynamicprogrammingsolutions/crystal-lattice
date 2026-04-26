"""agent_terminal_app: FastAPI + terminal UI example.

This package provides a minimal application that builds on the
``agent_app.AgentApplication`` API from the core SDK. It exposes:

- a FastAPI-based JSON API for sessions and requests
- an in-process terminal client built with ``prompt_toolkit``

Both share an in-memory event store so that multiple frontends can
observe the same request/response streams for a given session.

The implementation is intentionally small and focused on structure
rather than features. It is meant as a starting point for richer
applications.
"""

from __future__ import annotations

__all__ = ["app", "run_api", "run_terminal"]


def __getattr__(name: str):
    if name in {"app", "run_api"}:
        from .server import app, run_api

        return {"app": app, "run_api": run_api}[name]
    if name == "run_terminal":
        from .terminal import run_terminal

        return run_terminal
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
