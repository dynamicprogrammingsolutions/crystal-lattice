from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "optional_plugins"
FIXTURE_OPTIONAL_PLUGIN_NAME = "_test-small-app"
FIXTURE_OPTIONAL_PLUGIN_DIR = FIXTURES_DIR / FIXTURE_OPTIONAL_PLUGIN_NAME
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_cloud_runtime_plugin_bundle import copytree_sanitized  # noqa: E402
from build_cloud_runtime_plugin_bundle import (  # noqa: E402
    stage_cloud_runtime_plugin_bundle,
)
import build_crystal_lattice_binary as binary_builder  # noqa: E402


def test_cloud_runtime_plugin_bundle_stages_preinstalled_metadata_and_sources(
    tmp_path: Path,
) -> None:
    output = tmp_path / "cloud-runtime-plugin-bundle"

    manifest = stage_cloud_runtime_plugin_bundle(
        plugins_root=ROOT / "plugins",
        selected_config=(
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
    assert "session-main-search-app" in manifest["preinstalled_plugins"]
    assert "session-archive-app" in manifest["preinstalled_plugins"]
    assert "session-pinned-app" in manifest["preinstalled_plugins"]
    assert "session-status-app" in manifest["preinstalled_plugins"]
    assert "tool-compat-shared" in manifest["local_projects"]
    assert "mcp-shared" in manifest["local_projects"]
    assert "skill-shared" in manifest["local_projects"]

    local_projects = (output / "local-projects.txt").read_text(encoding="utf-8")
    assert "./plugin_sources/codex-tools\n" in local_projects
    assert "./plugin_sources/tool-compat-shared\n" in local_projects


def test_builtin_plugin_selection_ignores_disabled_plugin_raw_strings(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "plugins": [
                    "path:${env:BUILTIN_PLUGINS}/openrouter",
                    "path:${env:BUILTIN_PLUGINS}/cloud-agent-app",
                ],
                "application": {
                    "cloud_agent": {
                        "disabled_plugins": [
                            {
                                "$raw": "path:${env:BUILTIN_PLUGINS}/message-export-actions"
                            }
                        ]
                    }
                },
                "providers": {},
                "agents": {},
            }
        ),
        encoding="utf-8",
    )

    selected = binary_builder.discover_selected_bundled_plugin_names(config_path)

    assert "openrouter" in selected
    assert "cloud-agent-app" in selected
    assert "message-export-actions" not in selected


def test_builtin_plugin_selection_uses_resolved_equivalent_path_forms(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("ALT_BUILTINS", str(ROOT / "plugins"))
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "plugins": [
                    f"path:{ROOT / 'plugins' / 'openrouter'}",
                    {"path": f"{ROOT / 'plugins' / 'cloud-agent-app'}"},
                    "bash:${env:ALT_BUILTINS}/bash-send-kindle-icloud",
                ],
                "providers": {},
                "agents": {},
            }
        ),
        encoding="utf-8",
    )

    selected = binary_builder.discover_selected_bundled_plugin_names(config_path)

    assert "openrouter" in selected
    assert "cloud-agent-app" in selected
    assert "bash-send-kindle-icloud" in selected


def test_cloud_runtime_plugin_bundle_prunes_disabled_builtin_plugin_specs(
    tmp_path: Path,
) -> None:
    selected_spec = f"path:{(ROOT / 'plugins' / 'message-export-actions').resolve()}"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "plugins": [
                    "path:${env:BUILTIN_PLUGINS}/cloud-agent-app",
                    selected_spec,
                ],
                "providers": {},
                "agents": {},
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "cloud-runtime-plugin-bundle"

    manifest = stage_cloud_runtime_plugin_bundle(
        plugins_root=ROOT / "plugins",
        selected_config=config_path,
        output=output,
        local_project_prefix="./plugin_sources",
        cloud_disabled_plugin_specs=[selected_spec],
    )

    assert "cloud-agent-app" in manifest["preinstalled_plugins"]
    assert "message-export-actions" not in manifest["preinstalled_plugins"]
    assert "message-export-actions" not in manifest["local_projects"]
    assert not (
        output / "bundled_plugins" / "message-export-actions" / "agent_plugin.json"
    ).exists()
    assert "./plugin_sources/message-export-actions\n" not in (
        output / "local-projects.txt"
    ).read_text(encoding="utf-8")


def test_cloud_runtime_plugin_bundle_prunes_disabled_builtin_plugin_specs_before_env_resolution(
    tmp_path: Path,
) -> None:
    disabled_spec = "path:${env:BUILTIN_PLUGINS}/message-export-actions"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "plugins": [
                    "path:${env:BUILTIN_PLUGINS}/cloud-agent-app",
                    disabled_spec,
                ],
                "providers": {},
                "agents": {},
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "cloud-runtime-plugin-bundle"

    manifest = stage_cloud_runtime_plugin_bundle(
        plugins_root=ROOT / "plugins",
        selected_config=config_path,
        output=output,
        local_project_prefix="./plugin_sources",
        cloud_disabled_plugin_specs=[disabled_spec],
    )

    assert "cloud-agent-app" in manifest["preinstalled_plugins"]
    assert "message-export-actions" not in manifest["preinstalled_plugins"]
    assert "message-export-actions" not in manifest["local_projects"]
    assert not (
        output / "bundled_plugins" / "message-export-actions" / "agent_plugin.json"
    ).exists()
    assert "./plugin_sources/message-export-actions\n" not in (
        output / "local-projects.txt"
    ).read_text(encoding="utf-8")


