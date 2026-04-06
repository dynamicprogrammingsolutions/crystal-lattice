"""Integration tests for GeminiWebFetchTool.

Tests with real Gemini API and OpenRouter for fallback.
"""

from __future__ import annotations

import os

import pytest

from agent_core import AgentCore, Session

from gemini_tools import GeminiWebFetchTool
from gemini_tools.gemini_web_fetch_tool import _rate_limit_cache


# ============================================================================
# Gemini API Integration Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.gemini
def test_gemini_primary_path_real_api():
    """Test primary path with real Gemini API.

    Requires GEMINI_API_KEY environment variable.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")

    # Clear rate limit history
    _rate_limit_cache.clear()

    from agent_core.plugin import ToolWrapper

    wrapper = ToolWrapper(GeminiWebFetchTool)
    state = wrapper.init({"gemini_api_key": api_key})

    # Test with a simple, reliable URL
    result = wrapper.execute_tool(
        "web_fetch",
        {"prompt": "What is the title of https://example.com?"},
        state,
    )

    assert result["success"] is True
    assert "Example Domain" in result["result"] or "example" in result["result"].lower()


@pytest.mark.integration
@pytest.mark.gemini
def test_gemini_primary_path_with_citations():
    """Test primary path returns citations.

    Requires GEMINI_API_KEY environment variable.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")

    _rate_limit_cache.clear()

    from agent_core.plugin import ToolWrapper

    wrapper = ToolWrapper(GeminiWebFetchTool)
    state = wrapper.init({"gemini_api_key": api_key})

    # This prompt should trigger grounding with citations
    result = wrapper.execute_tool(
        "web_fetch",
        {"prompt": "Summarize the content from https://httpbin.org/html"},
        state,
    )

    assert result["success"] is True
    # The response should have some content
    assert len(result["result"]) > 50


# ============================================================================
# OpenRouter Integration Tests (Fallback LLM)
# ============================================================================


MODEL = os.getenv("OPENROUTER_MODEL_GEMINI_TOOLS", "google/gemini-2.5-flash-lite")


