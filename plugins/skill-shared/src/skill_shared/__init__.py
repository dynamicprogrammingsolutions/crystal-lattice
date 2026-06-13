"""Shared discovery and parsing helpers for vendor skill integrations.

This package is a library package, not a plugin package.
"""

from .discovery import discover_skill_files
from .files import resolved_path_within_root, sanitize_single_line, validate_max_len
from .models import DiscoveredSkillFile, DiscoveryOptions, ParsedYamlFile, SkillDocument
from .parser import (
    extract_frontmatter_and_body,
    load_optional_yaml_mapping,
    parse_skill_document,
    parse_yaml_mapping,
)

__all__ = [
    "DiscoveredSkillFile",
    "DiscoveryOptions",
    "ParsedYamlFile",
    "SkillDocument",
    "discover_skill_files",
    "extract_frontmatter_and_body",
    "load_optional_yaml_mapping",
    "parse_skill_document",
    "parse_yaml_mapping",
    "resolved_path_within_root",
    "sanitize_single_line",
    "validate_max_len",
]