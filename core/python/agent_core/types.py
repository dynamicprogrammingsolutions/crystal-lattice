"""
Core data types for the AI Agent Platform.

This module defines immutable data structures following functional programming principles.
All transformations return new instances rather than modifying existing ones.
"""

from typing import Any, Dict, List, Optional, Literal, Tuple, Protocol, Iterator, AsyncIterator
from dataclasses import dataclass, field
from copy import deepcopy


MessageRole = Literal["system", "user", "assistant", "tool"]


# Plugin Protocol Types

class ProviderPlugin(Protocol):
    """Protocol for provider plugins."""
    
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
    def to_native_messages(messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]: ...
    
    @staticmethod
    def from_native_messages(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]: ...
    
    @staticmethod
    def build_request_body(messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]: ...
    
    @staticmethod
    def process_chunk(native_chunk: Dict[str, Any], state: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]: ...
    
    @staticmethod
    def finalize(state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]: ...
    
    @staticmethod
    def to_display_format(message: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]: ...
    
    @staticmethod
    def call_api(body: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]: ...
    
    @staticmethod
    def stream_api(body: Dict[str, Any], state: Dict[str, Any]) -> Iterator[Dict[str, Any]]: ...
    
    @staticmethod
    def detect_capabilities(config: Dict[str, Any]) -> List[str]: ...


class ProviderExtensionPlugin(Protocol):
    """Protocol for provider extension plugins."""
    
    name: str
    version: str
    target_provider: str
    
    @staticmethod
    def get_config_schema() -> Dict[str, Any]: ...
    
    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]: ...
    
    @staticmethod
    def init(config: Dict[str, Any]) -> Dict[str, Any]: ...
    
    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]: ...
    
    @staticmethod
    def process_chunk(
        native_chunk: Dict[str, Any],
        provider_state: Dict[str, Any],
        extension_state: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]: ...
    
    @staticmethod
    def enhance_final_message(
        message: Dict[str, Any],
        metadata: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]: ...


class FeaturePlugin(Protocol):
    """Protocol for feature plugins."""
    
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
    def can_handle(capability_id: str, state: Dict[str, Any]) -> bool: ...
    
    @staticmethod
    def modify_request_body(body: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]: ...
    
    @staticmethod
    def transform_messages(messages: List[Dict[str, Any]], state: Dict[str, Any], direction: str) -> List[Dict[str, Any]]: ...
    
    @staticmethod
    def process_final_message(message: Dict[str, Any], conversation_state: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]: ...
    
    @staticmethod
    def format_display(display: Dict[str, Any], message: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]: ...


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
class Session:
    """
    Immutable session data structure (pure data container).
    
    Contains only data, no transformation logic. All transformations
    are performed by AgentCore functions that return new sessions.
    
    Attributes:
        session_id: Unique identifier for this session
        messages: Immutable tuple of messages
        metadata: Optional session-level metadata
    
    Examples:
        >>> session = Session(session_id="test", messages=())
        >>> len(session.messages)
        0
    """
    session_id: str
    messages: Tuple[Message, ...] = field(default_factory=tuple)
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
        messages = tuple(Message.from_dict(msg) for msg in data.get("messages", []))
        return cls(
            session_id=data["session_id"],
            messages=messages,
            metadata=deepcopy(data.get("metadata", {}))
        )



