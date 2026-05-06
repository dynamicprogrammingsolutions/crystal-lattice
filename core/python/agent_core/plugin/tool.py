"""
Tool plugin wrapper.

Manages tool plugin state (if any) and provides typed interface.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import inspect
from typing import Dict, Any, List, Optional, Iterator, AsyncIterator

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
        self.prepared: Optional[Dict[str, Any]] = None
        self.name = getattr(plugin_class, "name", plugin_class.__name__)
        self.version = getattr(plugin_class, "version", "unknown")
        self.priority = getattr(plugin_class, "priority", 100)

    @staticmethod
    def _state_or_default(
        state: Optional[Dict[str, Any]],
        default_state: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if isinstance(state, dict):
            return state
        if isinstance(default_state, dict):
            return default_state
        raise RuntimeError("Tool not initialized")

    @staticmethod
    def _prepared_or_default(
        prepared: Optional[Dict[str, Any]],
        default_prepared: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if prepared is not None:
            return prepared
        return default_prepared

    @staticmethod
    def _run_awaitable_blocking(
        awaitable: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        app = None
        if isinstance(context, dict):
            app = context.get("app") or context.get("application")
        runner = getattr(app, "run_awaitable_blocking", None)
        if callable(runner):
            return runner(awaitable)
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(awaitable)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, awaitable)
            return future.result()

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize tool state and return it."""
        self.state = self.plugin.init(config)
        self.prepared = None
        assert self.state is not None
        return self.state

    def get_config_schema(self) -> Dict[str, Any]:
        """Get tool configuration schema."""
        return self.plugin.get_config_schema()

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Get tool UI elements."""
        return self.plugin.get_ui_elements(config, context)

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

    def prepare(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Prepare the tool synchronously, blocking on async hooks when needed."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = self._state_or_default(state, self.state)
        impl_sync = self.plugin._get_impl_method("prepare", ToolPlugin)
        if impl_sync is not None:
            self.prepared = self.plugin.prepare(config, working_state, context=context)
            return self.prepared
        impl_async = getattr(self.plugin.impl, "prepare_async", None)
        if callable(impl_async):
            result = self.plugin._call_with_optional_kwargs(
                impl_async,
                config,
                working_state,
                context=context,
            )
            if inspect.isawaitable(result):
                result = self._run_awaitable_blocking(result, context=context)
            self.prepared = result if isinstance(result, dict) else {}
            return self.prepared
        self.prepared = {}
        return self.prepared

    async def prepare_async(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Prepare the tool asynchronously; prefers async implementations."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = self._state_or_default(state, self.state)
        self.prepared = await self.plugin.prepare_async(
            config,
            working_state,
            context=context,
        )
        return self.prepared

    def get_tool_schemas(
        self,
        state: Dict[str, Any],
        *,
        prepared: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Get tool schemas via plugin; requires initialized state."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = self._state_or_default(state, self.state)
        working_prepared = self._prepared_or_default(prepared, self.prepared)
        return self.plugin.get_tool_schemas(working_state, prepared=working_prepared)

    def get_tool_interop_contribution(
        self, state: Dict[str, Any]
    ) -> ToolInteropContribution:
        """Return tool-contributed interop accessors/adapters."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = self._state_or_default(state, self.state)
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
        prepared: Optional[Dict[str, Any]] = None,
    ) -> Optional[bool]:
        """Return whether this tool can handle the inspected tool call."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = self._state_or_default(state, self.state)
        working_prepared = self._prepared_or_default(prepared, self.prepared)
        return self.plugin.can_handle_tool_call(
            tool_name,
            payload,
            working_state,
            payload_kind=payload_kind,
            payload_format=payload_format,
            payload_metadata=payload_metadata,
            tool_call=tool_call,
            tool_schema=tool_schema,
            prepared=working_prepared,
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
        prepared: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute tool via plugin; requires initialized state."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = self._state_or_default(state, self.state)
        working_prepared = self._prepared_or_default(prepared, self.prepared)
        impl_sync = self.plugin._get_impl_method("execute_tool", ToolPlugin)
        if impl_sync is None:
            impl_async = getattr(self.plugin.impl, "execute_tool_async", None)
            if callable(impl_async):
                return self._run_awaitable_blocking(
                    self.plugin.execute_tool_async(
                        tool_name,
                        payload,
                        working_state,
                        payload_kind=payload_kind,
                        payload_format=payload_format,
                        payload_metadata=payload_metadata,
                        tool_call=tool_call,
                        cancellation=cancellation,
                        context=context,
                        prepared=working_prepared,
                    ),
                    context=context,
                )
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
            prepared=working_prepared,
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

    def materialize_interception_prompt(
        self,
        state: Dict[str, Any],
        *,
        schema_id: str,
        schema_params: Dict[str, Any],
        tool_call_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.materialize_interception_prompt(
            working_state,
            schema_id=schema_id,
            schema_params=schema_params,
            tool_call_id=tool_call_id,
        )

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
        prepared: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute tool via the canonical async hook when available."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = self._state_or_default(state, self.state)
        working_prepared = self._prepared_or_default(prepared, self.prepared)
        return await self.plugin.execute_tool_async(
            tool_name,
            payload,
            working_state,
            payload_kind=payload_kind,
            payload_format=payload_format,
            payload_metadata=payload_metadata,
            tool_call=tool_call,
            cancellation=cancellation,
            context=context,
            prepared=working_prepared,
        )

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> Any:
        """Format tool result via plugin; requires initialized state."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = self._state_or_default(state, self.state)
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
        prepared: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate pre-execution preview via plugin; requires initialized state."""

        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = self._state_or_default(state, self.state)
        working_prepared = self._prepared_or_default(prepared, self.prepared)
        return self.plugin.format_tool_call_preview(
            tool_name,
            payload,
            working_state,
            payload_kind=payload_kind,
            payload_format=payload_format,
            payload_metadata=payload_metadata,
            tool_call=tool_call,
            prepared=working_prepared,
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
        prepared: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Stream tool results via plugin; requires initialized state.

        Returns an iterator of display-oriented payload dictionaries; when the
        underlying tool does not implement streaming, the iterator yields
        nothing.
        """
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = self._state_or_default(state, self.state)
        working_prepared = self._prepared_or_default(prepared, self.prepared)
        impl_sync = self.plugin._get_impl_method("stream_tool", ToolPlugin)
        if impl_sync is not None:
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
                prepared=working_prepared,
            )

        async def _collect_async_chunks() -> List[Dict[str, Any]]:
            chunks: List[Dict[str, Any]] = []
            async for chunk in self.plugin.stream_tool_async(
                tool_name,
                payload,
                working_state,
                payload_kind=payload_kind,
                payload_format=payload_format,
                payload_metadata=payload_metadata,
                tool_call=tool_call,
                cancellation=cancellation,
                context=context,
                prepared=working_prepared,
            ):
                if isinstance(chunk, dict):
                    chunks.append(chunk)
            return chunks

        chunks = self._run_awaitable_blocking(_collect_async_chunks(), context=context)

        def _iter_chunks() -> Iterator[Dict[str, Any]]:
            for chunk in chunks or []:
                if isinstance(chunk, dict):
                    yield chunk

        return _iter_chunks()

    async def stream_tool_async(
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
        prepared: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream tool results asynchronously; prefers async implementations."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = self._state_or_default(state, self.state)
        working_prepared = self._prepared_or_default(prepared, self.prepared)
        async for chunk in self.plugin.stream_tool_async(
            tool_name,
            payload,
            working_state,
            payload_kind=payload_kind,
            payload_format=payload_format,
            payload_metadata=payload_metadata,
            tool_call=tool_call,
            cancellation=cancellation,
            context=context,
            prepared=working_prepared,
        ):
            yield chunk

    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Convert a tool result into a UI display payload."""
        if self.state is None:
            raise RuntimeError(f"Tool {self.name} not initialized")
        working_state = self._state_or_default(state, self.state)
        return self.plugin.to_display_format(text, result, working_state)
