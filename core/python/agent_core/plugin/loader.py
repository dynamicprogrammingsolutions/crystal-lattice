from __future__ import annotations

"""Core plugin loader interfaces and minimal dotted-path implementation.

This module defines small, dependency-free interfaces and helpers that both the
application layer and other consumers can rely on. It deliberately avoids any
network or package installation logic.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Protocol
import importlib


@dataclass
class PluginMetadata:
    """Describes the origin and install details of a loaded plugin.

    The core does not populate these fields beyond what is known locally.
    Application-level loaders (git, local path, wheel) should fill in
    additional details (ref, commit, install_dir, installed_at).
    """

    id: str
    kind: Optional[str]
    origin: str
    entry: str
    raw_spec: Any
    ref: Optional[str] = None
    commit: Optional[str] = None
    install_dir: Optional[Path] = None
    installed_at: Optional[str] = None


@dataclass
class PluginLoadResult:
    """Result of attempting to load a plugin class."""

    cls: Optional[type]
    metadata: Optional[PluginMetadata]
    error: Optional[Dict[str, Any]]


class PluginSource(Protocol):
    """Protocol for plugin sources (dotted path, local path, git, wheel, ...)."""

    def supports(self, raw_spec: Any) -> bool:
        """Return True if this loader can handle ``raw_spec``."""

    def load(self, raw_spec: Any, *, cache_dir: Path, policy: Mapping[str, Any]) -> PluginLoadResult:
        """Load and import a plugin class from ``raw_spec``.

        Core implementations should not perform network or subprocess work.
        Application-level implementations may ignore ``cache_dir`` and
        ``policy`` when not applicable.
        """


def get_plugin_id(plugin_class: type) -> str:
    """Return stable plugin id (prefer class-level ``name`` over class name)."""

    name_attr = getattr(plugin_class, "name", None)
    if isinstance(name_attr, str) and name_attr:
        return name_attr
    return plugin_class.__name__


def _deduce_kind_from_class(plugin_class: type) -> str:
    """Infer plugin kind by duck-typing.

    Order matches legacy discovery:
    - provider: has ``stream_api`` or ``call_api``
    - tool: has both ``get_tool_schemas`` and ``execute_tool``
    - extension: has ``process_chunk``
    - application: heuristics for app plugins (``get_actions`` or ``execute_action``)
    - feature: fallback
    """

    if hasattr(plugin_class, "stream_api") or hasattr(plugin_class, "call_api"):
        return "providers"
    if hasattr(plugin_class, "get_tool_schemas") and hasattr(plugin_class, "execute_tool"):
        return "tools"
    if hasattr(plugin_class, "process_chunk"):
        return "extensions"
    # Application-level plugin heuristic (app layer protocol):
    if hasattr(plugin_class, "get_actions") or hasattr(plugin_class, "execute_action"):
        return "application"
    return "features"


def validate_plugin_for_kind(plugin_class: type, expected_kind: str) -> Optional[Dict[str, Any]]:
    """Return None if ``plugin_class`` matches ``expected_kind`` else an error dict.

    expected_kind should be one of: "providers", "extensions", "features",
    "tools", or "application".
    """

    actual = _deduce_kind_from_class(plugin_class)
    if actual == expected_kind:
        return None
    return {
        "type": "plugin_type_mismatch",
        "detail": f"Expected kind {expected_kind!r} but inferred {actual!r}",
        "expected": expected_kind,
        "actual": actual,
        "class": f"{getattr(plugin_class, '__module__', '')}.{getattr(plugin_class, '__qualname__', '')}",
    }


class DottedPathSource:
    """Minimal dotted-path loader (module.Class) with no side effects."""

    def supports(self, raw_spec: Any) -> bool:  # type: ignore[override]
        if not isinstance(raw_spec, str):
            return False
        s = raw_spec.strip()
        if not s or "::" in s:
            return False
        # Avoid claiming other well-known prefixes (left for app loaders)
        if s.startswith("git+") or s.startswith("path:") or s.startswith("file:"):
            return False
        # Basic dotted path check (module.Class)
        return "." in s

    def load(self, raw_spec: Any, *, cache_dir: Path, policy: Mapping[str, Any]) -> PluginLoadResult:  # type: ignore[override]
        if not isinstance(raw_spec, str):
            return PluginLoadResult(cls=None, metadata=None, error={
                "type": "plugin_path_invalid",
                "detail": "DottedPathSource requires a string spec",
                "path": raw_spec,
            })
        path = raw_spec.strip()
        module_path, sep, attr = path.rpartition(".")
        if not sep:
            return PluginLoadResult(cls=None, metadata=None, error={
                "type": "plugin_path_invalid",
                "detail": "Invalid plugin path: expected 'module.Class'",
                "path": raw_spec,
            })
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, attr)
        except Exception as exc:  # pragma: no cover - import failures surfaced
            return PluginLoadResult(cls=None, metadata=None, error={
                "type": "plugin_import_error",
                "detail": str(exc),
                "path": raw_spec,
            })

        metadata = PluginMetadata(
            id=get_plugin_id(cls),
            kind=None,
            origin=module_path,
            entry=path,
            raw_spec=raw_spec,
        )
        return PluginLoadResult(cls=cls, metadata=metadata, error=None)


__all__ = [
    "PluginMetadata",
    "PluginLoadResult",
    "PluginSource",
    "DottedPathSource",
    "get_plugin_id",
    "validate_plugin_for_kind",
]
