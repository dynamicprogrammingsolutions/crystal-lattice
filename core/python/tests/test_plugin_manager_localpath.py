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
