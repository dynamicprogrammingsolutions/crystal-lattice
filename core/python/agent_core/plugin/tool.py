"""
Tool plugin wrapper.

Manages tool plugin state (if any) and provides typed interface.
"""

from typing import Dict, Any, List, Optional
from ..types import ToolPlugin


class ToolWrapper(ToolPlugin):
    """
    Wrapper for tool plugin.

    Holds tool state if needed. Many tools are stateless.
    All protocol-facing methods are implemented here with state validation.
    """

    def __init__(self, plugin_class: type):
        """
        Initialize wrapper with tool plugin class.

        Args:
            plugin_class: Tool plugin class (instance methods; stateless behavior)
        """
        self.plugin_class = plugin_class
        self.plugin = plugin_class()
        self.state: Optional[Dict[str, Any]] = None
        self.name = getattr(plugin_class, "name", plugin_class.__name__)
        self.version = getattr(plugin_class, "version", "unknown")

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize tool state and return it.

        Args:
            config: Tool configuration
        """
        if hasattr(self.plugin, "init"):
            self.state = self.plugin.init(config)
        else:
            # Stateless tool, just store provided config under a single key.
            self.state = {"config": config}
        assert self.state is not None
        return self.state

    def get_config_schema(self) -> Dict[str, Any]:
        """Get tool configuration schema."""
        if hasattr(self.plugin, "get_config_schema"):
            return self.plugin.get_config_schema()
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Get tool UI elements."""
        if hasattr(self.plugin, "get_ui_elements"):
            return self.plugin.get_ui_elements()
        return []

    def get_tags(

        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return capability/environment tags from the underlying tool if any."""
        if hasattr(self.plugin, "get_tags"):
            return self.plugin.get_tags(config, models)
        return []

    def required_tags(self) -> List[str]:
        """Tags required for this tool to be exposed."""
        if hasattr(self.plugin, "required_tags"):
            return self.plugin.required_tags()
        return []
 
    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get tool schemas via plugin if implemented; otherwise empty list."""

        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        if hasattr(self.plugin, "get_tool_schemas"):
            return self.plugin.get_tool_schemas(working_state)
        return []

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool via plugin; requires initialized state."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.execute_tool(tool_name, arguments, working_state)

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Format tool result via plugin if implemented; otherwise default formatting."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        if hasattr(self.plugin, "format_tool_result"):
            return self.plugin.format_tool_result(result, working_state)
        if result.get("success"):
            return f"Result: {result.get('result')}"
        else:
            return f"Error: {result.get('error')}"
