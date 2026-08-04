from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from prepare_review_bundle import (  # noqa: E402
    prepare_review_bundle,
    render_messages_markdown,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_render_messages_counts_tool_calls_between_visible_messages() -> None:
    session = {
        "messages": [
            {"role": "user", "content": "Please inspect this."},
            {
                "role": "assistant",
                "content": "I will inspect it.",
                "metadata": {
                    "phase": "commentary",
                    "tool_calls": [
                        {"function": {"name": "shell", "arguments": "{}"}},
                        {"function": {"name": "shell", "arguments": "{}"}},
                    ],
                },
            },
            {"role": "tool", "content": "result"},
            {
                "role": "assistant",
                "content": "",
                "metadata": {
                    "tool_calls": [
                        {"function": {"name": "Read", "arguments": "{}"}}
                    ]
                },
            },
            {"role": "tool", "content": "result"},
            {
                "role": "assistant",
                "content": "Here is the result.",
                "metadata": {"phase": "final_answer"},
            },
        ]
    }

    rendered = render_messages_markdown(
        session,
        {
            "scenario": "demo",
            "agent_id": "agent",
            "model": "model",
        },
    )

    assert "## 2. Assistant commentary" in rendered
    assert "Tool calls before the next exported message: **3**" in rendered
    assert "`shell` × 2" in rendered
    assert "`Read` × 1" in rendered
    assert "Total tool calls: **3**" in rendered


def test_prepare_review_bundle_uses_saved_artifacts(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    case_dir = run_dir / "create-task-after-plan" / "demo-model"
    case_dir.mkdir(parents=True)

    guidance = "# Task guidance\n\nSaved version.\n"
    guidance_hash = hashlib.sha256(guidance.encode("utf-8")).hexdigest()
    run_dir.joinpath("TASKS.md").write_text(guidance, encoding="utf-8")
    case_dir.joinpath("TASKS.md").write_text(guidance, encoding="utf-8")
    case_dir.joinpath("compiled-system-message.md").write_text(
        "Full compiled prompt.\n",
        encoding="utf-8",
    )
    case_dir.joinpath("task-file.md").write_text(
        "# Demo Task\n\n"
        "Record the desired outcome.\n\n"
        "## Requirements checklist\n\n"
        "- [ ] Observable result.\n",
        encoding="utf-8",
    )
    case_dir.joinpath("git-status-1.txt").write_text("", encoding="utf-8")
    _write_json(
        case_dir / "metadata.json",
        {
            "scenario": "create-task-after-plan",
            "agent_id": "demo-agent",
            "model": "demo-model",
            "guidance_sha256": guidance_hash,
            "mutation_call_limit": 3,
        },
    )
    _write_json(case_dir / "mutation-calls.json", [{"tool_name": "Write"}])
    _write_json(
        case_dir / "session-1.json",
        {
            "session_id": "demo",
            "metadata": {},
            "messages": [
                {"role": "user", "content": "Create the task."},
                {
                    "role": "assistant",
                    "content": "Created the requested task file.",
                    "metadata": {},
                },
            ],
        },
    )

    output = prepare_review_bundle(
        run_dir,
        tmp_path / "review",
    )
    case_output = (
        output / "cases" / "create-task-after-plan" / "demo-model"
    )

    assert output.joinpath("README.md").is_file()
    assert output.joinpath("TASKS.md").read_text(encoding="utf-8") == guidance
    assert "Assistant" in case_output.joinpath("messages.md").read_text(
        encoding="utf-8"
    )
    assert (
        case_output.joinpath("compiled-system-message.md").read_text(
            encoding="utf-8"
        )
        == "Full compiled prompt.\n"
    )
    assertions = case_output.joinpath("assertions.md").read_text(
        encoding="utf-8"
    )
    assert "| PASS |" in assertions
    assert "| FAIL |" not in assertions