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


class _RequestsMessageStream:
    def __init__(self, response: requests.Response) -> None:
        self._response = response

    def __iter__(self) -> Iterator[dict[str, Any]]:
        data_lines: list[str] = []
        event_name: str | None = None
        for raw_line in self._response.iter_lines(decode_unicode=True):
            line = raw_line if isinstance(raw_line, str) else raw_line.decode("utf-8")
            if line == "":
                payload = "\n".join(data_lines)
                if payload:
                    parsed = json.loads(payload)
                    if isinstance(parsed, dict):
                        if event_name and "type" not in parsed:
                            parsed["type"] = event_name
                        yield parsed
                data_lines = []
                event_name = None
                continue
            if line.startswith("event:"):
                event_name = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].lstrip())

    def close(self) -> None:
        self._response.close()


class _ModelsResource:
    def __init__(self, client: RequestsAnthropicClient) -> None:
        self._client = client

    def list(self, *, limit: int = 1000) -> list[dict[str, Any]]:
        payload = self._client._request_json(
            "GET",
            "/v1/models",
            params={"limit": limit},
        )
        data = payload.get("data")
        return [item for item in data if isinstance(item, dict)] if isinstance(
            data, list
        ) else []


class _MessagesResource:
    def __init__(self, client: RequestsAnthropicClient) -> None:
        self._client = client

    def create(self, **payload: Any) -> dict[str, Any] | _RequestsMessageStream:
        stream = bool(payload.pop("stream", False))
        timeout = payload.pop("timeout", None)
        extra_headers = payload.pop("extra_headers", None)
        extra_body = payload.pop("extra_body", None)
        betas = payload.pop("betas", None)
        if isinstance(extra_body, dict):
            payload.update(extra_body)
        headers = dict(extra_headers) if isinstance(extra_headers, dict) else {}
        if isinstance(betas, list) and betas:
            headers.setdefault(
                "anthropic-beta",
                ",".join(item for item in betas if isinstance(item, str)),
            )
        if stream:
            return self._client._request_stream(
                "POST",
                "/v1/messages",
                payload=payload,
                headers=headers,
                timeout=timeout,
            )
        return self._client._request_json(
            "POST",
            "/v1/messages",
            payload=payload,
            headers=headers,
            timeout=timeout,
        )


class RequestsAnthropicClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: float,
        max_retries: int = 0,
        default_headers: Mapping[str, str] | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max(0, max_retries)
        self.default_headers = dict(default_headers or {})
        self._session = session or requests.Session()
        self.models = _ModelsResource(self)
        self.messages = _MessagesResource(self)
        self.beta = SimpleNamespace(messages=self.messages)

    def _url(self, path: str) -> str:
        if self.base_url.endswith("/v1") and path.startswith("/v1/"):
            return f"{self.base_url}{path[3:]}"
        return f"{self.base_url}{path}"

    def _headers(
        self,
        extra: Mapping[str, str] | None,
    ) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            **self.default_headers,
            **dict(extra or {}),
        }

    def _send(
        self,
        method: str,
        path: str,
        *,
        payload: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
        stream: bool = False,
    ) -> requests.Response:
        for attempt in range(self.max_retries + 1):
            try:
                response = self._session.request(
                    method,
                    self._url(path),
                    json=dict(payload) if payload is not None else None,
                    params=dict(params) if params is not None else None,
                    headers=self._headers(headers),
                    timeout=timeout if timeout is not None else self.timeout,
                    stream=stream,
                )
            except requests.RequestException as error:
                if attempt < self.max_retries:
                    continue
                raise RequestsTransportError(
                    f"Anthropic request failed: {error}"
                ) from error
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
                f"Anthropic request failed with HTTP {status}: {body}",
                status_code=status,
                headers=response_headers,
            )
        raise RequestsTransportError("Anthropic request failed without a response")

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        response = self._send(
            method,
            path,
            payload=payload,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        try:
            parsed = response.json()
        except ValueError as error:
            body = response.text[:1000]
            response.close()
            raise RequestsTransportError(
                f"Anthropic response was not valid JSON: {body}"
            ) from error
        response.close()
        if not isinstance(parsed, dict):
            raise RequestsTransportError("Anthropic response must be a JSON object")
        return parsed

    def _request_stream(
        self,
        method: str,
        path: str,
        *,
        payload: Mapping[str, Any],
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> _RequestsMessageStream:
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
        return _RequestsMessageStream(response)

    def close(self) -> None:
        self._session.close()