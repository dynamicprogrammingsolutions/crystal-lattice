"""Application-level integration tests for shell tool selection via config loading.

Tests the complete application flow including:
- Plugin loading via config path resolution
- CodexVariantFeature tag emission
- Shell tool selection based on model name and config

Uses OpenRouter provider, so requires OPENROUTER_API_KEY.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import AgentCore


REPO_ROOT = Path(__file__).resolve().parents[3]
BUILTIN_PLUGINS = REPO_ROOT / "plugins"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def _write_config(tmp_path: Path, config: Dict[str, Any]) -> Path:
    """Write config to temp file and return path."""
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


def _make_app(tmp_path: Path, config: Dict[str, Any]) -> AgentApplication:
    """Create AgentApplication with event store and env overrides."""
    config_path = _write_config(tmp_path, config)
    session_root = tmp_path / "sessions"
    return AgentApplication(
        str(config_path),
        str(session_root),
        core_factory=AgentCore,
        event_store=InMemoryEventStore(),
        env_overrides={
            "BUILTIN_PLUGINS": str(BUILTIN_PLUGINS),
            "OPENROUTER_API_KEY": OPENROUTER_API_KEY or "",
        },
    )


def _get_tool_names(core: AgentCore, config: Dict[str, Any]) -> List[str]:
    """Get names of enabled tools for a config."""
    _, _, _, tools, _ = core._resolve_plugins_for_config(config)
    return [t.name for t in tools]


def _get_tags(core: AgentCore, config: Dict[str, Any]) -> List[str]:
    """Get computed tags for a config."""
    _, _, _, _, tags = core._resolve_plugins_for_config(config)
    return tags


@pytest.mark.parametrize("model", ["openai/gpt-5.1", "openai/gpt-5.2", "openai/gpt-5.4"])
def test_shell_command_family_enables_unified_exec_via_application_config(
    tmp_path, model
):
    """Shell-command-family GPT models should auto-select unified exec."""

    config = {
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/openrouter",
            "path:${env:BUILTIN_PLUGINS}/codex-tools",
        ],
        "providers": {
            "openrouter": {
                "provider": "openrouter",
                "api_key": "${env:OPENROUTER_API_KEY}",
            }
        },
        "agents": {
            "codex-agent": {
                "provider": "openrouter",
                "model": model,
            }
        },
    }

    app = _make_app(tmp_path, config)
    core, agent_config, _ = app.create_session("codex-agent")

    tool_names = _get_tool_names(core, agent_config)
    tags = _get_tags(core, agent_config)

    assert "codex-variant" in tags
    assert "exec_command" in tool_names
    assert "write_stdin" in tool_names
    assert "shell_command" not in tool_names
    assert "shell" not in tool_names


@pytest.mark.integration
@pytest.mark.openrouter
def test_codex_model_enables_unified_exec_via_config(tmp_path):
    """Test that codex model enables unified exec via codex-variant tag."""
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set")

    config = {
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/openrouter",
            "path:${env:BUILTIN_PLUGINS}/codex-tools"
        ],
        "providers": {
            "openrouter": {
                "provider": "openrouter",
                "api_key": "${env:OPENROUTER_API_KEY}",
            }
        },
        "agents": {
            "codex-agent": {
                "provider": "openrouter",
                "model": "openai/gpt-4o-mini-codex",  # Fake codex name for selection testing
            }
        }
    }

    app = _make_app(tmp_path, config)
    core, agent_config, _ = app.create_session("codex-agent")

    tool_names = _get_tool_names(core, agent_config)
    tags = _get_tags(core, agent_config)

    assert "codex-variant" in tags, "codex-variant tag should be emitted for -codex model"
    assert "exec_command" in tool_names, "exec_command should be enabled for codex model"
    assert "write_stdin" in tool_names, "write_stdin should be enabled for codex model"
    assert "shell" not in tool_names, "shell should be disabled for codex model"
    assert "shell_command" not in tool_names, "shell_command should be disabled for codex model"


@pytest.mark.integration
@pytest.mark.openrouter
def test_exec_command_mode_forces_unified_exec_via_config(tmp_path):
    """Test that shell_tool_mode='exec_command' forces unified exec for any model."""
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set")

    config = {
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/openrouter",
            "path:${env:BUILTIN_PLUGINS}/codex-tools"
        ],
        "providers": {
            "openrouter": {
                "provider": "openrouter",
                "api_key": "${env:OPENROUTER_API_KEY}",
            }
        },
        "agents": {
            "forced-exec-agent": {
                "provider": "openrouter",
                "model": "openai/gpt-4o-mini",  # Non-codex model
                "shell_tool_mode": "exec_command",
            }
        }
    }

    app = _make_app(tmp_path, config)
    core, agent_config, _ = app.create_session("forced-exec-agent")

    tool_names = _get_tool_names(core, agent_config)

    assert "exec_command" in tool_names, "exec_command should be forced on"
    assert "write_stdin" in tool_names, "write_stdin should be forced on"
    assert "shell" not in tool_names, "shell should be off in exec_command mode"
    assert "shell_command" not in tool_names, "shell_command should be off in exec_command mode"


@pytest.mark.integration
@pytest.mark.openrouter
def test_non_codex_model_enables_unified_exec_via_config(tmp_path):
    """Test that plain gpt-5 also gets unified exec (model-agnostic default)."""
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set")

    config = {
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/openrouter",
            "path:${env:BUILTIN_PLUGINS}/codex-tools"
        ],
        "providers": {
            "openrouter": {
                "provider": "openrouter",
                "api_key": "${env:OPENROUTER_API_KEY}",
            }
        },
        "agents": {
            "standard-agent": {
                "provider": "openrouter",
                "model": "openai/gpt-5",
            }
        }
    }

    app = _make_app(tmp_path, config)
    core, agent_config, _ = app.create_session("standard-agent")

    tool_names = _get_tool_names(core, agent_config)
    tags = _get_tags(core, agent_config)

    assert "codex-variant" not in tags, "codex-variant tag should not be emitted for gpt-5"
    assert "exec_command" in tool_names, "exec_command should be enabled for gpt-5"
    assert "write_stdin" in tool_names, "write_stdin should be enabled for gpt-5"
    assert "shell" not in tool_names, "shell should be disabled in auto mode"
    assert "shell_command" not in tool_names, "shell_command should be disabled in auto mode"


@pytest.mark.integration
@pytest.mark.openrouter
def test_shell_mode_forces_shell_for_codex_model_via_config(tmp_path):
    """Test that shell_tool_mode='shell' forces shell even for codex model."""
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set")

    config = {
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/openrouter",
            "path:${env:BUILTIN_PLUGINS}/codex-tools"
        ],
        "providers": {
            "openrouter": {
                "provider": "openrouter",
                "api_key": "${env:OPENROUTER_API_KEY}",
            }
        },
        "agents": {
            "forced-shell-agent": {
                "provider": "openrouter",
                "model": "openai/gpt-4o-mini-codex",  # Fake codex name
                "shell_tool_mode": "shell",
            }
        }
    }

    app = _make_app(tmp_path, config)
    core, agent_config, _ = app.create_session("forced-shell-agent")

    tool_names = _get_tool_names(core, agent_config)
    tags = _get_tags(core, agent_config)

    assert "codex-variant" in tags  # Tag is still emitted
    assert "shell" in tool_names, "shell should be forced on in shell mode"
    assert "shell_command" not in tool_names, "shell_command should be off in shell mode"
    assert "exec_command" not in tool_names, "exec_command should be off in shell mode"
    assert "write_stdin" not in tool_names, "write_stdin should be off in shell mode"


@pytest.mark.integration
@pytest.mark.openrouter
def test_shell_command_mode_forces_shell_command_via_config(tmp_path):
    """Test that shell_tool_mode='shell_command' forces shell_command for non-codex model."""
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set")

    config = {
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/openrouter",
            "path:${env:BUILTIN_PLUGINS}/codex-tools"
        ],
        "providers": {
            "openrouter": {
                "provider": "openrouter",
                "api_key": "${env:OPENROUTER_API_KEY}",
            }
        },
        "agents": {
            "forced-command-agent": {
                "provider": "openrouter",
                "model": "openai/gpt-4o-mini",
                "shell_tool_mode": "shell_command",
            }
        }
    }

    app = _make_app(tmp_path, config)
    core, agent_config, _ = app.create_session("forced-command-agent")

    tool_names = _get_tool_names(core, agent_config)
    tags = _get_tags(core, agent_config)

    assert "codex-variant" not in tags
    assert "shell_command" in tool_names, "shell_command should be forced on"
    assert "shell" not in tool_names, "shell should be off in shell_command mode"
    assert "exec_command" not in tool_names, "exec_command should be off in shell_command mode"


@pytest.mark.integration
@pytest.mark.openrouter
def test_force_enabled_plugins_enables_both_via_config(tmp_path):
    """Test that force_enabled_plugins enables both shell tools."""
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set")

    config = {
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/openrouter",
            "path:${env:BUILTIN_PLUGINS}/codex-tools"
        ],
        "providers": {
            "openrouter": {
                "provider": "openrouter",
                "api_key": "${env:OPENROUTER_API_KEY}",
            }
        },
        "agents": {
            "both-tools-agent": {
                "provider": "openrouter",
                "model": "openai/gpt-4o-mini-codex",  # Fake codex name
                "force_enabled_plugins": ["shell", "shell_command"],
            }
        }
    }

    app = _make_app(tmp_path, config)
    core, agent_config, _ = app.create_session("both-tools-agent")

    tool_names = _get_tool_names(core, agent_config)

    assert "shell" in tool_names, "force_enabled should enable shell"
    assert "shell_command" in tool_names, "force_enabled should enable shell_command"


@pytest.mark.integration
@pytest.mark.openrouter
def test_enabled_plugins_enables_legacy_tool_via_config(tmp_path):
    """Test that enabled_plugins enables shell_legacy."""
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set")

    config = {
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/openrouter",
            "path:${env:BUILTIN_PLUGINS}/codex-tools"
        ],
        "providers": {
            "openrouter": {
                "provider": "openrouter",
                "api_key": "${env:OPENROUTER_API_KEY}",
            }
        },
        "agents": {
            "legacy-agent": {
                "provider": "openrouter",
                "model": "openai/gpt-4o-mini",
                "enabled_plugins": ["shell_legacy"],
                "disabled_plugins": ["shell", "shell_command"],
            }
        }
    }

    app = _make_app(tmp_path, config)
    core, agent_config, _ = app.create_session("legacy-agent")

    tool_names = _get_tool_names(core, agent_config)

    assert "shell_legacy" in tool_names, "enabled_plugins should enable legacy tool"
    assert "shell" not in tool_names, "shell should be disabled"
    assert "shell_command" not in tool_names, "shell_command should be disabled"


@pytest.mark.integration
@pytest.mark.openrouter
def test_multiple_agents_different_selections_via_config(tmp_path):
    """Test multiple agents with different models have different tool selections."""
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set")

    config = {
        "plugins": [
            "path:${env:BUILTIN_PLUGINS}/openrouter",
            "path:${env:BUILTIN_PLUGINS}/codex-tools"
        ],
        "providers": {
            "openrouter": {
                "provider": "openrouter",
                "api_key": "${env:OPENROUTER_API_KEY}",
            }
        },
        "agents": {
            "codex-agent": {
                "provider": "openrouter",
                "model": "openai/gpt-4o-mini-codex",  # Fake codex name
            },
            "standard-agent": {
                "provider": "openrouter",
                "model": "openai/gpt-4o-mini",
            }
        }
    }

    app = _make_app(tmp_path, config)

    # Codex agent should have unified exec
    codex_core, codex_config, _ = app.create_session("codex-agent")
    codex_tools = _get_tool_names(codex_core, codex_config)
    assert "exec_command" in codex_tools
    assert "write_stdin" in codex_tools
    assert "shell_command" not in codex_tools
    assert "shell" not in codex_tools

    # Standard agent should also have unified exec (model-agnostic default)
    standard_core, standard_config, _ = app.create_session("standard-agent")
    standard_tools = _get_tool_names(standard_core, standard_config)
    assert "shell" not in standard_tools
    assert "shell_command" not in standard_tools
    assert "exec_command" in standard_tools
    assert "write_stdin" in standard_tools