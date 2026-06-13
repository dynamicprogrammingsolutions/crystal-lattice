from __future__ import annotations

from pathlib import Path
from typing import Any

from agent_core.core import AgentCore
from plugins.request_options_feature import RequestOptionsFeature
from repo_test_env import load_repo_root_env

from reference_openai_compatible_provider.attachments_extension import (
    OpenAICompatibleAttachmentsExtension,
)
from reference_openai_compatible_provider.provider import OpenAICompatibleProvider
from reference_openai_compatible_provider.reasoning_extension import (
    OpenAICompatibleReasoningExtension,
)
from reference_openai_compatible_provider.tools_extension import (
    OpenAICompatibleToolsExtension,
)
from reference_openai_compatible_provider.usage_extension import (
    OpenAICompatibleUsageExtension,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
REASONING_TEST_DIR = REPO_ROOT / "core/python/tests/reasoning_test"


def load_root_env() -> None:
    load_repo_root_env()


def build_reference_core(*tool_plugins: Any) -> AgentCore:
    core = AgentCore()
    for tool_plugin in tool_plugins:
        core.register_tool(tool_plugin)
    core.register_feature(RequestOptionsFeature)
    core.register_provider(
        OpenAICompatibleProvider,
        extensions=[
            OpenAICompatibleAttachmentsExtension,
            OpenAICompatibleToolsExtension,
            OpenAICompatibleReasoningExtension,
            OpenAICompatibleUsageExtension,
        ],
    )
    return core