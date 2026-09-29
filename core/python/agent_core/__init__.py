"""
AI Agent Platform Core SDK.

A modular, functional AI agent platform for building conversational applications
with any LLM provider through an extensible plugin system.

Architecture:
- AgentCore stores registered plugin wrappers and Core-local caches.
- Session and Message are frozen dataclasses whose nested values are treated
  as immutable by convention.
- Applications manage durable sessions and configuration.
- Session operations return new values; request and tool methods may perform
  external I/O.
- Specialized adapters provide interfaces and defaults for each plugin type.
"""

from .core import AgentCore
from .model_cache import ModelDiscoveryCache
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
    "ModelDiscoveryCache",
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
