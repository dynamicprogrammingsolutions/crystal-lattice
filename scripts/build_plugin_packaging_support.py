#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "core" / "python"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from agent_app.config import collect_unique_declared_plugin_specs
from agent_app.config import load_resolved_config
from agent_app.config import remove_declared_plugin_specs_by_exact_match


EXCLUDED_DIR_NAMES = {
    ".crystal",
    ".git",
    ".mypy_cache",
    ".plugin_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "auth",
    "build",
    "dist",
    "htmlcov",
    "node_modules",
    "tests",
}
EXCLUDED_FILE_SUFFIXES = {
    ".log",
    ".pyc",
    ".pyo",
}
EXCLUDED_FILE_NAMES = {
    ".coverage",
}
LOCAL_PLUGIN_SPEC_PREFIXES = ("path:", "bash:", "node:")
SKIPPED_RESOURCE_KEYS = {
    "disabled_plugins",
    "enabled_plugins",
    "force_enabled_plugins",
    "plugins",
}


@dataclass(frozen=True)
class PackagingPluginAnalysis:
    resolved_config: dict[str, Any]
    config_errors: list[dict[str, Any]]
    selected_plugin_names: set[str]
    builtin_resource_paths: set[Path]
    local_project_names: set[str]


def analyze_packaging_plugins(
    *,
    config_path: Path,
    plugins_root: Path,
    cloud_disabled_plugin_specs: Iterable[str] | None = None,
) -> PackagingPluginAnalysis:
    config_path = config_path.expanduser().resolve()
    plugins_root = plugins_root.expanduser().resolve()
    resolved_config, config_errors, _resolution_env = load_resolved_config(
        config_path,
        env_overrides={
            "BUILTIN_PLUGINS": str(plugins_root),
            "CLOUD_RUNTIME_BUILD_CONTEXT": str(
                config_path.parent / "__cloud_runtime_build_context__"
            ),
        },
    )

    analysis_config = copy.deepcopy(resolved_config)
    if cloud_disabled_plugin_specs:
        remove_declared_plugin_specs_by_exact_match(
            analysis_config,
            cloud_disabled_plugin_specs,
        )

    selected_plugin_names = discover_selected_bundled_plugin_names_from_resolved_config(
        analysis_config,
        plugins_root=plugins_root,
        config_dir=config_path.parent,
    )
    builtin_resource_paths = (
        discover_builtin_plugin_resource_paths_from_resolved_config(
            analysis_config,
            plugins_root=plugins_root,
            config_dir=config_path.parent,
        )
    )
    local_project_names = resolve_local_project_names(selected_plugin_names, plugins_root)
    return PackagingPluginAnalysis(
        resolved_config=analysis_config,
        config_errors=config_errors,
        selected_plugin_names=selected_plugin_names,
        builtin_resource_paths=builtin_resource_paths,
        local_project_names=local_project_names,
    )


def discover_selected_bundled_plugin_names(
    selected_config: Path,
    plugins_root: Path,
    *,
    cloud_disabled_plugin_specs: Iterable[str] | None = None,
) -> set[str]:
    return analyze_packaging_plugins(
        config_path=selected_config,
        plugins_root=plugins_root,
        cloud_disabled_plugin_specs=cloud_disabled_plugin_specs,
    ).selected_plugin_names


def discover_selected_bundled_plugin_names_from_resolved_config(
    resolved_config: Mapping[str, Any],
    *,
    plugins_root: Path,
    config_dir: Path,
) -> set[str]:
    names: set[str] = set()
    for spec in collect_unique_declared_plugin_specs(resolved_config):
        plugin_name = resolve_builtin_plugin_name_from_spec(
            spec,
            plugins_root=plugins_root,
            config_dir=config_dir,
        )
        if plugin_name is not None:
            names.add(plugin_name)
    return names


def discover_builtin_plugin_resource_paths(
    selected_config: Path,
    plugins_root: Path,
    *,
    cloud_disabled_plugin_specs: Iterable[str] | None = None,
) -> set[Path]:
    return analyze_packaging_plugins(
        config_path=selected_config,
        plugins_root=plugins_root,
        cloud_disabled_plugin_specs=cloud_disabled_plugin_specs,
    ).builtin_resource_paths


