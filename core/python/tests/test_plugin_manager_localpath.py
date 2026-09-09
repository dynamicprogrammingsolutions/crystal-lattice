"""Tests for application-level PluginManager local path support.

Local path repos are installed into the plugin cache via
`pip install --target ...`, then loaded from the installed target.
"""

from __future__ import annotations

import json
from pathlib import Path
import importlib
import subprocess
import sys
import textwrap

from agent_app.plugin_sources.install import (
    InstallRequest,
    PipTargetInstallStrategy,
    PluginInstallError,
)
from agent_app.plugin_sources.descriptor import read_descriptor
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


def test_descriptor_reads_local_workspace_dependencies(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "agent_plugin.json").write_text(
        json.dumps(
            {
                "entries": ["pkg.mod.Plugin"],
                "local_workspace_dependencies": [
                    {"name": "sharedpkg", "path": "../sharedpkg"},
                ],
            }
        ),
        encoding="utf-8",
    )

    descriptor, error = read_descriptor(repo)

    assert error is None
    assert descriptor is not None
    assert descriptor.local_workspace_dependencies[0].name == "sharedpkg"
    assert descriptor.local_workspace_dependencies[0].path == "../sharedpkg"


def test_localpath_manifest_preinstalled_imports_without_cache_install(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "runtime" / "plugins" / "pluginrepo"
    pkg = tmp_path / "site" / "pluginrepo"
    repo.mkdir(parents=True, exist_ok=True)
    pkg.mkdir(parents=True, exist_ok=True)
    (repo / "agent_plugin.json").write_text(
        json.dumps({"entries": ["pluginrepo.tool_mod.ManifestTool"]}),
        encoding="utf-8",
    )
    (repo / "pyproject.toml").write_text(
        "from setuptools import setup\n", encoding="utf-8"
    )
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "tool_mod.py").write_text(
        "class ManifestTool:\n    pass\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "runtime" / "preinstalled-plugins.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "plugins": [{"name": "pluginrepo", "path": "plugins/pluginrepo"}],
            }
        ),
        encoding="utf-8",
    )

    sys.path.insert(0, str(tmp_path / "site"))
    try:
        mgr = PluginManager(
            cache_dir=tmp_path / "cache",
            policy={"preinstalled_plugin_manifest": str(manifest)},
        )
        res = mgr.resolve_all([f"path:{repo}"])
    finally:
        sys.path.remove(str(tmp_path / "site"))
        sys.modules.pop("pluginrepo", None)
        sys.modules.pop("pluginrepo.tool_mod", None)

    assert res.errors == []
    assert [getattr(cls, "__name__", "") for cls in res.classes] == ["ManifestTool"]
    assert not any((tmp_path / "cache").glob("pluginrepo@*"))


