"""Integration test for GitInstallerSource using a local git repo.

This test creates a minimal Python package, commits it to a local git repo,
then uses the PluginManager to install it into a cache directory and import
the declared plugin entry.
"""

from __future__ import annotations

from pathlib import Path
import textwrap
import subprocess
import sys
import json

import pytest

from agent_app.plugin_manager import PluginManager


def _init_local_git_repo(repo: Path) -> str:
    repo.mkdir(parents=True, exist_ok=True)
    # Minimal legacy setup.py package to avoid needing a build backend config
    (repo / "setup.py").write_text(
        textwrap.dedent(
            """
            from setuptools import setup
            setup(name='mydevplugin', version='0.0.1', packages=['mydevplugin'])
            """
        ),
        encoding="utf-8",
    )
    pkg = repo / "mydevplugin"
    pkg.mkdir(exist_ok=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "provider_mod.py").write_text(
        textwrap.dedent(
            """
            class GitDevProvider:
                name = "git_dev_provider"

                def init(self, config):
                    return {}

                def call_api(self, native_messages, state):
                    return [], [], [], state
            """
        ),
        encoding="utf-8",
    )
    # Initialize git and commit
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
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo)).decode().strip()
    return commit


@pytest.mark.integration
def test_git_installer_installs_and_imports(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    commit = _init_local_git_repo(repo)

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    entry = "mydevplugin.provider_mod.GitDevProvider"
    spec = f"git+{repo}::{entry}"
    mgr = PluginManager(cache_dir=cache_dir)

    # Load via plugins config path (providers list)
    sections, errors = mgr.load_plugins_config({"providers": [spec]})
    assert errors == []
    assert len(sections["providers"]) == 1
    cls = sections["providers"][0]
    assert getattr(cls, "__name__", "") == "GitDevProvider"

    # Verify cache directory exists and metadata recorded
    # safe id derived from repo dir name 'repo'
    install_dir = cache_dir / f"repo@{commit}"
    assert install_dir.exists()
    meta_path = install_dir / "plugin_metadata.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta.get("commit") == commit
    assert meta.get("entry") == entry
