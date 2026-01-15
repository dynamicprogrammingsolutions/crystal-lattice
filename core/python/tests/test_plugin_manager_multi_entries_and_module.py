from __future__ import annotations

from pathlib import Path
import subprocess
import textwrap
import json

from agent_app.plugin_manager import PluginManager


def _fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


def _init_local_git_repo_from_fixtures(tmp_path: Path) -> Path:
    src = _fixtures_dir()
    repo = tmp_path / "repo"
    subprocess.check_call(["git", "init"], cwd=str(tmp_path))
    # Copy tree
    subprocess.check_call(["bash", "-lc", f"cp -R '{src}' '{repo}'"])
    (repo / "setup.py").write_text(
        "from setuptools import setup\nsetup(name='dev_plugins', version='0.0.1', packages=['dev_plugins'])",
        encoding="utf-8",
    )
    subprocess.check_call(["git", "init"], cwd=str(repo))
    subprocess.check_call(["git", "add", "."], cwd=str(repo))
    subprocess.check_call([
        "git",
        "-c",
        "user.email=test@example.com",
        "-c",
        "user.name=Test User",
        "commit",
        "-m",
        "init",
    ], cwd=str(repo))
    return repo


def test_localpath_entries_list(tmp_path: Path) -> None:
    mgr = PluginManager(cache_dir=tmp_path)
    fixtures = _fixtures_dir()
    spec = {
        "path": str(fixtures),
        "entries": [
            "dev_plugins.file_reader_tool.FileReaderTool",
            "dev_plugins.file_writer_tool.FileWriterTool",
        ],
    }
    core_kinds, app_classes, errors = mgr.load_plugins([{"spec": spec, "kind": None}])
    assert errors == []
    tools = [cls.__name__ for cls in core_kinds.get("tools", [])]
    assert set(tools) >= {"FileReaderTool", "FileWriterTool"}


def test_localpath_module_only_module(tmp_path: Path) -> None:
    mgr = PluginManager(cache_dir=tmp_path)
    fixtures = _fixtures_dir()
    spec = {
        "path": str(fixtures),
        "entry": "dev_plugins.file_reader_tool",
    }
    core_kinds, app_classes, errors = mgr.load_plugins([{"spec": spec, "kind": None}])
    assert errors == []
    tools = [cls.__name__ for cls in core_kinds.get("tools", [])]
    assert "FileReaderTool" in tools


def test_git_entries_list(tmp_path: Path) -> None:
    repo = _init_local_git_repo_from_fixtures(tmp_path)
    mgr = PluginManager(cache_dir=tmp_path)
    spec = {
        "git": str(repo),
        "entries": [
            "dev_plugins.file_reader_tool.FileReaderTool",
            "dev_plugins.file_writer_tool.FileWriterTool",
        ],
    }
    core_kinds, app_classes, errors = mgr.load_plugins([{"spec": spec, "kind": None}])
    assert errors == []
    tools = [cls.__name__ for cls in core_kinds.get("tools", [])]
    assert set(tools) >= {"FileReaderTool", "FileWriterTool"}


def test_git_module_only_with_descriptor(tmp_path: Path) -> None:
    repo = _init_local_git_repo_from_fixtures(tmp_path)
    # write descriptor
    (repo / "agent_plugin.json").write_text(
        json.dumps(
            {
                "entries": [
                    "dev_plugins.file_reader_tool.FileReaderTool",
                    "dev_plugins.file_writer_tool.FileWriterTool",
                ]
            }
        ),
        encoding="utf-8",
    )
    subprocess.check_call(["git", "add", "."], cwd=str(repo))
    subprocess.check_call([
        "git",
        "-c",
        "user.email=test@example.com",
        "-c",
        "user.name=Test User",
        "commit",
        "-m",
        "descriptor",
    ], cwd=str(repo))

    mgr = PluginManager(cache_dir=tmp_path)
    spec = {
        "git": str(repo),
        "entry": "dev_plugins",
    }
    core_kinds, app_classes, errors = mgr.load_plugins([{"spec": spec, "kind": None}])
    assert errors == []
    tools = [cls.__name__ for cls in core_kinds.get("tools", [])]
    assert set(tools) >= {"FileReaderTool", "FileWriterTool"}
