from __future__ import annotations

import json
import sys
from pathlib import Path

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_cloud_runtime_plugin_bundle import stage_cloud_runtime_plugin_bundle
import build_crystal_lattice_binary as binary_builder


def test_cloud_runtime_plugin_bundle_stages_preinstalled_metadata_and_sources(
    tmp_path: Path,
) -> None:
    output = tmp_path / "cloud-runtime-plugin-bundle"

    manifest = stage_cloud_runtime_plugin_bundle(
        plugins_root=ROOT / "plugins",
        default_config=(
            ROOT
            / "application"
            / "python"
            / "agent_terminal_app"
            / "default_config"
            / "config.json"
        ),
        output=output,
        local_project_prefix="./plugin_sources",
    )

    bundled_plugins = output / "bundled_plugins"
    descriptor_path = bundled_plugins / "cloud-agent-app" / "agent_plugin.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))

    assert descriptor["preinstalled"] is True
    assert (
        bundled_plugins / "cloud-agent-app" / "docs" / "cloud-script-authoring.md"
    ).is_file()
    assert "cloud-agent-app" in manifest["preinstalled_plugins"]
    assert "codex-tools" in manifest["preinstalled_plugins"]
    assert "tool-compat-shared" in manifest["local_projects"]
    assert "mcp-shared" in manifest["local_projects"]
    assert "skill-shared" in manifest["local_projects"]

    local_projects = (output / "local-projects.txt").read_text(encoding="utf-8")
    assert "./plugin_sources/codex-tools\n" in local_projects
    assert "./plugin_sources/tool-compat-shared\n" in local_projects


def test_binary_asset_staging_keeps_selected_preinstalled_and_optional_installable(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(binary_builder, "ASSET_STAGE_DIR", tmp_path / "assets")

    selected = binary_builder.discover_selected_bundled_plugin_names()
    resources = binary_builder.discover_builtin_plugin_resource_paths()

    assert "codex-tools" in selected
    assert "cloud-agent-app" in selected
    assert "message-export-actions" not in selected

    binary_builder.prepare_staged_assets(selected, resources)

    bundled_plugins = tmp_path / "assets" / "bundled_plugins"
    selected_descriptor = json.loads(
        (bundled_plugins / "codex-tools" / "agent_plugin.json").read_text(
            encoding="utf-8"
        )
    )
    optional_descriptor = json.loads(
        (bundled_plugins / "message-export-actions" / "agent_plugin.json").read_text(
            encoding="utf-8"
        )
    )

    assert selected_descriptor["preinstalled"] is True
    assert not (bundled_plugins / "codex-tools" / "src").exists()
    assert optional_descriptor.get("preinstalled") is not True
    assert (bundled_plugins / "message-export-actions" / "pyproject.toml").is_file()
    assert (
        bundled_plugins
        / "message-export-actions"
        / "src"
        / "message_export_actions"
        / "__init__.py"
    ).is_file()

    hidden_imports = binary_builder.discover_plugin_hidden_imports(bundled_plugins)
    assert "codex_tools" in hidden_imports
    assert "message_export_actions" not in hidden_imports


def test_optional_bundled_source_plugin_installs_and_loads_from_staged_assets(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(binary_builder, "ASSET_STAGE_DIR", tmp_path / "assets")
    selected = binary_builder.discover_selected_bundled_plugin_names()
    resources = binary_builder.discover_builtin_plugin_resource_paths()
    binary_builder.prepare_staged_assets(selected, resources)

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    plugin_cache = tmp_path / "plugin-cache"
    config_path = config_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "plugin_cache_dir": str(plugin_cache),
                "plugins": [
                    "path:${env:BUILTIN_PLUGINS}/message-export-actions",
                ],
                "providers": {},
                "agents": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("BUILTIN_PLUGINS", str(tmp_path / "assets" / "bundled_plugins"))
    monkeypatch.setenv("CONFIG_DIR", str(config_dir))

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )

    assert app.get_config_errors() == []
    application_plugins = {
        plugin["id"]: plugin for plugin in app.list_application_plugins()
    }
    assert "message_send_to_kindle" in application_plugins
    assert "message_share_as_pdf" in application_plugins
    install_dir = next(plugin_cache.glob("message-export-actions@*"))
    assert install_dir.is_dir()
    _assert_distribution_installed(install_dir, "markdown")
    _assert_distribution_installed(install_dir, "xhtml2pdf")


def _assert_distribution_installed(install_dir: Path, distribution_name: str) -> None:
    normalized = distribution_name.lower().replace("-", "_")
    assert any(
        path.name.lower()
        .replace("-", "_")
        .removesuffix(".dist_info")
        .startswith(f"{normalized}_")
        and path.name.endswith(".dist-info")
        for path in install_dir.glob("*.dist-info")
    ), f"{distribution_name} was not installed into {install_dir}"
