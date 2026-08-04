from __future__ import annotations

import asyncio
import threading
from typing import Any, Callable, Dict, Optional, Protocol

from openai import AsyncOpenAI, OpenAI

from .openai_responses_runtime import build_async_openai_sdk_client


COMPACTION_TRANSPORT_CONTEXT_KEY = "_openai_responses_compaction_transport"


class OpenAIResponsesCompactionTransport(Protocol):
    def compact(
        self,
        *,
        model: str,
        input_items: list[Dict[str, Any]],
        instructions: Optional[str],
        timeout: float,
    ) -> Any:
        """Run native compaction and return the SDK response payload."""


class SyncOpenAIResponsesCompactionTransport:
    def __init__(self, client: OpenAI) -> None:
        self._client = client

    def compact(
        self,
        *,
        model: str,
        input_items: list[Dict[str, Any]],
        instructions: Optional[str],
        timeout: float,
    ) -> Any:
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
        config: Dict[str, Any],
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

    def compact(
        self,
        *,
        model: str,
        input_items: list[Dict[str, Any]],
        instructions: Optional[str],
        timeout: float,
    ) -> Any:
        return self._run_awaitable_blocking(
            self._compact_async(
                model=model,
                input_items=input_items,
                instructions=instructions,
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
        timeout: float,
    ) -> Any:
        loop = asyncio.get_running_loop()
        task = asyncio.current_task()
        if task is None:
            raise RuntimeError("OpenAI compaction task is unavailable")
        with self._lock:
            self._loop = loop
            self._task = task
            cancel_requested = self._cancel_requested
        if cancel_requested:
            task.cancel()

        client: AsyncOpenAI = build_async_openai_sdk_client(
            self._config,
            timeout=timeout,
            max_retries=self._max_retries,
        )
        try:
            return await client.responses.compact(
                model=model,
                input=input_items,
                instructions=instructions,
                timeout=timeout,
            )
        finally:
            try:
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
        timeout: float,
    ) -> Dict[str, Any]:
        payload = transport.compact(
            model=model,
            input_items=input_items,
            instructions=instructions,
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
