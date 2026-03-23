from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from plugins.file_reader_tool import FileReaderTool
from plugins.math_tools import MathTools

from fireworks_test_utils import (
    FIREWORKS_KIMI_MODEL,
    build_fireworks_cfg,
    build_reference_core,
    fireworks_model,
    iter_request_stream_or_skip,
    send_request_or_skip,
)

pytestmark = [pytest.mark.integration, pytest.mark.fireworks]


MODELS = {
    "kimi_fireworks": FIREWORKS_KIMI_MODEL,
}


REPO_TMP_DIR = Path(__file__).resolve().parents[3] / "tmp"
REPO_TMP_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def temp_files():
    tmp_dir = tempfile.mkdtemp(dir=str(REPO_TMP_DIR))
    f1 = Path(tmp_dir) / "numbers.txt"
    f2 = Path(tmp_dir) / "data.txt"
    f1.write_text("42")
    f2.write_text("17")

    yield str(tmp_dir), str(f1), str(f2)

    try:
        f1.unlink()
        f2.unlink()
        Path(tmp_dir).rmdir()
    except Exception:
        pass


def create_core_with_tools():
    return build_reference_core(FileReaderTool, MathTools)


def get_config(allowed_paths: list[str] | None = None):
    cfg = build_fireworks_cfg(
        fireworks_model("FIREWORKS_KIMI_MODEL", FIREWORKS_KIMI_MODEL),
        request_options={"temperature": 0, "seed": 2},
    )
    if allowed_paths is not None:
        cfg["allowed_paths"] = allowed_paths
    cfg.setdefault("max_file_size", 1024 * 1024)
    return cfg


def _collect_response(core, session, config: dict, *, stream: bool):
    if not stream:
        return send_request_or_skip(core, session, config)

    final_event = None
    for event in iter_request_stream_or_skip(core, session, config):
        if event.get("type") == "final":
            final_event = event
    assert final_event is not None
    return final_event["session"], final_event["messages"]


def _assert_tool_calls_well_formed(tool_calls: list[dict], *, context: str):
    assert tool_calls, f"expected tool calls in {context}"
    for call in tool_calls:
        function = call.get("function") or {}
        name = function.get("name")
        assert isinstance(name, str) and name.strip(), (
            f"expected non-empty function.name in {context}, got {call!r}"
        )


def _execute_and_append_tool_calls(core, session, tool_calls: list[dict], config: dict):
    _assert_tool_calls_well_formed(tool_calls, context="tool execution")
    tool_messages = core.execute_tool_calls(tool_calls, config)
    assert tool_messages, "expected tool results"

    for tool_message in tool_messages:
        content = tool_message.get("content", "")
        assert "no tool handled 'None'" not in content
        session = core.add_message(
            session,
            role=tool_message.get("role", "tool"),
            content=content,
            metadata=tool_message.get("metadata"),
            config=config,
        )
    return session, tool_messages


@pytest.mark.parametrize("model_name,model_id", list(MODELS.items()))
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_single_tool_call_math_fireworks(model_name, model_id, stream):
    core = create_core_with_tools()
    config = get_config()
    config["model"] = model_id

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. When asked to perform calculations, "
        "you MUST use the provided math tools (add, multiply, square). "
        "Never calculate manually.",
    )
    session = core.add_message(
        session,
        "user",
        "Use the add tool to calculate 15 + 27. Return only the result.",
    )

    session, responses = _collect_response(core, session, config, stream=stream)
    assert responses, f"expected assistant response for {model_name}"

    assistant = responses[-1]
    tool_calls = (assistant.get("metadata") or {}).get("tool_calls") or []
    session, _tool_messages = _execute_and_append_tool_calls(
        core, session, tool_calls, config
    )

    _session, responses = _collect_response(core, session, config, stream=stream)
    assert responses, f"expected follow-up response for {model_name}"
    assert "42" in responses[-1].get("content", "")


@pytest.mark.parametrize("model_name,model_id", list(MODELS.items()))
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_single_tool_call_file_read_fireworks(temp_files, model_name, model_id, stream):
    tmp_dir, f1, _f2 = temp_files
    core = create_core_with_tools()
    config = get_config([tmp_dir])
    config["model"] = model_id
    config["working_directory"] = tmp_dir

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. When asked about file contents, you MUST use "
        f"the read_file tool. The working directory is: {tmp_dir}. You can use relative paths.",
    )
    session = core.add_message(
        session,
        "user",
        f"Use the read_file tool to read {os.path.basename(f1)} and tell me its exact content.",
    )

    session, responses = _collect_response(core, session, config, stream=stream)
    assert responses, f"expected assistant response for {model_name}"
    tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []
    session, _tool_messages = _execute_and_append_tool_calls(
        core, session, tool_calls, config
    )

    _session, responses = _collect_response(core, session, config, stream=stream)
    assert responses, f"expected follow-up response for {model_name}"
    assert "42" in responses[-1].get("content", "")


@pytest.mark.parametrize("model_name,model_id", list(MODELS.items()))
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_parallel_tool_calls_math_fireworks(model_name, model_id, stream):
    core = create_core_with_tools()
    config = get_config()
    config["model"] = model_id

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. When asked to perform multiple calculations, "
        "issue multiple tool calls in parallel in the same response. Use the math tools provided.",
    )
    session = core.add_message(
        session,
        "user",
        "Calculate three values using tools in parallel: (1) add 10 and 5, "
        "(2) multiply 3 and 7, (3) square 6. Return all three results.",
    )

    expected_results = {"15", "21", "36"}
    all_results: list[str] = []
    for _ in range(5):
        session, responses = _collect_response(core, session, config, stream=stream)
        assert responses, f"expected assistant response for {model_name}"
        assistant = responses[-1]
        tool_calls = (assistant.get("metadata") or {}).get("tool_calls") or []
        if not tool_calls:
            content = assistant.get("content", "")
            assert any(result in content for result in expected_results) or expected_results.issubset(
                set(all_results)
            )
            return

        session, tool_messages = _execute_and_append_tool_calls(
            core, session, tool_calls, config
        )
        all_results.extend((msg.get("content", "") or "").strip() for msg in tool_messages)
        if expected_results.issubset(set(all_results)):
            return

    pytest.fail(f"parallel math test did not complete; collected results: {all_results}")


