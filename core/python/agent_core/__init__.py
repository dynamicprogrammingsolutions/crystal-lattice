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
from .constants import UIConfigKeys
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
    ExtensionWrapper,
    FeatureWrapper,
    ToolWrapper,
)

__version__ = "0.3.0"

__all__ = [
    # Core
    "AgentCore",
    # UI config contract (for plugins and frontends)
    "UIConfigKeys",
    # Data types
    "Session",
    "Message",
    "MessageRole",
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
]
