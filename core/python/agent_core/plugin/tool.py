"""
Tool plugin wrapper.

Manages tool plugin state (if any) and provides typed interface.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Iterator

from ..types import ToolPlugin
from .adapters import ToolDefaultsAdapter


class ToolWrapper(ToolPlugin):
    """Wrapper for tool plugin.

    Holds tool state if needed. Many tools are stateless.
    All protocol-facing methods are implemented here with state validation.
    """

    def __init__(self, plugin_class: type) -> None:
        """Initialize wrapper with tool plugin class.

        Args:
            plugin_class: Tool plugin class (instance methods; stateless behavior)
        """
        self.plugin_class = plugin_class
        self.plugin = ToolDefaultsAdapter(plugin_class())
        self.state: Optional[Dict[str, Any]] = None
        self.name = getattr(plugin_class, "name", plugin_class.__name__)
        self.version = getattr(plugin_class, "version", "unknown")

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize tool state and return it."""
        self.state = self.plugin.init(config)
        assert self.state is not None
        return self.state

    def get_config_schema(self) -> Dict[str, Any]:
        """Get tool configuration schema."""
        return self.plugin.get_config_schema()

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Get tool UI elements."""
        return self.plugin.get_ui_elements()

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return capability/environment tags from the underlying tool if any."""
        return self.plugin.get_tags(config, models)

    def required_tags(self) -> List[str]:
        """Tags required for this tool to be exposed."""
        return self.plugin.required_tags()

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get tool schemas via plugin; requires initialized state."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.get_tool_schemas(working_state)

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute tool via plugin; requires initialized state."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.execute_tool(tool_name, arguments, working_state)

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Format tool result via plugin; requires initialized state."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.format_tool_result(result, working_state)

    def format_tool_call_preview(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> str:
        """Generate pre-execution preview via plugin; requires initialized state."""

        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.format_tool_call_preview(tool_name, arguments, working_state)

    def stream_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        """Stream tool results via plugin; requires initialized state.

        Returns an iterator of display-oriented payload dictionaries; when the
        underlying tool does not implement streaming, the iterator yields
        nothing.
        """
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.stream_tool(tool_name, arguments, working_state)

    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Convert a tool result into a UI display payload."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.to_display_format(text, result, working_state)
