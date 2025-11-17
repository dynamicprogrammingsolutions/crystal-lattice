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
    ProviderPlugin,
    ProviderExtensionPlugin,
    FeaturePlugin,
    ToolPlugin,
)
from .plugin import (
    ProviderWrapper,
    ProviderAdapter,
    ExtensionWrapper,
    FeatureWrapper,
    FeatureAdapter,
    ToolWrapper,
    ToolAdapter,
)

__version__ = "0.3.0"

__all__ = [
    # Core
    "AgentCore",
    # Data types
    "Session",
    "Message",
    "MessageRole",
    # Plugin protocols
    "ProviderPlugin",
    "ProviderExtensionPlugin",
    "FeaturePlugin",
    "ToolPlugin",
    # Specialized adapters and wrappers
    "ProviderWrapper",
    "ProviderAdapter",
    "ExtensionWrapper",
    "FeatureWrapper",
    "FeatureAdapter",
    "ToolWrapper",
    "ToolAdapter",
]
