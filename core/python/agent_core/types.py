"""
Core data types for the AI Agent Platform.

This module defines immutable data structures following functional programming principles.
All transformations return new instances rather than modifying existing ones.

Examples:
    Creating immutable messages and sessions:

    ```python
    from agent_core.types import Message, Session

    msg = Message(role="user", content="Hello")
    session = Session(session_id="s1", messages=[msg])
    data = session.to_dict()
    restored = Session.from_dict(data)
    ```
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Literal,
    Tuple,
    Protocol,
    Iterator,
    AsyncIterator,
    TYPE_CHECKING,
    runtime_checkable,
)
from dataclasses import dataclass, field
from copy import deepcopy

MessageRole = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class ToolDescriptor:
    """Normalized metadata for a tool schema exposed to UI and requests."""

    plugin_name: str
    tool_name: str
    schema: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


if TYPE_CHECKING:
    from .tool_interop import ToolInteropContribution

# Plugin Protocol Types


class ProviderRequestCancelled(RuntimeError):
    """Raised when a provider request is cancelled by request id."""

    def __init__(self, request_id: str | None = None):
        super().__init__("Provider request cancelled")
        self.request_id = request_id


@runtime_checkable
class BasePlugin(Protocol):
    """Common instance-level protocol for non-tool plugins.

    Applies to Provider, ProviderExtension, and Feature plugins.
    Unifies identity, configuration UI, and lifecycle method signatures
    that are identical across these plugin types. Methods should remain
    stateless and operate on explicit state parameters; plugin instances
    are short‑lived per request.
    """

    # Identity (attributes on the class)
    name: str
    version: str

    # Config/UI
    def get_config_schema(self) -> Dict[str, Any]:
        """Return JSON schema describing this plugin's configuration.

        Returns:
            JSON schema dictionary.
        """
        return {}

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Return UI element definitions contributed by this plugin.

        The returned list describes configuration and display-oriented
        elements that applications can use to build UIs. Each element is a
        plain dictionary; the core treats these dictionaries as opaque and
        flattens them via :meth:`AgentCore.get_ui_schema`.

        Args:
            config: Effective configuration for the current agent/request.
            context: Optional derived context for schema generation. The core
                provides keys such as `tags`, `models`, `available_tools`,
                and `tools` here.

        Note:
            The canonical hook shape is `(config, context=None)`. For backward
            compatibility, adapters also accept legacy plugin
            implementations that define `get_ui_elements(self)`,
            `get_ui_elements(self, config)`, `get_ui_elements(self, config, tags, models)`,
            or `get_ui_elements(self, config, tags, models, context)`.

        Recommended element shapes:

        * **Configuration elements** (default ``ui_type == "config"``):

          Used to describe editable settings for the plugin. Typical keys are::

              {
                  "type": "checkbox" | "text" | "number" | "select" | "dropdown" | ...,
                  "key": "config_key",          # stable configuration key
                  "label": "Human label",       # short caption for UIs
                  "description": "Longer help text",  # optional
                  "options": [                    # for select-like fields
                      "value" | {"value": "v", "label": "Display"},
                  ],
                  "placeholder": "Search or enter a value",
                  "custom_value": {               # optional dropdown escape hatch
                      "enabled": True,
                      "pattern": r"^[^\\s]+$",
                      "option_label": "Use '{value}'",
                  },
                  "rich_ui": {                   # optional self-contained compact UI
                      "kind": "dropdown",
                      "label": "Short label",
                      "show_label": False,
                      "options": [],
                      "placements": ["composer"],
                  },
                  ...  # plugin-specific extras are allowed
              }

          When ``"ui_type"`` is missing or falsy, the core normalizes the
          element to ``"config"`` and will de-duplicate on ``"key"`` when
          flattening the global UI schema.

        * **Message footer elements** (``ui_type == "message_footer"``):

          Used by some applications (for example, the terminal client) to
          render a compact footer line under individual messages. A common
          shape is::

              {
                  "ui_type": "message_footer",
                  "data": "metadata.timestamp",   # dotted JSON path
                  "template": "{{data}}",         # optional; defaults vary
                  ...
              }

          ``"data"`` is interpreted as a dotted path into the core message
          dictionary (e.g. ``"metadata.timestamp"``). ``"template"`` is a
          simple string where ``"{{data}}"`` is replaced with the resolved
          value, but individual applications are free to use different
          conventions.

        * **Status bar elements** (``ui_type == "status_bar"``):

          Similar to ``"message_footer"`` but intended for persistent status
          bars (for example, values derived from the last assistant message)::

              {
                  "ui_type": "status_bar",
                  "data": "metadata.total_cost",
                  "template": "Total: {{data}}",
                  ...
              }

        The core will attach a ``"plugin"`` field (when absent) naming the
        contributing plugin class when it flattens UI elements. Plugins may
        include additional keys beyond those shown above; callers should treat
        the returned element dictionaries as immutable.

        Args:
            config: Effective configuration for the current agent/request.
            context: Optional derived context for schema generation.

        Returns:
            List of UI element dictionaries.
        """
        return []

    # Common lifecycle across provider/extension/feature
    # No dedicated update_state lifecycle step is required; plugins are free
    # to define and use whatever state shape they need. Configuration and
    # UI-driven values should be provided via the config dict passed into
    # init/initialize_request rather than a separate UI state merge step.


