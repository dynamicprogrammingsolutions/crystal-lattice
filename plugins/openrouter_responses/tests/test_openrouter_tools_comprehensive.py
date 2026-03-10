"""
Comprehensive tool calling tests for OpenRouter provider.

Tests three scenarios:
1. Single tool call - one tool, one round
2. Parallel tool calls - multiple tools in one turn
3. Tool chains - multiple rounds with dependencies

Models tested:
- OpenAI GPT-5 Mini
- Claude Haiku 4.5
- Gemini 3 Pro Preview
- Grok 4 Fast
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# Load .env file if it exists
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from agent_core import AgentCore
from plugins.file_reader_tool import FileReaderTool
from plugins.math_tools import MathTools
from openrouter_responses_plugins.openrouter_responses_provider import OpenRouterResponsesProvider
from openrouter_responses_plugins.openrouter_responses_reasoning_extension import OpenRouterResponsesReasoningExtension
from openrouter_responses_plugins.openrouter_responses_tools_extension import OpenRouterResponsesToolsExtension
from plugins.request_options_feature import RequestOptionsFeature

pytestmark = [pytest.mark.integration, pytest.mark.openrouter]


MODELS = {
    "gpt5_mini": "openai/gpt-5-mini",
    "claude_haiku": "anthropic/claude-haiku-4.5",
    "gemini_3_flash": "google/gemini-3-flash-preview",
    "grok_4_fast": "x-ai/grok-4-fast",
}


REPO_TMP_DIR = Path(__file__).resolve().parents[3] / "tmp"
REPO_TMP_DIR.mkdir(parents=True, exist_ok=True)


def _get_openai_provider_options() -> dict[str, object]:
    """Build provider routing block based on OPENAI_PROVIDER.

    OPENAI_PROVIDER can be set to "openai" or "azure" (or another
    OpenRouter-backed provider id); defaults to "openai".
    """
    provider_id = os.getenv("OPENAI_PROVIDER")
    if not provider_id:
        return {}
    else:
        return {
            "provider": {
                "order": [provider_id],
                "allow_fallbacks": False,
            }
        }


@pytest.fixture(scope="module")
def ensure_api_key():
    """Skip tests if OpenRouter API key is not configured."""
    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter tools tests")


@pytest.fixture
def temp_files():
    """Create temporary test files."""
    tmp_dir = tempfile.mkdtemp(dir=str(REPO_TMP_DIR))
    f1 = Path(tmp_dir) / "numbers.txt"
    f2 = Path(tmp_dir) / "data.txt"
    f1.write_text("42")
    f2.write_text("17")
    
    yield str(tmp_dir), str(f1), str(f2)
    
    # Cleanup
    try:
        f1.unlink()
        f2.unlink()
        Path(tmp_dir).rmdir()
    except Exception:
        pass


def create_core_with_tools():
    """Create AgentCore with OpenRouter provider, tools, and request options."""
    core = AgentCore()
    extensions = [OpenRouterResponsesReasoningExtension, OpenRouterResponsesToolsExtension]
    core.register_provider(OpenRouterResponsesProvider, extensions=extensions)
    core.register_feature(RequestOptionsFeature)
    core.register_tool(FileReaderTool)
    core.register_tool(MathTools)
    return core


def get_config(model: str, allowed_paths: list | None = None):
    """Get configuration for OpenRouter with tool support and reasoning enabled.

    For OpenAI models, lock routing to the "openai" provider without fallbacks
    via RequestOptionsFeature so that encrypted reasoning_details are handled
    consistently.
    """
    if allowed_paths is None:
        allowed_paths = [""]

    config: dict[str, object] = {
        "model": model,
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 300,  # Increased timeout for slower models and streaming
        "allowed_paths": allowed_paths,
        "max_file_size": 1024 * 1024,
        "temperature": 0.0,
        "enable_reasoning": True,
        "reasoning_effort": "low",
    }

    if isinstance(model, str) and model.startswith("openai/"):
        config["request_options"] = _get_openai_provider_options()

    return config





# ==========================================================================
# Single Tool Call Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.openrouter
@pytest.mark.parametrize("model_name,model_id", list(MODELS.items()))
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_single_tool_call_math(ensure_api_key, model_name, model_id, stream):
    """Test single tool call with math operation."""
    core = create_core_with_tools()
    config = get_config(model_id)
    
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. When asked to perform calculations, "
        "you MUST use the provided math tools (add, multiply, square). "
        "Never calculate manually."
    )
    session = core.add_message(
        session,
        "user",
        "Use the add tool to calculate 15 + 27. Return only the result."
    )
    
    mode = "streaming" if stream else "non-streaming"
    print(f"\n[{model_name}] Testing single tool call ({mode})...")
    
    # Round 1: expect tool call
    responses = []
    if stream:
        for chunk in core.send_request_stream(session, config):
            if chunk["type"] == "final":
                session = chunk["session"]
                responses = chunk["messages"]
                break
    else:
        session, responses = core.send_request(session, config)
    
    assert responses, "expected assistant response"
    
    assistant = responses[-1]
    metadata = assistant.get("metadata", {})
    tool_calls = metadata.get("tool_calls", [])
    
    print(f"  Tool calls received: {len(tool_calls)}")
    assert len(tool_calls) >= 1, f"expected at least 1 tool call, got {len(tool_calls)}"
    
    # Execute tool
    tool_msgs = core.execute_tool_calls(tool_calls, config)
    assert tool_msgs, "expected tool results"
    for tm in tool_msgs:
        print(f"  Tool result: {tm.get('content', '')}")
        session = core.add_message(
            session,
            role=tm.get("role", "tool"),
            content=tm.get("content", ""),
            metadata=tm.get("metadata"),
            config=config,
        )

    
    # Round 2: expect final answer using the same mode
    responses = []
    if stream:
        for chunk in core.send_request_stream(session, config):
            if chunk["type"] == "final":
                session = chunk["session"]
                responses = chunk["messages"]
                break
    else:
        session, responses = core.send_request(session, config)

    assert responses, "expected follow-up response"
    
    final = responses[-1]
    content = final.get("content", "")
    print(f"  Final answer: {content}")
    
    # Should mention 42 (15 + 27)
    assert "42" in content, f"Expected '42' in response, got: {content!r}"


@pytest.mark.integration
@pytest.mark.openrouter
@pytest.mark.parametrize("model_name,model_id", list(MODELS.items()))
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_single_tool_call_file_read(ensure_api_key, temp_files, model_name, model_id, stream):
    """Test single tool call with file reading (streaming and non-streaming)."""
    tmp_dir, f1, f2 = temp_files
    core = create_core_with_tools()
    
    # Use working_directory for relative path resolution
    config = get_config(model_id, allowed_paths=[tmp_dir])
    config["working_directory"] = tmp_dir
    
    # Get just the filename for relative path
    f1_name = os.path.basename(f1)
    
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        f"You are a helpful assistant. When asked about file contents, "
        f"you MUST use the read_file tool. Never guess. "
        f"The working directory is: {tmp_dir}. You can use relative paths."
    )
    session = core.add_message(
        session,
        "user",
        f"Use the read_file tool to read {f1_name} and tell me its exact content."
    )
    
    mode = "streaming" if stream else "non-streaming"
    print(f"\n[{model_name}] Testing single file read ({mode})...")
    
    # Round 1: expect tool call
    responses = []
    if stream:
        for chunk in core.send_request_stream(session, config):
            if chunk["type"] == "final":
                session = chunk["session"]
                responses = chunk["messages"]
                break
    else:
        session, responses = core.send_request(session, config)
    assert responses, "expected assistant response"
    
    assistant = responses[-1]
    metadata = assistant.get("metadata", {})
    tool_calls = metadata.get("tool_calls", [])
    
    assert len(tool_calls) >= 1, "expected at least 1 tool call"
    
    # Execute and send back
    tool_msgs = core.execute_tool_calls(tool_calls, config)
    for tm in tool_msgs:
        print(f"  Tool result: {tm.get('content', '')}")
        session = core.add_message(
            session,
            role=tm.get("role", "tool"),
            content=tm.get("content", ""),
            metadata=tm.get("metadata"),
            config=config,
        )
    
    # Round 2: expect answer with file content using same mode
    responses = []
    if stream:
        for chunk in core.send_request_stream(session, config):
            if chunk["type"] == "final":
                session = chunk["session"]
                responses = chunk["messages"]
                break
    else:
        session, responses = core.send_request(session, config)
    assert responses, "expected follow-up response"
    
    final = responses[-1]
    content = final.get("content", "")
    print(f"  Final answer: {content}")
    
    assert "42" in content, f"Expected '42' from file, got: {content!r}"


# ============================================================================
# Parallel Tool Call Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.openrouter
@pytest.mark.parametrize("model_name,model_id", list(MODELS.items()))
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_parallel_tool_calls_math(ensure_api_key, model_name, model_id, stream):
    """Test parallel tool calls with multiple math operations (streaming and non-streaming)."""
    core = create_core_with_tools()
    config = get_config(model_id)
    
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. When asked to perform multiple calculations, "
        "issue multiple tool calls in parallel (in the same response). "
        "Use the math tools provided."
    )
    session = core.add_message(
        session,
        "user",
        "Calculate three values using tools in parallel: "
        "(1) add 10 and 5, (2) multiply 3 and 7, (3) square 6. "
        "Return all three results."
    )
    
    mode = "streaming" if stream else "non-streaming"
    print(f"\n[{model_name}] Testing parallel tool calls ({mode})...")
    
    # Allow multiple rounds for models that don't do true parallel execution
    max_rounds = 5
    all_results: list[str] = []
    expected_results = {"15", "21", "36"}
    
    for round_num in range(max_rounds):
        responses = []
        if stream:
            for chunk in core.send_request_stream(session, config):
                if chunk["type"] == "final":
                    session = chunk["session"]
                    responses = chunk["messages"]
                    break
        else:
            session, responses = core.send_request(session, config)
        
        if not responses:
            break
        
        assistant = responses[-1]
        metadata = assistant.get("metadata", {})
        tool_calls = metadata.get("tool_calls", [])
        
        print(f"  Round {round_num + 1}: {len(tool_calls)} tool calls")
        
        if not tool_calls:
            # No more tool calls, check final answer
            content = assistant.get("content", "").lower()
            print(f"  Final answer: {content}")
            
            # Check for expected results: 15 (10+5), 21 (3*7), 36 (6^2)
            has_result = any(v in content for v in expected_results)
            if not has_result:
                # Check if any results were collected
                has_result = expected_results.issubset(set(all_results))
            
            assert has_result, (
                f"Expected calculation results in response. Got: '{content}'. "
                f"Collected results: {all_results}"
            )
            return
        
        # Execute all tools
        tool_msgs = core.execute_tool_calls(tool_calls, config)
        for tm in tool_msgs:
            result = tm.get("content", "")
            print(f"    Tool result: {result}")
            all_results.append(result.strip())
            session = core.add_message(
                session,
                role=tm.get("role", "tool"),
                content=result,
                metadata=tm.get("metadata"),
                config=config,
            )
        
        # If we've seen all expected results in tool outputs, consider the test successful
        if expected_results.issubset(set(all_results)):
            print(
                "  Collected all expected results from tools: "
                f"{sorted(set(all_results))}"
            )
            return
    
    pytest.fail(f"Test did not complete in {max_rounds} rounds; collected results: {all_results}")



@pytest.mark.integration
@pytest.mark.openrouter
@pytest.mark.parametrize("model_name,model_id", list(MODELS.items()))
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_parallel_tool_calls_file_read(ensure_api_key, temp_files, model_name, model_id, stream):
    """Test parallel tool calls with multiple file reads (streaming and non-streaming)."""
    tmp_dir, f1, f2 = temp_files
    core = create_core_with_tools()
    
    # Use working_directory for relative path resolution
    config = get_config(model_id, allowed_paths=[tmp_dir])
    config["working_directory"] = tmp_dir
    
    # Get just the filenames for relative paths
    f1_name = os.path.basename(f1)
    f2_name = os.path.basename(f2)
    
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        f"You are a helpful assistant. When asked to read multiple files, "
        f"issue multiple read_file calls in parallel (in the same response). "
        f"The working directory is: {tmp_dir}. You can use relative paths."
    )
    session = core.add_message(
        session,
        "user",
        f"Read both files in parallel: {f1_name} and {f2_name}. "
        "Then tell me the sum of the numbers they contain."
    )
    
    mode = "streaming" if stream else "non-streaming"
    print(f"\n[{model_name}] Testing parallel file reads ({mode})...")
    
    # Allow multiple rounds for models that don't do true parallel execution
    max_rounds = 5
    all_results: list[str] = []
    
    for round_num in range(max_rounds):
        responses = []
        if stream:
            for chunk in core.send_request_stream(session, config):
                if chunk["type"] == "final":
                    session = chunk["session"]
                    responses = chunk["messages"]
                    break
        else:
            session, responses = core.send_request(session, config)
        
        if not responses:
            break
        
        assistant = responses[-1]
        metadata = assistant.get("metadata", {})
        tool_calls = metadata.get("tool_calls", [])
        
        print(f"  Round {round_num + 1}: {len(tool_calls)} tool calls")
        
        if not tool_calls:
            # No more tool calls, check final answer
            content = assistant.get("content", "")
            print(f"  Final answer: {content}")
            
            # Should mention 42 and/or 17, or the sum 59
            # Also check collected results
            has_data = "42" in content or "17" in content or "59" in content
            if not has_data:
                has_data = any("42" in r or "17" in r for r in all_results)
            
            assert has_data, (
                "Expected file contents (42, 17, or 59) in response. "
                f"Got: '{content}'. Collected results: {all_results}"
            )
            return
        
        # Execute all tools
        tool_msgs = core.execute_tool_calls(tool_calls, config)
        for tm in tool_msgs:
            result = tm.get("content", "")
            print(f"    Tool result: {result}")
            all_results.append(result)
            session = core.add_message(
                session,
                role=tm.get("role", "tool"),
                content=result,
                metadata=tm.get("metadata"),
                config=config,
            )
        
        # If we've seen both expected file contents in tool outputs, consider the test successful
        has_42 = any("42" in r for r in all_results)
        has_17 = any("17" in r for r in all_results)
        if has_42 and has_17:
            print(
                "  Collected expected file contents from tools: "
                f"{all_results}"
            )
            return
    
    pytest.fail(
        f"Test did not complete in {max_rounds} rounds; collected results: {all_results}"
    )



# ============================================================================
# Tool Chain Tests (Multiple Rounds)
# ============================================================================

@pytest.mark.integration
@pytest.mark.openrouter
@pytest.mark.parametrize("model_name,model_id", list(MODELS.items()))
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_tool_chain_math_sequence(ensure_api_key, model_name, model_id, stream):
    """Test tool chain with sequential dependent calculations (streaming and non-streaming)."""
    core = create_core_with_tools()
    config = get_config(model_id)
    
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. Use the math tools to perform calculations. "
        "Break complex problems into steps using multiple tool calls."
    )
    session = core.add_message(
        session,
        "user",
        "Calculate (5 + 3) * 4 using tools. "
        "First add 5 and 3, then multiply the result by 4. "
        "Show each step."
    )
    
    mode = "streaming" if stream else "non-streaming"
    print(f"\n[{model_name}] Testing tool chain (math sequence, {mode})...")
    
    max_rounds = 5
    for round_num in range(max_rounds):
        responses = []
        if stream:
            for chunk in core.send_request_stream(session, config):
                if chunk["type"] == "final":
                    session = chunk["session"]
                    responses = chunk["messages"]
                    break
        else:
            session, responses = core.send_request(session, config)
        
        if not responses:
            break
        
        assistant = responses[-1]
        metadata = assistant.get("metadata", {})
        tool_calls = metadata.get("tool_calls", [])
        
        print(f"  Round {round_num + 1}: {len(tool_calls)} tool calls")
        
        if not tool_calls:
            # No more tools, final answer
            content = assistant.get("content", "")
            print(f"  Final answer: {content}")
            # Should mention 32 ((5+3)*4 = 8*4 = 32)
            assert "32" in content, f"Expected '32' in final answer, got: {content!r}"
            break
        
        # Execute tools
        tool_msgs = core.execute_tool_calls(tool_calls, config)
        for tm in tool_msgs:
            print(f"    Tool result: {tm.get('content', '')}")
            session = core.add_message(
                session,
                role=tm.get("role", "tool"),
                content=tm.get("content", ""),
                metadata=tm.get("metadata"),
                config=config,
            )
    else:
        pytest.fail(f"Tool chain did not complete in {max_rounds} rounds")


@pytest.mark.integration
@pytest.mark.openrouter
@pytest.mark.parametrize("model_name,model_id", list(MODELS.items()))
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_tool_chain_file_then_math(ensure_api_key, temp_files, model_name, model_id, stream):
    """Test tool chain with file read followed by math operation (streaming and non-streaming)."""
    tmp_dir, f1, f2 = temp_files
    core = create_core_with_tools()
    
    # Use working_directory for relative path resolution
    config = get_config(model_id, allowed_paths=[tmp_dir])
    config["working_directory"] = tmp_dir
    
    # Get just the filename for relative path
    f1_name = os.path.basename(f1)
    
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        f"You are a helpful assistant. Use the available tools to complete tasks. "
        f"You have access to read_file, add, multiply, and square tools. "
        f"The working directory is: {tmp_dir}. You can use relative paths for files."
    )
    session = core.add_message(
        session,
        "user",
        f"First read the number from {f1_name}, then square that number using the square tool. "
        "Report the final result."
    )
    
    mode = "streaming" if stream else "non-streaming"
    print(f"\n[{model_name}] Testing tool chain (file + math, {mode})...")
    
    max_rounds = 4
    for round_num in range(max_rounds):
        responses = []
        if stream:
            for chunk in core.send_request_stream(session, config):
                if chunk["type"] == "final":
                    session = chunk["session"]
                    responses = chunk["messages"]
                    break
        else:
            session, responses = core.send_request(session, config)
        
        if not responses:
            break
        
        assistant = responses[-1]
        metadata = assistant.get("metadata", {})
        tool_calls = metadata.get("tool_calls", [])
        
        print(f"  Round {round_num + 1}: {len(tool_calls)} tool calls")
        
        if not tool_calls:
            # Final answer
            content = assistant.get("content", "")
            print(f"  Final answer: {content}")
            # Should mention 1764 (42^2). Some models format this as
            # "1,764" with a thousands separator, so normalize commas
            # before checking.
            normalized = content.replace(",", "")
            assert "1764" in normalized, (
                f"Expected '1764' (42^2) in final answer, got: {content!r}"
            )
            break
        
        # Execute tools
        tool_msgs = core.execute_tool_calls(tool_calls, config)
        for tm in tool_msgs:
            print(f"    Tool result: {tm.get('content', '')}")
            session = core.add_message(
                session,
                role=tm.get("role", "tool"),
                content=tm.get("content", ""),
                metadata=tm.get("metadata"),
                config=config,
            )
    else:
        pytest.fail(f"Tool chain did not complete in {max_rounds} rounds")


@pytest.mark.integration
@pytest.mark.openrouter
@pytest.mark.parametrize("model_name,model_id", list(MODELS.items()))
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_tool_chain_complex_multi_step(ensure_api_key, temp_files, model_name, model_id, stream):
    """Test complex tool chain with multiple files and calculations (streaming and non-streaming)."""
    tmp_dir, f1, f2 = temp_files
    core = create_core_with_tools()
    
    # Use working_directory for relative path resolution
    config = get_config(model_id, allowed_paths=[tmp_dir])
    config["working_directory"] = tmp_dir
    
    # Get just the filenames for relative paths
    f1_name = os.path.basename(f1)
    f2_name = os.path.basename(f2)
    
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        f"You are a helpful assistant. Use tools to solve problems step by step. "
        f"The working directory is: {tmp_dir}. You can use relative paths for files."
    )
    session = core.add_message(
        session,
        "user",
        f"Read numbers from {f1_name} and {f2_name}, add them together, then square the result. "
        "Show your work step by step."
    )
    
    mode = "streaming" if stream else "non-streaming"
    print(f"\n[{model_name}] Testing complex tool chain ({mode})...")
    
    max_rounds = 10
    for round_num in range(max_rounds):
        responses = []
        if stream:
            for chunk in core.send_request_stream(session, config):
                if chunk["type"] == "final":
                    session = chunk["session"]
                    responses = chunk["messages"]
                    break
        else:
            session, responses = core.send_request(session, config)
        
        if not responses:
            break
        
        assistant = responses[-1]
        metadata = assistant.get("metadata", {})
        tool_calls = metadata.get("tool_calls", [])
        
        print(f"  Round {round_num + 1}: {len(tool_calls)} tool calls")
        
        if not tool_calls:
            # Final answer
            content = assistant.get("content", "")
            print(f"  Final answer: {content}")
            # Should mention 3481 ((42+17)^2 = 59^2)
            # Allow formatted variants like "3,481" and encoding artefacts
            normalized = content.replace(",", "").replace("Â", "")
            assert "3481" in normalized, (
                "Expected '3481' ((42+17)^2) in final answer, got: "
                f"{content}"
            )
            break
        
        # Execute tools
        tool_msgs = core.execute_tool_calls(tool_calls, config)
        for tm in tool_msgs:
            print(f"    Tool result: {tm.get('content', '')}")
            session = core.add_message(
                session,
                role=tm.get("role", "tool"),
                content=tm.get("content", ""),
                metadata=tm.get("metadata"),
                config=config,
            )
    else:
        pytest.fail(f"Tool chain did not complete in {max_rounds} rounds")
