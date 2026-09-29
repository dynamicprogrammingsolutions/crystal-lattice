"""Interleaved-thinking provider extension for the OpenAI-compatible provider."""

from .plugin import InterleavedThinking, strip_think_segments

__all__ = ["InterleavedThinking", "strip_think_segments"]
