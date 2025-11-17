"""
Core SDK for the AI Agent Platform.

Functional architecture: AgentCore stores only the processing pipeline (plugins via adapters),
all transformations are pure functions that take session/config and return new objects.
"""

from typing import Any, Dict, List, Optional, Iterator, AsyncIterator, Tuple
from .types import Message, Session, MessageRole
from .plugin import (
    ProviderWrapper, ProviderAdapter,
    FeatureWrapper, FeatureAdapter,
    ToolWrapper, ToolAdapter,
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
        self,
        plugin_class: type,
        extensions: Optional[List[type]] = None
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
        return Session(session_id=session_id, messages=())
    
    def add_message(
        self,
        session: Session,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """Add message to session (pure function - returns new session)."""
        message = Message(role=role, content=content, metadata=metadata)
        new_messages = session.messages + (message,)
        return Session(
            session_id=session.session_id,
            messages=new_messages,
            metadata=session.metadata
        )
    
    def send_request(
        self,
        session: Session,
        config: Dict[str, Any]
    ) -> Tuple[Session, Dict[str, Any]]:
        """
        Send request and return new session with response (pure function).
        """
        if not self._provider:
            raise RuntimeError("No provider registered")
        
        # Initialize provider with config
        self._provider.initialize(config)
        
        # Initialize features
        for feature in self._features:
            feature.initialize(config)
        
        # Convert messages to dicts
        messages = [msg.to_dict() for msg in session.messages]
        
        # Transform through features
        for feature in self._features:
            messages = feature.transform_messages(messages, direction="to_compat")
        
        # Convert to native format
        native_messages = self._provider.to_native_messages(messages)
        
        # Build request body
        body = self._provider.build_request_body(native_messages)
        
        # Modify body through features
        for feature in self._features:
            body = feature.modify_request_body(body)
        
        # Call provider API
        response_message = self._provider.call_api(body)
        
        # Process through features
        for feature in self._features:
            response_message = feature.process_final_message(
                response_message,
                session.to_dict()
            )
        
        # Add response to session
        response_msg = Message.from_dict(response_message)
        new_messages = session.messages + (response_msg,)
        new_session = Session(
            session_id=session.session_id,
            messages=new_messages,
            metadata=session.metadata
        )
        
        return new_session, response_message
    
    def send_request_stream(
        self,
        session: Session,
        config: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream request and yield partials, then final session (generator function).
        """
        if not self._provider:
            raise RuntimeError("No provider registered")
        
        # Initialize provider with config
        self._provider.initialize(config)
        
        # Initialize features
        for feature in self._features:
            feature.initialize(config)
        
        # Convert messages to dicts
        messages = [msg.to_dict() for msg in session.messages]
        
        # Transform through features
        for feature in self._features:
            messages = feature.transform_messages(messages, direction="to_compat")
        
        # Convert to native format
        native_messages = self._provider.to_native_messages(messages)
        
        # Build request body
        body = self._provider.build_request_body(native_messages)
        
        # Modify body through features
        for feature in self._features:
            body = feature.modify_request_body(body)
        
        # Stream from provider
        for chunk in self._provider.stream_api(body):
            # Process chunk through provider (provider wrapper invokes extensions)
            partial = self._provider.process_chunk(chunk)
            if partial:
                yield {"type": "partial", "content": partial}
        
        # Finalize (provider wrapper enhances via extensions)
        final_message, metadata = self._provider.finalize()
        
        # Process through features
        for feature in self._features:
            final_message = feature.process_final_message(
                final_message,
                session.to_dict()
            )
        
        # Create new session with response
        response_msg = Message.from_dict(final_message)
        new_messages = session.messages + (response_msg,)
        new_session = Session(
            session_id=session.session_id,
            messages=new_messages,
            metadata=session.metadata
        )
        
        yield {
            "type": "final",
            "session": new_session,
            "message": final_message
        }
    
    async def send_request_stream_async(
        self,
        session: Session,
        config: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Async version of send_request_stream.
        """
        if not self._provider:
            raise RuntimeError("No provider registered")
        
        # Initialize provider with config
        self._provider.initialize(config)
        
        # Initialize features
        for feature in self._features:
            feature.initialize(config)
        
        # Convert messages to dicts
        messages = [msg.to_dict() for msg in session.messages]
        
        # Transform through features
        for feature in self._features:
            messages = feature.transform_messages(messages, direction="to_compat")
        
        # Convert to native format
        native_messages = self._provider.to_native_messages(messages)
        
        # Build request body
        body = self._provider.build_request_body(native_messages)
        
        # Modify body through features
        for feature in self._features:
            body = feature.modify_request_body(body)
        
        # Stream from provider (async)
        async for chunk in self._provider.stream_api_async(body):
            partial = self._provider.process_chunk(chunk)
            if partial:
                yield {"type": "partial", "content": partial}
        
        # Finalize (provider wrapper enhances via extensions)
        final_message, metadata = self._provider.finalize()
        
        # Process through features
        for feature in self._features:
            final_message = feature.process_final_message(
                final_message,
                session.to_dict()
            )
        
        # Create new session with response
        response_msg = Message.from_dict(final_message)
        new_messages = session.messages + (response_msg,)
        new_session = Session(
            session_id=session.session_id,
            messages=new_messages,
            metadata=session.metadata
        )
        
        yield {
            "type": "final",
            "session": new_session,
            "message": final_message
        }
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get combined config schema from all registered plugins."""
        schema: Dict[str, Any] = {}
        if self._provider:
            schema[self._provider.name] = self._provider.get_config_schema()
            # Include provider extension schemas
            for name, ext_schema in self._provider.get_extension_config_schemas().items():
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
        - Provider: has static 'stream_api' or 'call_api'
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
        summary: Dict[str, List[str]] = {"providers": [], "features": [], "tools": [], "extensions": []}
        if providers:
            provider_cls = providers[0]
            # Match extensions by target_provider name
            target_name = getattr(provider_cls, "name", provider_cls.__name__)
            matched_exts = [ext for ext in extensions if getattr(ext, "target_provider", None) in (target_name,)]
            self.register_provider(provider_cls, extensions=matched_exts)
            summary["providers"].append(target_name)
            summary["extensions"].extend([getattr(ext, "name", ext.__name__) for ext in matched_exts])
        
        # Register features and tools
        for feat in features:
            self.register_feature(feat)
            summary["features"].append(getattr(feat, "name", feat.__name__))
        for tool in tools:
            self.register_tool(tool)
            summary["tools"].append(getattr(tool, "name", tool.__name__))
        
        return summary
