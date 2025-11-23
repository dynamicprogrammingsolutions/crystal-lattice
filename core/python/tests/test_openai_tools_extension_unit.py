"""
Unit tests for OpenAIToolsExtension behavior (stateless functions tested via instance methods).
"""

import sys
import os

# Ensure repo root is importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

Ext = __import__(
    "plugins.providers.openai.python.openai_tools_extension", fromlist=["OpenAIToolsExtension"]
).OpenAIToolsExtension


def test_to_native_messages_maps_tool_call_id_and_tool_calls():
    ext = Ext()
    messages = [
        {"role": "assistant", "content": "", "metadata": {"tool_calls": [{"id": "c1", "type": "function", "function": {"name": "read_file", "arguments": '{"file_path": "x"}'}}]}},
        {"role": "tool", "content": "ok", "metadata": {"tool_call_id": "abc"}},
    ]
    native = [
        {"role": "assistant", "content": ""},
        {"role": "tool", "content": "ok"},
    ]
    out = ext.to_native_messages(messages, native)
    assert isinstance(out[0].get("tool_calls"), list) and (out[0]["tool_calls"][0].get("function") or {}).get("name") == "read_file"
    assert out[1].get("tool_call_id") == "abc"


def test_process_chunk_accumulates_tool_calls_into_existing_final():
    ext = Ext()
    state = {}
    # existing final message (as provider would produce)
    finals = [{"role": "assistant", "content": ""}]
    natives = [{"role": "assistant", "content": ""}]

    chunk = {
        "choices": [
            {
                "delta": {
                    "tool_calls": [
                        {
                            "id": "c1",
                            "type": "function",
                            "function": {"name": "read_file", "arguments": '{"file_path": "bar.txt"}'}
                        }
                    ]
                }
            }
        ]
    }
    pm, fm, nm, state = ext.process_chunk(chunk, state, [], finals, natives)
    assert fm and isinstance(fm[-1].get("tool_calls"), list)
    assert nm and nm[-1] == fm[-1]


def test_from_native_messages_attaches_metadata_tool_calls():
    ext = Ext()
    messages = [
        {"role": "assistant", "content": ""}
    ]
    native = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"id": "x1", "type": "function", "function": {"name": "read_file", "arguments": '{"file_path": "baz.txt"}'}}
            ],
        }
    ]
    out = ext.from_native_messages(native, messages)
    md = out[0].get("metadata") or {}
    tcs = md.get("tool_calls") or []
    assert tcs and (tcs[0].get("function") or {}).get("name") == "read_file"
    import json as _json
    args_raw = (tcs[0].get("function") or {}).get("arguments")
    if isinstance(args_raw, str):
        args = _json.loads(args_raw)
    else:
        args = args_raw or {}
    assert args.get("file_path") == "baz.txt"


def test_finalize_is_noop():
    ext = Ext()
    finals, native, state = ext.finalize([], [], {})
    assert finals == [] and native == [] and state == {}
