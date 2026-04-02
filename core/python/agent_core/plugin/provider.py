"""\
Provider plugin wrapper and streaming mixin.

Manages provider plugin state and provides typed interface for provider operations.
"""

from __future__ import annotations

from typing import Dict, Any, List, Iterator, AsyncIterator, Tuple, Optional

from .adapters import ProviderDefaultsAdapter
from .extension import ExtensionWrapper
from ..types import ProviderPlugin, Session
from ..utils import pipeline, get_logger

logger = None
log_chunk_processing = None

class ProviderWrapper(ProviderPlugin):
    """Wrapper for provider plugin managing state during streaming.

    Holds provider state and manages provider extensions in the same language (hot path).
    """

    def __init__(
        self,
        plugin_class: type,
        extension_classes: Optional[List[type]] = None,
    ) -> None:
        """Initialize wrapper with provider plugin class and optional extensions.

        Args:
            plugin_class: Provider plugin class (instance methods; stateless behavior)
            extension_classes: Optional list of provider extension classes
        """
        global logger, log_chunk_processing
        logger = get_logger("provider")
        log_chunk_processing = get_logger("chunk_processing")

        self.plugin_class = plugin_class
        self.plugin = ProviderDefaultsAdapter(plugin_class())
        self.state: Optional[Dict[str, Any]] = None
        self.name = getattr(plugin_class, "name", plugin_class.__name__)
        self.version = getattr(plugin_class, "version", "unknown")
        self._extensions: List[ExtensionWrapper] = []
        self._active_extensions: Optional[List[ExtensionWrapper]] = None
        self._last_native_messages: List[Dict[str, Any]] = []
        if extension_classes:
            for ext_cls in extension_classes:
                self._extensions.append(ExtensionWrapper(ext_cls))

    @property
    def extensions(self) -> List[ExtensionWrapper]:
        """Get extension wrappers.

        Returns:
            List of registered ExtensionWrapper instances.
        """
        return self._extensions

    def _iter_extensions(self) -> List[ExtensionWrapper]:
        """Return the list of extensions active for the current request.

        Extensions are sorted by `priority` (lower numbers run first).
        """

        exts = self._active_extensions if self._active_extensions is not None else self._extensions
        return sorted(exts, key=lambda ext: getattr(ext, "priority", 100))

    def set_active_extensions(self, extensions: List[ExtensionWrapper]) -> None:
        """Restrict active extensions for the current request."""
        self._active_extensions = list(extensions)

    def add_extensions(self, extension_classes: List[type]) -> None:
        """Add provider extensions (same language).

        Args:
            extension_classes: Extension classes to add to this provider.
        """
        for ext_cls in extension_classes:
            self._extensions.append(ExtensionWrapper(ext_cls))

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize provider and extensions using shared state owned by provider wrapper.

        Args:
            config: Provider configuration

        Returns:
            Shared provider state after extensions have updated it (if they do).
        """
        self.state = self.plugin.init(config)
        # Let extensions update shared state during init
        pipe = pipeline(config)
        self.state = pipe([ext.init for ext in self._iter_extensions()], self._get_state())
        return self._get_state()

    def _get_state(self) -> Dict[str, Any]:
        """Internal helper to get non-optional state with validation.

        Returns:
            Shared provider state.

        Raises:
            RuntimeError: If wrapper has not been initialized.
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        return self.state

    def get_config_schema(self) -> Dict[str, Any]:
        """Get provider configuration schema.

        Returns:
            JSON schema mapping for the provider, or empty dict.
        """
        return self.plugin.get_config_schema()

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Get provider UI elements."""
        return self.plugin.get_ui_elements(config, tags, models)

    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Delegate model discovery to the underlying provider via adapter."""
        return self.plugin.get_models(config)

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Delegate tag computation to the underlying provider via adapter."""
        return self.plugin.get_tags(config, models)

    def get_state(self) -> Dict[str, Any]:
        """Expose the current shared state for orchestration.

        Returns:
            Shared provider state.
        """
        return self._get_state()

    def set_state(self, state: Dict[str, Any]) -> None:
        """Replace the current shared state (used by features).

        Args:
            state: New shared provider state to set.

        Raises:
            RuntimeError: If wrapper has not been initialized.
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        self.state = state

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Run provider and extensions initialize_request with native messages for a new turn.

        Args:
            native_messages: Provider-native messages to initialize the new turn.
            state: Shared provider state (optional; wrapper state used if empty).

        Returns:
            Tuple of (full provider-native history for this turn, updated shared provider state).
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        # Start full native history at request boundary
        self._last_native_messages = list(native_messages)
        native_after_provider, new_state = self.plugin.initialize_request(
            native_messages, working_state
        )
        # Sort extensions by priority (lower numbers run first, default: 100)
        sorted_extensions = sorted(
            self._iter_extensions(),
            key=lambda ext: getattr(ext, 'priority', 100)
        )
        pipe = pipeline()
        native_after_exts, new_state = pipe(
            [ext.initialize_request for ext in sorted_extensions],
            native_after_provider,
            new_state,
        )
        self.state = new_state
        self._last_native_messages = list(native_after_exts)
        return native_after_exts, self._get_state()

    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert core messages to provider's native format (provider-first).

        Args:
            messages: Core message dicts.
            state: Shared provider state (optional; wrapper state used if empty).

        Returns:
            Provider-native message list.
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.to_native_messages(messages, working_state)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert provider-native messages back to core messages.

        Args:
            native_messages: Provider-native messages to convert.
            state: Shared provider state (optional; wrapper state used if empty).

        Returns:
            Core message dicts.
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.from_native_messages(native_messages, working_state)

    def to_display_format(self, message: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Format a message for display if supported; otherwise return as-is.

        Args:
            message: Core message to format.
            state: Shared provider state (optional; wrapper state used if empty).

        Returns:
            Display-friendly message dictionary or the input message unchanged.
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        return self.plugin.to_display_format(message, working_state)

    def apply_extension_transforms(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply extension transforms to provider-native messages.

        Args:
            messages: Core messages (context).
            native_messages: Provider-native messages to transform.

        Returns:
            Transformed provider-native messages after applying each extension.
        """
        state = self._get_state()
        result = native_messages
        for ext in self._iter_extensions():
            result = ext.to_native_messages(messages, result, state)
        return result

    def _merge_history(
        self, base: List[Dict[str, Any]], returned: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Merge plugin-returned native messages into base, ensuring full history.

        Args:
            base: Baseline full provider-native history.
            returned: Provider-returned native messages.

        Returns:
            Full merged history that includes all baseline messages and any new ones.
        """
        if not returned:
            return base
        if len(returned) >= len(base) and returned[: len(base)] == base:
            return returned
        return [*base, *returned]

    def call_api(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        """Make non-streaming API call and allow extensions to finalize outputs.

        Initializes the native history baseline, calls the provider, updates wrapper state,
        and returns full native history for subsequent steps.

        Args:
            native_messages: Provider-native inputs.
            state: Shared provider state (optional; wrapper state used if empty).

        Returns:
            Tuple of (partial_messages, final_messages, full_native_history, new_state).
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        # Initialize history baseline
        self._last_native_messages = list(native_messages)
        partials, final_messages, native_returned, new_state = self.plugin.call_api(
            self._last_native_messages, working_state
        )
        # Merge to full history and track
        full_history = self._merge_history(self._last_native_messages, native_returned)

        # Let extensions finalize non-streaming finals against the full history.
        pipe = pipeline()
        final_messages, full_history, new_state = pipe(
            [ext.finalize for ext in self._iter_extensions()],
            final_messages,
            full_history,
            new_state,
        )

        self.state = new_state
        self._last_native_messages = full_history
        return partials, final_messages, full_history, self._get_state()

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Make streaming API call (state-validated).

        Args:
            native_messages: Provider-native inputs.
            state: Shared provider state (optional; wrapper state used if empty).

        Yields:
            Provider-native streaming chunks.
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        yield from self.plugin.stream_api(native_messages, working_state)

    async def stream_api_async(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """Make async streaming API call, preferring native async if available.

        Args:
            native_messages: Provider-native inputs.
            state: Shared provider state (optional; wrapper state used if empty).

        Yields:
            Provider-native streaming chunks.
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        if hasattr(self.plugin, "stream_api_async"):
            async for chunk in self.plugin.stream_api_async(  # type: ignore[attr-defined]
                native_messages, working_state
            ):
                yield chunk
            return
        # Fallback to sync stream
        for chunk in self.plugin.stream_api(native_messages, working_state):
            yield chunk

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        """Process provider chunk and invoke extensions (hot path).

        Converts partial messages to core using provider + extensions when possible.

        Args:
            native_chunk: Provider-native streaming chunk.
            native_messages: Full provider-native history up to this chunk.
            state: Shared provider state (optional; wrapper state used if empty).

        Returns:
            Tuple of (partial_core_messages, final_messages, full_native_history, new_state).
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state
        # Use the provided full native history directly
        full_history = list(native_messages)

        log_chunk_processing.debug("processing chunk", chunk=native_chunk)

        partial_messages, final_messages, full_history, new_state = self.plugin.process_chunk(
            native_chunk, full_history, working_state
        )

        # Let extensions transform partials/finals/native history in order
        ext_state = new_state
        pipe = pipeline(native_chunk)
        partial_messages, final_messages, full_history, ext_state = pipe(
            [ext.process_chunk for ext in self._iter_extensions()],
            partial_messages,
            final_messages,
            full_history,
            ext_state,
        )
        self.state = ext_state

        log_chunk_processing.debug("processed chunk", partials=partial_messages)

        # Convert partial messages (provider-native) to core using the same
        # from_native pipeline as final messages (provider first, then active
        # extensions). Features are cold-path only and are not applied here.
        core_partials: List[Dict[str, Any]] = []
        if partial_messages:
            try:
                pipe = pipeline(partial_messages)
                core_partials = pipe(
                    [self.plugin.from_native_messages]
                    + [ext.from_native_messages for ext in self._iter_extensions()],
                    ext_state,
                )
            except Exception as e:
                logger.warning("failed to convert partials to core, using as-is", error=str(e))
                core_partials = partial_messages
        # Track latest full history
        self._last_native_messages = full_history

        log_chunk_processing.debug("converted partials to core", core_partials=core_partials)

        return core_partials, final_messages, full_history, self._get_state()

    def finalize(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Finalize provider turn and let extensions enhance outputs.

        Args:
            native_messages: Full provider-native history for this turn (baseline if no streaming).
            state: Shared provider state (optional; wrapper state used if empty).

        Returns:
            Tuple of (final_provider_native_messages, full_native_history, new_state).
        """
        if self.state is None:
            raise RuntimeError(f"Provider {self.name} not initialized")
        working_state = state or self.state

        # Use full history baseline
        baseline = self._last_native_messages or list(native_messages)
        final_messages, native_returned, new_state = self.plugin.finalize(baseline, working_state)

        # Merge and allow extensions to modify full history
        full_history = self._merge_history(baseline, native_returned)
        pipe = pipeline()
        final_messages, full_history, new_state = pipe(
            [ext.finalize for ext in self._iter_extensions()],
            final_messages,
            full_history,
            new_state,
        )

        self.state = new_state
        # track latest full history
        self._last_native_messages = full_history

        return final_messages, full_history, self._get_state()

    def get_extension_config_schemas(self) -> Dict[str, Any]:
        """Get config schemas for all extensions.

        Returns:
            Mapping from extension name to its JSON schema.
        """
        return {ext.name: ext.get_config_schema() for ext in self._extensions}

    def get_extension_ui_elements(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get UI schemas for registered extensions.

        Uses the same priority-sorted extension order as the request pipeline.
        """

        return {ext.name: ext.get_ui_elements(config, tags, models) for ext in self._iter_extensions()}

    def get_extension_actions(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Return session-scoped action definitions for active extensions."""

        return {ext.name: ext.get_actions(state) for ext in self._iter_extensions()}

    def execute_extension_action(
        self,
        plugin_id: str,
        action_id: str,
        session: Session,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Dispatch a session-scoped action to the matching active extension."""

        for ext in self._iter_extensions():
            if ext.name != plugin_id:
                continue
            return ext.execute_action(action_id, session, native_messages, params, context, state)
        raise KeyError(f"Unknown provider extension {plugin_id!r}")

    def reset_state(self) -> None:
        """Discard internal shared state after request."""
        self.state = None
        self._last_native_messages = []
        self._active_extensions = None

    # Optimized streaming helpers for provider wrappers.

    _last_native_messages: List[Dict[str, Any]]

    def stream_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Stream provider results while processing chunks internally.

        Events yielded:
            - {"type": "partial", "message": <partial_message_like_core>}
            - {"type": "final_messages", "messages": <list_of_provider_native_finals>}

        Args:
            native_messages: Provider-native input messages for this request.
            state: Current shared provider state (or wrapper state if empty).

        Yields:
            Dict events representing partials and batches of final provider-native messages.

        Raises:
            RuntimeError: If the wrapper is not initialized (missing state).
        """
        # Resolve initial state via wrapper; error if uninitialized
        try:
            working_state = state or self._get_state()  # type: ignore[attr-defined]
        except Exception:
            raise RuntimeError(f"Provider {self.name} not initialized")  # type: ignore[attr-defined]

        # Initialize full native history for this turn
        self._last_native_messages = list(native_messages)  # type: ignore[attr-defined]
        current_native = self._last_native_messages
        chunk_count = 0
        for native_chunk in self.plugin.stream_api(current_native, working_state):  # type: ignore[attr-defined]
            chunk_count += 1
            partials, finals, current_native, working_state = self.process_chunk(  # type: ignore[misc]
                native_chunk, current_native, working_state
            )
            # track latest native messages (full history)
            self._last_native_messages = current_native  # type: ignore[attr-defined]
            # yield partials first
            for p in partials:
                yield {"type": "partial", "message": p}
            if finals:
                yield {"type": "final_messages", "messages": finals}

        logger.debug("stream_messages complete")

    async def stream_messages_async(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """Async variant of stream_messages.

        Prefers the provider's native async streaming when available, falling back
        to sync streaming otherwise.

        Args:
            native_messages: Provider-native input messages for this request.
            state: Current shared provider state (or wrapper state if empty).

        Yields:
            Dict events representing partials and batches of final provider-native messages.

        Raises:
            RuntimeError: If the wrapper is not initialized (missing state).
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
                partials, finals, current_native, working_state = self.process_chunk(  # type: ignore[misc]
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
            partials, finals, current_native, working_state = self.process_chunk(  # type: ignore[misc]
                native_chunk, current_native, working_state
            )
            self._last_native_messages = current_native  # type: ignore[attr-defined]
            for p in partials:
                yield {"type": "partial", "message": p}
            if finals:
                yield {"type": "final_messages", "messages": finals}

    def get_last_native_messages(self) -> List[Dict[str, Any]]:
        """Return the latest accumulated provider-native messages tracked during streaming.

        Returns:
            Full provider-native history after the most recent chunk or finalize step.
        """
        # type: ignore[attr-defined]
        return getattr(self, "_last_native_messages", [])
