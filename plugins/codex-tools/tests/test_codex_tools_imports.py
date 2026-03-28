from __future__ import annotations

import json
from pathlib import Path


def test_can_import_tools() -> None:
    from codex_tools.apply_patch_tool import ApplyPatchTool
    from codex_tools.shell_tool import ShellArrayTool
    from codex_tools.shell_command_tool import ShellCommandTool
    from codex_tools.shell_tool_legacy import ShellTool
    from codex_tools.codex_variant_feature import CodexVariantFeature

    assert ApplyPatchTool.name
    assert ShellArrayTool.name
    assert ShellCommandTool.name
    assert ShellTool.name
    assert CodexVariantFeature.name


def test_descriptor_is_present() -> None:
    desc = Path(__file__).resolve().parents[1] / "agent_plugin.json"
    data = json.loads(desc.read_text(encoding="utf-8"))
    assert "entries" in data
    assert data.get("module") == "codex_tools"
    assert "codex_tools.shell_tool.ShellArrayTool" in data["entries"]
    assert "codex_tools.shell_command_tool.ShellCommandTool" in data["entries"]
    assert "codex_tools.shell_tool_legacy.ShellTool" in data["entries"]
    assert "codex_tools.apply_patch_tool.ApplyPatchTool" in data["entries"]
    assert "codex_tools.codex_variant_feature.CodexVariantFeature" in data["entries"]
    assert data["kinds"]["codex_tools.codex_variant_feature.CodexVariantFeature"] == "features"
