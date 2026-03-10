"""Direct OpenRouter `/responses` API regression test for reasoning continuity.

This bypasses provider/framework code and calls the OpenRouter API directly so
we can distinguish provider-side issues from API-side behavior.

Flow (non-streaming only, GPT-5 Mini):
1. Send the reasoning_test prompt with a read_file tool.
2. Execute the returned tool call locally.
3. Send a second request with full prior history plus function_call_output.

Assertions:
- final answer contains "Clock"
- second response reasoning summary length is at most half of first response
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pytest
import requests


try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


BASE_URL = "https://openrouter.ai/api/v1"


def _get_openai_provider_options() -> Dict[str, Any]:
    provider_id = os.getenv("OPENAI_PROVIDER") or "openai"
    return {
        "provider": {
            "order": [provider_id],
            "allow_fallbacks": False,
        }
    }


def _reasoning_test_dir() -> Path:
    return Path(__file__).parent / "reasoning_test"


def _load_prompt() -> str:
    return (_reasoning_test_dir() / "prompt.txt").read_text(encoding="utf-8")


def _print_curl_repro(label: str, payload: Dict[str, Any]) -> None:
    payload_json = json.dumps(payload, ensure_ascii=True)
    print(f"\n[api-debug] {label} request curl:")
    print(
        "cat <<'JSON' | curl -sS https://openrouter.ai/api/v1/responses "
        '-H "Authorization: Bearer $OPENROUTER_API_KEY" '
        '-H "Content-Type: application/json" --data-binary @-'
    )
    print(payload_json)
    print("JSON")


def _post_responses(
    payload: Dict[str, Any], api_key: str, *, curl_label: str
) -> Dict[str, Any]:
    _print_curl_repro(curl_label, payload)
    r = requests.post(
        f"{BASE_URL}/responses",
        json=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        timeout=180,
    )
    r.encoding = "utf-8"
    if r.status_code != 200:
        try:
            err = r.json()
        except Exception:
            err = r.text
        raise RuntimeError(
            f"OpenRouter /responses failed: {r.status_code} {r.reason}. Error: {err}"
        )
    obj = r.json()
    if not isinstance(obj, dict):
        raise RuntimeError(f"OpenRouter /responses returned non-object: {obj}")
    return obj


def _extract_tool_calls(output_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        item
        for item in output_items
        if isinstance(item, dict) and item.get("type") == "function_call"
    ]


def _extract_assistant_text(output_items: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for item in output_items:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "message":
            continue
        role = item.get("role")
        if role is not None and role != "assistant":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") not in ("output_text", "text"):
                continue
            text = block.get("text")
            if isinstance(text, str) and text:
                parts.append(text)
    return "\n".join(parts).strip()


def _extract_reasoning_summary_text(output_items: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for item in output_items:
        if not isinstance(item, dict) or item.get("type") != "reasoning":
            continue
        summary = item.get("summary")
        if not isinstance(summary, list):
            continue
        for block in summary:
            if not isinstance(block, dict) or block.get("type") != "summary_text":
                continue
            text = block.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
    return "\n\n".join(parts).strip()


def _safe_read_fixture_file(path_str: str) -> str:
    if not path_str:
        raise RuntimeError("tool call path is empty")
    base = _reasoning_test_dir().resolve()
    target = (base / path_str).resolve()
    if base not in [target, *target.parents]:
        raise RuntimeError(f"tool call path escapes fixture dir: {path_str}")
    return target.read_text(encoding="utf-8")


def _build_read_file_tool_schema() -> Dict[str, Any]:
    return {
        "type": "function",
        "name": "read_file",
        "description": "Read a UTF-8 text file by relative path from the reasoning test fixture.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to a file in the reasoning_test fixture.",
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    }


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_responses_api_gpt5_mini_reasoning_regression() -> None:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    prompt = _load_prompt()
    working_directory = str(_reasoning_test_dir())

    first_input: List[Dict[str, Any]] = [
        {
            "type": "message",
            "role": "system",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        "You have access to the read_file tool. "
                        f"The working directory for file paths is: {working_directory}. "
                        "You can use relative file paths (like 'bank0.json') "
                        "which will be resolved relative to this directory."
                    ),
                }
            ],
        },
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": prompt}],
        },
    ]

    base_payload: Dict[str, Any] = {
        "model": "openai/gpt-5-mini",
        "tools": [_build_read_file_tool_schema()],
        "tool_choice": "auto",
        "reasoning": {
            "enabled": True,
            "effort": "high",
            "summary": "detailed",
        },
        "include": ["reasoning.encrypted_content"],
        "stream": False,
        **_get_openai_provider_options(),
    }

    response1 = _post_responses(
        {**base_payload, "input": first_input},
        api_key,
        curl_label="first",
    )
    output1 = [item for item in response1.get("output", []) if isinstance(item, dict)]
    assert output1, "expected first response to contain output items"

    tool_calls = _extract_tool_calls(output1)
    assert tool_calls, "expected first response to include a function_call"

    print("\n[api-debug] first response id:", response1.get("id"))
    print(
        "[api-debug] first response output types:",
        [item.get("type") for item in output1],
    )

    tool_outputs: List[Dict[str, Any]] = []
    for call in tool_calls:
        assert (
            call.get("name") == "read_file"
        ), f"unexpected tool name: {call.get('name')}"
        call_id = call.get("call_id")
        assert isinstance(call_id, str) and call_id, f"missing call_id: {call}"
        raw_args = call.get("arguments")
        assert isinstance(raw_args, str), f"expected string arguments: {call}"
        args = json.loads(raw_args)
        assert isinstance(args, dict), f"expected object arguments: {raw_args}"
        print("[api-debug] tool call arguments:", args)
        path = args.get("path")
        if not isinstance(path, str) or not path:
            path = args.get("file_path")
        assert isinstance(path, str) and path, f"expected path argument: {args}"

        file_content = _safe_read_fixture_file(path)
        tool_outputs.append(
            {
                "type": "function_call_output",
                "call_id": call_id,
                "output": file_content,
            }
        )

    second_input = [*first_input, *output1, *tool_outputs]

    assert any(
        isinstance(item, dict)
        and item.get("type") == "reasoning"
        and isinstance(item.get("summary"), list)
        and item.get("summary")
        for item in second_input
    ), "expected second request input to contain first response reasoning summary"
    assert any(
        isinstance(item, dict)
        and item.get("type") == "reasoning"
        and isinstance(item.get("encrypted_content"), str)
        and item.get("encrypted_content")
        for item in second_input
    ), "expected second request input to carry first response encrypted reasoning content"

    has_signature = any(
        isinstance(item, dict) and "signature" in item for item in output1
    )
    if has_signature:
        assert any(
            isinstance(item, dict) and "signature" in item for item in second_input
        ), "expected second request input to preserve signature fields from first response"

    response2 = _post_responses(
        {**base_payload, "input": second_input},
        api_key,
        curl_label="second",
    )
    output2 = [item for item in response2.get("output", []) if isinstance(item, dict)]
    assert output2, "expected second response to contain output items"

    final_answer = _extract_assistant_text(output2)
    print("[api-debug] second response id:", response2.get("id"))
    print("[api-debug] final answer:", final_answer)
    assert "Clock" in final_answer, f"Expected 'Clock', got: {final_answer}"

    first_reasoning = _extract_reasoning_summary_text(output1)
    second_reasoning = _extract_reasoning_summary_text(output2)
    print(
        "[api-debug] reasoning summary lengths:",
        f"first={len(first_reasoning)}, second={len(second_reasoning)}",
    )
    assert first_reasoning, "expected first response reasoning summary text"
    assert len(second_reasoning) * 2 <= len(first_reasoning), (
        "expected second response reasoning summary to be at most half of first; "
        f"got first={len(first_reasoning)}, second={len(second_reasoning)}"
    )
