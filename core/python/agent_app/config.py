from __future__ import annotations

from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    MutableMapping,
    Set,
    Tuple,
)
import json
import os
import importlib
import re

from .config_merge import MERGE_KEY, copy_config_value, merge_config
from .config_variants import resolve_config_variants, validate_config_variants


JsonMapping = Mapping[str, Any]
_MIXIN_REFS_KEY = "mixin_refs"
_MIXIN_MERGE_KEY = "mixin_merge"
_MIXIN_POLICY_KEY = "mixin_policy"
_MIXINS_KEY = "mixins"
_DEFAULT_MIXIN_DEPTH = 16
INCLUDE_KEY = "$include"
_DEFAULT_INCLUDE_DEPTH = 16


def _default_builtin_plugins_dir() -> Path:
    """Return the default built-in plugins directory for this install layout.

    In the repository layout this resolves to ``<repo>/plugins``. Packaged
    distributions can override it by passing ``env_overrides`` when creating
    the application.
    """

    return Path(__file__).resolve().parents[3] / "plugins"


def _default_crystal_data_dir() -> Path:
    """Return the default user-level Crystal data directory.

    This is the home for user-owned state that must not follow the active
    config file location (``CONFIG_DIR``) — for example usage journals, cost
    tracking stores, and other per-user data. It defaults to ``~/.crystal``,
    which is also the usual ``CONFIG_DIR`` location, so both point at the same
    directory on a normal machine while remaining independently overridable.
    """

    return Path.home() / ".crystal"


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
        "CRYSTAL_DATA_DIR": str(_default_crystal_data_dir()),
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
        "CRYSTAL_DATA_DIR": str(_default_crystal_data_dir()),
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


def load_resolved_config(
    config_path: str | Path,
    *,
    env: Mapping[str, str] | None = None,
    config_env: Mapping[str, str] | None = None,
    env_overrides: Mapping[str, str] | None = None,
) -> tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, str]]:
    """Load, placeholder-resolve, and mixin-resolve a config from disk.

    Packaging/build helpers need the same config interpretation contract as the
    runtime application, but without constructing an AgentApplication.
    """

    raw_config = load_raw_config(config_path)
    resolution_env = build_config_resolution_env(
        config_path,
        env=env,
        config_env=config_env,
        env_overrides=env_overrides,
    )
    resolved_config, placeholder_errors = resolve_placeholders(
        raw_config, env=resolution_env
    )
    include_resolved_config, include_errors = resolve_config_includes(
        resolved_config,
        config_dir=Path(config_path).expanduser().resolve().parent,
    )
    mixin_resolved_config, mixin_errors = resolve_config_mixins(include_resolved_config)
    variant_errors = validate_resolved_config_variants(mixin_resolved_config)
    return (
        mixin_resolved_config,
        placeholder_errors + include_errors + mixin_errors + variant_errors,
        resolution_env,
    )


def coerce_plugin_specs(
    raw_value: Any,
    path: str,
    errors: List[Dict[str, Any]] | None = None,
) -> List[Any]:
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        return list(raw_value)
    if errors is not None:
        errors.append(
            {
                "type": "plugin_config_invalid",
                "detail": f"'{path}' should be a list; coerced single value into list",
                "path": path,
            }
        )
    return [raw_value]


def iter_specs_in_order(*spec_lists: List[Any]) -> Iterator[Any]:
    seen: Set[str] = set()
    for spec_list in spec_lists:
        for spec in spec_list:
            if isinstance(spec, str):
                cache_key = f"str:{spec}"
            else:
                try:
                    encoded = json.dumps(spec, sort_keys=True, separators=(",", ":"))
                except Exception:
                    encoded = repr(spec)
                cache_key = f"json:{encoded}"
            if cache_key in seen:
                continue
            seen.add(cache_key)
            yield spec


def iter_unique_specs(first: List[Any], *rest: Iterable[List[Any]]) -> Iterator[Any]:
    flat_lists: List[List[Any]] = [first]
    for value in rest:
        for spec_list in value:
            flat_lists.append(list(spec_list))
    yield from iter_specs_in_order(*flat_lists)


