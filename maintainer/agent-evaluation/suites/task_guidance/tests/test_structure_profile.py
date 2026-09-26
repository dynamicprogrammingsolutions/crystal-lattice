"""Structure-profile unit tests on synthetic task files.

Each synthetic file exhibits one quality gap observed in real evaluations:
a checklist-only execution plan, an unstructured prose wall, a dropped
plan, and a well-structured reference file. The profile must report the
structural facts that separate them without asserting anything.
"""

from __future__ import annotations

from suites.task_guidance.structure import (
    conversation_plan_ratio,
    profile_task_files,
    profile_text,
)

WELL_STRUCTURED = """# Paginate the blog archive

## Requirements checklist
- [ ] The archive lists posts in reverse date order across pages.
- [ ] Page size is clamped between 5 and 50.

## Supporting details
The paginator owns page assembly; the route owns query parsing.

| Param | Range |
|---|---|
| page | >= 1 |
| limit | 5..50 |

## Execution plan
Status: Approved

### Decided design
The paginator owns page assembly and clamping; the route parses the query
and never sees page math. The client contract is unchanged.

### Verification
`test_archive_pagination` walks pages 1..3 and asserts ordering and clamps.

### Steps
1. Add the paginator with clamping.
2. Wire the route to the paginator.
3. Add the walker test.

## Questions and decisions
- Open: none.
"""

CHECKLIST_ONLY_PLAN = """# Paginate the blog archive

## Requirements checklist
- [ ] The archive lists posts in reverse date order across pages.

## Execution plan
Status: Approved

1. Add a paginator module with page-size clamping and reverse ordering.
2. Wire the archive route to call the paginator and pass query parameters.
3. Add tests covering ordering, clamping, and empty pages end to end.
4. Update the documentation page for the archive query parameters.
5. Run the full test suite and fix any regressions found during the work.

## Questions and decisions
- Open: none.
"""

PROSE_WALL = """# Migrate author metadata

## Requirements checklist
- [ ] Posts render structured authors.

## Supporting details
The current front matter stores a single string author field per post and
the templates read it directly, but we agreed that this has to become a
structured list where each entry carries the display name and an optional
profile link, and the migration has to keep rendering working throughout
the transition, which means the reader side has to accept both shapes for
as long as un-migrated content exists, and the authoring tool has to write
the new shape only after the reader is deployed, and we also found that
generated tag pages embed the raw string so they need the same dual-shape
handling during the transition period.

## Execution plan
Status: Draft

We will migrate the front matter first, then the templates, then the
authoring tool, then clean up the legacy path once every post is migrated,
and each stage has its own verification steps listed in order.
"""

NO_PLAN = """# Track the archive fix

## Requirements checklist
- [ ] The archive lists posts in reverse date order.

## Supporting details
The fix was decided in conversation; the paginator owns page assembly.
"""


def test_reference_file_reports_design_bearing_plan() -> None:
    profile = profile_text("t.md", WELL_STRUCTURED)

    assert profile["plan_present"] is True
    assert profile["plan_subsection_count"] == 3
    assert profile["plan_prose_share"] >= 0.4
    assert profile["table_row_count"] >= 3
    assert profile["code_span_count"] >= 1


def test_checklist_only_plan_reports_low_prose_share() -> None:
    profile = profile_text("t.md", CHECKLIST_ONLY_PLAN)

    assert profile["plan_present"] is True
    assert profile["plan_subsection_count"] == 0
    assert profile["plan_list_item_count"] == 5
    assert profile["plan_prose_share"] < 0.2
    assert (
        profile["plan_prose_share"]
        < profile_text("t.md", WELL_STRUCTURED)["plan_prose_share"]
    )


def test_prose_wall_reports_dense_paragraphs() -> None:
    profile = profile_text("t.md", PROSE_WALL)

    assert profile["paragraph_words_max"] > 80
    assert profile["paragraph_count"] <= 2
    assert profile["subsection_count"] == 0
    assert profile["table_row_count"] == 0


def test_missing_plan_is_reported_not_asserted() -> None:
    profile = profile_text("t.md", NO_PLAN)

    assert profile["plan_present"] is False
    assert profile["plan_words"] == 0
    assert profile["plan_prose_share"] == 0.0


def test_question_sections_are_not_plan_sections() -> None:
    profile = profile_text(
        "t.md",
        """# Task

## Questions and decisions
- Open: which plan shape?

## Execution plan
Status: Draft

The design is undecided; nothing is ordered yet.
""",
    )

    assert profile["plan_present"] is True
    assert profile["plan_paragraph_count"] == 1


def test_profile_task_files_aggregates_multiple_files() -> None:
    combined = profile_task_files(
        {"tasks/a.md": WELL_STRUCTURED, "tasks/b.md": NO_PLAN}
    )

    assert combined["file_count"] == 2
    assert combined["plan_file_count"] == 1
    assert combined["total_words"] == sum(item["words"] for item in combined["files"])


def test_conversation_ratio_reports_compression_evidence() -> None:
    conversation = "\n".join(
        f"Design point {number}: the paginator owns assembly and the route"
        " owns parsing, with clamping between five and fifty per page."
        for number in range(20)
    )
    ratio = conversation_plan_ratio({"tasks/a.md": WELL_STRUCTURED}, conversation)

    assert ratio["conversation_words"] > ratio["task_file_words"] > 0
    assert 0.0 < ratio["file_to_conversation_ratio"] < 1.0
