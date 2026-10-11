"""OpenRouter integration tests for Codex shell tools.

Tests that codex variant detection and shell tool selection work correctly
with the OpenRouter provider.
"""

from __future__ import annotations

import os

import pytest

from agent_core import AgentCore

from codex_tools import ShellArrayTool, ShellCommandTool, CodexVariantFeature
from codex_tools.unified_exec_tool import ExecCommandTool, WriteStdinTool


# Model for testing
STANDARD_MODEL = os.getenv("OPENROUTER_MODEL_STANDARD_TOOLS", "openai/gpt-4o-mini")


@pytest.mark.integration
@pytest.mark.openrouter
def test_codex_variant_feature_with_standard_model(tmp_path):
    """Test that CodexVariantFeature correctly handles standard (non-codex) models."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_feature(CodexVariantFeature)
    core.register_tool(ShellCommandTool)
    core.register_tool(ShellArrayTool)
    core.register_tool(ExecCommandTool)
    core.register_tool(WriteStdinTool)

    config = {
        "model": STANDARD_MODEL,
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
        "project_temp_dir": str(tmp_path / ".temp"),
    }

    # Verify no codex-variant tag for standard model
    _, _, _, tools, tags = core._resolve_plugins_for_config(config)
    assert "codex-variant" not in tags, "codex-variant tag should not be emitted for non-codex model"

    # Verify unified exec is enabled (model-agnostic default) and legacy
    # shell tools are disabled
    tool_names = [t.name for t in tools]
    assert "shell" not in tool_names, "shell should be disabled in auto mode"
    assert "shell_command" not in tool_names, "shell_command should be disabled in auto mode"
    assert "exec_command" in tool_names, "exec_command should be enabled for non-codex model"
    assert "write_stdin" in tool_names, "write_stdin should be enabled for non-codex model"


@pytest.mark.integration
@pytest.mark.openrouter
def test_codex_variant_tag_for_codex_model_name(tmp_path):
    """Test that CodexVariantFeature emits codex-variant tag for model names ending with -codex."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_feature(CodexVariantFeature)
    core.register_tool(ShellCommandTool)
    core.register_tool(ShellArrayTool)
    core.register_tool(ExecCommandTool)
    core.register_tool(WriteStdinTool)

    # Use a model name that ends with -codex (doesn't need to be real for selection testing)
    config = {
        "model": "openai/gpt-4o-mini-codex",  # Fake codex model name
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
        "project_temp_dir": str(tmp_path / ".temp"),
    }

    # Verify codex-variant tag is emitted for model name ending with -codex
    _, _, _, tools, tags = core._resolve_plugins_for_config(config)
    assert "codex-variant" in tags, "codex-variant tag should be emitted for model ending with -codex"

    # Verify unified exec is enabled and legacy shell tools are disabled
    tool_names = [t.name for t in tools]
    assert "exec_command" in tool_names, "exec_command should be enabled for codex model"
    assert "write_stdin" in tool_names, "write_stdin should be enabled for codex model"
    assert "shell_command" not in tool_names, "shell_command should be disabled in auto mode"
    assert "shell" not in tool_names, "shell should be disabled for codex model"


@pytest.mark.integration
@pytest.mark.openrouter
def test_shell_tool_mode_shell_forces_shell(tmp_path):
    """Test that shell_tool_mode='shell' forces shell even with codex model name."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_feature(CodexVariantFeature)
    core.register_tool(ShellCommandTool)
    core.register_tool(ShellArrayTool)
    core.register_tool(ExecCommandTool)
    core.register_tool(WriteStdinTool)

    # Use a model name that ends with -codex but force shell mode
    config = {
        "model": "openai/gpt-4o-mini-codex",
        "shell_tool_mode": "shell",
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
        "project_temp_dir": str(tmp_path / ".temp"),
    }

    # Verify codex-variant tag is still emitted
    _, _, _, tools, tags = core._resolve_plugins_for_config(config)
    assert "codex-variant" in tags, "codex-variant tag should still be emitted"

    # Verify shell is forced on despite codex model
    tool_names = [t.name for t in tools]
    assert "shell" in tool_names, "shell should be forced on in shell mode"
    assert "shell_command" not in tool_names, "shell_command should be off in shell mode"
    assert "exec_command" not in tool_names, "exec_command should be off in shell mode"
    assert "write_stdin" not in tool_names, "write_stdin should be off in shell mode"


@pytest.mark.integration
@pytest.mark.openrouter
def test_shell_tool_mode_shell_command_forces_shell_command(tmp_path):
    """Test that shell_tool_mode='shell_command' forces shell_command for standard model."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_feature(CodexVariantFeature)
    core.register_tool(ShellCommandTool)
    core.register_tool(ShellArrayTool)
    core.register_tool(ExecCommandTool)
    core.register_tool(WriteStdinTool)

    # Use standard model but force shell_command mode
    config = {
        "model": STANDARD_MODEL,
        "shell_tool_mode": "shell_command",
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
        "project_temp_dir": str(tmp_path / ".temp"),
    }

    # Verify no codex-variant tag for standard model
    _, _, _, tools, tags = core._resolve_plugins_for_config(config)
    assert "codex-variant" not in tags

    # Verify shell_command is forced on
    tool_names = [t.name for t in tools]
    assert "shell_command" in tool_names, "shell_command should be forced on"
    assert "shell" not in tool_names, "shell should be off in shell_command mode"
    assert "exec_command" not in tool_names, "exec_command should be off in shell_command mode"
    assert "write_stdin" not in tool_names, "write_stdin should be off in shell_command mode"