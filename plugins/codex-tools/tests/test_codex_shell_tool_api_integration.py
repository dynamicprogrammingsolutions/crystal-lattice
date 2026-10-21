"""OpenRouter integration tests for Codex shell tools with real API calls.

Tests that each shell tool variant works correctly with real OpenRouter models:
- exec_command + write_stdin: Tested with codex model (unified exec surface)
- shell_command: Tested with codex model (gpt-5.1-codex-mini, explicit mode)
- shell (array): Tested with standard model (gpt-5.4-nano)
- shell_legacy: Tested with standard model (explicitly enabled)
"""

from __future__ import annotations

import os

import pytest

from agent_core import AgentCore

from codex_tools import ShellArrayTool, ShellCommandTool, ShellTool, CodexVariantFeature
from codex_tools.unified_exec_tool import ExecCommandTool, WriteStdinTool


# Models for testing
CODEX_MODEL = os.getenv("OPENROUTER_MODEL_CODEX_TOOLS", "openai/gpt-6-luna")
STANDARD_MODEL = os.getenv("OPENROUTER_MODEL_STANDARD_TOOLS", "openai/gpt-5.4-nano")


@pytest.mark.integration
@pytest.mark.openrouter
def test_exec_command_tool_with_codex_model(tmp_path):
    """Test that exec_command (unified exec) works correctly with codex model."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    target = tmp_path / "unified_exec_output.txt"

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_feature(CodexVariantFeature)
    core.register_tool(ExecCommandTool)
    core.register_tool(WriteStdinTool)

    config = {
        "model": CODEX_MODEL,
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
        "project_temp_dir": str(tmp_path / ".temp"),
        # Use seed for deterministic model behavior
        "request_options": {"seed": 42},
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        f"You must use the exec_command tool to execute shell commands. Never answer without calling the tool first. Always set the workdir parameter to: {tmp_path}",
    )
    session = core.add_message(
        session,
        "user",
        "Execute a shell command to write the text 'Unified exec test' to a file named unified_exec_output.txt using echo and redirection.",
    )

    session, responses = core.send_request(session, config)
    tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
    assert tool_calls, "expected a tool call"

    tool_name = tool_calls[0].get("function", {}).get("name")
    assert tool_name == "exec_command", f"expected 'exec_command', got '{tool_name}'"

    # Parse arguments (they come as JSON string)
    args_str = tool_calls[0].get("function", {}).get("arguments", "{}")
    import json
    args = json.loads(args_str) if isinstance(args_str, str) else args_str

    # Verify the cmd arg is a string
    assert "cmd" in args, f"expected 'cmd' arg, got {list(args.keys())}"
    assert isinstance(args["cmd"], str), "cmd should be a string"

    for tool_msg in core.execute_tool_calls(tool_calls, config):
        session = core.add_message(
            session,
            role=tool_msg["role"],
            content=tool_msg["content"],
            metadata=tool_msg.get("metadata"),
            config=config,
        )

    # Verify file was created with correct content
    assert target.exists(), "unified_exec_output.txt should have been created"
    assert "Unified exec test" in target.read_text()


@pytest.mark.integration
@pytest.mark.openrouter
def test_shell_command_tool_with_codex_model(tmp_path):
    """Test that shell_command tool works correctly with codex model."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    target = tmp_path / "codex_output.txt"

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_feature(CodexVariantFeature)
    core.register_tool(ShellCommandTool)

    config = {
        "model": CODEX_MODEL,
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
        "project_temp_dir": str(tmp_path / ".temp"),
        # Legacy tool: auto mode selects unified exec for codex models.
        "shell_tool_mode": "shell_command",
        # Use seed for deterministic model behavior
        "request_options": {"seed": 42},
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        f"You must use the shell_command tool to execute shell commands. Never answer without calling the tool first. Always set the workdir parameter to: {tmp_path}",
    )
    session = core.add_message(
        session,
        "user",
        "Execute a shell command to write the text 'Codex shell test' to a file named codex_output.txt using echo and redirection.",
    )

    session, responses = core.send_request(session, config)
    tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
    assert tool_calls, "expected a tool call"

    tool_name = tool_calls[0].get("function", {}).get("name")
    assert tool_name == "shell_command", f"expected 'shell_command', got '{tool_name}'"

    # Parse arguments (they come as JSON string)
    args_str = tool_calls[0].get("function", {}).get("arguments", "{}")
    import json
    args = json.loads(args_str) if isinstance(args_str, str) else args_str
    
    # Verify the command arg is a string (not array)
    assert "command" in args, f"expected 'command' arg, got {list(args.keys())}"
    assert isinstance(args["command"], str), "command should be a string"

    for tool_msg in core.execute_tool_calls(tool_calls, config):
        session = core.add_message(
            session,
            role=tool_msg["role"],
            content=tool_msg["content"],
            metadata=tool_msg.get("metadata"),
            config=config,
        )

    # Verify file was created with correct content
    assert target.exists(), "codex_output.txt should have been created"
    assert "Codex shell test" in target.read_text()