def collect_declared_plugin_specs(
    resolved_config: JsonMapping,
    *,
    errors: List[Dict[str, Any]] | None = None,
) -> tuple[List[Any], Dict[str, List[Any]], Dict[str, List[Any]]]:
    plugin_specs = coerce_plugin_specs(
        resolved_config.get("plugins"), "plugins", errors
    )

    providers_cfg = (
        resolved_config.get("providers")
        if isinstance(resolved_config.get("providers"), dict)
        else {}
    )
    provider_plugin_specs: Dict[str, List[Any]] = {}
    for provider_id, provider_cfg in providers_cfg.items():
        if not isinstance(provider_cfg, dict):
            continue
        provider_plugin_specs[provider_id] = coerce_plugin_specs(
            provider_cfg.get("plugins"),
            f"providers.{provider_id}.plugins",
            errors,
        )

    agents_cfg = (
        resolved_config.get("agents")
        if isinstance(resolved_config.get("agents"), dict)
        else {}
    )
    agent_plugin_specs: Dict[str, List[Any]] = {}
    for agent_id, agent_cfg in agents_cfg.items():
        if not isinstance(agent_cfg, dict):
            continue
        agent_plugin_specs[agent_id] = coerce_plugin_specs(
            agent_cfg.get("plugins"),
            f"agents.{agent_id}.plugins",
            errors,
        )

    return plugin_specs, provider_plugin_specs, agent_plugin_specs


def collect_unique_declared_plugin_specs(
    resolved_config: JsonMapping,
    *,
    errors: List[Dict[str, Any]] | None = None,
) -> List[Any]:
    plugin_specs, provider_plugin_specs, agent_plugin_specs = (
        collect_declared_plugin_specs(resolved_config, errors=errors)
    )
    return list(
        iter_unique_specs(
            plugin_specs,
            provider_plugin_specs.values(),
            agent_plugin_specs.values(),
        )
    )


def iter_string_values(value: object) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from iter_string_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_string_values(child)


def remove_declared_plugin_specs_by_exact_match(
    config: MutableMapping[str, Any], disabled_specs: Iterable[str]
) -> Dict[str, Any]:
    disabled_set = {spec for spec in disabled_specs if isinstance(spec, str) and spec}
    removed: list[Dict[str, str]] = []

    def filter_plugins(container: MutableMapping[str, Any], path: str) -> None:
        plugins = container.get("plugins")
        if not isinstance(plugins, list):
            return
        kept = []
        for item in plugins:
            if isinstance(item, str) and item in disabled_set:
                removed.append({"path": path, "spec": item})
            else:
                kept.append(item)
        container["plugins"] = kept

    filter_plugins(config, "plugins")

    providers = config.get("providers")
    if isinstance(providers, MutableMapping):
        for provider_id, provider_cfg in providers.items():
            if isinstance(provider_cfg, MutableMapping):
                filter_plugins(provider_cfg, f"providers.{provider_id}.plugins")

    agents = config.get("agents")
    if isinstance(agents, MutableMapping):
        for agent_id, agent_cfg in agents.items():
            if isinstance(agent_cfg, MutableMapping):
                filter_plugins(agent_cfg, f"agents.{agent_id}.plugins")

    return {
        "requested": sorted(disabled_set),
        "removed": removed,
    }


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
                    "severity": "warning",
                    "variable": var_name,
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


def _resolve_include_tree(
    node: Any,
    base_dir: Path,
    chain: Tuple[Path, ...],
    depth: int,
    default_mode: str,
    max_depth: int,
    errors: List[Dict[str, Any]],
    path: str = "",
) -> Any:
    """Recursively resolve ``$include`` keys within ``node``'s subtree.

    Mappings are traversed; arrays and scalars are opaque. A mapping carrying
    ``$include`` has the referenced JSON file's object merged underneath its
    local keys (local keys win) and the control key consumed.
    """

    if not isinstance(node, Mapping):
        return copy_config_value(node)

    if INCLUDE_KEY in node:
        return _resolve_include_node(
            node,
            base_dir=base_dir,
            chain=chain,
            depth=depth,
            default_mode=default_mode,
            max_depth=max_depth,
            errors=errors,
            path=path,
        )

    resolved: Dict[str, Any] = {}
    for key, value in node.items():
        child_path = f"{path}.{key}" if path else str(key)
        if isinstance(value, Mapping):
            resolved[key] = _resolve_include_tree(
                value,
                base_dir,
                chain,
                depth,
                default_mode,
                max_depth,
                errors,
                child_path,
            )
        else:
            resolved[key] = copy_config_value(value)
    return resolved


