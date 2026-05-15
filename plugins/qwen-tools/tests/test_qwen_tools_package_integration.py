"""Integration tests for loading the full qwen-tools package.

Tests loading all tools via PluginManager with "path:" pattern.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import pytest


@pytest.fixture
def qwen_tools_repo() -> Path:
    """Get the path to qwen-tools repo."""
    return Path(__file__).resolve().parents[1]


class TestPackageLoading:
    """Tests for loading the full package."""

    def test_package_loads_all_tools_via_path(self, qwen_tools_repo: Path, tmp_path: Path) -> None:
        """Verify entire qwen-tools package loads correctly."""
        from agent_app.plugin_manager import PluginManager

        mgr = PluginManager(cache_dir=tmp_path / "cache", policy={"install_deps": True})
        resolution = mgr.resolve_all([{"path": str(qwen_tools_repo)}])

        assert resolution.errors == []

        # Should include all tools including QwenWebFetchTool
        class_names = [cls.__name__ for cls in resolution.classes]
        assert "QwenReadFileTool" in class_names
        assert "QwenWriteFileTool" in class_names
        assert "QwenEditTool" in class_names
        assert "QwenListDirectoryTool" in class_names
        assert "QwenGrepSearchTool" in class_names
        assert "QwenGlobTool" in class_names
        assert "QwenShellTool" in class_names
        assert "QwenWebFetchTool" in class_names

    def test_web_fetch_tool_available_after_package_load(self, qwen_tools_repo: Path, tmp_path: Path) -> None:
        """Verify web fetch tool is available after loading package."""
        from agent_app.plugin_manager import PluginManager
        from agent_core.plugin import ToolWrapper

        mgr = PluginManager(cache_dir=tmp_path / "cache", policy={"install_deps": True})
        resolution = mgr.resolve_all([{"path": str(qwen_tools_repo)}])

        assert resolution.errors == []

        # Find QwenWebFetchTool class
        web_fetch_class = None
        for cls in resolution.classes:
            if cls.__name__ == "QwenWebFetchTool":
                web_fetch_class = cls
                break

        assert web_fetch_class is not None

        # Verify it works
        wrapper = ToolWrapper(web_fetch_class)
        state = wrapper.init({})

        schemas = wrapper.get_tool_schemas(state)
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "web_fetch"


class TestPackageIntegrationWithOpenRouter:
    """Integration tests with OpenRouter provider when loading full package."""

    @pytest.mark.skipif(
        not os.environ.get("OPENROUTER_API_KEY"),
        reason="OPENROUTER_API_KEY not set",
    )
    @pytest.mark.openrouter
    def test_web_fetch_in_package_context(self, qwen_tools_repo: Path, tmp_path: Path) -> None:
        """Web fetch works when loaded as part of full package."""
        from agent_app.plugin_manager import PluginManager
        from agent_core import AgentCore

        mgr = PluginManager(cache_dir=tmp_path / "cache", policy={"install_deps": True})
        resolution = mgr.resolve_all([{"path": str(qwen_tools_repo)}])

        assert resolution.errors == []

        # Register all tools from package
        core = AgentCore()
        for cls in resolution.classes:
            core.register_tool(cls)

        config = {
            "provider": "openrouter",
            "model": "openai/gpt-4.1-mini",
            "api_key": os.environ.get("OPENROUTER_API_KEY"),
        }

        # Execute web_fetch
        messages = core.execute_tool_calls(
            [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "web_fetch",
                        "arguments": {
                            "url": "https://httpbin.org/html",
                            "prompt": "What is this page about?",
                        },
                    },
                }
            ],
            config,
        )

        assert len(messages) == 1
        assert messages[0]["role"] == "tool"
        assert messages[0]["metadata"]["tool_name"] == "web_fetch"

    @pytest.mark.skipif(
        not os.environ.get("OPENROUTER_API_KEY"),
        reason="OPENROUTER_API_KEY not set",
    )
    @pytest.mark.openrouter
    def test_read_file_and_web_fetch_together(self, qwen_tools_repo: Path, tmp_path: Path) -> None:
        """Multiple tools from package work together."""
        from agent_app.plugin_manager import PluginManager
        from agent_core import AgentCore

        mgr = PluginManager(cache_dir=tmp_path / "cache", policy={"install_deps": True})
        resolution = mgr.resolve_all([{"path": str(qwen_tools_repo)}])

        core = AgentCore()
        for cls in resolution.classes:
            core.register_tool(cls)

        config = {
            "provider": "openrouter",
            "model": "openai/gpt-4.1-mini",
            "api_key": os.environ.get("OPENROUTER_API_KEY"),
            "working_directory": str(tmp_path),
        }

        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello from test file\n")

        # Execute both read_file and web_fetch
        messages = core.execute_tool_calls(
            [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "arguments": {"absolute_path": str(test_file)},
                    },
                },
                {
                    "id": "call_2",
                    "type": "function",
                    "function": {
                        "name": "web_fetch",
                        "arguments": {
                            "url": "https://httpbin.org/html",
                            "prompt": "Summarize in one sentence",
                        },
                    },
                },
            ],
            config,
        )

        assert len(messages) == 2
        assert messages[0]["metadata"]["tool_name"] == "read_file"
        assert messages[1]["metadata"]["tool_name"] == "web_fetch"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
