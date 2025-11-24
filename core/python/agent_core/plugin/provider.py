"""
Provider plugin wrapper and streaming mixin.

Manages provider plugin state and provides typed interface for provider operations.
"""

from typing import Dict, Any, List, Iterator, AsyncIterator, Tuple, Optional
from .extension import ExtensionWrapper
from ..types import ProviderPlugin


class ProviderStreamMixin:
    """
    Mixin that provides optimized streaming helpers which consume provider-native
    chunks internally and yield processed partial/final messages. This avoids
    passing raw chunks back to the core, reducing overhead on the hot path.
    """

    _last_native_messages: List[Dict[str, Any]]

    def stream_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream provider results while processing chunks internally.

        Yields dict events:
        - {"type": "partial", "message": <partial_message>}
        - {"type": "final_messages", "messages": <list_of_final_messages>}
        """
        # Resolve initial state via wrapper; error if uninitialized
        try:
            working_state = state or self._get_state()  # type: ignore[attr-defined]
        except Exception:
            raise RuntimeError(f"Provider {self.name} not initialized")  # type: ignore[attr-defined]
        # Initialize full native history for this turn
        self._last_native_messages = list(native_messages)  # type: ignore[attr-defined]
        current_native = self._last_native_messages
        for native_chunk in self.plugin.stream_api(current_native, working_state):  # type: ignore[attr-defined]
            finals, partials, current_native, working_state = self.process_chunk(  # type: ignore[misc]
                native_chunk, current_native, working_state
            )
            # track latest native messages (full history)
            self._last_native_messages = current_native  # type: ignore[attr-defined]
            # yield partials first
            for p in partials:
                yield {"type": "partial", "message": p}
            if finals:
                yield {"type": "final_messages", "messages": finals}

    async def stream_messages_async(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Async variant of stream_messages. Prefers native async streaming when available.
        """
        # Resolve initial state via wrapper; error if uninitialized
        try:
            working_state = state or self._get_state()  # type: ignore[attr-defined]
        except Exception:
            raise RuntimeError(f"Provider {self.name} not initialized")  # type: ignore[attr-defined]
        current_native = list(native_messages)

        if hasattr(self.plugin, "stream_api_async"):  # type: ignore[attr-defined]
            async for native_chunk in self.plugin.stream_api_async(  # type: ignore[attr-defined]
                current_native, working_state
            ):
                finals, partials, current_native, working_state = self.process_chunk(  # type: ignore[misc]
                    native_chunk, current_native, working_state
                )
                self._last_native_messages = current_native  # type: ignore[attr-defined]
                for p in partials:
                    yield {"type": "partial", "message": p}
                if finals:
                    yield {"type": "final_messages", "messages": finals}
            return

        # Fallback to sync stream
        for native_chunk in self.plugin.stream_api(current_native, working_state):  # type: ignore[attr-defined]
            finals, partials, current_native, working_state = self.process_chunk(  # type: ignore[misc]
                native_chunk, current_native, working_state
            )
            self._last_native_messages = current_native  # type: ignore[attr-defined]
            for p in partials:
                yield {"type": "partial", "message": p}
            if finals:
                yield {"type": "final_messages", "messages": finals}

    def get_last_native_messages(self) -> List[Dict[str, Any]]:
        """Expose the latest accumulated native messages tracked during streaming."""
        # type: ignore[attr-defined]
        return getattr(self, "_last_native_messages", [])


