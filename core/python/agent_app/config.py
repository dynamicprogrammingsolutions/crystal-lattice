from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Set, Tuple
import json
import os
import importlib
import re


JsonMapping = Mapping[str, Any]
_MIXIN_REFS_KEY = "mixin_refs"
_MIXIN_MERGE_KEY = "mixin_merge"
_MIXIN_POLICY_KEY = "mixin_policy"
_MIXINS_KEY = "mixins"
_DEFAULT_MIXIN_DEPTH = 16


def _default_builtin_plugins_dir() -> Path:
    """Return the default built-in plugins directory for this install layout.

    In the repository layout this resolves to ``<repo>/plugins``. Packaged
    distributions can override it by passing ``env_overrides`` when creating
    the application.
    """

    return Path(__file__).resolve().parents[3] / "plugins"


def build_config_resolution_env(
    config_path: str | Path,
    *,
    env: Mapping[str, str] | None = None,
    config_env: Mapping[str, str] | None = None,
    env_overrides: Mapping[str, str] | None = None,
) -> Dict[str, str]:
    """Build the environment used for config placeholder resolution.

    Resolution starts with derived defaults, then overlays config-only values,
    process env, and finally explicit ``env_overrides`` from the embedding
    application. This keeps configs portable while still allowing callers to
    provide placeholder values without mutating global process state.
    """

    config_dir = str(Path(config_path).expanduser().resolve().parent)
    working_dir = str(Path.cwd().resolve())
    derived: Dict[str, str] = {
        "CONFIG_DIR": config_dir,
        "WORKING_DIR": working_dir,
        "BUILTIN_PLUGINS": str(_default_builtin_plugins_dir()),
    }

    merged: Dict[str, str] = dict(derived)
    if config_env:
        merged.update({key: str(value) for key, value in config_env.items()})
    merged.update(dict(os.environ if env is None else env))
    if env_overrides:
        merged.update({key: str(value) for key, value in env_overrides.items()})
    return merged


def build_runtime_overlay_env(
    config_path: str | Path,
    *,
    env_overrides: Mapping[str, str] | None = None,
) -> Dict[str, str]:
    """Build the subset of runtime env keys installed into ``os.environ``.

    The real process environment already contains inherited variables, so the
    overlay only needs to install application-owned anchor keys plus explicit
    caller overrides that may not exist in the parent process.
    """

    overlay = {
        "CONFIG_DIR": str(Path(config_path).expanduser().resolve().parent),
        "WORKING_DIR": str(Path.cwd().resolve()),
        "BUILTIN_PLUGINS": str(_default_builtin_plugins_dir()),
    }
    if env_overrides:
        overlay.update({key: str(value) for key, value in env_overrides.items()})
    return overlay


def load_raw_config(path: str | Path) -> Dict[str, Any]:
    """Load JSON configuration from disk.

    The function performs no placeholder resolution; callers should invoke
    :func:`resolve_placeholders` afterwards.
    """

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_value(
    value: Any, path: str, env: Mapping[str, str], errors: List[Dict[str, Any]]
) -> Any:
    """Resolve a single value, handling ${env:...} and ${file:...} placeholders.

    - ${env:VAR} placeholders are now supported anywhere within a string.
    - ${file:...} remains whole-string only to avoid surprising concatenations.
    """

    if not isinstance(value, str):
        return value

    # Replace embedded ${env:VAR} placeholders anywhere within the string.
    # Record an error for each missing variable and substitute empty string.
    def _env_repl(match: re.Match[str]) -> str:
        var_name = match.group(1)
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

    if "${env:" in value:
        value = re.sub(r"\$\{env:([^}]+)\}", _env_repl, value)

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


def _walk_and_resolve(
    obj: Any, path: str, env: Mapping[str, str], errors: List[Dict[str, Any]]
) -> Any:
    if isinstance(obj, dict) and set(obj.keys()) == {"$raw"}:
        return _copy_jsonish(obj["$raw"])
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


