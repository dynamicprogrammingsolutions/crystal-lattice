from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict

import pytest
from dotenv import load_dotenv

from agent_app.application_future import AgentApplication
from agent_core import AgentCore

from openai_responses_plugins.openai_responses_prompt_caching_extension import (
    OpenAIResponsesPromptCachingExtension,
)
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI prompt caching integration tests")
    return api_key


def _base_config(api_key: str) -> Dict[str, Any]:
    return {
        "model": "gpt-5-mini",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
    }


def _assert_successful_text_response(responses: list[dict[str, Any]], marker: str) -> None:
    assert responses
    final = responses[-1]
    assert final.get("role") == "assistant"
    content = str(final.get("content") or "")
    assert marker in content


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_generated_prompt_cache_key_real_api(
    tmp_path: Path,
    ensure_openai_api_key: str,
) -> None:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openai": {
                "provider": "openai_responses",
                **_base_config(ensure_openai_api_key),
            }
        },
        "plugins": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider",
            "openai_responses_plugins.openai_responses_prompt_caching_extension.OpenAIResponsesPromptCachingExtension",
        ],
        "agents": {"default": {"provider": "openai"}},
    }
    config_path = tmp_path / "config_openai_prompt_caching_integration.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")

    app = AgentApplication(str(config_path), str(tmp_path / "sessions"))
    core, base_config, session = app.create_session("default")

    generated_key = ((session.metadata or {}).get("overrides") or {}).get("prompt_cache_key")
    assert isinstance(generated_key, str) and generated_key

    session = core.add_message(
        session,
        "user",
        "Reply with exactly: OPENAI_PROMPT_CACHE_GENERATED_OK",
        config=base_config,
    )
    app.save_session(session)

    events = list(app.send_request(core, session, base_config, stream=False))
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert checkpoints
    final_session = checkpoints[-1]["session"]
    _assert_successful_text_response(
        [message.to_dict() for message in final_session.messages if message.role == "assistant"],
        "OPENAI_PROMPT_CACHE_GENERATED_OK",
    )


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_manual_prompt_cache_key_real_api(
    ensure_openai_api_key: str,
) -> None:
    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[OpenAIResponsesPromptCachingExtension],
    )

    config = {
        **_base_config(ensure_openai_api_key),
        "prompt_cache_key": f"manual_{uuid.uuid4().hex}",
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly: OPENAI_PROMPT_CACHE_MANUAL_OK")

    _new_session, responses = core.send_request(session, config)

    _assert_successful_text_response(responses, "OPENAI_PROMPT_CACHE_MANUAL_OK")


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_prompt_cache_retention_24h_real_api(
    ensure_openai_api_key: str,
) -> None:
    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[OpenAIResponsesPromptCachingExtension],
    )

    config = {
        **_base_config(ensure_openai_api_key),
        "prompt_cache_key": f"retained_{uuid.uuid4().hex}",
        "enable_prompt_cache_retention_24h": True,
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: OPENAI_PROMPT_CACHE_RETENTION_OK",
    )

    _new_session, responses = core.send_request(session, config)

    _assert_successful_text_response(responses, "OPENAI_PROMPT_CACHE_RETENTION_OK")