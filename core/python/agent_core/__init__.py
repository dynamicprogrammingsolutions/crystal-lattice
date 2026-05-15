"""
AI Agent Platform Core SDK.

A modular, functional AI agent platform for building conversational applications
with any LLM provider through an extensible plugin system.

Functional Architecture:
- AgentCore stores only the processing pipeline (registered plugins via adapters)
- Session is an immutable dataclass (pure data container)
- Config is managed by the application layer
- All transformations are pure functions that return new objects
- Specialized adapters provide typed, intuitive interfaces for each plugin type
"""

from .core import AgentCore
from .types import (
    Message,
    Session,
    MessageRole,
    ToolDescriptor,
    ProviderPlugin,
    ProviderExtensionPlugin,
    FeaturePlugin,
    ToolPlugin,
)
from .plugin import (
    ProviderWrapper,
    ExtensionWrapper,
    FeatureWrapper,
    ToolWrapper,
)
from .tool_result_payloads import (
    FORMAT_ANTHROPIC_MESSAGES,
    FORMAT_OPENAI_CHAT_COMPLETIONS,
    FORMAT_OPENAI_RESPONSES,
    PROVIDER_NATIVE_TOOL_RESULT_TYPE,
    make_provider_native_tool_result,
)

__version__ = "0.3.0"

__all__ = [
    # Core
    "AgentCore",
    # Data types
    "Session",
    "Message",
    "MessageRole",
    "ToolDescriptor",
    # Plugin protocols
    "ProviderPlugin",
    "ProviderExtensionPlugin",
    "FeaturePlugin",
    "ToolPlugin",
    # Specialized wrappers
    "ProviderWrapper",
    "ExtensionWrapper",
    "FeatureWrapper",
    "ToolWrapper",
    "PROVIDER_NATIVE_TOOL_RESULT_TYPE",
    "FORMAT_ANTHROPIC_MESSAGES",
    "FORMAT_OPENAI_CHAT_COMPLETIONS",
    "FORMAT_OPENAI_RESPONSES",
    "make_provider_native_tool_result",
]
