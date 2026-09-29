"""Interleaved-thinking provider extension.

When this extension is enabled, thinking from previous assistant turns is
omitted from outgoing requests:

- ``<think>...</think>`` segments are removed from assistant message content
  (the form used by models that interleave thinking directly in content,
  for example through Ollama).
- ``reasoning`` and ``reasoning_content`` keys are removed from assistant
  native messages (the separate-field form used by Z.ai GLM and other
  OpenAI-compatible providers).

The stored session history is never modified — only the messages built for
the request. With the extension absent, the provider's default behavior
applies (content-embedded thinking stays in the history that is re-sent;
field-based reasoning is already dropped by the provider when building
requests).

This makes "preserve previous-turn thinking" a provider-independent switch:
include the plugin to omit prior thinking, exclude it to keep the provider
default. The current turn's thinking is unaffected — only previous turns
are stripped.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from agent_core.types import ProviderExtensionPlugin

_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)
_THINK_OPEN = re.compile(r"<think>.*\Z", re.DOTALL)

_REASONING_FIELDS = ("reasoning", "reasoning_content")


def strip_think_segments(content: str) -> str:
    """Remove ``<think>`` blocks from message content.

    Handles balanced blocks and a trailing unterminated block (which can
    appear when a streamed turn was cut off mid-thinking). Surrounding
    whitespace is normalized so stripped content does not leave blank runs.
    """

    without_blocks = _THINK_BLOCK.sub("", content)
    without_open = _THINK_OPEN.sub("", without_blocks)
    stripped = without_open.strip()
    if not stripped:
        return ""
    return re.sub(r"\n{3,}", "\n\n", stripped)


class InterleavedThinking(ProviderExtensionPlugin):
    """Omit previous-turn thinking blocks from outgoing requests."""

    name: str = "interleaved_thinking"
    version: str = "0.1.0"

    def required_tags(self) -> List[str]:
        return ["provider:openai_compatible"]

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        _ = (config, models)
        return ["ext:interleaved_thinking"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for message in native_messages:
            if not isinstance(message, dict) or message.get("role") != "assistant":
                out.append(message)
                continue
            cleaned = dict(message)
            for field in _REASONING_FIELDS:
                cleaned.pop(field, None)
            content = cleaned.get("content")
            if isinstance(content, str):
                cleaned["content"] = strip_think_segments(content)
            elif isinstance(content, list):
                cleaned_parts: List[Dict[str, Any]] = []
                for part in content:
                    if (
                        isinstance(part, dict)
                        and part.get("type") == "text"
                        and isinstance(part.get("text"), str)
                    ):
                        cleaned_parts.append(
                            {**part, "text": strip_think_segments(part["text"])}
                        )
                    else:
                        cleaned_parts.append(part)
                cleaned["content"] = cleaned_parts
            out.append(cleaned)
        return out