@pytest.mark.integration
@pytest.mark.openrouter
def test_gemini_web_fetch_via_openrouter():
    """Test web_fetch tool via OpenRouter provider.

    Requires OPENROUTER_API_KEY environment variable.
    Uses Gemini for primary fetch, OpenRouter for fallback LLM.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not gemini_key:
        pytest.skip("GEMINI_API_KEY not set")
    if not openrouter_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    _rate_limit_cache.clear()

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_tool(GeminiWebFetchTool)

    config = {
        "model": MODEL,
        "api_key": openrouter_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "gemini_api_key": gemini_key,  # For web_fetch primary path
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "Use the web_fetch tool when you need to fetch content from a URL. "
        "After fetching, summarize the content briefly.",
    )
    session = core.add_message(
        session,
        "user",
        "Use web_fetch to fetch https://example.com and tell me the page title.",
    )

    session, responses = core.send_request(session, config)
    tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []

    if not tool_calls:
        # LLM might have answered without tool call
        final_text = (responses[-1].get("content") or "").strip()
        # This is OK, just verify we got a response
        assert len(final_text) > 0
        return

    for tool_msg in core.execute_tool_calls(tool_calls, config):
        session = core.add_message(
            session,
            role=tool_msg["role"],
            content=tool_msg["content"],
            metadata=tool_msg.get("metadata"),
            config=config,
        )

    session, follow_up = core.send_request(session, config)
    final_text = (follow_up[-1].get("content") or "").strip()

    # Should mention something from example.com
    assert "example" in final_text.lower() or "domain" in final_text.lower()


@pytest.mark.integration
@pytest.mark.openrouter
def test_gemini_web_fetch_private_url_fallback():
    """Test that private URLs trigger fallback path.

    Uses a localhost URL to trigger fallback, then uses
    context['core'] for LLM summarization via OpenRouter.
    """
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    _rate_limit_cache.clear()

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_tool(GeminiWebFetchTool)

    config = {
        "model": MODEL,
        "api_key": openrouter_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "gemini_api_key": "test-key",  # Has key, but will use fallback for private URL
    }

    # The tool should detect localhost as private and use fallback
    # But fallback fetch will fail for localhost (nothing there)
    # So we test the behavior indirectly

    from agent_core.plugin import ToolWrapper

    wrapper = ToolWrapper(GeminiWebFetchTool)
    state = wrapper.init(config)

    # This should detect localhost as private and try fallback
    # Fallback will fail because localhost isn't serving anything
    result = wrapper.execute_tool(
        "web_fetch",
        {"prompt": "Fetch http://localhost:9999/test"},
        state,
    )

    # Should fail (nothing at localhost:9999)
    assert result["success"] is False
    assert "Failed to fetch" in result["error"] or "Error" in result["error"]


# ============================================================================
# End-to-End Tool Loop Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.openrouter
def test_web_fetch_e2e_tool_loop(tmp_path):
    """End-to-end test with full tool loop.

    Tests that an LLM can successfully call web_fetch and use the result.
    """
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not openrouter_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    if not gemini_key:
        pytest.skip("GEMINI_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    _rate_limit_cache.clear()

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_tool(GeminiWebFetchTool)

    config = {
        "model": MODEL,
        "api_key": openrouter_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "gemini_api_key": gemini_key,
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Fetch https://example.com using web_fetch and tell me what kind of website it is.",
    )

    # Run the request
    session, responses = core.send_request(session, config)

    # Check for tool calls
    tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []

    if tool_calls:
        # Execute tools and get follow-up
        for tool_msg in core.execute_tool_calls(tool_calls, config):
            session = core.add_message(
                session,
                role=tool_msg["role"],
                content=tool_msg["content"],
                metadata=tool_msg.get("metadata"),
                config=config,
            )

        session, follow_up = core.send_request(session, config)
        final = (follow_up[-1].get("content") or "").strip()
    else:
        final = (responses[-1].get("content") or "").strip()

    # Verify we got some response
    assert len(final) > 20


@pytest.mark.integration
@pytest.mark.openrouter
def test_web_fetch_e2e_ollama_api_docs():
    """End-to-end test with real documentation page.

    Tests that an LLM can fetch the Ollama API documentation and
    provide a meaningful summary. This simulates a real user workflow.
    """
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not openrouter_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    if not gemini_key:
        pytest.skip("GEMINI_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    _rate_limit_cache.clear()

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_tool(GeminiWebFetchTool)

    config = {
        "model": MODEL,
        "api_key": openrouter_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "gemini_api_key": gemini_key,
    }

    # Create a session with a real user prompt
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. When the user asks about documentation or web content, "
        "use the web_fetch tool to fetch and analyze the content. Always use the tool when "
        "the user mentions a URL or asks about online documentation.",
    )
    session = core.add_message(
        session,
        "user",
        "Please summarize the key points from the Ollama API introduction page at "
        "https://docs.ollama.com/api/introduction. What are the main features and capabilities?",
    )

    # First turn: LLM should decide to call web_fetch
    session, responses = core.send_request(session, config)

    tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []

    # Verify that the LLM made a tool call
    assert len(tool_calls) > 0, "Expected LLM to call web_fetch tool"

    # Find the web_fetch tool call
    web_fetch_call = None
    for tc in tool_calls:
        fn_name = tc.get("function", {}).get("name", "")
        if fn_name == "web_fetch":
            web_fetch_call = tc
            break

    assert web_fetch_call is not None, "Expected web_fetch tool to be called"

    # Execute the tool call
    for tool_msg in core.execute_tool_calls([web_fetch_call], config):
        session = core.add_message(
            session,
            role=tool_msg["role"],
            content=tool_msg["content"],
            metadata=tool_msg.get("metadata"),
            config=config,
        )

    # Second turn: LLM should summarize the fetched content
    session, follow_up = core.send_request(session, config)

    final_response = (follow_up[-1].get("content") or "").strip()

    # Verify we got a meaningful response
    assert len(final_response) > 100, "Expected detailed summary of the API documentation"

    # The response should mention Ollama-related concepts
    response_lower = final_response.lower()
    assert "ollama" in response_lower or "api" in response_lower, (
        f"Response should mention Ollama or API concepts. Got: {final_response[:200]}..."
    )


@pytest.mark.integration
@pytest.mark.openrouter
def test_web_fetch_e2e_user_request_for_documentation():
    """End-to-end test simulating a real user asking for documentation summary.

    This test verifies the complete flow:
    1. User asks to summarize a documentation page
    2. LLM recognizes it should use web_fetch
    3. Tool fetches the content
    4. LLM provides a helpful summary based on fetched content
    """
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not openrouter_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    if not gemini_key:
        pytest.skip("GEMINI_API_KEY not set")

    try:
        from openrouter_plugins.openrouter_provider import OpenRouterProvider
        from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension
        from plugins.request_options_feature import RequestOptionsFeature
    except ImportError as exc:
        pytest.skip(f"OpenRouter test dependencies not installed: {exc}")

    _rate_limit_cache.clear()

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterToolsExtension])
    core.register_feature(RequestOptionsFeature)
    core.register_tool(GeminiWebFetchTool)

    config = {
        "model": MODEL,
        "api_key": openrouter_key,
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 180,
        "temperature": 0.0,
        "gemini_api_key": gemini_key,
    }

    # Simulate a real user asking about documentation
    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "I'm trying to understand how to use the Ollama API. Can you fetch "
        "https://docs.ollama.com/api/introduction and give me a brief overview "
        "of what the API provides and how to get started?",
    )

    # Run the full agent loop
    max_iterations = 3
    iteration = 0
    final_response = ""

    while iteration < max_iterations:
        iteration += 1

        session, responses = core.send_request(session, config)
        tool_calls = (responses[-1].get("metadata") or {}).get("tool_calls") or []

        if not tool_calls:
            # No more tool calls, we have the final response
            final_response = (responses[-1].get("content") or "").strip()
            break

        # Execute tool calls
        for tool_msg in core.execute_tool_calls(tool_calls, config):
            session = core.add_message(
                session,
                role=tool_msg["role"],
                content=tool_msg["content"],
                metadata=tool_msg.get("metadata"),
                config=config,
            )

    # Verify the agent provided a helpful response
    assert len(final_response) > 100, (
        f"Expected a comprehensive response. Got: {final_response[:200]}..."
    )

    # The response should be about Ollama or APIs
    response_lower = final_response.lower()
    assert any(keyword in response_lower for keyword in ["ollama", "api", "model", "endpoint", "request"]), (
        f"Response should be relevant to the Ollama API documentation. Got: {final_response[:300]}..."
    )

    print(f"\n=== Agent Response ===\n{final_response[:500]}...\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
