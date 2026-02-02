from __future__ import annotations

import importlib
from typing import Any, Dict, List

from .types import PluginContext, PluginResolution


class DottedClassSource:
    """Resolve a dotted class path like ``pkg.module.Class``."""

    def supports(self, spec: Any) -> bool:
        if not isinstance(spec, str):
            return False
        s = spec.strip()
        if not s or s.startswith("path:") or s.startswith("git+"):
            return False
        return "." in s

    def resolve(self, spec: Any, ctx: PluginContext) -> PluginResolution:
        if not isinstance(spec, str):
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_path_invalid",
                "detail": "Dotted class spec must be a string",
                "path": spec,
            }])

        module_path, sep, attr = spec.rpartition(".")
        if not sep:
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_path_invalid",
                "detail": "Invalid dotted class spec (expected module.Class)",
                "path": spec,
            }])
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, attr)
        except Exception as exc:
            return PluginResolution(classes=[], errors=[{
                "type": "plugin_import_error",
                "detail": str(exc),
                "path": spec,
            }])
        return PluginResolution(classes=[cls], errors=[])
