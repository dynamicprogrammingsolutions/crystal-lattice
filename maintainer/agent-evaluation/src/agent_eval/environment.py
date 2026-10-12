"""Execution-environment contract for the generic evaluation kernel."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generic, Protocol, TypeVar

from .result import RunError
from .services import RunServices


ContextT = TypeVar("ContextT")


@dataclass
class IsolatedExecutionOutcome:
    """Result of an environment-owned isolated program execution.

    Environments may expose an optional ``isolated_execute`` method
    (detected by the kernel via ``getattr``) that runs the whole
    open → program → snapshot → finalize lifecycle in a worker the
    environment controls — for example a forked process whose global
    state is private to one run. The kernel falls back to its inline
    composition whenever the method is absent.
    """

    value: object = None
    snapshot: object | None = None
    observation: object = field(default_factory=dict)
    error: RunError | None = None


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

    # Optional extension (detected, not required): environments that can
    # isolate a whole execution in a worker define
    #
    #     def isolated_execute(
    #         self,
    #         *,
    #         services: RunServices,
    #         workspace: Path | None,
    #         parent_snapshot: object | None,
    #         program: Callable[[ContextT], object],
    #         writer: ArtifactWriter,
    #     ) -> IsolatedExecutionOutcome
    #
    # and the kernel prefers it over its inline composition. The
    # outcome mirrors the inline contract: ``value`` from the program,
    # ``snapshot``/``observation`` from the environment hooks, and
    # ``error`` capturing the first failed phase with its traceback
    # written through ``writer``.
