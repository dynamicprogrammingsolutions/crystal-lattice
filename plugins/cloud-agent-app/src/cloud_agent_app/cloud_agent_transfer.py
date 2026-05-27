from __future__ import annotations

import copy
import fnmatch
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional, Set

from agent_app.config import resolve_config_mixins


CLOUD_INSTANCE_DIR = "/cloud-agent/instance"
CLOUD_WORKSPACE_DIR = f"{CLOUD_INSTANCE_DIR}/workspace"
CLOUD_SESSIONS_DIR = f"{CLOUD_INSTANCE_DIR}/sessions"
CLOUD_CONFIG_PATH = f"{CLOUD_INSTANCE_DIR}/config/config.json"
CLOUD_CONFIG_ASSETS_DIR = f"{CLOUD_INSTANCE_DIR}/config/assets"
CLOUD_CACHE_DIR = "/cloud-agent/cache"
CLOUD_PLUGIN_CACHE_DIR = f"{CLOUD_CACHE_DIR}/plugin_cache/plugins"

ENV_PLACEHOLDER_RE = re.compile(r"\$\{env:([^}]+)\}")

RESERVED_RUNTIME_ENV_NAMES = {
    "BUILTIN_PLUGINS",
    "CLOUD_AGENT_CACHE_DIR",
    "CLOUD_AGENT_CONFIG_PATH",
    "CLOUD_AGENT_INSTANCE_DIR",
    "CLOUD_AGENT_SESSIONS_DIR",
    "CLOUD_AGENT_WORKSPACE_DIR",
    "CLOUD_WORKSPACE_DIR",
    "CONFIG_DIR",
    "LOCAL_WORKSPACE_DIR",
    "SESSION_DIR",
    "SESSION_ID",
    "TRANSFER_DIR",
    "WORKING_DIR",
    "PIP_CACHE_DIR",
    "XDG_CACHE_HOME",
}


