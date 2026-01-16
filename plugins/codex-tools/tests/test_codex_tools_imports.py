from __future__ import annotations

import json
import importlib.resources as ilr


def test_can_import_tools() -> None:
    from codex_tools.apply_patch_tool import ApplyPatchTool
    from codex_tools.shell_tool import ShellTool

    assert ApplyPatchTool.name
    assert ShellTool.name


def test_descriptor_is_present() -> None:
    import codex_tools

    desc = ilr.files(codex_tools) / "agent_plugin.json"
    assert desc.is_file()
    data = json.loads(desc.read_text(encoding="utf-8"))
    assert "entries" in data
    assert "codex_tools.shell_tool.ShellTool" in data["entries"]
