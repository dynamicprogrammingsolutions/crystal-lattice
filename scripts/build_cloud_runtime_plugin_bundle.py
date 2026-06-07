#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Iterable


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


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Stage preinstalled plugin metadata/resources for the cloud runtime "
            "and write a local-project requirements file for wheel building."
        )
    )
    parser.add_argument("--plugins-root", type=Path, required=True)
    parser.add_argument("--default-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--local-project-prefix",
        default=None,
        help=(
            "Prefix used in local-projects.txt. Defaults to the resolved "
            "--plugins-root path."
        ),
    )
    args = parser.parse_args()

    stage_cloud_runtime_plugin_bundle(
        plugins_root=args.plugins_root,
        default_config=args.default_config,
        output=args.output,
        local_project_prefix=args.local_project_prefix,
    )


def stage_cloud_runtime_plugin_bundle(
    *,
    plugins_root: Path,
    default_config: Path,
    output: Path,
    local_project_prefix: str | None = None,
) -> dict[str, object]:
    plugins_root = plugins_root.expanduser().resolve()
    default_config = default_config.expanduser().resolve()
    output = output.expanduser().resolve()

    selected_plugin_names = discover_selected_bundled_plugin_names(
        default_config, plugins_root
    )
    builtin_resource_paths = discover_builtin_plugin_resource_paths(
        default_config, plugins_root
    )
    local_project_names = resolve_local_project_names(
        selected_plugin_names, plugins_root
    )

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    bundled_plugins = output / "bundled_plugins"
    stage_preinstalled_plugins(
        bundled_plugins,
        plugins_root=plugins_root,
        selected_plugin_names=selected_plugin_names,
        builtin_resource_paths=builtin_resource_paths,
    )

    prefix = local_project_prefix or str(plugins_root)
    local_projects = [
        f"{prefix.rstrip('/')}/{name}"
        for name in sorted(local_project_names)
        if is_python_project(plugins_root / name)
    ]
    (output / "local-projects.txt").write_text(
        "".join(f"{project}\n" for project in local_projects),
        encoding="utf-8",
    )

    manifest = {
        "schema_version": 1,
        "preinstalled_plugins": sorted(selected_plugin_names),
        "local_projects": sorted(local_project_names),
        "local_project_requirements": local_projects,
        "resource_paths": [
            path.relative_to(plugins_root).as_posix()
            for path in sorted(builtin_resource_paths)
        ],
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def discover_selected_bundled_plugin_names(
    default_config: Path, plugins_root: Path
) -> set[str]:
    config = json.loads(default_config.read_text(encoding="utf-8"))
    names: set[str] = set()
    for value in iter_json_strings(config):
        if not value.startswith("path:${env:BUILTIN_PLUGINS}/"):
            continue
        relative = value.removeprefix("path:${env:BUILTIN_PLUGINS}/")
        name = relative.split("/", 1)[0]
        if (plugins_root / name / "agent_plugin.json").is_file():
            names.add(name)
    return names


def discover_builtin_plugin_resource_paths(
    default_config: Path, plugins_root: Path
) -> set[Path]:
    config = json.loads(default_config.read_text(encoding="utf-8"))
    paths: set[Path] = set()
    pattern = re.compile(r"\$\{env:BUILTIN_PLUGINS\}/([^}\" ]+)")
    plugins_root = plugins_root.resolve()
    for value in iter_json_strings(config):
        for match in pattern.finditer(value):
            relative = Path(match.group(1))
            source = (plugins_root / relative).resolve()
            try:
                source.relative_to(plugins_root)
            except ValueError:
                continue
            if source.is_file():
                paths.add(source)
    return paths


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


def iter_json_strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from iter_json_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_json_strings(child)


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


if __name__ == "__main__":
    main()
