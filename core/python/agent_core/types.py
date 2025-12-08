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
    runtime_checkable,
)
from dataclasses import dataclass, field
from copy import deepcopy

MessageRole = Literal["system", "user", "assistant", "tool"]

# Plugin Protocol Types


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

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Return UI element definitions for configuring this plugin.

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
            def get_ui_elements(self) -> List[Dict[str, Any]]:  # optional
                return []
            def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
                # Provider state is an opaque dict; this minimal example
                # only stores configuration.
                return {"config": dict(config)}
            def initialize_request(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
                return state
            def to_native_messages(self, messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
                return list(messages)
            def from_native_messages(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
                return list(native_messages)
            def call_api(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
                content = f"Echo: {next((m['content'] for m in reversed(native_messages) if m.get('role')=='user'), '')}"
                return ([{"role": "assistant", "content": content}], [], [], state)
            def stream_api(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
                yield from []
        ```
    """

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize provider state from application config.

        Args:
            config: Application-supplied configuration for the provider.

        Returns:
            Initial shared provider state owned by the provider wrapper.
        """
        return {"config": dict(config)}

    # Message conversion
    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert core messages to this provider's native wire format.

        Note:
            When the core converts a single new message (e.g., via add_message), it passes a list
            containing only that single message in "messages". Implementations must handle both
            full-history lists and single-message lists.

        Args:
            messages: Core session messages (may be a single-element list for add_message).
            state: Current shared provider state.

        Returns:
            Provider-native messages suitable for API calls.
        """
        return [
            {"role": m.get("role", "user"), "content": m.get("content", "")}
            for m in messages
            if isinstance(m, dict)
        ]

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert provider-native messages into core message dictionaries.

        This base implementation intentionally ignores provider-specific
        reasoning fields. Providers and extensions that work with
        reasoning/thinking should surface that information via metadata
        (e.g., in a provider extension), not as a top-level field on the
        core message.

        Args:
            native_messages: Provider-native messages to convert.
            state: Current shared provider state.

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
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare for a new request with provider-native messages.

        Args:
            native_messages: Provider-native messages for this request.
            state: Current shared provider state.

        Returns:
            Updated shared provider state (or the same state).
        """
        return state

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        """Process a streaming chunk from the provider on the hot path.

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
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Perform final processing after streaming completes.

        The provider runs first in the finalize chain. Both final_messages and
        native_messages are provider-native. final_messages contains only the
        new messages for this turn; native_messages MUST be full history.

        Args:
            native_messages: Full provider-native message history (all prior turns plus any for this turn).
            state: Current shared provider state.

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

        Implementations must be pure and deterministic for a given
        (config, models) pair.
        """
        return []

    # I/O entry points now take native messages
    def call_api(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
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
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Make a streaming API call; yields provider-native chunks.

        Args:
            native_messages: Provider-native input messages.
            state: Current shared provider state.

        Yields:
            Provider-native streaming chunks.
        """
        return iter([])



class ProviderExtensionPlugin(BasePlugin, Protocol):
    """Protocol for provider extension plugins (shared provider state, hot + cold path observers).

    Provider extensions run in the provider's language and observe/transform streaming
    chunks on the hot path and participate in finalize on the cold path. They do not own
    separate state; they receive and update the shared provider state.

    Example:
        Basic prefix extension:

        ```python
        from typing import Any, Dict, List, Tuple, Optional
        class PrefixExt:
            name = "prefix"
            version = "1.0.0"
            def get_config_schema(self):
                return {"prefix": {"type": "string", "default": "[EXT]"}}
            def init(self, config, state):
                return state
            def process_chunk(self, native_chunk, state, partial_messages, final_messages, native_messages):
                pfx = state.get("config", {}).get("prefix", "[EXT]")
                finals = [{**m, "content": f"{pfx} {m['content']}"} for m in final_messages]
                return partial_messages, finals, native_messages, state
            def finalize(self, final_messages, native_messages, state):
                return final_messages, native_messages, state
        ```
    """

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize with application config and shared provider state.
 
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
        """
        return list(models)
 
    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return capability/environment tags contributed by this extension."""
        return []
 
    def required_tags(self) -> List[str]:
        """Tags that must be present for this extension to be enabled."""
        return []
 
    # Stateless transforms
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        """Transform provider-native messages using visibility of core messages (stateless).

        Note:
            When the core converts a single new message (e.g., via add_message), it passes a list containing only
            that single message in "messages". Implementations must handle both full-history lists and single-message lists.

        Args:
            messages: Core session messages for context (may be a single-element list for add_message).
            native_messages: Current provider-native messages.

        Returns:
            Updated provider-native messages.
        """
        return list(native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform provider-native messages back into core messages (stateless).

        Args:
            native_messages: Provider-native messages to transform.
            messages: Core session messages for context.

        Returns:
            Updated core messages.
        """
        return list(messages)

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare for a new request with provider-native messages.

        Args:
            native_messages: Provider-native messages for this request.
            state: Current shared provider state.

        Returns:
            Updated shared provider state (or the same state).
        """
        return state

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
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Final cold-path processing after provider streaming/finalize.

        Args:
            final_messages: Provider-native final messages emitted this turn (deltas).
            native_messages: Full provider-native message history for this turn.
            state: Current shared provider state.

        Returns:
            Tuple of (final_messages, native_messages, new_state), all provider-native.
        """
        return final_messages, native_messages, state


class FeaturePlugin(BasePlugin, Protocol):
    """Protocol for feature plugins (cold path; shared provider state).

    Features operate on the cold path only (no per-chunk processing). They can
    transform both provider-native messages and core messages during finalize and
    may update the shared provider state during init and initialize_request.

    Example:
        Minimal feature that annotates finals:

        ```python
        class TagFeature:
            name = "tag"
            version = "1.0.0"
            def get_config_schema(self):
                return {"enabled": {"type": "boolean", "default": True}}
            def init(self, config, state):
                return state
            def to_native_messages(self, messages, native_messages):
                return native_messages
            def from_native_messages(self, native_messages, messages):
                return messages
            def initialize_request(self, native_messages, state):
                return state
            def finalize(self, final_messages, native_messages, state):
                finals = [{**m, "metadata": {**m.get("metadata", {}), "tag": True}} for m in final_messages]
                return finals, native_messages, state
        ```
    """

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize with application config and shared provider state.
 
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
        """Statelessly transform or provide model descriptors."""
        return list(models)
 
    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return capability/environment tags contributed by this feature."""
        return []
 
    def required_tags(self) -> List[str]:
        """Tags that must be present for this feature to be enabled."""
        return []
 
    # Stateless transforms
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        """Transform provider-native messages using visibility of core messages (stateless).

        Note:
            When the core converts a single new message (e.g., via add_message), it passes a list containing only
            that single message in "messages". Implementations must handle both full-history lists and single-message lists.

        Args:
            messages: Core session messages for context (may be a single-element list for add_message).
            native_messages: Current provider-native messages.

        Returns:
            Updated provider-native messages.
        """
        return list(native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform provider-native messages back into core messages (stateless).

        Args:
            native_messages: Provider-native messages to transform.
            messages: Core session messages for context.

        Returns:
            Updated core messages.
        """
        return list(messages)

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare for a new request with provider-native messages.

        Args:
            native_messages: Provider-native messages for this request.
            state: Current shared provider state.

        Returns:
            Updated shared provider state (or the same state).
        """
        return state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Final cold-path processing after provider and extensions complete.

        Args:
            final_messages: Provider-native final messages emitted this turn (deltas).
            native_messages: Full provider-native message history for this turn.
            state: Current shared provider state.

        Returns:
            Tuple of (final_messages, native_messages, new_state), all provider-native.
        """
        return final_messages, native_messages, state


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

        Args:
            config: Application-supplied configuration for the tool.

        Returns:
            Initial tool state dictionary.
        """
        return {"config": dict(config)}

    def get_tags(

        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return capability/environment tags contributed by this tool."""
        return []

    def required_tags(self) -> List[str]:
        """Tags that must be present for this tool to be exposed."""
        return []

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return OpenAI-style function definitions provided by this tool.

        Args:
            state: Current tool state (if needed by the tool).

        Returns:
            List of tool/function definition dictionaries.
        """
        return []

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool function by name with structured arguments.

        Args:
            tool_name: Name of the tool/function to execute.
            arguments: Structured arguments for the tool.
            state: Current tool state.

        Returns:
            Result dictionary, e.g., {"success": bool, "result": any, "error": str}.
        """
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Format a tool result dictionary for LLM consumption/display.

        Args:
            result: Tool execution result dictionary.
            state: Current tool state.

        Returns:
            Human-readable string representation.
        """
        if result.get("success"):
            return f"Result: {result.get('result')}"
        return f"Error: {result.get('error')}"

    def stream_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        """Optional streaming execution hook for tools.

        Default implementation yields nothing. Concrete tools may override this
        to provide incremental, display-oriented results for long-running
        operations.
        """
        return iter(())

    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Optional display conversion hook for tool results.

        Default implementation wraps the formatted text in a simple
        ``{"type": "text", "content": text}`` payload suitable for UIs.
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
    content: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format.

        Returns:
            Dictionary representation of the message.
        """
        result: Dict[str, Any] = {"role": self.role, "content": self.content}
        if self.metadata:
            result["metadata"] = deepcopy(self.metadata)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary.

        Args:
            data: Dictionary containing role, content, and optional metadata.

        Returns:
            New Message instance.
        """
        return cls(
            role=data["role"],
            content=data["content"],
            metadata=deepcopy(data.get("metadata")),
        )


@dataclass(frozen=True)
class PartialMessage:
    """Partial message type used during streaming (forwarded to frontend as-is)."""

    role: MessageRole
    content: str
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
