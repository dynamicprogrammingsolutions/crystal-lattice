from __future__ import annotations

"""Application-level plugin manager.

The plugin manager is intentionally thin: it only orchestrates across plugin
sources. Each source owns the low-level work to resolve a spec into one or more
plugin classes (installation/cloning, descriptor parsing, importing, etc.).
"""

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from agent_app.plugin_sources import (
    DottedClassSource,
    GitRepoSource,
    LocalPathRepoSource,
    PluginContext,
    PluginResolution,
    PluginSource,
)
from agent_app.plugin_sources.install import PipTargetInstallStrategy


class PluginManager:
    def __init__(
        self,
        *,
        cache_dir: Path,
        policy: Optional[Mapping[str, Any]] = None,
        sources: Optional[List[PluginSource]] = None,
    ) -> None:
        self.cache_dir = cache_dir
        self.policy: Mapping[str, Any] = policy or {}
        if sources is None:
            installer = PipTargetInstallStrategy()
            self.sources: List[PluginSource] = [
                DottedClassSource(),
                LocalPathRepoSource(installer=installer),
                GitRepoSource(installer=installer),
            ]
        else:
            self.sources = sources

    def resolve_all(self, specs: Any) -> PluginResolution:
        """Resolve plugin specs into classes.

        Args:
            specs: A list of specs, or a single spec. Specs are strings or dicts.

        Returns:
            PluginResolution with accumulated classes and errors.
        """

        items: List[Any]
        if specs is None:
            items = []
        elif isinstance(specs, list):
            items = specs
        else:
            items = [specs]

        ctx = PluginContext(cache_dir=self.cache_dir, policy=self.policy)
        classes: List[type] = []
        errors: List[Dict[str, Any]] = []

        for spec in items:
            src = self._find_source(spec)
            if src is None:
                errors.append(
                    {
                        "type": "plugin_path_invalid",
                        "detail": "No plugin source supports the given spec",
                        "path": spec,
                    }
                )
                continue
            res = src.resolve(spec, ctx)
            classes.extend(res.classes)
            errors.extend(res.errors)

        return PluginResolution(classes=classes, errors=errors)

    def _find_source(self, spec: Any) -> Optional[PluginSource]:
        for src in self.sources:
            try:
                if src.supports(spec):
                    return src
            except Exception:
                continue
        return None


__all__ = ["PluginManager"]
