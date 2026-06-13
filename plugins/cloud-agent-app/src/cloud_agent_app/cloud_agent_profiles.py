from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence


DEFAULT_PROJECT_CONFIG_PATH = "${env:WORKING_DIR}/.cloud-agent/cloud-agent.json"
DEFAULT_RUNTIME_IMAGE = "cloud-agent-runtime:latest"
CONTAINER_MODES = {"image", "dockerfile"}
MOUNT_SCOPES = {"global", "profile", "connection", "instance"}

PROFILE_SECTIONS = {
    "transfer_up_profiles",
    "sync_down_profiles",
    "container_profiles",
}
DEFAULT_PROFILE_KEYS = {
    "default_transfer_up_profile",
    "default_sync_down_profile",
    "default_container_profile",
}
SCRIPT_FIELDS_BY_SECTION = {
    "transfer_up_profiles": {
        "local_stage_script",
        "local_transfer_script",
        "cloud_setup_script",
        "install_script",
        "validation_script",
    },
    "sync_down_profiles": {
        "cloud_export_script",
        "cloud_mark_synced_script",
        "local_apply_script",
    },
}
OPTIONAL_TRANSFER_HOOK_DEFAULTS = {
    "local_stage_script": "${env:WORKING_DIR}/.cloud-agent/local-stage",
    "install_script": "${env:WORKING_DIR}/.cloud-agent/install-cloud",
    "validation_script": "${env:WORKING_DIR}/.cloud-agent/validate-cloud",
}
ENV_PLACEHOLDER_RE = re.compile(r"\$\{env:([^}]+)\}")


ScriptCandidate = tuple[Any, Path]
ScriptCandidates = Dict[tuple[str, str, str], list[ScriptCandidate]]


def resolve_cloud_agent_profiles(
    cloud_agent_config: Mapping[str, Any],
    *,
    env: Mapping[str, str] | None = None,
) -> Dict[str, Any]:
    """Resolve cloud profile defaults into the existing plugin state shape."""

    env_map = dict(os.environ if env is None else env)
    configured_workspace = cloud_agent_config.get("workspace_dir")
    workspace_hint = (
        str(configured_workspace).strip()
        if isinstance(configured_workspace, str) and configured_workspace.strip()
        else ""
    )
    working_dir = Path(
        env_map.get("WORKING_DIR") or workspace_hint or os.getcwd()
    ).expanduser()
    merged = copy.deepcopy(dict(cloud_agent_config))
    _reject_requires(merged, path="application.cloud_agent")

    script_candidates = _initial_script_candidates(merged, base_dir=working_dir)
    project_config = _load_project_config(merged, env=env_map, working_dir=working_dir)
    if project_config is not None:
        project_config_data, project_base_dir = project_config
        _reject_requires(project_config_data, path="project cloud-agent config")
        _merge_profile_override(
            merged,
            project_config_data,
            script_candidates=script_candidates,
            base_dir=project_base_dir,
        )
    _ensure_optional_transfer_hook_candidates(
        merged, script_candidates=script_candidates, base_dir=working_dir
    )

    if not any(
        isinstance(merged.get(section), Mapping) for section in PROFILE_SECTIONS
    ):
        return dict(merged)

    _validate_sections(merged)
    transfer_id = _required_id(merged, "default_transfer_up_profile")
    sync_id = _required_id(merged, "default_sync_down_profile")
    container_id = _required_id(merged, "default_container_profile")

    transfer = _profile(merged, "transfer_up_profiles", transfer_id)
    sync = _profile(merged, "sync_down_profiles", sync_id)
    container = _profile(merged, "container_profiles", container_id)

    _validate_declared_compatibility(
        merged,
        transfer_id=transfer_id,
        transfer=transfer,
        sync_id=sync_id,
        sync=sync,
    )

    effective = dict(merged)
    effective["selected_transfer_up_profile"] = transfer_id
    effective["selected_sync_down_profile"] = sync_id
    effective["selected_container_profile"] = container_id
    effective["local_stage_script"] = _resolve_optional_script(
        script_candidates,
        "transfer_up_profiles",
        transfer_id,
        "local_stage_script",
        env=env_map,
        allowed_missing_paths={
            _standard_optional_hook_path("local_stage_script", env=env_map)
        },
    )
    effective["local_transfer_script"] = _resolve_script(
        script_candidates,
        "transfer_up_profiles",
        transfer_id,
        "local_transfer_script",
        env=env_map,
    )
    effective["cloud_setup_script"] = _resolve_script(
        script_candidates,
        "transfer_up_profiles",
        transfer_id,
        "cloud_setup_script",
        env=env_map,
    )
    effective["install_script"] = _resolve_optional_script(
        script_candidates,
        "transfer_up_profiles",
        transfer_id,
        "install_script",
        env=env_map,
        allowed_missing_paths={
            _standard_optional_hook_path("install_script", env=env_map)
        },
    )
    effective["validation_script"] = _resolve_optional_script(
        script_candidates,
        "transfer_up_profiles",
        transfer_id,
        "validation_script",
        env=env_map,
        allowed_missing_paths={
            _standard_optional_hook_path("validation_script", env=env_map)
        },
    )
    effective["cloud_export_script"] = _resolve_script(
        script_candidates,
        "sync_down_profiles",
        sync_id,
        "cloud_export_script",
        env=env_map,
    )
    effective["local_apply_script"] = _resolve_script(
        script_candidates,
        "sync_down_profiles",
        sync_id,
        "local_apply_script",
        env=env_map,
    )
    effective["cloud_mark_synced_script"] = _resolve_optional_script(
        script_candidates,
        "sync_down_profiles",
        sync_id,
        "cloud_mark_synced_script",
        env=env_map,
    )

    resolved_container = _resolve_container_profile(
        container_id, container, env=env_map, base_dir=working_dir
    )
    effective["container"] = resolved_container
    return effective


