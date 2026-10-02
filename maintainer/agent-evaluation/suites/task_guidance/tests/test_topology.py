from __future__ import annotations

from ..topology import task_tree


def test_task_tree_records_parent_dependencies_and_phase_names() -> None:
    files = {
        "tasks/demo/000-main.md": """\
# Main

Description.

## Requirements checklist

- [ ] Deliver the result.
""",
        "tasks/demo/010-backend-implementation.md": """\
Parent Task: `tasks/demo/000-main.md`

Depends On:

- `tasks/demo/000-main.md`

# Backend implementation

Description.

## Requirements checklist

- [ ] Implement the backend.

## Execution plan

Status: Draft
""",
    }

    tree = task_tree(files)

    assert tree["task_file_count"] == 2
    assert tree["implementation_task_count"] == 1
    assert tree["coordinating_files"] == ["tasks/demo/000-main.md"]
    assert tree["task_directory_count"] == 1
    assert tree["all_parent_links_resolve"] is True
    assert tree["all_dependencies_resolve"] is True
    assert tree["phase_named_files"] == ["tasks/demo/010-backend-implementation.md"]
    child = tree["files"][1]
    assert child["requirement_count"] == 1
    assert child["plan_status"] == "Draft"


def test_task_tree_reports_unresolved_links_without_rejecting_the_record() -> None:
    tree = task_tree(
        {
            "tasks/demo/010-slice.md": """\
Parent Task: `tasks/demo/000-main.md`

# Slice

Description.

## Requirements checklist

- [ ] Deliver.
"""
        }
    )

    assert tree["all_parent_links_resolve"] is False
    assert tree["implementation_task_count"] == 1
