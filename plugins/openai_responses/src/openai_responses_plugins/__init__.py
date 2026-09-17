"""OpenAI Responses provider bundle with lazy public exports."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
    "OpenAIResponsesProvider": (
        "openai_responses_provider",
        "OpenAIResponsesProvider",
    ),
    "OpenAIResponsesAttachmentsExtension": (
        "openai_responses_attachments_extension",
        "OpenAIResponsesAttachmentsExtension",
    ),
    "OpenAIResponsesChatGPTAuthFeature": (
        "openai_responses_chatgpt_auth_feature",
        "OpenAIResponsesChatGPTAuthFeature",
    ),
    "OpenAIResponsesFastModeExtension": (
        "openai_responses_fast_mode_extension",
        "OpenAIResponsesFastModeExtension",
    ),
    "OpenAIResponsesFlexProcessingExtension": (
        "openai_responses_flex_processing_extension",
        "OpenAIResponsesFlexProcessingExtension",
    ),
    "OpenAIResponsesNativeCompactionExtension": (
        "openai_responses_native_compaction_extension",
        "OpenAIResponsesNativeCompactionExtension",
    ),
    "OpenAIResponsesNativeCompactionAppPlugin": (
        "openai_responses_native_compaction_app",
        "OpenAIResponsesNativeCompactionAppPlugin",
    ),
    "OpenAIResponsesPromptCachingExtension": (
        "openai_responses_prompt_caching_extension",
        "OpenAIResponsesPromptCachingExtension",
    ),
    "OpenAIResponsesToolsExtension": (
        "openai_responses_tools_extension",
        "OpenAIResponsesToolsExtension",
    ),
    "OpenAIResponsesWebSearchExtension": (
        "openai_responses_websearch_extension",
        "OpenAIResponsesWebSearchExtension",
    ),
    "OpenAIResponsesReasoningExtension": (
        "openai_responses_reasoning_extension",
        "OpenAIResponsesReasoningExtension",
    ),
    "OpenAIResponsesUsageExtension": (
        "openai_responses_usage_extension",
        "OpenAIResponsesUsageExtension",
    ),
    "OpenAIResponsesVerbosityExtension": (
        "openai_responses_verbosity_extension",
        "OpenAIResponsesVerbosityExtension",
    ),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attribute = target
    value = getattr(import_module(f".{module_name}", __name__), attribute)
    globals()[name] = value
    return value
