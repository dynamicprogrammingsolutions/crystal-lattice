"""
Provider plugin wrapper and adapter.

Manages provider plugin state and provides typed interface for provider operations.
"""

from typing import Dict, Any, List, Iterator, AsyncIterator, Tuple, Optional
from .extension import ExtensionWrapper
from ..types import ProviderWrapperProtocol


class ProviderWrapper(ProviderWrapperProtocol):
    """
    Wrapper for provider plugin managing state during streaming.

    Holds provider state and manages provider extensions in the same language (hot path).
    Adapters must not implement error handling and should delegate directly to this wrapper.
    """

    def __init__(
        self, plugin_class: type, extension_classes: Optional[List[type]] = None
    ):
        """
        Initialize wrapper with provider plugin class and optional extensions.

        Args:
            plugin_class: Provider plugin class (instance methods; stateless behavior)
            extension_classes: Optional list of provider extension classes
        """
        self.plugin_class = plugin_class
        self.plugin = plugin_class()
        self.state: Optional[Dict[str, Any]] = None
        self.name = getattr(plugin_class, "name", plugin_class.__name__)
        self.version = getattr(plugin_class, "version", "unknown")
        self._extensions: List[ExtensionWrapper] = []
        if extension_classes:
            for ext_cls in extension_classes:
                self._extensions.append(ExtensionWrapper(ext_cls))

    @property
    def extensions(self) -> List[ExtensionWrapper]:
        """Get extension wrappers."""
        return self._extensions

    def add_extensions(self, extension_classes: List[type]) -> None:
        """Add provider extensions (same language)."""
        for ext_cls in extension_classes:
            self._extensions.append(ExtensionWrapper(ext_cls))

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize provider and extensions using shared state owned by provider wrapper.

        Args:
            config: Provider configuration
        """
        self.state = self.plugin.init(config)
        # Let extensions update shared state during init
        for ext in self._extensions:
            self.state = ext.init(config, self._get_state())
        return self._get_state()

    def _get_state(self) -> Dict[str, Any]:
        """Internal helper to get non-optional state with validation."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        return self.state

    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update shared provider state and propagate to extensions.

        Args:
            state: Current shared provider state
            updates: State updates (e.g., UI settings)
        """
        # Ensure wrapper is initialized
        _ = self._get_state()
        # Prefer provided state if given; fall back to internal
        working_state = state or self.state or {}
        new_state = self.plugin.update_state(working_state, updates)
        for ext in self._extensions:
            new_state = ext.update_state(new_state, updates)
        self.state = new_state
        return self._get_state()

    def get_config_schema(self) -> Dict[str, Any]:
        """Get provider configuration schema."""
        if hasattr(self.plugin, "get_config_schema"):
            return self.plugin.get_config_schema()
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Get provider UI elements."""
        if hasattr(self.plugin, "get_ui_elements"):
            return self.plugin.get_ui_elements()
        return []

    def get_state(self) -> Dict[str, Any]:
        """Expose a copy of the current shared state for orchestration."""
        return dict(self._get_state())

    def set_state(self, state: Dict[str, Any]) -> None:
        """Replace the current shared state (used by features)."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        self.state = state

    def initialize_request(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        """Run provider and extensions initialize_request with native messages for a new turn; returns updated state."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        new_state = self.plugin.initialize_request(native_messages, working_state)
        for ext in self._extensions:
            new_state = ext.initialize_request(native_messages, new_state)
        self.state = new_state
        return self._get_state()

    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert core messages to provider's native format (provider-first)."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        native = self.plugin.to_native_messages(messages, working_state)
        return native

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert provider-native messages back to core messages if supported; otherwise return empty list."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        if hasattr(self.plugin, "from_native_messages"):
            return self.plugin.from_native_messages(native_messages, working_state)
        return []

    def to_display_format(self, message: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Format a message for display if supported; otherwise return as-is."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        if hasattr(self.plugin, "to_display_format"):
            return self.plugin.to_display_format(message, working_state)
        return message

    def apply_extension_transforms(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply stateless extension transforms to messages with visibility of provider native messages."""
        transformed = list(messages)
        for ext in self._extensions:
            transformed = ext.to_native_messages(transformed, native_messages)
        return transformed

    def call_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        """
        Make non-streaming API call and allow extensions to finalize outputs.
        Returns (final_messages, partial_messages, native_messages_from_provider, state).
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        transformed_native = list(native_messages)
        final_messages, partials, native_msgs, new_state = self.plugin.call_api(
            transformed_native, working_state
        )
        self.state = new_state
        return final_messages, partials, native_msgs, self._get_state()

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Make streaming API call (state-validated)."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        yield from self.plugin.stream_api(native_messages, working_state)

    async def stream_api_async(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """Make async streaming API call, preferring native async if available."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        if hasattr(self.plugin, "stream_api_async"):
            async for chunk in self.plugin.stream_api_async(
                native_messages, working_state
            ):
                yield chunk
            return
        # Fallback to sync stream
        for chunk in self.plugin.stream_api(native_messages, working_state):
            yield chunk

    def process_chunk(
        self, native_chunk: Dict[str, Any], native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Process provider chunk and invoke extensions (hot path).
        Returns (final_messages, partial_messages, native_messages, state) produced for this chunk.
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        final_messages, partial_messages, native_messages, new_state = (
            self.plugin.process_chunk(native_chunk, native_messages, working_state)
        )
        # Extensions observe and can enhance/discard using shared state
        ext_state = new_state
        for ext in self._extensions:
            partial_messages, final_messages, native_messages, ext_state = (
                ext.process_chunk(
                    native_chunk=native_chunk,
                    messages=native_messages,
                    state=ext_state,
                    partial_messages=partial_messages,
                    final_messages=final_messages,
                    native_messages=native_messages,
                )
            )
        self.state = ext_state
        return final_messages, partial_messages, native_messages, self._get_state()

    def finalize(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Finalize provider turn and let extensions enhance outputs.
        Returns (final_messages, native_messages, state).
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        if not hasattr(self.plugin, "finalize"):
            return [], [], self._get_state()
        final_messages, native_messages, new_state = self.plugin.finalize(
            native_messages, working_state
        )

        # Allow extensions to modify final/native messages
        for ext in self._extensions:
            final_messages, native_messages, new_state = ext.finalize(
                final_messages=final_messages,
                native_messages=native_messages,
                state=new_state,
            )

        self.state = new_state

        return final_messages, native_messages, self._get_state()

    def detect_capabilities(self, config: Dict[str, Any]) -> List[str]:
        """Detect provider capabilities using static plugin method when available."""
        if hasattr(self.plugin_class, "detect_capabilities"):
            try:
                return list(self.plugin_class.detect_capabilities(config))
            except Exception:
                return []
        return []

    def get_extension_config_schemas(self) -> Dict[str, Any]:
        """Get config schemas for all extensions."""
        return {ext.name: ext.get_config_schema() for ext in self._extensions}

    def get_extension_ui_elements(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get UI schemas for all extensions."""
        return {ext.name: ext.get_ui_elements() for ext in self._extensions}

    def reset_state(self) -> None:
        """Discard internal shared state after request."""
        self.state = None


class ProviderAdapter(ProviderWrapperProtocol):
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

        self.name: str = wrapper.name
        self.version: str = wrapper.version

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize provider with configuration.

        Args:
            config: Provider configuration
        """
        return self.wrapper.init(config)

    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update provider state.

        Args:
            state: Current shared provider state
            updates: State updates
        """
        return self.wrapper.update_state(state, updates)

    def initialize_request(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare provider for a new request with native messages (passthrough)."""
        return self.wrapper.initialize_request(native_messages, state)

    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert messages to provider's native format (passthrough)."""
        return self.wrapper.to_native_messages(messages, state)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return self.wrapper.from_native_messages(native_messages, state)

    def to_display_format(self, message: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return self.wrapper.to_display_format(message, state)

    def apply_extension_transforms(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply extension transforms to messages using provider-native context."""
        return self.wrapper.apply_extension_transforms(messages, native_messages)

    def call_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        """Make non-streaming API call (passthrough).
        Returns (final_messages, partial_messages, native_messages, state)."""
        return self.wrapper.call_api(native_messages, state)

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Make streaming API call (passthrough)."""
        yield from self.wrapper.stream_api(native_messages, state)

    async def stream_api_async(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """Make async streaming API call (passthrough)."""
        async for chunk in self.wrapper.stream_api_async(native_messages, state):
            yield chunk

    def process_chunk(
        self, native_chunk: Dict[str, Any], native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Process streaming chunk (provider + extensions) and update internal state.
        Returns (final_messages, partial_messages, native_messages, state) for this chunk.
        """
        return self.wrapper.process_chunk(native_chunk, native_messages, state)

    def finalize(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Finalize after streaming (passthrough). Returns (final_messages, native_messages, state).
        """
        return self.wrapper.finalize(native_messages, state)

    def get_state(self) -> Dict[str, Any]:
        """Expose current shared state for orchestration."""
        return self.wrapper.get_state()

    def set_state(self, state: Dict[str, Any]) -> None:
        """Replace current shared state."""
        self.wrapper.set_state(state)

    def reset_state(self) -> None:
        """Discard internal state after request."""
        self.wrapper.state = None

    def get_config_schema(self) -> Dict[str, Any]:
        """Get provider configuration schema."""
        return self.wrapper.get_config_schema()

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Get provider UI elements."""
        return self.wrapper.get_ui_elements()

    def detect_capabilities(self, config: Dict[str, Any]) -> List[str]:
        """Detect provider capabilities (passthrough)."""
        return self.wrapper.detect_capabilities(config)

    def get_extension_config_schemas(self) -> Dict[str, Any]:
        """Get config schemas for registered extensions."""
        return self.wrapper.get_extension_config_schemas()

    def get_extension_ui_elements(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get UI schemas for registered extensions."""
        return self.wrapper.get_extension_ui_elements()
