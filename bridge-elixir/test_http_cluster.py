#!/usr/bin/env python3
"""Multi-node HTTP bridge transfer test through the Docker HAProxy edge."""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
import websockets


BRIDGE_URL = os.environ.get("BRIDGE_URL", "ws://localhost:4000/ws/websocket")
BRIDGE_HTTP_BASE_URL = os.environ.get(
    "BRIDGE_HTTP_BASE_URL", "http://localhost:4000"
).rstrip("/")
TIMEOUT_SECONDS = 30.0

_ref_counter = 0


def phoenix_message(topic: str, event: str, payload: dict[str, Any]) -> str:
    global _ref_counter
    _ref_counter += 1
    return json.dumps(
        {
            "topic": topic,
            "event": event,
            "payload": payload,
            "ref": str(_ref_counter),
        }
    )


async def receive_event(
    websocket: Any,
    expected_event: str,
) -> dict[str, Any]:
    while True:
        raw = await asyncio.wait_for(websocket.recv(), timeout=TIMEOUT_SECONDS)
        message = json.loads(raw)
        if message.get("event") == expected_event:
            return message


async def register_server(websocket: Any, server_id: str) -> None:
    topic = f"server:{server_id}"
    await websocket.send(phoenix_message(topic, "phx_join", {}))
    await receive_event(websocket, "phx_reply")
    await websocket.send(
        phoenix_message(
            topic,
            "register",
            {
                "server_id": server_id,
                "display_name": "HTTP Cluster Test Server",
                "computer_name": "http-cluster-test.local",
                "location": "Docker",
            },
        )
    )
    response = await receive_event(websocket, "phx_reply")
    assert response["payload"]["status"] == "ok"


async def pair_over_http(
    client: httpx.AsyncClient,
    websocket: Any,
    server_id: str,
    client_id: str,
) -> str:
    request_response = await client.post(
        f"{BRIDGE_HTTP_BASE_URL}/bridge/v1/pairings/request",
        json={"server_id": server_id, "client_id": client_id},
    )
    request_response.raise_for_status()
    pairing_request_token = request_response.json()["pairing_request_token"]

    pairing_message = await receive_event(websocket, "pairing_requested")
    assert pairing_message["payload"]["client_id"] == client_id

    confirm_response = await client.post(
        f"{BRIDGE_HTTP_BASE_URL}/bridge/v1/pairings/confirm",
        json={
            "pairing_request_token": pairing_request_token,
            "code": pairing_message["payload"]["code"],
        },
    )
    confirm_response.raise_for_status()
    response_body = confirm_response.json()
    assert response_body["server_id"] == server_id
    return response_body["pairing_token"]


async def run_transfer(
    websocket: Any,
    server_id: str,
    pairing_token: str,
    unique_path: str,
) -> str:
    request_body = bytes(index % 251 for index in range(1_200_000))
    response_body = bytes((250 - index) % 251 for index in range(900_000))
    proxy_url = (
        f"{BRIDGE_HTTP_BASE_URL}/bridge/v1/proxy/{unique_path}" "?cluster_test=1"
    )

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as frontend_client:
        frontend_task = asyncio.create_task(
            frontend_client.put(
                proxy_url,
                headers={
                    "Authorization": "Bearer backend-token",
                    "Content-Type": "application/octet-stream",
                    "X-Crystal-Bridge-Body-Present": "1",
                    "X-Crystal-Bridge-Token": pairing_token,
                },
                content=request_body,
            )
        )

        request_message = await receive_event(websocket, "http_request_v2")
        request = request_message["payload"]
        request_id = request["request_id"]
        assert request["path"] == f"/{unique_path}?cluster_test=1"
        assert request["request_body_present"] is True
        assert request["headers"]["authorization"] == "Bearer backend-token"
        assert "body" not in request
        assert "chunk" not in request

        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as transfer_client:
            download = await transfer_client.get(
                f"{BRIDGE_HTTP_BASE_URL}{request['request_body_path']}",
                headers={"Authorization": f"Bearer {request['request_body_token']}"},
            )
            download.raise_for_status()
            assert download.content == request_body

            await websocket.send(
                phoenix_message(
                    f"server:{server_id}",
                    "http_response_v2_init",
                    {
                        "request_id": request_id,
                        "status": 201,
                        "headers": {
                            "content-type": "application/octet-stream",
                            "x-cluster-test": "complete",
                        },
                    },
                )
            )

            upload = await transfer_client.put(
                f"{BRIDGE_HTTP_BASE_URL}{request['response_body_path']}",
                headers={"Authorization": f"Bearer {request['response_body_token']}"},
                content=response_body,
            )
            upload.raise_for_status()

        frontend_response = await frontend_task
        assert frontend_response.status_code == 201
        assert frontend_response.headers["x-cluster-test"] == "complete"
        assert frontend_response.content == response_body
        return request_id


def assert_transfer_crossed_nodes(
    *,
    since: datetime,
    unique_path: str,
    request_id: str,
) -> None:
    time.sleep(0.25)
    result = subprocess.run(
        [
            "docker",
            "logs",
            "haproxy",
            "--since",
            since.isoformat(),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    relevant_lines = [
        line
        for line in (result.stdout + result.stderr).splitlines()
        if unique_path in line or f"/transfers/{request_id}/" in line
    ]
    nodes = {
        match.group(1)
        for line in relevant_lines
        if (match := re.search(r"bridge_nodes/(bridge-node-[12])", line))
    }

    assert len(relevant_lines) >= 3, (
        "Expected proxy, request-download, and response-upload HAProxy "
        f"entries for request {request_id}; got {relevant_lines!r}"
    )
    assert nodes == {"bridge-node-1", "bridge-node-2"}, (
        "Expected one HTTP transfer to cross both bridge nodes; "
        f"observed nodes={sorted(nodes)} lines={relevant_lines!r}"
    )


async def main() -> None:
    server_id = f"http-cluster-{uuid.uuid4()}"
    client_id = str(uuid.uuid4())
    unique_path = f"__test/http-cluster/{uuid.uuid4()}"
    transfer_started_at = datetime.now(timezone.utc)

    async with websockets.connect(f"{BRIDGE_URL}?type=server") as websocket:
        await register_server(websocket, server_id)
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            pairing_token = await pair_over_http(
                client, websocket, server_id, client_id
            )
        request_id = await run_transfer(
            websocket, server_id, pairing_token, unique_path
        )

    assert_transfer_crossed_nodes(
        since=transfer_started_at,
        unique_path=unique_path,
        request_id=request_id,
    )
    print(
        "HTTP cluster transfer passed: pairing and one raw large-body "
        "transfer crossed bridge-node-1 and bridge-node-2"
    )


if __name__ == "__main__":
    asyncio.run(main())
