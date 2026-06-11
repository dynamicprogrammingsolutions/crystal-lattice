from __future__ import annotations

import os
from typing import Any

import pytest
import requests

from agent_core.core import AgentCore

from hosted_test_utils import REASONING_TEST_DIR
from plugins.file_reader_tool import FileReaderTool
from plugins.math_tools import MathTools
from plugins.request_options_feature import RequestOptionsFeature

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

OLLAMA_GLM_5_1_MODEL = "glm-5.1:cloud"
OLLAMA_KIMI_K2_6_MODEL = "kimi-k2.6:cloud"
OLLAMA_MINIMAX_M3_MODEL = "minimax-m3:cloud"
OLLAMA_INTERRUPTED_REASONING_MODELS = [
    ("OLLAMA_OPENAI_GLM_5_1_MODEL", OLLAMA_GLM_5_1_MODEL),
    ("OLLAMA_OPENAI_KIMI_K2_6_MODEL", OLLAMA_KIMI_K2_6_MODEL),
    ("OLLAMA_OPENAI_MINIMAX_M3_MODEL", OLLAMA_MINIMAX_M3_MODEL),
]


def _ollama_available(base_url: str) -> bool:
    try:
        r = requests.get(f"{base_url.rstrip('/')}/models", timeout=2)
        return bool(r.ok)
    except Exception:
        return False


def _ollama_cfg() -> dict:
    return {
        "base_url": os.environ.get(
            "OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1"
        ),
        "model": os.environ.get("OLLAMA_OPENAI_MODEL", "qwen3:0.6b"),
        "timeout": float(os.environ.get("OLLAMA_OPENAI_TIMEOUT", "60")),
    }


def _ollama_cloud_reasoning_cfg(
    model_env_var: str,
    default_model: str,
    *,
    request_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "base_url": os.environ.get(
            "OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1"
        ),
        "model": os.environ.get(model_env_var, default_model),
        "timeout": float(os.environ.get("OLLAMA_OPENAI_TIMEOUT", "180")),
        "allowed_paths": [str(REASONING_TEST_DIR)],
        "working_directory": str(REASONING_TEST_DIR),
        "max_file_size": 1024 * 1024,
    }
    if request_options:
        cfg["request_options"] = request_options
    return cfg


def _ollama_model_available(base_url: str, model: str) -> bool:
    try:
        response = requests.get(f"{base_url.rstrip('/')}/models", timeout=5)
    except Exception:
        return False
    if not response.ok:
        return False
    data = response.json().get("data") or []
    return any(isinstance(item, dict) and item.get("id") == model for item in data)


def _build_reference_core(*tool_plugins: Any) -> AgentCore:
    core = AgentCore()
    for tool_plugin in tool_plugins:
        core.register_tool(tool_plugin)
    core.register_feature(RequestOptionsFeature)
    core.register_provider(
        OpenAICompatibleProvider,
        extensions=[
            OpenAICompatibleToolsExtension,
            OpenAICompatibleReasoningExtension,
            OpenAICompatibleUsageExtension,
        ],
    )
    return core


def _reasoning_test_prompt() -> str:
    return (REASONING_TEST_DIR / "prompt.txt").read_text()


def _assistant_with_content(messages: list[dict[str, Any]]) -> dict[str, Any] | None:
    for message in reversed(messages):
        if message.get("role") == "assistant" and message.get("content"):
            return message
    return None


def _assistant_reasoning(message: dict[str, Any]) -> str:
    metadata = message.get("metadata") or {}
    reasoning = metadata.get("reasoning_content") or metadata.get("reasoning")
    if isinstance(reasoning, str):
        return reasoning.strip()
    return ""


def _assert_tool_calls_have_names(tool_calls: list[dict[str, Any]], *, model: str):
    for call in tool_calls:
        function = call.get("function") or {}
        name = function.get("name")
        assert isinstance(name, str) and name.strip(), (
            f"expected non-empty function.name for {model}, got {call!r}"
        )


def _run_interrupted_reasoning_test(cfg: dict[str, Any]) -> tuple[str, int, int]:
    core = _build_reference_core(FileReaderTool)
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You have access to the read_file tool. The working directory for file paths "
        f"is: {REASONING_TEST_DIR}. You can use relative file paths like 'bank0.json'.",
    )
    session = core.add_message(session, "user", _reasoning_test_prompt())

    session, first_responses = core.send_request(session, cfg)
    assert first_responses, "expected first assistant response"

    first_assistant = first_responses[-1]
    assert first_assistant.get("role") == "assistant"
    first_reasoning = _assistant_reasoning(first_assistant)
    assert first_reasoning, "expected first assistant reasoning"

    tool_calls = (first_assistant.get("metadata") or {}).get("tool_calls") or []
    assert tool_calls, "expected first assistant tool call"
    _assert_tool_calls_have_names(tool_calls, model=cfg["model"])

    tool_messages = core.execute_tool_calls(tool_calls, cfg)
    for tool_message in tool_messages:
        session = core.add_message(
            session,
            role=tool_message.get("role", "tool"),
            content=tool_message.get("content", ""),
            metadata=tool_message.get("metadata"),
            config=cfg,
        )

    session = core.add_message(session, "user", "give me the final result")
    _session, second_responses = core.send_request(session, cfg)
    assert second_responses, "expected interrupted follow-up assistant response"

    final_message = _assistant_with_content(second_responses)
    assert final_message is not None, "no final assistant content after interrupted follow-up"

    content = final_message.get("content", "").strip()
    second_reasoning = _assistant_reasoning(final_message)
    return content, len(first_reasoning), len(second_reasoning)


