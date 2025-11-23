"""
Streaming integration test for OpenAI-compatible provider with tools (writer + reader) on Ollama.

Scenario:
- Generate a 4-stanza poem
- Call write_file with the poem
- Call read_file to verify content
- Finally reply "OK" if matches, else "MISMATCH"

Skips gracefully if Ollama/model unavailable.
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
        pytest.skip("ollama is not installed; skipping streaming tools test")
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
def test_tools_flow_with_ollama_stream(ensure_model):
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
    FileWriterTool = __import__(
        "plugins.tools.python.file_writer_tool", fromlist=["FileWriterTool"]
    ).FileWriterTool

    core = AgentCore()
    core.register_provider(OpenAICompatibleProvider, extensions=[OpenAIToolsExtension])
    core.register_tool(FileWriterTool)
    core.register_tool(FileReaderTool)

    tmp_dir = tempfile.mkdtemp(dir=".")
    poem_path = os.path.join(tmp_dir, "poem.txt")

    try:
        config = {
            "model": MODEL_TOOLS,
            "base_url": OPENAI_BASE_URL,
            "timeout": 180,
            "allowed_paths": ["."],
            "max_file_size": 5 * 1024 * 1024,
        }

        session = core.create_session()
        session = core.add_message(
            session,
            "system",
            "You are a helpful assistant. When asked to manipulate files, always use the available tools. Do not answer without using the tools.",
        )
        session = core.add_message(
            session,
            "user",
            (
                "Write long poem.\n"
                f"Then: 1) call write_file with file_path='{poem_path}' and content set to exactly the poem you generated, "
                "2) call read_file on the same file to verify the content, and "
                "3) finally respond with 'OK' only if the read content matches exactly what you wrote, otherwise respond 'MISMATCH'."
            ),
        )

        # Iterate until no more tool calls, expecting final textual verdict
        for _ in range(3):
            final_messages = None
            for ev in core.send_request_stream(session, config):
                if ev["type"] != "final":
                    continue
                session = ev["session"]
                final_messages = ev["messages"]
            assert final_messages is not None

            #print(f"Final messages: {final_messages}")

            # Aggregate tool calls across all assistant finals
            all_tool_calls = []
            for m in final_messages:
                md = (m.get("metadata") or {}) if isinstance(m, dict) else {}
                calls = md.get("tool_calls") or []
                all_tool_calls.extend(calls)

            if all_tool_calls:
                # Execute and feed back results
                tool_msgs = core.execute_tool_calls(all_tool_calls, config)
                assert tool_msgs, "expected tool results"
                for tm in tool_msgs:
                    session = core.add_message(
                        session,
                        role=tm.get("role", "tool"),
                        content=tm.get("content", ""),
                        metadata=tm.get("metadata"),
                    )
                # Loop to next turn for further tool calls or final verdict
                continue

            # No tool calls -> expect final verdict
            #print("\n\nsession:", session)
            
            assistant = final_messages[-1]
            text = assistant.get("content", "")
            assert isinstance(text, str)
            assert "OK" in text or "MISMATCH" in text
            # For success path, ensure file exists and has content
            if "OK" in text:
                assert os.path.exists(poem_path)
                contents = open(poem_path, "r", encoding="utf-8").read()
                assert isinstance(contents, str) and len(contents) > 5

            break
        else:
            pytest.fail("Did not converge to a final OK/MISMATCH response within 3 turns")
    finally:
        try:
            if os.path.exists(poem_path):
                os.unlink(poem_path)
            os.rmdir(tmp_dir)
        except Exception:
            pass
