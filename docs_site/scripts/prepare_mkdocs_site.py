#!/usr/bin/env python3
"""Assemble MkDocs input files from repo-local documentation sources."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_SITE_DIR = REPO_ROOT / "docs_site"
DOCS_DIR = REPO_ROOT / "docs"
MKDOCS_SOURCE_DIR = DOCS_SITE_DIR / "source"
PREPARED_DIR = DOCS_SITE_DIR / "prepared"
PLUGIN_DOCS_DIR = REPO_ROOT / "plugins" / "docs"
PLUGIN_DEVELOPMENT_DIR = PREPARED_DIR / "plugin-development"
BUILT_IN_PLUGINS_DIR = PREPARED_DIR / "built-in-plugins"
DEFAULT_CONFIG_PATH = (
    REPO_ROOT / "application" / "python" / "agent_terminal_app" / "default_config" / "config.json"
)
DEFAULT_CONFIG_DOC_PATH = PREPARED_DIR / "reference" / "default-config.md"
GITHUB_BLOB_ROOT = "https://github.com/dynamicprogrammingsolutions/crystal-lattice/blob/main"
IGNORED_DOCS_DIRS = {"reference", "plugin-development", "built-in-plugins"}

MARKDOWN_LINK_RE = re.compile(r"(!?\[[^\]]*])\(([^)]+)\)")
REPO_ROOT_PREFIXES = (
    "application/",
    "bridge-elixir/",
    "cloud-orchestrator/",
    "core/",
    "desktop/",
    "docs/",
    "evaluations/",
    "landing_page/",
    "mobile/",
    "packages/",
    "plugins/",
    "scripts/",
)


def remove_and_recreate(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


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


def normalize_readme_links(content: str, source_path: Path) -> str:
    source_rel_parent = source_path.parent.relative_to(REPO_ROOT)

    def replace(match: re.Match[str]) -> str:
        label = match.group(1)
        raw_target = match.group(2)
        target, suffix = split_link_target(raw_target)
        if is_external_or_absolute(target):
            return match.group(0)

        if target == "application/python/agent_terminal_app/default_config/config.json":
            return f"{label}(../../reference/default-config.md{suffix})"

        target_path, sep, fragment = target.partition("#")
        if target_path.startswith(REPO_ROOT_PREFIXES):
            repo_rel = target_path
        else:
            repo_rel = (source_rel_parent / target_path).as_posix()

        normalized = str(Path(repo_rel))
        normalized = normalized.replace("\\", "/")
        link = github_link(normalized)
        if sep:
            link = f"{link}#{fragment}"
        return f"{label}({link}{suffix})"

    return MARKDOWN_LINK_RE.sub(replace, content)


def normalize_plugin_docs_links(content: str) -> str:
    replacements = (
        ("../../docs/plugins/development.md", "../plugins/development.md"),
        ("#concepts--vocabulary", "#concepts-vocabulary"),
        ("#quickstart--development-workflow", "#quickstart-development-workflow"),
        ("#deep-dive-streaming-patterns--recipes", "#deep-dive-streaming-patterns-recipes"),
        ("#deep-dive-interop-extensionsfeatures-tools", "#deep-dive-interop-extensionsfeaturestools"),
    )
    for old, new in replacements:
        content = content.replace(old, new)
    return content


def copy_tree_contents(source: Path, destination: Path, *, ignore_dirs: set[str] | None = None) -> None:
    ignore_dirs = ignore_dirs or set()
    for child in sorted(source.iterdir()):
        if child.name in ignore_dirs:
            continue
        target = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(child, target)


def assemble_base_docs() -> None:
    remove_and_recreate(PREPARED_DIR)
    copy_tree_contents(DOCS_DIR, PREPARED_DIR, ignore_dirs=IGNORED_DOCS_DIRS)
    copy_tree_contents(MKDOCS_SOURCE_DIR, PREPARED_DIR)


def copy_plugin_development_docs() -> None:
    remove_and_recreate(PLUGIN_DEVELOPMENT_DIR)
    for source in sorted(PLUGIN_DOCS_DIR.glob("*.md")):
        if source.name == "AGENTS.md":
            continue
        content = normalize_plugin_docs_links(source.read_text(encoding="utf-8"))
        write_text(PLUGIN_DEVELOPMENT_DIR / source.name, content)


def discover_plugin_readmes() -> list[Path]:
    return sorted((REPO_ROOT / "plugins").glob("*/README.md"), key=lambda path: path.parent.name)


def generate_built_in_plugin_docs() -> None:
    remove_and_recreate(BUILT_IN_PLUGINS_DIR)
    readmes = discover_plugin_readmes()
    index_lines = [
        "# Built-In Plugins",
        "",
        "Generated from `plugins/*/README.md`.",
        "",
    ]

    for readme in readmes:
        plugin_name = readme.parent.name
        content = readme.read_text(encoding="utf-8")
        content = normalize_readme_links(content, readme)
        body = strip_markdown_title(content)
        page = "\n".join(
            [
                f"# {plugin_name}",
                "",
                f"Generated from `plugins/{plugin_name}/README.md`.",
                "",
                body.rstrip(),
                "",
            ]
        )
        write_text(BUILT_IN_PLUGINS_DIR / plugin_name / "index.md", page)
        index_lines.append(f"- [{plugin_name}]({plugin_name}/index.md)")

    index_lines.append("")
    write_text(BUILT_IN_PLUGINS_DIR / "index.md", "\n".join(index_lines))


def generate_default_config_reference() -> None:
    raw_config = DEFAULT_CONFIG_PATH.read_text(encoding="utf-8")
    parsed_config = json.loads(raw_config)
    formatted_config = json.dumps(parsed_config, indent=2, ensure_ascii=False)
    content = "\n".join(
        [
            "# Default Configuration",
            "",
            "Generated from `application/python/agent_terminal_app/default_config/config.json`.",
            "",
            "```json",
            formatted_config,
            "```",
            "",
        ]
    )
    write_text(DEFAULT_CONFIG_DOC_PATH, content)


def main() -> None:
    assemble_base_docs()
    copy_plugin_development_docs()
    generate_built_in_plugin_docs()
    generate_default_config_reference()


if __name__ == "__main__":
    main()