class ProviderPlugin(BasePlugin, Protocol):
    """Protocol for provider plugins (hot + cold paths, shared provider state).

    Providers handle API I/O with LLMs and convert between core messages and
    provider-native messages. They run chunk processing on the hot path and
    participate in per-turn finalization on the cold path.

    Example:
        Minimal echo-like provider:

        ```python
        from typing import Any, Dict, List, Tuple, Iterator
        class EchoProvider:
            name = "echo"
            version = "1.0.0"
            def get_config_schema(self) -> Dict[str, Any]:
                return {"model": {"type": "string", "default": "echo-1"}}
                    def get_ui_elements(self, config: Dict[str, Any], tags: List[str], models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:  # optional
                return []
            def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
                # Provider state is an opaque dict; this minimal example
                # only stores configuration.
                return {"config": config}
            def initialize_request(
                self,
                native_messages: List[Dict[str, Any]],
                state: Dict[str, Any],
            ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
                return native_messages, state
            def to_native_messages(self, messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
                return list(messages)
            def from_native_messages(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
                return list(native_messages)
            def call_api(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
                content = f"Echo: {next((m['content'] for m in reversed(native_messages) if m.get('role')=='user'), '')}"
                msg = {"role": "assistant", "content": content}
                # Return (partial_messages, final_messages, native_messages, new_state)
                return ([], [msg], [*native_messages, msg], state)
            def stream_api(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
                yield from []
        ```
    """

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize provider state from application config.

        Note:
            In the default ``AgentCore`` request flow, this hook is called once
            per request. Provider extensions run their ``init`` hooks after the
            provider initializes, and features run their ``init`` hooks after
            the provider+extensions init chain completes.

        Args:
            config: Application-supplied configuration for the provider.

        Returns:
            Initial shared provider state owned by the provider wrapper.
        """
        return {"config": config}

    # Message conversion
    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Convert core messages to this provider's native wire format.

        Note:
            When the core converts a single new message (e.g., via add_message), it passes a list
            containing only that single message in "messages". Implementations must handle both
            full-history lists and single-message lists.

            In the default ``AgentCore`` request flow, this conversion runs
            first. Active provider extensions and features may then apply
            stateless transforms via their own ``to_native_messages`` hooks.

        Args:
            messages: Core session messages (may be a single-element list for add_message).
            state: Current shared provider state.
            context: Optional request/runtime context for this conversion.

        Returns:
            Provider-native messages suitable for API calls.
        """
        return [
            {"role": m.get("role", "user"), "content": m.get("content", "")}
            for m in messages
            if isinstance(m, dict)
        ]

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Convert provider-native messages into core message dictionaries.

        Note:
            In the default ``AgentCore`` request flow, this conversion runs
            first. Active provider extensions and features may then apply
            stateless transforms via their own ``from_native_messages`` hooks.

        This base implementation intentionally ignores provider-specific
        reasoning fields. Providers and extensions that work with
        reasoning/thinking should surface that information via metadata
        (e.g., in a provider extension), not as a top-level field on the
        core message.

        Args:
            native_messages: Provider-native messages to convert.
            state: Current shared provider state.
            context: Optional request/runtime context for this conversion.

        Returns:
            Core messages derived from native messages.
        """
        finals: List[Dict[str, Any]] = []
        for m in native_messages:
            if not isinstance(m, dict):
                continue
            if not ("role" in m or "content" in m):
                continue
            msg: Dict[str, Any] = {
                "role": m.get("role", "assistant"),
                "content": m.get("content", ""),
            }
            finals.append({**msg, "metadata": {}})
        return finals

    # New request lifecycle
    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Prepare for a new request with provider-native messages.

        Note:
            In the default ``AgentCore`` request flow, this hook runs first in
            the ``initialize_request`` chain. Active provider extensions run
            their ``initialize_request`` hooks next (in order), and feature
            ``initialize_request`` hooks run after the provider (and
            extensions) complete.

        Args:
            native_messages: Provider-native messages for this request.
            state: Current shared provider state.
            context: Optional request context. The core provides keys such as
                `core`, `config`, `request_id`, `tags`, `models`,
                `available_tools`, `tools`, and `tool_interop` here.

        Returns:
            Tuple of (provider-native messages for this request, updated shared state).
            Implementations MAY return the same native_messages when only state changes.
        """
        return native_messages, state

    def get_tool_interop_contribution(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any] | None = None,
    ) -> "ToolInteropContribution":
        """Return provider-contributed tool interop accessors/adapters."""
        from .tool_interop import ToolInteropContribution

        return ToolInteropContribution()

    def accepted_tool_schema_formats(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any] | None = None,
    ) -> List[str]:
        """Return schema formats this provider can send without further adaptation."""
        return []

    def emitted_tool_call_formats(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any] | None = None,
    ) -> List[str]:
        """Return tool-call formats this provider may emit in responses."""
        return []

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        """Process a streaming chunk from the provider on the hot path.

        Note:
            In the default ``AgentCore`` request flow, the provider processes
            each chunk first; provider extensions are then invoked (in order)
            to observe and adjust partials/finals/native history.

        Args:
            native_chunk: Provider-native streaming chunk.
            native_messages: Provider-native input messages (context).
            state: Current shared provider state.

        Returns:
            Tuple of (partial_messages, final_messages, native_messages, new_state).
            native_messages MUST be the full provider-native history (not a delta).
        """
        return [], [], native_messages, state

    # Returns: (partial_messages, final_messages, native_messages, new_state)

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Perform final processing after streaming completes.

        The provider runs first in the finalize chain. Both final_messages and
        native_messages are provider-native. final_messages contains only the
        new messages for this turn; native_messages MUST be full history.

        Active provider extensions run their ``finalize`` hooks next (in order),
        followed by feature ``finalize`` hooks.

        Args:
            native_messages: Full provider-native message history (all prior turns plus any for this turn).
            state: Current shared provider state.
            context: Optional request context for this turn.

        Returns:
            Tuple of (final_messages, native_messages, new_state).
        """
        return [], native_messages, state

    # Returns: (final_messages, native_messages, new_state)

    def to_display_format(
        self, message: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert a message to a display-friendly format for UIs.

        Args:
            message: Core message dictionary to format.
            state: Current shared provider state.

        Returns:
            Display-friendly message dictionary.
        """
        return message

    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return model descriptors available for this provider and config.

        Optional; providers may return an empty list when model enumeration
        is not supported.
        """
        return []

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return capability/environment tags for this provider.

        Note:
            In the default ``AgentCore`` dependency-resolution flow, these tags
            are aggregated with tags from provider extensions, features, and
            tools to decide which plugins are enabled for a request.

        Implementations must be pure and deterministic for a given
        (config, models) pair.
        """
        return []

    # I/O entry points now take native messages
    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        """Make a non-streaming API call with provider-native messages.

        Args:
            native_messages: Provider-native input messages.
            state: Current shared provider state.

        Returns:
            Tuple of (partial_messages, final_messages, native_messages, new_state).
        """
        return [], [], native_messages, state

    # Returns: (partial_messages, final_messages, native_messages, new_state)

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Iterator[Dict[str, Any]]:
        """Make a streaming API call; yields provider-native chunks.

        Args:
            native_messages: Provider-native input messages.
            state: Current shared provider state.

        Yields:
            Provider-native streaming chunks.
        """
        return iter([])

    def cancel_request(self, request_id: str) -> bool:
        """Best-effort cancellation for an in-flight request.

        Providers that track active runtime requests by ``request_id`` should
        attempt to cancel the matching request and return ``True`` when a
        matching in-flight request was found. Returning ``False`` indicates the
        provider did not recognize the request id or had nothing active to
        cancel.
        """
        return False