def test_descriptor_rejects_malformed_local_workspace_dependencies(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "agent_plugin.json").write_text(
        json.dumps(
            {
                "entries": ["pkg.mod.Plugin"],
                "local_workspace_dependencies": [{"name": "sharedpkg"}],
            }
        ),
        encoding="utf-8",
    )

    descriptor, error = read_descriptor(repo)

    assert descriptor is None
    assert error is not None
    assert error["type"] == "plugin_descriptor_invalid"
    assert "local_workspace_dependencies" in error["detail"]


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
    (plugin / "agent_plugin.json").write_text(
        json.dumps(
            {
                "entries": ["pluginrepo.tool_mod.DependentTool"],
                "local_workspace_dependencies": [
                    {"name": "sharedpkg", "path": "../sharedpkg"},
                ],
            }
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

    spec = f"path:{plugin}"
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


def test_activate_sys_path_evicts_record_discovered_dependency_modules(
    tmp_path: Path,
) -> None:
    host = tmp_path / "host"
    install_dir = tmp_path / "install"
    host_dependency = host / "skew_dependency"
    installed_dependency = install_dir / "skew_dependency"
    installed_plugin = install_dir / "skew_plugin"
    plugin_dist = install_dir / "skew_plugin-1.0.dist-info"
    dependency_dist = install_dir / "skew_dependency-2.0.dist-info"

    host_dependency.mkdir(parents=True)
    installed_dependency.mkdir(parents=True)
    installed_plugin.mkdir(parents=True)
    plugin_dist.mkdir()
    dependency_dist.mkdir()

    (host_dependency / "__init__.py").write_text(
        "VERSION = 'host-old'\n", encoding="utf-8"
    )
    (host_dependency / "submodule.py").write_text(
        "VERSION = 'host-old'\n", encoding="utf-8"
    )
    (installed_dependency / "__init__.py").write_text(
        "VERSION = 'cache-new'\nNEW_API = object()\n", encoding="utf-8"
    )
    (installed_dependency / "submodule.py").write_text(
        "VERSION = 'cache-new'\n", encoding="utf-8"
    )
    (installed_plugin / "__init__.py").write_text(
        "from skew_dependency import NEW_API\n", encoding="utf-8"
    )
    (plugin_dist / "top_level.txt").write_text("skew_plugin\n", encoding="utf-8")
    (dependency_dist / "RECORD").write_text(
        "\n".join(
            [
                "skew_dependency/__init__.py,,",
                "skew_dependency/submodule.py,,",
                "skew_dependency-2.0.dist-info/METADATA,,",
                "skew_dependency-2.0.dist-info/RECORD,,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    installer = PipTargetInstallStrategy()
    original_sys_path = list(sys.path)
    original_modules = {
        name: sys.modules.pop(name, None)
        for name in (
            "skew_dependency",
            "skew_dependency.submodule",
            "skew_plugin",
        )
    }
    try:
        sys.path.insert(0, str(host))
        host_module = importlib.import_module("skew_dependency")
        host_submodule = importlib.import_module("skew_dependency.submodule")
        assert host_module.VERSION == "host-old"
        assert host_submodule.VERSION == "host-old"

        installer._activate_sys_path(install_dir)

        assert "skew_dependency" not in sys.modules
        assert "skew_dependency.submodule" not in sys.modules
        plugin_module = importlib.import_module("skew_plugin")
        dependency_module = importlib.import_module("skew_dependency")
        dependency_submodule = importlib.import_module("skew_dependency.submodule")
        assert plugin_module.NEW_API is dependency_module.NEW_API
        assert dependency_module.VERSION == "cache-new"
        assert dependency_submodule.VERSION == "cache-new"

        installer._activate_sys_path(install_dir)

        assert sys.modules["skew_dependency"] is dependency_module
        assert sys.modules["skew_dependency.submodule"] is dependency_submodule
        assert sys.modules["skew_plugin"] is plugin_module
    finally:
        sys.path[:] = original_sys_path
        for name, module in original_modules.items():
            if module is not None:
                sys.modules[name] = module
            else:
                sys.modules.pop(name, None)


def test_top_level_discovery_uses_each_distributions_metadata(tmp_path: Path) -> None:
    install_dir = tmp_path / "install"
    install_dir.mkdir()
    plugin_dist = install_dir / "plugin_dist-1.0.dist-info"
    module_dependency_dist = install_dir / "module_dependency-1.0.dist-info"
    package_dependency_dist = install_dir / "package_dependency-1.0.dist-info"
    unusable_dist = install_dir / "unusable_dist-1.0.dist-info"
    for dist_info in (
        plugin_dist,
        module_dependency_dist,
        package_dependency_dist,
        unusable_dist,
    ):
        dist_info.mkdir()

    (install_dir / "plugin_package").mkdir()
    (install_dir / "module_dependency.py").write_text("", encoding="utf-8")
    package_dependency = install_dir / "package_dependency"
    package_dependency.mkdir()
    (package_dependency / "__init__.py").write_text("", encoding="utf-8")
    (install_dir / "fallback_package").mkdir()

    (plugin_dist / "top_level.txt").write_text(
        "plugin_package\nnot-a-module\n", encoding="utf-8"
    )
    (module_dependency_dist / "RECORD").write_text(
        "module_dependency.py,,\n" "module_dependency-1.0.dist-info/RECORD,,\n",
        encoding="utf-8",
    )
    (package_dependency_dist / "RECORD").write_text(
        "package_dependency/__init__.py,,\n"
        "package_dependency/data.json,,\n"
        "../outside.py,,\n",
        encoding="utf-8",
    )

    discovered = PipTargetInstallStrategy()._top_level_modules_for_install_dir(
        install_dir
    )

    assert discovered == {
        "fallback_package",
        "module_dependency",
        "package_dependency",
        "plugin_package",
    }


def test_non_preinstalled_bundled_localpath_source_installs_to_cache(
    tmp_path: Path, monkeypatch
) -> None:
    bundled_root = tmp_path / "bundled_plugins"
    plugin = bundled_root / "pluginrepo"
    plugin_pkg = plugin / "src" / "pluginrepo"
    plugin_pkg.mkdir(parents=True, exist_ok=True)
    (plugin / "pyproject.toml").write_text(
        textwrap.dedent(
            """
            [build-system]
            requires = ["setuptools>=61.0", "wheel"]
            build-backend = "setuptools.build_meta"

            [project]
            name = "pluginrepo"
            version = "0.0.1"

            [tool.setuptools]
            package-dir = {"" = "src"}

            [tool.setuptools.packages.find]
            where = ["src"]
            """
        ),
        encoding="utf-8",
    )
    (plugin_pkg / "__init__.py").write_text("", encoding="utf-8")
    (plugin_pkg / "tool_mod.py").write_text(
        textwrap.dedent(
            """
            class BundledTool:
                name = "bundled_tool"

                def init(self, config):
                    return {}

                def get_tool_schemas(self, state):
                    return []
            """
        ),
        encoding="utf-8",
    )
    (plugin / "agent_plugin.json").write_text(
        json.dumps({"entries": ["pluginrepo.tool_mod.BundledTool"]}),
        encoding="utf-8",
    )

    original_sys_path = list(sys.path)
    monkeypatch.setenv("BUILTIN_PLUGINS", str(bundled_root))

    try:
        mgr = PluginManager(cache_dir=tmp_path / "cache")
        res = mgr.resolve_all([f"path:{plugin}"])

        assert res.errors == []
        assert [getattr(cls, "__name__", "") for cls in res.classes] == ["BundledTool"]
        assert next((tmp_path / "cache").glob("pluginrepo@*")).is_dir()
    finally:
        sys.path[:] = original_sys_path


def test_non_preinstalled_bundled_installer_uses_pip_with_dependencies(
    tmp_path: Path, monkeypatch
) -> None:
    bundled_root = tmp_path / "bundled_plugins"
    plugin = bundled_root / "pluginrepo"
    plugin.mkdir(parents=True)
    (plugin / "pyproject.toml").write_text("", encoding="utf-8")

    cache_dir = tmp_path / "cache"
    commands: list[list[str]] = []
    original_sys_path = list(sys.path)
    monkeypatch.setenv("BUILTIN_PLUGINS", str(bundled_root))

    def fake_check_call(cmd):  # type: ignore[no-untyped-def]
        commands.append(list(cmd))
        target = Path(cmd[cmd.index("--target") + 1])
        target.mkdir(parents=True, exist_ok=True)
        (target / "plugin_metadata.json").write_text("{}", encoding="utf-8")
        return 0

    monkeypatch.setattr(subprocess, "check_call", fake_check_call)

    try:
        install_dir = PipTargetInstallStrategy().ensure_installed(
            InstallRequest(
                cache_dir=cache_dir,
                safe_id="pluginrepo",
                revision="rev",
                project_dir=plugin,
                policy={},
                metadata={},
            )
        )
    finally:
        sys.path[:] = original_sys_path

    assert commands
    assert commands[0][-1] == str(plugin)
    assert "--no-deps" not in commands[0]
    assert install_dir == cache_dir / "pluginrepo@rev"


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


def test_preinstalled_descriptor_imports_without_source_tree(
    tmp_path: Path,
) -> None:
    installed = tmp_path / "installed"
    pkg = installed / "preinstalledpkg"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "tool_mod.py").write_text(
        textwrap.dedent(
            """
            class PreinstalledTool:
                name = "preinstalled_tool"

                def init(self, config):
                    return {}

                def get_tool_schemas(self, state):
                    return []
            """
        ),
        encoding="utf-8",
    )

    bundled_root = tmp_path / "bundled_plugins"
    plugin = bundled_root / "pluginrepo"
    plugin.mkdir(parents=True, exist_ok=True)
    (plugin / "agent_plugin.json").write_text(
        json.dumps(
            {
                "entries": ["preinstalledpkg.tool_mod.PreinstalledTool"],
                "preinstalled": True,
            }
        ),
        encoding="utf-8",
    )

    original_sys_path = list(sys.path)
    try:
        sys.path.insert(0, str(installed))
        mgr = PluginManager(cache_dir=tmp_path / "cache")
        res = mgr.resolve_all([f"path:{plugin}"])
    finally:
        sys.path[:] = original_sys_path

    assert res.errors == []
    assert [getattr(cls, "__name__", "") for cls in res.classes] == ["PreinstalledTool"]
    assert not (tmp_path / "cache").exists()


def test_plugin_manager_defaults_pip_cache_next_to_plugins_cache(
    tmp_path: Path,
) -> None:
    mgr = PluginManager(cache_dir=tmp_path / ".plugin_cache" / "plugins")

    assert mgr.policy["pip_cache_dir"] == str(tmp_path / ".plugin_cache" / "pip")


def test_pip_target_installer_uses_configured_pip_cache_dir(
    tmp_path: Path, monkeypatch
) -> None:
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


def test_pip_target_installer_uses_plugin_python_override_when_frozen(
    tmp_path: Path, monkeypatch
) -> None:
    project_dir = _make_dev_repo(tmp_path)
    cache_dir = tmp_path / ".plugin_cache" / "plugins"
    commands: list[list[str]] = []
    original_sys_path = list(sys.path)

    def fake_check_call(cmd):  # type: ignore[no-untyped-def]
        commands.append(list(cmd))
        return 0

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("CRYSTAL_PLUGIN_PYTHON", "/custom/python")
    monkeypatch.setattr(subprocess, "check_call", fake_check_call)
    try:
        PipTargetInstallStrategy().ensure_installed(
            InstallRequest(
                cache_dir=cache_dir,
                safe_id="repo",
                revision="rev",
                project_dir=project_dir,
                policy={"allow_dynamic_plugin_install": True},
                metadata={},
            )
        )
    finally:
        sys.path[:] = original_sys_path

    assert commands
    assert commands[0][:3] == ["/custom/python", "-m", "pip"]


def test_pip_target_installer_rejects_dynamic_install_in_frozen_runtime(
    tmp_path: Path, monkeypatch
) -> None:
    project_dir = _make_dev_repo(tmp_path)
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    try:
        PipTargetInstallStrategy().ensure_installed(
            InstallRequest(
                cache_dir=tmp_path / ".plugin_cache" / "plugins",
                safe_id="repo",
                revision="rev",
                project_dir=project_dir,
                policy={},
                metadata={},
            )
        )
    except PluginInstallError as exc:
        assert "Dynamic plugin installation is not supported" in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("expected frozen runtime dynamic plugin install rejection")


def test_pip_target_installer_uses_cache_for_local_dependency_metadata(
    tmp_path: Path, monkeypatch
) -> None:
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
                metadata={"local_dependencies": {"sharedpkg": "fingerprint"}},
            )
        )
    finally:
        sys.path[:] = original_sys_path

    assert commands
    assert "--cache-dir" in commands[0]
    assert commands[0][commands[0].index("--cache-dir") + 1] == str(pip_cache_dir)
    assert "--no-cache-dir" not in commands[0]
