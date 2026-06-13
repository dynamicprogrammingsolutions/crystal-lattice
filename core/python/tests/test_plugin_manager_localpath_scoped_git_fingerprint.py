from __future__ import annotations

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import List

import pytest

from agent_app.plugin_manager import PluginManager
from agent_app.plugin_sources.local_path import LocalPathRepoSource


class _RecordingInstaller:
    def __init__(self) -> None:
        self.requests = []
        self._sys_paths_added: List[str] = []

    def ensure_installed(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        install_dir = request.cache_dir / f"{request.safe_id}@{request.revision}"
        if not install_dir.exists():
            shutil.copytree(request.project_dir, install_dir, dirs_exist_ok=True)
            (install_dir / "plugin_metadata.json").write_text(
                json.dumps(request.metadata), encoding="utf-8"
            )

        install_dir_str = str(install_dir)
        try:
            sys.path.remove(install_dir_str)
        except ValueError:
            pass
        sys.path.insert(0, install_dir_str)
        if install_dir_str not in self._sys_paths_added:
            self._sys_paths_added.append(install_dir_str)
        return install_dir

    def cleanup(self) -> None:
        for item in self._sys_paths_added:
            try:
                sys.path.remove(item)
            except ValueError:
                pass


def _git_commit(repo_root: Path, message: str) -> str:
    subprocess.check_call(["git", "add", "."], cwd=str(repo_root))
    subprocess.check_call(
        [
            "git",
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test User",
            "commit",
            "-m",
            message,
        ],
        cwd=str(repo_root),
    )
    return (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_root)).decode().strip()
    )


