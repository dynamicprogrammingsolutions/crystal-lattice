from __future__ import annotations

import io
import shutil
import zipfile
from pathlib import Path

import pytest

from agent_app.plugin_manager import PluginManager
from agent_core import AgentCore


def _plugin_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _policy() -> dict:
    return {
        "allow_bash_tools": True,
        "bash_timeout_seconds": 30,
        "bash_error_timeout_seconds": 5,
    }


def _have_build_epub_deps() -> bool:
    return (
        shutil.which("bash") is not None
        and shutil.which("jq") is not None
        and shutil.which("pandoc") is not None
    )


def _resolve_tool_class_by_name(tmp_path: Path, tool_name: str):
    mgr = PluginManager(cache_dir=tmp_path / "cache", policy=_policy())
    res = mgr.resolve_all([{"bash_tool": {"path": str(_plugin_dir())}}])
    assert res.errors == []

    for tool_cls in res.classes:
        tool = tool_cls()
        state = tool.init({})
        schemas = tool.get_tool_schemas(state)
        if schemas and schemas[0]["function"]["name"] == tool_name:
            return tool_cls
    raise AssertionError(f"tool not found: {tool_name}")


@pytest.mark.skipif(
    shutil.which("bash") is None, reason="bash executable not available"
)
def test_send_to_kindle_preview_uses_agent_config_keys(tmp_path: Path) -> None:
    attachment = tmp_path / "book.epub"
    attachment.write_bytes(b"dummy epub")

    tool_cls = _resolve_tool_class_by_name(tmp_path, "send_to_kindle")
    tool = tool_cls()
    state = tool.init(
        {
            "send_to_kindle_smtp_user": "tester@icloud.com",
            "send_to_kindle_from_addr": "tester@icloud.com",
            "send_to_kindle_default_to": "reader@kindle.com",
            "send_to_kindle_keychain_service": "test-kindle",
        }
    )
    preview = tool.format_tool_call_preview(
        "send_to_kindle",
        {"attachment": str(attachment)},
        state,
    )

    assert preview.startswith("send_to_kindle attachment=")
    assert "to=reader@kindle.com" in preview
    assert "book.epub" in preview


@pytest.mark.skipif(
    shutil.which("bash") is None, reason="bash executable not available"
)
def test_send_to_kindle_dry_run_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SEND_TO_KINDLE_DRY_RUN", "1")

    attachment = tmp_path / "book.epub"
    attachment.write_bytes(b"dummy epub")

    tool_cls = _resolve_tool_class_by_name(tmp_path, "send_to_kindle")

    core = AgentCore()
    core.register_tool(tool_cls)

    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {
            "name": "send_to_kindle",
            "arguments": {
                "attachment": str(attachment),
                "to": "override@example.com",
                "subject": "Custom subject",
            },
        },
    }

    items = list(
        core.iter_tool_messages(
            [tool_call],
            config={
                "send_to_kindle_smtp_user": "tester@icloud.com",
                "send_to_kindle_from_addr": "tester@icloud.com",
                "send_to_kindle_default_to": "reader@kindle.com",
                "send_to_kindle_keychain_service": "test-kindle",
            },
        )
    )
    finals = [it for it in items if isinstance(it, dict) and it.get("role") == "tool"]
    assert len(finals) == 1
    content = finals[0].get("content", "")
    assert "dry_run=true" in content
    assert "override@example.com" in content
    assert "book.epub" in content


@pytest.mark.skipif(
    shutil.which("bash") is None, reason="bash executable not available"
)
def test_send_to_kindle_accepts_existing_non_epub_attachment_in_dry_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SEND_TO_KINDLE_DRY_RUN", "1")

    attachment = tmp_path / "attachment.txt"
    attachment.write_text("still attachable", encoding="utf-8")

    tool_cls = _resolve_tool_class_by_name(tmp_path, "send_to_kindle")

    core = AgentCore()
    core.register_tool(tool_cls)

    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {
            "name": "send_to_kindle",
            "arguments": {
                "attachment": str(attachment),
            },
        },
    }

    items = list(
        core.iter_tool_messages(
            [tool_call],
            config={
                "send_to_kindle_smtp_user": "tester@icloud.com",
                "send_to_kindle_default_to": "reader@kindle.com",
            },
        )
    )
    finals = [it for it in items if isinstance(it, dict) and it.get("role") == "tool"]
    assert len(finals) == 1
    content = finals[0].get("content", "")
    assert "dry_run=true" in content
    assert "attachment.txt" in content


@pytest.mark.skipif(
    shutil.which("bash") is None or shutil.which("jq") is None,
    reason="bash and jq executables are required",
)
def test_build_epub_preview_summarizes_inputs(tmp_path: Path) -> None:
    first = tmp_path / "01.md"
    second = tmp_path / "02.md"
    first.write_text("# First\n", encoding="utf-8")
    second.write_text("# Second\n", encoding="utf-8")
    output = tmp_path / "book.epub"

    tool_cls = _resolve_tool_class_by_name(tmp_path, "build_epub_from_markdown")
    tool = tool_cls()
    state = tool.init({})
    preview = tool.format_tool_call_preview(
        "build_epub_from_markdown",
        {
            "markdown_files": [str(first), str(second)],
            "output_epub": str(output),
            "title": "Preview Book",
        },
        state,
    )

    assert preview.startswith("build_epub_from_markdown")
    assert "files=2" in preview
    assert "Preview Book" in preview
    assert "book.epub" in preview


@pytest.mark.skipif(
    not _have_build_epub_deps(),
    reason="bash, jq, and pandoc executables are required",
)
def test_build_epub_round_trip_uses_default_local_link_filter(tmp_path: Path) -> None:
    second = tmp_path / "02-details.md"
    second.write_text("# Details\n\nSupporting content.\n", encoding="utf-8")

    first = tmp_path / "01-main.md"
    first.write_text(
        f"# Main\n\nSee [details]({second}).\n\nExternal [site](https://example.com).\n",
        encoding="utf-8",
    )

    output = tmp_path / "bundle.epub"
    tool_cls = _resolve_tool_class_by_name(tmp_path, "build_epub_from_markdown")

    core = AgentCore()
    core.register_tool(tool_cls)

    tool_call = {
        "id": "call_build_1",
        "type": "function",
        "function": {
            "name": "build_epub_from_markdown",
            "arguments": {
                "markdown_files": [str(first), str(second)],
                "output_epub": str(output),
                "title": "Bundle Book",
                "author": "Plugin Test",
            },
        },
    }

    items = list(core.iter_tool_messages([tool_call], config={}))
    finals = [it for it in items if isinstance(it, dict) and it.get("role") == "tool"]
    assert len(finals) == 1
    content = finals[0].get("content", "")
    assert "built_epub=" in content
    assert "bundle.epub" in content
    assert output.is_file()
    assert output.stat().st_size > 0

    with zipfile.ZipFile(output) as zf:
        xhtml_text = io.StringIO()
        for name in zf.namelist():
            if name.endswith(".xhtml"):
                xhtml_text.write(zf.read(name).decode("utf-8", errors="ignore"))
        rendered = xhtml_text.getvalue()

    assert "details" in rendered
    assert str(second) not in rendered
    assert "https://example.com" in rendered