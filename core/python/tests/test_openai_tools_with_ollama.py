"""
Integration test for OpenAI-compatible provider with tool-calling (FileReaderTool) on Ollama.

Asserts:
- First assistant response contains a tool call
- core.execute_tool_calls executes the tool and returns a tool message
- After feeding tool result back, assistant answers correctly (mentions file content)
"""

import os
import sys
import shutil
import subprocess
import tempfile
from typing import Optional

import pytest

# Ensure repo root and core/python are importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
CORE_PY = os.path.join(ROOT, "core/python")
if CORE_PY not in sys.path:
    sys.path.insert(0, CORE_PY)

from agent_core import AgentCore


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_BASE_URL = f"{OLLAMA_HOST}/v1"
MODEL_TOOLS = os.getenv("OLLAMA_MODEL_TOOLS", "qwen3:0.6b")


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout
    )


@pytest.fixture(scope="module")
def ensure_model():
    if _which("ollama") is None:
        pytest.skip("ollama is not installed; skipping tools integration test")
    try:
        _run(["ollama", "ps"], timeout=30)
    except Exception:
        pytest.skip("ollama command unavailable or not responding; skipping")
    try:
        cp = _run(["ollama", "pull", MODEL_TOOLS], timeout=1200)
        if cp.returncode != 0:
            msg = cp.stderr.decode("utf-8", errors="ignore")
            pytest.skip(f"failed to pull model {MODEL_TOOLS}: {msg}")
    except Exception as e:
        pytest.skip(f"could not pull model {MODEL_TOOLS}: {e}")


@pytest.mark.integration
def test_tools_flow_with_ollama(ensure_model):
    # Imports after sys.path adjustments
    OpenAICompatibleProvider = __import__(
        "plugins.providers.openai.python.openai_provider", fromlist=["OpenAICompatibleProvider"]
    ).OpenAICompatibleProvider
    OpenAIToolsExtension = __import__(
        "plugins.providers.openai.python.openai_tools_extension",
        fromlist=["OpenAIToolsExtension"],
    ).OpenAIToolsExtension
    FileReaderTool = __import__(
        "plugins.tools.python.file_reader_tool", fromlist=["FileReaderTool"]
    ).FileReaderTool

    # Setup
    core = AgentCore()
    core.register_provider(OpenAICompatibleProvider, extensions=[OpenAIToolsExtension])
    core.register_tool(FileReaderTool)

    with tempfile.NamedTemporaryFile("w+", delete=False, dir=".") as tf:
        tf.write("hello from tools")
        tf.flush()
        file_path = tf.name

    try:
        config = {
            "model": MODEL_TOOLS,
            "base_url": OPENAI_BASE_URL,
            "timeout": 180,
            # Tool config (consumed by tool init)
            "allowed_paths": ["."],
            "max_file_size": 1024 * 1024,
        }

        session = core.create_session()
        session = core.add_message(
            session,
            "system",
            "You are a helpful assistant. Always use the read_file tool when asked about file contents; do not answer without using the tool.",
        )
        session = core.add_message(
            session,
            "user",
            f"Use the tool to read this file and tell me its content exactly: {file_path}",
        )

        # Round 1: expect tool call
        new_session, responses = core.send_request(session, config)
        session = new_session
        assert responses, "expected assistant response"
        assistant = responses[-1]
        print("\n\nresponses:",responses)
        print("\n\nnew session:",new_session)
        md = assistant.get("metadata") or {}
        tool_calls = md.get("tool_calls") or []
        call = tool_calls[0]
        fn = call.get("function") or {}
        assert fn.get("name") == "read_file"
        args = fn.get("arguments")
        if isinstance(args, str):
            import json as _json
            try:
                args = _json.loads(args)
            except Exception:
                args = {}
        assert "file_path" in (args or {})

        # Execute tool calls
        tool_msgs = core.execute_tool_calls(tool_calls, config)
        assert tool_msgs, "expected tool results"
        # Feed back tool results
        for tm in tool_msgs:
            session = core.add_message(
                session,
                role=tm.get("role", "tool"),
                content=tm.get("content", ""),
                metadata=tm.get("metadata"),
            )

        print("\n\nsession after tool results:",session)

        # Round 2: expect final answer referencing file content
        new_session, responses = core.send_request(session, config)
        session = new_session
        
        print(f"\n\nsession after final answer: {session}")
        
        assert responses, "expected a follow-up assistant response"
        final = responses[-1]
        text = final.get("content", "")
        assert isinstance(text, str)
        assert "hello from tools" in text or "File contents:" in text
    finally:
        try:
            os.unlink(file_path)
        except Exception:
            pass
