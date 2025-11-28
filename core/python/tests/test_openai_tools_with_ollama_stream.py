"""
Streaming integration test for OpenAI-compatible provider with tools (single write) on Ollama.

Scenario:
- Ask the assistant to write EXACT content to a file using write_file
- Expect exactly ONE tool call (write_file)
- Feed back the tool result
- Expect a final textual response (e.g., "OK") without further tool calls
- Verify file exists and content matches exactly

Skips gracefully if Ollama/model unavailable.
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


@pytest.mark.ollama
def test_tools_flow_with_ollama_stream(ensure_model):
    from plugins.openai_provider import OpenAICompatibleProvider
    from plugins.openai_tools_extension import OpenAIToolsExtension
    from plugins.file_writer_tool import FileWriterTool

    core = AgentCore()
    core.register_provider(OpenAICompatibleProvider, extensions=[OpenAIToolsExtension])
    core.register_tool(FileWriterTool)

    tmp_dir = tempfile.mkdtemp(dir=".")
    file_path = os.path.join(tmp_dir, "stream_write.txt")
    expected_content = "STREAM-ONLY-WRITE-OK"

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
            "You are a helpful assistant. Use available tools for file operations. Do not answer without using tools when file writes are requested.",
        )
        session = core.add_message(
            session,
            "user",
            (
                f"Write exactly this content to the given path using write_file, then respond with 'OK' only.\n"
                f"path: {file_path}\n"
                f"content: {expected_content}\n"
                "Do not call any other tools."
            ),
        )
        print("\n==> Streaming request: single write_file call expected")
        print("  - system: Use tools for file write; do not answer without tools")
        print(f"  - target file: {file_path}")
        print(f"  - content: {expected_content}")

        # Step 1: stream until first final to collect tool call(s)
        final_messages = None
        for ev in core.send_request_stream(session, config):
            if ev["type"] == "partial":
                msg = ev["message"]
                print((msg.get("content", "")), end="", flush=True)
                print((msg.get("reasoning", "")), end="", flush=True)
                tool_calls = msg.get("metadata", {}).get("tool_calls", None)
                if tool_calls:
                    print("(partial) tool call:", tool_calls, end="", flush=True)
            if ev["type"] != "final":
                continue
            session = ev["session"]
            final_messages = ev["messages"]
            print("final messages:", final_messages)
        assert final_messages is not None

        # print("messages: ", final_messages)

        # Aggregate tool calls
        all_tool_calls = []
        for m in final_messages:
            md = (m.get("metadata") or {}) if isinstance(m, dict) else {}
            calls = md.get("tool_calls") or []
            all_tool_calls.extend(calls)
        print("\n<== Assistant proposed tool calls (raw):", len(all_tool_calls))
        # Deduplicate identical calls that may appear across finals
        _uniq = {}
        import json as _json

        for tc in all_tool_calls:
            fn0 = tc.get("function") or {}
            args0 = fn0.get("arguments")
            if isinstance(args0, str):
                try:
                    args0 = _json.loads(args0)
                except Exception:
                    args0 = args0
            sig = (
                fn0.get("name"),
                _json.dumps(args0, sort_keys=True) if isinstance(args0, dict) else str(args0),
            )
            _uniq[sig] = tc
        uniq_tool_calls = list(_uniq.values())
        print("<== Assistant proposed tool calls (unique):", len(uniq_tool_calls))
        assert (
            len(uniq_tool_calls) == 1
        ), f"expected exactly one tool call, got {len(uniq_tool_calls)}"

        # Validate tool call is write_file with expected args
        tc = uniq_tool_calls[0]
        fn = tc.get("function") or {}
        assert fn.get("name") == "write_file"
        args = fn.get("arguments")
        if isinstance(args, str):
            import json as _json

            try:
                args = _json.loads(args)
            except Exception:
                args = {}
        assert isinstance(args, dict)
        assert args.get("file_path") == file_path
        assert args.get("content") == expected_content

        # Execute tool call and feed back single result (no loop)
        tool_msgs = core.execute_tool_calls(uniq_tool_calls, config)
        assert tool_msgs and len(tool_msgs) == 1, "expected one tool result"
        tm = tool_msgs[0]
        print("==> Tool result:", tm.get("content", ""))
        session = core.add_message(
            session,
            role=tm.get("role", "tool"),
            content=tm.get("content", ""),
            metadata=tm.get("metadata"),
        )
        print("==> Sent tool result back to assistant")

        # Step 2: stream final answer (no further tool calls expected)
        final_messages2 = None
        for ev in core.send_request_stream(session, config):
            if ev["type"] == "partial":
                msg = ev["message"]
                print((msg.get("content", "")), end="", flush=True)
                print((msg.get("reasoning", "")), end="", flush=True)
                print((msg.get("metadata", {}).get("tool_calls", "")), end="", flush=True)
            if ev["type"] != "final":
                continue
            session = ev["session"]
            final_messages2 = ev["messages"]
        assert final_messages2 is not None

        # Ensure no further tool calls and final textual answer is OK
        all_tool_calls2 = []
        for m in final_messages2:
            md = (m.get("metadata") or {}) if isinstance(m, dict) else {}
            calls = md.get("tool_calls") or []
            all_tool_calls2.extend(calls)
        print("\n<== Assistant final tool calls:", len(all_tool_calls2))
        assert len(all_tool_calls2) == 0

        assistant = final_messages2[-1]
        text = assistant.get("content", "")
        print("<== Assistant final answer:", text)
        assert isinstance(text, str)
        assert "OK" in text or "ok" in text.lower()

        # Validate file content
        assert os.path.exists(file_path)
        contents = open(file_path, "r", encoding="utf-8").read()
        print("==> File content:", contents)
        assert contents == expected_content
    finally:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
            os.rmdir(tmp_dir)
        except Exception:
            pass