def _resolve_container_profile(
    profile_id: str,
    profile: Mapping[str, Any],
    *,
    env: Mapping[str, str],
    base_dir: Path,
) -> Dict[str, Any]:
    mode = _container_mode(profile)
    image = _container_image(profile)
    raw_context = profile.get("context")
    resolved: Dict[str, Any] = {
        "profile_id": profile_id,
        "mode": mode,
        "image": image,
    }
    if "label" in profile and isinstance(profile.get("label"), str):
        resolved["label"] = str(profile["label"])

    if mode == "dockerfile":
        dockerfile = _required_container_string(profile, "dockerfile", profile_id)
        resolved["dockerfile"] = dockerfile
        if isinstance(raw_context, list):
            context_entries = _container_path_entries(
                profile, "context", profile_id, env=env, base_dir=base_dir
            )
            if not context_entries:
                raise ValueError(
                    f"application.cloud_agent.container_profiles.{profile_id}.context must not be empty"
                )
            resolved["context_entries"] = context_entries
        else:
            context = _required_container_string(profile, "context", profile_id)
            resolved["context"] = context
            resolved["context_path"] = str(
                _resolve_config_path(context, env=env, base_dir=base_dir)
            )
            resolved["dockerfile_path"] = str(
                _resolve_config_path(dockerfile, env=env, base_dir=base_dir)
            )
        target = _optional_container_string(profile, "target")
        if target is not None:
            resolved["target"] = target
        resolved["build_args"] = _container_build_args(profile, profile_id)
        resolved["build_assets"] = _container_path_entries(
            profile, "build_assets", profile_id, env=env, base_dir=base_dir
        )
    elif any(
        key in profile for key in ("dockerfile", "context", "target", "build_args")
    ):
        raise ValueError(
            f"application.cloud_agent.container_profiles.{profile_id} uses Dockerfile fields but mode is {mode!r}"
        )

    resolved["cache_mounts"] = _container_mounts(profile, "cache_mounts", profile_id)
    resolved["mounts"] = _container_mounts(profile, "mounts", profile_id)
    return resolved


def _container_mode(profile: Mapping[str, Any]) -> str:
    raw = profile.get("mode")
    if raw is None:
        return "dockerfile" if "dockerfile" in profile else "image"
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(
            "application.cloud_agent.container_profiles.<id>.mode must be a string"
        )
    mode = raw.strip()
    if mode not in CONTAINER_MODES:
        raise ValueError(
            "application.cloud_agent.container_profiles.<id>.mode must be one of: "
            + ", ".join(sorted(CONTAINER_MODES))
        )
    return mode


def _container_image(profile: Mapping[str, Any]) -> str:
    image = profile.get("image")
    if not isinstance(image, str) or not image.strip():
        raise ValueError(
            "application.cloud_agent.container_profiles.<id>.image is required"
        )
    return image.strip()


def _required_container_string(
    profile: Mapping[str, Any], key: str, profile_id: str
) -> str:
    value = _optional_container_string(profile, key)
    if value is None:
        raise ValueError(
            f"application.cloud_agent.container_profiles.{profile_id}.{key} is required"
        )
    return value


