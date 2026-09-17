from __future__ import annotations

from pathlib import Path

from embedded_tools_shared import FetchedPage

from embedded_claude_tools import (
    ClaudeLikeEditTool,
    ClaudeLikeGlobTool,
    ClaudeLikeGrepTool,
    ClaudeLikeReadTool,
    ClaudeLikeWebFetchTool,
    ClaudeLikeWriteTool,
)
from embedded_claude_tools import web_fetch_tool as web_fetch_module


def test_model_visible_schema_names_are_claude_like(tmp_path: Path) -> None:
    config = {"working_directory": str(tmp_path)}
    tools = [
        ClaudeLikeReadTool(),
        ClaudeLikeWriteTool(),
        ClaudeLikeEditTool(),
        ClaudeLikeGlobTool(),
        ClaudeLikeGrepTool(),
        ClaudeLikeWebFetchTool(),
    ]
    assert [
        tool.get_tool_schemas(tool.init(config))[0]["function"]["name"]
        for tool in tools
    ] == ["Read", "Write", "Edit", "Glob", "Grep", "WebFetch"]


def test_write_and_edit_existing_files_require_prior_read(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "settings.txt"
    target.write_text("mode=old\n", encoding="utf-8")
    config = {"working_directory": str(workspace)}
    context = {"request_id": "request-guard"}

    read = ClaudeLikeReadTool()
    read_state = read.init(config)
    write = ClaudeLikeWriteTool()
    write_state = write.init(config)
    edit = ClaudeLikeEditTool()
    edit_state = edit.init(config)

    denied_write = write.execute_tool(
        "Write",
        {"file_path": "settings.txt", "content": "mode=write\n"},
        write_state,
        context=context,
    )
    assert not denied_write["success"]
    assert "Read it first" in denied_write["error"]

    denied_edit = edit.execute_tool(
        "Edit",
        {
            "file_path": "settings.txt",
            "old_string": "old",
            "new_string": "new",
        },
        edit_state,
        context=context,
    )
    assert not denied_edit["success"]
    assert "Read it first" in denied_edit["error"]

    assert read.execute_tool(
        "Read",
        {"file_path": "settings.txt"},
        read_state,
        context=context,
    )["success"]
    edited = edit.execute_tool(
        "Edit",
        {
            "file_path": "settings.txt",
            "old_string": "old",
            "new_string": "new",
        },
        edit_state,
        context=context,
    )
    assert edited["success"]
    assert target.read_text(encoding="utf-8") == "mode=new\n"

    written = write.execute_tool(
        "Write",
        {"file_path": "settings.txt", "content": "mode=final\n"},
        write_state,
        context=context,
    )
    assert written["success"]
    assert target.read_text(encoding="utf-8") == "mode=final\n"


def test_glob_and_grep_use_workspace_relative_results(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "docs/nested").mkdir(parents=True)
    (workspace / "docs/alpha.md").write_text(
        "# Alpha\nORBITAL marker\n",
        encoding="utf-8",
    )
    (workspace / "docs/nested/beta.md").write_text(
        "# Beta\norbital marker\n",
        encoding="utf-8",
    )
    (workspace / "docs/ignored.txt").write_text("ORBITAL\n", encoding="utf-8")
    config = {"working_directory": str(workspace)}

    glob = ClaudeLikeGlobTool()
    glob_result = glob.execute_tool(
        "Glob",
        {"path": "docs", "pattern": "**/*.md"},
        glob.init(config),
    )
    assert glob_result["success"]
    assert glob_result["result"].splitlines() == [
        "docs/alpha.md",
        "docs/nested/beta.md",
    ]

    grep = ClaudeLikeGrepTool()
    grep_result = grep.execute_tool(
        "Grep",
        {
            "path": "docs",
            "pattern": "orbital",
            "glob": "**/*.md",
            "output_mode": "content",
            "-i": True,
            "-n": True,
        },
        grep.init(config),
    )
    assert grep_result["success"]
    assert grep_result["result"].splitlines() == [
        "docs/alpha.md:2:ORBITAL marker",
        "docs/nested/beta.md:2:orbital marker",
    ]


def test_web_fetch_uses_shared_public_fetch_engine(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _ = tmp_path
    calls: list[str] = []

    def fake_fetch(url: str, *, policy):
        calls.append(url)
        assert policy.max_bytes == 2048
        return FetchedPage(
            requested_url=url,
            final_url="https://example.com/final",
            status_code=200,
            reason="OK",
            headers=(("Content-Type", "text/html"),),
            content_type="text/html",
            body_text="<title>Example</title><p>hello</p>",
            extracted_text="Example\nhello",
            title="Example",
            truncated_bytes=False,
            truncated_text=False,
            duration_seconds=0.01,
        )

    monkeypatch.setattr(web_fetch_module, "fetch_public_url", fake_fetch)
    tool = ClaudeLikeWebFetchTool()
    state = tool.init({"web_fetch_max_bytes": 2048})
    result = tool.execute_tool(
        "WebFetch",
        {"url": "https://example.com", "prompt": "Find the title"},
        state,
    )

    assert calls == ["https://example.com"]
    assert result["success"]
    assert "Title: Example" in result["result"]
    assert "Requested focus: Find the title" in result["result"]