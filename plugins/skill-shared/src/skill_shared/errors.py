from __future__ import annotations


class SkillSharedError(Exception):
    """Base exception for shared skill discovery and parsing helpers."""


class SkillFrontmatterError(SkillSharedError):
    """Raised when a skill file has invalid or missing frontmatter."""


class SkillYamlError(SkillSharedError):
    """Raised when a YAML payload is malformed or not a mapping."""