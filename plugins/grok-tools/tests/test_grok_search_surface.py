from __future__ import annotations

from pathlib import Path

from agent_app.plugin_manager import PluginManager
from agent_core.plugin import ToolWrapper


def test_grok_package_does_not_expose_list_grep_or_glob_names(tmp_path: Path) -> None:
    mgr = PluginManager(cache_dir=tmp_path / "cache", policy={"install_deps": True})
    repo = Path(__file__).resolve().parents[1]
    resolution = mgr.resolve_all([{"path": str(repo)}])
    assert resolution.errors == []

    names = []
    for cls in resolution.classes:
        wrapper = ToolWrapper(cls)
        state = wrapper.init({"working_directory": str(tmp_path), "allowed_paths": [str(tmp_path)], "project_temp_dir": str(tmp_path / ".temp")})
        names.extend(schema["function"]["name"] for schema in wrapper.get_tool_schemas(state))

    assert names == ["view_file", "create_file", "str_replace_editor"]
