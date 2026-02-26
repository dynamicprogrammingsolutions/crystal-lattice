"""
Integration tests for OpenRouter tools + reasoning with the reasoning_test scenario.

Tests that tool calling and reasoning work together correctly, specifically that
reasoning_details are preserved across tool calls and tool results.

Expected answer: "Clock" (id 7 from bank0.json) when reasoning is preserved correctly.

Models tested:
- OpenAI GPT-5 Mini
- Claude Haiku 4.5
- Gemini 3 Pro Preview
- Grok 4 Fast
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import pytest

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from agent_core import AgentCore
from openrouter_plugins.openrouter_provider import OpenRouterProvider
from openrouter_plugins.openrouter_reasoning_extension import OpenRouterReasoningExtension
from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
from plugins.file_reader_tool import FileReaderTool
from plugins.request_options_feature import RequestOptionsFeature


def _get_openai_provider_options() -> Dict[str, Any]:
    """Build provider routing block based on OPENAI_PROVIDER.

    OPENAI_PROVIDER can be set to "openai" or "azure"; defaults to "openai".
    """
    provider_id = os.getenv("OPENAI_PROVIDER") or "openai"
    return {
        "provider": {
            "order": [provider_id],
            "allow_fallbacks": False,
        }
    }


def get_reasoning_test_prompt() -> str:
    """Load the reasoning test prompt."""
    test_dir = Path(__file__).parent / "reasoning_test"
    prompt_path = test_dir / "prompt.txt"
    with open(prompt_path, "r") as f:
        return f.read()


def run_reasoning_test(
    model: str,
    stream: bool = False,
    max_iterations: int = 5,
) -> tuple[Any, list[Dict[str, Any]]]:
    """Run the reasoning test with a given model.
    
    Returns (final_session, final_responses).
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    # Set up the reasoning test directory as allowed path for file reading
    test_dir = Path(__file__).parent / "reasoning_test"
    allowed_paths = [str(test_dir)]
    working_directory = str(test_dir)

    # Create core with plugins
    core = AgentCore()
    
    # Register plugins
    core.register_provider(
        OpenRouterProvider, 
        extensions=[OpenRouterReasoningExtension, OpenRouterToolsExtension]
    )
    core.register_feature(RequestOptionsFeature)
    core.register_tool(FileReaderTool)

    # Create session
    config: Dict[str, Any] = {
        "model": model,
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,  # Increased timeout
        "enable_reasoning": True,
        "reasoning_effort": "high",
        "allowed_paths": allowed_paths,
        "working_directory": working_directory,
        "max_file_size": 1024 * 1024,
    }

    # For OpenAI models, lock routing using OPENAI_PROVIDER (openai/azure)
    if model.startswith("openai/"):
        config["request_options"] = _get_openai_provider_options()

    # Send the reasoning test prompt with system message about working directory
    prompt = get_reasoning_test_prompt()
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        f"You have access to the read_file tool. The working directory for file paths is: {working_directory}. "
        "You can use relative file paths (like 'bank0.json') which will be resolved relative to this directory."
    )
    session = core.add_message(session, "user", prompt)

    # Execute tool calls iteratively
    final_responses = []
    for i in range(max_iterations):
        if stream:
            # Streaming mode
            for chunk in core.send_request_stream(session, config):
                if chunk["type"] == "final":
                    session = chunk["session"]
                    final_responses = chunk["messages"]
                    break
        else:
            # Non-streaming mode
            session, final_responses = core.send_request(session, config)
        
        if not final_responses:
            break
        
        last_msg = final_responses[-1]
        if last_msg.get("role") != "assistant":
            break
        
        metadata = last_msg.get("metadata", {})
        tool_calls = metadata.get("tool_calls", [])
        
        if not tool_calls:
            # No more tool calls, we're done
            break
        
        # Execute all tool calls (working_directory handles relative paths automatically)
        tool_msgs = core.execute_tool_calls(tool_calls, config)
        for tm in tool_msgs:
            session = core.add_message(
                session,
                role=tm.get("role", "tool"),
                content=tm.get("content", ""),
                metadata=tm.get("metadata"),
                config=config,
            )
    
    return session, final_responses


@pytest.mark.integration
@pytest.mark.openrouter
@pytest.mark.parametrize("stream", [False, True])
def test_reasoning_test_gpt5_mini(stream):
    """Test reasoning retention with OpenAI GPT-5 Mini."""
    session, responses = run_reasoning_test("openai/gpt-5-mini", stream=stream)
    
    # Check that we got responses
    assert len(responses) > 0
    
    # Find the final assistant message
    final_msg = None
    for msg in reversed(responses):
        if msg.get("role") == "assistant" and msg.get("content"):
            final_msg = msg
            break
    
    assert final_msg is not None, "No final assistant message found"
    
    # The content should be "Clock" (or contain it) if reasoning was preserved
    content = final_msg.get("content", "").strip()
    print(f"\nGPT-5 Mini answer: {content}")
    assert f"Clock" in content, f"Expected 'Clock', got: {content}"
    
    # Check that reasoning_details were captured
    metadata = final_msg.get("metadata", {})
    reasoning = metadata.get("reasoning", "")
    if reasoning:
        print(f"Reasoning captured: {reasoning[:200]}...")


@pytest.mark.integration
@pytest.mark.openrouter
@pytest.mark.parametrize("stream", [False, True])
def test_reasoning_test_claude_haiku_45(stream):
    """Test reasoning retention with Claude Haiku 4.5."""
    session, responses = run_reasoning_test("anthropic/claude-haiku-4.5", stream=stream)
    
    assert len(responses) > 0
    
    final_msg = None
    for msg in reversed(responses):
        if msg.get("role") == "assistant" and msg.get("content"):
            final_msg = msg
            break
    
    assert final_msg is not None, "No final assistant message found"
    content = final_msg.get("content", "").strip()
    print(f"\nClaude Haiku 4.5 answer: {content}")
    assert "Clock" in content, f"Expected 'Clock', got: {content}"


@pytest.mark.integration
@pytest.mark.openrouter
@pytest.mark.parametrize("stream", [False, True])
def test_reasoning_test_gemini_3_pro_preview(stream):
    """Test reasoning retention with Gemini 3 Pro Preview."""
    session, responses = run_reasoning_test("google/gemini-3-pro-preview", stream=stream)
    
    assert len(responses) > 0
    
    final_msg = None
    for msg in reversed(responses):
        if msg.get("role") == "assistant" and msg.get("content"):
            final_msg = msg
            break
    
    assert final_msg is not None, "No final assistant message found"
    content = final_msg.get("content", "").strip()
    print(f"\nGemini 3 Pro Preview answer: {content}")
    assert "Clock" in content, f"Expected 'Clock', got: {content}"


@pytest.mark.integration
@pytest.mark.openrouter
@pytest.mark.parametrize("stream", [False, True])
def test_reasoning_test_grok_4_fast(stream):
    """Test reasoning retention with Grok 4 Fast."""
    session, responses = run_reasoning_test("x-ai/grok-4-fast", stream=stream)
    
    assert len(responses) > 0
    
    final_msg = None
    for msg in reversed(responses):
        if msg.get("role") == "assistant" and msg.get("content"):
            final_msg = msg
            break
    
    assert final_msg is not None, "No final assistant message found"
    content = final_msg.get("content", "").strip()
    print(f"\nGrok 4 Fast answer: {content}")
    assert "Clock" in content, f"Expected 'Clock', got: {content}"