def _copy_jsonish(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _copy_jsonish(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_jsonish(item) for item in value]
    return value


def _strip_mixin_control_keys(
    mapping: Mapping[str, Any], *, preserve_merge_mode: bool = False
) -> Dict[str, Any]:
    excluded = {_MIXIN_REFS_KEY}
    if not preserve_merge_mode:
        excluded.add(_MIXIN_MERGE_KEY)
    return {
        key: _copy_jsonish(value)
        for key, value in mapping.items()
        if key not in excluded
    }


def _deep_merge(base: Mapping[str, Any], overlay: Mapping[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {key: _copy_jsonish(value) for key, value in base.items()}
    for key, value in overlay.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(existing, value)
        else:
            merged[key] = _copy_jsonish(value)
    return merged


def _merge_mappings(
    base: Mapping[str, Any], overlay: Mapping[str, Any], mode: str
) -> Dict[str, Any]:
    if mode == "deep":
        return _deep_merge(base, overlay)
    merged: Dict[str, Any] = {key: _copy_jsonish(value) for key, value in base.items()}
    for key, value in overlay.items():
        merged[key] = _copy_jsonish(value)
    return merged


def _coerce_mixin_merge_mode(
    raw_value: Any,
    path: str,
    errors: List[Dict[str, Any]],
    default_mode: str,
) -> str:
    if raw_value is None:
        return default_mode
    if raw_value in {"shallow", "deep"}:
        return str(raw_value)
    errors.append(
        {
            "type": "mixin_config_invalid",
            "path": path,
            "detail": f"{path!r} must be 'shallow' or 'deep'",
        }
    )
    return default_mode


def _coerce_mixin_refs(
    raw_value: Any, path: str, errors: List[Dict[str, Any]]
) -> List[str]:
    if raw_value is None:
        return []
    if not isinstance(raw_value, list):
        errors.append(
            {
                "type": "mixin_config_invalid",
                "path": path,
                "detail": f"{path!r} must be a list of non-empty strings",
            }
        )
        return []
    refs: List[str] = []
    invalid = False
    for index, value in enumerate(raw_value):
        if isinstance(value, str) and value:
            refs.append(value)
            continue
        invalid = True
        errors.append(
            {
                "type": "mixin_config_invalid",
                "path": f"{path}[{index}]",
                "detail": "Mixin references must be non-empty strings",
            }
        )
    return refs if not invalid else refs


def resolve_config_mixins(
    raw_config: Mapping[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Resolve provider/agent mixins in a placeholder-resolved config mapping.

    The returned config preserves the original top-level structure, but
    provider and agent entries are expanded so downstream code sees the
    effective configuration without mixin control keys.
    """

    config = dict(raw_config)
    errors: List[Dict[str, Any]] = []

    policy_in = config.get(_MIXIN_POLICY_KEY)
    if policy_in is None:
        policy: Dict[str, Any] = {}
    elif isinstance(policy_in, dict):
        policy = dict(policy_in)
    else:
        errors.append(
            {
                "type": "mixin_config_invalid",
                "path": _MIXIN_POLICY_KEY,
                "detail": "'mixin_policy' must be a mapping",
            }
        )
        policy = {}

    default_merge = _coerce_mixin_merge_mode(
        policy.get("default_merge"),
        f"{_MIXIN_POLICY_KEY}.default_merge",
        errors,
        "shallow",
    )

    max_depth_in = policy.get("max_depth", _DEFAULT_MIXIN_DEPTH)
    if isinstance(max_depth_in, int) and max_depth_in > 0:
        max_depth = max_depth_in
    else:
        errors.append(
            {
                "type": "mixin_config_invalid",
                "path": f"{_MIXIN_POLICY_KEY}.max_depth",
                "detail": "'mixin_policy.max_depth' must be a positive integer",
            }
        )
        max_depth = _DEFAULT_MIXIN_DEPTH

    mixins_in = config.get(_MIXINS_KEY)
    if mixins_in is None:
        mixins: Dict[str, Any] = {}
    elif isinstance(mixins_in, dict):
        mixins = dict(mixins_in)
    else:
        errors.append(
            {
                "type": "mixin_config_invalid",
                "path": _MIXINS_KEY,
                "detail": "'mixins' must be a mapping",
            }
        )
        mixins = {}

    resolved_mixins: Dict[str, Dict[str, Any]] = {}
    resolving: Set[str] = set()

    def _resolve_named_mixin(mixin_id: str, depth: int) -> Dict[str, Any]:
        if mixin_id in resolved_mixins:
            return resolved_mixins[mixin_id]
        if mixin_id in resolving:
            errors.append(
                {
                    "type": "mixin_cycle",
                    "path": f"{_MIXINS_KEY}.{mixin_id}",
                    "detail": f"Circular mixin reference detected for {mixin_id!r}",
                }
            )
            return {}
        if depth > max_depth:
            errors.append(
                {
                    "type": "mixin_depth_exceeded",
                    "path": f"{_MIXINS_KEY}.{mixin_id}",
                    "detail": f"Mixin expansion exceeded max_depth={max_depth}",
                }
            )
            return {}

        mixin_cfg = mixins.get(mixin_id)
        if not isinstance(mixin_cfg, dict):
            errors.append(
                {
                    "type": "mixin_missing",
                    "path": f"{_MIXINS_KEY}.{mixin_id}",
                    "detail": f"Unknown mixin {mixin_id!r}",
                }
            )
            return {}

        resolving.add(mixin_id)
        try:
            resolved = _resolve_node(mixin_cfg, f"{_MIXINS_KEY}.{mixin_id}", depth)
            resolved_mixins[mixin_id] = resolved
            return resolved
        finally:
            resolving.discard(mixin_id)

    def _resolve_node(
        node_cfg: Mapping[str, Any], path: str, depth: int
    ) -> Dict[str, Any]:
        mode = _coerce_mixin_merge_mode(
            node_cfg.get(_MIXIN_MERGE_KEY),
            f"{path}.{_MIXIN_MERGE_KEY}",
            errors,
            default_merge,
        )
        refs = _coerce_mixin_refs(
            node_cfg.get(_MIXIN_REFS_KEY), f"{path}.{_MIXIN_REFS_KEY}", errors
        )

        merged: Dict[str, Any] = {}
        for index, mixin_id in enumerate(refs):
            if mixin_id not in mixins:
                errors.append(
                    {
                        "type": "mixin_missing",
                        "path": f"{path}.{_MIXIN_REFS_KEY}[{index}]",
                        "detail": f"Unknown mixin {mixin_id!r}",
                    }
                )
                continue
            merged = _merge_mappings(
                merged, _resolve_named_mixin(mixin_id, depth + 1), mode
            )

        preserve_mode = path.startswith("providers.") or path.startswith("agents.")
        return _merge_mappings(
            merged,
            _strip_mixin_control_keys(node_cfg, preserve_merge_mode=preserve_mode),
            mode,
        )

    resolved_config: Dict[str, Any] = {
        key: _copy_jsonish(value) for key, value in config.items()
    }

    for scope_key in ("providers", "agents"):
        scope_in = config.get(scope_key)
        if scope_in is None:
            continue
        if not isinstance(scope_in, dict):
            errors.append(
                {
                    "type": "mixin_config_invalid",
                    "path": scope_key,
                    "detail": f"'{scope_key}' must be a mapping when using config mixins",
                }
            )
            continue
        resolved_scope: Dict[str, Any] = {}
        for entry_id, entry_cfg in scope_in.items():
            if isinstance(entry_cfg, dict):
                resolved_scope[entry_id] = _resolve_node(
                    entry_cfg, f"{scope_key}.{entry_id}", 0
                )
            else:
                resolved_scope[entry_id] = _copy_jsonish(entry_cfg)
        resolved_config[scope_key] = resolved_scope

    if mixins:
        resolved_config[_MIXINS_KEY] = {
            mixin_id: _resolve_named_mixin(mixin_id, 0)
            for mixin_id in mixins.keys()
            if isinstance(mixins.get(mixin_id), dict)
        }

    return resolved_config, errors


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
        raise ValueError(
            f"Agent {agent_id!r} must define a non-empty 'provider' string"
        )

    providers = resolved_config.get("providers") or {}
    provider_defaults = dict(providers.get(provider_name) or {})
    merge_mode = _coerce_mixin_merge_mode(
        agent_cfg.get(_MIXIN_MERGE_KEY, provider_defaults.get(_MIXIN_MERGE_KEY)),
        f"agents.{agent_id}.{_MIXIN_MERGE_KEY}",
        [],
        (
            str(
                ((resolved_config.get(_MIXIN_POLICY_KEY) or {}).get("default_merge"))
                if isinstance(resolved_config.get(_MIXIN_POLICY_KEY), dict)
                else "shallow"
            )
            if (
                isinstance(resolved_config.get(_MIXIN_POLICY_KEY), dict)
                and (resolved_config.get(_MIXIN_POLICY_KEY) or {}).get("default_merge")
                in {"shallow", "deep"}
            )
            else "shallow"
        ),
    )

    # Provider key used by AgentCore selector: prefer explicit, fallback to name
    provider_key = provider_defaults.get("provider") or provider_name

    merged = _merge_mappings(provider_defaults, agent_cfg, merge_mode)
    merged["provider"] = provider_key
    # These keys control application/plugin-package resolution and should not
    # be forwarded into the runtime provider/tool config.
    merged.pop("plugins", None)
    merged.pop("disabled_plugins", None)
    merged.pop(_MIXIN_REFS_KEY, None)
    merged.pop(_MIXIN_MERGE_KEY, None)
    # Note: enabled_plugins and force_enabled_plugins are preserved for core-layer resolution
    # (enabled_plugins is used for default_enabled=False plugins, force_enabled_plugins bypasses tag checks)
    return merged


def resolve_request_config(
    base_agent_config: JsonMapping, overrides: Mapping[str, Any] | None
) -> Dict[str, Any]:
    """Merge per-request overrides into a base agent config.

    Callers should treat the returned mapping as immutable.
    """

    from typing import cast

    if not overrides:
        # base_agent_config is produced by build_agent_config and is already a dict;
        # reuse it directly instead of making a defensive shallow copy.
        return cast(Dict[str, Any], base_agent_config)
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
        raise AttributeError(
            f"Module {module_path!r} has no attribute {attr!r}"
        ) from exc


def load_plugins(
    plugin_config: Mapping[str, Any] | None,
) -> Tuple[Dict[str, List[type[Any]]], List[Dict[str, Any]]]:
    """Deprecated: load plugin classes from dotted paths listed by kind.

    The application now prefers a flat `plugins` list that is resolved via
    :class:`agent_app.plugin_manager.PluginManager`.

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


def load_application_plugins(
    plugin_paths: Iterable[Any] | None,
) -> Tuple[List[type[Any]], List[Dict[str, Any]]]:
    """Deprecated: load application-level plugin classes from dotted paths.

    Application plugins are now configured in the main `plugins` list and
    classified by duck-typing.

    Args:
        plugin_paths: Iterable of dotted class paths
            (e.g. ``"session_actions_app.SessionActionsAppPlugin"``).

    Returns:
        Tuple of ``(classes, errors)`` where ``classes`` is a flat list of
        imported plugin classes and ``errors`` collects any import or path
        issues in the same shape as :func:`load_plugins`.
    """

    classes: List[type[Any]] = []
    errors: List[Dict[str, Any]] = []

    if not plugin_paths:
        return classes, errors

    for raw in plugin_paths:
        if not isinstance(raw, str):
            errors.append(
                {
                    "type": "plugin_path_invalid",
                    "kind": "application",
                    "path": raw,
                    "detail": "Application plugin path must be a string",
                }
            )
            continue
        try:
            cls = _import_string(raw)
            classes.append(cls)
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(
                {
                    "type": "plugin_import_error",
                    "kind": "application",
                    "path": raw,
                    "detail": str(exc),
                }
            )

    return classes, errors
