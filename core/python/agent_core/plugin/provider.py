"""
Provider plugin wrapper and adapter.

Manages provider plugin state and provides typed interface for provider operations.
"""

from typing import Dict, Any, List, Iterator, AsyncIterator, Tuple, Optional
from .extension import ExtensionWrapper


class ProviderWrapper:
    """
    Wrapper for provider plugin managing state during streaming.
    
    Holds provider state and accumulates native messages during streaming.
    Manages provider extensions in the same language (hot path).
    All protocol methods are exposed here with state validation; adapters must
    not implement error handling and should delegate directly to this wrapper.
    """
    
    def __init__(self, plugin_class: type, extension_classes: Optional[List[type]] = None):
        """
        Initialize wrapper with provider plugin class and optional extensions.
        
        Args:
            plugin_class: Provider plugin class with static methods
            extension_classes: Optional list of provider extension classes
        """
        self.plugin_class = plugin_class
        self.state: Optional[Dict[str, Any]] = None
        self._name = getattr(plugin_class, "name", plugin_class.__name__)
        self._version = getattr(plugin_class, "version", "unknown")
        self._extensions: List[ExtensionWrapper] = []
        if extension_classes:
            for ext_cls in extension_classes:
                self._extensions.append(ExtensionWrapper(ext_cls))
    
    @property
    def name(self) -> str:
        """Get provider name."""
        return self._name
    
    @property
    def version(self) -> str:
        """Get provider version."""
        return self._version
    
    @property
    def extensions(self) -> List[ExtensionWrapper]:
        """Get extension wrappers."""
        return self._extensions
    
    def add_extensions(self, extension_classes: List[type]) -> None:
        """Add provider extensions (same language)."""
        for ext_cls in extension_classes:
            self._extensions.append(ExtensionWrapper(ext_cls))
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize provider and extensions state.
        
        Args:
            config: Provider configuration
        """
        self.state = self.plugin_class.init(config)
        for ext in self._extensions:
            ext.initialize(config)
    
    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        Update provider state.
        
        Args:
            updates: State updates
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        self.state = self.plugin_class.update_state(self.state, updates)
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get provider configuration schema."""
        if hasattr(self.plugin_class, "get_config_schema"):
            return self.plugin_class.get_config_schema()
        return {}
    
    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Get provider UI elements."""
        if hasattr(self.plugin_class, "get_ui_elements"):
            return self.plugin_class.get_ui_elements()
        return []
    
    def process_chunk(self, native_chunk: Dict[str, Any]) -> str:
        """
        Process provider chunk and invoke extensions (hot path).
        Updates provider and extension states.
        Returns provider partial content.
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        partial, new_state = self.plugin_class.process_chunk(native_chunk, self.state)
        self.state = new_state
        # Extensions observe the same native chunk and provider state
        for ext in self._extensions:
            ext.process_chunk(native_chunk, self.state)
        return partial
    
    def finalize(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Finalize provider message and enhance via extensions.
        Returns (final_message, final_metadata). Also ensures metadata is
        merged into message["metadata"].
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        message, metadata = self.plugin_class.finalize(self.state)
        for ext in self._extensions:
            message, metadata = ext.enhance_final_message(message, metadata)
        # Ensure metadata is present on the message
        msg_meta = message.get("metadata", {})
        message["metadata"] = {**msg_meta, **metadata}
        return message, metadata
    
    def get_extensions_config_schemas(self) -> Dict[str, Any]:
        """Get config schemas for all extensions."""
        return {ext.name: ext.get_config_schema() for ext in self._extensions}
    
    def get_extensions_ui_elements(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get UI schemas for all extensions."""
        return {ext.name: ext.get_ui_elements() for ext in self._extensions}

    def to_native_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert messages to provider's native format (state-validated)."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        return self.plugin_class.to_native_messages(messages, self.state)

    def build_request_body(self, native_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build request body for API call (state-validated)."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        return self.plugin_class.build_request_body(native_messages, self.state)

    def call_api(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Make non-streaming API call (state-validated)."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        return self.plugin_class.call_api(body, self.state)

    def stream_api(self, body: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Make streaming API call (state-validated)."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        yield from self.plugin_class.stream_api(body, self.state)

    async def stream_api_async(self, body: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Make async streaming API call, preferring native async if available."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        if hasattr(self.plugin_class, "stream_api_async"):
            async for chunk in self.plugin_class.stream_api_async(body, self.state):
                yield chunk
            return
        # Fallback to sync stream
        for chunk in self.plugin_class.stream_api(body, self.state):
            yield chunk


class ProviderAdapter:
    """
    Passthrough adapter for provider plugins.
    
    This adapter performs no validation or error handling and delegates all
    operations to the ProviderWrapper, which enforces protocol and state.
    """
    
    def __init__(self, wrapper: ProviderWrapper):
        """
        Initialize adapter with provider wrapper.
        
        Args:
            wrapper: ProviderWrapper instance
        """
        self.wrapper = wrapper
    
    @property
    def name(self) -> str:
        """Get provider name."""
        return self.wrapper.name
    
    @property
    def version(self) -> str:
        """Get provider version."""
        return self.wrapper.version
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize provider with configuration.
        
        Args:
            config: Provider configuration
        """
        self.wrapper.initialize(config)
    
    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        Update provider state.
        
        Args:
            updates: State updates
        """
        self.wrapper.update_state(updates)
    
    def to_native_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert messages to provider's native format (passthrough)."""
        return self.wrapper.to_native_messages(messages)
    
    def build_request_body(self, native_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build API request body (passthrough)."""
        return self.wrapper.build_request_body(native_messages)
    
    def process_chunk(self, native_chunk: Dict[str, Any]) -> str:
        """
        Process streaming chunk (provider + extensions) and update internal state.
        Returns partial content string from provider.
        """
        return self.wrapper.process_chunk(native_chunk)
    
    def finalize(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Finalize message and enhance via extensions.
        Returns (message, metadata).
        """
        return self.wrapper.finalize()
    
    def call_api(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Make non-streaming API call (passthrough)."""
        return self.wrapper.call_api(body)
    
    def stream_api(self, body: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Make streaming API call (passthrough)."""
        yield from self.wrapper.stream_api(body)
    
    async def stream_api_async(self, body: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Make async streaming API call (passthrough)."""
        async for chunk in self.wrapper.stream_api_async(body):
            yield chunk
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get provider configuration schema."""
        return self.wrapper.get_config_schema()
    
    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Get provider UI elements."""
        return self.wrapper.get_ui_elements()
    
    def get_extension_config_schemas(self) -> Dict[str, Any]:
        """Get config schemas for registered extensions."""
        return self.wrapper.get_extensions_config_schemas()
    
    def get_extension_ui_elements(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get UI schemas for registered extensions."""
        return self.wrapper.get_extensions_ui_elements()