def discover_builtin_plugin_resource_paths_from_resolved_config(
    resolved_config: Mapping[str, Any],
    *,
    plugins_root: Path,
    config_dir: Path,
) -> set[Path]:
    plugins_root = plugins_root.resolve()
    paths: set[Path] = set()
    for value in _iter_resource_string_values(resolved_config):
        candidate = _resolved_local_path_from_string(value, config_dir)
        if candidate is None or not candidate.is_file():
            continue
        try:
            candidate.relative_to(plugins_root)
        except ValueError:
            continue
        paths.add(candidate)
    return paths


def resolve_builtin_plugin_name_from_spec(
    spec: Any,
    *,
    plugins_root: Path,
    config_dir: Path,
) -> str | None:
    source_path = _resolved_local_path_from_spec(spec, config_dir)
    if source_path is None:
        return None
    return _builtin_plugin_name_from_path(source_path, plugins_root)


def resolve_local_project_names(
    selected_plugin_names: set[str], plugins_root: Path
) -> set[str]:
    plugins_root = plugins_root.resolve()
    pending = list(sorted(selected_plugin_names))
    resolved: set[str] = set()
    while pending:
        name = pending.pop(0)
        if name in resolved:
            continue
        project_dir = plugins_root / name
        if not project_dir.is_dir():
            continue
        resolved.add(name)
        descriptor_path = project_dir / "agent_plugin.json"
        if not descriptor_path.is_file():
            continue
        descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
        for dependency in descriptor.get("local_workspace_dependencies") or []:
            if not isinstance(dependency, dict):
                continue
            dep_path_raw = dependency.get("path")
            if not isinstance(dep_path_raw, str) or not dep_path_raw.strip():
                continue
            dependency_dir = (project_dir / dep_path_raw).resolve()
            try:
                dependency_name = dependency_dir.relative_to(plugins_root).parts[0]
            except (ValueError, IndexError):
                continue
            if dependency_name not in resolved:
                pending.append(dependency_name)
    return resolved


