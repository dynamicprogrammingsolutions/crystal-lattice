from __future__ import annotations

import json
from pathlib import Path

from agent_core import AgentCore

from embedded_claude_tools import ClaudeLikeReadTool, ClaudeLikeWriteTool


def _call(name: str, arguments: dict[str, object], call_id: str) -> dict[str, object]:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(arguments),
        },
    }


def test_schemas_use_claude_like_names(tmp_path: Path) -> None:
    config = {"working_directory": str(tmp_path)}

    read = ClaudeLikeReadTool()
    write = ClaudeLikeWriteTool()

    assert read.get_tool_schemas(read.init(config))[0]["function"]["name"] == "Read"
    assert write.get_tool_schemas(write.init(config))[0]["function"]["name"] == "Write"


def test_core_round_trip_uses_shared_workspace_engine(tmp_path: Path) -> None:
    config = {"working_directory": str(tmp_path / "workspace")}
    core = AgentCore()
    core.register_tool(ClaudeLikeReadTool)
    core.register_tool(ClaudeLikeWriteTool)

    written = core.execute_tool_calls(
        [
            _call(
                "Write",
                {"file_path": "nested/output.txt", "content": "hello\nworld\n"},
                "write-1",
            )
        ],
        config,
    )
    assert written[0]["content"] == "Wrote 12 bytes to nested/output.txt"
    assert written[0]["metadata"]["tool_name"] == "Write"

    read = core.execute_tool_calls(
        [_call("Read", {"file_path": "nested/output.txt"}, "read-1")],
        config,
    )
    assert read[0]["content"] == "1\thello\n2\tworld"
    assert read[0]["metadata"]["tool_name"] == "Read"


def test_tools_reject_absolute_traversal_and_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (workspace / "linked").symlink_to(outside, target_is_directory=True)
    config = {"working_directory": str(workspace)}

    write = ClaudeLikeWriteTool()
    write_state = write.init(config)
    read = ClaudeLikeReadTool()
    read_state = read.init(config)

    assert not write.execute_tool(
        "Write",
        {"file_path": "../outside.txt", "content": "blocked"},
        write_state,
    )["success"]
    assert not read.execute_tool(
        "Read",
        {"file_path": str(outside / "outside.txt")},
        read_state,
    )["success"]
    assert not write.execute_tool(
        "Write",
        {"file_path": "linked/escape.txt", "content": "blocked"},
        write_state,
    )["success"]
    assert not (outside / "escape.txt").exists()


def test_tools_use_session_directory_within_fixed_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    selected = workspace / "projects" / "alpha"
    sibling = workspace / "projects" / "beta"
    selected.mkdir(parents=True)
    sibling.mkdir()
    config = {
        "workspace_root": str(workspace),
        "allowed_paths": [str(workspace)],
        "working_directory": str(selected),
    }
    write = ClaudeLikeWriteTool()
    state = write.init(config)

    written = write.execute_tool(
        "Write",
        {"file_path": "session.txt", "content": "alpha"},
        state,
    )
    escaped = write.execute_tool(
        "Write",
        {"file_path": "../beta/escape.txt", "content": "blocked"},
        state,
    )

    assert written["success"]
    assert (selected / "session.txt").read_text(encoding="utf-8") == "alpha"
    assert not escaped["success"]
    assert not (sibling / "escape.txt").exists()