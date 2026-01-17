from __future__ import annotations

from pathlib import Path
import subprocess
import json
import shutil

from agent_app.plugin_manager import PluginManager
import sys


def _fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


def _init_local_git_repo_from_fixtures(tmp_path: Path) -> Path:
    src = _fixtures_dir()
    repo = tmp_path / "repo"
    subprocess.check_call(["git", "init"], cwd=str(tmp_path))
    # Copy tree (fixtures/dev_plugins and configs if present)
    shutil.copytree(src, repo, dirs_exist_ok=True)
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
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
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
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
    fixtures = _fixtures_dir()
    spec = {
        "path": str(fixtures),
        "entry": "dev_plugins.file_reader_tool",
    }
    core_kinds, app_classes, errors = mgr.load_plugins([{"spec": spec, "kind": None}])
    assert errors == []
    tools = [cls.__name__ for cls in core_kinds.get("tools", [])]
    assert "FileReaderTool" in tools


def test_localpath_module_only_string_dotted(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
    fixtures = _fixtures_dir()
    spec = f"path:{fixtures}::dev_plugins.file_reader_tool"
    core_kinds, app_classes, errors = mgr.load_plugins([{"spec": spec, "kind": None}])
    assert errors == []
    tools = [cls.__name__ for cls in core_kinds.get("tools", [])]
    assert "FileReaderTool" in tools


def test_git_entries_list(tmp_path: Path) -> None:
    repo = _init_local_git_repo_from_fixtures(tmp_path)
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
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


def test_git_module_only_string_dotted(tmp_path: Path) -> None:
    repo = _init_local_git_repo_from_fixtures(tmp_path)
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
    spec = f"git+{repo}::dev_plugins.file_reader_tool"
    core_kinds, app_classes, errors = mgr.load_plugins([{"spec": spec, "kind": None}])
    assert errors == []
    tools = [cls.__name__ for cls in core_kinds.get("tools", [])]
    assert "FileReaderTool" in tools


def test_git_module_only_with_descriptor(tmp_path: Path) -> None:
    repo = _init_local_git_repo_from_fixtures(tmp_path)
    # Add an extra tool that should be excluded when descriptor entries are used.
    (repo / "dev_plugins" / "extra_tool.py").write_text(
        """\
class ExtraTool:\n    name = 'extra_tool'\n\n    def get_tool_schemas(self, state):\n        return []\n\n    def execute_tool(self, tool_name, arguments, state):\n        return {}\n""",
        encoding="utf-8",
    )

    # Write descriptor at repo root and ensure setup.py installs it as a top-level data file.
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
    (repo / "setup.py").write_text(
        "from setuptools import setup\nsetup(name='dev_plugins', version='0.0.1', packages=['dev_plugins'], data_files=[('', ['agent_plugin.json'])])\n",
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

    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
    spec = {
        "git": str(repo),
        "entry": "dev_plugins",
    }
    core_kinds, app_classes, errors = mgr.load_plugins([{"spec": spec, "kind": None}])
    assert errors == []
    tools = [cls.__name__ for cls in core_kinds.get("tools", [])]
    assert set(tools) == {"FileReaderTool", "FileWriterTool"}


def test_git_remote_disallowed_by_default(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
    spec = {"git": "https://example.com/repo.git", "entry": "dev_plugins"}
    core_kinds, app_classes, errors = mgr.load_plugins([{"spec": spec, "kind": None}])
    assert errors, "expected error for remote git without allow_remote policy"
    assert any(e.get("type") == "plugin_install_error" for e in errors)


def test_localpath_discovery_excludes_non_plugins(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
    fixtures = _fixtures_dir()
    # Ensure path is appended during test
    spec = {"path": str(fixtures), "entry": "dev_plugins"}
    core_kinds, app_classes, errors = mgr.load_plugins([{"spec": spec, "kind": None}])
    assert errors == []
    # Collect all discovered class names
    names = set()
    for kind_list in core_kinds.values():
        names.update(cls.__name__ for cls in kind_list)
    assert "NotAPlugin" not in names


def test_localpath_sys_path_append_policy(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
    fixtures = _fixtures_dir()
    p = str(fixtures)
    # Remove if present for deterministic assertion
    try:
        while p in sys.path:
            sys.path.remove(p)
    except ValueError:
        pass
    before = list(sys.path)
    spec = {"path": p, "entries": ["dev_plugins.file_reader_tool.FileReaderTool"]}
    core_kinds, app_classes, errors = mgr.load_plugins([{"spec": spec, "kind": None}])
    assert errors == []
    assert sys.path[-1] != p, "expected local path to be installed, not appended"
    assert str(cache_dir) in sys.path[-1], "expected sys.path to include cache install dir"
    assert sys.path[0] == before[0], "should not prepend path"


def test_localpath_module_only_with_descriptor(tmp_path: Path) -> None:
    # Copy fixtures to a temp dir and add agent_plugin.json
    src = _fixtures_dir()
    dst = tmp_path / "local_plugins"
    shutil.copytree(src, dst, dirs_exist_ok=True)
    (dst / "dev_plugins" / "extra_tool.py").write_text(
        """\
class ExtraTool:\n    name = 'extra_tool'\n\n    def get_tool_schemas(self, state):\n        return []\n\n    def execute_tool(self, tool_name, arguments, state):\n        return {}\n""",
        encoding="utf-8",
    )
    (dst / "agent_plugin.json").write_text(
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
    (dst / "setup.py").write_text(
        "from setuptools import setup\nsetup(name='dev_plugins', version='0.0.1', packages=['dev_plugins'], data_files=[('', ['agent_plugin.json'])])\n",
        encoding="utf-8",
    )
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
    spec = {"path": str(dst), "entry": "dev_plugins"}
    core_kinds, app_classes, errors = mgr.load_plugins([{"spec": spec, "kind": None}])
    assert errors == []
    tools = [cls.__name__ for cls in core_kinds.get("tools", [])]
    assert set(tools) == {"FileReaderTool", "FileWriterTool"}
