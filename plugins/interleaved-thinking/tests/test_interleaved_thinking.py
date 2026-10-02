from __future__ import annotations

from interleaved_thinking import InterleavedThinking, strip_think_segments


def _plugin() -> InterleavedThinking:
    return InterleavedThinking()


def test_strips_balanced_think_blocks() -> None:
    assert strip_think_segments("<think>internal</think>Answer text") == "Answer text"


def test_strips_multiple_and_multiline_blocks() -> None:
    content = "<think>a</think>First\n\n<think>b\nmore</think>\n\nSecond"
    assert strip_think_segments(content) == "First\n\nSecond"


def test_strips_trailing_unterminated_block() -> None:
    assert strip_think_segments("Answer<think>cut off") == "Answer"


def test_empty_result_becomes_empty_string() -> None:
    assert strip_think_segments("<think>only thinking</think>\n") == ""


def test_plain_content_is_untouched() -> None:
    assert strip_think_segments("Plain answer with < brackets >") == (
        "Plain answer with < brackets >"
    )


def test_native_messages_strip_content_and_fields() -> None:
    native = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "question"},
        {
            "role": "assistant",
            "content": "<think>reasoning</think>answer",
            "reasoning_content": "reasoning",
        },
        {
            "role": "assistant",
            "content": "plain answer",
            "reasoning": "more reasoning",
            "tool_calls": [{"id": "t1", "type": "function"}],
        },
    ]
    cleaned = _plugin().to_native_messages(native, [dict(m) for m in native])
    assert cleaned[0] == native[0]
    assert cleaned[1] == native[1]
    assert cleaned[2] == {"role": "assistant", "content": "answer"}
    assert cleaned[3] == {
        "role": "assistant",
        "content": "plain answer",
        "tool_calls": [{"id": "t1", "type": "function"}],
    }


def test_multipart_text_parts_are_stripped() -> None:
    native = [
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "<think>x</think>answer"},
                {"type": "image_url", "image_url": {"url": "data:..."}},
            ],
        }
    ]
    cleaned = _plugin().to_native_messages(native, [dict(m) for m in native])
    parts = cleaned[0]["content"]
    assert parts[0] == {"type": "text", "text": "answer"}
    assert parts[1] == {"type": "image_url", "image_url": {"url": "data:..."}}


def test_input_messages_are_not_required() -> None:
    native = [{"role": "assistant", "content": "<think>x</think>ok"}]
    cleaned = _plugin().to_native_messages([], [dict(m) for m in native])
    assert cleaned == [{"role": "assistant", "content": "ok"}]


def test_plugin_tags_and_hooks() -> None:
    plugin = _plugin()
    assert plugin.required_tags() == ["provider:openai_compatible"]
    assert plugin.get_tags({}, []) == ["ext:interleaved_thinking"]
    assert plugin.get_config_schema() == {}