@pytest.mark.integration
@pytest.mark.ollama
def test_tools_tool_loop_ollama_openai_compat():
    cfg = _ollama_cfg()
    if not _ollama_available(cfg["base_url"]):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    core = AgentCore()
    core.register_tool(MathTools)
    core.register_feature(RequestOptionsFeature)
    core.register_provider(
        OpenAICompatibleProvider,
        extensions=[
            OpenAICompatibleToolsExtension,
            OpenAICompatibleReasoningExtension,
            OpenAICompatibleUsageExtension,
        ],
    )

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Use the add tool to add 2 and 3. After using tools, reply with just the number.",
    )

    session2, finals = core.send_request(session, cfg)
    assert finals and finals[-1]["role"] == "assistant"

    tool_calls = (finals[-1].get("metadata") or {}).get("tool_calls")
    if not isinstance(tool_calls, list) or not tool_calls:
        pytest.skip("Model did not emit tool calls")

    tool_messages = core.execute_tool_calls(tool_calls, cfg)
    assert tool_messages

    for tm in tool_messages:
        session2 = core.add_message(
            session2,
            tm.get("role", "tool"),
            tm.get("content", ""),
            metadata=tm.get("metadata"),
            config=cfg,
        )

    _session3, finals2 = core.send_request(session2, cfg)
    assert finals2 and finals2[-1]["role"] == "assistant"


@pytest.mark.integration
@pytest.mark.ollama
def test_reasoning_metadata_ollama_openai_compat():
    cfg = {**_ollama_cfg(), "request_options": {"think": True}}

    if not _ollama_available(cfg["base_url"]):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    core = AgentCore()
    core.register_feature(RequestOptionsFeature)
    core.register_provider(
        OpenAICompatibleProvider,
        extensions=[
            OpenAICompatibleToolsExtension,
            OpenAICompatibleReasoningExtension,
            OpenAICompatibleUsageExtension,
        ],
    )

    session = core.create_session()
    session = core.add_message(
        session, "user", "Compute 12*12. Return only the number."
    )

    final_event = None
    try:
        for e in core.send_request_stream(session, cfg):
            if e.get("type") == "final":
                final_event = e
    except RuntimeError as e:
        msg = str(e)
        if "reasoning" in msg or "think value" in msg:
            pytest.skip("Reasoning request options not supported by this model/server")
        raise

    assert final_event is not None
    assistant = final_event["messages"][-1]
    reasoning = (assistant.get("metadata") or {}).get("reasoning")
    if not isinstance(reasoning, str) or not reasoning:
        pytest.skip(
            "No reasoning metadata produced (model/server may not support reasoning deltas)"
        )


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.parametrize(
    "model_env_var,default_model",
    OLLAMA_INTERRUPTED_REASONING_MODELS,
    ids=["glm-5.1-cloud", "kimi-k2.6-cloud", "minimax-m3-cloud"],
)
def test_reasoning_test_interrupted_user_followup_ollama_cloud_models(
    model_env_var: str,
    default_model: str,
):
    cfg = _ollama_cloud_reasoning_cfg(
        model_env_var, default_model, request_options={"think": True}
    )
    if not _ollama_model_available(cfg["base_url"], cfg["model"]):
        pytest.skip(f"Ollama model {cfg['model']!r} is not available")

    last_failure: tuple[str, int, int] | None = None
    for _ in range(5):
        content, first_reasoning_length, second_reasoning_length = (
            _run_interrupted_reasoning_test(cfg)
        )
        if (
            "Clock" in content
            and first_reasoning_length > 0
            and (
                second_reasoning_length == 0
                or second_reasoning_length < first_reasoning_length
            )
        ):
            return
        last_failure = (content, first_reasoning_length, second_reasoning_length)

    pytest.fail(
        f"Ollama reasoning for {cfg['model']!r} did not survive the inserted user "
        "follow-up in the bank-file reasoning test. "
        f"Last attempt details: content={last_failure[0]!r}, "
        f"first_reasoning_length={last_failure[1]}, "
        f"second_reasoning_length={last_failure[2]}",
        pytrace=False,
    )

