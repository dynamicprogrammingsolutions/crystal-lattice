"""
Core data types for the AI Agent Platform.

This module defines immutable data structures following functional programming principles.
All transformations return new instances rather than modifying existing ones.
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
    """
    Common instance-level protocol for non-tool plugins (Provider, ProviderExtension, Feature).

    Unifies identity, configuration UI, and the subset of lifecycle methods whose
    signatures are identical across these plugin types. Methods should remain
    stateless and operate on explicit state parameters; plugin instances are short‑lived per request.
    """

    # Identity (attributes on the class)
    name: str
    version: str

    # Config/UI
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema describing this provider's configuration.

        Returns:
            Tuple of (final_messages, native_messages, new_state).
            native_messages MUST be full history (not a delta).
        """
        ...



    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """
        Return UI element definitions for configuring this provider.

        Returns:
            List of UI element descriptors used by frontends.
        """
        ...

    # Common lifecycle across provider/extension/feature
    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply UI/runtime updates to the shared provider state immutably.

        Args:
            state: Current shared provider state.
            updates: Partial updates (e.g., UI inputs) to merge.

        Returns:
            New shared provider state.
        """
        ...


class ProviderPlugin(BasePlugin, Protocol):
    """Protocol for provider plugins (new lifecycle)."""

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize provider state from application config.

        Args:
            config: Application-supplied configuration for the provider.

        Returns:
            Initial shared provider state owned by the provider wrapper.
        """
        ...

    # Message conversion
    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Convert core messages to this provider's native wire format.

        Args:
            messages: Core session messages.
            state: Current shared provider state.

        Returns:
            Provider-native messages suitable for API calls.
        """
        ...

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Convert provider-native messages into core message dictionaries.

        Args:
            native_messages: Provider-native messages to convert.
            state: Current shared provider state.

        Returns:
            Core messages derived from native messages.
        """
        ...

    # New request lifecycle
    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare for a new request with provider-native messages.

        Args:
            native_messages: Provider-native messages for this request.
            state: Current shared provider state.

        Returns:
            Updated shared provider state (or the same state).
        """
        ...

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        """
        Process a streaming chunk from the provider on the hot path.

        Args:
            native_chunk: Provider-native streaming chunk.
            native_messages: Provider-native input messages (context).
            state: Current shared provider state.

        Returns:
            Tuple of (final_messages, partial_messages, native_messages, new_state).
            native_messages MUST be the full provider-native history (not a delta).
        """
        ...

    # Returns: (final_messages, partial_messages, native_messages, new_state)

    def finalize(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Perform final processing after streaming completes; provider runs first in finalize chain.

        Args:
            native_messages: Full provider-native message history (all prior turns plus any for this turn).
            state: Current shared provider state.

        Returns:
            Tuple of (final_messages, native_messages, new_state). native_messages MUST be full history.
        """
        ...

    # Returns: (final_messages, native_messages, new_state)

    def to_display_format(
        self, message: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert a message to a display-friendly format for UIs.

        Args:
            message: Core message dictionary to format.
            state: Current shared provider state.

        Returns:
            Display-friendly message dictionary.
        """
        ...

    # I/O entry points now take native messages
    def call_api(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        """
        Make a non-streaming API call with provider-native messages.

        Args:
            native_messages: Provider-native input messages.
            state: Current shared provider state.

        Returns:
            Tuple of (final_messages, partial_messages, native_messages, new_state).
        """
        ...

    # Returns: (final_messages, partial_messages, native_messages, new_state)

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """
        Make a streaming API call; yields provider-native chunks.

        Args:
            native_messages: Provider-native input messages.
            state: Current shared provider state.

        Yields:
            Provider-native streaming chunks.
        """
        ...

    @staticmethod
    def detect_capabilities(config: Dict[str, Any]) -> List[str]:
        """
        Detect capability flags supported by the provider for a given config.

        Args:
            config: Application-supplied configuration for probing capabilities.

        Returns:
            List of capability identifiers.
        """
        ...


class ProviderExtensionPlugin(BasePlugin, Protocol):
    """Protocol for provider extension plugins (shared provider state)."""

    target_provider: str

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize with application config and shared provider state.

        Args:
            config: Application-supplied configuration.
            state: Current shared provider state.

        Returns:
            Updated shared provider state (or the same state).
        """
        ...

    # Stateless transforms
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform provider-native messages using visibility of core messages.

        Stateless and deterministic; must not depend on shared state or config.

        Args:
            messages: Core session messages for context.
            native_messages: Current provider-native messages.

        Returns:
            Updated provider-native messages.
        """
        ...

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform provider-native messages back into core messages.

        Stateless and deterministic; must not depend on shared state or config.

        Args:
            native_messages: Provider-native messages to transform.
            messages: Core session messages for context.

        Returns:
            Updated core messages.
        """
        ...

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare for a new request with provider-native messages.

        Args:
            native_messages: Provider-native messages for this request.
            state: Current shared provider state.

        Returns:
            Updated shared provider state (or the same state).
        """
        ...

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        """
        Observe/modify provider outputs for a streaming chunk.

        Called on the hot path for each provider-native chunk. May be called
        with native_chunk=None during provider finalize.

        Args:
            native_chunk: Provider-native streaming chunk, or None during finalize.
            messages: Core session messages (context).
            state: Current shared provider state.
            partial_messages: Current list of partial messages.
            final_messages: Current list of final messages.
            native_messages: Current list of provider-native messages.

        Returns:
            Tuple of (updated_partial_messages, updated_final_messages, updated_native_messages, new_state).
            updated_native_messages MUST be full history (not a delta).
        """
        ...

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Final cold-path processing after provider streaming/finalize.

        Args:
            final_messages: Final core messages emitted this turn.
            native_messages: Accumulated provider-native messages for this turn.
            state: Current shared provider state.

        Returns:
            Tuple of (final_messages, native_messages, new_state).
        """
        ...


class FeaturePlugin(BasePlugin, Protocol):
    """Protocol for feature plugins (cold path, shared state)."""

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize with application config and shared provider state.

        Args:
            config: Application-supplied configuration.
            state: Current shared provider state.

        Returns:
            Updated shared provider state (or the same state).
        """
        ...

    # Stateless transforms
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform provider-native messages using visibility of core messages.

        Stateless and deterministic; must not depend on shared state or config.

        Args:
            messages: Core session messages for context.
            native_messages: Current provider-native messages.

        Returns:
            Updated provider-native messages.
        """
        ...

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform provider-native messages back into core messages.

        Stateless and deterministic; must not depend on shared state or config.

        Args:
            native_messages: Provider-native messages to transform.
            messages: Core session messages for context.

        Returns:
            Updated core messages.
        """
        ...

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare for a new request with provider-native messages.

        Args:
            native_messages: Provider-native messages for this request.
            state: Current shared provider state.

        Returns:
            Updated shared provider state (or the same state).
        """
        ...

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Final cold-path processing after provider and extensions complete.

        Args:
            final_messages: Final core messages emitted this turn.
            native_messages: Accumulated provider-native messages for this turn.
            state: Current shared provider state.

        Returns:
            Tuple of (final_messages, native_messages, new_state).
        """
        ...


class ToolPlugin(BasePlugin, Protocol):
    """Protocol for tool plugins."""

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize internal tool state from application config.

        Args:
            config: Application-supplied configuration for the tool.

        Returns:
            Initial tool state dictionary.
        """
        ...

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Return OpenAI-style function definitions provided by this tool.

        Args:
            state: Current tool state (if needed by the tool).

        Returns:
            List of tool/function definition dictionaries.
        """
        ...

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool function by name with structured arguments.

        Args:
            tool_name: Name of the tool/function to execute.
            arguments: Structured arguments for the tool.
            state: Current tool state.

        Returns:
            Result dictionary, e.g., {"success": bool, "result": any, "error": str}.
        """
        ...

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """
        Format a tool result dictionary for LLM consumption/display.

        Args:
            result: Tool execution result dictionary.
            state: Current tool state.

        Returns:
            Human-readable string representation.
        """
        ...


@dataclass(frozen=True)
class Message:
    """
    Immutable message structure representing a single conversation message.

    Attributes:
        role: Message role ("system", "user", "assistant", or "tool")
        content: Message content text
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
        """
        Convert message to dictionary format.

        Returns:
            Dictionary representation of the message
        """
        result: Dict[str, Any] = {"role": self.role, "content": self.content}
        if self.metadata:
            result["metadata"] = deepcopy(self.metadata)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """
        Create message from dictionary.

        Args:
            data: Dictionary containing role, content, and optional metadata

        Returns:
            New Message instance
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
    """
    Immutable session data structure (pure data container).

    Contains only data, no transformation logic. All transformations
    are performed by AgentCore functions that return new sessions.

    Attributes:
        session_id: Unique identifier for this session
        messages: List of messages
        metadata: Optional session-level metadata

    Examples:
        >>> session = Session(session_id="test", messages=[])
        >>> len(session.messages)
        0
    """

    session_id: str
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert session to dictionary format.

        Returns:
            Dictionary representation of the session
        """
        return {
            "session_id": self.session_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": deepcopy(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """
        Create session from dictionary.

        Args:
            data: Dictionary containing session_id, messages, and optional metadata

        Returns:
            New Session instance
        """
        messages = [Message.from_dict(msg) for msg in data.get("messages", [])]
        return cls(
            session_id=data["session_id"],
            messages=messages,
            metadata=deepcopy(data.get("metadata", {})),
        )
