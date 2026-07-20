from __future__ import annotations

import sys
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from harness import (  # noqa: E402
    MutationBudget,
    PREMADE_TASK_TEMPLATE,
    assert_draft_execution_plan,
    assert_no_execution_plan,
    assert_task_prefix,
    describe_tool_call,
    requirements_section,
)


def test_describe_tool_call_detects_task_file_mutations() -> None:
    direct = {
        "type": "function",
        "function": {
            "name": "apply_patch",
            "arguments": '{"patch":"*** Begin Patch"}',
        },
    }
    shell = {
        "type": "function",
        "function": {
            "name": "shell",
            "arguments": (
                '{"command":["apply_patch","*** Begin Patch\\n*** End Patch"]}'
            ),
        },
    }
    write = {
        "type": "function",
        "function": {
            "name": "Write",
            "arguments": '{"file_path":"tasks/demo.md","content":"demo"}',
        },
    }
    read = {
        "type": "function",
        "function": {
            "name": "Read",
            "arguments": '{"file_path":"README.md"}',
        },
    }

    assert describe_tool_call(direct)["mutation_kind"] == "apply_patch"
    assert describe_tool_call(shell)["mutation_kind"] == "apply_patch_via_shell"
    assert describe_tool_call(write)["mutation_kind"] == "write"
    assert describe_tool_call(read)["is_mutation"] is False


def test_premade_task_has_required_prefix_and_no_plan() -> None:
    text = PREMADE_TASK_TEMPLATE.read_text(encoding="utf-8")

    assert_task_prefix(text)
    assert_no_execution_plan(text)
    assert "- [ ]" in requirements_section(text)


def test_draft_plan_structure_is_checked_separately() -> None:
    text = """\
# Demo

Description.

## Requirements checklist

- [ ] Observable result.

## Context

Useful details.

## Execution plan

Status: Draft

Approach.

### Requirement verification

- Requirement: component test.

### Documentation

No change, because this is internal.

### Task checklist

- [ ] Implement.
"""

    assert_task_prefix(text)
    assert_draft_execution_plan(text)


def test_default_creation_rejects_an_execution_plan() -> None:
    for heading in ("## Execution plan", "## Execution Plan", "## Plan (Draft)"):
        with pytest.raises(AssertionError, match="unexpectedly included"):
            assert_no_execution_plan(
                "# Demo\n\nDescription.\n\n## Requirements checklist\n\n"
                f"- [ ] Outcome.\n\n{heading}\n"
            )


def test_task_prefix_rejects_status_before_requirements() -> None:
    with pytest.raises(AssertionError, match="status metadata"):
        assert_task_prefix(
            "# Demo\n\nDescription.\n\nStatus: Draft\n\n"
            "## Requirements checklist\n\n- [ ] Outcome.\n"
        )


def test_draft_plan_accepts_heading_capitalization() -> None:
    text = """\
# Demo

Description.

## Requirements checklist

- [ ] Outcome.

## Execution Plan

Status: Draft

### Requirement verification

Evidence.

### Documentation

No change.

### Task checklist

- [ ] Execute.
"""

    assert_draft_execution_plan(text)


def test_mutation_budget_applies_to_rebuilt_core_instances() -> None:
    class FakeCore:
        def iter_tool_messages(self, tool_calls, config, context=None):
            yield {"tool_calls": tool_calls, "config": config, "context": context}

    first_core = FakeCore()
    budget = MutationBudget(limit=1)
    budget.install(first_core)
    apply_patch_call = {
        "type": "function",
        "function": {
            "name": "apply_patch",
            "arguments": '{"patch":"*** Begin Patch"}',
        },
    }

    try:
        assert list(
            FakeCore().iter_tool_messages([apply_patch_call], {}, context=None)
        )
        with pytest.raises(RuntimeError, match="mutation-call limit exceeded"):
            list(FakeCore().iter_tool_messages([apply_patch_call], {}, context=None))
    finally:
        budget.uninstall()

    assert len(budget.calls) == 2
