"""
Provider plugin wrapper and adapter.

Manages provider plugin state and provides typed interface for provider operations.
"""

from typing import Dict, Any, List, Iterator, AsyncIterator, Tuple, Optional, cast
from .extension import ExtensionWrapper


class ProviderWrapper:
    """
    Wrapper for provider plugin managing state during streaming.

    Holds provider state and manages provider extensions in the same language (hot path).
    Adapters must not implement error handling and should delegate directly to this wrapper.
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

    def _get_state(self) -> Dict[str, Any]:
        """Internal helper to get non-optional state with validation."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        return self.state


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

    def initialize_request(self, native_messages: List[Dict[str, Any]]) -> None:
        """Run provider.initialize_request with native messages for a new turn."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        self.state = self.plugin_class.initialize_request(native_messages, self.state)

    def to_native_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert messages to provider's native format (state-validated)."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        return self.plugin_class.to_native_messages(messages, self.state)

    def call_api(self, native_messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Make non-streaming API call and allow extensions to process outputs.
        Returns (final_messages, partial_messages, native_messages_from_provider).
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        final_messages, partials, native_msgs, new_state = self.plugin_class.call_api(native_messages, self.state)
        self.state = new_state
        # Let extensions post-process the provider outputs
        provider_state = cast(Dict[str, Any], self.state)
        for ext in self._extensions:
            partials, final_messages, native_msgs, _ = ext.process_chunk(
                native_chunk=None,
                messages=native_messages,
                provider_state=provider_state,
                partial_messages=partials,
                final_messages=final_messages,
                native_messages=native_msgs,
            )
        return final_messages, partials, native_msgs

    def stream_api(self, native_messages: List[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """Make streaming API call (state-validated)."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        yield from self.plugin_class.stream_api(native_messages, self.state)

    async def stream_api_async(self, native_messages: List[Dict[str, Any]]) -> AsyncIterator[Dict[str, Any]]:
        """Make async streaming API call, preferring native async if available."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        if hasattr(self.plugin_class, "stream_api_async"):
            async for chunk in self.plugin_class.stream_api_async(native_messages, self.state):
                yield chunk
            return
        # Fallback to sync stream
        for chunk in self.plugin_class.stream_api(native_messages, self.state):
            yield chunk

    def process_chunk(self, native_chunk: Dict[str, Any], messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process provider chunk and invoke extensions (hot path).
        Updates provider and extension states.
        Returns (final_messages, partial_messages, native_messages) produced for this chunk.
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        final_messages, partial_messages, native_messages, new_state = self.plugin_class.process_chunk(
            native_chunk, messages, self.state
        )
        self.state = new_state
        # Extensions observe the same native chunk and provider outputs/state and can enhance/discard
        provider_state = cast(Dict[str, Any], self.state)
        for ext in self._extensions:
            partial_messages, final_messages, native_messages, _ = ext.process_chunk(
                native_chunk=native_chunk,
                messages=messages,
                provider_state=provider_state,
                partial_messages=partial_messages,
                final_messages=final_messages,
                native_messages=native_messages,
            )
        return final_messages, partial_messages, native_messages

    def finalize(self, messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Finalize provider turn and let extensions enhance outputs.
        Returns (final_messages, native_messages).
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        if not hasattr(self.plugin_class, "finalize"):
            return [], []
        final_messages, native_messages, new_state = self.plugin_class.finalize(messages, self.state)
        self.state = new_state
        # Allow extensions to modify final/native messages
        partials: List[Dict[str, Any]] = []
        provider_state = self._get_state()
        for ext in self._extensions:
            partials, final_messages, native_messages, _ = ext.process_chunk(
                native_chunk=None,
                messages=messages,
                provider_state=provider_state,
                partial_messages=partials,
                final_messages=final_messages,
                native_messages=native_messages,
            )
        return final_messages, native_messages


    def get_extensions_config_schemas(self) -> Dict[str, Any]:
        """Get config schemas for all extensions."""
        return {ext.name: ext.get_config_schema() for ext in self._extensions}

    def get_extensions_ui_elements(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get UI schemas for all extensions."""
        return {ext.name: ext.get_ui_elements() for ext in self._extensions}


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

    def initialize_request(self, native_messages: List[Dict[str, Any]]) -> None:
        """Prepare provider for a new request with native messages (passthrough)."""
        self.wrapper.initialize_request(native_messages)

    def to_native_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert messages to provider's native format (passthrough)."""
        return self.wrapper.to_native_messages(messages)

    def call_api(self, native_messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Make non-streaming API call (passthrough)."""
        return self.wrapper.call_api(native_messages)

    def stream_api(self, native_messages: List[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """Make streaming API call (passthrough)."""
        yield from self.wrapper.stream_api(native_messages)

    async def stream_api_async(self, native_messages: List[Dict[str, Any]]) -> AsyncIterator[Dict[str, Any]]:
        """Make async streaming API call (passthrough)."""
        async for chunk in self.wrapper.stream_api_async(native_messages):
            yield chunk

    def process_chunk(self, native_chunk: Dict[str, Any], messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process streaming chunk (provider + extensions) and update internal state.
        Returns (final_messages, partial_messages, native_messages) for this chunk.
        """
        return self.wrapper.process_chunk(native_chunk, messages)

    def finalize(self, messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Finalize messages after streaming (passthrough).
        Returns (final_messages, native_messages).
        """
        return self.wrapper.finalize(messages)

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
