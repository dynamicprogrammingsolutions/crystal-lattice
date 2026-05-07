from __future__ import annotations

from typing import Any, Dict

from agent_core import Session

from openai_responses_plugins.openai_responses_prompt_caching_extension import (
    OpenAIResponsesPromptCachingExtension,
)


def _config(**overrides: Any) -> Dict[str, Any]:
    return {
        "model": "gpt-5-mini",
        "api_key": "test_key",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30,
        **overrides,
    }


def _session(*, prompt_cache_key: str | None = None) -> Session:
    metadata: Dict[str, Any] = {"agent_id": "default"}
    if prompt_cache_key is not None:
        metadata["overrides"] = {"prompt_cache_key": prompt_cache_key}
    return Session(session_id="prompt-cache-session", messages=[], metadata=metadata)


def test_initialize_request_injects_prompt_cache_key_and_optional_retention() -> None:
    extension = OpenAIResponsesPromptCachingExtension()
    native_messages = [{"type": "message", "role": "user"}]

    returned_native_messages, state = extension.initialize_request(
        native_messages,
        {
            "config": _config(
                enable_prompt_cache_key=True,
                prompt_cache_key="manual-key",
                enable_prompt_cache_retention_24h=True,
            ),
            "request": {"payload": {"model": "gpt-5-mini"}},
        },
    )

    assert returned_native_messages is native_messages
    assert state["request"]["payload"]["prompt_cache_key"] == "manual-key"
    assert state["request"]["payload"]["prompt_cache_retention"] == "24h"


def test_initialize_request_skips_prompt_cache_when_disabled_or_key_missing() -> None:
    extension = OpenAIResponsesPromptCachingExtension()
    native_messages = [{"type": "message", "role": "user"}]

    _native_messages, state_disabled = extension.initialize_request(
        native_messages,
        {
            "config": _config(enable_prompt_cache_key=False, prompt_cache_key="manual-key"),
            "request": {"payload": {"model": "gpt-5-mini", "prompt_cache_retention": "24h"}},
        },
    )
    assert "prompt_cache_key" not in state_disabled["request"]["payload"]
    assert "prompt_cache_retention" not in state_disabled["request"]["payload"]

    _native_messages, state_blank = extension.initialize_request(
        native_messages,
        {
            "config": _config(enable_prompt_cache_key=True, prompt_cache_key="   "),
            "request": {"payload": {"model": "gpt-5-mini"}},
        },
    )
    assert "prompt_cache_key" not in state_blank["request"]["payload"]
    assert "prompt_cache_retention" not in state_blank["request"]["payload"]


def test_initialize_request_defaults_prompt_cache_key_support_to_enabled() -> None:
    extension = OpenAIResponsesPromptCachingExtension()

    _native_messages, state = extension.initialize_request(
        [],
        {
            "config": _config(prompt_cache_key="generated-like-key"),
            "request": {"payload": {"model": "gpt-5-mini"}},
        },
    )

    assert state["request"]["payload"]["prompt_cache_key"] == "generated-like-key"


def test_initialize_request_strips_prompt_cache_retention_in_chatgpt_mode() -> None:
    extension = OpenAIResponsesPromptCachingExtension()
    native_messages = [{"type": "message", "role": "user"}]

    returned_native_messages, state = extension.initialize_request(
        native_messages,
        {
            "config": _config(
                auth_mode="auto",
                _openai_responses_effective_auth_mode="chatgpt",
                enable_prompt_cache_key=True,
                prompt_cache_key="manual-key",
                enable_prompt_cache_retention_24h=True,
            ),
            "request": {"payload": {"model": "gpt-5-mini", "prompt_cache_retention": "24h"}},
        },
    )

    assert returned_native_messages is native_messages
    assert state["request"]["payload"]["prompt_cache_key"] == "manual-key"
    assert "prompt_cache_retention" not in state["request"]["payload"]


def test_initialize_request_preserves_references_when_nothing_changes() -> None:
    extension = OpenAIResponsesPromptCachingExtension()
    native_messages = [{"type": "message", "role": "user"}]
    state = {
        "config": _config(enable_prompt_cache_key=False),
        "request": {"payload": {"model": "gpt-5-mini"}},
    }

    returned_native_messages, returned_state = extension.initialize_request(
        native_messages,
        state,
    )

    assert returned_native_messages is native_messages
    assert returned_state is state


def test_ensure_prompt_cache_key_generates_only_when_enabled_and_missing() -> None:
    extension = OpenAIResponsesPromptCachingExtension()
    native_messages = [{"type": "message", "role": "user"}]

    generated = extension.execute_action(
        "ensure_prompt_cache_key",
        _session(),
        native_messages,
        {},
        None,
        {"config": _config(enable_prompt_cache_key=True)},
    )

    generated_key = generated["session_metadata"]["overrides"]["prompt_cache_key"]
    assert generated_key.startswith("opcache_")
    assert generated["native_messages"] is native_messages

    preserved = extension.execute_action(
        "ensure_prompt_cache_key",
        _session(prompt_cache_key="existing-key"),
        native_messages,
        {},
        None,
        {"config": _config(enable_prompt_cache_key=True)},
    )
    assert "session_metadata" not in preserved
    assert preserved["native_messages"] is native_messages

    disabled = extension.execute_action(
        "ensure_prompt_cache_key",
        _session(),
        native_messages,
        {},
        None,
        {"config": _config(enable_prompt_cache_key=False)},
    )
    assert "session_metadata" not in disabled
    assert disabled["native_messages"] is native_messages


def test_regenerate_prompt_cache_key_replaces_existing_value() -> None:
    extension = OpenAIResponsesPromptCachingExtension()
    native_messages = [{"type": "message", "role": "user"}]

    result = extension.execute_action(
        "regenerate_prompt_cache_key",
        _session(prompt_cache_key="existing-key"),
        native_messages,
        {},
        None,
        {"config": _config(enable_prompt_cache_key=True)},
    )

    assert result["message"] == "Regenerated prompt cache key"
    regenerated_key = result["session_metadata"]["overrides"]["prompt_cache_key"]
    assert regenerated_key.startswith("opcache_")
    assert regenerated_key != "existing-key"
    assert result["native_messages"] is native_messages