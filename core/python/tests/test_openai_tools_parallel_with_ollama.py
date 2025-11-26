"""
Integration test for parallel tool calls (multiple read_file invocations in a single assistant turn).

Asserts:
- Assistant proposes multiple tool calls in one response
- core.execute_tool_calls executes both and results are fed back (no loops)
- Assistant final response mentions both file contents
"""

import os
import shutil
import subprocess
import tempfile
from typing import Optional

import pytest

from agent_core import AgentCore


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_BASE_URL = f"{OLLAMA_HOST}/v1"
MODEL_TOOLS = os.getenv("OLLAMA_MODEL_TOOLS", "qwen3:0.6b")


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


@pytest.fixture(scope="module")
def ensure_model():
    if _which("ollama") is None:
        pytest.skip("ollama is not installed; skipping parallel tools test")
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
def test_parallel_tools_read_multiple_files(ensure_model):
    from plugins.openai_provider import OpenAICompatibleProvider
    from plugins.openai_tools_extension import OpenAIToolsExtension
    from plugins.file_reader_tool import FileReaderTool

    core = AgentCore()
    core.register_provider(OpenAICompatibleProvider, extensions=[OpenAIToolsExtension])
    core.register_tool(FileReaderTool)

    # Prepare two files
    tmp_dir = tempfile.mkdtemp(dir=".")
    f1 = os.path.join(tmp_dir, "a.txt")
    f2 = os.path.join(tmp_dir, "b.txt")
    open(f1, "w", encoding="utf-8").write("ALPHA-CONTENT")
    open(f2, "w", encoding="utf-8").write("BETA-CONTENT")

    try:
        config = {
            "model": MODEL_TOOLS,
            "base_url": OPENAI_BASE_URL,
            "timeout": 180,
            "allowed_paths": ["."],
            "max_file_size": 1024 * 1024,
        }

        session = core.create_session()
        session = core.add_message(
            session,
            "system",
            (
                "You are a helpful assistant. When the user asks about multiple files, "
                "issue multiple read_file tool calls in the same response (parallel calls). "
                "Do not answer without using the tools."
            ),
        )
        session = core.add_message(
            session,
            "user",
            (
                f"Read BOTH files exactly and then reply in the format "
                f"A: <content of {f1}> | B: <content of {f2}>. Use read_file twice in a single turn."
            ),
        )
        print("\n==> Sending messages (parallel read request)")
        print("  - system: Use parallel read_file calls when multiple files")
        print(f"  - user: Read both: {f1} and {f2}")

        # Round 1: expect multiple tool calls
        new_session, responses = core.send_request(session, config)
        session = new_session
        assert responses, "expected assistant response"
        assistant = responses[-1]
        md = assistant.get("metadata") or {}
        tool_calls = md.get("tool_calls") or []
        print("\n<== Assistant proposed tool calls (expect >= 2)")
        print("  count:", len(tool_calls))
        assert len(tool_calls) >= 2, f"expected at least two tool calls, got {len(tool_calls)}"

        # Execute both tool calls (no loop, index explicitly)
        tool_msgs = core.execute_tool_calls(tool_calls, config)
        assert tool_msgs and len(tool_msgs) >= 2, "expected two tool results"
        tm0 = tool_msgs[0]
        tm1 = tool_msgs[1]
        print("\n==> Tool result #0:", tm0.get("content", ""))
        print("==> Tool result #1:", tm1.get("content", ""))
        session = core.add_message(
            session,
            role=tm0.get("role", "tool"),
            content=tm0.get("content", ""),
            metadata=tm0.get("metadata"),
        )
        session = core.add_message(
            session,
            role=tm1.get("role", "tool"),
            content=tm1.get("content", ""),
            metadata=tm1.get("metadata"),
        )
        print("\n==> Sent both tool results back to assistant")

        # Round 2: expect a single textual response mentioning both contents
        new_session, responses = core.send_request(session, config)
        session = new_session
        assert responses, "expected a follow-up assistant response"
        final = responses[-1]
        text = final.get("content", "")
        print("\n<== Assistant final answer:", text)
        assert isinstance(text, str)
        assert "ALPHA-CONTENT" in text and "BETA-CONTENT" in text
    finally:
        try:
            if os.path.exists(f1):
                os.unlink(f1)
            if os.path.exists(f2):
                os.unlink(f2)
            os.rmdir(tmp_dir)
        except Exception:
            pass
