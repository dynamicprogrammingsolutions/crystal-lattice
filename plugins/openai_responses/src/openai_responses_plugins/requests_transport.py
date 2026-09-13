from __future__ import annotations

import json
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Iterator, Mapping

import requests


@dataclass(frozen=True)
class _ResponseInfo:
    status_code: int
    headers: Mapping[str, str]


class RequestsTransportError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = (
            _ResponseInfo(status_code=status_code, headers=headers or {})
            if status_code is not None
            else None
        )


class _RequestsResponseStream:
    def __init__(self, response: requests.Response) -> None:
        self._response = response
        self.headers = response.headers

    def __enter__(self) -> _RequestsResponseStream:
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        _ = exc_type, exc, traceback
        self.close()

    def __iter__(self) -> Iterator[dict[str, Any]]:
        event_name: str | None = None
        data_lines: list[str] = []
        for raw_line in self._response.iter_lines(decode_unicode=True):
            line = raw_line if isinstance(raw_line, str) else raw_line.decode("utf-8")
            if line == "":
                payload = "\n".join(data_lines)
                if payload and payload != "[DONE]":
                    parsed = json.loads(payload)
                    if isinstance(parsed, dict):
                        if event_name and "type" not in parsed:
                            parsed["type"] = event_name
                        yield parsed
                event_name = None
                data_lines = []
                continue
            if line.startswith("event:"):
                event_name = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
        payload = "\n".join(data_lines)
        if payload and payload != "[DONE]":
            parsed = json.loads(payload)
            if isinstance(parsed, dict):
                if event_name and "type" not in parsed:
                    parsed["type"] = event_name
                yield parsed

    def close(self) -> None:
        self._response.close()


class _ModelsResource:
    def __init__(self, client: RequestsOpenAIClient) -> None:
        self._client = client

    def list(self) -> SimpleNamespace:
        payload = self._client._request_json("GET", "/models")
        data = payload.get("data")
        return SimpleNamespace(
            data=[item for item in data if isinstance(item, dict)]
            if isinstance(data, list)
            else []
        )


class _ResponsesResource:
    def __init__(self, client: RequestsOpenAIClient) -> None:
        self._client = client

    def create(
        self,
        *,
        extra_headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
        **payload: Any,
    ) -> dict[str, Any] | _RequestsResponseStream:
        stream = bool(payload.get("stream", False))
        if stream:
            return self._client._request_stream(
                "POST",
                "/responses",
                payload=payload,
                headers=extra_headers,
                timeout=timeout,
            )
        return self._client._request_json(
            "POST",
            "/responses",
            payload=payload,
            headers=extra_headers,
            timeout=timeout,
        )


class _UnsupportedFilesResource:
    def create(self, **kwargs: Any) -> Any:
        _ = kwargs
        raise RequestsTransportError(
            "File upload is unavailable with provider_transport=requests"
        )


class RequestsOpenAIClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: float,
        default_headers: Mapping[str, str] | None = None,
        max_retries: int = 0,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_headers = dict(default_headers or {})
        self.max_retries = max(0, max_retries)
        self._session = session or requests.Session()
        self.models = _ModelsResource(self)
        self.responses = _ResponsesResource(self)
        self.files = _UnsupportedFilesResource()

    def with_options(
        self,
        *,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> RequestsOpenAIClient:
        return RequestsOpenAIClient(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout if timeout is not None else self.timeout,
            default_headers=self.default_headers,
            max_retries=(
                max_retries if max_retries is not None else self.max_retries
            ),
            session=self._session,
        )

    def _headers(
        self,
        extra: Mapping[str, str] | None,
    ) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.default_headers,
            **dict(extra or {}),
        }

    def _send(
        self,
        method: str,
        path: str,
        *,
        payload: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
        stream: bool = False,
    ) -> requests.Response:
        for attempt in range(self.max_retries + 1):
            try:
                response = self._session.request(
                    method,
                    f"{self.base_url}{path}",
                    json=dict(payload) if payload is not None else None,
                    headers=self._headers(headers),
                    timeout=timeout if timeout is not None else self.timeout,
                    stream=stream,
                )
            except requests.RequestException as error:
                if attempt < self.max_retries:
                    continue
                raise RequestsTransportError(f"OpenAI request failed: {error}") from error
            if response.status_code < 400:
                return response
            if attempt < self.max_retries and response.status_code in {
                408,
                409,
                429,
                500,
                502,
                503,
                504,
            }:
                response.close()
                continue
            body = response.text[:1000]
            status = response.status_code
            response_headers = dict(response.headers)
            response.close()
            raise RequestsTransportError(
                f"OpenAI request failed with HTTP {status}: {body}",
                status_code=status,
                headers=response_headers,
            )
        raise RequestsTransportError("OpenAI request failed without a response")

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        response = self._send(
            method,
            path,
            payload=payload,
            headers=headers,
            timeout=timeout,
        )
        try:
            parsed = response.json()
        except ValueError as error:
            body = response.text[:1000]
            response.close()
            raise RequestsTransportError(
                f"OpenAI response was not valid JSON: {body}"
            ) from error
        response.close()
        if not isinstance(parsed, dict):
            raise RequestsTransportError("OpenAI response must be a JSON object")
        return parsed

    def _request_stream(
        self,
        method: str,
        path: str,
        *,
        payload: Mapping[str, Any],
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> _RequestsResponseStream:
        response = self._send(
            method,
            path,
            payload=payload,
            headers={
                "Accept": "text/event-stream",
                **dict(headers or {}),
            },
            timeout=timeout,
            stream=True,
        )
        return _RequestsResponseStream(response)

    def close(self) -> None:
        self._session.close()