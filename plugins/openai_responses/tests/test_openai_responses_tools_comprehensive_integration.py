from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_tools_extension import (
    OpenAIResponsesToolsExtension,
)
from plugins.file_reader_tool import FileReaderTool
from plugins.math_tools import MathTools
from plugins.request_options_feature import RequestOptionsFeature


REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI tools integration tests")
    return api_key


@pytest.fixture
def temp_files(tmp_path: Path) -> Tuple[str, str, str]:
    numbers = tmp_path / "numbers.txt"
    data = tmp_path / "data.txt"
    numbers.write_text("42", encoding="utf-8")
    data.write_text("17", encoding="utf-8")
    return str(tmp_path), str(numbers), str(data)


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[OpenAIResponsesToolsExtension],
    )
    core.register_feature(RequestOptionsFeature)
    core.register_tool(FileReaderTool)
    core.register_tool(MathTools)
    return core


def _config(api_key: str, *, allowed_paths: List[str] | None = None) -> Dict[str, Any]:
    config: Dict[str, Any] = {
        "model": "gpt-5-mini",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 300,
        "temperature": 0.0,
        "max_file_size": 1024 * 1024,
    }
    if allowed_paths is not None:
        config["allowed_paths"] = allowed_paths
    return config


def _send_turn(
    core: AgentCore,
    session: Any,
    config: Dict[str, Any],
    *,
    stream: bool,
) -> Tuple[Any, List[Dict[str, Any]]]:
    if not stream:
        return core.send_request(session, config)

    final_session = None
    final_messages: List[Dict[str, Any]] = []
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "final":
            final_session = chunk.get("session")
            final_messages = chunk.get("messages") or []
            break

    assert final_session is not None, "expected final streaming event"
    return final_session, final_messages


def _assistant_tool_calls(message: Dict[str, Any]) -> List[Dict[str, Any]]:
    metadata = message.get("metadata") or {}
    tool_calls = metadata.get("tool_calls") or []
    assert isinstance(tool_calls, list)
    return tool_calls


def _assert_valid_tool_calls(tool_calls: List[Dict[str, Any]]) -> None:
    assert tool_calls, "expected at least one tool call"
    for tool_call in tool_calls:
        assert isinstance(tool_call.get("id"), str) and tool_call["id"], tool_call
        fn = tool_call.get("function") or {}
        assert isinstance(fn.get("name"), str) and fn["name"], tool_call
        assert isinstance(fn.get("arguments"), str) and fn["arguments"].strip(), tool_call


def _append_tool_messages(
    core: AgentCore,
    session: Any,
    tool_calls: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> tuple[Any, List[str]]:
    results: List[str] = []
    tool_messages = core.execute_tool_calls(tool_calls, config)
    assert tool_messages, "expected tool execution results"
    for tool_message in tool_messages:
        content = tool_message.get("content", "")
        results.append(str(content))
        session = core.add_message(
            session,
            role=tool_message.get("role", "tool"),
            content=content,
            metadata=tool_message.get("metadata"),
            config=config,
        )
    return session, results


@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_openai_responses_single_tool_call_math(
    ensure_openai_api_key: str,
    stream: bool,
) -> None:
    core = _build_core()
    config = _config(ensure_openai_api_key)

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. When asked to perform calculations, you MUST use "
        "the provided math tools and never calculate manually.",
    )
    session = core.add_message(
        session,
        "user",
        "Use the add tool to calculate 15 + 27. Return only the result.",
    )

    session, responses = _send_turn(core, session, config, stream=stream)
    assert responses, "expected assistant response"
    tool_calls = _assistant_tool_calls(responses[-1])
    _assert_valid_tool_calls(tool_calls)

    session, _tool_results = _append_tool_messages(core, session, tool_calls, config)
    session, responses = _send_turn(core, session, config, stream=stream)
    assert responses, "expected follow-up response"

    content = str(responses[-1].get("content") or "")
    assert "42" in content, f"Expected '42' in response, got: {content!r}"


