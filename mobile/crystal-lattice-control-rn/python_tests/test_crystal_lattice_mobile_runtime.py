from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import time


RUNTIME_MODULE = (
    Path(__file__).resolve().parents[1]
    / "ios"
    / "CrystalLatticePythonRuntime"
    / "Python"
    / "crystal_lattice_mobile_runtime.py"
)
CORE_PYTHON = Path(__file__).resolve().parents[3] / "core" / "python"
EMBEDDED_TOOLS_SHARED = (
    Path(__file__).resolve().parents[3]
    / "plugins"
    / "embedded-tools-shared"
    / "src"
)
EMBEDDED_CLAUDE_TOOLS = (
    Path(__file__).resolve().parents[3]
    / "plugins"
    / "embedded-claude-tools"
    / "src"
)


def load_runtime_module():
    for path in (CORE_PYTHON, EMBEDDED_TOOLS_SHARED, EMBEDDED_CLAUDE_TOOLS):
        sys.path.insert(0, str(path))
    spec = importlib.util.spec_from_file_location(
        "crystal_lattice_mobile_runtime",
        RUNTIME_MODULE,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def call(module, root: Path, method: str, path: str, body=None):
    response = json.loads(
        module.execute_json(
            json.dumps(
                {
                    "method": method,
                    "path": path,
                    "body": body,
                }
            ),
            str(root),
        )
    )
    assert response["status"] < 300, response
    return response["data"]


def test_in_process_transport_session_request_flow(tmp_path: Path) -> None:
    module = load_runtime_module()

    try:
        assert call(module, tmp_path, "GET", "/agents") == {"agents": ["local"]}
        created = call(
            module,
            tmp_path,
            "POST",
            "/sessions",
            {"agent_id": "local"},
        )
        session_id = created["session"]["session_id"]
        started = call(
            module,
            tmp_path,
            "POST",
            f"/sessions/{session_id}/send_message",
            {
                "message": {
                    "role": "user",
                    "content": "hello",
                }
            },
        )

        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            events = call(
                module,
                tmp_path,
                "GET",
                (
                    f"/events?session_id={session_id}"
                    f"&request_id={started['request_id']}"
                ),
            )
            if any(
                event.get("type") == "request_completed" for event in events["events"]
            ):
                break
            time.sleep(0.01)
        else:
            raise AssertionError("Embedded request did not complete")

        messages = call(
            module,
            tmp_path,
            "GET",
            f"/sessions/{session_id}/messages",
        )
        assert [entry["message"]["role"] for entry in messages["messages"]] == [
            "user",
            "assistant",
        ]
        assert (
            messages["messages"][-1]["message"]["content"]
            == "Embedded runtime smoke response"
        )
    finally:
        module.shutdown_runtime()


def test_external_claude_like_tools_reject_escapes_and_round_trip_text(
    tmp_path: Path,
) -> None:
    module = load_runtime_module()
    from embedded_claude_tools import ClaudeLikeReadTool, ClaudeLikeWriteTool

    assert not hasattr(module, "WorkspaceReadTool")
    assert not hasattr(module, "WorkspaceWriteTool")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    read_tool = ClaudeLikeReadTool()
    write_tool = ClaudeLikeWriteTool()
    read_state = read_tool.init({"working_directory": str(workspace)})
    write_state = write_tool.init({"working_directory": str(workspace)})

    assert not write_tool.execute_tool(
        "Write",
        {"file_path": "../outside.txt", "content": "blocked"},
        write_state,
    )["success"]
    assert not read_tool.execute_tool(
        "Read",
        {"file_path": str(tmp_path / "outside.txt")},
        read_state,
    )["success"]

    written = write_tool.execute_tool(
        "Write",
        {"file_path": "nested/output.txt", "content": "hello\nworld\n"},
        write_state,
    )
    assert written["success"]
    read = read_tool.execute_tool(
        "Read",
        {"file_path": "nested/output.txt"},
        read_state,
    )
    assert read["success"]
    assert read["result"] == "1\thello\n2\tworld"

    outside = tmp_path / "outside"
    outside.mkdir()
    symlink = workspace / "linked"
    symlink.symlink_to(outside, target_is_directory=True)
    escaped = write_tool.execute_tool(
        "Write",
        {"file_path": "linked/escape.txt", "content": "blocked"},
        write_state,
    )
    assert not escaped["success"]
    assert not (outside / "escape.txt").exists()
