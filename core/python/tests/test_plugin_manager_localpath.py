"""Tests for application-level PluginManager local path support.

Local path repos are installed into the plugin cache via
`pip install --target ...`, then loaded from the installed target.
"""

from __future__ import annotations

from pathlib import Path
import importlib
import subprocess
import sys
import textwrap

from agent_app.plugin_sources.install import InstallRequest, PipTargetInstallStrategy
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
    mgr = PluginManager(cache_dir=cache_dir)
    res = mgr.resolve_all([spec])

    assert res.errors == []
    assert [getattr(cls, "__name__", "") for cls in res.classes] == ["DependentTool"]
    assert res.classes[0]().execute_tool("show_value", {}, {})["result"] == 7
    installed = next(cache_dir.glob("pluginrepo@*"))
    assert (installed / "sharedpkg").is_dir()


def test_activate_sys_path_gives_precedence_to_latest_install(tmp_path: Path) -> None:
    older = tmp_path / "older"
    newer = tmp_path / "newer"
    for base, value in ((older, "old"), (newer, "new")):
        pkg = base / "shadowpkg"
        pkg.mkdir(parents=True, exist_ok=True)
        (pkg / "__init__.py").write_text(f"VALUE = {value!r}\n", encoding="utf-8")

    installer = PipTargetInstallStrategy()
    original_sys_path = list(sys.path)
    original_module = sys.modules.pop("shadowpkg", None)
    try:
        installer._activate_sys_path(older)
        import shadowpkg  # type: ignore[import-not-found]

        assert shadowpkg.VALUE == "old"

        installer._activate_sys_path(newer)
        assert "shadowpkg" not in sys.modules
        shadowpkg = importlib.import_module("shadowpkg")
        assert shadowpkg.VALUE == "new"
        assert sys.path[0] == str(newer)
    finally:
        sys.path[:] = original_sys_path
        if original_module is not None:
            sys.modules["shadowpkg"] = original_module
        else:
            sys.modules.pop("shadowpkg", None)


def test_activate_sys_path_evicts_stale_imported_modules(tmp_path: Path) -> None:
    older = tmp_path / "older"
    newer = tmp_path / "newer"
    for base, value in ((older, "old"), (newer, "new")):
        pkg = base / "shadowpkg"
        dist = base / f"shadowpkg-{value}.dist-info"
        pkg.mkdir(parents=True, exist_ok=True)
        dist.mkdir(parents=True, exist_ok=True)
        (pkg / "__init__.py").write_text(f"VALUE = {value!r}\n", encoding="utf-8")
        (pkg / "sub.py").write_text(f"VALUE = {value!r}\n", encoding="utf-8")
        (dist / "top_level.txt").write_text("shadowpkg\n", encoding="utf-8")

    installer = PipTargetInstallStrategy()
    original_sys_path = list(sys.path)
    original_shadowpkg = sys.modules.pop("shadowpkg", None)
    original_shadowpkg_sub = sys.modules.pop("shadowpkg.sub", None)
    try:
        installer._activate_sys_path(older)
        import shadowpkg  # type: ignore[import-not-found]
        import shadowpkg.sub  # type: ignore[import-not-found]

        assert shadowpkg.VALUE == "old"
        assert shadowpkg.sub.VALUE == "old"

        installer._activate_sys_path(newer)

        assert "shadowpkg" not in sys.modules
        assert "shadowpkg.sub" not in sys.modules

        import shadowpkg as reimported_shadowpkg  # type: ignore[import-not-found]
        import shadowpkg.sub as reimported_shadowpkg_sub  # type: ignore[import-not-found]

        assert reimported_shadowpkg.VALUE == "new"
        assert reimported_shadowpkg_sub.VALUE == "new"
    finally:
        sys.path[:] = original_sys_path
        if original_shadowpkg is not None:
            sys.modules["shadowpkg"] = original_shadowpkg
        else:
            sys.modules.pop("shadowpkg", None)
        if original_shadowpkg_sub is not None:
            sys.modules["shadowpkg.sub"] = original_shadowpkg_sub
        else:
            sys.modules.pop("shadowpkg.sub", None)


def test_bundled_localpath_source_activates_source_tree_without_pip(
    tmp_path: Path, monkeypatch
) -> None:
    bundled_root = tmp_path / "bundled_plugins"
    plugin = bundled_root / "pluginrepo"
    shared = bundled_root / "sharedpkg"
    plugin_pkg = plugin / "src" / "pluginrepo"
    shared_pkg = shared / "src" / "sharedpkg"
    plugin_pkg.mkdir(parents=True, exist_ok=True)
    shared_pkg.mkdir(parents=True, exist_ok=True)
    (plugin / "pyproject.toml").write_text("", encoding="utf-8")
    (shared / "pyproject.toml").write_text("", encoding="utf-8")
    (plugin_pkg / "__init__.py").write_text("", encoding="utf-8")
    (shared_pkg / "__init__.py").write_text("VALUE = 11\n", encoding="utf-8")

    installer = PipTargetInstallStrategy()
    original_sys_path = list(sys.path)
    monkeypatch.setenv("BUILTIN_PLUGINS", str(bundled_root))

    try:
        install_dir = installer.ensure_installed(
            InstallRequest(
                cache_dir=tmp_path / "cache",
                safe_id="pluginrepo",
                revision="rev",
                project_dir=plugin,
                policy={},
                metadata={},
            )
        )

        assert install_dir == plugin.resolve()
        assert str(plugin / "src") in sys.path
        assert str(shared / "src") in sys.path
        assert not (tmp_path / "cache").exists()
    finally:
        sys.path[:] = original_sys_path


def test_non_bundled_builtin_plugins_path_still_installs_to_cache(
    tmp_path: Path, monkeypatch
) -> None:
    repo = _make_dev_repo(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    monkeypatch.setenv("BUILTIN_PLUGINS", str(repo.parent))

    spec = {"path": str(repo), "entry": "myplugins.provider_mod.DevProvider"}
    mgr = PluginManager(cache_dir=cache_dir)
    res = mgr.resolve_all([spec])

    assert res.errors == []
    assert next(cache_dir.glob("repo@*")).is_dir()


def test_plugin_manager_defaults_pip_cache_next_to_plugins_cache(tmp_path: Path) -> None:
    mgr = PluginManager(cache_dir=tmp_path / ".plugin_cache" / "plugins")

    assert mgr.policy["pip_cache_dir"] == str(tmp_path / ".plugin_cache" / "pip")


def test_pip_target_installer_uses_configured_pip_cache_dir(tmp_path: Path, monkeypatch) -> None:
    project_dir = _make_dev_repo(tmp_path)
    cache_dir = tmp_path / ".plugin_cache" / "plugins"
    pip_cache_dir = tmp_path / ".plugin_cache" / "pip"
    commands: list[list[str]] = []
    original_sys_path = list(sys.path)

    def fake_check_call(cmd):  # type: ignore[no-untyped-def]
        commands.append(list(cmd))
        return 0

    monkeypatch.setattr(subprocess, "check_call", fake_check_call)
    try:
        PipTargetInstallStrategy().ensure_installed(
            InstallRequest(
                cache_dir=cache_dir,
                safe_id="repo",
                revision="rev",
                project_dir=project_dir,
                policy={"pip_cache_dir": str(pip_cache_dir)},
                metadata={},
            )
        )
    finally:
        sys.path[:] = original_sys_path

    assert commands
    assert "--cache-dir" in commands[0]
    assert commands[0][commands[0].index("--cache-dir") + 1] == str(pip_cache_dir)
    assert "--no-cache-dir" not in commands[0]
