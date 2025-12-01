from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Tuple
import json
import os
import importlib


JsonMapping = Mapping[str, Any]


def load_raw_config(path: str | Path) -> Dict[str, Any]:
    """Load JSON configuration from disk.

    The function performs no placeholder resolution; callers should invoke
    :func:`resolve_placeholders` afterwards.
    """

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_value(value: Any, path: str, env: Mapping[str, str], errors: List[Dict[str, Any]]) -> Any:
    """Resolve a single value, handling ${env:...} and ${file:...} placeholders.

    Only whole-string placeholders are supported in the MVP.
    """

    if not isinstance(value, str):
        return value

    if value.startswith("${env:") and value.endswith("}"):
        var_name = value[len("${env:") : -1]
        resolved = env.get(var_name, "")
        if resolved == "":
            errors.append(
                {
                    "path": path,
                    "type": "env_missing",
                    "detail": f"Environment variable {var_name!r} is not set",
                }
            )
        return resolved

    if value.startswith("${file:") and value.endswith("}"):
        file_ref = value[len("${file:") : -1]
        file_path = Path(os.path.expanduser(file_ref))
        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(
                {
                    "path": path,
                    "type": "file_missing",
                    "detail": f"Could not read file {file_ref!r}: {exc}",
                }
            )
            return ""
        return text

    return value


def _walk_and_resolve(obj: Any, path: str, env: Mapping[str, str], errors: List[Dict[str, Any]]) -> Any:
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for key, value in obj.items():
            sub_path = f"{path}.{key}" if path else str(key)
            out[key] = _walk_and_resolve(value, sub_path, env, errors)
        return out
    if isinstance(obj, list):
        return [
            _walk_and_resolve(value, f"{path}[{index}]", env, errors)
            for index, value in enumerate(obj)
        ]
    return _resolve_value(obj, path, env, errors)


def resolve_placeholders(
    raw: Mapping[str, Any], env: Mapping[str, str] | None = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Resolve ${env:...} and ${file:...} placeholders in a config mapping.

    Missing environment variables or files are recorded as error dictionaries
    and replaced with an empty string, but they do not raise exceptions.

    Returns a tuple of ``(resolved_config, errors)``.
    """

    errors: List[Dict[str, Any]] = []
    resolved = _walk_and_resolve(dict(raw), "", env or os.environ, errors)
    return resolved, errors


def build_agent_config(resolved_config: JsonMapping, agent_id: str) -> Dict[str, Any]:
    """Build a flat configuration dict for a given agent.

    Merges provider defaults and agent overrides into a single dictionary
    suitable for passing directly to :class:`agent_core.AgentCore`.
    """

    agents = resolved_config.get("agents") or {}
    if agent_id not in agents:
        raise KeyError(f"Unknown agent_id {agent_id!r}")

    agent_cfg = dict(agents[agent_id])
    provider_name = agent_cfg.get("provider")
    if not isinstance(provider_name, str) or not provider_name:
        raise ValueError(f"Agent {agent_id!r} must define a non-empty 'provider' string")

    providers = resolved_config.get("providers") or {}
    provider_defaults = dict(providers.get(provider_name) or {})

    # Provider key used by AgentCore selector: prefer explicit, fallback to name
    provider_key = provider_defaults.get("provider") or provider_name

    merged: Dict[str, Any] = {**provider_defaults, **agent_cfg}
    merged["provider"] = provider_key
    return merged


def resolve_request_config(base_agent_config: JsonMapping, overrides: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Merge per-request overrides into a base agent config.

    The returned mapping is a shallow copy; callers should treat it as
    immutable from that point on.
    """

    if not overrides:
        return dict(base_agent_config)
    return {**base_agent_config, **dict(overrides)}


def _import_string(path: str) -> type[Any]:
    """Import ``"package.module.Class"`` and return the class object.

    Raises ImportError or AttributeError if the target cannot be imported.
    """

    module_path, sep, attr = path.rpartition(".")
    if not sep:
        raise ImportError(f"Invalid plugin path {path!r}: expected 'module.Class'")
    module = importlib.import_module(module_path)
    try:
        return getattr(module, attr)
    except AttributeError as exc:  # pragma: no cover - defensive
        raise AttributeError(f"Module {module_path!r} has no attribute {attr!r}") from exc


def load_plugins(
    plugin_config: Mapping[str, Any] | None,
) -> Tuple[Dict[str, List[type[Any]]], List[Dict[str, Any]]]:
    """Load plugin classes from dotted paths listed in config.

    Returns (plugins, errors) where ``plugins`` is a dict with keys
    ``providers``, ``features``, ``tools``, ``extensions`` mapped to lists
    of classes. Import errors are collected into ``errors`` instead of
    raising, so the caller can decide how to surface them.
    """

    sections = {"providers": [], "features": [], "tools": [], "extensions": []}
    errors: List[Dict[str, Any]] = []

    if not plugin_config:
        return sections, errors

    for kind in sections.keys():
        entries: Iterable[Any] = plugin_config.get(kind) or []
        for raw in entries:
            if not isinstance(raw, str):
                errors.append(
                    {
                        "type": "plugin_path_invalid",
                        "kind": kind,
                        "path": raw,
                        "detail": "Plugin path must be a string",
                    }
                )
                continue
            try:
                cls = _import_string(raw)
                sections[kind].append(cls)
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(
                    {
                        "type": "plugin_import_error",
                        "kind": kind,
                        "path": raw,
                        "detail": str(exc),
                    }
                )

    return sections, errors
