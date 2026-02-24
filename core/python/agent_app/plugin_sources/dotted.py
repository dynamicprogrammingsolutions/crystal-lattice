from __future__ import annotations

import importlib
import re
from typing import Any, Dict, List

from .types import PluginContext, PluginResolution


class DottedClassSource:
    """Resolve a dotted class path like ``pkg.module.Class``."""

    _dotted_re = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+$")

    def supports(self, spec: Any) -> bool:
        if not isinstance(spec, str):
            return False
        s = spec.strip()
        if not s:
            return False
        return self._dotted_re.fullmatch(s) is not None

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
