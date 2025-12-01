"""Application layer for the AI Agent Platform.

Provides a thin, imperative shell around the functional `agent_core` SDK.

The public entry point is `AgentApplication`, which exposes dict-based
operations suitable for HTTP/JSON APIs while delegating all message
processing to `AgentCore`.
"""

from __future__ import annotations

from .application import AgentApplication

__all__ = ["AgentApplication"]
