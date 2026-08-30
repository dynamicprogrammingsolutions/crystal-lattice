#!/usr/bin/env python3
"""Assemble MkDocs input files from repo-local documentation sources."""

from __future__ import annotations

import json
import posixpath
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib


REPO_ROOT = Path(__file__).resolve().parents[2]
GITHUB_BLOB_ROOT = "https://github.com/dynamicprogrammingsolutions/crystal-lattice/blob/main"
IGNORED_DOCS_DIRS = {"reference", "plugin-development", "built-in-plugins"}
REGISTRY_VERSION = 1
REGISTRY_TOP_LEVEL_KEYS = {"version", "package"}
REGISTRY_ENTRY_KEYS = {
    "id",
    "title",
    "group",
    "summary",
    "source",
    "destination",
    "include_readme",
    "include_docs",
    "publish_development",
}
NON_PUBLIC_SOURCE_ROOTS = {"maintainer", "tasks", "task", "plan", "plans"}
PACKAGE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_RE = re.compile(r"(!?\[[^\]]*])\(([^)]+)\)")


class PreparationError(ValueError):
    """Raised when documentation preparation inputs are invalid."""


@dataclass(frozen=True)
class SitePaths:
    repo_root: Path
    docs_site_dir: Path
    docs_dir: Path
    source_dir: Path
    prepared_dir: Path
    registry_path: Path
    plugin_docs_dir: Path
    plugins_dir: Path
    default_config_path: Path

    @classmethod
    def from_repo_root(cls, repo_root: Path) -> SitePaths:
        root = repo_root.resolve()
        docs_site_dir = root / "docs_site"
        return cls(
            repo_root=root,
            docs_site_dir=docs_site_dir,
            docs_dir=root / "docs",
            source_dir=docs_site_dir / "source",
            prepared_dir=docs_site_dir / "prepared",
            registry_path=docs_site_dir / "packages.toml",
            plugin_docs_dir=root / "plugins" / "docs",
            plugins_dir=root / "plugins",
            default_config_path=(
                root
                / "application"
                / "python"
                / "agent_terminal_app"
                / "default_config"
                / "config.json"
            ),
        )


@dataclass(frozen=True)
class PackageEntry:
    id: str
    title: str
    group: str
    summary: str
    source: PurePosixPath
    destination: PurePosixPath
    include_readme: bool
    include_docs: bool
    publish_development: bool


@dataclass(frozen=True)
class PackageFile:
    source: Path
    output: PurePosixPath


@dataclass(frozen=True)
class PackagePlan:
    entry: PackageEntry
    files: tuple[PackageFile, ...]
    landing_source: Path


@dataclass(frozen=True)
class PluginPlan:
    id: str
    readme: Path
    docs_files: tuple[PackageFile, ...]
    has_authored_docs_index: bool


