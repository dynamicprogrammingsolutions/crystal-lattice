from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any, Mapping


PHASE_TERMS = {
    "implementation",
    "testing",
    "tests",
    "documentation",
    "docs",
    "review",
    "deployment",
    "frontend",
    "backend",
    "integration",
}


def task_tree(task_files: Mapping[str, str]) -> dict[str, Any]:
    files = [
        _task_file_record(path, text)
        for path, text in sorted(task_files.items())
    ]
    paths = {item["path"] for item in files}
    coordinating_files = [
        item["path"]
        for item in files
        if PurePosixPath(item["path"]).name == "000-main.md"
    ]
    parent_links = [
        {
            "child": item["path"],
            "parent": item["parent_task"],
            "resolves": item["parent_task"] in paths,
        }
        for item in files
        if item["parent_task"]
    ]
    dependencies = [
        {
            "task": item["path"],
            "dependency": dependency,
            "resolves": dependency in paths,
        }
        for item in files
        for dependency in item["dependencies"]
    ]
    return {
        "task_file_count": len(files),
        "implementation_task_count": len(files) - len(coordinating_files),
        "coordinating_files": coordinating_files,
        "task_directory_count": len(
            {
                str(PurePosixPath(item["path"]).parent)
                for item in files
                if len(PurePosixPath(item["path"]).parts) > 2
            }
        ),
        "files": files,
        "parent_links": parent_links,
        "dependencies": dependencies,
        "all_parent_links_resolve": all(
            item["resolves"] for item in parent_links
        ),
        "all_dependencies_resolve": all(
            item["resolves"] for item in dependencies
        ),
        "phase_named_files": [
            item["path"]
            for item in files
            if item["phase_terms"]
            and item["path"] not in coordinating_files
        ],
    }


def _task_file_record(path: str, text: str) -> dict[str, Any]:
    title_match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    title = title_match.group(1).strip() if title_match else ""
    parent_match = re.search(
        r"(?im)^Parent Task:\s*`?([^`\n]+?)`?\s*$",
        text,
    )
    parent_task = parent_match.group(1).strip() if parent_match else None
    dependencies = _dependencies(text)
    requirement_section = _section(text, "## Requirements checklist")
    requirement_count = len(
        re.findall(r"(?m)^\s*-\s+\[[ xX]\]\s+", requirement_section)
    )
    normalized_name = (
        PurePosixPath(path).stem.replace("-", " ") + " " + title
    ).lower()
    phase_terms = sorted(
        term for term in PHASE_TERMS if re.search(rf"\b{term}\b", normalized_name)
    )
    return {
        "path": path,
        "title": title,
        "requirement_count": requirement_count,
        "parent_task": parent_task,
        "dependencies": dependencies,
        "phase_terms": phase_terms,
        "has_execution_plan": bool(
            re.search(r"(?im)^##\s+Execution plan\s*$", text)
        ),
        "plan_status": _plan_status(text),
    }


def _dependencies(text: str) -> list[str]:
    match = re.search(
        r"(?ims)^Depends On:\s*(.*?)(?=^##\s+|^[A-Z][A-Za-z ]+:\s*$|\Z)",
        text,
    )
    if match is None:
        return []
    return [
        value.strip()
        for value in re.findall(r"`([^`]+\.md)`", match.group(1))
    ]


def _section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    following = text.find("\n## ", start + len(heading))
    return text[start:] if following < 0 else text[start:following]


def _plan_status(text: str) -> str | None:
    plan = re.search(r"(?im)^##\s+Execution plan\s*$", text)
    if plan is None:
        return None
    match = re.search(r"(?im)^Status:\s*(Draft|Approved)\s*$", text[plan.end() :])
    return match.group(1) if match else None