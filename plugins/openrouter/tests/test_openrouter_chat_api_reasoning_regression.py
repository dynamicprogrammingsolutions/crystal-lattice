"""Direct OpenRouter `/chat/completions` regression test for reasoning continuity.

This bypasses provider/framework code and calls OpenRouter's chat-completions
endpoint directly so we can separate API behavior from provider behavior.

Flow (non-streaming only, GPT-5 Mini):
1. Send the reasoning_test prompt with a read_file tool.
2. Execute the returned tool call locally.
3. Send a second request with full prior history plus tool result message.

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
pytestmark = pytest.mark.api


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


def _build_read_file_tool_schema() -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
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
        },
    }


def _print_curl_repro(label: str, payload: Dict[str, Any]) -> None:
    payload_json = json.dumps(payload, ensure_ascii=True)
    print(f"\n[api-debug] {label} request curl:")
    print(
        "cat <<'JSON' | curl -sS https://openrouter.ai/api/v1/chat/completions "
        '-H "Authorization: Bearer $OPENROUTER_API_KEY" '
        '-H "Content-Type: application/json" --data-binary @-'
    )
    print(payload_json)
    print("JSON")


def _post_chat_completions(
    payload: Dict[str, Any], api_key: str, *, curl_label: str
) -> Dict[str, Any]:
    _print_curl_repro(curl_label, payload)
    r = requests.post(
        f"{BASE_URL}/chat/completions",
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
            f"OpenRouter /chat/completions failed: {r.status_code} {r.reason}. Error: {err}"
        )
    obj = r.json()
    if not isinstance(obj, dict):
        raise RuntimeError(f"OpenRouter /chat/completions returned non-object: {obj}")
    return obj


def _extract_first_choice_message(response_obj: Dict[str, Any]) -> Dict[str, Any]:
    choices = response_obj.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError(
            f"missing choices in chat completion response: {response_obj}"
        )
    first = choices[0]
    if not isinstance(first, dict):
        raise RuntimeError(
            f"invalid first choice in chat completion response: {choices[0]}"
        )
    message = first.get("message")
    if not isinstance(message, dict):
        raise RuntimeError(
            f"missing choice.message in chat completion response: {first}"
        )
    return message


def _extract_assistant_text(message: Dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: List[str] = []
        for part in content:
            if not isinstance(part, dict):
                continue
            text = part.get("text")
            if isinstance(text, str) and text:
                parts.append(text)
        return "\n".join(parts).strip()
    return ""


def _reasoning_detail_summary_text(detail: Dict[str, Any]) -> str:
    summary = detail.get("summary")
    if isinstance(summary, str) and summary.strip():
        return summary.strip()
    if isinstance(summary, list):
        parts: List[str] = []
        for block in summary:
            if isinstance(block, dict):
                text = block.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
            elif isinstance(block, str) and block.strip():
                parts.append(block.strip())
        return "\n\n".join(parts).strip()
    text = detail.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()
    return ""


def _extract_reasoning_summary_text(message: Dict[str, Any]) -> str:
    details = message.get("reasoning_details")
    if not isinstance(details, list):
        return ""
    parts: List[str] = []
    for detail in details:
        if not isinstance(detail, dict):
            continue
        text = _reasoning_detail_summary_text(detail)
        if text:
            parts.append(text)
    return "\n\n".join(parts).strip()


def _has_encrypted_reasoning_detail(message: Dict[str, Any]) -> bool:
    details = message.get("reasoning_details")
    if not isinstance(details, list):
        return False
    return any(
        isinstance(detail, dict)
        and detail.get("type") == "reasoning.encrypted"
        and isinstance(detail.get("data"), str)
        and bool(detail.get("data"))
        for detail in details
    )


def _has_signature_detail(message: Dict[str, Any]) -> bool:
    details = message.get("reasoning_details")
    if not isinstance(details, list):
        return False
    return any(
        isinstance(detail, dict)
        and isinstance(detail.get("signature"), str)
        and bool(detail.get("signature"))
        for detail in details
    )


def _safe_read_fixture_file(path_str: str) -> str:
    if not path_str:
        raise RuntimeError("tool call path is empty")
    base = _reasoning_test_dir().resolve()
    target = (base / path_str).resolve()
    if base not in [target, *target.parents]:
        raise RuntimeError(f"tool call path escapes fixture dir: {path_str}")
    return target.read_text(encoding="utf-8")


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_chat_api_gpt5_mini_reasoning_regression() -> None:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    prompt = _load_prompt()
    working_directory = str(_reasoning_test_dir())

    first_messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You have access to the read_file tool. "
                f"The working directory for file paths is: {working_directory}. "
                "You can use relative file paths (like 'bank0.json') "
                "which will be resolved relative to this directory."
            ),
        },
        {
            "role": "user",
            "content": prompt,
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
        "stream": False,
        **_get_openai_provider_options(),
    }

    response1 = _post_chat_completions(
        {**base_payload, "messages": first_messages},
        api_key,
        curl_label="first",
    )
    first_message = _extract_first_choice_message(response1)
    tool_calls = first_message.get("tool_calls")
    assert (
        isinstance(tool_calls, list) and tool_calls
    ), "expected first response to include tool_calls"

    print("\n[api-debug] first response id:", response1.get("id"))
    print(
        "[api-debug] first finish_reason:",
        (response1.get("choices") or [{}])[0].get("finish_reason"),
    )

    tool_messages: List[Dict[str, Any]] = []
    for tool_call in tool_calls:
        assert isinstance(tool_call, dict), f"invalid tool_call item: {tool_call}"
        fn = tool_call.get("function")
        assert isinstance(
            fn, dict
        ), f"missing function object in tool_call: {tool_call}"
        assert fn.get("name") == "read_file", f"unexpected tool name: {fn.get('name')}"

        call_id = tool_call.get("id")
        assert (
            isinstance(call_id, str) and call_id
        ), f"missing tool_call id: {tool_call}"

        raw_args = fn.get("arguments")
        assert isinstance(
            raw_args, str
        ), f"expected string arguments in tool_call: {tool_call}"
        args = json.loads(raw_args)
        assert isinstance(args, dict), f"expected object arguments: {raw_args}"
        print("[api-debug] tool call arguments:", args)

        path = args.get("path")
        if not isinstance(path, str) or not path:
            path = args.get("file_path")
        assert isinstance(path, str) and path, f"expected path argument: {args}"

        file_content = _safe_read_fixture_file(path)
        tool_messages.append(
            {
                "role": "tool",
                "tool_call_id": call_id,
                "content": file_content,
            }
        )

    second_messages = [*first_messages, first_message, *tool_messages]

    first_summary = _extract_reasoning_summary_text(first_message)
    assert first_summary, "expected first response reasoning summary text"
    assert _has_encrypted_reasoning_detail(
        first_message
    ), "expected first response to include encrypted reasoning detail"
    assert _extract_reasoning_summary_text(
        second_messages[2]
    ), "expected second request payload to preserve first response reasoning summary"
    assert _has_encrypted_reasoning_detail(
        second_messages[2]
    ), "expected second request payload to preserve first response encrypted reasoning detail"
    if _has_signature_detail(first_message):
        assert _has_signature_detail(
            second_messages[2]
        ), "expected second request to preserve signature in assistant message"

    response2 = _post_chat_completions(
        {**base_payload, "messages": second_messages},
        api_key,
        curl_label="second",
    )
    second_message = _extract_first_choice_message(response2)

    final_answer = _extract_assistant_text(second_message)
    print("[api-debug] second response id:", response2.get("id"))
    print("[api-debug] final answer:", final_answer)
    assert "Clock" in final_answer, f"Expected 'Clock', got: {final_answer}"

    second_summary = _extract_reasoning_summary_text(second_message)
    print(
        "[api-debug] reasoning summary lengths:",
        f"first={len(first_summary)}, second={len(second_summary)}",
    )
    assert len(second_summary) * 2 <= len(first_summary), (
        "expected second response reasoning summary to be at most half of first; "
        f"got first={len(first_summary)}, second={len(second_summary)}"
    )
