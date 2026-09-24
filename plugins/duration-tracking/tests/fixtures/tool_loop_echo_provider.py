"""Tool-loop echo provider for integration tests.

Extends the core echo provider with the one behavior the plain echo
lacks: its first response carries a ``read_file`` tool call, so the
production tool loop runs a genuine multi-round request (LLM round one
emits the call, the tool executes, LLM round two answers). Once a tool
result appears in the conversation the provider echoes like the base
class. Round detection uses the conversation shape (a ``tool`` message in
history), not provider state, so it is robust to per-round state
re-initialization.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from plugins.echo_openai_like_provider import EchoOpenAILikeProvider


class ToolLoopEchoProvider(EchoOpenAILikeProvider):
    """Echo provider whose first response requests one tool call."""

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        if any(
            isinstance(item, dict) and item.get("role") == "tool"
            for item in native_messages
        ):
            return super().call_api(native_messages, state)

        config = state.get("config") or {}
        working_directory = config.get("working_directory") or "."
        target = Path(working_directory) / "hello.txt"
        call = {
            "id": "call_loop_1",
            "type": "function",
            "function": {
                "name": "read_file",
                "arguments": json.dumps({"file_path": str(target)}),
            },
        }
        final = {
            "role": "assistant",
            "content": "",
            "_metadata": {"tool_calls": [call]},
        }
        return [], [final], [*native_messages, final], state
