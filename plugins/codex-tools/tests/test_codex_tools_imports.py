from __future__ import annotations

import json
from pathlib import Path


def test_can_import_tools() -> None:
    from codex_tools.apply_patch_tool import ApplyPatchTool
    from codex_tools.shell_tool import ShellTool

    assert ApplyPatchTool.name
    assert ShellTool.name


def test_descriptor_is_present() -> None:
    desc = Path(__file__).resolve().parents[1] / "agent_plugin.json"
    data = json.loads(desc.read_text(encoding="utf-8"))
    assert "entries" in data
    assert data.get("module") == "codex_tools"
    assert "codex_tools.shell_tool.ShellTool" in data["entries"]
