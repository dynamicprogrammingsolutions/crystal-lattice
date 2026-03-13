from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pytest
from dotenv import load_dotenv

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import Session


REPO_ROOT = Path(__file__).resolve().parents[3]
REASONING_DIR = REPO_ROOT / "plugins" / "openrouter_responses" / "tests" / "reasoning_test"
PROMPT_TEMPLATE = (REASONING_DIR / "prompt.txt").read_text(encoding="utf-8")
DEFAULT_SEED = "Fennel 983; Olive 193; Graphite 668."
FOLLOW_UP_SEED = "Juniper 741; Amber 202; Quartz 515."


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI AgentApplication reasoning tests")
    return api_key


def _prompt_for_seed(seed: str) -> str:
    return PROMPT_TEMPLATE.replace(DEFAULT_SEED, seed)


def _expected_label(seed: str) -> str:
    letters = [ch.upper() for ch in seed if ch.isalpha()]
    letter_values = {chr(ord("A") + idx): idx + 1 for idx in range(26)}
    salpha = sum(letter_values[ch] * ((idx % 3) + 1) for idx, ch in enumerate(letters))
    sdigits = sum(int(ch) for ch in seed if ch.isdigit())
    words = re.findall(r"[A-Za-z]+", seed)
    even_initials = {"B", "D", "F", "H", "J", "L", "N", "P", "R", "T", "V", "X", "Z"}
    wc = sum(1 for word in words if word[:1].upper() in even_initials)
    lval = len(letters)
    pval = (salpha + 7 * sdigits + 11 * wc + lval) % 10
    slen = sum(len(word) for word in words)
    bank_index = (slen + lval + pval) % 3

    bank = json.loads((REASONING_DIR / f"bank{bank_index}.json").read_text(encoding="utf-8"))
    items = bank.get("items") if isinstance(bank, dict) else None
    if not isinstance(items, list):
        raise RuntimeError("expected reasoning bank fixture to expose an items list")
    for item in items:
        if isinstance(item, dict) and item.get("id") == pval:
            payload = item.get("payload")
            label = payload.get("label") if isinstance(payload, dict) else None
            if isinstance(label, str) and label:
                return label
    raise RuntimeError(f"expected label for id={pval} in bank{bank_index}.json")


def _make_config(tmp_path: Path, api_key: str) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openai_responses": {
                "provider": "openai_responses",
                "model": "gpt-5-mini",
                "api_key": api_key,
                "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
                "timeout": 240,
                "reasoning_effort": "high",
                "reasoning_summary": "detailed",
                "allowed_paths": [str(REASONING_DIR)],
                "working_directory": str(REASONING_DIR),
                "max_file_size": 1024 * 1024,
            }
        },
        "plugins": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider",
            "openai_responses_plugins.openai_responses_tools_extension.OpenAIResponsesToolsExtension",
            "openai_responses_plugins.openai_responses_reasoning_extension.OpenAIResponsesReasoningExtension",
            "plugins.request_options_feature.RequestOptionsFeature",
            "plugins.file_reader_tool.FileReaderTool",
        ],
        "agents": {"default": {"provider": "openai_responses"}},
    }

    path = tmp_path / "config_openai_responses_reasoning.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _run_request(
    app: AgentApplication,
    core: Any,
    session: Session,
    base_config: Dict[str, Any],
) -> Tuple[Session, List[Dict[str, Any]]]:
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert checkpoints, "expected at least one session checkpoint"
    final_session = checkpoints[-1]["session"]
    assert isinstance(final_session, Session)
    app.save_session(final_session)
    return final_session, events


def _assistant_messages(session: Session) -> List[Any]:
    return [message for message in session.messages if message.role == "assistant"]