def test_localpath_git_fingerprint_scoped_to_project_dir(tmp_path: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git is not installed")

    repo_root = tmp_path / "repo"
    plugin_dir = repo_root / "pluginA"
    other_dir = repo_root / "other"
    pkg_name = "scoped_dev_plugin"

    plugin_pkg = plugin_dir / pkg_name
    plugin_pkg.mkdir(parents=True, exist_ok=True)
    (plugin_pkg / "__init__.py").write_text("", encoding="utf-8")
    (plugin_pkg / "tool_mod.py").write_text(
        textwrap.dedent(
            """
            class MyTool:
                name = "my_tool"

                def init(self, config):
                    return {}

                def get_tool_schemas(self, state):
                    return []
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (plugin_dir / "setup.py").write_text(
        textwrap.dedent(
            f"""
            from setuptools import setup

            setup(name='{pkg_name}', version='0.0.1', packages=['{pkg_name}'])
            """
        ).lstrip(),
        encoding="utf-8",
    )

    other_dir.mkdir(parents=True, exist_ok=True)
    (other_dir / "unrelated.txt").write_text("unrelated", encoding="utf-8")

    subprocess.check_call(["git", "init"], cwd=str(repo_root))
    _git_commit(repo_root, "init")

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    installer = _RecordingInstaller()
    try:
        mgr = PluginManager(
            cache_dir=cache_dir,
            sources=[LocalPathRepoSource(installer=installer)],
        )
        entry = f"{pkg_name}.tool_mod.MyTool"
        spec = {"path": str(repo_root), "subdirectory": "pluginA", "entry": entry}

        res1 = mgr.resolve_all([spec])
        assert res1.errors == []
        assert len(installer.requests) == 1
        rev1 = installer.requests[-1].revision

        # Commit that does not touch the plugin directory should not change revision.
        (other_dir / "unrelated.txt").write_text("changed", encoding="utf-8")
        _git_commit(repo_root, "unrelated change")
        res2 = mgr.resolve_all([spec])
        assert res2.errors == []
        rev2 = installer.requests[-1].revision
        assert rev2 == rev1

        # Working tree change under the plugin directory should change revision.
        (plugin_pkg / "tool_mod.py").write_text(
            (plugin_pkg / "tool_mod.py").read_text(encoding="utf-8") + "\n# local change\n",
            encoding="utf-8",
        )
        res3 = mgr.resolve_all([spec])
        assert res3.errors == []
        rev3 = installer.requests[-1].revision
        assert rev3 != rev1

        # Committed change under the plugin directory should change revision.
        _git_commit(repo_root, "plugin change")
        res4 = mgr.resolve_all([spec])
        assert res4.errors == []
        rev4 = installer.requests[-1].revision
        assert rev4 != rev2
    finally:
        installer.cleanup()


def test_localpath_git_fingerprint_includes_declared_sibling_dependency(
    tmp_path: Path,
) -> None:
    if shutil.which("git") is None:
        pytest.skip("git is not installed")

    repo_root = tmp_path / "repo"
    plugin_dir = repo_root / "qwen-tools"
    shared_dir = repo_root / "tool-compat-shared"
    pkg_name = "dep_fingerprint_plugin"
    plugin_pkg = plugin_dir / pkg_name
    shared_pkg = shared_dir / "src" / "tool_compat_shared"
    plugin_pkg.mkdir(parents=True, exist_ok=True)
    shared_pkg.mkdir(parents=True, exist_ok=True)
    (plugin_pkg / "__init__.py").write_text("", encoding="utf-8")
    (plugin_pkg / "tool_mod.py").write_text(
        textwrap.dedent(
            """
            class MyTool:
                name = "my_tool"

                def init(self, config):
                    return {}

                def get_tool_schemas(self, state):
                    return []
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (plugin_dir / "setup.py").write_text(
        textwrap.dedent(
            """
            from pathlib import Path
            from setuptools import setup

            sibling = (Path(__file__).resolve().parents[1] / "tool-compat-shared").resolve()

            setup(
                name="qwen-tools",
                version="0.0.1",
                packages=["dep_fingerprint_plugin"],
                install_requires=[f"tool-compat-shared @ file://{sibling}"],
            )
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (plugin_dir / "agent_plugin.json").write_text(
        json.dumps(
            {
                "entries": [f"{pkg_name}.tool_mod.MyTool"],
                "local_workspace_dependencies": [
                    {"name": "tool-compat-shared", "path": "../tool-compat-shared"},
                ],
            }
        ),
        encoding="utf-8",
    )
    (shared_dir / "pyproject.toml").write_text(
        textwrap.dedent(
            """
            [build-system]
            requires = ["setuptools>=61.0", "wheel"]
            build-backend = "setuptools.build_meta"

            [project]
            name = "tool-compat-shared"
            version = "0.0.1"

            [tool.setuptools]
            package-dir = {"" = "src"}

            [tool.setuptools.packages.find]
            where = ["src"]
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (shared_pkg / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")

    subprocess.check_call(["git", "init"], cwd=str(repo_root))
    _git_commit(repo_root, "init")

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    installer = _RecordingInstaller()
    try:
        mgr = PluginManager(
            cache_dir=cache_dir,
            sources=[LocalPathRepoSource(installer=installer)],
        )
        spec = {
            "path": str(plugin_dir),
            "entry": f"{pkg_name}.tool_mod.MyTool",
        }

        res1 = mgr.resolve_all([spec])
        assert res1.errors == []
        assert len(installer.requests) == 2
        assert installer.requests[-2].safe_id == "tool-compat-shared"
        assert installer.requests[-1].safe_id == "qwen-tools"
        rev1 = installer.requests[-1].revision
        assert "tool-compat-shared" in installer.requests[-1].metadata["local_dependencies"]
        assert (
            installer.requests[-1]
            .metadata["local_workspace_dependencies"]["tool-compat-shared"]["revision"]
            == installer.requests[-2].revision
        )
        assert "local_dependency_versions" not in installer.requests[-1].metadata
        assert installer.requests[-1].policy["pip_cache_dir"] == str(cache_dir / "pip")
        assert "--no-cache-dir" not in installer.requests[-1].policy.get("pip_args", [])

        (shared_pkg / "__init__.py").write_text("VALUE = 2\n", encoding="utf-8")
        res2 = mgr.resolve_all([spec])
        assert res2.errors == []
        rev2 = installer.requests[-1].revision

        assert rev2 != rev1
    finally:
        installer.cleanup()


def test_localpath_file_dependency_requires_descriptor_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    plugin_dir = repo_root / "qwen-tools"
    shared_dir = repo_root / "tool-compat-shared"
    pkg_name = "missing_dep_metadata_plugin"
    plugin_pkg = plugin_dir / pkg_name
    shared_pkg = shared_dir / "src" / "tool_compat_shared"
    plugin_pkg.mkdir(parents=True, exist_ok=True)
    shared_pkg.mkdir(parents=True, exist_ok=True)
    (plugin_pkg / "__init__.py").write_text("", encoding="utf-8")
    (plugin_pkg / "tool_mod.py").write_text(
        textwrap.dedent(
            """
            class MyTool:
                name = "my_tool"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (plugin_dir / "setup.py").write_text(
        textwrap.dedent(
            """
            from pathlib import Path
            from setuptools import setup

            sibling = (Path(__file__).resolve().parents[1] / "tool-compat-shared").resolve()

            setup(
                name="qwen-tools",
                version="0.0.1",
                packages=["missing_dep_metadata_plugin"],
                install_requires=[f"tool-compat-shared @ file://{sibling}"],
            )
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (plugin_dir / "agent_plugin.json").write_text(
        json.dumps({"entries": [f"{pkg_name}.tool_mod.MyTool"]}),
        encoding="utf-8",
    )
    (shared_dir / "pyproject.toml").write_text(
        textwrap.dedent(
            """
            [build-system]
            requires = ["setuptools>=61.0", "wheel"]
            build-backend = "setuptools.build_meta"

            [project]
            name = "tool-compat-shared"
            version = "0.0.1"
            """
        ).lstrip(),
        encoding="utf-8",
    )

    mgr = PluginManager(
        cache_dir=tmp_path / "cache",
        sources=[LocalPathRepoSource()],
    )
    res = mgr.resolve_all([{"path": str(plugin_dir), "entry": f"{pkg_name}.tool_mod.MyTool"}])

    assert res.classes == []
    assert res.errors
    assert res.errors[0]["type"] == "plugin_descriptor_invalid"
    assert "local_workspace_dependencies" in res.errors[0]["detail"]