@pytest.mark.integration
@pytest.mark.openrouter
def test_shell_command_tool_with_codex_mini_model(tmp_path):
    """Test that shell_command tool works correctly with codex-mini model."""
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

    config = {
        "model": "openai/gpt-5.1-codex-mini",
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
        "project_temp_dir": str(tmp_path / ".temp"),
        # Legacy tool: auto mode selects unified exec for codex models.
        "shell_tool_mode": "shell_command",
        # Use seed for deterministic model behavior
        "request_options": {"seed": 42},
    }

    target = tmp_path / "codex_mini_output.txt"

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        f"You must use the shell_command tool to execute shell commands. Never answer without calling the tool first. Always set the workdir parameter to the absolute path: {tmp_path}",
    )
    session = core.add_message(
        session,
        "user",
        "Execute a shell command to write the text 'Codex mini test' to a file named codex_mini_output.txt using echo and redirection.",
    )

    session, responses = core.send_request(session, config)
    tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
    assert tool_calls, "expected a tool call"

    tool_name = tool_calls[0].get("function", {}).get("name")
    assert tool_name == "shell_command", f"expected 'shell_command', got '{tool_name}'"

    # Parse arguments (they come as JSON string)
    args_str = tool_calls[0].get("function", {}).get("arguments", "{}")
    import json
    args = json.loads(args_str) if isinstance(args_str, str) else args_str
    
    # Verify the command arg is a string (not array)
    assert "command" in args, f"expected 'command' arg, got {list(args.keys())}"
    assert isinstance(args["command"], str), "command should be a string"

    for tool_msg in core.execute_tool_calls(tool_calls, config):
        session = core.add_message(
            session,
            role=tool_msg["role"],
            content=tool_msg["content"],
            metadata=tool_msg.get("metadata"),
            config=config,
        )

    # Verify file was created with correct content
    assert target.exists(), "codex_mini_output.txt should have been created"
    assert "Codex mini test" in target.read_text()


@pytest.mark.integration
@pytest.mark.openrouter
def test_shell_array_tool_with_standard_model(tmp_path):
    """Test that shell (array-based) tool works correctly with standard model."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    target = tmp_path / "shell_output.txt"

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_feature(CodexVariantFeature)
    core.register_tool(ShellArrayTool)

    config = {
        "model": STANDARD_MODEL,
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
        "project_temp_dir": str(tmp_path / ".temp"),
        # Legacy tool: auto mode selects unified exec for every model.
        "shell_tool_mode": "shell",
        # Use seed for deterministic model behavior
        "request_options": {"seed": 42},
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        f"You must use the shell tool to execute shell commands. Never answer without calling the tool first. Always set the workdir parameter to: {tmp_path}",
    )
    session = core.add_message(
        session,
        "user",
        "Execute a shell command to write the text 'Shell array test' to a file named shell_output.txt using echo and redirection.",
    )

    session, responses = core.send_request(session, config)
    tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
    assert tool_calls, "expected a tool call"

    tool_name = tool_calls[0].get("function", {}).get("name")
    assert tool_name == "shell", f"expected 'shell', got '{tool_name}'"

    # Parse arguments (they come as JSON string)
    args_str = tool_calls[0].get("function", {}).get("arguments", "{}")
    import json
    args = json.loads(args_str) if isinstance(args_str, str) else args_str
    
    # Verify the command arg is a list (array)
    assert "command" in args, f"expected 'command' arg, got {list(args.keys())}"
    assert isinstance(args["command"], list), "command should be a list"

    for tool_msg in core.execute_tool_calls(tool_calls, config):
        session = core.add_message(
            session,
            role=tool_msg["role"],
            content=tool_msg["content"],
            metadata=tool_msg.get("metadata"),
            config=config,
        )

    # Verify file was created with correct content
    assert target.exists(), "shell_output.txt should have been created"
    assert "Shell array test" in target.read_text()


@pytest.mark.integration
@pytest.mark.openrouter
def test_shell_legacy_tool_with_standard_model(tmp_path):
    """Test that shell_legacy tool works correctly when explicitly enabled."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    target = tmp_path / "legacy_output.txt"

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_feature(CodexVariantFeature)
    core.register_tool(ShellTool)  # Legacy tool

    config = {
        "model": STANDARD_MODEL,
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
        "project_temp_dir": str(tmp_path / ".temp"),
        # Legacy tool has default_enabled=False, must force enable
        "force_enabled_plugins": ["shell_legacy"],
        # Use seed for deterministic model behavior
        "request_options": {"seed": 42},
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        f"You must use the shell tool to execute shell commands. Never answer without calling the tool first. Always set the workdir parameter to: {tmp_path}",
    )
    session = core.add_message(
        session,
        "user",
        "Execute a shell command to write the text 'Legacy shell test' to a file named legacy_output.txt using echo and redirection.",
    )

    session, responses = core.send_request(session, config)
    tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
    assert tool_calls, "expected a tool call"

    tool_name = tool_calls[0].get("function", {}).get("name")
    # Legacy tool schema name is "shell"
    assert tool_name == "shell", f"expected 'shell', got '{tool_name}'"

    # Parse arguments (they come as JSON string)
    args_str = tool_calls[0].get("function", {}).get("arguments", "{}")
    import json
    args = json.loads(args_str) if isinstance(args_str, str) else args_str
    
    # Legacy tool uses single command arg (string)
    assert "command" in args, f"expected 'command' arg, got {list(args.keys())}"
    assert isinstance(args["command"], str), "command should be a string"

    for tool_msg in core.execute_tool_calls(tool_calls, config):
        session = core.add_message(
            session,
            role=tool_msg["role"],
            content=tool_msg["content"],
            metadata=tool_msg.get("metadata"),
            config=config,
        )

    # Verify file was created with correct content
    assert target.exists(), "legacy_output.txt should have been created"
    assert "Legacy shell test" in target.read_text()