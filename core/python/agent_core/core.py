"""
Core SDK for the AI Agent Platform.

Functional architecture: AgentCore stores only the processing pipeline (plugins via adapters),
all transformations are pure functions that take session/config and return new objects.
"""

from typing import Any, Dict, List, Optional, Iterator, AsyncIterator, Tuple
from .types import Message, Session, MessageRole
from .plugin import (
    ProviderWrapper,
    ProviderAdapter,
    FeatureWrapper,
    FeatureAdapter,
    ToolWrapper,
    ToolAdapter,
)
import uuid
import json


class AgentCore:
    """
    Stateless processing pipeline for AI Agent Platform.

    Stores registered plugin adapters (processing logic), not runtime state.
    All methods are pure functions that take session/config as parameters.
    The application layer manages sessions and configuration.
    """

    def __init__(self):
        """Initialize core with empty plugin pipeline."""
        self._provider: Optional[ProviderAdapter] = None
        self._features: List[FeatureAdapter] = []
        self._tools: List[ToolAdapter] = []

    def register_provider(
        self, plugin_class: type, extensions: Optional[List[type]] = None
    ) -> None:
        """
        Register provider plugin class with optional provider extensions.
        Extensions are loaded by the provider wrapper (same language, hot path).
        """
        wrapper = ProviderWrapper(plugin_class, extensions or [])
        self._provider = ProviderAdapter(wrapper)

    def register_feature(self, plugin_class: type) -> None:
        """Register feature plugin class."""
        wrapper = FeatureWrapper(plugin_class)
        adapter = FeatureAdapter(wrapper)
        self._features.append(adapter)

    def register_tool(self, plugin_class: type) -> None:
        """Register tool plugin class."""
        wrapper = ToolWrapper(plugin_class)
        adapter = ToolAdapter(wrapper)
        self._tools.append(adapter)

    def create_session(self, session_id: Optional[str] = None) -> Session:
        """Create new empty session (convenience function)."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        return Session(session_id=session_id, messages=[])

    def add_message(
        self,
        session: Session,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """Add message to session (pure function - returns new session)."""
        message = Message(role=role, content=content, metadata=metadata)
        new_messages: List[Message] = [*session.messages, message]
        return Session(
            session_id=session.session_id,
            messages=new_messages,
            metadata=session.metadata,
        )

    def _pre_request(
        self, session: Session, config: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Prepare state and inputs for a request; returns (messages, native_messages)."""
        assert self._provider is not None
        # Init chain: Provider → Extensions (inside provider) → Features
        self._provider.initialize(config)
        ui_state = config.get("ui_state", {})
        # Update chain: Provider → Extensions (inside provider) → Features
        if ui_state:
            self._provider.update_state(ui_state)
        for feature in self._features:
            state = self._provider.get_state()
            state = feature.init(config, state)
            state = feature.update_state(state, ui_state) if ui_state else state
            self._provider.set_state(state)
        # Build messages
        messages = [msg.to_dict() for msg in session.messages]
        # Provider-first conversion (native_base for stateless transforms)
        native_messages = self._provider.to_native_messages(messages)
        # Apply stateless transforms: Extensions then Features
        native_messages = self._provider.apply_extension_transforms(
            messages, native_messages
        )
        for feature in self._features:
            native_messages = feature.to_native_messages(messages, native_messages)
        # Initialize request chains
        self._provider.initialize_request(native_messages)
        for feature in self._features:
            state = self._provider.get_state()
            state = feature.initialize_request(native_messages, state)
            self._provider.set_state(state)
        return messages, native_messages

    def send_request(
        self, session: Session, config: Dict[str, Any]
    ) -> Tuple[Session, List[Dict[str, Any]]]:
        """
        Send request and return new session with response (pure function).
        """
        if not self._provider:
            raise RuntimeError("No provider registered")
        messages, native_messages = self._pre_request(session, config)
        final_messages_1, partial_messages, native_messages, state = (
            self._provider.call_api(native_messages)
        )

        # maybe redundant, but the API is defined this way
        final_messages_2, native_messages, state = self._provider.finalize(
            native_messages
        )

        # Combine finals from call_api and provider.finalize
        final_messages = final_messages_1 + final_messages_2

        # Feature finalize chain over all finals
        for feature in self._features:
            final_messages, native_messages, state = feature.finalize(
                final_messages, native_messages, state
            )

        # Build new session messages by appending new Message objects
        appended: List[Message] = [Message.from_dict(m) for m in final_messages]
        new_session = Session(
            session.session_id, [*session.messages, *appended], session.metadata
        )

        return new_session, final_messages

    def send_request_stream(
        self, session: Session, config: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream request and yield partials, then final session (generator function).
        """
        if not self._provider:
            raise RuntimeError("No provider registered")
        messages, native_messages = self._pre_request(session, config)
        aggregated_finals: List[Dict[str, Any]] = []

        # Stream from provider
        for native_chunk in self._provider.stream_api(native_messages):
            final_messages, partial_msgs, native_messages = (
                self._provider.process_chunk(native_chunk, native_messages)
            )
            for p in partial_msgs:
                yield {"type": "partial", "message": p}
            if final_messages:
                aggregated_finals.extend(final_messages)

        # Finalize
        final_messages, native_messages, state = self._provider.finalize(
            native_messages
        )

        # Feature finalize chain
        for feature in self._features:
            final_messages, native_messages, state = feature.finalize(
                final_messages, native_messages, state
            )

        if final_messages:
            aggregated_finals.extend(final_messages)

        appended: List[Message] = [Message.from_dict(m) for m in aggregated_finals]
        new_session = Session(
            session.session_id, [*session.messages, *appended], session.metadata
        )

        yield {"type": "final", "session": new_session, "messages": final_messages}

    async def send_request_stream_async(
        self, session: Session, config: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Async version of send_request_stream.
        """
        if not self._provider:
            raise RuntimeError("No provider registered")

        messages, native_messages = self._pre_request(session, config)
        aggregated_finals: List[Dict[str, Any]] = []

        # Stream from provider (async)
        async for native_chunk in self._provider.stream_api_async(native_messages):
            final_messages, partial_msgs, native_messages = (
                self._provider.process_chunk(native_chunk, native_messages)
            )
            for p in partial_msgs:
                yield {"type": "partial", "message": p}
            if final_messages:
                aggregated_finals.extend(final_messages)

        final_messages, native_messages, state = self._provider.finalize(
            native_messages
        )

        # Feature finalize chain
        for feature in self._features:
            final_messages, native_messages, state = feature.finalize(
                final_messages, native_messages, state
            )

        if final_messages:
            aggregated_finals.extend(final_messages)

        appended: List[Message] = [Message.from_dict(m) for m in aggregated_finals]
        new_session = Session(
            session.session_id, [*session.messages, *appended], session.metadata
        )

        yield {"type": "final", "session": new_session, "messages": final_messages}

    def get_config_schema(self) -> Dict[str, Any]:
        """Get combined config schema from all registered plugins."""
        schema: Dict[str, Any] = {}
        if self._provider:
            schema[self._provider.name] = self._provider.get_config_schema()
            # Include provider extension schemas
            for (
                name,
                ext_schema,
            ) in self._provider.get_extension_config_schemas().items():
                schema[name] = ext_schema
        for feature in self._features:
            schema[feature.name] = feature.get_config_schema()
        for tool in self._tools:
            schema[tool.name] = tool.get_config_schema()
        return schema

    def get_ui_schema(self) -> Dict[str, Any]:
        """Get combined UI schema from all registered plugins."""
        ui: Dict[str, Any] = {}
        if self._provider:
            ui[self._provider.name] = self._provider.get_ui_elements()
            # Include provider extension UI schemas
            for name, ext_ui in self._provider.get_extension_ui_elements().items():
                ui[name] = ext_ui
        for feature in self._features:
            ui[feature.name] = feature.get_ui_elements()
        for tool in self._tools:
            ui[tool.name] = tool.get_ui_elements()
        return ui

    def get_tool_schemas(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get tool schemas from all registered tool plugins."""
        schemas: List[Dict[str, Any]] = []
        for tool in self._tools:
            tool.initialize(config)
            schemas.extend(tool.get_tool_schemas())
        return schemas

    def export_session(self, session: Session, format: str = "json") -> str:
        """Export session to string."""
        if format == "json":
            return json.dumps(session.to_dict(), indent=2)
        raise ValueError(f"Unsupported format: {format}")

    def import_session(self, data: str, format: str = "json") -> Session:
        """Import session from string."""
        if format == "json":
            session_dict = json.loads(data)
            return Session.from_dict(session_dict)
        raise ValueError(f"Unsupported format: {format}")

    def discover_and_register(self, modules: List[str]) -> Dict[str, List[str]]:
        """
        Discover plugins from a list of module import paths and register them.

        Discovery is duck-typed:
        - Provider: has 'stream_api' or 'call_api'
        - Provider Extension: has 'process_chunk' and 'target_provider'
        - Tool: has 'get_tool_schemas' and 'execute_tool'
        - Feature: otherwise

        Args:

            modules: List of Python module import paths to scan

        Returns:
            Summary dict with registered plugin names by type
        """
        import importlib
        import inspect

        providers = []
        features = []
        tools = []
        extensions = []

        for mod_path in modules:
            module = importlib.import_module(mod_path)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                # Only consider classes defined in the module (not imports)
                if getattr(obj, "__module__", None) != module.__name__:
                    continue
                # Duck typing
                if hasattr(obj, "stream_api") or hasattr(obj, "call_api"):
                    providers.append(obj)
                elif hasattr(obj, "process_chunk") and hasattr(obj, "target_provider"):
                    extensions.append(obj)
                elif hasattr(obj, "get_tool_schemas") and hasattr(obj, "execute_tool"):
                    tools.append(obj)
                else:
                    features.append(obj)

        # Register a single provider (first), with matching extensions
        summary: Dict[str, List[str]] = {
            "providers": [],
            "features": [],
            "tools": [],
            "extensions": [],
        }
        if providers:
            provider_cls = providers[0]
            # Match extensions by target_provider name
            target_name = getattr(provider_cls, "name", provider_cls.__name__)
            matched_exts = [
                ext
                for ext in extensions
                if getattr(ext, "target_provider", None) in (target_name,)
            ]
            self.register_provider(provider_cls, extensions=matched_exts)
            summary["providers"].append(target_name)
            summary["extensions"].extend(
                [getattr(ext, "name", ext.__name__) for ext in matched_exts]
            )

        # Register features and tools
        for feat in features:
            self.register_feature(feat)
            summary["features"].append(getattr(feat, "name", feat.__name__))
        for tool in tools:
            self.register_tool(tool)
            summary["tools"].append(getattr(tool, "name", tool.__name__))

        return summary
