from __future__ import annotations

import importlib
import sys
from pathlib import Path

from agent_app.plugin_manager import PluginManager


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_namespace_plugins_dir_does_not_shadow_regular_package(tmp_path: Path) -> None:
    """Ensure a namespace-style `plugins/` directory cannot shadow a real package.

    Python's import resolution prefers a regular package (directory with
    `__init__.py`) over a namespace package candidate (directory without it).

    This test simulates:
      - An early sys.path entry with `plugins/` but no `__init__.py` (namespace candidate)
      - A later sys.path entry with a real `plugins` package and a different submodule

    Expectation: `import plugins.shell_tool` resolves to the real package.
    """

    ns_root = tmp_path / "ns_root"
    core_root = tmp_path / "core_root"

    # Namespace candidate (no __init__.py)
    _write_file(
        ns_root / "plugins" / "shell_tool.py",
        "SENTINEL = 'namespace'\n",
    )

    # Regular package (wins)
    _write_file(core_root / "plugins" / "__init__.py", "")
    _write_file(
        core_root / "plugins" / "shell_tool.py",
        "SENTINEL = 'regular'\n",
    )

    orig_sys_path = list(sys.path)
    try:
        sys.path.insert(0, str(ns_root))
        sys.path.insert(1, str(core_root))
        importlib.invalidate_caches()
        sys.modules.pop("plugins.shell_tool", None)
        sys.modules.pop("plugins", None)

        mod = importlib.import_module("plugins.shell_tool")
        assert getattr(mod, "SENTINEL") == "regular"
        assert Path(mod.__file__ or "").resolve() == (core_root / "plugins" / "shell_tool.py").resolve()
    finally:
        sys.path[:] = orig_sys_path
        sys.modules.pop("plugins.shell_tool", None)
        sys.modules.pop("plugins", None)


def test_path_plugins_still_load_with_namespace_plugins_present(tmp_path: Path) -> None:
    """Ensure LocalPath plugin loading still works alongside a `plugins/` namespace.

    This verifies that using LocalPath repo specs ("path:..." / dict with `entry`) is not
    affected by unrelated namespace-package candidates earlier in sys.path.
    """

    ns_root = tmp_path / "ns_root"
    plugin_root = tmp_path / "tool_pkg_root"

    # Namespace candidate (no __init__.py)
    _write_file(ns_root / "plugins" / "anything.py", "x = 1\n")

    # A separate plugin package loaded via LocalPath
    _write_file(plugin_root / "tool_pkg" / "__init__.py", "")
    _write_file(
        plugin_root / "setup.py",
        "from setuptools import setup\nsetup(name='tool_pkg', version='0.0.1', packages=['tool_pkg'])\n",
    )
    _write_file(
        plugin_root / "tool_pkg" / "my_tool.py",
        """from __future__ import annotations

from typing import Any, Dict, List

from agent_core.types import ToolPlugin


class MyTool(ToolPlugin):
    name: str = "my_tool"
    version: str = "0.0.1"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return "ok"
""",
    )

    orig_sys_path = list(sys.path)
    try:
        sys.path.insert(0, str(ns_root))
        importlib.invalidate_caches()

        mgr = PluginManager(cache_dir=tmp_path, policy={"base_dir": str(tmp_path)})
        res = mgr.resolve_all(
            [{"path": str(plugin_root), "entry": "tool_pkg.my_tool.MyTool"}]
        )
        assert res.errors == []
        assert [cls.__name__ for cls in res.classes] == ["MyTool"]
    finally:
        sys.path[:] = orig_sys_path
        sys.modules.pop("tool_pkg.my_tool", None)
        sys.modules.pop("tool_pkg", None)
        sys.modules.pop("plugins.anything", None)
        sys.modules.pop("plugins", None)
