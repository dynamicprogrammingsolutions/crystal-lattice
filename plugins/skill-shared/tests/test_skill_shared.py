from __future__ import annotations

from pathlib import Path

import pytest

from skill_shared import (
    DiscoveryOptions,
    discover_skill_files,
    load_optional_yaml_mapping,
    parse_skill_document,
)
from skill_shared.errors import SkillFrontmatterError, SkillYamlError


def test_discover_skill_files_preserves_root_order_and_skips_hidden(tmp_path: Path) -> None:
    root_one = tmp_path / "one"
    root_two = tmp_path / "two"
    (root_one / "alpha").mkdir(parents=True)
    (root_two / ".hidden").mkdir(parents=True)
    (root_two / "beta").mkdir(parents=True)
    (root_one / "alpha" / "SKILL.md").write_text(
        "---\ndescription: alpha\n---\n", encoding="utf-8"
    )
    (root_two / ".hidden" / "SKILL.md").write_text(
        "---\ndescription: hidden\n---\n", encoding="utf-8"
    )
    (root_two / "beta" / "SKILL.md").write_text(
        "---\ndescription: beta\n---\n", encoding="utf-8"
    )

    discovered = discover_skill_files(
        [root_two, root_one],
        DiscoveryOptions(),
    )

    assert [item.skill_dir.name for item in discovered] == ["beta", "alpha"]


def test_discover_skill_files_rejects_symlink_escape_even_when_following(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "escaped").mkdir()
    (outside / "escaped" / "SKILL.md").write_text(
        "---\ndescription: escaped\n---\n", encoding="utf-8"
    )
    root.mkdir()
    (root / "link").symlink_to(outside / "escaped", target_is_directory=True)

    discovered = discover_skill_files([root], DiscoveryOptions(follow_symlinks=True))

    assert discovered == []


def test_parse_skill_document_reads_frontmatter_and_body(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    skill_dir = root / "demo"
    skill_dir.mkdir(parents=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(
        "---\nname: demo\ndescription: useful\nmetadata:\n  short-description: short\n---\n\n# Body\n",
        encoding="utf-8",
    )

    discovered = discover_skill_files([root], DiscoveryOptions())
    document = parse_skill_document(discovered[0])

    assert document.frontmatter["name"] == "demo"
    assert document.frontmatter["metadata"]["short-description"] == "short"
    assert "# Body" in document.body


def test_parse_skill_document_requires_frontmatter(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    skill_dir = root / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Body\n", encoding="utf-8")

    discovered = discover_skill_files([root], DiscoveryOptions())
    with pytest.raises(SkillFrontmatterError):
        parse_skill_document(discovered[0])


def test_load_optional_yaml_mapping_accepts_json_compatible_yaml(tmp_path: Path) -> None:
    path = tmp_path / "openai.yaml"
    path.write_text('{"interface": {"display_name": "Demo"}}\n', encoding="utf-8")

    loaded = load_optional_yaml_mapping(path)

    assert loaded is not None
    assert loaded.data["interface"]["display_name"] == "Demo"


def test_load_optional_yaml_mapping_requires_mapping(tmp_path: Path) -> None:
    path = tmp_path / "openai.yaml"
    path.write_text("- nope\n", encoding="utf-8")

    with pytest.raises(SkillYamlError):
        load_optional_yaml_mapping(path)