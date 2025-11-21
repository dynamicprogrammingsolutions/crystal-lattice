"""
Plugin infrastructure for the AI Agent Platform.

This module provides specialized wrappers for each plugin type.
"""

from .provider import ProviderWrapper
from .extension import ExtensionWrapper
from .feature import FeatureWrapper
from .tool import ToolWrapper

__all__ = [
    "ProviderWrapper",
    "ExtensionWrapper",
    "FeatureWrapper",
    "ToolWrapper",
]