def _optional_container_string(profile: Mapping[str, Any], key: str) -> str | None:
    value = profile.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"application.cloud_agent.container_profiles.<id>.{key} must be a non-empty string"
        )
    return value.strip()


def _container_build_args(
    profile: Mapping[str, Any], profile_id: str
) -> Dict[str, str]:
    raw = profile.get("build_args")
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise ValueError(
            f"application.cloud_agent.container_profiles.{profile_id}.build_args must be an object"
        )
    result: Dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(
                f"application.cloud_agent.container_profiles.{profile_id}.build_args keys must be non-empty strings"
            )
        if not isinstance(value, str):
            raise ValueError(
                f"application.cloud_agent.container_profiles.{profile_id}.build_args.{key} must be a string"
            )
        result[key.strip()] = value
    return result


def _container_path_entries(
    profile: Mapping[str, Any],
    key: str,
    profile_id: str,
    *,
    env: Mapping[str, str],
    base_dir: Path,
) -> list[Dict[str, str]]:
    raw = profile.get(key)
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(
            f"application.cloud_agent.container_profiles.{profile_id}.{key} must be a list"
        )
    result: list[Dict[str, str]] = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, Mapping):
            raise ValueError(
                f"application.cloud_agent.container_profiles.{profile_id}.{key}[{index}] must be an object"
            )
        source = entry.get("source")
        target = entry.get("target")
        if not isinstance(source, str) or not source.strip():
            raise ValueError(
                f"application.cloud_agent.container_profiles.{profile_id}.{key}[{index}].source is required"
            )
        if not isinstance(target, str) or not target.strip():
            raise ValueError(
                f"application.cloud_agent.container_profiles.{profile_id}.{key}[{index}].target is required"
            )
        result.append(
            {
                "source": source.strip(),
                "source_path": str(
                    _resolve_config_path(source, env=env, base_dir=base_dir)
                ),
                "target": target.strip(),
            }
        )
    return result


def _container_mounts(
    profile: Mapping[str, Any], key: str, profile_id: str
) -> list[Dict[str, str]]:
    raw = profile.get(key)
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(
            f"application.cloud_agent.container_profiles.{profile_id}.{key} must be a list"
        )
    result: list[Dict[str, str]] = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, Mapping):
            raise ValueError(
                f"application.cloud_agent.container_profiles.{profile_id}.{key}[{index}] must be an object"
            )
        raw_id = entry.get("id")
        target = entry.get("target")
        raw_scope = entry.get("scope", "profile")
        if not isinstance(raw_id, str) or not raw_id.strip():
            raise ValueError(
                f"application.cloud_agent.container_profiles.{profile_id}.{key}[{index}].id is required"
            )
        if not isinstance(target, str) or not target.strip():
            raise ValueError(
                f"application.cloud_agent.container_profiles.{profile_id}.{key}[{index}].target is required"
            )
        if not isinstance(raw_scope, str) or raw_scope.strip() not in MOUNT_SCOPES:
            raise ValueError(
                f"application.cloud_agent.container_profiles.{profile_id}.{key}[{index}].scope must be one of: "
                + ", ".join(sorted(MOUNT_SCOPES))
            )
        mount_id = raw_id.strip()
        scope = raw_scope.strip()
        result.append({"id": mount_id, "target": target, "scope": scope})
    return result


def _load_project_config(
    config: Mapping[str, Any], *, env: Mapping[str, str], working_dir: Path
) -> tuple[Dict[str, Any], Path] | None:
    raw_path = config.get("project_config_path")
    if raw_path is None:
        raw_path = DEFAULT_PROJECT_CONFIG_PATH
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None

    expanded = _expand_env(raw_path, env)
    path = Path(expanded).expanduser()
    if not path.is_absolute():
        path = working_dir / path
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(
            f"application.cloud_agent.project_config_path is not a file: {path}"
        )
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("Project cloud-agent config must be a JSON object")
    return parsed, _project_script_base_dir(path, env=env, working_dir=working_dir)


def _project_script_base_dir(
    path: Path, *, env: Mapping[str, str], working_dir: Path
) -> Path:
    if path.name == "cloud-agent.json" and path.parent.name == ".cloud-agent":
        return path.parent.parent
    if "WORKING_DIR" in env:
        return working_dir
    return path.parent