def _load_include_file(
    include_value: Any,
    base_dir: Path,
    chain: Tuple[Path, ...],
    depth: int,
    default_mode: str,
    max_depth: int,
    errors: List[Dict[str, Any]],
    path: str,
) -> Dict[str, Any] | None:
    """Load and include-resolve the JSON file referenced by ``$include``.

    Relative paths resolve against ``base_dir`` (the directory of the file
    that carries the ``$include`` key); ``~`` expands to the user's home.
    Returns the resolved object, or None when the file cannot be loaded
    (the error is recorded in ``errors``).
    """

    if depth >= max_depth:
        errors.append(
            {
                "type": "include_depth_exceeded",
                "path": f"{path}.{INCLUDE_KEY}",
                "detail": f"$include expansion exceeded max_depth={max_depth}",
            }
        )
        return None

    raw_path = str(include_value).strip()
    include_path = Path(raw_path).expanduser()
    if not include_path.is_absolute():
        include_path = base_dir / include_path
    resolved_path = include_path.resolve()

    if resolved_path in chain:
        errors.append(
            {
                "type": "include_cycle",
                "path": f"{path}.{INCLUDE_KEY}",
                "detail": f"Circular $include reference to {str(resolved_path)}",
            }
        )
        return None

    try:
        content = json.loads(resolved_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(
            {
                "type": "include_missing",
                "path": f"{path}.{INCLUDE_KEY}",
                "detail": f"$include file not found: {str(resolved_path)}",
            }
        )
        return None
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(
            {
                "type": "include_invalid",
                "path": f"{path}.{INCLUDE_KEY}",
                "detail": f"Could not load $include file {str(resolved_path)}: {exc}",
            }
        )
        return None

    if not isinstance(content, dict):
        errors.append(
            {
                "type": "include_invalid",
                "path": f"{path}.{INCLUDE_KEY}",
                "detail": f"$include file must contain a JSON object: {str(resolved_path)}",
            }
        )
        return None

    return _resolve_include_tree(
        content,
        resolved_path.parent,
        (*chain, resolved_path),
        depth + 1,
        default_mode,
        max_depth,
        errors,
        path,
    )


def _resolve_include_node(
    node: Mapping[str, Any],
    *,
    base_dir: Path,
    chain: Tuple[Path, ...],
    depth: int,
    default_mode: str,
    max_depth: int,
    errors: List[Dict[str, Any]],
    path: str,
) -> Dict[str, Any]:
    """Merge the ``$include`` target underneath a node's local keys.

    The included object is the base and the node's local keys (minus the
    control key) are the overlay, so local keys override included content.
    A ``$merge`` directive on the included file's root governs the merge;
    otherwise the node's own ``$merge`` applies. The node's ``$merge`` is
    preserved in the result so later mixin resolution still sees it.
    """

    include_value = node.get(INCLUDE_KEY)
    local = {key: value for key, value in node.items() if key != INCLUDE_KEY}

    included: Dict[str, Any] = {}
    if not isinstance(include_value, str) or not str(include_value).strip():
        errors.append(
            {
                "type": "include_invalid",
                "path": f"{path}.{INCLUDE_KEY}",
                "detail": "'$include' must be a non-empty string path to a JSON file",
            }
        )
    else:
        loaded = _load_include_file(
            include_value,
            base_dir,
            chain,
            depth,
            default_mode,
            max_depth,
            errors,
            path,
        )
        if loaded is not None:
            included = loaded

    local_resolved: Dict[str, Any] = {}
    for key, value in local.items():
        child_path = f"{path}.{key}" if path else str(key)
        if isinstance(value, Mapping):
            local_resolved[key] = _resolve_include_tree(
                value,
                base_dir,
                chain,
                depth,
                default_mode,
                max_depth,
                errors,
                child_path,
            )
        else:
            local_resolved[key] = copy_config_value(value)

    included_directive = included.get(MERGE_KEY)
    overlay = dict(local_resolved)
    if included_directive is not None:
        overlay[MERGE_KEY] = copy_config_value(included_directive)

    merged = merge_config(
        included,
        overlay,
        default_mode=default_mode,  # type: ignore[arg-type]
        path=path,
        errors=errors,
        max_depth=max_depth,
    )

    local_had_merge = MERGE_KEY in local_resolved
    if local_had_merge and MERGE_KEY not in merged:
        merged[MERGE_KEY] = copy_config_value(local_resolved[MERGE_KEY])
    return merged


def resolve_config_includes(
    config: Mapping[str, Any],
    *,
    config_dir: str | Path | None = None,
    max_depth: int = _DEFAULT_INCLUDE_DEPTH,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Resolve ``"$include": "path/to.json"`` keys in a config mapping.

    Any config object may carry a ``$include`` key referencing a JSON file.
    The file's object is merged into that object with the same merge
    machinery config mixins use: the included content is the base, the
    object's local keys are the overlay (local keys win), a ``$merge``
    directive on the included file's root governs the merge (else the
    object's own ``$merge``, else ``mixin_policy.default_merge`` or
    ``shallow``), and the ``$include`` key is consumed so downstream config
    sees only the merged result. Relative paths resolve against the
    directory of the file carrying the key; ``~`` expands to the user's
    home; ``${env:...}`` placeholders are expected to be resolved already
    (run :func:`resolve_placeholders` first). Guards mirror mixins: cycles
    are reported as structured errors, expansion depth is bounded, and
    missing or unparsable files leave the object's local keys intact.

    Returns a tuple of ``(resolved_config, errors)``.
    """

    errors: List[Dict[str, Any]] = []
    policy_in = config.get(_MIXIN_POLICY_KEY)
    raw_default = (
        policy_in.get("default_merge") if isinstance(policy_in, Mapping) else None
    )
    default_mode = raw_default if raw_default in {"shallow", "deep"} else "shallow"

    base_dir = (
        Path(config_dir).expanduser().resolve()
        if config_dir is not None
        else Path.cwd().resolve()
    )
    resolved = _resolve_include_tree(
        config, base_dir, (), 0, default_mode, max_depth, errors
    )
    return resolved, errors


def _copy_jsonish(value: Any) -> Any:
    return copy_config_value(value)


def _strip_mixin_control_keys(
    mapping: Mapping[str, Any], *, preserve_merge_mode: bool = False
) -> Dict[str, Any]:
    excluded = {_MIXIN_REFS_KEY}
    if not preserve_merge_mode:
        excluded.add(_MIXIN_MERGE_KEY)
        excluded.add(MERGE_KEY)
    return {
        key: _copy_jsonish(value)
        for key, value in mapping.items()
        if key not in excluded
    }


def _merge_mappings(
    base: Mapping[str, Any],
    overlay: Mapping[str, Any],
    mode: str,
    *,
    path: str = "",
    errors: List[Dict[str, Any]] | None = None,
    max_depth: int = _DEFAULT_MIXIN_DEPTH,
    preserve_directives: bool = False,
) -> Dict[str, Any]:
    normalized_mode = "deep" if mode == "deep" else "shallow"
    return merge_config(
        base,
        overlay,
        default_mode=normalized_mode,
        path=path,
        errors=errors,
        max_depth=max_depth,
        preserve_directives=preserve_directives,
    )


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


def _root_merge_directive(
    node_cfg: Mapping[str, Any],
    *,
    path: str,
    errors: List[Dict[str, Any]],
    default_mode: str,
) -> Any:
    legacy_raw = node_cfg.get(_MIXIN_MERGE_KEY)
    legacy_mode: str | None = None
    if legacy_raw is not None:
        legacy_mode = _coerce_mixin_merge_mode(
            legacy_raw,
            f"{path}.{_MIXIN_MERGE_KEY}",
            errors,
            default_mode,
        )

    directive = node_cfg.get(MERGE_KEY)
    if directive is None:
        return legacy_mode

    if legacy_mode is not None and directive != legacy_mode:
        errors.append(
            {
                "type": "mixin_config_invalid",
                "path": f"{path}.{MERGE_KEY}",
                "detail": (
                    f"{path!r} defines conflicting {_MIXIN_MERGE_KEY!r} "
                    f"and {MERGE_KEY!r} values"
                ),
            }
        )
    return directive


def _overlay_with_merge_directive(
    mapping: Mapping[str, Any],
    directive: Any,
    *,
    replace_existing: bool = False,
) -> Dict[str, Any]:
    """Copy ``mapping`` and set its root merge directive to ``directive``.

    With ``replace_existing`` any directive already present on ``mapping`` is
    removed first, so the caller fully owns the resulting root policy.
    """
    overlay = {key: _copy_jsonish(value) for key, value in mapping.items()}
    if replace_existing:
        overlay.pop(MERGE_KEY, None)
    if directive is not None:
        overlay[MERGE_KEY] = _copy_jsonish(directive)
    return overlay


def _strip_consumed_merge_directives(
    target: MutableMapping[str, Any], ref: Mapping[str, Any]
) -> None:
    """Remove a consumed mixin's merge directives from a merged mapping.

    After a referenced mixin carrying ``$merge`` directives has been merged,
    its directives must not persist into the referrer's configuration. Every
    ``$merge`` position the mixin defines is removed from the merged result at
    the same path. Overlay directives win during merging, so those keys
    provably originate from the referenced mixin.
    """
    for key, value in ref.items():
        if key == MERGE_KEY:
            target.pop(MERGE_KEY, None)
        elif isinstance(value, Mapping) and isinstance(target.get(key), Mapping):
            _strip_consumed_merge_directives(target[key], value)


def resolve_config_mixins(
    raw_config: Mapping[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Resolve provider/agent mixins in a placeholder-resolved config mapping.

    The returned config preserves the original top-level structure, but
    provider and agent entries are expanded so downstream code sees the
    effective configuration without mixin control keys.

    A referenced mixin's own root ``$merge`` governs how that mixin merges
    into its referrer; references without their own directive use the
    referrer's root policy. Mixin-carried directives are consumed by that
    merge action and do not persist into the referrer's resolved
    configuration.
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
        directive = _root_merge_directive(
            node_cfg,
            path=path,
            errors=errors,
            default_mode=default_merge,
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
            resolved_ref = _resolve_named_mixin(mixin_id, depth + 1)
            # A mixin's own root $merge governs its merge into the referrer;
            # directive-less references use the referencing node's policy.
            ref_directive = resolved_ref.get(MERGE_KEY)
            merged = _merge_mappings(
                merged,
                _overlay_with_merge_directive(
                    resolved_ref,
                    ref_directive if ref_directive is not None else directive,
                    replace_existing=True,
                ),
                default_merge,
                path=path,
                errors=errors,
                max_depth=max_depth,
                preserve_directives=True,
            )
            if ref_directive is not None:
                # Consume the mixin-carried directive: it must not persist
                # into the referrer's resolved configuration or govern any
                # later merge action.
                merged.pop(MERGE_KEY, None)
                _strip_consumed_merge_directives(merged, resolved_ref)

        preserve_mode = path.startswith("providers.") or path.startswith("agents.")
        local_overlay = _strip_mixin_control_keys(
            node_cfg, preserve_merge_mode=preserve_mode
        )
        local_overlay = _overlay_with_merge_directive(local_overlay, directive)
        resolved = _merge_mappings(
            merged,
            local_overlay,
            default_merge,
            path=path,
            errors=errors,
            max_depth=max_depth,
            preserve_directives=True,
        )
        if preserve_mode:
            if _MIXIN_MERGE_KEY in node_cfg:
                resolved[_MIXIN_MERGE_KEY] = _copy_jsonish(node_cfg[_MIXIN_MERGE_KEY])
            if MERGE_KEY in node_cfg:
                resolved[MERGE_KEY] = _copy_jsonish(node_cfg[MERGE_KEY])
        return resolved

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


def validate_resolved_config_variants(
    resolved_config: JsonMapping,
) -> List[Dict[str, Any]]:
    errors: List[Dict[str, Any]] = []
    for scope_key in (_MIXINS_KEY, "providers", "agents"):
        scope = resolved_config.get(scope_key)
        if not isinstance(scope, Mapping):
            continue
        for entry_id, entry_cfg in scope.items():
            if not isinstance(entry_cfg, Mapping):
                continue
            errors.extend(
                validate_config_variants(
                    entry_cfg,
                    path=f"{scope_key}.{entry_id}",
                    root_scope=True,
                    max_depth=_DEFAULT_MIXIN_DEPTH,
                )
            )
    return errors


def build_agent_config(resolved_config: JsonMapping, agent_id: str) -> Dict[str, Any]:
    """Build a flat configuration dict for a given agent.

    Merges provider defaults and agent overrides into a single dictionary
    suitable for passing directly to :class:`agent_core.AgentCore`.
    """

    agents = resolved_config.get("agents") or {}
    if agent_id not in agents:
        raise KeyError(f"Unknown agent_id {agent_id!r}")

    agent_cfg = dict(agents[agent_id])
    agent_cfg.pop("display", None)
    provider_name = agent_cfg.get("provider")
    if not isinstance(provider_name, str) or not provider_name:
        raise ValueError(
            f"Agent {agent_id!r} must define a non-empty 'provider' string"
        )

    providers = resolved_config.get("providers") or {}
    provider_defaults = dict(providers.get(provider_name) or {})
    policy_default = (
        str(((resolved_config.get(_MIXIN_POLICY_KEY) or {}).get("default_merge")))
        if (
            isinstance(resolved_config.get(_MIXIN_POLICY_KEY), dict)
            and (resolved_config.get(_MIXIN_POLICY_KEY) or {}).get("default_merge")
            in {"shallow", "deep"}
        )
        else "shallow"
    )
    agent_directive = (
        agent_cfg.get(MERGE_KEY)
        if MERGE_KEY in agent_cfg
        else agent_cfg.get(_MIXIN_MERGE_KEY)
    )
    provider_directive = (
        provider_defaults.get(MERGE_KEY)
        if MERGE_KEY in provider_defaults
        else provider_defaults.get(_MIXIN_MERGE_KEY)
    )
    merge_directive = (
        agent_directive if agent_directive is not None else provider_directive
    )

    # Provider key used by AgentCore selector: prefer explicit, fallback to name
    provider_key = provider_defaults.get("provider") or provider_name

    agent_overlay = _overlay_with_merge_directive(agent_cfg, merge_directive)
    merged = _merge_mappings(
        provider_defaults,
        agent_overlay,
        policy_default,
        path=f"agents.{agent_id}",
    )
    merged["provider"] = provider_key
    # These keys control application/plugin-package resolution and should not
    # be forwarded into the runtime provider/tool config.
    merged.pop("plugins", None)
    merged.pop("disabled_plugins", None)
    merged.pop("enabled", None)
    merged.pop(_MIXIN_REFS_KEY, None)
    merged.pop(_MIXIN_MERGE_KEY, None)
    merged.pop(MERGE_KEY, None)
    # Note: enabled_plugins and force_enabled_plugins are preserved for core-layer resolution
    # (enabled_plugins is used for default_enabled=False plugins, force_enabled_plugins bypasses tag checks)
    return merged


def resolve_request_config(
    base_agent_config: JsonMapping, overrides: Mapping[str, Any] | None
) -> Dict[str, Any]:
    """Merge per-request overrides into a base agent config.

    Callers should treat the returned mapping as immutable.
    """

    explicit_overrides = dict(overrides or {})
    selector = {**base_agent_config, **explicit_overrides}
    resolved_base, errors = resolve_config_variants(
        base_agent_config,
        selector=selector,
    )
    if errors:
        details = "; ".join(
            " - ".join(
                str(value)
                for value in (
                    error.get("type"),
                    error.get("path"),
                    error.get("detail"),
                )
                if value
            )
            for error in errors
        )
        raise ValueError(f"Invalid configuration variants: {details}")
    return {**resolved_base, **explicit_overrides}


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
