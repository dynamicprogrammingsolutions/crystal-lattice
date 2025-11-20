"""
Tool plugin wrapper and adapter.

Manages tool plugin state (if any) and provides typed interface.
"""

from typing import Dict, Any, List, Optional


class ToolWrapper:
    """
    Wrapper for tool plugin.

    Holds tool state if needed. Many tools are stateless.
    All protocol-facing methods are implemented here with state validation.
    Adapters must delegate without performing error handling.
    """

    def __init__(self, plugin_class: type):
        """
        Initialize wrapper with tool plugin class.

        Args:
            plugin_class: Tool plugin class with static methods
        """
        self.plugin_class = plugin_class
        self.state: Optional[Dict[str, Any]] = None
        self._name = getattr(plugin_class, "name", plugin_class.__name__)
        self._version = getattr(plugin_class, "version", "unknown")

    @property
    def name(self) -> str:
        """Get tool name."""
        return self._name

    @property
    def version(self) -> str:
        """Get tool version."""
        return self._version

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize tool state.

        Args:
            config: Tool configuration
        """
        if hasattr(self.plugin_class, "init"):
            self.state = self.plugin_class.init(config)
        else:
            # Stateless tool, just store config and default state buckets
            self.state = {
                "config": config,
                "capabilities": [],
                "runtime_state": {},
                "ui_state": {},
            }

    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        Update tool state.

        Args:
            updates: State updates
        """
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")

        if hasattr(self.plugin_class, "update_state"):
            self.state = self.plugin_class.update_state(self.state, updates)
        else:
            # Simple config update
            self.state = {
                **self.state,
                "config": {**self.state.get("config", {}), **updates},
            }

    def get_config_schema(self) -> Dict[str, Any]:
        """Get tool configuration schema."""
        if hasattr(self.plugin_class, "get_config_schema"):
            return self.plugin_class.get_config_schema()
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Get tool UI elements."""
        if hasattr(self.plugin_class, "get_ui_elements"):
            return self.plugin_class.get_ui_elements()
        return []

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get tool schemas via plugin if implemented; otherwise empty list."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        if hasattr(self.plugin_class, "get_tool_schemas"):
            return self.plugin_class.get_tool_schemas(self.state)
        return []

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool via plugin; requires initialized state."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        return self.plugin_class.execute_tool(tool_name, arguments, self.state)

    def format_tool_result(self, result: Dict[str, Any]) -> str:
        """Format tool result via plugin if implemented; otherwise default formatting."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        if hasattr(self.plugin_class, "format_tool_result"):
            return self.plugin_class.format_tool_result(result, self.state)
        if result.get("success"):
            return f"Result: {result.get('result')}"
        else:
            return f"Error: {result.get('error')}"


class ToolAdapter:
    """
    Passthrough adapter for tool plugins.

    Performs no validation or error handling; delegates to ToolWrapper which
    enforces protocol and state.
    """

    def __init__(self, wrapper: ToolWrapper):
        """
        Initialize adapter with tool wrapper.

        Args:
            wrapper: ToolWrapper instance
        """
        self.wrapper = wrapper

    @property
    def name(self) -> str:
        """Get tool name."""
        return self.wrapper.name

    @property
    def version(self) -> str:
        """Get tool version."""
        return self.wrapper.version

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize tool with configuration.

        Args:
            config: Tool configuration
        """
        self.wrapper.initialize(config)

    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        Update tool state.

        Args:
            updates: State updates
        """
        self.wrapper.update_state(updates)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get tool schemas (passthrough)."""
        return self.wrapper.get_tool_schemas()

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool (passthrough)."""
        return self.wrapper.execute_tool(tool_name, arguments)

    def format_tool_result(self, result: Dict[str, Any]) -> str:
        """Format tool result for display (passthrough)."""
        return self.wrapper.format_tool_result(result)

    def get_config_schema(self) -> Dict[str, Any]:
        """Get tool configuration schema."""
        return self.wrapper.get_config_schema()

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Get tool UI elements."""
        return self.wrapper.get_ui_elements()
