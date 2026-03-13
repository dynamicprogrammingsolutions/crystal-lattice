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
SWITCH_SEED = "Harbor 814; Maple 370; Cinder 926."
DELETE_BRANCH_SEED = "Willow 462; Copper 118; Slate 907."
FORK_BRANCH_SEED = "Briar 555; Onyx 204; Cedar 731."
EDIT_BRANCH_SEED = "Saffron 620; Lattice 146; Ember 833."


@pytest.fixture(scope="module")
def ensure_provider_api_keys() -> Tuple[str, str]:
    load_dotenv(REPO_ROOT / ".env")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openai_api_key or not openrouter_api_key:
        pytest.skip(
            "OPENAI_API_KEY and OPENROUTER_API_KEY are required for cross-provider switch tests"
        )
    return openai_api_key, openrouter_api_key


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


def _openrouter_request_options() -> Dict[str, Any]:
    provider_id = os.getenv("OPENAI_PROVIDER") or "openai"
    return {
        "provider": {
            "order": [provider_id],
            "allow_fallbacks": False,
        }
    }


def _plugin_entry(repo_name: str, entry: str) -> Dict[str, str]:
    return {"path": str(REPO_ROOT / "plugins" / repo_name), "entry": entry}


def _make_config(tmp_path: Path, openai_api_key: str, openrouter_api_key: str) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openai_responses": {
                "provider": "openai_responses",
                "model": "gpt-5-mini",
                "api_key": openai_api_key,
                "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
                "timeout": 240,
                "reasoning_effort": "high",
                "reasoning_summary": "detailed",
                "allowed_paths": [str(REASONING_DIR)],
                "working_directory": str(REASONING_DIR),
                "max_file_size": 1024 * 1024,
            },
            "openrouter": {
                "provider": "openrouter",
                "model": "openai/gpt-5-mini",
                "api_key": openrouter_api_key,
                "base_url": os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1",
                "timeout": 240,
                "reasoning_effort": "high",
                "request_options": {
                    **_openrouter_request_options(),
                    "reasoning": {"summary": "detailed"},
                },
                "allowed_paths": [str(REASONING_DIR)],
                "working_directory": str(REASONING_DIR),
                "max_file_size": 1024 * 1024,
            },
        },
        "plugins": [
            _plugin_entry(
                "openai_responses",
                "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider",
            ),
            _plugin_entry(
                "openai_responses",
                "openai_responses_plugins.openai_responses_tools_extension.OpenAIResponsesToolsExtension",
            ),
            _plugin_entry(
                "openai_responses",
                "openai_responses_plugins.openai_responses_reasoning_extension.OpenAIResponsesReasoningExtension",
            ),
            _plugin_entry(
                "openrouter",
                "openrouter_plugins.openrouter_provider.OpenRouterProvider",
            ),
            _plugin_entry(
                "openrouter",
                "openrouter_plugins.openrouter_tools_extension.OpenRouterToolsExtension",
            ),
            _plugin_entry(
                "openrouter",
                "openrouter_plugins.openrouter_reasoning_extension.OpenRouterReasoningExtension",
            ),
            _plugin_entry(
                "feature-request-options",
                "feature_request_options.RequestOptionsFeature",
            ),
            "plugins.file_reader_tool.FileReaderTool",
            _plugin_entry(
                "rebuild-native-app",
                "rebuild_native_app.RebuildNativeAppPlugin",
            ),
        ],
        "agents": {
            "responses_agent": {"provider": "openai_responses"},
            "chat_agent": {"provider": "openrouter"},
        },
        "application": {
            "rebuild_native_enabled": True,
        },
    }

    path = tmp_path / "config_openai_responses_provider_switch.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _run_request(
    app: AgentApplication,
    core: Any,
    session: Session,
    base_config: Dict[str, Any],
) -> Tuple[Session, List[Dict[str, Any]]]:
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    checkpoints = [event for event in events if event.get("type") == "session_checkpoint"]
    assert checkpoints, "expected at least one session checkpoint"
    final_session = checkpoints[-1]["session"]
    assert isinstance(final_session, Session)
    app.save_session(final_session)
    return final_session, events


def _assistant_messages(session: Session) -> List[Any]:
    return [message for message in session.messages if message.role == "assistant"]


def _assert_final_answer(session: Session, seed: str) -> None:
    assistants = _assistant_messages(session)
    assert assistants, "expected assistant messages in final session"
    assert assistants[-1].content.strip() == _expected_label(seed)


def _load_session_ctx(app: AgentApplication, session_id: str) -> Tuple[Any, Dict[str, Any], Session]:
    ctx = app.load_session(session_id)
    assert ctx is not None, f"expected session {session_id!r} to be loadable"
    return ctx


def _save_and_reload(app: AgentApplication, session: Session) -> Tuple[Any, Dict[str, Any], Session]:
    app.save_session(session)
    return _load_session_ctx(app, session.session_id)


def _assert_native_shape(session: Session) -> None:
    session_md = session.metadata if isinstance(session.metadata, dict) else {}
    native_messages = session_md.get("native_messages")
    integrity = session_md.get("native_messages_integrity")

    assert isinstance(native_messages, list) and native_messages
    assert isinstance(integrity, dict)
    assert session.messages, "expected visible messages after rebuild"
    assert session.messages[-1].role != "tool", "session should not end with an orphaned tool message"

    for message in session.messages:
        md = message.metadata if isinstance(message.metadata, dict) else {}
        native_indices = md.get("native_indices")
        if native_indices is None:
            continue
        assert isinstance(native_indices, list)
        assert native_indices
        for native_index in native_indices:
            assert isinstance(native_index, int)
            assert 0 <= native_index < len(native_messages)


