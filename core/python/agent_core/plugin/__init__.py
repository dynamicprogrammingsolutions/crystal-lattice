"""
Plugin infrastructure for the AI Agent Platform.

This module provides specialized wrappers and adapters for each plugin type.
"""

from .provider import ProviderWrapper, ProviderAdapter
from .extension import ExtensionWrapper
from .feature import FeatureWrapper, FeatureAdapter
from .tool import ToolWrapper, ToolAdapter

__all__ = [
    "ProviderWrapper",
    "ProviderAdapter",
    "ExtensionWrapper",
    "FeatureWrapper",
    "FeatureAdapter",
    "ToolWrapper",
    "ToolAdapter",
]
