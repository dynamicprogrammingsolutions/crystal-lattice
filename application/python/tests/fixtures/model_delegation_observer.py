"""Credential-free evidence from the production provider and session store.

The observers forward every call and streamed event to/from the real implementation.
Only bounded user prompts, instruction fingerprints, final answer text, model names,
and session-write identities are recorded; credentials and reasoning are omitted.
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
from pathlib import Path
from typing import Any


TRACE_ENV = "CRYSTAL_DELEGATION_TEST_TRACE"
PARENT_GUIDANCE = "# Delegating work through Crystal Lattice"
TEXT_LIMIT = 6000


def _record(kind: str, **fields: Any) -> None:
    trace_path = Path(os.environ[TRACE_ENV])
    record = {"kind": kind, "pid": os.getpid(), **fields}
    # One append/write per record permits observation of parent and child processes.
    with trace_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def _text_parts(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "\n".join(
        part["text"]
        for part in content
        if isinstance(part, dict) and isinstance(part.get("text"), str)
    )


class _ResponsesCreateObserver:
    def __init__(self, target: Any) -> None:
        self._target = target

    def create(self, **kwargs: Any) -> Any:
        items = kwargs.get("input") or []
        user_prompts = [
            _text_parts(item.get("content"))[:TEXT_LIMIT]
            for item in items
            if isinstance(item, dict) and item.get("role") == "user"
        ]
        instructions = kwargs.get("instructions") or ""
        _record(
            "provider_request",
            model=kwargs.get("model"),
            user_prompts=user_prompts,
            input_roles=[
                item.get("role")
                for item in items
                if isinstance(item, dict) and item.get("role")
            ],
            instructions_sha256=hashlib.sha256(instructions.encode()).hexdigest(),
            instructions_length=len(instructions),
            instructions_start=instructions[:200],
            has_parent_guidance=PARENT_GUIDANCE in instructions,
        )
        return self._target.create(**kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


class _ResponsesObserver(_ResponsesCreateObserver):
    def __init__(self, target: Any) -> None:
        super().__init__(target)
        streaming = getattr(target, "with_streaming_response", None)
        if streaming is not None:
            self.with_streaming_response = _ResponsesCreateObserver(streaming)


class _ClientObserver:
    def __init__(self, target: Any) -> None:
        self._target = target
        self.responses = _ResponsesObserver(target.responses)

    def with_options(self, **kwargs: Any) -> _ClientObserver:
        return _ClientObserver(self._target.with_options(**kwargs))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


def install_observers() -> None:
    from agent_app.sessions import FilesystemSessionStore
    from openai_responses_plugins.openai_responses_provider import (
        OpenAIResponsesProvider,
    )

    create_client = OpenAIResponsesProvider._create_sdk_client_with_options
    if getattr(create_client, "_delegation_observer", False):
        return
    stream_api = OpenAIResponsesProvider.stream_api
    save_session = FilesystemSessionStore.save
    create_snapshot = FilesystemSessionStore.create_snapshot

    @functools.wraps(create_client)
    def observed_client(self: Any, *args: Any, **kwargs: Any) -> Any:
        return _ClientObserver(create_client(self, *args, **kwargs))

    @functools.wraps(stream_api)
    def observed_stream(
        self: Any, native_messages: Any, state: Any, **kwargs: Any
    ) -> Any:
        context = state.get("_request_context") or {}
        identity = {
            "session_id": context.get("session_id"),
            "request_id": kwargs.get("request_id"),
            "configured_model": (state.get("config") or {}).get("model"),
        }
        _record("provider_stream_started", **identity)
        finished_messages: list[str] = []
        for event in stream_api(self, native_messages, state, **kwargs):
            if event.get("type") == "response.output_item.done":
                item = event.get("item") or {}
                if item.get("type") == "message":
                    finished_messages.append(_text_parts(item.get("content")))
            if event.get("type") == "response.completed":
                response = event.get("response") or {}
                terminal_messages = [
                    _text_parts(item.get("content"))
                    for item in response.get("output", [])
                    if isinstance(item, dict) and item.get("type") == "message"
                ]
                # ChatGPT can send message items before an empty terminal output list.
                answer = "\n".join(terminal_messages or finished_messages)
                _record(
                    "provider_completed",
                    **identity,
                    response_model=response.get("model"),
                    status=response.get("status"),
                    output_text=answer[:TEXT_LIMIT],
                )
            yield event

    @functools.wraps(save_session)
    def observed_save(self: Any, session: Any) -> Any:
        _record(
            "session_save",
            session_id=session.session_id,
            session_root=str(self._root_dir),
        )
        return save_session(self, session)

    @functools.wraps(create_snapshot)
    def observed_snapshot(self: Any, session: Any, **kwargs: Any) -> Any:
        _record(
            "session_snapshot",
            session_id=session.session_id,
            session_root=str(self._root_dir),
        )
        return create_snapshot(self, session, **kwargs)

    observed_client._delegation_observer = True  # type: ignore[attr-defined]
    OpenAIResponsesProvider._create_sdk_client_with_options = observed_client
    OpenAIResponsesProvider.stream_api = observed_stream
    FilesystemSessionStore.save = observed_save
    FilesystemSessionStore.create_snapshot = observed_snapshot


class DelegationEvidenceAppPlugin:
    """Install observers after plugin discovery, including import-cache eviction."""

    name = "delegation_evidence_fixture"
    version = "0.1.0"

    def init(self, app_config: dict[str, Any]) -> dict[str, Any]:
        install_observers()
        return {}

    def get_config_schema(self) -> dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        state: dict[str, Any],
        config: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return []

    def get_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        return []
