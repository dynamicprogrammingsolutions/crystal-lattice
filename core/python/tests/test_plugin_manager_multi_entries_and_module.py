from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import sys

from agent_app.plugin_manager import PluginManager


def _fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


def _make_installable_repo(repo: Path, *, with_descriptor: bool) -> None:
    src = _fixtures_dir() / "dev_plugins"
    shutil.copytree(src, repo / "dev_plugins", dirs_exist_ok=True)

    if with_descriptor:
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
    else:
        (repo / "setup.py").write_text(
            "from setuptools import setup\nsetup(name='dev_plugins', version='0.0.1', packages=['dev_plugins'])\n",
            encoding="utf-8",
        )


def _init_git_repo(repo: Path) -> None:
    subprocess.check_call(["git", "init"], cwd=str(repo))
    subprocess.check_call(["git", "add", "."], cwd=str(repo))
    subprocess.check_call(
        [
            "git",
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test User",
            "commit",
            "-m",
            "init",
        ],
        cwd=str(repo),
    )


def test_localpath_descriptor_driven_shorthand_loads_entries(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    _make_installable_repo(repo, with_descriptor=True)

    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
    res = mgr.resolve_all([f"path:{repo}"])
    assert res.errors == []
    assert {cls.__name__ for cls in res.classes} == {"FileReaderTool", "FileWriterTool"}


def test_localpath_shorthand_requires_descriptor(tmp_path: Path) -> None:
    repo = tmp_path / "repo_no_desc"
    repo.mkdir(parents=True)
    _make_installable_repo(repo, with_descriptor=False)

    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
    res = mgr.resolve_all([f"path:{repo}"])
    assert any(e.get("type") == "plugin_descriptor_missing" for e in res.errors)


def test_localpath_explicit_entry_dict_loads_single_class(tmp_path: Path) -> None:
    repo = tmp_path / "repo_explicit"
    repo.mkdir(parents=True)
    _make_installable_repo(repo, with_descriptor=False)

    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
    res = mgr.resolve_all(
        [
            {
                "path": str(repo),
                "entry": "dev_plugins.file_reader_tool.FileReaderTool",
            }
        ]
    )
    assert res.errors == []
    assert [cls.__name__ for cls in res.classes] == ["FileReaderTool"]


def test_localpath_does_not_append_raw_repo_path_to_sys_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo_sys_path"
    repo.mkdir(parents=True)
    _make_installable_repo(repo, with_descriptor=True)

    raw_repo = str(repo)
    while raw_repo in sys.path:
        sys.path.remove(raw_repo)

    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
    res = mgr.resolve_all([f"path:{repo}"])
    assert res.errors == []
    assert raw_repo not in sys.path
    assert any(str(cache_dir) in p for p in sys.path), "expected installed cache dir on sys.path"


def test_git_descriptor_driven_shorthand_loads_entries(tmp_path: Path) -> None:
    repo = tmp_path / "repo_git"
    repo.mkdir(parents=True)
    _make_installable_repo(repo, with_descriptor=True)
    _init_git_repo(repo)

    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
    res = mgr.resolve_all([f"git+{repo}"])
    assert res.errors == []
    assert {cls.__name__ for cls in res.classes} == {"FileReaderTool", "FileWriterTool"}


def test_git_remote_disallowed_by_default(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir)
    res = mgr.resolve_all(["git+https://example.com/repo.git"])
    assert any(e.get("type") == "plugin_install_error" for e in res.errors)