def _response_ids(native_messages: Iterable[Dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for item in native_messages:
        if not isinstance(item, dict):
            continue
        metadata = item.get("_metadata")
        if not isinstance(metadata, dict):
            continue
        response_id = metadata.get("response_id")
        if isinstance(response_id, str) and response_id:
            out.add(response_id)
    return out


def _tool_output_count(native_messages: Iterable[Dict[str, Any]]) -> int:
    return sum(
        1
        for item in native_messages
        if isinstance(item, dict) and item.get("type") == "function_call_output"
    )


def _reasoning_response_ids(native_messages: Iterable[Dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for item in native_messages:
        if not isinstance(item, dict) or item.get("type") != "reasoning":
            continue
        metadata = item.get("_metadata")
        if not isinstance(metadata, dict):
            continue
        response_id = metadata.get("response_id")
        if isinstance(response_id, str) and response_id:
            out.add(response_id)
    return out


def _assert_final_answer(session: Session, seed: str, *, require_reasoning: bool = True) -> None:
    assistants = _assistant_messages(session)
    assert assistants, "expected assistant messages in final session"
    final = assistants[-1]
    assert final.content.strip() == _expected_label(seed)
    metadata = final.metadata or {}
    if require_reasoning:
        reasoning = metadata.get("reasoning")
        assert isinstance(reasoning, str)
        assert reasoning.strip()


@pytest.mark.integration
@pytest.mark.openai
def test_agent_application_openai_responses_reasoning_single_turn(
    tmp_path: Path,
    ensure_openai_api_key: str,
) -> None:
    config_path = _make_config(tmp_path, ensure_openai_api_key)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), event_store=InMemoryEventStore())

    core, base_config, session = app.create_session("default")
    session = core.add_message(
        session,
        "system",
        (
            "You have access to the read_file tool. The working directory for file paths is: "
            f"{REASONING_DIR}. Use relative paths like 'bank0.json'."
        ),
        config=base_config,
    )
    session = core.add_message(session, "user", _prompt_for_seed(DEFAULT_SEED), config=base_config)
    app.save_session(session)

    final_session, events = _run_request(app, core, session, base_config)

    assert any(ev.get("type") == "tool_calls" for ev in events)
    assert any(ev.get("type") == "tool_results" for ev in events)
    _assert_final_answer(final_session, DEFAULT_SEED)


@pytest.mark.integration
@pytest.mark.openai
def test_agent_application_openai_responses_reasoning_follow_up(
    tmp_path: Path,
    ensure_openai_api_key: str,
) -> None:
    config_path = _make_config(tmp_path, ensure_openai_api_key)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), event_store=InMemoryEventStore())

    core, base_config, session = app.create_session("default")
    session = core.add_message(
        session,
        "system",
        (
            "You have access to the read_file tool. The working directory for file paths is: "
            f"{REASONING_DIR}. Use relative paths like 'bank0.json'."
        ),
        config=base_config,
    )
    session = core.add_message(session, "user", _prompt_for_seed(DEFAULT_SEED), config=base_config)
    app.save_session(session)

    first_session, first_events = _run_request(app, core, session, base_config)
    assert any(ev.get("type") == "tool_calls" for ev in first_events)
    _assert_final_answer(first_session, DEFAULT_SEED)

    native_before = (first_session.metadata or {}).get("native_messages") or []
    response_ids_before = _response_ids(native_before)
    tool_outputs_before = _tool_output_count(native_before)
    reasoning_response_ids_before = _reasoning_response_ids(native_before)

    follow_up_session = core.add_message(
        first_session,
        "user",
        _prompt_for_seed(FOLLOW_UP_SEED),
        config=base_config,
    )
    app.save_session(follow_up_session)

    second_session, second_events = _run_request(app, core, follow_up_session, base_config)

    assert any(ev.get("type") == "tool_calls" for ev in second_events)
    assert any(ev.get("type") == "tool_results" for ev in second_events)
    _assert_final_answer(second_session, FOLLOW_UP_SEED, require_reasoning=False)

    native_after = (second_session.metadata or {}).get("native_messages") or []
    assert _tool_output_count(native_after) > tool_outputs_before
    assert len(_response_ids(native_after) - response_ids_before) >= 2
    assert _reasoning_response_ids(native_after) - reasoning_response_ids_before