def _merge_profile_override(
    base: Dict[str, Any],
    override: Mapping[str, Any],
    *,
    script_candidates: ScriptCandidates,
    base_dir: Path,
) -> None:
    for key in DEFAULT_PROFILE_KEYS:
        if key in override:
            base[key] = copy.deepcopy(override[key])

    for section in PROFILE_SECTIONS:
        raw_profiles = override.get(section)
        if raw_profiles is None:
            continue
        if not isinstance(raw_profiles, Mapping):
            raise ValueError(f"application.cloud_agent.{section} must be an object")
        target = base.setdefault(section, {})
        if not isinstance(target, dict):
            raise ValueError(f"application.cloud_agent.{section} must be an object")

        script_fields = SCRIPT_FIELDS_BY_SECTION.get(section, set())
        for profile_id, raw_profile in raw_profiles.items():
            if not isinstance(profile_id, str) or not profile_id.strip():
                raise ValueError(
                    f"application.cloud_agent.{section} profile ids must be strings"
                )
            if not isinstance(raw_profile, Mapping):
                raise ValueError(
                    f"application.cloud_agent.{section}.{profile_id} must be an object"
                )
            existing = target.get(profile_id)
            merged_profile = (
                {}
                if section == "container_profiles"
                else dict(existing) if isinstance(existing, Mapping) else {}
            )
            for field, value in raw_profile.items():
                merged_profile[field] = copy.deepcopy(value)
                if field in script_fields:
                    key = (section, profile_id, field)
                    inherited = script_candidates.get(key, [])
                    candidates = _script_candidates(value, base_dir)
                    if isinstance(value, list):
                        candidates.extend(inherited)
                    script_candidates[key] = candidates
            target[profile_id] = merged_profile


def _initial_script_candidates(
    config: Mapping[str, Any], *, base_dir: Path
) -> ScriptCandidates:
    candidates: ScriptCandidates = {}
    for section, fields in SCRIPT_FIELDS_BY_SECTION.items():
        profiles = config.get(section)
        if not isinstance(profiles, Mapping):
            continue
        for profile_id, profile in profiles.items():
            if not isinstance(profile_id, str) or not isinstance(profile, Mapping):
                continue
            for field in fields:
                if field in profile:
                    candidates[(section, profile_id, field)] = _script_candidates(
                        profile[field], base_dir
                    )
    return candidates


def _ensure_optional_transfer_hook_candidates(
    config: Mapping[str, Any],
    *,
    script_candidates: ScriptCandidates,
    base_dir: Path,
) -> None:
    profiles = config.get("transfer_up_profiles")
    if not isinstance(profiles, Mapping):
        return
    for profile_id, profile in profiles.items():
        if not isinstance(profile_id, str) or not isinstance(profile, Mapping):
            continue
        for field, default_value in OPTIONAL_TRANSFER_HOOK_DEFAULTS.items():
            key = ("transfer_up_profiles", profile_id, field)
            if key in script_candidates:
                continue
            script_candidates[key] = _script_candidates(default_value, base_dir)


def _script_candidates(value: Any, base_dir: Path) -> list[ScriptCandidate]:
    if isinstance(value, str):
        return [(value, base_dir)]
    if isinstance(value, list):
        return [(item, base_dir) for item in value if isinstance(item, str)]
    return []


def _resolve_script(
    candidates: ScriptCandidates,
    section: str,
    profile_id: str,
    field: str,
    *,
    env: Mapping[str, str],
) -> str:
    key = (section, profile_id, field)
    attempted: list[str] = []
    for raw, base_dir in candidates.get(key, []):
        if not isinstance(raw, str) or not raw.strip():
            continue
        path = Path(_expand_env(raw, env)).expanduser()
        if not path.is_absolute():
            path = base_dir / path
        path = path.resolve()
        attempted.append(str(path))
        if path.is_file():
            return str(path)

    path_label = f"application.cloud_agent.{section}.{profile_id}.{field}"
    if attempted:
        raise ValueError(
            f"{path_label} did not resolve to an existing script: {attempted}"
        )
    raise ValueError(f"{path_label} is required")


def _resolve_optional_script(
    candidates: ScriptCandidates,
    section: str,
    profile_id: str,
    field: str,
    *,
    env: Mapping[str, str],
    allowed_missing_paths: set[Path] | None = None,
) -> str | None:
    key = (section, profile_id, field)
    if key not in candidates:
        return None
    attempted: list[str] = []
    non_optional_attempts: list[str] = []
    for raw, base_dir in candidates.get(key, []):
        if not isinstance(raw, str) or not raw.strip():
            continue
        path = Path(_expand_env(raw, env)).expanduser()
        if not path.is_absolute():
            path = base_dir / path
        path = path.resolve()
        attempted.append(str(path))
        if path.is_file():
            return str(path)
        if allowed_missing_paths is None or path not in allowed_missing_paths:
            non_optional_attempts.append(str(path))

    if non_optional_attempts:
        path_label = f"application.cloud_agent.{section}.{profile_id}.{field}"
        raise ValueError(
            f"{path_label} did not resolve to an existing script: {attempted}"
        )
    return None


