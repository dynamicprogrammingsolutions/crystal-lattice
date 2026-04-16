"""
Tool plugin wrapper.

Manages tool plugin state (if any) and provides typed interface.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Iterator

from ..types import ToolPlugin
from ..tool_interop import ToolInteropContribution
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
        self.priority = getattr(plugin_class, "priority", 100)

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize tool state and return it."""
        self.state = self.plugin.init(config)
        assert self.state is not None
        return self.state

    def get_config_schema(self) -> Dict[str, Any]:
        """Get tool configuration schema."""
        return self.plugin.get_config_schema()

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Get tool UI elements."""
        return self.plugin.get_ui_elements(config, tags, models)

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

    def forbidden_tags(self) -> List[str]:
        """Tags that must NOT be present for this tool to be exposed."""
        return self.plugin.forbidden_tags()

    def is_enabled(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Optional[bool]:
        """Return whether this tool should be enabled given the context."""
        return self.plugin.is_enabled(config, tags, models, context)

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get tool schemas via plugin; requires initialized state."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.get_tool_schemas(working_state)

    def get_tool_interop_contribution(self, state: Dict[str, Any]) -> ToolInteropContribution:
        """Return tool-contributed interop accessors/adapters."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.get_tool_interop_contribution(working_state)

    def can_handle_tool_call(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        tool_schema: Optional[Dict[str, Any]] = None,
    ) -> Optional[bool]:
        """Return whether this tool can handle the inspected tool call."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.can_handle_tool_call(
            tool_name,
            payload,
            working_state,
            payload_kind=payload_kind,
            payload_format=payload_format,
            payload_metadata=payload_metadata,
            tool_call=tool_call,
            tool_schema=tool_schema,
        )

    def execute_tool(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        cancellation: Any | None = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute tool via plugin; requires initialized state."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.execute_tool(
            tool_name,
            payload,
            working_state,
            payload_kind=payload_kind,
            payload_format=payload_format,
            payload_metadata=payload_metadata,
            tool_call=tool_call,
            cancellation=cancellation,
            context=context,
        )

    def intercept_tool_call(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.intercept_tool_call(payload, context, working_state)

    def intercept_tool_result(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.intercept_tool_result(payload, context, working_state)

    async def execute_tool_async(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        cancellation: Any | None = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute tool via plugin asynchronously; requires initialized state.
        
        This method supports tools with async execute_tool implementations.
        If the underlying tool's execute_tool is a coroutine function,
        it will be awaited correctly.
        """
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        
        # Check if the underlying implementation has an async execute_tool
        import inspect
        impl_fn = getattr(self.plugin.impl, "execute_tool", None)
        if impl_fn is not None and callable(impl_fn):
            result = self.plugin._call_with_optional_kwargs(
                impl_fn,
                tool_name,
                payload,
                working_state,
                payload_kind=payload_kind,
                payload_format=payload_format,
                payload_metadata=payload_metadata,
                tool_call=tool_call,
                cancellation=cancellation,
                context=context,
            )
            if inspect.isawaitable(result):
                result = await result
            if isinstance(result, dict):
                return result
            return {"success": False, "error": "invalid tool result"}
        
        # Fall back to adapter (sync)
        return self.plugin.execute_tool(
            tool_name,
            payload,
            working_state,
            payload_kind=payload_kind,
            payload_format=payload_format,
            payload_metadata=payload_metadata,
            tool_call=tool_call,
            cancellation=cancellation,
            context=context,
        )

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Format tool result via plugin; requires initialized state."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.format_tool_result(result, working_state)

    def format_tool_call_preview(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate pre-execution preview via plugin; requires initialized state."""

        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.format_tool_call_preview(
            tool_name,
            payload,
            working_state,
            payload_kind=payload_kind,
            payload_format=payload_format,
            payload_metadata=payload_metadata,
            tool_call=tool_call,
        )

    def stream_tool(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        cancellation: Any | None = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Stream tool results via plugin; requires initialized state.

        Returns an iterator of display-oriented payload dictionaries; when the
        underlying tool does not implement streaming, the iterator yields
        nothing.
        """
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.stream_tool(
            tool_name,
            payload,
            working_state,
            payload_kind=payload_kind,
            payload_format=payload_format,
            payload_metadata=payload_metadata,
            tool_call=tool_call,
            cancellation=cancellation,
            context=context,
        )

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
