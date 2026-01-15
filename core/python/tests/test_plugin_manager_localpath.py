"""Unit tests for application-level PluginManager and LocalPathSource.

These tests avoid git/pip and validate the local-path development workflow and
manager orchestration for dotted-path and local-path specs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import textwrap

from agent_app.plugin_manager import PluginManager, LocalPathSource
from agent_core.plugin.loader import DottedPathSource


def _make_dev_package(tmp_path: Path) -> str:
    """Create a minimal dev package with a provider plugin class."""

    pkg = tmp_path / "myplugins"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
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
        )
    )
    return str(tmp_path)


def test_localpath_source_loads_provider(tmp_path: Path) -> None:
    base = _make_dev_package(tmp_path)
    spec = f"path:{base}::myplugins.provider_mod.DevProvider"
    mgr = PluginManager(cache_dir=tmp_path, loaders=[LocalPathSource()])

    result = mgr.load_one(spec, kind="providers")
    assert result.error is None
    assert result.cls is not None
    assert getattr(result.cls, "__name__", "") == "DevProvider"


def test_manager_loads_mixed_dotted_and_localpath(tmp_path: Path) -> None:
    base = _make_dev_package(tmp_path)
    spec_local = f"path:{base}::myplugins.provider_mod.DevProvider"
    # Known dotted-path provider class from repo
    spec_dotted = "plugins.openai_provider.OpenAICompatibleProvider"

    mgr = PluginManager(cache_dir=tmp_path, loaders=[DottedPathSource(), LocalPathSource()])

    plugins_cfg: Dict[str, Any] = {"providers": [spec_local, spec_dotted], "features": [], "tools": [], "extensions": []}
    canonical = mgr.normalize_plugins(plugins_cfg)
    core_kinds, app_classes, errors = mgr.load_plugins(canonical)
    assert errors == []
    assert len(core_kinds["providers"]) == 2
    names = [cls.__name__ for cls in core_kinds["providers"]]
    assert set(names) == {"DevProvider", "OpenAICompatibleProvider"}