class ProviderWrapper(ProviderStreamMixin, ProviderPlugin):
    """
    Wrapper for provider plugin managing state during streaming.

    Holds provider state and manages provider extensions in the same language (hot path).
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
        self._last_native_messages: List[Dict[str, Any]] = []
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
        # Start full native history at request boundary
        self._last_native_messages = list(native_messages)
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
        """Apply stateless extension transforms to provider-native messages with visibility of core messages."""
        transformed_native = list(native_messages)
        for ext in self._extensions:
            transformed_native = ext.to_native_messages(messages, transformed_native)
        return transformed_native

    def _merge_history(self, base: List[Dict[str, Any]], returned: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge plugin-returned native messages into base, ensuring full history without duplication."""
        if not returned:
            return base
        if len(returned) >= len(base) and returned[: len(base)] == base:
            return returned
        return [*base, *returned]

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
        # Initialize history baseline
        self._last_native_messages = list(native_messages)
        final_messages, partials, native_returned, new_state = self.plugin.call_api(
            self._last_native_messages, working_state
        )
        self.state = new_state
        # Merge to full history and track
        full_history = self._merge_history(self._last_native_messages, native_returned)
        self._last_native_messages = full_history
        return final_messages, partials, full_history, self._get_state()

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
        # Use the provided full native history directly
        full_history = list(native_messages)
        final_messages, partial_messages, returned_history, new_state = (
            self.plugin.process_chunk(native_chunk, full_history, working_state)
        )
        # Replace history with provider-returned history
        full_history = returned_history
        # Let extensions transform partials/finals/native history in order
        ext_state = new_state
        for ext in self._extensions:
            partial_messages, final_messages, full_history, ext_state = (
                ext.process_chunk(
                    native_chunk=native_chunk,
                    state=ext_state,
                    partial_messages=partial_messages,
                    final_messages=final_messages,
                    native_messages=full_history,
                )
            )
        self.state = ext_state
        
        #print("\nchunk:",native_chunk,"\n","partial_messages:",partial_messages," final_messages:",final_messages, "accumulated:", (self.state or {}).get("partial",{}))
        
        if (len(final_messages) > 0):
            print("\nfinal_messages:",final_messages, "accumulated:", (self.state or {}).get("partial",{}))
            
        # if (len(partial_messages) > 0):
        #     print("partial_messages:",partial_messages)
        
        # Convert partial messages (provider-native) to core using provider + extensions
        core_partials: List[Dict[str, Any]] = []
        if partial_messages:
            try:
                core_partials = (
                    self.plugin.from_native_messages(partial_messages, ext_state)  # type: ignore[attr-defined]
                    if hasattr(self.plugin, "from_native_messages")  # type: ignore[attr-defined]
                    else []
                )
                for ext in self._extensions:
                    core_partials = ext.from_native_messages(partial_messages, core_partials)
            except Exception:
                core_partials = partial_messages
        # Track latest full history
        self._last_native_messages = full_history
                
        return final_messages, core_partials, full_history, self._get_state()

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
        
        print("(finalize) accumulated:", (self.state or {}).get("partial",{}))
        
        if not hasattr(self.plugin, "finalize"):
            return [], self._last_native_messages, self._get_state()
        # Use full history baseline
        baseline = self._last_native_messages or list(native_messages)
        final_messages, native_returned, new_state = self.plugin.finalize(
            baseline, working_state
        )

        # Merge and allow extensions to modify full history
        full_history = self._merge_history(baseline, native_returned)
        for ext in self._extensions:
            final_messages, full_history, new_state = ext.finalize(
                final_messages=final_messages,
                native_messages=full_history,
                state=new_state,
            )

        self.state = new_state
        # track latest full history
        self._last_native_messages = full_history

        if (len(final_messages) > 0):
            print("\n(finalize) final_messages:",final_messages)

        return final_messages, full_history, self._get_state()

    def get_extension_config_schemas(self) -> Dict[str, Any]:
        """Get config schemas for all extensions."""
        return {ext.name: ext.get_config_schema() for ext in self._extensions}

    def get_extension_ui_elements(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get UI schemas for all extensions."""
        return {ext.name: ext.get_ui_elements() for ext in self._extensions}

    def reset_state(self) -> None:
        """Discard internal shared state after request."""
        self.state = None
        self._last_native_messages = []

    @staticmethod
    def detect_capabilities(config: Dict[str, Any]) -> List[str]:
        """Static capability detection shim for protocol compliance; wrappers don't implement probing."""
        return []