@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_openai_responses_single_tool_call_file_read(
    ensure_openai_api_key: str,
    temp_files: Tuple[str, str, str],
    stream: bool,
) -> None:
    tmp_dir, f1, _f2 = temp_files
    core = _build_core()
    config = _config(ensure_openai_api_key, allowed_paths=[tmp_dir])
    config["working_directory"] = tmp_dir

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. When asked about file contents, you MUST use the "
        "read_file tool. Never guess.",
    )
    session = core.add_message(
        session,
        "user",
        f"Use the read_file tool to read {Path(f1).name} and tell me its exact content.",
    )

    session, responses = _send_turn(core, session, config, stream=stream)
    assert responses, "expected assistant response"
    tool_calls = _assistant_tool_calls(responses[-1])
    _assert_valid_tool_calls(tool_calls)

    session, _tool_results = _append_tool_messages(core, session, tool_calls, config)
    session, responses = _send_turn(core, session, config, stream=stream)
    assert responses, "expected follow-up response"

    content = str(responses[-1].get("content") or "")
    assert "42" in content, f"Expected '42' from file, got: {content!r}"


@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_openai_responses_parallel_tool_calls_math(
    ensure_openai_api_key: str,
    stream: bool,
) -> None:
    core = _build_core()
    config = _config(ensure_openai_api_key)

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. When asked to perform multiple calculations, issue "
        "multiple tool calls in parallel when possible and use the math tools provided.",
    )
    session = core.add_message(
        session,
        "user",
        "Calculate three values using tools in parallel: (1) add 10 and 5, "
        "(2) multiply 3 and 7, (3) square 6. Return all three results.",
    )

    expected_results = {"15", "21", "36"}
    all_results: List[str] = []

    for _ in range(5):
        session, responses = _send_turn(core, session, config, stream=stream)
        assert responses, "expected assistant response"

        assistant = responses[-1]
        tool_calls = _assistant_tool_calls(assistant)
        if not tool_calls:
            content = str(assistant.get("content") or "").lower()
            if not any(value in content for value in expected_results):
                assert expected_results.issubset(set(all_results)), (
                    f"Expected calculation results in response. Got: {content!r}. "
                    f"Collected results: {all_results}"
                )
            return

        _assert_valid_tool_calls(tool_calls)
        session, tool_results = _append_tool_messages(core, session, tool_calls, config)
        all_results.extend(result.strip() for result in tool_results)
        if expected_results.issubset(set(all_results)):
            return

    pytest.fail(f"Test did not complete in 5 rounds; collected results: {all_results}")


@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_openai_responses_parallel_tool_calls_file_read(
    ensure_openai_api_key: str,
    temp_files: Tuple[str, str, str],
    stream: bool,
) -> None:
    tmp_dir, f1, f2 = temp_files
    core = _build_core()
    config = _config(ensure_openai_api_key, allowed_paths=[tmp_dir])
    config["working_directory"] = tmp_dir

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. When asked to read multiple files, issue multiple "
        "read_file calls in parallel when possible.",
    )
    session = core.add_message(
        session,
        "user",
        f"Read both files in parallel: {Path(f1).name} and {Path(f2).name}. "
        "Then tell me the sum of the numbers they contain.",
    )

    all_results: List[str] = []

    for _ in range(5):
        session, responses = _send_turn(core, session, config, stream=stream)
        assert responses, "expected assistant response"

        assistant = responses[-1]
        tool_calls = _assistant_tool_calls(assistant)
        if not tool_calls:
            content = str(assistant.get("content") or "")
            has_data = "42" in content or "17" in content or "59" in content
            if not has_data:
                has_data = any("42" in result or "17" in result for result in all_results)
            assert has_data, (
                "Expected file contents (42, 17, or 59) in response. "
                f"Got: {content!r}. Collected results: {all_results}"
            )
            return

        _assert_valid_tool_calls(tool_calls)
        session, tool_results = _append_tool_messages(core, session, tool_calls, config)
        all_results.extend(tool_results)
        has_42 = any("42" in result for result in all_results)
        has_17 = any("17" in result for result in all_results)
        if has_42 and has_17:
            return

    pytest.fail(f"Test did not complete in 5 rounds; collected results: {all_results}")


