from __future__ import annotations

from pathlib import Path
from typing import Any

from codex_tools.codex_skill_loader import (
    build_skill_injection_message,
    collect_explicit_skill_mentions,
    existing_injected_skill_keys,
    load_codex_skills,
    render_codex_skills_section,
)
from codex_tools.codex_skills_feature import CodexSkillsFeature
from skill_shared import DiscoveryOptions


class _FakeCore:
    def core_messages_to_native(
        self,
        core_messages: list[dict[str, Any]],
        config: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        _ = config, context
        return [dict(message) for message in core_messages]


def _write_skill(root: Path, name: str, description: str) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(
        (
            "---\n"
            f"name: {name}\n"
            f"description: {description}\n"
            "metadata:\n"
            "  short-description: short summary\n"
            "---\n\n"
            "# Body\n"
        ),
        encoding="utf-8",
    )
    return skill_path


def test_load_codex_skills_uses_directory_name_fallback_and_root_precedence(
    tmp_path: Path,
) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_path = _write_skill(first_root, "demo", "from first")
    second_path = _write_skill(second_root, "demo", "from second")
    first_path.write_text(
        "---\ndescription: from first\n---\n\n# Body\n", encoding="utf-8"
    )
    second_path.write_text(
        "---\ndescription: from second\n---\n\n# Body\n", encoding="utf-8"
    )

    skills = load_codex_skills(
        [first_root, second_root],
        options=DiscoveryOptions(),
    )

    assert len(skills) == 1
    assert skills[0].name == "demo"
    assert skills[0].description == "from first"


def test_render_codex_skills_section_uses_upstream_wording(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    _write_skill(root, "demo", "does things")
    skills = load_codex_skills([root], options=DiscoveryOptions())

    rendered = render_codex_skills_section(skills)

    assert rendered.startswith("## Skills\nA skill is a set of local instructions")
    assert "### Available skills" in rendered
    assert "- demo: does things (file:" in rendered
    assert "### How to use skills" in rendered
    assert "If the user names a skill" in rendered


def test_collect_explicit_skill_mentions_uses_dollar_syntax(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    _write_skill(root, "demo", "does things")
    _write_skill(root, "other", "other things")
    skills = load_codex_skills([root], options=DiscoveryOptions())

    selected = collect_explicit_skill_mentions(
        [{"role": "user", "content": "Please use $demo and then $demo again."}],
        skills,
    )

    assert [skill.name for skill in selected] == ["demo"]


def test_build_skill_injection_message_matches_upstream_shape(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    skill_path = _write_skill(root, "demo", "does things")
    skills = load_codex_skills([root], options=DiscoveryOptions())

    message = build_skill_injection_message(
        skills[0],
        contents=skill_path.read_text(encoding="utf-8"),
    )

    assert message["role"] == "user"
    assert message["content"].startswith("<skill>\n<name>demo</name>\n<path>")
    assert message["metadata"]["codex_skill_injected"] is True
    assert message["metadata"]["codex_skill_name"] == "demo"
    assert "</skill>" in message["content"]


def test_existing_injected_skill_keys_detects_metadata_and_payload(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    skill_path = _write_skill(root, "demo", "does things")
    messages = [
        {
            "role": "user",
            "content": "<skill>\n<name>demo</name>\n<path>"
            f"{skill_path.as_posix()}</path>\nbody\n</skill>",
        },
        {
            "role": "user",
            "content": "other",
            "metadata": {
                "codex_skill_injected": True,
                "codex_skill_name": "other",
                "codex_skill_path": "/tmp/other/SKILL.md",
            },
        },
    ]

    keys = existing_injected_skill_keys(messages)

    assert ("demo", skill_path.as_posix()) in keys
    assert ("other", "/tmp/other/SKILL.md") in keys


def test_codex_skills_feature_adds_section_and_request_scoped_injection(
    tmp_path: Path,
) -> None:
    root = tmp_path / "skills"
    _write_skill(root, "demo", "does things")
    feature = CodexSkillsFeature()

    native_messages = [{"role": "user", "content": "Use $demo for this task."}]
    state: dict[str, Any] = {
        "config": {
            "skills_enabled": True,
            "skills_roots": [str(root)],
            "working_directory": str(tmp_path),
        }
    }

    new_native, new_state = feature.initialize_request(
        native_messages,
        state,
        context={"core": _FakeCore(), "config": state["config"]},
    )

    assert len(new_native) == 2
    assert new_native[0]["content"] == "Use $demo for this task."
    assert new_native[1]["content"].startswith("<skill>\n<name>demo</name>\n<path>")
    assert "## Skills" in new_state["system_message_variables"]["CODEX_SKILLS_SECTION"]


def test_codex_skills_feature_updates_existing_request_override_messages(
    tmp_path: Path,
) -> None:
    root = tmp_path / "skills"
    _write_skill(root, "demo", "does things")
    feature = CodexSkillsFeature()

    native_messages = [
        {"role": "user", "content": "Use $demo please."}
    ]
    state: dict[str, Any] = {
        "request": {"messages": list(native_messages)},
        "config": {
            "skills_enabled": True,
            "skills_roots": [str(root)],
            "working_directory": str(tmp_path),
        }
    }

    new_native, new_state = feature.initialize_request(
        native_messages,
        state,
        context={"core": _FakeCore(), "config": state["config"]},
    )

    assert len(new_native) == 2
    request_messages = new_state["request"]["messages"]
    assert len(request_messages) == 2
    assert request_messages[1]["role"] == "user"
    assert request_messages[1]["content"].startswith("<skill>\n<name>demo</name>")


def test_codex_skills_feature_does_not_inject_duplicate_skill_messages(
    tmp_path: Path,
) -> None:
    root = tmp_path / "skills"
    skill_path = _write_skill(root, "demo", "does things")
    feature = CodexSkillsFeature()

    native_messages = [
        {"role": "user", "content": "Use $demo please."},
        {
            "role": "user",
            "content": "existing",
            "_metadata": {
                "codex_skill_injected": True,
                "codex_skill_name": "demo",
                "codex_skill_path": str(skill_path.resolve()),
            },
        },
    ]
    state: dict[str, Any] = {
        "config": {
            "skills_enabled": True,
            "skills_roots": [str(root)],
            "working_directory": str(tmp_path),
        }
    }

    new_native, new_state = feature.initialize_request(
        native_messages,
        state,
        context={"core": _FakeCore(), "config": state["config"]},
    )

    assert new_native == native_messages
    assert "request" not in new_state