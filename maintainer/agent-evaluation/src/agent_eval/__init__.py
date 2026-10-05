"""Programmatic evaluation kernel.

The generic package intentionally has no Crystal Lattice runtime dependency.
Environment integrations live in dedicated subpackages.
"""

from .environment import RunEnvironment
from .eval import AgentEval
from .result import Run, RunError, RunFailedError
from .services import (
    ArtifactWriter,
    Evidence,
    EvidenceJournal,
    EvidenceReference,
    EvidenceVisibility,
    RunServices,
)
from .workspace import WorkspaceFactory, git_workspace

__all__ = [
    "AgentEval",
    "ArtifactWriter",
    "Evidence",
    "EvidenceJournal",
    "EvidenceReference",
    "EvidenceVisibility",
    "Run",
    "RunEnvironment",
    "RunError",
    "RunFailedError",
    "RunServices",
    "WorkspaceFactory",
    "git_workspace",
]