@dataclass(frozen=True)
class PreparationPlan:
    paths: SitePaths
    packages: tuple[PackagePlan, ...]
    plugins: tuple[PluginPlan, ...]
    source_outputs: Mapping[Path, PurePosixPath]


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _require_mapping(value: Any, *, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PreparationError(f"{context} must be a TOML table")
    return value


def _require_string(entry: Mapping[str, Any], field: str, *, context: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        raise PreparationError(f"{context}.{field} must be a non-empty string")
    return value


def _require_bool(entry: Mapping[str, Any], field: str, *, context: str) -> bool:
    value = entry.get(field)
    if type(value) is not bool:
        raise PreparationError(f"{context}.{field} must be a boolean")
    return value


def _validate_relative_path(raw: str, *, context: str) -> PurePosixPath:
    if "\\" in raw:
        raise PreparationError(f"{context} must use forward slashes: {raw!r}")
    path = PurePosixPath(raw)
    if (
        not path.parts
        or path.is_absolute()
        or raw != path.as_posix()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise PreparationError(
            f"{context} must be a normalized repository-relative path "
            f"without traversal: {raw!r}"
        )
    return path


def load_package_registry(paths: SitePaths) -> tuple[PackageEntry, ...]:
    try:
        with paths.registry_path.open("rb") as registry_file:
            raw_registry = tomllib.load(registry_file)
    except FileNotFoundError as exc:
        raise PreparationError(
            f"package registry does not exist: {paths.registry_path}"
        ) from exc
    except tomllib.TOMLDecodeError as exc:
        raise PreparationError(
            f"invalid package registry {paths.registry_path}: {exc}"
        ) from exc

    registry = _require_mapping(raw_registry, context="registry")
    unknown_top_level = sorted(set(registry) - REGISTRY_TOP_LEVEL_KEYS)
    if unknown_top_level:
        raise PreparationError(
            f"registry contains unknown key(s): {', '.join(unknown_top_level)}"
        )
    if registry.get("version") != REGISTRY_VERSION:
        raise PreparationError(
            f"registry.version must be {REGISTRY_VERSION}, "
            f"got {registry.get('version')!r}"
        )

    raw_packages = registry.get("package")
    if not isinstance(raw_packages, list) or not raw_packages:
        raise PreparationError(
            "registry.package must contain at least one [[package]] entry"
        )

    packages: list[PackageEntry] = []
    for index, raw_entry in enumerate(raw_packages, start=1):
        context = f"package[{index}]"
        entry = _require_mapping(raw_entry, context=context)
        unknown_keys = sorted(set(entry) - REGISTRY_ENTRY_KEYS)
        missing_keys = sorted(REGISTRY_ENTRY_KEYS - set(entry))
        if unknown_keys:
            raise PreparationError(
                f"{context} contains unknown key(s): {', '.join(unknown_keys)}"
            )
        if missing_keys:
            raise PreparationError(
                f"{context} is missing required key(s): {', '.join(missing_keys)}"
            )

        package_id = _require_string(entry, "id", context=context)
        if not PACKAGE_ID_RE.fullmatch(package_id):
            raise PreparationError(
                f"{context}.id must be lowercase URL-safe kebab-case: "
                f"{package_id!r}"
            )
        title = _require_string(entry, "title", context=context).strip()
        group = _require_string(entry, "group", context=context).strip()
        summary = _require_string(entry, "summary", context=context).strip()
        source = _validate_relative_path(
            _require_string(entry, "source", context=context),
            context=f"{context}.source",
        )
        destination = _validate_relative_path(
            _require_string(entry, "destination", context=context),
            context=f"{context}.destination",
        )
        include_readme = _require_bool(entry, "include_readme", context=context)
        include_docs = _require_bool(entry, "include_docs", context=context)
        publish_development = _require_bool(
            entry, "publish_development", context=context
        )
        if not include_readme and not include_docs:
            raise PreparationError(
                f"{context} must enable include_readme or include_docs"
            )
        if publish_development and not include_docs:
            raise PreparationError(
                f"{context}.publish_development cannot be true when "
                "include_docs is false"
            )

        packages.append(
            PackageEntry(
                id=package_id,
                title=title,
                group=group,
                summary=summary,
                source=source,
                destination=destination,
                include_readme=include_readme,
                include_docs=include_docs,
                publish_development=publish_development,
            )
        )

    _validate_registry_uniqueness(packages)
    for index, package in enumerate(packages, start=1):
        expected_destination = PurePosixPath("packages") / package.id
        if package.destination != expected_destination:
            raise PreparationError(
                f"package[{index}].destination must be "
                f"{expected_destination.as_posix()!r} for package id "
                f"{package.id!r}, got {package.destination.as_posix()!r}"
            )
    return tuple(packages)


def _validate_registry_uniqueness(packages: Iterable[PackageEntry]) -> None:
    seen_ids: dict[str, PackageEntry] = {}
    seen_sources: dict[PurePosixPath, PackageEntry] = {}
    seen_destinations: dict[PurePosixPath, PackageEntry] = {}
    package_list = list(packages)

    for entry in package_list:
        for value, seen, field in (
            (entry.id, seen_ids, "id"),
            (entry.source, seen_sources, "source"),
            (entry.destination, seen_destinations, "destination"),
        ):
            previous = seen.get(value)
            if previous is not None:
                raise PreparationError(
                    f"duplicate package {field} {str(value)!r}: "
                    f"{previous.id!r} and {entry.id!r}"
                )
            seen[value] = entry

    for index, left in enumerate(package_list):
        for right in package_list[index + 1 :]:
            if (
                left.destination in right.destination.parents
                or right.destination in left.destination.parents
            ):
                raise PreparationError(
                    "nested package destinations collide: "
                    f"{left.destination.as_posix()!r} and "
                    f"{right.destination.as_posix()!r}"
                )


def _iter_tree_files(
    source: Path,
    *,
    ignore_top_level_dirs: set[str] | None = None,
    exclude_agents: bool = False,
    exclude_development: bool = False,
) -> Iterable[tuple[Path, PurePosixPath]]:
    ignored = ignore_top_level_dirs or set()
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = PurePosixPath(path.relative_to(source).as_posix())
        if relative.parts and relative.parts[0] in ignored:
            continue
        if exclude_agents and path.name == "AGENTS.md":
            continue
        if (
            exclude_development
            and relative.parts
            and relative.parts[0] == "development"
        ):
            continue
        yield path, relative


def _validate_source_path(
    path: Path, *, package_root: Path, context: str
) -> None:
    resolved = path.resolve()
    if not _is_relative_to(resolved, package_root.resolve()):
        raise PreparationError(
            f"{context} resolves outside its package root: {path}"
        )


def _fixed_source_outputs(
    paths: SitePaths,
) -> tuple[
    dict[Path, PurePosixPath],
    set[PurePosixPath],
    tuple[PluginPlan, ...],
]:
    source_outputs: dict[Path, PurePosixPath] = {}
    output_paths: set[PurePosixPath] = set()
    plugin_plans: list[PluginPlan] = []

    for source, relative in _iter_tree_files(
        paths.docs_dir,
        ignore_top_level_dirs=IGNORED_DOCS_DIRS,
    ):
        source_outputs[source.resolve()] = relative
        output_paths.add(relative)

    for source, relative in _iter_tree_files(paths.source_dir):
        source_outputs[source.resolve()] = relative
        output_paths.add(relative)

    for source in sorted(paths.plugin_docs_dir.rglob("*.md")):
        if source.name == "AGENTS.md":
            continue
        relative = PurePosixPath(
            source.relative_to(paths.plugin_docs_dir).as_posix()
        )
        output = PurePosixPath("plugin-development") / relative
        source_outputs[source.resolve()] = output
        output_paths.add(output)

    output_paths.add(PurePosixPath("built-in-plugins/index.md"))
    for readme in discover_plugin_readmes(paths):
        plugin_id = readme.parent.name
        output = (
            PurePosixPath("built-in-plugins")
            / plugin_id
            / "index.md"
        )
        source_outputs[readme.resolve()] = output
        output_paths.add(output)
        docs_files: list[PackageFile] = []
        docs_dir = readme.parent / "docs"
        has_authored_docs_index = False
        if docs_dir.is_dir():
            for source, relative in _iter_tree_files(
                docs_dir,
                exclude_agents=True,
            ):
                _validate_source_path(
                    source,
                    package_root=readme.parent,
                    context=f"plugin {plugin_id!r} docs source",
                )
                docs_output = (
                    PurePosixPath("built-in-plugins")
                    / plugin_id
                    / "docs"
                    / relative
                )
                if docs_output in output_paths:
                    raise PreparationError(
                        f"plugin {plugin_id!r} docs output collides with an "
                        f"existing prepared path: {docs_output.as_posix()!r}"
                    )
                output_paths.add(docs_output)
                source_outputs[source.resolve()] = docs_output
                docs_files.append(PackageFile(source=source, output=docs_output))
                if relative == PurePosixPath("index.md"):
                    has_authored_docs_index = True
            if docs_files and not has_authored_docs_index:
                generated_index = (
                    PurePosixPath("built-in-plugins")
                    / plugin_id
                    / "docs"
                    / "index.md"
                )
                if generated_index in output_paths:
                    raise PreparationError(
                        f"plugin {plugin_id!r} generated docs index collides "
                        f"with {generated_index.as_posix()!r}"
                    )
                output_paths.add(generated_index)
        plugin_plans.append(
            PluginPlan(
                id=plugin_id,
                readme=readme,
                docs_files=tuple(docs_files),
                has_authored_docs_index=has_authored_docs_index,
            )
        )

    default_config_output = PurePosixPath("reference/default-config.md")
    source_outputs[paths.default_config_path.resolve()] = default_config_output
    output_paths.add(default_config_output)
    output_paths.add(PurePosixPath("packages/index.md"))
    return source_outputs, output_paths, tuple(plugin_plans)


def create_preparation_plan(paths: SitePaths) -> PreparationPlan:
    entries = load_package_registry(paths)
    source_outputs, occupied_outputs, plugin_plans = _fixed_source_outputs(paths)
    package_plans: list[PackagePlan] = []

    for entry in entries:
        package_root = (paths.repo_root / entry.source).resolve()
        if entry.source.parts[0] in NON_PUBLIC_SOURCE_ROOTS or (
            entry.source.parts[0] == "docs_site"
            and len(entry.source.parts) > 1
            and entry.source.parts[1] in {"prepared", "dist"}
        ):
            raise PreparationError(
                f"package {entry.id!r} uses a non-public source root: "
                f"{entry.source.as_posix()!r}"
            )
        if not _is_relative_to(package_root, paths.repo_root):
            raise PreparationError(
                f"package {entry.id!r} source resolves outside the repository: "
                f"{entry.source.as_posix()!r}"
            )
        if not package_root.is_dir():
            raise PreparationError(
                f"package {entry.id!r} source directory does not exist: "
                f"{entry.source.as_posix()!r}"
            )

        readme = package_root / "README.md"
        docs_dir = package_root / "docs"
        if entry.include_readme and not readme.is_file():
            raise PreparationError(
                f"package {entry.id!r} enables include_readme but README.md "
                f"is missing: {readme}"
            )
        if entry.include_docs and not docs_dir.is_dir():
            raise PreparationError(
                f"package {entry.id!r} enables include_docs but docs/ "
                f"is missing: {docs_dir}"
            )

        landing_source: Path | None = None
        files: list[PackageFile] = []
        if entry.include_docs:
            for source, relative in _iter_tree_files(
                docs_dir,
                exclude_agents=True,
                exclude_development=not entry.publish_development,
            ):
                _validate_source_path(
                    source,
                    package_root=package_root,
                    context=f"package {entry.id!r} docs source",
                )
                output = entry.destination / relative
                files.append(PackageFile(source=source, output=output))
                if relative == PurePosixPath("index.md"):
                    landing_source = source

        if landing_source is None and entry.include_readme:
            _validate_source_path(
                readme,
                package_root=package_root,
                context=f"package {entry.id!r} README source",
            )
            landing_source = readme
            files.append(
                PackageFile(
                    source=readme,
                    output=entry.destination / "index.md",
                )
            )
        if landing_source is None:
            raise PreparationError(
                f"package {entry.id!r} cannot produce a landing page: "
                "docs/index.md is missing and README fallback is disabled"
            )

        package_outputs: set[PurePosixPath] = set()
        for package_file in files:
            output = package_file.output
            if output in package_outputs:
                raise PreparationError(
                    f"package {entry.id!r} maps more than one source to "
                    f"{output.as_posix()!r}"
                )
            if output in occupied_outputs:
                raise PreparationError(
                    f"package {entry.id!r} output collides with an existing "
                    f"prepared path: {output.as_posix()!r}"
                )
            package_outputs.add(output)
            occupied_outputs.add(output)
            source_outputs[package_file.source.resolve()] = output

        package_plans.append(
            PackagePlan(
                entry=entry,
                files=tuple(files),
                landing_source=landing_source,
            )
        )

    return PreparationPlan(
        paths=paths,
        packages=tuple(package_plans),
        plugins=plugin_plans,
        source_outputs=source_outputs,
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def strip_markdown_title(content: str) -> str:
    lines = content.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).lstrip()
    return content.lstrip()


def github_link(path: str) -> str:
    return f"{GITHUB_BLOB_ROOT}/{path}"


def split_link_target(raw_target: str) -> tuple[str, str]:
    target = raw_target.strip()
    if not target:
        return raw_target, ""
    if target.startswith("<") and target.endswith(">"):
        return target, ""
    if " " not in target:
        return target, ""
    first, rest = target.split(" ", 1)
    return first, f" {rest}"


def is_external_or_absolute(target: str) -> bool:
    lower = target.lower()
    return (
        lower.startswith("http://")
        or lower.startswith("https://")
        or lower.startswith("mailto:")
        or lower.startswith("tel:")
        or lower.startswith("#")
        or target.startswith("/")
    )


def _source_output_aliases(
    source_outputs: Mapping[Path, PurePosixPath],
) -> dict[Path, PurePosixPath]:
    aliases = dict(source_outputs)
    for source, output in source_outputs.items():
        if source.name.lower() == "index.md":
            aliases.setdefault(source.parent, output)
    return aliases


def _resolve_repo_link_target(
    target: str,
    *,
    source_path: Path,
    repo_root: Path,
    source_outputs: Mapping[Path, PurePosixPath],
) -> Path | None:
    relative_candidate = (source_path.parent / target).resolve()
    repo_candidate = (repo_root / target).resolve()

    if _is_relative_to(relative_candidate, repo_root) and (
        relative_candidate.exists() or relative_candidate in source_outputs
    ):
        return relative_candidate
    if _is_relative_to(repo_candidate, repo_root) and (
        repo_candidate.exists() or repo_candidate in source_outputs
    ):
        return repo_candidate
    if _is_relative_to(relative_candidate, repo_root):
        return relative_candidate
    if _is_relative_to(repo_candidate, repo_root):
        return repo_candidate
    return None


def normalize_markdown_links(
    content: str,
    *,
    source_path: Path,
    output_path: PurePosixPath,
    repo_root: Path,
    source_outputs: Mapping[Path, PurePosixPath],
) -> str:
    aliases = _source_output_aliases(source_outputs)

    def replace(match: re.Match[str]) -> str:
        label = match.group(1)
        raw_target = match.group(2)
        target, suffix = split_link_target(raw_target)
        if (
            is_external_or_absolute(target)
            or (target.startswith("<") and target.endswith(">"))
        ):
            return match.group(0)

        target_path, separator, fragment = target.partition("#")
        resolved = _resolve_repo_link_target(
            target_path,
            source_path=source_path,
            repo_root=repo_root,
            source_outputs=aliases,
        )
        if resolved is None:
            return match.group(0)

        published_output = aliases.get(resolved)
        if published_output is not None:
            start = output_path.parent.as_posix() or "."
            link = posixpath.relpath(
                published_output.as_posix(),
                start=start,
            )
        else:
            repo_relative = resolved.relative_to(repo_root).as_posix()
            link = github_link(repo_relative)
        if separator:
            link = f"{link}#{fragment}"
        return f"{label}({link}{suffix})"

    return MARKDOWN_LINK_RE.sub(replace, content)


def normalize_plugin_docs_links(content: str) -> str:
    replacements = (
        ("#concepts--vocabulary", "#concepts-vocabulary"),
        ("#quickstart--development-workflow", "#quickstart-development-workflow"),
        (
            "#deep-dive-streaming-patterns--recipes",
            "#deep-dive-streaming-patterns-recipes",
        ),
        (
            "#deep-dive-interop-extensionsfeatures-tools",
            "#deep-dive-interop-extensionsfeaturestools",
        ),
    )
    for old, new in replacements:
        content = content.replace(old, new)
    return content


def copy_tree_contents(
    source: Path,
    destination: Path,
    *,
    ignore_dirs: set[str] | None = None,
) -> None:
    ignored = ignore_dirs or set()
    for child in sorted(source.iterdir()):
        if child.name in ignored:
            continue
        target = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(child, target)


def assemble_base_docs(paths: SitePaths, output_root: Path) -> None:
    copy_tree_contents(
        paths.docs_dir,
        output_root,
        ignore_dirs=IGNORED_DOCS_DIRS,
    )
    copy_tree_contents(paths.source_dir, output_root)


def assemble_package_docs(plan: PreparationPlan, output_root: Path) -> None:
    for package in plan.packages:
        for package_file in package.files:
            target = output_root / package_file.output
            target.parent.mkdir(parents=True, exist_ok=True)
            if package_file.source.suffix.lower() == ".md":
                content = package_file.source.read_text(encoding="utf-8")
                content = normalize_markdown_links(
                    content,
                    source_path=package_file.source,
                    output_path=package_file.output,
                    repo_root=plan.paths.repo_root,
                    source_outputs=plan.source_outputs,
                )
                write_text(target, content)
            else:
                shutil.copy2(package_file.source, target)

    index_lines = [
        "# Package Documentation",
        "",
        "Choose the package that owns the SDK, application, component, or "
        "service you want to use.",
        "",
    ]
    grouped_packages: dict[str, list[PackagePlan]] = {}
    for package in plan.packages:
        grouped_packages.setdefault(package.entry.group, []).append(package)

    for group, packages in grouped_packages.items():
        index_lines.extend([f"## {group}", ""])
        for package in packages:
            index_lines.append(
                f"- **[{package.entry.title}]({package.entry.id}/index.md)** — "
                f"{package.entry.summary}"
            )
        index_lines.append("")
    write_text(output_root / "packages" / "index.md", "\n".join(index_lines))


def copy_plugin_development_docs(
    paths: SitePaths, output_root: Path
) -> None:
    destination = output_root / "plugin-development"
    destination.mkdir(parents=True, exist_ok=True)
    for source in sorted(paths.plugin_docs_dir.rglob("*.md")):
        if source.name == "AGENTS.md":
            continue
        relative = source.relative_to(paths.plugin_docs_dir)
        content = normalize_plugin_docs_links(
            source.read_text(encoding="utf-8")
        )
        write_text(destination / relative, content)


def discover_plugin_readmes(paths: SitePaths) -> list[Path]:
    return sorted(
        paths.plugins_dir.glob("*/README.md"),
        key=lambda path: path.parent.name,
    )


def generate_built_in_plugin_docs(
    plan: PreparationPlan, output_root: Path
) -> None:
    destination = output_root / "built-in-plugins"
    destination.mkdir(parents=True, exist_ok=True)
    index_lines = [
        "# Built-In Plugins",
        "",
        "Generated from `plugins/*/README.md`.",
        "",
    ]

    for plugin in plan.plugins:
        readme = plugin.readme
        plugin_name = plugin.id
        output_path = (
            PurePosixPath("built-in-plugins") / plugin_name / "index.md"
        )
        content = readme.read_text(encoding="utf-8")
        content = normalize_markdown_links(
            content,
            source_path=readme,
            output_path=output_path,
            repo_root=plan.paths.repo_root,
            source_outputs=plan.source_outputs,
        )
        body = strip_markdown_title(content)
        page = "\n".join(
            [
                f"# {plugin_name}",
                "",
                f"Generated from `plugins/{plugin_name}/README.md`.",
                "",
                (
                    "Package documentation: "
                    "[browse guides and development docs](docs/index.md)."
                    if plugin.docs_files
                    else ""
                ),
                "",
                body.rstrip(),
                "",
            ]
        )
        write_text(output_root / output_path, page)
        index_lines.append(f"- [{plugin_name}]({plugin_name}/index.md)")
        _copy_plugin_package_docs(plan, plugin, output_root)

    index_lines.append("")
    write_text(destination / "index.md", "\n".join(index_lines))


def _markdown_page_title(source: Path) -> str:
    for line in source.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return source.stem.replace("-", " ").replace("_", " ").title()


def _copy_plugin_package_docs(
    plan: PreparationPlan,
    plugin: PluginPlan,
    output_root: Path,
) -> None:
    if not plugin.docs_files:
        return

    for docs_file in plugin.docs_files:
        target = output_root / docs_file.output
        target.parent.mkdir(parents=True, exist_ok=True)
        if docs_file.source.suffix.lower() == ".md":
            content = normalize_markdown_links(
                docs_file.source.read_text(encoding="utf-8"),
                source_path=docs_file.source,
                output_path=docs_file.output,
                repo_root=plan.paths.repo_root,
                source_outputs=plan.source_outputs,
            )
            write_text(target, content)
        else:
            shutil.copy2(docs_file.source, target)

    if plugin.has_authored_docs_index:
        return

    docs_root = plugin.readme.parent / "docs"
    index_lines = [
        f"# {plugin.id} documentation",
        "",
        f"Generated from `plugins/{plugin.id}/docs/`.",
        "",
    ]
    for docs_file in plugin.docs_files:
        if docs_file.source.suffix.lower() != ".md":
            continue
        relative = docs_file.source.relative_to(docs_root).as_posix()
        index_lines.append(
            f"- [{_markdown_page_title(docs_file.source)}]({relative})"
        )
    index_lines.append("")
    write_text(
        output_root
        / "built-in-plugins"
        / plugin.id
        / "docs"
        / "index.md",
        "\n".join(index_lines),
    )


def generate_default_config_reference(
    paths: SitePaths, output_root: Path
) -> None:
    raw_config = paths.default_config_path.read_text(encoding="utf-8")
    parsed_config = json.loads(raw_config)
    formatted_config = json.dumps(parsed_config, indent=2, ensure_ascii=False)
    content = "\n".join(
        [
            "# Default Configuration",
            "",
            "Generated from "
            "`application/python/agent_terminal_app/default_config/config.json`.",
            "",
            "```json",
            formatted_config,
            "```",
            "",
        ]
    )
    write_text(
        output_root / "reference" / "default-config.md",
        content,
    )


def assemble_prepared_tree(
    plan: PreparationPlan, output_root: Path
) -> None:
    assemble_base_docs(plan.paths, output_root)
    assemble_package_docs(plan, output_root)
    copy_plugin_development_docs(plan.paths, output_root)
    generate_built_in_plugin_docs(plan, output_root)
    generate_default_config_reference(plan.paths, output_root)


def replace_prepared_tree(
    staging_dir: Path, prepared_dir: Path
) -> None:
    backup_dir: Path | None = None
    if prepared_dir.exists():
        backup_dir = Path(
            tempfile.mkdtemp(
                prefix=".prepared-backup-",
                dir=prepared_dir.parent,
            )
        )
        backup_dir.rmdir()
        prepared_dir.rename(backup_dir)

    try:
        staging_dir.rename(prepared_dir)
    except BaseException:
        if (
            backup_dir is not None
            and backup_dir.exists()
            and not prepared_dir.exists()
        ):
            backup_dir.rename(prepared_dir)
        raise
    else:
        if backup_dir is not None:
            shutil.rmtree(backup_dir)


def prepare_docs_site(repo_root: Path = REPO_ROOT) -> None:
    paths = SitePaths.from_repo_root(repo_root)
    plan = create_preparation_plan(paths)
    paths.docs_site_dir.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(
            prefix=".prepared-staging-",
            dir=paths.docs_site_dir,
        )
    )
    try:
        assemble_prepared_tree(plan, staging_dir)
        replace_prepared_tree(staging_dir, paths.prepared_dir)
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)


def main() -> None:
    prepare_docs_site()


if __name__ == "__main__":
    main()