def _validate_sections(config: Mapping[str, Any]) -> None:
    for section in PROFILE_SECTIONS:
        profiles = config.get(section)
        if profiles is None:
            continue
        if not isinstance(profiles, Mapping):
            raise ValueError(f"application.cloud_agent.{section} must be an object")
        for profile_id, profile in profiles.items():
            if not isinstance(profile_id, str) or not profile_id.strip():
                raise ValueError(
                    f"application.cloud_agent.{section} profile ids must be strings"
                )
            if not isinstance(profile, Mapping):
                raise ValueError(
                    f"application.cloud_agent.{section}.{profile_id} must be an object"
                )


def _required_id(config: Mapping[str, Any], key: str) -> str:
    value = config.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"application.cloud_agent.{key} is required")
    return value.strip()


def _profile(
    config: Mapping[str, Any], section: str, profile_id: str
) -> Mapping[str, Any]:
    profiles = config.get(section)
    if not isinstance(profiles, Mapping) or profile_id not in profiles:
        raise ValueError(
            f"application.cloud_agent.{section}.{profile_id} is not defined"
        )
    profile = profiles[profile_id]
    if not isinstance(profile, Mapping):
        raise ValueError(
            f"application.cloud_agent.{section}.{profile_id} must be an object"
        )
    return profile


def _validate_declared_compatibility(
    config: Mapping[str, Any],
    *,
    transfer_id: str,
    transfer: Mapping[str, Any],
    sync_id: str,
    sync: Mapping[str, Any],
) -> None:
    transfer_profiles = config.get("transfer_up_profiles")
    sync_profiles = config.get("sync_down_profiles")
    if not isinstance(transfer_profiles, Mapping) or not isinstance(
        sync_profiles, Mapping
    ):
        return

    for declared in _string_list(transfer.get("compatible_sync_down_profiles")):
        if declared not in sync_profiles:
            raise ValueError(
                f"application.cloud_agent.transfer_up_profiles.{transfer_id}.compatible_sync_down_profiles references unknown sync profile {declared!r}"
            )
    for declared in _string_list(sync.get("compatible_transfer_up_profiles")):
        if declared not in transfer_profiles:
            raise ValueError(
                f"application.cloud_agent.sync_down_profiles.{sync_id}.compatible_transfer_up_profiles references unknown transfer profile {declared!r}"
            )

    compatible_syncs = _string_list(transfer.get("compatible_sync_down_profiles"))
    if compatible_syncs and sync_id not in compatible_syncs:
        raise ValueError(
            f"application.cloud_agent default sync profile {sync_id!r} is not compatible with transfer profile {transfer_id!r}"
        )

    compatible_transfers = _string_list(sync.get("compatible_transfer_up_profiles"))
    if compatible_transfers and transfer_id not in compatible_transfers:
        raise ValueError(
            f"application.cloud_agent default transfer profile {transfer_id!r} is not compatible with sync profile {sync_id!r}"
        )


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _reject_requires(value: Any, *, path: str) -> None:
    if isinstance(value, Mapping):
        if "requires" in value:
            raise ValueError(
                f"{path}.requires is not supported; dependencies belong in container images or install scripts"
            )
        for key, item in value.items():
            _reject_requires(item, path=f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _reject_requires(item, path=f"{path}[{index}]")


def _expand_env(value: str, env: Mapping[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        return env.get(match.group(1), "")

    return ENV_PLACEHOLDER_RE.sub(replace, value)


def _resolve_config_path(value: str, *, env: Mapping[str, str], base_dir: Path) -> Path:
    expanded = _expand_env(value, env)
    path = Path(expanded).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def _standard_optional_hook_path(field: str, *, env: Mapping[str, str]) -> Path:
    raw = OPTIONAL_TRANSFER_HOOK_DEFAULTS[field]
    working_dir = Path(env.get("WORKING_DIR") or os.getcwd()).expanduser()
    path = Path(_expand_env(raw, env)).expanduser()
    if not path.is_absolute():
        path = working_dir / path
    return path.resolve()


__all__ = [
    "DEFAULT_PROJECT_CONFIG_PATH",
    "DEFAULT_RUNTIME_IMAGE",
    "resolve_cloud_agent_profiles",
]
