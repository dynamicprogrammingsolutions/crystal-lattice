from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DiscoveryOptions:
    follow_symlinks: bool = False
    max_scan_depth: int = 6
    max_dirs_per_root: int = 2000
    include_hidden: bool = False


@dataclass(frozen=True)
class DiscoveredSkillFile:
    root: Path
    skill_path: Path

    @property
    def skill_dir(self) -> Path:
        return self.skill_path.parent


@dataclass(frozen=True)
class SkillDocument:
    skill_path: Path
    skill_dir: Path
    root: Path
    frontmatter: dict[str, Any]
    body: str


@dataclass(frozen=True)
class ParsedYamlFile:
    path: Path
    data: dict[str, Any]