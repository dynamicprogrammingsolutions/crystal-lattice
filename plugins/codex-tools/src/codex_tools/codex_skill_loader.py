from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Iterable, Sequence

from skill_shared import (
    DiscoveryOptions,
    SkillDocument,
    discover_skill_files,
    load_optional_yaml_mapping,
    parse_skill_document,
    sanitize_single_line,
    validate_max_len,
)


_MENTION_RE = re.compile(r"\$([A-Za-z0-9:_-]+)")
_SKILL_MESSAGE_NAME_RE = re.compile(r"<name>([^<]+)</name>")
_SKILL_MESSAGE_PATH_RE = re.compile(r"<path>([^<]+)</path>")
_NAME_MAX_LEN = 64
_DESCRIPTION_MAX_LEN = 1024
_SHORT_DESCRIPTION_MAX_LEN = 1024
_SIDECAR_RELATIVE_PATH = Path("agents/openai.yaml")

_AVAILABLE_SKILLS_INTRO = (
    "## Skills\n"
    "A skill is a set of local instructions to follow that is stored in a `SKILL.md` file. "
    "Below is the list of skills that can be used. Each entry includes a name, description, "
    "and file path so you can open the source for full instructions when using a specific skill.\n"
    "### Available skills"
)

_AVAILABLE_SKILLS_USAGE = """### How to use skills
- Discovery: The list above is the skills available in this session (name + description + file path). Skill bodies live on disk at the listed paths.
- Trigger rules: If the user names a skill (with `$SkillName` or plain text) OR the task clearly matches a skill's description shown above, you must use that skill for that turn. Multiple mentions mean use them all. Do not carry skills across turns unless re-mentioned.
- Missing/blocked: If a named skill isn't in the list or the path can't be read, say so briefly and continue with the best fallback.
- How to use a skill (progressive disclosure):
  1) After deciding to use a skill, open its `SKILL.md`. Read only enough to follow the workflow.
  2) When `SKILL.md` references relative paths (e.g., `scripts/foo.py`), resolve them relative to the skill directory listed above first, and only consider other paths if needed.
  3) If `SKILL.md` points to extra folders such as `references/`, load only the specific files needed for the request; don't bulk-load everything.
  4) If `scripts/` exist, prefer running or patching them instead of retyping large code blocks.
  5) If `assets/` or templates exist, reuse them instead of recreating from scratch.
- Coordination and sequencing:
  - If multiple skills apply, choose the minimal set that covers the request and state the order you'll use them.
  - Announce which skill(s) you're using and why (one short line). If you skip an obvious skill, say why.
- Context hygiene:
  - Keep context small: summarize long sections instead of pasting them; only load extra files when needed.
  - Avoid deep reference-chasing: prefer opening only files directly linked from `SKILL.md` unless you're blocked.
  - When variants exist (frameworks, providers, domains), pick only the relevant reference file(s) and note that choice.
- Safety and fallback: If a skill can't be applied cleanly (missing files, unclear instructions), state the issue, pick the next-best approach, and continue."""


@dataclass(frozen=True)
class CodexSkillMetadata:
    name: str
    description: str
    short_description: str | None
    path_to_skills_md: Path
    root: Path
    document: SkillDocument


def load_codex_skills(
    roots: Sequence[Path],
    *,
    options: DiscoveryOptions,
) -> list[CodexSkillMetadata]:
    discovered = discover_skill_files(roots, options)
    skills: list[CodexSkillMetadata] = []
    seen_names: set[str] = set()

    for item in discovered:
        document = parse_skill_document(item)
        skill = _document_to_codex_skill(document)
        if skill is None:
            continue
        lowered = skill.name.lower()
        if lowered in seen_names:
            continue
        seen_names.add(lowered)
        skills.append(skill)

    return skills


