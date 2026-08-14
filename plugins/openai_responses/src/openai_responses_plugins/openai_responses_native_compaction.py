from __future__ import annotations

import asyncio
import json
import threading
from typing import Any, Callable, Dict, Optional, Protocol

from openai import AsyncOpenAI, OpenAI

from .openai_responses_runtime import (
    build_async_openai_sdk_client,
    effective_auth_mode,
)


COMPACTION_TRANSPORT_CONTEXT_KEY = "_openai_responses_compaction_transport"
_COMPACTION_ITEM_TYPES = {"compaction", "compaction_summary"}
_REMOTE_COMPACTION_V2_HEADERS = {
    "x-codex-beta-features": "remote_compaction_v2",
}
_REMOTE_COMPACTION_V2_RETAINED_TOKEN_BUDGET = 64_000
_REMOTE_COMPACTION_V2_MAX_AGENT_MESSAGE_TOKENS = 10_000
_REMOTE_COMPACTION_V2_REQUEST_OPTION_KEYS = {
    "include",
    "parallel_tool_calls",
    "prompt_cache_key",
    "reasoning",
    "service_tier",
    "text",
    "tool_choice",
    "tools",
}


def _to_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="python")
        if isinstance(dumped, dict):
            return dumped
    return {}


def _estimated_tokens(value: Dict[str, Any]) -> int:
    try:
        encoded = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError):
        encoded = str(value)
    return max(1, (len(encoded) + 3) // 4)


def _is_retained_remote_v2_item(item: Dict[str, Any]) -> bool:
    item_type = item.get("type")
    if item_type == "message":
        return item.get("role") in {"user", "developer", "system"}
    if item_type != "agent_message":
        return False

    content = item.get("content")
    first = content[0] if isinstance(content, list) and content else None
    text = first.get("text") if isinstance(first, dict) else None
    if isinstance(text, str) and text.startswith("Message Type: FINAL_ANSWER\n"):
        return False
    return _estimated_tokens(item) <= _REMOTE_COMPACTION_V2_MAX_AGENT_MESSAGE_TOKENS


def _retained_remote_v2_input(
    input_items: list[Dict[str, Any]],
) -> list[Dict[str, Any]]:
    candidates = [
        item for item in input_items if _is_retained_remote_v2_item(item)
    ]
    remaining = _REMOTE_COMPACTION_V2_RETAINED_TOKEN_BUDGET
    retained_reversed: list[Dict[str, Any]] = []
    for item in reversed(candidates):
        token_count = _estimated_tokens(item)
        if token_count > remaining:
            continue
        retained_reversed.append(item)
        remaining -= token_count
        if remaining == 0:
            break
    retained_reversed.reverse()
    return retained_reversed


def _remote_v2_result(
    *,
    input_items: list[Dict[str, Any]],
    output_items: list[Dict[str, Any]],
    response: Dict[str, Any],
) -> Dict[str, Any]:
    compaction_items = [
        item
        for item in output_items
        if item.get("type") in _COMPACTION_ITEM_TYPES
    ]
    if len(compaction_items) != 1:
        raise RuntimeError(
            "OpenAI Responses remote compaction v2 expected exactly one "
            f"compaction output item, got {len(compaction_items)}"
        )

    result: Dict[str, Any] = {
        "object": "response.compaction",
        "output": [
            *_retained_remote_v2_input(input_items),
            compaction_items[0],
        ],
    }
    response_id = response.get("id")
    if isinstance(response_id, str) and response_id:
        result["id"] = response_id
    usage = response.get("usage")
    if isinstance(usage, dict):
        result["usage"] = usage
    return result


def _remote_v2_request(
    *,
    model: str,
    input_items: list[Dict[str, Any]],
    instructions: Optional[str],
    request_options: Optional[Dict[str, Any]],
    timeout: float,
) -> Dict[str, Any]:
    compatible_options = {
        key: value
        for key, value in (request_options or {}).items()
        if key in _REMOTE_COMPACTION_V2_REQUEST_OPTION_KEYS
    }
    return {
        **compatible_options,
        "model": model,
        "input": [*input_items, {"type": "compaction_trigger"}],
        "instructions": instructions,
        "store": False,
        "stream": True,
        "extra_headers": _REMOTE_COMPACTION_V2_HEADERS,
        "timeout": timeout,
    }


def _collect_remote_v2_events(
    events: Any,
    *,
    input_items: list[Dict[str, Any]],
) -> Dict[str, Any]:
    output_items: list[Dict[str, Any]] = []
    completed_response: Dict[str, Any] | None = None
    for event in events:
        event_dict = _to_dict(event)
        event_type = event_dict.get("type")
        if event_type == "response.output_item.done":
            item = _to_dict(event_dict.get("item"))
            if item:
                output_items.append(item)
        elif event_type == "response.completed":
            completed_response = _to_dict(event_dict.get("response"))
            break

    if completed_response is None:
        raise RuntimeError(
            "OpenAI Responses remote compaction v2 stream closed before "
            "response.completed"
        )
    if not output_items:
        response_output = completed_response.get("output")
        if isinstance(response_output, list):
            output_items = [
                item_dict
                for item in response_output
                if (item_dict := _to_dict(item))
            ]
    return _remote_v2_result(
        input_items=input_items,
        output_items=output_items,
        response=completed_response,
    )


async def _collect_remote_v2_events_async(
    events: Any,
    *,
    input_items: list[Dict[str, Any]],
) -> Dict[str, Any]:
    output_items: list[Dict[str, Any]] = []
    completed_response: Dict[str, Any] | None = None
    async for event in events:
        event_dict = _to_dict(event)
        event_type = event_dict.get("type")
        if event_type == "response.output_item.done":
            item = _to_dict(event_dict.get("item"))
            if item:
                output_items.append(item)
        elif event_type == "response.completed":
            completed_response = _to_dict(event_dict.get("response"))
            break

    if completed_response is None:
        raise RuntimeError(
            "OpenAI Responses remote compaction v2 stream closed before "
            "response.completed"
        )
    if not output_items:
        response_output = completed_response.get("output")
        if isinstance(response_output, list):
            output_items = [
                item_dict
                for item in response_output
                if (item_dict := _to_dict(item))
            ]
    return _remote_v2_result(
        input_items=input_items,
        output_items=output_items,
        response=completed_response,
    )


class OpenAIResponsesCompactionTransport(Protocol):
    def compact(
        self,
        *,
        model: str,
        input_items: list[Dict[str, Any]],
        instructions: Optional[str],
        request_options: Optional[Dict[str, Any]] = None,
        timeout: float,
    ) -> Any:
        """Run native compaction and return the SDK response payload."""


class SyncOpenAIResponsesCompactionTransport:
    def __init__(self, client: OpenAI, *, config: Dict[str, Any] | None = None) -> None:
        self._client = client
        self._config = config or {}

    def compact(
        self,
        *,
        model: str,
        input_items: list[Dict[str, Any]],
        instructions: Optional[str],
        request_options: Optional[Dict[str, Any]] = None,
        timeout: float,
    ) -> Any:
        if effective_auth_mode(self._config) == "chatgpt":
            stream = self._client.responses.create(
                **_remote_v2_request(
                    model=model,
                    input_items=input_items,
                    instructions=instructions,
                    request_options=request_options,
                    timeout=timeout,
                )
            )
            if hasattr(stream, "__enter__") and hasattr(stream, "__exit__"):
                with stream as active_stream:
                    return _collect_remote_v2_events(
                        active_stream,
                        input_items=input_items,
                    )
            try:
                return _collect_remote_v2_events(
                    stream,
                    input_items=input_items,
                )
            finally:
                close = getattr(stream, "close", None)
                if callable(close):
                    close()

        return self._client.responses.compact(
            model=model,
            input=input_items,
            instructions=instructions,
            timeout=timeout,
        )


class CancellableAsyncOpenAIResponsesCompactionTransport:
    """Synchronous adapter over a cancellable AsyncOpenAI compact task."""

    def __init__(
        self,
        *,
        config: Dict[str, Any] | None = None,
        run_awaitable_blocking: Callable[[Any], Any],
        max_retries: int | None = None,
    ) -> None:
        self._config = config
        self._run_awaitable_blocking = run_awaitable_blocking
        self._max_retries = max_retries
        self._lock = threading.RLock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task[Any] | None = None
        self._cancel_requested = False

    def configure(self, config: Dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise TypeError("config must be a dict")
        with self._lock:
            if self._task is not None:
                raise RuntimeError(
                    "OpenAI compaction transport cannot be reconfigured while running"
                )
            self._config = config

    def compact(
        self,
        *,
        model: str,
        input_items: list[Dict[str, Any]],
        instructions: Optional[str],
        request_options: Optional[Dict[str, Any]] = None,
        timeout: float,
    ) -> Any:
        return self._run_awaitable_blocking(
            self._compact_async(
                model=model,
                input_items=input_items,
                instructions=instructions,
                request_options=request_options,
                timeout=timeout,
            )
        )

    def cancel(self) -> None:
        with self._lock:
            self._cancel_requested = True
            loop = self._loop
            task = self._task
        if loop is not None and task is not None:
            loop.call_soon_threadsafe(task.cancel)

    async def _compact_async(
        self,
        *,
        model: str,
        input_items: list[Dict[str, Any]],
        instructions: Optional[str],
        request_options: Optional[Dict[str, Any]] = None,
        timeout: float,
    ) -> Any:
        loop = asyncio.get_running_loop()
        task = asyncio.current_task()
        if task is None:
            raise RuntimeError("OpenAI compaction task is unavailable")
        with self._lock:
            config = self._config
            if config is None:
                raise RuntimeError(
                    "OpenAI compaction transport must be configured before use"
                )
            self._loop = loop
            self._task = task
            cancel_requested = self._cancel_requested
        if cancel_requested:
            task.cancel()

        client: AsyncOpenAI | None = None
        try:
            client = build_async_openai_sdk_client(
                config,
                timeout=timeout,
                max_retries=self._max_retries,
            )
            if effective_auth_mode(config) == "chatgpt":
                stream = await client.responses.create(
                    **_remote_v2_request(
                        model=model,
                        input_items=input_items,
                        instructions=instructions,
                        request_options=request_options,
                        timeout=timeout,
                    )
                )
                if hasattr(stream, "__aenter__") and hasattr(stream, "__aexit__"):
                    async with stream as active_stream:
                        return await _collect_remote_v2_events_async(
                            active_stream,
                            input_items=input_items,
                        )
                try:
                    return await _collect_remote_v2_events_async(
                        stream,
                        input_items=input_items,
                    )
                finally:
                    close = getattr(stream, "close", None)
                    if callable(close):
                        close_result = close()
                        if asyncio.iscoroutine(close_result):
                            await close_result

            return await client.responses.compact(
                model=model,
                input=input_items,
                instructions=instructions,
                timeout=timeout,
            )
        finally:
            try:
                if client is not None:
                    await client.close()
            finally:
                with self._lock:
                    if self._task is task:
                        self._task = None
                        self._loop = None


class OpenAIResponsesNativeCompactionBackend:
    def compact(
        self,
        transport: OpenAIResponsesCompactionTransport,
        *,
        model: str,
        input_items: list[Dict[str, Any]],
        instructions: Optional[str],
        request_options: Optional[Dict[str, Any]] = None,
        timeout: float,
    ) -> Dict[str, Any]:
        payload = transport.compact(
            model=model,
            input_items=input_items,
            instructions=instructions,
            request_options=request_options,
            timeout=timeout,
        )
        if isinstance(payload, dict):
            return payload
        model_dump = getattr(payload, "model_dump", None)
        if callable(model_dump):
            dumped = model_dump(mode="python")
            if isinstance(dumped, dict):
                return dumped
        raise RuntimeError(
            "[openai_responses_native_compaction] invalid SDK compaction payload"
        )


__all__ = [
    "COMPACTION_TRANSPORT_CONTEXT_KEY",
    "CancellableAsyncOpenAIResponsesCompactionTransport",
    "OpenAIResponsesCompactionTransport",
    "OpenAIResponsesNativeCompactionBackend",
    "SyncOpenAIResponsesCompactionTransport",
]