def prepare_cloud_transfer(
    *,
    raw_config: Mapping[str, Any],
    config_path: Path,
    transfer_dir: Path,
    cloud_agent_config: Mapping[str, Any],
    env: Mapping[str, str],
    selected_agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Write cloud runtime config/assets/env into ``transfer_dir``.

    This helper owns the local-to-cloud packaging policy for runtime config.
    It intentionally does not rewrite plugin-owned settings such as
    ``working_directory`` and ``allowed_paths``.
    """

    cloud_root = transfer_dir / ".cloud-agent"
    config_root = cloud_root / "config"
    assets_root = config_root / "assets"
    env_root = cloud_root / "env"

    config_root.mkdir(parents=True, exist_ok=True)
    env_root.mkdir(parents=True, exist_ok=True)

    portable_config, config_manifest = build_portable_config(
        raw_config,
        cloud_agent_config=cloud_agent_config,
        selected_agent_id=selected_agent_id,
    )
    (config_root / "config.json").write_text(
        json.dumps(portable_config, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    assets_manifest = copy_config_assets(
        config_dir=Path(env.get("CONFIG_DIR") or config_path.parent),
        target_dir=assets_root,
        policy=_mapping(cloud_agent_config.get("config_assets")),
    )
    env_manifest = write_runtime_env(
        raw_config=raw_config,
        config_dir=Path(env.get("CONFIG_DIR") or config_path.parent),
        target_dir=env_root,
        policy=_mapping(cloud_agent_config.get("runtime_env")),
        env=env,
    )

    manifest = {
        "config": config_manifest,
        "config_assets": assets_manifest,
        "runtime_env": env_manifest,
    }
    (cloud_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def build_portable_config(
    raw_config: Mapping[str, Any],
    *,
    cloud_agent_config: Mapping[str, Any] | None = None,
    selected_agent_id: Optional[str] = None,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    if selected_agent_id:
        config, optimization_manifest = _build_selected_agent_config(
            raw_config, selected_agent_id=selected_agent_id
        )
    else:
        config = copy.deepcopy(dict(raw_config))
        optimization_manifest = None
    rewrites = []

    app_cfg = config.get("application")
    if isinstance(app_cfg, MutableMapping) and "cloud_agent" in app_cfg:
        app_cfg = dict(app_cfg)
        app_cfg.pop("cloud_agent", None)
        config["application"] = app_cfg
        rewrites.append(
            {
                "path": "application.cloud_agent",
                "reason": "local_orchestrator_config_removed",
            }
        )

    config["plugin_cache_dir"] = CLOUD_PLUGIN_CACHE_DIR
    rewrites.append({"path": "plugin_cache_dir", "reason": "cloud_runtime_storage"})

    plugin_policy = config.get("plugin_policy")
    if plugin_policy is None:
        config["plugin_policy"] = {"base_dir": "${env:CONFIG_DIR}"}
        rewrites.append(
            {"path": "plugin_policy.base_dir", "reason": "cloud_config_assets_base_dir"}
        )
    elif isinstance(plugin_policy, MutableMapping) and not plugin_policy.get(
        "base_dir"
    ):
        plugin_policy = dict(plugin_policy)
        plugin_policy["base_dir"] = "${env:CONFIG_DIR}"
        config["plugin_policy"] = plugin_policy
        rewrites.append(
            {"path": "plugin_policy.base_dir", "reason": "cloud_config_assets_base_dir"}
        )

    manifest: Dict[str, Any] = {"rewrites": rewrites}
    disabled_plugin_specs = _string_list(
        _mapping(cloud_agent_config).get("disabled_plugins")
    )
    if disabled_plugin_specs:
        manifest["disabled_plugins"] = _remove_cloud_disabled_plugin_specs(
            config, disabled_plugin_specs
        )
    if optimization_manifest is not None:
        manifest["optimization"] = optimization_manifest
    return config, manifest


def _build_selected_agent_config(
    raw_config: Mapping[str, Any], *, selected_agent_id: str
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    config, mixin_errors = resolve_config_mixins(raw_config)
    agent_id = str(selected_agent_id).strip()
    agents_in = config.get("agents") if isinstance(config.get("agents"), dict) else {}
    if agent_id not in agents_in:
        raise ValueError(f"Selected agent {agent_id!r} is not present in config")

    kept_agents = {agent_id: copy.deepcopy(agents_in[agent_id])}
    used_provider_ids = []
    for agent_cfg in kept_agents.values():
        provider_id = agent_cfg.get("provider") if isinstance(agent_cfg, dict) else None
        if (
            isinstance(provider_id, str)
            and provider_id
            and provider_id not in used_provider_ids
        ):
            used_provider_ids.append(provider_id)

    providers_in = (
        config.get("providers") if isinstance(config.get("providers"), dict) else {}
    )
    kept_providers = {
        provider_id: copy.deepcopy(providers_in[provider_id])
        for provider_id in used_provider_ids
        if provider_id in providers_in
    }

    config["agents"] = kept_agents
    config["providers"] = kept_providers
    config.pop("mixins", None)
    config.pop("mixin_policy", None)

    return config, {
        "selected_agent_id": agent_id,
        "kept_agent_ids": list(kept_agents.keys()),
        "kept_provider_ids": list(kept_providers.keys()),
        "removed_agent_count": max(0, len(agents_in) - len(kept_agents)),
        "removed_provider_count": max(0, len(providers_in) - len(kept_providers)),
        "mixin_errors": mixin_errors,
    }


def copy_config_assets(
    *, config_dir: Path, target_dir: Path, policy: Mapping[str, Any]
) -> Dict[str, Any]:
    include = bool(policy.get("include_config_dir", True))
    excludes = _string_list(policy.get("exclude"))
    max_bytes = _optional_int(policy.get("max_top_level_entry_bytes"))
    copied = []
    excluded = []

    if not include:
        return {"copied": copied, "excluded": [{"path": ".", "reason": "disabled"}]}

    config_dir = config_dir.expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    if not config_dir.exists():
        return {"copied": copied, "excluded": [{"path": ".", "reason": "missing"}]}

    for entry in sorted(config_dir.iterdir(), key=lambda path: path.name):
        rel = entry.name
        if _matches_any(rel, excludes):
            excluded.append({"path": rel, "reason": "exclude_pattern"})
            continue
        if entry.is_symlink():
            excluded.append({"path": rel, "reason": "symlink"})
            continue
        try:
            size = _top_level_size(entry)
        except OSError:
            excluded.append({"path": rel, "reason": "unreadable"})
            continue
        if max_bytes is not None and size > max_bytes:
            excluded.append({"path": rel, "reason": "size_limit", "bytes": size})
            continue

        target = target_dir / entry.name
        if entry.is_dir():
            shutil.copytree(
                entry,
                target,
                symlinks=False,
                ignore=lambda current, names: [
                    name
                    for name in names
                    if Path(current, name).is_symlink()
                    or _matches_any(
                        str(Path(current, name).resolve().relative_to(config_dir)),
                        excludes,
                    )
                ],
            )
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry, target)
        copied.append({"path": rel, "bytes": size})

    return {"copied": copied, "excluded": excluded}


def write_runtime_env(
    *,
    raw_config: Mapping[str, Any],
    config_dir: Path,
    target_dir: Path,
    policy: Mapping[str, Any],
    env: Mapping[str, str],
) -> Dict[str, Any]:
    include_config_env = bool(policy.get("include_config_env", True))
    include_names = set(_string_list(policy.get("include")))
    exclude_names = set(_string_list(policy.get("exclude")))
    names: Set[str] = set()
    if include_config_env:
        names.update(scan_env_placeholders(raw_config))
    names.update(include_names)
    names.difference_update(exclude_names)
    names.difference_update(RESERVED_RUNTIME_ENV_NAMES)

    values = {name: env[name] for name in sorted(names) if name in env}
    target_dir.mkdir(parents=True, exist_ok=True)
    runtime_env = target_dir / "runtime.env"
    runtime_env.write_text(
        "".join(f"{name}={_dotenv_quote(value)}\n" for name, value in values.items()),
        encoding="utf-8",
    )

    copied_env_files = []
    env_files_dir = target_dir / "runtime.env.d"
    for index, raw_path in enumerate(_string_list(policy.get("env_files"))):
        source = Path(raw_path).expanduser()
        if not source.is_absolute():
            source = config_dir / source
        if not source.is_file():
            copied_env_files.append({"path": raw_path, "status": "missing"})
            continue
        env_files_dir.mkdir(parents=True, exist_ok=True)
        target = env_files_dir / f"{index:03d}-{source.name}"
        shutil.copy2(source, target)
        copied_env_files.append(
            {"path": raw_path, "status": "copied", "target": target.name}
        )

    missing = sorted(name for name in names if name not in env)
    return {
        "included_names": sorted(values.keys()),
        "missing_names": missing,
        "excluded_names": sorted(
            (set(_string_list(policy.get("exclude"))) | RESERVED_RUNTIME_ENV_NAMES)
            & (scan_env_placeholders(raw_config) | include_names)
        ),
        "env_files": copied_env_files,
    }


def scan_env_placeholders(value: Any) -> Set[str]:
    names: Set[str] = set()
    if isinstance(value, str):
        names.update(match.group(1) for match in ENV_PLACEHOLDER_RE.finditer(value))
    elif isinstance(value, Mapping):
        for item in value.values():
            names.update(scan_env_placeholders(item))
    elif isinstance(value, list):
        for item in value:
            names.update(scan_env_placeholders(item))
    return names


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _remove_cloud_disabled_plugin_specs(
    config: MutableMapping[str, Any], disabled_specs: Iterable[str]
) -> Dict[str, Any]:
    disabled_set = set(disabled_specs)
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


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _matches_any(path: str, patterns: Iterable[str]) -> bool:
    normalized = path.replace(os.sep, "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


def _top_level_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    total = 0
    for root, dirs, files in os.walk(path):
        root_path = Path(root)
        dirs[:] = [name for name in dirs if not (root_path / name).is_symlink()]
        for name in files:
            file_path = root_path / name
            if not file_path.is_symlink():
                total += file_path.stat().st_size
    return total


def _dotenv_quote(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_@%+=:,./-]*", value):
        return value
    return (
        '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    )


__all__ = [
    "CLOUD_CONFIG_ASSETS_DIR",
    "CLOUD_CONFIG_PATH",
    "CLOUD_INSTANCE_DIR",
    "CLOUD_PLUGIN_CACHE_DIR",
    "CLOUD_SESSIONS_DIR",
    "CLOUD_WORKSPACE_DIR",
    "RESERVED_RUNTIME_ENV_NAMES",
    "build_portable_config",
    "copy_config_assets",
    "prepare_cloud_transfer",
    "scan_env_placeholders",
    "write_runtime_env",
]
