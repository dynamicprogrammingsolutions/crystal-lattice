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

    def continuation_fingerprint(self) -> object:
        """Return what a parent run's snapshot needs to restore here.

        The evaluation kernel compares this between a parent run and
        the environment continuing it. Environments that do not define
        it fall back to :meth:`fingerprint`, keeping continuation
        within one environment configuration. An environment whose
        snapshots are portable across its own configurations (for
        example a provider-agnostic session) can widen this surface
        without weakening :meth:`fingerprint`, which still guards
        caching and provenance.
        """

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