def stage_cloud_runtime_plugin_bundle(
    *,
    plugins_root: Path,
    selected_config: Path,
    output: Path,
    local_project_prefix: str | None = None,
    cloud_disabled_plugin_specs: Iterable[str] | None = None,
) -> dict[str, object]:
    plugins_root = plugins_root.expanduser().resolve()
    selected_config = selected_config.expanduser().resolve()
    output = output.expanduser().resolve()

    analysis = analyze_packaging_plugins(
        config_path=selected_config,
        plugins_root=plugins_root,
        cloud_disabled_plugin_specs=cloud_disabled_plugin_specs,
    )

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    bundled_plugins = output / "bundled_plugins"
    stage_preinstalled_plugins(
        bundled_plugins,
        plugins_root=plugins_root,
        selected_plugin_names=analysis.selected_plugin_names,
        builtin_resource_paths=analysis.builtin_resource_paths,
    )

    prefix = local_project_prefix or str(plugins_root)
    local_projects = [
        f"{prefix.rstrip('/')}/{name}"
        for name in sorted(analysis.local_project_names)
        if is_python_project(plugins_root / name)
    ]
    (output / "local-projects.txt").write_text(
        "".join(f"{project}\n" for project in local_projects),
        encoding="utf-8",
    )

    manifest = {
        "schema_version": 1,
        "preinstalled_plugins": sorted(analysis.selected_plugin_names),
        "local_projects": sorted(analysis.local_project_names),
        "local_project_requirements": local_projects,
        "resource_paths": [
            path.relative_to(plugins_root).as_posix()
            for path in sorted(analysis.builtin_resource_paths)
        ],
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def stage_preinstalled_plugins(
    destination: Path,
    *,
    plugins_root: Path,
    selected_plugin_names: set[str],
    builtin_resource_paths: set[Path],
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for plugin_name in sorted(selected_plugin_names):
        source = plugins_root / plugin_name
        if not source.is_dir():
            continue
        stage_preinstalled_plugin_metadata(
            source,
            destination / plugin_name,
            builtin_resource_paths=builtin_resource_paths,
        )

    manifest = {
        "schema_version": 1,
        "preinstalled_plugins": sorted(selected_plugin_names),
    }
    (destination / "bundled_plugins.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def stage_preinstalled_plugin_metadata(
    source: Path,
    target: Path,
    *,
    builtin_resource_paths: set[Path],
) -> None:
    target.mkdir(parents=True, exist_ok=True)
    descriptor_path = source / "agent_plugin.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["preinstalled"] = True
    (target / "agent_plugin.json").write_text(
        json.dumps(descriptor, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    for resource in sorted(builtin_resource_paths):
        try:
            relative = resource.relative_to(source)
        except ValueError:
            continue
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(resource, destination)


def copy_local_project_sources(
    destination: Path,
    *,
    plugins_root: Path,
    local_project_names: Iterable[str],
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name in sorted(set(local_project_names)):
        source = plugins_root / name
        if source.is_dir():
            copytree_sanitized(source, destination / name)


def is_python_project(project_dir: Path) -> bool:
    return (project_dir / "pyproject.toml").is_file() or (
        project_dir / "setup.py"
    ).is_file()


def copytree_sanitized(
    source: Path,
    destination: Path,
    *,
    excluded_dir_names: Iterable[str] = (),
) -> None:
    excluded_dirs = set(excluded_dir_names).union(EXCLUDED_DIR_NAMES)

    def ignore(_directory: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        for name in names:
            path = Path(name)
            if name in excluded_dirs or name.endswith(".egg-info"):
                ignored.add(name)
            elif name in EXCLUDED_FILE_NAMES:
                ignored.add(name)
            elif path.suffix in EXCLUDED_FILE_SUFFIXES:
                ignored.add(name)
        return ignored

    shutil.copytree(source, destination, ignore=ignore, ignore_dangling_symlinks=True)


def _iter_resource_string_values(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, child in value.items():
            if key in SKIPPED_RESOURCE_KEYS:
                continue
            yield from _iter_resource_string_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_resource_string_values(child)


def _resolved_local_path_from_spec(spec: Any, config_dir: Path) -> Path | None:
    raw_path: str | None = None
    if isinstance(spec, str):
        raw_path = _raw_local_path_from_string(spec)
    elif isinstance(spec, dict):
        candidate = spec.get("path")
        if isinstance(candidate, str) and candidate.strip():
            raw_path = candidate.strip()
    if raw_path is None:
        return None
    return _resolve_local_path(raw_path, config_dir)


def _resolved_local_path_from_string(value: str, config_dir: Path) -> Path | None:
    text = value.strip()
    if not text or "\n" in text or len(text) > 4096:
        return None
    raw_path = _raw_local_path_from_string(text)
    if raw_path is not None:
        return _resolve_local_path(raw_path, config_dir)
    if not _looks_like_plain_path(text):
        return None
    return _resolve_local_path(text, config_dir)


def _raw_local_path_from_string(value: str) -> str | None:
    for prefix in LOCAL_PLUGIN_SPEC_PREFIXES:
        if value.startswith(prefix):
            raw_path = value[len(prefix) :].strip()
            return raw_path or None
    return None


def _looks_like_plain_path(value: str) -> bool:
    if value.startswith(("/", ".", "~")):
        return True
    return len(value) >= 3 and value[1] == ":" and value[2] in {"/", "\\"}


def _resolve_local_path(raw_path: str, config_dir: Path) -> Path:
    path = Path(os.path.expanduser(raw_path))
    if not path.is_absolute():
        path = config_dir / path
    return path.resolve(strict=False)


def _builtin_plugin_name_from_path(path: Path, plugins_root: Path) -> str | None:
    plugins_root = plugins_root.resolve()
    try:
        relative = path.resolve(strict=False).relative_to(plugins_root)
    except ValueError:
        return None
    if not relative.parts:
        return None
    plugin_name = relative.parts[0]
    if (plugins_root / plugin_name / "agent_plugin.json").is_file():
        return plugin_name
    return None