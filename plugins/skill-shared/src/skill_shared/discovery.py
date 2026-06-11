from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Sequence

from .files import resolved_path_within_root
from .models import DiscoveredSkillFile, DiscoveryOptions


def discover_skill_files(
    roots: Sequence[Path],
    options: DiscoveryOptions,
) -> list[DiscoveredSkillFile]:
    discovered: list[DiscoveredSkillFile] = []

    for raw_root in roots:
        try:
            root = raw_root.resolve()
        except OSError:
            continue
        if not root.is_dir():
            continue

        seen_skill_paths: set[Path] = set()
        visited_dirs = 0
        queue: deque[tuple[Path, int]] = deque([(root, 0)])

        while queue and visited_dirs < options.max_dirs_per_root:
            current_dir, depth = queue.popleft()
            visited_dirs += 1

            try:
                entries = sorted(current_dir.iterdir(), key=lambda entry: entry.name)
            except OSError:
                continue

            for entry in entries:
                name = entry.name
                if not options.include_hidden and name.startswith("."):
                    continue

                try:
                    if entry.is_symlink() and entry.is_dir() and not options.follow_symlinks:
                        continue
                except OSError:
                    continue

                if entry.name == "SKILL.md":
                    try:
                        resolved_skill_path = entry.resolve()
                    except OSError:
                        continue
                    if not resolved_path_within_root(resolved_skill_path, root):
                        continue
                    if resolved_skill_path in seen_skill_paths:
                        continue
                    seen_skill_paths.add(resolved_skill_path)
                    discovered.append(
                        DiscoveredSkillFile(root=root, skill_path=resolved_skill_path)
                    )
                    continue

                try:
                    is_dir = entry.is_dir()
                except OSError:
                    continue
                if not is_dir:
                    continue
                if depth >= options.max_scan_depth:
                    continue
                try:
                    resolved_dir = entry.resolve()
                except OSError:
                    continue
                if not resolved_path_within_root(resolved_dir, root):
                    continue
                queue.append((resolved_dir, depth + 1))

    return discovered