from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from agent_core.core import AgentCore
from plugins.request_options_feature import RequestOptionsFeature

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
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


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