def test_binary_asset_staging_keeps_selected_preinstalled_and_optional_installable(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(binary_builder, "ASSET_STAGE_DIR", tmp_path / "assets")

    selected = binary_builder.discover_selected_bundled_plugin_names()
    resources = binary_builder.discover_builtin_plugin_resource_paths()

    assert "anthropic-compatible" in selected
    assert "codex-tools" in selected
    assert "cloud-agent-app" in selected
    assert "gemini-compaction-feature" not in selected

    binary_builder.prepare_staged_assets(selected, resources)

    bundled_plugins = tmp_path / "assets" / "bundled_plugins"
    selected_descriptor = json.loads(
        (bundled_plugins / "codex-tools" / "agent_plugin.json").read_text(
            encoding="utf-8"
        )
    )
    anthropic_descriptor = json.loads(
        (bundled_plugins / "anthropic-compatible" / "agent_plugin.json").read_text(
            encoding="utf-8"
        )
    )
    optional_descriptor = json.loads(
        (bundled_plugins / "gemini-compaction-feature" / "agent_plugin.json").read_text(
            encoding="utf-8"
        )
    )

    assert selected_descriptor["preinstalled"] is True
    assert anthropic_descriptor["preinstalled"] is True
    assert not (bundled_plugins / "codex-tools" / "src").exists()
    assert optional_descriptor.get("preinstalled") is not True
    assert (bundled_plugins / "gemini-compaction-feature" / "pyproject.toml").is_file()
    assert (
        bundled_plugins
        / "gemini-compaction-feature"
        / "src"
        / "gemini_compaction_feature"
        / "__init__.py"
    ).is_file()

    hidden_imports = binary_builder.discover_plugin_hidden_imports(bundled_plugins)
    assert "anthropic_plugins" in hidden_imports
    assert "codex_tools" in hidden_imports
    assert "gemini_compaction_feature" not in hidden_imports


def test_bundled_cloud_runtime_includes_python_headers_for_native_wheels() -> None:
    dockerfile = (
        ROOT
        / "plugins"
        / "cloud-agent-app"
        / "src"
        / "cloud_agent_app"
        / "bundled_runtime"
        / "python"
        / "Dockerfile"
    )

    text = dockerfile.read_text(encoding="utf-8")

    assert "build-essential" in text
    assert "python3-dev" in text
    assert "python3-venv" in text


def test_cloud_runtime_context_sanitizer_excludes_private_generated_state(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "module.py").write_text("value = 1\n", encoding="utf-8")
    for dirname in (".plugin_cache", ".venv", ".crystal", "auth"):
        private_dir = source / dirname
        private_dir.mkdir()
        (private_dir / "secret.txt").write_text("secret\n", encoding="utf-8")

    destination = tmp_path / "destination"
    copytree_sanitized(source, destination)

    assert (destination / "module.py").is_file()
    for dirname in (".plugin_cache", ".venv", ".crystal", "auth"):
        assert not (destination / dirname).exists()


def test_optional_fixture_plugin_installs_from_bundled_plugins_root(
    tmp_path: Path, monkeypatch
) -> None:
    bundled_plugins = tmp_path / "bundled-plugins"
    shutil.copytree(
        FIXTURE_OPTIONAL_PLUGIN_DIR, bundled_plugins / FIXTURE_OPTIONAL_PLUGIN_NAME
    )

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    plugin_cache = tmp_path / "plugin-cache"
    config_path = config_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "plugin_cache_dir": str(plugin_cache),
                "plugins": [
                    f"path:${{env:BUILTIN_PLUGINS}}/{FIXTURE_OPTIONAL_PLUGIN_NAME}",
                ],
                "providers": {},
                "agents": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("BUILTIN_PLUGINS", str(bundled_plugins))
    monkeypatch.setenv("CONFIG_DIR", str(config_dir))

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )

    assert app.get_config_errors() == []
    _assert_optional_fixture_plugin_loaded(app, plugin_cache)


def test_optional_fixture_plugin_installs_from_arbitrary_direct_path(
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    plugin_cache = tmp_path / "plugin-cache"
    config_path = config_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "plugin_cache_dir": str(plugin_cache),
                "plugins": [f"path:{FIXTURE_OPTIONAL_PLUGIN_DIR}"],
                "providers": {},
                "agents": {},
            }
        ),
        encoding="utf-8",
    )

    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )

    assert app.get_config_errors() == []
    _assert_optional_fixture_plugin_loaded(app, plugin_cache)


def _assert_optional_fixture_plugin_loaded(
    app: AgentApplication, plugin_cache: Path
) -> None:
    assert any(
        plugin.get("name") == "_test_small_app"
        for plugin in app.list_application_plugins()
    )
    assert any(
        action.get("id") == "_test_small_app.ping"
        for action in app.get_application_actions()
    )
    install_dir = next(plugin_cache.glob(f"{FIXTURE_OPTIONAL_PLUGIN_NAME}@*"))
    assert install_dir.is_dir()
    _assert_distribution_installed(install_dir, "tomli-w")


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