@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_openai_responses_tool_chain_math_sequence(
    ensure_openai_api_key: str,
    stream: bool,
) -> None:
    core = _build_core()
    config = _config(ensure_openai_api_key)

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. Use the math tools to perform calculations. Break "
        "complex problems into steps using multiple tool calls.",
    )
    session = core.add_message(
        session,
        "user",
        "Calculate (5 + 3) * 4 using tools. First add 5 and 3, then multiply the result "
        "by 4. Show each step.",
    )

    for _ in range(5):
        session, responses = _send_turn(core, session, config, stream=stream)
        assert responses, "expected assistant response"

        assistant = responses[-1]
        tool_calls = _assistant_tool_calls(assistant)
        if not tool_calls:
            content = str(assistant.get("content") or "")
            assert "32" in content, f"Expected '32' in final answer, got: {content!r}"
            return

        _assert_valid_tool_calls(tool_calls)
        session, _tool_results = _append_tool_messages(core, session, tool_calls, config)

    pytest.fail("Tool chain did not complete in 5 rounds")


@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_openai_responses_tool_chain_file_then_math(
    ensure_openai_api_key: str,
    temp_files: Tuple[str, str, str],
    stream: bool,
) -> None:
    tmp_dir, f1, _f2 = temp_files
    core = _build_core()
    config = _config(ensure_openai_api_key, allowed_paths=[tmp_dir])
    config["working_directory"] = tmp_dir

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. Use the available tools to complete tasks. You have "
        "access to read_file, add, multiply, and square tools.",
    )
    session = core.add_message(
        session,
        "user",
        f"First read the number from {Path(f1).name}, then square that number using the "
        "square tool. Report the final result.",
    )

    for _ in range(4):
        session, responses = _send_turn(core, session, config, stream=stream)
        assert responses, "expected assistant response"

        assistant = responses[-1]
        tool_calls = _assistant_tool_calls(assistant)
        if not tool_calls:
            content = str(assistant.get("content") or "")
            assert "1764" in content.replace(",", ""), (
                f"Expected '1764' (42^2) in final answer, got: {content!r}"
            )
            return

        _assert_valid_tool_calls(tool_calls)
        session, _tool_results = _append_tool_messages(core, session, tool_calls, config)

    pytest.fail("Tool chain did not complete in 4 rounds")


@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_openai_responses_tool_chain_complex_multi_step(
    ensure_openai_api_key: str,
    temp_files: Tuple[str, str, str],
    stream: bool,
) -> None:
    tmp_dir, f1, f2 = temp_files
    core = _build_core()
    config = _config(ensure_openai_api_key, allowed_paths=[tmp_dir])
    config["working_directory"] = tmp_dir

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. Use tools to solve problems step by step.",
    )
    session = core.add_message(
        session,
        "user",
        f"Read numbers from {Path(f1).name} and {Path(f2).name}, add them together, then "
        "square the result. Show your work step by step.",
    )

    for _ in range(10):
        session, responses = _send_turn(core, session, config, stream=stream)
        assert responses, "expected assistant response"

        assistant = responses[-1]
        tool_calls = _assistant_tool_calls(assistant)
        if not tool_calls:
            content = str(assistant.get("content") or "")
            normalized = content.replace(",", "")
            assert "3481" in normalized, (
                "Expected '3481' ((42+17)^2) in final answer, got: "
                f"{content!r}"
            )
            return

        _assert_valid_tool_calls(tool_calls)
        session, _tool_results = _append_tool_messages(core, session, tool_calls, config)

    pytest.fail("Tool chain did not complete in 10 rounds")