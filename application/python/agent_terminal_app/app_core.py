"""Deprecated helper module for agent_terminal_app.

This module previously contained shared application wiring, but the
current architecture uses per-frontend application classes instead
(:class:`ServerApplication` and :class:`TerminalApplication`).

It is kept as a minimal stub to avoid import errors in any downstream
code but no longer provides any functionality.
"""

from __future__ import annotations

__all__ = []