def _document_to_codex_skill(document: SkillDocument) -> CodexSkillMetadata | None:
    frontmatter = document.frontmatter
    raw_name = frontmatter.get("name")
    name = sanitize_single_line(str(raw_name)) if raw_name is not None else ""
    if not name:
        name = sanitize_single_line(document.skill_dir.name)

    raw_description = frontmatter.get("description")
    description = sanitize_single_line(str(raw_description)) if raw_description is not None else ""
    if not description:
        return None

    metadata = frontmatter.get("metadata")
    short_description: str | None = None
    if isinstance(metadata, dict):
        short_value = metadata.get("short-description")
        if short_value is not None:
            normalized_short = sanitize_single_line(str(short_value))
            short_description = normalized_short or None

    validate_max_len(name, _NAME_MAX_LEN, "name")
    validate_max_len(description, _DESCRIPTION_MAX_LEN, "description")
    if short_description is not None:
        validate_max_len(
            short_description,
            _SHORT_DESCRIPTION_MAX_LEN,
            "metadata.short-description",
        )

    try:
        load_optional_yaml_mapping(document.skill_dir / _SIDECAR_RELATIVE_PATH)
    except Exception:
        pass

    return CodexSkillMetadata(
        name=name,
        description=description,
        short_description=short_description,
        path_to_skills_md=document.skill_path,
        root=document.root,
        document=document,
    )


def render_codex_skills_section(skills: Sequence[CodexSkillMetadata]) -> str:
    if not skills:
        return ""

    lines = [_AVAILABLE_SKILLS_INTRO]
    lines.extend(_render_skill_lines(skills))
    lines.append(_AVAILABLE_SKILLS_USAGE)
    return "\n".join(lines)


def _render_skill_lines(skills: Sequence[CodexSkillMetadata]) -> list[str]:
    rendered: list[str] = []
    for skill in skills:
        path = skill.path_to_skills_md.as_posix()
        rendered.append(f"- {skill.name}: {skill.description} (file: {path})")
    return rendered


def collect_explicit_skill_mentions(
    messages: Sequence[dict[str, Any]],
    skills: Sequence[CodexSkillMetadata],
) -> list[CodexSkillMetadata]:
    by_name = {skill.name.lower(): skill for skill in skills}
    selected: list[CodexSkillMetadata] = []
    seen: set[str] = set()

    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "user":
            continue
        for text in iter_message_text(message):
            for match in _MENTION_RE.finditer(text):
                name = match.group(1).lower()
                skill = by_name.get(name)
                if skill is None or name in seen:
                    continue
                seen.add(name)
                selected.append(skill)

    return selected


def build_skill_injection_message(
    skill: CodexSkillMetadata,
    *,
    contents: str,
) -> dict[str, Any]:
    payload = (
        "<skill>\n"
        f"<name>{skill.name}</name>\n"
        f"<path>{skill.path_to_skills_md.as_posix()}</path>\n"
        f"{contents}\n"
        "</skill>"
    )
    return {
        "role": "user",
        "content": payload,
        "metadata": {
            "codex_skill_injected": True,
            "codex_skill_name": skill.name,
            "codex_skill_path": skill.path_to_skills_md.as_posix(),
        },
    }


def existing_injected_skill_keys(
    messages: Sequence[dict[str, Any]],
) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for message in messages:
        if not isinstance(message, dict):
            continue

        metadata = message.get("_metadata")
        if not isinstance(metadata, dict):
            metadata = message.get("metadata")
        if isinstance(metadata, dict):
            injected = metadata.get("codex_skill_injected")
            name = metadata.get("codex_skill_name")
            path = metadata.get("codex_skill_path")
            if injected and isinstance(name, str) and isinstance(path, str):
                keys.add((name.lower(), path))
                continue

        for text in iter_message_text(message):
            if "<skill>" not in text:
                continue
            name_match = _SKILL_MESSAGE_NAME_RE.search(text)
            path_match = _SKILL_MESSAGE_PATH_RE.search(text)
            if not name_match or not path_match:
                continue
            keys.add((name_match.group(1).strip().lower(), path_match.group(1).strip()))
            break
    return keys


def iter_message_text(message: dict[str, Any]) -> Iterable[str]:
    content = message.get("content")
    if isinstance(content, str):
        yield content
        return
    if not isinstance(content, list):
        return
    for part in content:
        if not isinstance(part, dict):
            continue
        part_type = part.get("type")
        if part_type in {"input_text", "text"}:
            text = part.get("text")
            if isinstance(text, str) and text:
                yield text
