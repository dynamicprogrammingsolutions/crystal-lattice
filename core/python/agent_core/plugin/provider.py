"""
Provider plugin wrapper and adapter.

Manages provider plugin state and provides typed interface for provider operations.
"""

from typing import Dict, Any, List, Iterator, AsyncIterator, Tuple, Optional, cast
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
            plugin_class: Provider plugin class with static methods
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

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize provider and extensions using shared state owned by provider wrapper.

        Args:
            config: Provider configuration
        """
        self.state = self.plugin.init(config)
        # Let extensions update shared state during init
        for ext in self._extensions:
            self.state = ext.init(config, self._get_state())

    def _get_state(self) -> Dict[str, Any]:
        """Internal helper to get non-optional state with validation."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        return self.state

    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        Update shared provider state and propagate to extensions.

        Args:
            updates: State updates (e.g., UI settings)
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        self.state = self.plugin.update_state(self.state, updates)
        for ext in self._extensions:
            self.state = ext.update_state(self._get_state(), updates)

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

    def initialize_request(self, native_messages: List[Dict[str, Any]]) -> None:
        """Run provider and extensions initialize_request with native messages for a new turn."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        self.state = self.plugin.initialize_request(native_messages, self.state)
        for ext in self._extensions:
            self.state = ext.initialize_request(native_messages, self._get_state())

    def to_native_messages(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert core messages to provider's native format (provider-first)."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        native = self.plugin.to_native_messages(messages, self.state)
        return native

    def apply_extension_transforms(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply stateless extension transforms to messages with visibility of provider native messages."""
        transformed = list(messages)
        for ext in self._extensions:
            transformed = ext.to_native_messages(transformed, native_messages)
        return transformed

    def call_api(
        self, native_messages: List[Dict[str, Any]]
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        """
        Make non-streaming API call and allow extensions to finalize outputs.
        Returns (final_messages, partial_messages, native_messages_from_provider, state).
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        # Call provider API directly; pre-request transforms were already applied in core
        transformed_native = list(native_messages)
        final_messages, partials, native_msgs, new_state = self.plugin.call_api(
            transformed_native, self.state
        )
        self.state = new_state
        return final_messages, partials, native_msgs, new_state

    def stream_api(
        self, native_messages: List[Dict[str, Any]]
    ) -> Iterator[Dict[str, Any]]:
        """Make streaming API call (state-validated)."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        yield from self.plugin.stream_api(native_messages, self.state)

    async def stream_api_async(
        self, native_messages: List[Dict[str, Any]]
    ) -> AsyncIterator[Dict[str, Any]]:
        """Make async streaming API call, preferring native async if available."""
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        if hasattr(self.plugin, "stream_api_async"):
            async for chunk in self.plugin.stream_api_async(
                native_messages, self.state
            ):
                yield chunk
            return
        # Fallback to sync stream
        for chunk in self.plugin.stream_api(native_messages, self.state):
            yield chunk

    def process_chunk(
        self, native_chunk: Dict[str, Any], native_messages: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process provider chunk and invoke extensions (hot path).
        Returns (final_messages, partial_messages, native_messages) produced for this chunk.
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        final_messages, partial_messages, native_messages, new_state = (
            self.plugin.process_chunk(native_chunk, native_messages, self.state)
        )
        self.state = new_state
        # Extensions observe and can enhance/discard using shared state
        for ext in self._extensions:
            partial_messages, final_messages, native_messages, self.state = (
                ext.process_chunk(
                    native_chunk=native_chunk,
                    messages=native_messages,
                    state=self._get_state(),
                    partial_messages=partial_messages,
                    final_messages=final_messages,
                    native_messages=native_messages,
                )
            )
        return final_messages, partial_messages, native_messages

    def finalize(
        self, native_messages: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Finalize provider turn and let extensions enhance outputs.
        Returns (final_messages, native_messages, state).
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        if not hasattr(self.plugin, "finalize"):
            return [], [], self._get_state()
        final_messages, native_messages, new_state = self.plugin.finalize(
            native_messages, self.state
        )

        # Allow extensions to modify final/native messages
        for ext in self._extensions:
            final_messages, native_messages, new_state = ext.finalize(
                final_messages=final_messages,
                native_messages=native_messages,
                state=new_state,
            )

        self.state = new_state

        return final_messages, native_messages, new_state

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

    def to_native_messages(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert messages to provider's native format (passthrough)."""
        return self.wrapper.to_native_messages(messages)

    def apply_extension_transforms(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply extension transforms to messages using provider-native context."""
        return self.wrapper.apply_extension_transforms(messages, native_messages)

    def call_api(
        self, native_messages: List[Dict[str, Any]]
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        """Make non-streaming API call (passthrough).
        Returns (final_messages, partial_messages, native_messages, state)."""
        return self.wrapper.call_api(native_messages)

    def stream_api(
        self, native_messages: List[Dict[str, Any]]
    ) -> Iterator[Dict[str, Any]]:
        """Make streaming API call (passthrough)."""
        yield from self.wrapper.stream_api(native_messages)

    async def stream_api_async(
        self, native_messages: List[Dict[str, Any]]
    ) -> AsyncIterator[Dict[str, Any]]:
        """Make async streaming API call (passthrough)."""
        async for chunk in self.wrapper.stream_api_async(native_messages):
            yield chunk

    def process_chunk(
        self, native_chunk: Dict[str, Any], native_messages: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process streaming chunk (provider + extensions) and update internal state.
        Returns (final_messages, partial_messages, native_messages) for this chunk.
        """
        return self.wrapper.process_chunk(native_chunk, native_messages)

    def finalize(
        self, native_messages: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Finalize after streaming (passthrough). Returns (final_messages, native_messages, state).
        """
        return self.wrapper.finalize(native_messages)

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

    def get_extension_config_schemas(self) -> Dict[str, Any]:
        """Get config schemas for registered extensions."""
        return self.wrapper.get_extension_config_schemas()

    def get_extension_ui_elements(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get UI schemas for registered extensions."""
        return self.wrapper.get_extension_ui_elements()