@pytest.mark.parametrize("model_name,model_id", list(MODELS.items()))
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_parallel_tool_calls_file_read_fireworks(temp_files, model_name, model_id, stream):
    tmp_dir, f1, f2 = temp_files
    core = create_core_with_tools()
    config = get_config([tmp_dir])
    config["model"] = model_id
    config["working_directory"] = tmp_dir

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. When asked to read multiple files, issue multiple "
        f"read_file calls in parallel. The working directory is: {tmp_dir}. You can use relative paths.",
    )
    session = core.add_message(
        session,
        "user",
        f"Read both files in parallel: {os.path.basename(f1)} and {os.path.basename(f2)}. "
        "Then tell me the sum of the numbers they contain.",
    )

    all_results: list[str] = []
    for _ in range(5):
        session, responses = _collect_response(core, session, config, stream=stream)
        assert responses, f"expected assistant response for {model_name}"
        assistant = responses[-1]
        tool_calls = (assistant.get("metadata") or {}).get("tool_calls") or []
        if not tool_calls:
            content = assistant.get("content", "")
            has_data = "42" in content or "17" in content or "59" in content
            if not has_data:
                has_data = any("42" in result or "17" in result for result in all_results)
            assert has_data
            return

        session, tool_messages = _execute_and_append_tool_calls(
            core, session, tool_calls, config
        )
        all_results.extend(msg.get("content", "") or "" for msg in tool_messages)
        if any("42" in result for result in all_results) and any(
            "17" in result for result in all_results
        ):
            return

    pytest.fail(f"parallel file-read test did not complete; collected results: {all_results}")


@pytest.mark.parametrize("model_name,model_id", list(MODELS.items()))
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_tool_chain_math_sequence_fireworks(model_name, model_id, stream):
    core = create_core_with_tools()
    config = get_config()
    config["model"] = model_id

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. Use tools to solve multi-step calculations. "
        "Do not calculate manually.",
    )
    session = core.add_message(
        session,
        "user",
        "First add 10 and 5. Then take that result and multiply it by 3. "
        "Finally square the result. Use tools for each step.",
    )

    for _ in range(6):
        session, responses = _collect_response(core, session, config, stream=stream)
        assert responses, f"expected assistant response for {model_name}"
        assistant = responses[-1]
        tool_calls = (assistant.get("metadata") or {}).get("tool_calls") or []
        if not tool_calls:
            assert "2025" in responses[-1].get("content", "").replace(",", "")
            return
        session, _tool_messages = _execute_and_append_tool_calls(
            core, session, tool_calls, config
        )

    pytest.fail("tool chain math sequence did not complete")


@pytest.mark.parametrize("model_name,model_id", list(MODELS.items()))
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_tool_chain_file_then_math_fireworks(temp_files, model_name, model_id, stream):
    tmp_dir, f1, _f2 = temp_files
    core = create_core_with_tools()
    config = get_config([tmp_dir])
    config["model"] = model_id
    config["working_directory"] = tmp_dir

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. Use tools to solve problems step by step. "
        f"The working directory is: {tmp_dir}. You can use relative paths for files.",
    )
    session = core.add_message(
        session,
        "user",
        f"Read the number from {os.path.basename(f1)}, then square it using a math tool.",
    )

    for _ in range(4):
        session, responses = _collect_response(core, session, config, stream=stream)
        assert responses, f"expected assistant response for {model_name}"
        assistant = responses[-1]
        tool_calls = (assistant.get("metadata") or {}).get("tool_calls") or []
        if not tool_calls:
            normalized = (assistant.get("content", "") or "").replace(",", "")
            assert "1764" in normalized
            return
        session, _tool_messages = _execute_and_append_tool_calls(
            core, session, tool_calls, config
        )

    pytest.fail("tool chain file then math did not complete")


@pytest.mark.parametrize("model_name,model_id", list(MODELS.items()))
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_tool_chain_complex_multi_step_fireworks(temp_files, model_name, model_id, stream):
    tmp_dir, f1, f2 = temp_files
    core = create_core_with_tools()
    config = get_config([tmp_dir])
    config["model"] = model_id
    config["working_directory"] = tmp_dir

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. Use tools to solve problems step by step. "
        f"The working directory is: {tmp_dir}. You can use relative paths for files.",
    )
    session = core.add_message(
        session,
        "user",
        f"Read numbers from {os.path.basename(f1)} and {os.path.basename(f2)}, add them together, "
        "then square the result. Show your work step by step.",
    )

    for _ in range(10):
        session, responses = _collect_response(core, session, config, stream=stream)
        assert responses, f"expected assistant response for {model_name}"
        assistant = responses[-1]
        tool_calls = (assistant.get("metadata") or {}).get("tool_calls") or []
        if not tool_calls:
            normalized = (assistant.get("content", "") or "").replace(",", "")
            assert "3481" in normalized
            return
        session, _tool_messages = _execute_and_append_tool_calls(
            core, session, tool_calls, config
        )

    pytest.fail("complex tool chain did not complete")