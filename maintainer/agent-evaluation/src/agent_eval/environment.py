"""Execution-environment contract for the generic evaluation kernel."""

from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path
from typing import Generic, Protocol, TypeVar

from .services import RunServices


ContextT = TypeVar("ContextT")


class RunEnvironment(Protocol, Generic[ContextT]):
    """Provide execution-specific state to :class:`agent_eval.AgentEval`."""

    def fingerprint(self) -> object:
        """Return deterministic compatibility-relevant environment data."""

    def open(
        self,
        *,
        services: RunServices,
        workspace: Path | None,
        parent_snapshot: object | None,
    ) -> AbstractContextManager[ContextT]:
        """Open a fresh or restored context."""

    def snapshot(self, context: ContextT) -> object | None:
        """Return reusable state, or ``None`` when continuation is unsupported."""

    def finalize(self, context: ContextT) -> object:
        """Return a normalized environment-specific observation."""