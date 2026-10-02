"""Application-level plugin manager.

The plugin manager is intentionally thin: it only orchestrates across plugin
sources. Each source owns the low-level work to resolve a spec into one or more
plugin classes (installation/cloning, descriptor parsing, importing, etc.).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional
from agent_app.plugin_cache import PluginCache
from agent_app.plugin_sources.types import (
    PluginContext,
    PluginResolution,
    PluginSource,
)


class PluginManager:
    def __init__(
        self,
        *,
        cache_dir: Path,
        policy: Optional[Mapping[str, Any]] = None,
        sources: Optional[List[PluginSource]] = None,
    ) -> None:
        self.cache_dir = cache_dir
        self._cache = PluginCache(cache_dir)
        policy_dict: Dict[str, Any] = dict(policy or {})
        pip_args = policy_dict.get("pip_args") or []
        explicit_pip_cache = any(
            isinstance(arg, str) and (arg == "--cache-dir" or arg.startswith("--cache-dir="))
            for arg in pip_args
        )
        self._default_pip_cache = "pip_cache_dir" not in policy_dict and not explicit_pip_cache
        if self._default_pip_cache:
            policy_dict["pip_cache_dir"] = None
        policy_dict["_cache_in_use"] = self._cache.in_use_by_other
        self.policy: Mapping[str, Any] = policy_dict
        if sources is None:
            self.sources = self._default_sources()
        else:
            self.sources = list(sources)

    def _default_sources(self) -> List[PluginSource]:
        from agent_app.plugin_sources import (
            BashToolSource,
            DottedClassSource,
            GitRepoSource,
            LocalPathRepoSource,
            NodeToolSource,
        )
        from agent_app.plugin_sources.install import PipTargetInstallStrategy

        installer = PipTargetInstallStrategy()
        return [
            DottedClassSource(),
            NodeToolSource(),
            BashToolSource(),
            LocalPathRepoSource(installer=installer),
            GitRepoSource(installer=installer),
        ]

    def _default_pip_cache_dir(self, cache_dir: Path) -> Path:
        if cache_dir.name == "plugins":
            return cache_dir.parent / "pip"
        return cache_dir / "pip"

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

        ctx = PluginContext(cache_dir=self.cache_dir, policy=self.policy, claim=self._cache.claim)
        classes: List[type] = []
        errors: List[Dict[str, Any]] = []

        with self._cache.locked():
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

    def cleanup(self) -> None:
        with self._cache.locked():
            pip_cache = (
                self._default_pip_cache_dir(self.cache_dir) if self._default_pip_cache else None
            )
            self._cache.cleanup(pip_cache=pip_cache)

    def close(self) -> None:
        self._cache.close()

    def _find_source(self, spec: Any) -> Optional[PluginSource]:
        for src in self.sources:
            try:
                if src.supports(spec):
                    return src
            except Exception:
                continue
        return None


__all__ = ["PluginManager"]
