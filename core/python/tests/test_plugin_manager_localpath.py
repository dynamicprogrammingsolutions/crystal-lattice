"""Tests for application-level PluginManager local path support.

Local path repos are installed into the plugin cache via
`pip install --target ...`, then loaded from the installed target.
"""

from __future__ import annotations

from pathlib import Path
import textwrap

from agent_app.plugin_manager import PluginManager


def _make_dev_repo(tmp_path: Path) -> Path:
    """Create a minimal installable repo with a provider plugin class."""

    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)

    (repo / "setup.py").write_text(
        "from setuptools import setup\nsetup(name='myplugins', version='0.0.1', packages=['myplugins'])\n",
        encoding="utf-8",
    )

    pkg = repo / "myplugins"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "provider_mod.py").write_text(
        textwrap.dedent(
            """
            class DevProvider:
                name = "dev_provider"

                def init(self, config):
                    return {}

                def call_api(self, native_messages, state):
                    return [], [], [], state
            """
        ),
        encoding="utf-8",
    )
    return repo


def test_localpath_source_loads_provider(tmp_path: Path) -> None:
    repo = _make_dev_repo(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)

    spec = {"path": str(repo), "entry": "myplugins.provider_mod.DevProvider"}
    mgr = PluginManager(cache_dir=cache_dir)

    res = mgr.resolve_all([spec])
    assert res.errors == []
    assert [getattr(cls, "__name__", "") for cls in res.classes] == ["DevProvider"]


def test_manager_loads_mixed_dotted_and_localpath(tmp_path: Path) -> None:
    repo = _make_dev_repo(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)

    spec_local = {"path": str(repo), "entry": "myplugins.provider_mod.DevProvider"}
    # Known dotted-path provider class from repo
    spec_dotted = "plugins.openai_provider.OpenAICompatibleProvider"

    mgr = PluginManager(cache_dir=cache_dir)
    res = mgr.resolve_all([spec_local, spec_dotted])
    assert res.errors == []
    assert len(res.classes) == 2
    names = [cls.__name__ for cls in res.classes]
    assert set(names) == {"DevProvider", "OpenAICompatibleProvider"}


def test_localpath_source_can_install_sibling_dependency(tmp_path: Path) -> None:
    root = tmp_path / "repos"
    shared = root / "sharedpkg"
    plugin = root / "pluginrepo"
    shared_pkg = shared / "src" / "sharedpkg"
    plugin_pkg = plugin / "src" / "pluginrepo"
    shared_pkg.mkdir(parents=True, exist_ok=True)
    plugin_pkg.mkdir(parents=True, exist_ok=True)

    (shared / "pyproject.toml").write_text(
        textwrap.dedent(
            """
            [build-system]
            requires = ["setuptools>=61.0", "wheel"]
            build-backend = "setuptools.build_meta"

            [project]
            name = "sharedpkg"
            version = "0.0.1"

            [tool.setuptools]
            package-dir = {"" = "src"}

            [tool.setuptools.packages.find]
            where = ["src"]
            """
        ),
        encoding="utf-8",
    )
    (shared_pkg / "__init__.py").write_text("VALUE = 7\n", encoding="utf-8")

    (plugin / "pyproject.toml").write_text(
        textwrap.dedent(
            """
            [build-system]
            requires = ["setuptools>=61.0", "wheel"]
            build-backend = "setuptools.build_meta"

            [project]
            name = "pluginrepo"
            version = "0.0.1"
            dynamic = ["dependencies"]

            [tool.setuptools]
            package-dir = {"" = "src"}

            [tool.setuptools.packages.find]
            where = ["src"]
            """
        ),
        encoding="utf-8",
    )
    (plugin / "setup.py").write_text(
        textwrap.dedent(
            """
            from pathlib import Path
            from setuptools import setup

            sibling = (Path(__file__).resolve().parents[1] / "sharedpkg").resolve()

            setup(
                name="pluginrepo",
                version="0.0.1",
                packages=["pluginrepo"],
                package_dir={"": "src"},
                install_requires=[f"sharedpkg @ file://{sibling}"],
            )
            """
        ),
        encoding="utf-8",
    )
    (plugin_pkg / "__init__.py").write_text("", encoding="utf-8")
    (plugin_pkg / "tool_mod.py").write_text(
        textwrap.dedent(
            """
            from sharedpkg import VALUE

            class DependentTool:
                name = "dependent_tool"

                def init(self, config):
                    return {"config": config}

                def get_tool_schemas(self, state):
                    return [{"type": "function", "function": {"name": "show_value", "parameters": {"type": "object", "properties": {}}}}]

                def execute_tool(self, tool_name, arguments, state):
                    return {"success": True, "result": VALUE}

                def format_tool_result(self, result, state):
                    return str(result["result"])
            """
        ),
        encoding="utf-8",
    )

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)

    spec = {"path": str(plugin), "entry": "pluginrepo.tool_mod.DependentTool"}
    mgr = PluginManager(cache_dir=cache_dir, policy={"install_deps": True})
    res = mgr.resolve_all([spec])

    assert res.errors == []
    assert [getattr(cls, "__name__", "") for cls in res.classes] == ["DependentTool"]
    assert res.classes[0]().execute_tool("show_value", {}, {})["result"] == 7