class ProviderExtensionPlugin(BasePlugin, Protocol):
    """Protocol for provider extension plugins (shared provider state, hot + cold path observers).

    Provider extensions run in the provider's language and observe/transform streaming
    chunks on the hot path and participate in finalize on the cold path. They do not own
    separate state; they receive and update the shared provider state.

    Attributes:
        priority: Optional execution priority (default: 100). Lower numbers run first.
                  Extensions are sorted by priority within the extension execution chain.

    Example:
        Basic prefix extension:

        ```python
        from typing import Any, Dict, List, Tuple, Optional
        class PrefixExt:
            name = "prefix"
            version = "1.0.0"
            priority = 50  # Optional: run before extensions with default priority (100)
            def get_config_schema(self):
                return {"prefix": {"type": "string", "default": "[EXT]"}}
            def init(self, config, state):
                return state
            def process_chunk(self, native_chunk, partial_messages, final_messages, native_messages, state):
                pfx = state.get("config", {}).get("prefix", "[EXT]")
                finals = [{**m, "content": f"{pfx} {m['content']}"} for m in final_messages]
                return partial_messages, finals, native_messages, state
            def finalize(self, final_messages, native_messages, state):
                return final_messages, native_messages, state
        ```
    """

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize with application config and shared provider state.

        Note:
            In the default ``AgentCore`` request flow, provider extensions are
            initialized after the provider's ``init`` hook.

        Args:
            config: Application-supplied configuration.
            state: Current shared provider state.

        Returns:
            Updated shared provider state (or the same state).
        """
        return state

    def get_models(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Statelessly transform or provide model descriptors.

        Implementations must not mutate the incoming models list; they
        should instead return a new list.

        Note:
            In the default ``AgentCore`` request flow, model discovery starts
            with the provider's ``get_models`` hook and then passes through each
            extension's ``get_models`` hook.
        """
        return list(models)

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return capability/environment tags contributed by this extension.

        Note:
            In the default ``AgentCore`` dependency-resolution flow, these tags
            are aggregated with tags from the provider, other extensions,
            features, and tools to decide which plugins are enabled.
        """
        return []

    def required_tags(self) -> List[str]:
        """Tags that must be present for this extension to be enabled."""
        return []

    def forbidden_tags(self) -> List[str]:
        """Tags that must NOT be present for this extension to be enabled.

        If any of these tags are in the available tag set, the extension is disabled.
        This provides a negative constraint complementary to required_tags.
        """
        return []

    def is_enabled(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Optional[bool]:
        """Return whether this extension should be enabled given the current context.

        This method allows extensions to implement complex enablement logic that
        goes beyond simple tag matching. It receives the full runtime context
        including configuration, computed tags, model descriptors, and information
        about other enabled plugins.

        Args:
            config: Effective configuration for the current request.
            tags: Capability tags computed for this config.
            models: Model descriptors computed for this config.
            context: Additional context including:
                - "enabled_plugin_ids": dict mapping plugin kind to list of enabled plugin ids
                - "disabled_plugins": config-level disabled plugin id list
                - "force_enabled_plugins": config-level force-enabled plugin id list

        Returns:
            True: extension is enabled (bypass required_tags/forbidden_tags check)
            False: extension is disabled
            None: fall back to required_tags/forbidden_tags check (default)
        """
        return None

    # Stateless transforms
    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any] | None = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Transform provider-native messages using visibility of core messages.

        Note:
            When the core converts a single new message (e.g., via add_message), it passes a list containing only
            that single message in "messages". Implementations must handle both full-history lists and single-message lists.

            In the default ``AgentCore`` request flow, extension transforms run
            after the provider's ``to_native_messages`` conversion and before
            feature transforms.

        Args:
            messages: Core session messages for context (may be a single-element list for add_message).
            native_messages: Current provider-native messages.
            state: Optional shared provider state (available when called via ProviderWrapper).
            context: Optional request/runtime context for this conversion.

        Returns:
            Updated provider-native messages.
        """
        return list(native_messages)

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any] | None = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Transform provider-native messages back into core messages.

        Note:
            In the default ``AgentCore`` request flow, extension transforms run
            after the provider's ``from_native_messages`` conversion and before
            feature transforms.

        Args:
            native_messages: Provider-native messages to transform.
            messages: Core session messages for context.
            state: Optional shared provider state (available when called via ProviderWrapper).
            context: Optional request/runtime context for this conversion.

        Returns:
            Updated core messages.
        """
        return list(messages)

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Prepare for a new request with provider-native messages.

        Note:
            In the default ``AgentCore`` request flow, this hook runs after the
            provider's ``initialize_request`` hook and before any feature
            ``initialize_request`` hooks.

        Args:
            native_messages: Provider-native messages for this request.
            state: Current shared provider state.
            context: Optional request context. The core provides keys such as
                `core`, `config`, `request_id`, `tags`, `models`,
                `available_tools`, `tools`, and `tool_interop` here.

        Returns:
            Tuple of (provider-native messages for this request, updated shared state).
            Implementations MAY return the same native_messages when only state changes.
        """
        return native_messages, state

    def get_tool_interop_contribution(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any] | None = None,
    ) -> "ToolInteropContribution":
        """Return extension-contributed tool interop accessors/adapters."""
        from .tool_interop import ToolInteropContribution

        return ToolInteropContribution()

    def accepted_tool_schema_formats(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any] | None = None,
    ) -> List[str]:
        """Return additional tool schema formats this extension can inject."""
        return []

    def emitted_tool_call_formats(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any] | None = None,
    ) -> List[str]:
        """Return additional tool-call formats this extension can surface."""
        return []

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        """Observe/modify provider outputs for a streaming chunk.

        Called on the hot path for each provider-native chunk. May be called with
        native_chunk=None during provider finalize.

        Note:
            In the default ``AgentCore`` request flow, extensions run after the
            provider's ``process_chunk`` hook. Multiple extensions are invoked
            in order; features are not invoked on the hot path.

        Args:
            native_chunk: Provider-native streaming chunk, or None during finalize.
            partial_messages: Current list of partial provider-native messages.
            final_messages: Current list of final provider-native messages.
            native_messages: Current full provider-native message history.
            state: Current shared provider state.

        Returns:
            Tuple of (updated_partial_messages, updated_final_messages, updated_native_messages, new_state).
            updated_native_messages MUST be full history (not a delta).
        """
        return partial_messages, final_messages, native_messages, state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Final cold-path processing after provider streaming/finalize.

        Args:
            final_messages: Provider-native final messages emitted this turn (deltas).
            native_messages: Full provider-native message history for this turn.
            state: Current shared provider state.
            context: Optional request context for this turn.

        Returns:
            Tuple of (final_messages, native_messages, new_state), all provider-native.
        """
        return final_messages, native_messages, state

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return session-scoped action definitions for this extension.

        These actions are analogous to application-plugin actions, but they
        operate only on a single session's provider-native history. The core
        owns session loading/saving and passes the selected session, current
        provider-native history, validated action params, and shared provider
        state into :meth:`execute_action`.

        Action definitions are plain dictionaries. A common shape is::

            {
                "id": "compact_native_history",
                "label": "Compact native history",
                "description": "Provider-native session action.",
                "inputs": {
                    "instructions": {"type": "string", "required": False},
                },
            }

        Transport-specific inputs such as ``session_id`` are handled by higher
        layers and should not be declared here unless the extension itself
        needs them.
        """
        return []

    def execute_action(
        self,
        action_id: str,
        session: "Session",
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a session-scoped provider-native action.

        The returned mapping is generic. Extensions should always return a
        full ``native_messages`` list representing the new provider-native
        history for the session. Optional control keys currently understood by
        the core include:

        - ``session_metadata``: mapping merged into ``session.metadata``

        For the core-owned ``response_finalize`` lifecycle, actions may also
        return ``final_messages`` to replace the current turn's in-flight final
        core messages before they are emitted or appended to the session.

        Additional keys are preserved and surfaced back to higher layers as an
        opaque result payload.

        The ``context`` parameter provides layered access to runtime capabilities
        (see FeaturePlugin.execute_action for details on context structure).
        """
        return {"native_messages": list(native_messages)}


class FeaturePlugin(BasePlugin, Protocol):
    """Protocol for feature plugins (cold path; shared provider state).

    Features operate on the cold path only (no per-chunk processing). They can
    transform both provider-native messages and core messages during finalize and
    may update the shared provider state during init and initialize_request.

    Attributes:
        priority: Optional execution priority (default: 100). Lower numbers run first.
                  Features are sorted by priority within the feature execution chain.

    Example:
        Minimal feature that annotates finals:

        ```python
        class TagFeature:
            name = "tag"
            version = "1.0.0"
            priority = 100  # Optional: default priority
            def get_config_schema(self):
                return {"enabled": {"type": "boolean", "default": True}}
            def init(self, config, state):
                return state
            def to_native_messages(self, messages, native_messages):
                return native_messages
            def from_native_messages(self, native_messages, messages):
                return messages
            def initialize_request(self, native_messages, state):
                return native_messages, state
            def finalize(self, final_messages, native_messages, state):
                finals = [{**m, "metadata": {**m.get("metadata", {}), "tag": True}} for m in final_messages]
                return finals, native_messages, state
        ```
    """

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize with application config and shared provider state.

        Note:
            In the default ``AgentCore`` request flow, feature init hooks run
            after the provider (and any active provider extensions) have
            initialized.

        Args:
            config: Application-supplied configuration.
            state: Current shared provider state.

        Returns:
            Updated shared provider state (or the same state).
        """
        return state

    def get_models(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Statelessly transform or provide model descriptors.

        Note:
            In the default ``AgentCore`` request flow, model discovery starts
            with the provider's ``get_models`` hook, then passes through provider
            extensions, and finally through feature ``get_models`` hooks.
        """
        return list(models)

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return capability/environment tags contributed by this feature.

        Note:
            In the default ``AgentCore`` dependency-resolution flow, these tags
            are aggregated with tags from the provider, provider extensions, and
            tools to decide which plugins are enabled.
        """
        return []

    def required_tags(self) -> List[str]:
        """Tags that must be present for this feature to be enabled."""
        return []

    def forbidden_tags(self) -> List[str]:
        """Tags that must NOT be present for this feature to be enabled.

        If any of these tags are in the available tag set, the feature is disabled.
        This provides a negative constraint complementary to required_tags.
        """
        return []

    def is_enabled(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Optional[bool]:
        """Return whether this feature should be enabled given the current context.

        This method allows features to implement complex enablement logic that
        goes beyond simple tag matching. It receives the full runtime context
        including configuration, computed tags, model descriptors, and information
        about other enabled plugins.

        Args:
            config: Effective configuration for the current request.
            tags: Capability tags computed for this config.
            models: Model descriptors computed for this config.
            context: Additional context including:
                - "enabled_plugin_ids": dict mapping plugin kind to list of enabled plugin ids
                - "disabled_plugins": config-level disabled plugin id list
                - "force_enabled_plugins": config-level force-enabled plugin id list

        Returns:
            True: feature is enabled (bypass required_tags/forbidden_tags check)
            False: feature is disabled
            None: fall back to required_tags/forbidden_tags check (default)
        """
        return None

    # Stateless transforms
    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any] | None = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Transform provider-native messages using visibility of core messages.

        Note:
            When the core converts a single new message (e.g., via add_message), it passes a list containing only
            that single message in "messages". Implementations must handle both full-history lists and single-message lists.

            In the default ``AgentCore`` request flow, feature transforms run
            after the provider and provider extension ``to_native_messages``
            transforms.

        Args:
            messages: Core session messages for context (may be a single-element list for add_message).
            native_messages: Current provider-native messages.
            state: Optional shared provider state (available when called via ProviderWrapper).

        Returns:
            Updated provider-native messages.
        """
        return list(native_messages)

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any] | None = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Transform provider-native messages back into core messages.

        Note:
            In the default ``AgentCore`` request flow, feature transforms run
            after the provider and provider extension ``from_native_messages``
            transforms.

        Args:
            native_messages: Provider-native messages to transform.
            messages: Core session messages for context.
            state: Optional shared provider state (available when called via ProviderWrapper).

        Returns:
            Updated core messages.
        """
        return list(messages)

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Prepare for a new request with provider-native messages.

        Note:
            In the default ``AgentCore`` request flow, feature hooks run after
            the provider (and any provider extensions) have run their
            ``initialize_request`` hooks.

        Args:
            native_messages: Provider-native messages for this request.
            state: Current shared provider state.
            context: Optional request context. The core provides keys such as
                `core`, `config`, `request_id`, `tags`, `models`,
                `available_tools`, `tools`, and `tool_interop` here.

        Returns:
            Tuple of (provider-native messages for this request, updated shared state).
            Implementations MAY return the same native_messages when only state changes.
        """
        return native_messages, state

    def prepare_tools(
        self,
        config: Dict[str, Any],
        tools: List["ToolDescriptor"],
        context: Optional[Dict[str, Any]] = None,
    ) -> List["ToolDescriptor"]:
        """Filter or transform the available tool catalog for a request.

        This hook runs before provider/extensions/features ``init`` hooks for
        the request so that the effective tool list can be threaded through the
        compatibility shim at `config["tools"]`.

        Args:
            config: Effective configuration for this request, including any
                UI-driven tool gating selections.
            tools: Normalized tool catalog for this request before policy
                filtering.
            context: Request-preparation context. The core provides keys such
                as `provider`, `tags`, `models`, `available_tools`, and
                `tools` here.

        Returns:
            The effective tool descriptor list for this request.
        """
        return list(tools)

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Final cold-path processing after provider and extensions complete.

        Args:
            final_messages: Provider-native final messages emitted this turn (deltas).
            native_messages: Full provider-native message history for this turn.
            state: Current shared provider state.
            context: Optional request context for this turn.

        Returns:
            Tuple of (final_messages, native_messages, new_state), all provider-native.
        """
        return final_messages, native_messages, state

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return session-scoped action definitions for this feature.

        Feature actions follow the same session-scoped shape as provider
        extension actions. They are optional and are primarily used for
        lifecycle-triggered single-session mutations.
        """
        return []

    def execute_action(
        self,
        action_id: str,
        session: "Session",
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a session-scoped feature action.

        The supported return contract matches provider-extension actions:
        features may return replacement ``native_messages`` and/or a
        ``session_metadata`` mapping that is merged into the session.

        For the core-owned ``response_finalize`` lifecycle, features may also
        return ``final_messages`` to replace the current turn's final core
        messages before they are emitted or appended to the session.

        The ``context`` parameter provides layered access to runtime capabilities:

        **Layer 1 (Core - always present):**
            - ``core``: AgentCore instance for session/message operations
            - ``config``: Current resolved request configuration
            - ``trigger_source``: Where the action was triggered ("core", "application")
            - ``session``: Serialized session dict (session.to_dict())
            - ``lifecycle``: Lifecycle trigger name (for lifecycle-triggered actions)
            - ``final_messages``: Current turn final core messages for
              ``response_finalize``
            - ``native_final_messages``: Provider-native finals for the current
              turn for ``response_finalize``
            - ``native_messages``: Full provider-native history for
              ``response_finalize``
            - ``stream``: Whether the request is streaming for
              ``response_finalize``
            - ``turn_native_start_index``: Native-history starting offset for
              the current turn for ``response_finalize``

        **Layer 2 (Application - when called from AgentApplication):**
            - ``app`` and ``application``: AgentApplication instance
            - ``base_config``: Full base configuration (all agents)
            - ``session_asset_store``: Session asset store for file attachments
            - ``runtime_state_root``: Persistent runtime-state root directory

        **Layer 3 (Terminal/Server - implementation-specific):**
            - Implementation-specific keys added by terminal or HTTP server

        Caller-supplied context is additive only. Reserved keys owned by the
        context builders are not overridden; on clashes the builder keeps the
        owned value and emits a warning.

        Features can check for enhanced capabilities using ``context.get("app")``.
        """
        return {"native_messages": list(native_messages)}

    # Completion / templates
    def get_template(self, config: Dict[str, Any]) -> str:
        """Return a template string used by this feature.

        This hook is intended for applications that need a feature-specific
        textual template (for example, to construct editor snippets or
        autocomplete expansions). Implementations may return an empty string
        when no template is applicable.

        Args:
            config: Application-supplied configuration for the current agent
                or request.

        Returns:
            Template string, or an empty string if the feature does not
            expose a template.
        """

        return ""

    def get_completions(
        self,
        config: Dict[str, Any],
        text: str,
    ) -> List[Dict[str, Any]]:
        """Return completion suggestions for the given input text.

        Each completion entry is a dictionary whose structure is
        application-defined. A common shape is::

            {
                "replacement": "text to insert",
                "start": 5,  # 0-based index in input text
                "display": "label shown in UI",
                "display_meta": "extra description",
            }

        Implementations may ignore ``text`` when not relevant and should
        return an empty list when no completions apply.

        Args:
            config: Application-supplied configuration for the current agent
                or request.
            text: Full text before the cursor (for example, the contents of
                an input line in a terminal UI).

        Returns:
            List of completion descriptor dictionaries.
        """

        return []

    def apply_completion(
        self,
        config: Dict[str, Any],
        text: str,
        completion: Dict[str, Any],
    ) -> str:
        """Optionally transform an accepted completion into a final snippet.

        Applications may call this hook when a user accepts one of the
        completion entries previously returned by :meth:`get_completions`.
        The default implementation returns an empty string, indicating that
        the feature does not wish to modify the completion.

        Args:
            config: Application-supplied configuration for the current agent
                or request.
            text: Full buffer text after the completion has been applied
                (for example, input containing ``"@file:path"``).
            completion: The completion descriptor dict that was accepted,
                as previously returned by :meth:`get_completions`.

        Returns:
            A replacement string to insert into the buffer in place of the
            completion text, or an empty string/falsey value to indicate no
            special handling.
        """

        return ""


class ToolPlugin(BasePlugin, Protocol):
    """Protocol for tool plugins (own tool state; unchanged by shared state design).

    Tools provide function schemas and handle execution with their own state, independent
    from the provider shared state.

    Example:
        Minimal calculator tool:

        ```python
        class DummyCalc:
            name = "calculator"
            version = "1.0.0"
            def get_tool_schemas(self, state):
                return [{"type": "function", "function": {"name": "add", "parameters": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}, "required": ["a","b"]}}}]
            def init(self, config):
                return {"config": config}
            def execute_tool(self, tool_name, arguments, state):
                if tool_name == "add":
                    return {"success": True, "result": arguments.get("a", 0) + arguments.get("b", 0)}
                return {"success": False, "error": "unknown"}
            def format_tool_result(self, result, state):
                return f"Result: {result['result']}" if result.get("success") else f"Error: {result.get('error')}"
        ```
    """

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize internal tool state from application config.

        Note:
            In the default ``AgentCore`` request flow, tools are initialized
            before the provider so their tool schemas can be injected into the
            provider config under the ``"tools"`` key.

        Args:
            config: Application-supplied configuration for the tool.

        Returns:
            Initial tool state dictionary.
        """
        return {"config": config}

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return capability/environment tags contributed by this tool.

        Note:
            In the default ``AgentCore`` dependency-resolution flow, these tags
            are aggregated with tags from the provider, provider extensions, and
            features to decide which tools are exposed.
        """
        return []

    def required_tags(self) -> List[str]:
        """Tags that must be present for this tool to be exposed."""
        return []

    def forbidden_tags(self) -> List[str]:
        """Tags that must NOT be present for this tool to be exposed.

        If any of these tags are in the available tag set, the tool is disabled.
        This provides a negative constraint complementary to required_tags.
        """
        return []

    def is_enabled(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Optional[bool]:
        """Return whether this tool should be enabled given the current context.

        This method allows tools to implement complex enablement logic that
        goes beyond simple tag matching. It receives the full runtime context
        including configuration, computed tags, model descriptors, and information
        about other enabled plugins.

        Args:
            config: Effective configuration for the current request.
            tags: Capability tags computed for this config.
            models: Model descriptors computed for this config.
            context: Additional context including:
                - "enabled_plugin_ids": dict mapping plugin kind to list of enabled plugin ids
                - "disabled_plugins": config-level disabled plugin id list
                - "force_enabled_plugins": config-level force-enabled plugin id list

        Returns:
            True: tool is enabled (bypass required_tags/forbidden_tags check)
            False: tool is disabled
            None: fall back to required_tags/forbidden_tags check (default)
        """
        return None

    def prepare(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform optional long-running preparation for later cheap hooks.

        ``prepare`` is separate from :meth:`init` so callers can keep schema
        discovery and preview helpers cheap by default. Implementations may do
        I/O, subprocess startup, discovery, or cache hydration here, but should
        return only JSON-like prepared data.
        """
        return {}

    async def prepare_async(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Async variant of :meth:`prepare` with identical semantics."""
        return self.prepare(config, state, context=context)

    def get_tool_schemas(
        self,
        state: Dict[str, Any],
        *,
        prepared: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Return tool schemas provided by this tool.

        Args:
            state: Current tool state (if needed by the tool).
            prepared: Optional JSON-like prepared data returned by
                :meth:`prepare` or :meth:`prepare_async`.

        Returns:
            List of tool definition dictionaries in any format understood by the
            active interop accessors/adapters.
        """
        return []

    def get_tool_interop_contribution(
        self,
        state: Dict[str, Any],
    ) -> "ToolInteropContribution":
        """Return tool-contributed tool interop accessors/adapters."""
        from .tool_interop import ToolInteropContribution

        return ToolInteropContribution()

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
        """Return whether this tool can handle the inspected tool call.

        ``None`` means no opinion and allows legacy name-based fallback.
        """
        return None

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
        """Execute a tool call using the final payload object.

        Args:
            tool_name: Name of the tool/function when available.
            payload: Final payload for the tool call, such as a dict or raw text.
            state: Current tool state.
            payload_kind: Optional semantic payload kind such as ``"object"`` or
                ``"text"``.
            payload_format: Optional format identifier for the payload itself.
            payload_metadata: Optional extra payload metadata from the accessor.
            tool_call: Optional original tool-call dict.
            context: Optional layered context providing access to runtime capabilities.
            prepared: Optional JSON-like prepared data returned by
                :meth:`prepare` or :meth:`prepare_async`.

        The ``context`` parameter provides layered access to runtime capabilities:

        **Layer 1 (Core - always present when called from AgentCore):**
            - ``core``: AgentCore instance for session/message operations and LLM calls
            - ``config``: Current resolved request configuration
            - ``trigger_source``: Where the tool was triggered ("core")
            - ``session``: Serialized session dict (session.to_dict()) when available

        **Layer 2 (Application - when called from AgentApplication):**
            - ``app`` and ``application``: AgentApplication instance
            - ``base_config``: Full base configuration (all agents)
            - ``session_asset_store``: Session asset store for file attachments
            - ``runtime_state_root``: Persistent runtime-state root directory

        Caller-supplied context is additive only. Reserved keys owned by the
        context builders are not overridden; on clashes the builder keeps the
        owned value and emits a warning.

        Tools can use context to make LLM calls::

            core = (context or {}).get("core")
            if core:
                temp_session = core.create_session()
                events = core.stream_request(temp_session, config)

        Returns:
            Result dictionary, e.g., {"success": bool, "result": any, "error": str}.
        """
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> Any:
        """Format a tool result dictionary for LLM consumption/display.

        Args:
            result: Tool execution result dictionary.
            state: Current tool state.

        Returns:
            Human-readable string representation or an explicit provider-native
            tool result payload.
        """
        if result.get("success"):
            return f"Result: {result.get('result')}"
        return f"Error: {result.get('error')}"

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
        """Generate a pre-execution preview for a tool call.

        This hook is invoked when an assistant message containing tool calls is
        finalized, before the tools are executed. It should return a brief
        summary of what the tool call will do.

        The preview is intended for human-facing UIs (e.g. a collapsible list of
        tool calls) and should not be used for model-facing tool output.

        Args:
            tool_name: Name of the tool/function when available.
            payload: Final payload for the tool call.
            state: Current tool state.
            prepared: Optional JSON-like prepared data returned by
                :meth:`prepare` or :meth:`prepare_async`.

        Returns:
            A short string (preferably single-line). Return an empty string when
            no preview is available.
        """

        return ""

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
        """Optional streaming execution hook for tools.

        Default implementation yields nothing. Concrete tools may override this
        to provide incremental, display-oriented results for long-running
        operations.

        Args:
            tool_name: Name of the tool/function when available.
            payload: Final payload for the tool call.
            state: Current tool state.
            payload_kind: Optional semantic payload kind.
            payload_format: Optional format identifier for the payload.
            payload_metadata: Optional extra payload metadata.
            tool_call: Optional original tool-call dict.
            cancellation: Optional cancellation token.
            context: Optional layered context providing access to runtime capabilities.
                See :meth:`execute_tool` for context structure documentation.
            prepared: Optional JSON-like prepared data returned by
                :meth:`prepare` or :meth:`prepare_async`.

        Yields:
            Dictionary chunks with partial results ({"part": ...}) or final
            result ({"success": bool, ...}).
        """
        return iter(())

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
        """Optional async execution hook for tool authors using async libraries."""
        return self.execute_tool(
            tool_name,
            payload,
            state,
            payload_kind=payload_kind,
            payload_format=payload_format,
            payload_metadata=payload_metadata,
            tool_call=tool_call,
            cancellation=cancellation,
            context=context,
            prepared=prepared,
        )

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
        """Optional async streaming hook for tool authors using async libraries."""
        for chunk in self.stream_tool(
            tool_name,
            payload,
            state,
            payload_kind=payload_kind,
            payload_format=payload_format,
            payload_metadata=payload_metadata,
            tool_call=tool_call,
            cancellation=cancellation,
            context=context,
            prepared=prepared,
        ):
            yield chunk

    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Optional display conversion hook for tool results.

        Default implementation wraps the formatted text in a simple
        ``{"type": "text", "content": text}`` payload suitable for UIs.

        Tools may optionally include a ``"single_line"`` field in the returned
        dict to provide a compact summary for collapsed/short views:
        ``{"type": "text", "content": <full>, "single_line": <compact>}``.

        The ``single_line`` field should contain a brief preview (e.g., just the
        command for shell tools, or a list of changed files for patch tools)
        that UIs can display when tool results are collapsed or shown in short
        mode. When expanded, UIs should use ``content`` for the full result.
        """
        return {"type": "text", "content": text}


@dataclass(frozen=True)
class Message:
    """Immutable message structure representing a single conversation message.

    Attributes:
        role: Message role ("system", "user", "assistant", or "tool").
        content: Message content text.
        metadata: Optional metadata dict containing tool_calls, tool_call_id, citations, etc.

    Examples:
        >>> msg = Message(role="user", content="Hello!")
        >>> msg.role
        'user'
        >>> msg.content
        'Hello!'
    """

    role: MessageRole
    content: Any
    metadata: Optional[Dict[str, Any]] = None
    multipart_content: Optional[List[Dict[str, Any]]] = None
    tool_result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format.

        Returns:
            Dictionary representation of the message.
        """
        result: Dict[str, Any] = {"role": self.role, "content": self.content}
        if self.metadata:
            result["metadata"] = deepcopy(self.metadata)
        if self.multipart_content:
            result["multipartContent"] = deepcopy(self.multipart_content)
        if self.tool_result:
            result["toolResult"] = deepcopy(self.tool_result)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary.

        Args:
            data: Dictionary containing role, content, and optional metadata.

        Returns:
            New Message instance.
        """
        multipart_content = data.get("multipartContent")
        if multipart_content is not None and not isinstance(multipart_content, list):
            raise TypeError("multipartContent must be a list or null")
        tool_result = data.get("toolResult")
        if tool_result is not None and not isinstance(tool_result, dict):
            raise TypeError("toolResult must be an object or null")

        return cls(
            role=data["role"],
            content=data["content"],
            metadata=deepcopy(data.get("metadata")),
            multipart_content=deepcopy(multipart_content),
            tool_result=deepcopy(tool_result),
        )


@dataclass(frozen=True)
class PartialMessage:
    """Partial message type used during streaming (forwarded to frontend as-is)."""

    role: MessageRole
    content: Any
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class Session:
    """Immutable session data structure (pure data container).

    Contains only data, no transformation logic. All transformations are performed
    by AgentCore functions that return new sessions.

    Attributes:
        session_id: Unique identifier for this session.
        messages: List of messages.
        metadata: Optional session-level metadata.

    Examples:
        >>> session = Session(session_id="test", messages=[])
        >>> len(session.messages)
        0
    """

    session_id: str
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary format.

        Returns:
            Dictionary representation of the session.
        """
        return {
            "session_id": self.session_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": deepcopy(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create session from dictionary.

        Args:
            data: Dictionary containing session_id, messages, and optional metadata.

        Returns:
            New Session instance.
        """
        messages = [Message.from_dict(msg) for msg in data.get("messages", [])]
        return cls(
            session_id=data["session_id"],
            messages=messages,
            metadata=deepcopy(data.get("metadata", {})),
        )
