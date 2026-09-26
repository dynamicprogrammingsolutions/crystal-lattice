"""Deterministic structure profiles of produced task files.

The profile reports structural facts about a set of produced task files —
heading depth, subheading density, list-item and paragraph lengths, the
prose-to-checklist shape of the execution plan, and table or code-block
usage. It asserts nothing: callers record the profile as evidence, compare
it across evaluations, and may promote selected ranges to assertions only
after baseline variance has been observed.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

HEADING = re.compile(r"^(#{2,6})\s+(.+?)\s*$", re.MULTILINE)
CHECKBOX_ITEM = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s+", re.MULTILINE)
STATUS_LINE = re.compile(r"^Status:\s", re.IGNORECASE)
ORDERED_ITEM = re.compile(r"^\s*\d+[.)]\s+", re.MULTILINE)
UNORDERED_ITEM = re.compile(r"^\s*[-*]\s+(?!\[)", re.MULTILINE)
FENCED_BLOCK = re.compile(r"^\s*(```|~~~)", re.MULTILINE)
TABLE_ROW = re.compile(r"^\s*\|.+\|\s*$", re.MULTILINE)
CODE_SPAN = re.compile(r"`[^`\n]+`")

PLAN_SECTION_HINTS = ("execution plan", "plan")


def _sections(text: str) -> list[dict[str, Any]]:
    """Split markdown text into its H2 sections with nested headings kept.

    Each section carries its title, heading depth, body text, and the H2
    title it belongs to (empty for text before the first H2).
    """

    headings = list(HEADING.finditer(text))
    sections: list[dict[str, Any]] = []
    if headings and headings[0].start() > 0:
        sections.append(
            {"title": "", "depth": 2, "parent": "", "body": text[: headings[0].start()]}
        )
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        title = match.group(2).strip()
        depth = len(match.group(1))
        parent = title if depth == 2 else _current_parent(sections, title)
        sections.append(
            {
                "title": title,
                "depth": depth,
                "parent": parent,
                "body": text[match.end() : end],
            }
        )
    return sections


def _current_parent(sections: Sequence[dict[str, Any]], fallback: str) -> str:
    for section in reversed(sections):
        if section["depth"] == 2 and section["title"]:
            return section["title"]
    return fallback


def _strip_blocks(text: str) -> tuple[str, int, int, int]:
    """Remove fenced blocks and tables, returning their counts."""

    lines = text.splitlines()
    kept: list[str] = []
    fence = None
    fenced = 0
    table_rows = 0
    for line in lines:
        stripped = line.strip()
        if fence is not None:
            fenced += 1
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence = stripped[:3]
            fenced += 1
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            table_rows += 1
            continue
        kept.append(line)
    return "\n".join(kept), fenced, table_rows, 0


def _paragraphs(body: str) -> list[str]:
    paragraphs = [block.strip() for block in re.split(r"\n\s*\n", body)]
    return [
        block
        for block in paragraphs
        if block
        and not block.startswith(("#", "- ", "* ", "1.", "|", ">", "```"))
        and not STATUS_LINE.match(block)
    ]


def _words(text: str) -> int:
    return len(text.split())


def _list_items(body: str) -> list[str]:
    items: list[str] = []
    for match in re.finditer(r"^\s*(?:\d+[.)]|[-*])\s+(.+?)\s*$", body, re.MULTILINE):
        items.append(CHECKBOX_ITEM.sub("", match.group(0)).strip())
    return items


def profile_text(title: str, text: str) -> dict[str, Any]:
    """The structure profile of one markdown task file."""

    _, fenced, table_rows, _ = _strip_blocks(text)
    code_spans = len(CODE_SPAN.findall(text))
    sections = [section for section in _sections(text) if section["title"]]
    named = [section for section in sections if section["title"]]
    subsections = [section for section in named if section["depth"] > 2]
    paragraphs = [
        paragraph for section in named for paragraph in _paragraphs(section["body"])
    ]
    list_items = [item for section in named for item in _list_items(section["body"])]
    words = _words(text)
    section_words = [_words(section["body"]) for section in named]
    plan_sections = [
        section
        for section in named
        if section["depth"] == 2 and _is_plan_section(section)
    ]
    plan_subsections = [
        section
        for section in subsections
        if section["parent"] in {item["title"] for item in plan_sections}
    ]
    plan_titles = {section["title"] for section in plan_sections}
    plan_scope = plan_sections + [
        section for section in subsections if section["parent"] in plan_titles
    ]
    plan_body = "\n\n".join(section["body"] for section in plan_scope)
    plan_paragraphs = [
        paragraph
        for section in plan_scope
        for paragraph in _paragraphs(section["body"])
    ]
    plan_items = [
        item for section in plan_scope for item in _list_items(section["body"])
    ]
    return {
        "title": title,
        "words": words,
        "section_count": len(named),
        "subsection_count": len(subsections),
        "h2_titles": [section["title"] for section in named if section["depth"] == 2],
        "paragraph_count": len(paragraphs),
        "paragraph_words_mean": (
            round(sum(_words(item) for item in paragraphs) / len(paragraphs), 2)
            if paragraphs
            else 0.0
        ),
        "paragraph_words_max": max((_words(item) for item in paragraphs), default=0),
        "list_item_count": len(list_items),
        "list_item_words_mean": (
            round(sum(_words(item) for item in list_items) / len(list_items), 2)
            if list_items
            else 0.0
        ),
        "list_item_words_max": max((_words(item) for item in list_items), default=0),
        "checkbox_item_count": len(CHECKBOX_ITEM.findall(text)),
        "longest_section_words": max(section_words, default=0),
        "subsection_density": round(len(subsections) / max(len(named), 1), 2),
        "fenced_block_count": fenced,
        "table_row_count": table_rows,
        "code_span_count": code_spans,
        "plan_present": bool(plan_sections),
        "plan_words": _words(plan_body),
        "plan_paragraph_count": len(plan_paragraphs),
        "plan_list_item_count": len(plan_items),
        "plan_subsection_count": len(plan_subsections),
        "plan_prose_share": (
            round(
                sum(_words(item) for item in plan_paragraphs)
                / max(_words(plan_body), 1),
                2,
            )
            if plan_body
            else 0.0
        ),
    }


def _is_plan_section(section: Mapping[str, Any]) -> bool:
    title = str(section.get("title", "")).lower()
    if "question" in title:
        return False
    return any(hint in title for hint in PLAN_SECTION_HINTS)


def profile_task_files(task_files: Mapping[str, str]) -> dict[str, Any]:
    """The combined structure profile of a set of produced task files."""

    profiles = [profile_text(path, text) for path, text in sorted(task_files.items())]
    return {
        "file_count": len(profiles),
        "files": profiles,
        "total_words": sum(item["words"] for item in profiles),
        "plan_file_count": sum(1 for item in profiles if item["plan_present"]),
        "checkbox_item_count": sum(item["checkbox_item_count"] for item in profiles),
        "fenced_block_count": sum(item["fenced_block_count"] for item in profiles),
        "table_row_count": sum(item["table_row_count"] for item in profiles),
    }


def conversation_plan_ratio(
    task_files: Mapping[str, str],
    conversation: str,
) -> dict[str, Any]:
    """Plan-size ratio between the task files and the model's conversation.

    The conversation here is the producer's final response text. The ratio
    is reported as supporting evidence for durable-context preservation; it
    is never an assertion on its own — a small ratio is legitimate
    compression, and the semantic assessment decides whether anything
    material was dropped.
    """

    file_words = sum(_words(text) for text in task_files.values())
    conversation_words = _words(conversation)
    return {
        "task_file_words": file_words,
        "conversation_words": conversation_words,
        "file_to_conversation_ratio": (
            round(file_words / max(conversation_words, 1), 3)
            if conversation_words
            else None
        ),
    }


def profile_sequence(texts: Sequence[str]) -> dict[str, Any]:
    """Aggregate profile helper for tests and calibration runs."""

    merged = "\n\n".join(texts)
    return profile_text("<merged>", merged)


def plan_is_absent_or_draft(task_files: Mapping[str, str]) -> list[str]:
    """Violations of an absent-or-draft execution-plan expectation.

    A task file satisfies the expectation when it carries no execution
    plan section at all, or when its plan section is an explicit draft:
    a status line marking it as not yet made and no ordered work steps
    presented as decided direction. Returns one violation string per
    offending file.
    """

    violations: list[str] = []
    for path, text in sorted(task_files.items()):
        sections = _sections(text)
        plan_titles = {
            section["title"]
            for section in sections
            if section["depth"] == 2 and _is_plan_section(section)
        }
        if not plan_titles:
            continue
        in_h2_plan = False
        draft_status = False
        ordered_steps = 0
        for line in text.splitlines():
            heading = HEADING.match(line)
            if heading:
                if len(heading.group(1)) == 2:
                    in_h2_plan = _is_plan_section({"title": heading.group(2).strip()})
                continue
            if not in_h2_plan:
                continue
            if STATUS_LINE.match(line.strip()):
                if "draft" in line.lower():
                    draft_status = True
                continue
            if ORDERED_ITEM.match(line):
                ordered_steps += 1
        if not draft_status:
            violations.append(f"{path}: execution plan present without a draft status")
        elif ordered_steps:
            violations.append(
                f"{path}: draft execution plan presents ordered work steps"
            )
    return violations
