# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

# ruff: noqa: E402

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
CORE_PY = ROOT / "core/python"
PLUGIN_SRC = ROOT / "plugins/claude-tools/src"
SHARED_SRC = ROOT / "plugins/tool-compat-shared/src"
FETCH_SRC = ROOT / "plugins/web-fetch-shared/src"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
if str(PLUGIN_SRC) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SRC))
if str(SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(SHARED_SRC))
if str(FETCH_SRC) not in sys.path:
    sys.path.insert(0, str(FETCH_SRC))

from agent_core import AgentCore
from agent_core.tool_interop import (
    DEFAULT_TOOL_INTEROP_REGISTRY,
    compose_tool_interop_registry,
)
from agent_core.tool_result_payloads import FORMAT_ANTHROPIC_MESSAGES, TOOL_RESULT_FIELD
from claude_tools import ClaudeWebFetchTool


def _wrapper(tmp_path: Path):
    tool = ClaudeWebFetchTool()
    state = tool.init({"working_directory": str(tmp_path)})
    return tool, state


def _fixture(name: str) -> dict:
    path = (
        Path(__file__).resolve().parents[1]
        / "investigation"
        / "fixtures"
        / "web-fetch"
        / f"{name}.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _execute_messages(tmp_path: Path, calls: list[dict]) -> list[dict]:
    core = AgentCore()
    core.register_tool(ClaudeWebFetchTool)
    return list(
        core.iter_tool_messages(
            calls,
            {"working_directory": str(tmp_path)},
        )
    )


def test_schema_matches_observed_fixture(tmp_path: Path) -> None:
    tool, state = _wrapper(tmp_path)
    assert (
        tool.get_tool_schemas(state)[0]
        == _fixture("success-text-file")["tool_schema"]
    )


def test_anthropic_schema_converts_to_openai_chat_schema(tmp_path: Path) -> None:
    tool, state = _wrapper(tmp_path)
    schema = tool.get_tool_schemas(state)[0]
    registry = compose_tool_interop_registry(
        contributed=[tool.get_tool_interop_contribution(state)],
        defaults=DEFAULT_TOOL_INTEROP_REGISTRY,
    )
    converted = registry.convert_schemas(
        [schema],
        target_formats=["openai.chat_completions.function.tool_schema"],
    )[0]

    assert converted["type"] == "function"
    assert converted["function"]["name"] == "WebFetch"
    assert converted["function"]["parameters"] == schema["input_schema"]


def test_success_text_result_matches_observed_shape(tmp_path: Path) -> None:
    with (
        patch(
            "claude_tools.claude_web_fetch_tool._probe_cross_host_redirect",
            return_value=(False, ""),
        ),
        patch(
            "claude_tools.claude_web_fetch_tool.fetch_url",
            return_value=SimpleNamespace(
                is_error=False,
                content="raw content",
                content_type="text/plain",
                error_message=None,
            ),
        ),
        patch(
            "claude_tools.claude_web_fetch_tool.extract_text",
            return_value="Extracted content",
        ),
        patch(
            "claude_tools.claude_web_fetch_tool.run_prompted_summary_request",
            return_value=(
                True,
                "RFC 2606 reserves four top-level DNS names—`.test`, `.example`, `.invalid`, and `.localhost`—for testing, documentation examples, invalid name construction, and localhost loopback use, respectively.",
            ),
        ),
    ):
        messages = _execute_messages(
            tmp_path,
            [
                {
                    "id": "call_web_fetch_1",
                    "type": "function",
                    "function": {
                        "name": "WebFetch",
                        "arguments": json.dumps(
                            {
                                "url": "https://www.rfc-editor.org/rfc/rfc2606.txt",
                                "prompt": "return a one-line summary only",
                            }
                        ),
                    },
                }
            ],
        )

    expected = _fixture("success-text-file")["tool_result_message"]["content"][0]
    assert messages[0]["content"] == expected["content"]
    assert messages[0][TOOL_RESULT_FIELD]["format"] == FORMAT_ANTHROPIC_MESSAGES


def test_redirect_message_matches_fixture(tmp_path: Path) -> None:
    redirect_text = _fixture("success-redirect-different-host")["tool_result_message"][
        "content"
    ][0]["content"]
    with patch(
        "claude_tools.claude_web_fetch_tool._probe_cross_host_redirect",
        return_value=(True, redirect_text),
    ):
        messages = _execute_messages(
            tmp_path,
            [
                {
                    "id": "call_web_fetch_1",
                    "type": "function",
                    "function": {
                        "name": "WebFetch",
                        "arguments": json.dumps(
                            {
                                "url": "https://www.iana.org/domains/example",
                                "prompt": "return a one-line summary only",
                            }
                        ),
                    },
                }
            ],
        )

    assert messages[0]["content"] == redirect_text


def test_invalid_private_url_matches_fixture(tmp_path: Path) -> None:
    messages = _execute_messages(
        tmp_path,
        [
            {
                "id": "call_web_fetch_1",
                "type": "function",
                "function": {
                    "name": "WebFetch",
                    "arguments": json.dumps(
                        {
                            "url": "http://localhost:3000",
                            "prompt": "return the page title only",
                        }
                    ),
                },
            }
        ],
    )

    expected = _fixture("error-invalid-private-url")["tool_result_message"]["content"][0]
    assert messages[0]["content"] == expected["content"]
    assert messages[0][TOOL_RESULT_FIELD]["content"][0]["is_error"] is True


def test_timeout_matches_fixture(tmp_path: Path) -> None:
    with (
        patch(
            "claude_tools.claude_web_fetch_tool._probe_cross_host_redirect",
            return_value=(False, ""),
        ),
        patch(
            "claude_tools.claude_web_fetch_tool.fetch_url",
            return_value=SimpleNamespace(
                is_error=True,
                content="",
                content_type="",
                error_message="Request timed out after 60.0 seconds",
            ),
        ),
    ):
        messages = _execute_messages(
            tmp_path,
            [
                {
                    "id": "call_web_fetch_1",
                    "type": "function",
                    "function": {
                        "name": "WebFetch",
                        "arguments": json.dumps(
                            {
                                "url": "https://example.org",
                                "prompt": "return a one-line summary only",
                            }
                        ),
                    },
                }
            ],
        )

    expected = _fixture("error-timeout")["tool_result_message"]["content"][0]
    assert messages[0]["content"] == expected["content"]
    assert messages[0][TOOL_RESULT_FIELD]["content"][0]["is_error"] is True