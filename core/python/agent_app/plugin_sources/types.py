from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Protocol


@dataclass(frozen=True)
class PluginContext:
    cache_dir: Path
    policy: Mapping[str, Any]


@dataclass(frozen=True)
class PluginResolution:
    classes: List[type]
    errors: List[Dict[str, Any]]


class PluginSource(Protocol):
    def supports(self, spec: Any) -> bool:
        """Return True if this source can resolve the spec."""

    def resolve(self, spec: Any, ctx: PluginContext) -> PluginResolution:
        """Resolve the spec into plugin classes."""
