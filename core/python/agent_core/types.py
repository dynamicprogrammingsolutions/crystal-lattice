"""
Core data types for the AI Agent Platform.

This module defines immutable data structures following functional programming principles.
All transformations return new instances rather than modifying existing ones.
"""

from typing import Any, Dict, List, Optional, Literal, Tuple, Protocol, Iterator, AsyncIterator, runtime_checkable
from dataclasses import dataclass, field
from copy import deepcopy


MessageRole = Literal["system", "user", "assistant", "tool"]


# Plugin Protocol Types

# Wrapper Protocol Types (for adapters/wrappers to implement)
class ProviderWrapperProtocol(Protocol):
    name: str
    version: str

    def initialize(self, config: Dict[str, Any]) -> None: ...
    def update_state(self, updates: Dict[str, Any]) -> None: ...
    def get_config_schema(self) -> Dict[str, Any]: ...
    def get_ui_elements(self) -> List[Dict[str, Any]]: ...

    def to_native_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...
    def initialize_request(self, native_messages: List[Dict[str, Any]]) -> None: ...
    def call_api(self, native_messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]: ...
    def stream_api(self, native_messages: List[Dict[str, Any]]) -> Iterator[Dict[str, Any]]: ...
    async def stream_api_async(self, native_messages: List[Dict[str, Any]]) -> AsyncIterator[Dict[str, Any]]: ...
    def process_chunk(self, native_chunk: Dict[str, Any], messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]: ...
    def finalize(self, native_messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]: ...

    def get_extension_config_schemas(self) -> Dict[str, Any]: ...
    def get_extension_ui_elements(self) -> Dict[str, List[Dict[str, Any]]]: ...

    def get_state(self) -> Dict[str, Any]: ...
    def set_state(self, state: Dict[str, Any]) -> None: ...
    def reset_state(self) -> None: ...

class ExtensionWrapperProtocol(Protocol):
    name: str
    version: str
    target_provider: Optional[str]

    def get_config_schema(self) -> Dict[str, Any]: ...
    def get_ui_elements(self) -> List[Dict[str, Any]]: ...

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]: ...
    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]: ...

    def to_native_messages(self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...
    def from_native_messages(self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...

    def initialize_request(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]: ...

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]: ...

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]: ...


class FeatureWrapperProtocol(Protocol):
    name: str
    version: str

    def get_config_schema(self) -> Dict[str, Any]: ...
    def get_ui_elements(self) -> List[Dict[str, Any]]: ...

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]: ...
    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]: ...
    def to_native_messages(self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...

    def from_native_messages(self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...

    def initialize_request(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]: ...

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]: ...


class ToolWrapperProtocol(Protocol):
    name: str
    version: str

    def get_config_schema(self) -> Dict[str, Any]: ...
    def get_ui_elements(self) -> List[Dict[str, Any]]: ...

    def initialize(self, config: Dict[str, Any]) -> None: ...
    def update_state(self, updates: Dict[str, Any]) -> None: ...

    def get_tool_schemas(self) -> List[Dict[str, Any]]: ...
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]: ...
    def format_tool_result(self, result: Dict[str, Any]) -> str: ...

# Plugin Protocol Types

class ProviderPlugin(Protocol):
    """Protocol for provider plugins (new lifecycle)."""

    name: str
    version: str

    @staticmethod
    def get_config_schema() -> Dict[str, Any]: ...

    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]: ...

    @staticmethod
    def init(config: Dict[str, Any]) -> Dict[str, Any]: ...

    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]: ...

    # Message conversion
    @staticmethod
    def to_native_messages(messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]: ...

    @staticmethod
    def from_native_messages(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]: ...

    # New request lifecycle
    @staticmethod
    def initialize_request(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]: ...

    @staticmethod
    def process_chunk(
        native_chunk: Dict[str, Any],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]: ...
    # Returns: (final_messages, partial_messages, native_messages, new_state)

    @staticmethod
    def finalize(
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]: ...
    # Returns: (final_messages, native_messages, new_state)

    @staticmethod
    def to_display_format(message: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]: ...

    # I/O entry points now take native messages
    @staticmethod
    def call_api(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]: ...
    # Returns: (final_messages, partial_messages, native_messages, new_state)

    @staticmethod
    def stream_api(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Iterator[Dict[str, Any]]: ...

    @staticmethod
    def detect_capabilities(config: Dict[str, Any]) -> List[str]: ...


class ProviderExtensionPlugin(Protocol):
    """Protocol for provider extension plugins (shared provider state)."""

    name: str
    version: str
    target_provider: str

    @staticmethod
    def get_config_schema() -> Dict[str, Any]: ...

    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]: ...

    @staticmethod
    def init(config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]: ...

    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]: ...

    # Stateless transforms
    @staticmethod
    def to_native_messages(messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...

    @staticmethod
    def from_native_messages(native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...

    @staticmethod
    def initialize_request(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]: ...

    @staticmethod
    def process_chunk(
        native_chunk: Optional[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]: ...
    # Returns: (partial_messages, final_messages, native_messages, new_state)

    @staticmethod
    def finalize(
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]: ...


class FeaturePlugin(Protocol):
    """Protocol for feature plugins (cold path, shared state)."""

    name: str
    version: str

    @staticmethod
    def get_config_schema() -> Dict[str, Any]: ...

    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]: ...

    @staticmethod
    def init(config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]: ...

    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]: ...

    # Stateless transforms
    @staticmethod
    def to_native_messages(messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...

    @staticmethod
    def from_native_messages(native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...

    @staticmethod
    def initialize_request(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]: ...

    @staticmethod
    def finalize(
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]: ...


class ToolPlugin(Protocol):
    """Protocol for tool plugins."""

    name: str
    version: str

    @staticmethod
    def get_config_schema() -> Dict[str, Any]: ...

    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]: ...

    @staticmethod
    def init(config: Dict[str, Any]) -> Dict[str, Any]: ...

    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]: ...

    @staticmethod
    def get_tool_schemas(state: Dict[str, Any]) -> List[Dict[str, Any]]: ...

    @staticmethod
    def execute_tool(
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]: ...

    @staticmethod
    def format_tool_result(result: Dict[str, Any], state: Dict[str, Any]) -> str: ...


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
        result: Dict[str, Any] = {
            "role": self.role,
            "content": self.content
        }
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
            metadata=deepcopy(data.get("metadata"))
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
            "metadata": deepcopy(self.metadata)
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
            metadata=deepcopy(data.get("metadata", {}))
        )