def _continue_with_seed(
    app: AgentApplication,
    core: Any,
    session: Session,
    base_config: Dict[str, Any],
    seed: str,
) -> Tuple[Session, List[Dict[str, Any]]]:
    native_before = ((session.metadata or {}).get("native_messages") or [])
    request_session = core.add_message(session, "user", _prompt_for_seed(seed), config=base_config)
    app.save_session(request_session)
    final_session, events = _run_request(app, core, request_session, base_config)

    _assert_final_answer(final_session, seed)
    native_after = ((final_session.metadata or {}).get("native_messages") or [])
    assert len(native_after) > len(native_before)
    assert not any(event.get("type") == "error" for event in events)
    return final_session, events


def _user_turn_boundaries(session: Session) -> List[Tuple[int, int]]:
    user_indices = [idx for idx, message in enumerate(session.messages) if message.role == "user"]
    bounds: List[Tuple[int, int]] = []
    for position, start_idx in enumerate(user_indices):
        next_start = user_indices[position + 1] if position + 1 < len(user_indices) else len(session.messages)
        bounds.append((start_idx, next_start))
    return bounds


def _remove_first_user_turn(core: Any, session: Session, base_config: Dict[str, Any]) -> Session:
    turn_bounds = _user_turn_boundaries(session)
    assert len(turn_bounds) >= 2, "expected at least two user turns"
    start_idx, end_idx = turn_bounds[0]
    return core.slice_session(session, base_config, remove_indices=list(range(start_idx, end_idx)))


def _fork_before_latest_turn(
    app: AgentApplication,
    core: Any,
    session: Session,
    base_config: Dict[str, Any],
) -> Session:
    turn_bounds = _user_turn_boundaries(session)
    assert len(turn_bounds) >= 3, "expected at least three user turns before fork"
    latest_turn_start, _ = turn_bounds[-1]
    _fork_core, _fork_base, forked = app.fork_session(
        core,
        session,
        base_config,
        upto_index=latest_turn_start - 1,
    )
    app.save_session(forked)
    return forked


def _edit_latest_user_turn(core: Any, session: Session, base_config: Dict[str, Any]) -> Session:
    turn_bounds = _user_turn_boundaries(session)
    latest_turn_start, _ = turn_bounds[-1]
    latest_turn_message = session.messages[latest_turn_start]
    assert latest_turn_message.role == "user"
    updated_content = latest_turn_message.content.rstrip() + "\nReply with the final label only."
    return core.modify_message(session, latest_turn_start, updated_content, config=base_config)


@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.openrouter
def test_agent_application_cross_provider_switch_rebuild_and_history_edits(
    tmp_path: Path,
    ensure_provider_api_keys: Tuple[str, str],
) -> None:
    openai_api_key, openrouter_api_key = ensure_provider_api_keys
    config_path = _make_config(tmp_path, openai_api_key, openrouter_api_key)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), event_store=InMemoryEventStore())

    core, base_config, session = app.create_session("responses_agent")
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

    first_session, _first_events = _run_request(app, core, session, base_config)
    _assert_final_answer(first_session, DEFAULT_SEED)

    second_session, _second_events = _continue_with_seed(
        app,
        core,
        first_session,
        base_config,
        FOLLOW_UP_SEED,
    )
    _assert_native_shape(second_session)

    switched_core, switched_base_config, switched_session = app.update_agent("chat_agent", second_session)
    app.save_session(switched_session)
    result = app.execute_application_action(
        "rebuild_native",
        "rebuild_native_history",
        {"session_id": switched_session.session_id},
    )

    mutations = result.get("mutations") or {}
    assert mutations.get("updated_session_ids") == [switched_session.session_id]

    switched_core, switched_base_config, rebuilt_session = _load_session_ctx(app, switched_session.session_id)
    assert (rebuilt_session.metadata or {}).get("agent_id") == "chat_agent"
    _assert_native_shape(rebuilt_session)

    converted_session, _converted_events = _continue_with_seed(
        app,
        switched_core,
        rebuilt_session,
        switched_base_config,
        SWITCH_SEED,
    )
    _assert_native_shape(converted_session)

    delete_candidate = _remove_first_user_turn(switched_core, converted_session, switched_base_config)
    delete_core, delete_base_config, delete_session = _save_and_reload(app, delete_candidate)
    _assert_native_shape(delete_session)
    delete_final, _delete_events = _continue_with_seed(
        app,
        delete_core,
        delete_session,
        delete_base_config,
        DELETE_BRANCH_SEED,
    )
    _assert_native_shape(delete_final)

    fork_candidate = _fork_before_latest_turn(app, switched_core, converted_session, switched_base_config)
    fork_core, fork_base_config, fork_session = _load_session_ctx(app, fork_candidate.session_id)
    _assert_native_shape(fork_session)
    fork_final, _fork_events = _continue_with_seed(
        app,
        fork_core,
        fork_session,
        fork_base_config,
        FORK_BRANCH_SEED,
    )
    _assert_native_shape(fork_final)

    edited_candidate = _edit_latest_user_turn(switched_core, converted_session, switched_base_config)
    edit_core, edit_base_config, edit_session = _save_and_reload(app, edited_candidate)
    _assert_native_shape(edit_session)
    edit_final, _edit_events = _continue_with_seed(
        app,
        edit_core,
        edit_session,
        edit_base_config,
        EDIT_BRANCH_SEED,
    )
    _assert_native_shape(edit_final)