from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .errors import SkillFrontmatterError, SkillYamlError
from .models import DiscoveredSkillFile, ParsedYamlFile, SkillDocument


def extract_frontmatter_and_body(contents: str) -> tuple[str, str]:
    lines = contents.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SkillFrontmatterError("missing YAML frontmatter delimited by ---")

    frontmatter_lines: list[str] = []
    closing_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = index
            break
        frontmatter_lines.append(line)

    if closing_index is None or not frontmatter_lines:
        raise SkillFrontmatterError("missing YAML frontmatter delimited by ---")

    body = "\n".join(lines[closing_index + 1 :])
    return "\n".join(frontmatter_lines), body


def parse_yaml_mapping(text: str, *, source: str) -> dict[str, Any]:
    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as exc:  # pragma: no cover - exercised indirectly
        raise SkillYamlError(f"invalid YAML in {source}: {exc}") from exc

    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise SkillYamlError(f"{source} must parse to a mapping")
    return dict(parsed)


def parse_skill_document(discovered: DiscoveredSkillFile) -> SkillDocument:
    contents = discovered.skill_path.read_text(encoding="utf-8")
    frontmatter_text, body = extract_frontmatter_and_body(contents)
    frontmatter = parse_yaml_mapping(frontmatter_text, source=str(discovered.skill_path))
    return SkillDocument(
        skill_path=discovered.skill_path,
        skill_dir=discovered.skill_dir,
        root=discovered.root,
        frontmatter=frontmatter,
        body=body,
    )


def load_optional_yaml_mapping(path: Path) -> ParsedYamlFile | None:
    if not path.is_file():
        return None
    contents = path.read_text(encoding="utf-8")
    return ParsedYamlFile(
        path=path.resolve(),
        data=parse_yaml_mapping(contents, source=str(path)),
    )