from __future__ import annotations

import argparse
import asyncio
import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from aiohttp import web


def _json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {str(key): _json_safe(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_json_safe(child) for child in value]
    return value


class OAuthMCPRecorder:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        log_path: Path,
        token_auth_methods_supported: list[str],
        registered_auth_method: str | None,
    ) -> None:
        self.host = host
        self.port = port
        self.log_path = log_path
        self.token_auth_methods_supported = token_auth_methods_supported
        self.registered_auth_method = registered_auth_method
        self.clients: dict[str, dict[str, Any]] = {}
        self.codes: dict[str, dict[str, Any]] = {}

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def mcp_url(self) -> str:
        return f"{self.base_url}/mcp"

    async def log(self, request: web.Request, body: Any = None) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "time": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": request.path,
            "query": dict(request.query),
            "headers": {
                key: value
                for key, value in request.headers.items()
                if key.lower() not in {"authorization"}
            },
            "authorization": "[present]"
            if request.headers.get("authorization")
            else None,
            "body": _json_safe(body),
        }
        with self.log_path.open("a", encoding="utf-8") as out:
            out.write(json.dumps(event, sort_keys=True) + "\n")

    async def health(self, request: web.Request) -> web.Response:
        await self.log(request)
        return web.json_response({"ok": True, "mcp_url": self.mcp_url})

    async def protected_resource_metadata(self, request: web.Request) -> web.Response:
        await self.log(request)
        return web.json_response(
            {
                "resource": self.mcp_url,
                "authorization_servers": [self.base_url],
                "scopes_supported": ["mcp:connect"],
            }
        )

    async def auth_metadata(self, request: web.Request) -> web.Response:
        await self.log(request)
        return web.json_response(
            {
                "issuer": self.base_url,
                "authorization_endpoint": f"{self.base_url}/oauth/authorize",
                "token_endpoint": f"{self.base_url}/oauth/token",
                "registration_endpoint": f"{self.base_url}/oauth/register",
                "response_types_supported": ["code"],
                "grant_types_supported": ["authorization_code", "refresh_token"],
                "code_challenge_methods_supported": ["S256"],
                "token_endpoint_auth_methods_supported": (
                    self.token_auth_methods_supported
                ),
                "scopes_supported": ["mcp:connect"],
            }
        )

    async def register(self, request: web.Request) -> web.Response:
        body = await request.json()
        await self.log(request, body)
        client_id = f"recorder-client-{len(self.clients) + 1}"
        client_secret = secrets.token_urlsafe(24)
        requested_auth_method = body.get("token_endpoint_auth_method")
        token_auth_method = self.registered_auth_method or requested_auth_method or "none"
        client = {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": body.get("client_name"),
            "redirect_uris": body.get("redirect_uris") or [],
            "grant_types": body.get("grant_types") or ["authorization_code"],
            "response_types": body.get("response_types") or ["code"],
            "scope": body.get("scope") or "",
            "token_endpoint_auth_method": token_auth_method,
        }
        self.clients[client_id] = client
        return web.json_response(client, status=201)

    async def authorize(self, request: web.Request) -> web.Response:
        await self.log(request)
        client_id = request.query.get("client_id") or ""
        redirect_uri = request.query.get("redirect_uri") or ""
        state = request.query.get("state") or ""
        code = f"recorder-code-{secrets.token_urlsafe(12)}"
        self.codes[code] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": request.query.get("scope"),
            "resource": request.query.get("resource"),
        }
        location = f"{redirect_uri}?{urlencode({'code': code, 'state': state})}"
        raise web.HTTPFound(location=location)

    async def token(self, request: web.Request) -> web.Response:
        form = dict(await request.post())
        await self.log(request, form)
        code = form.get("code")
        if code not in self.codes:
            return web.json_response(
                {
                    "error": "invalid_grant",
                    "error_description": "Unknown recorder authorization code",
                },
                status=400,
            )
        return web.json_response(
            {
                "access_token": f"recorder-access-{secrets.token_urlsafe(18)}",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": f"recorder-refresh-{secrets.token_urlsafe(18)}",
                "scope": form.get("scope") or "mcp:connect",
            }
        )

    async def mcp(self, request: web.Request) -> web.Response:
        body: Any = None
        if request.method in {"POST", "PUT", "PATCH"}:
            try:
                body = await request.json()
            except Exception:
                body = await request.text()
        await self.log(request, body)
        if not request.headers.get("authorization"):
            headers = {
                "WWW-Authenticate": (
                    'Bearer error="invalid_token", '
                    f'resource_metadata="{self.base_url}/.well-known/oauth-protected-resource/mcp", '
                    'scope="mcp:connect"'
                )
            }
            return web.Response(status=401, headers=headers)
        if request.method == "HEAD":
            return web.Response(status=200)
        if isinstance(body, dict) and body.get("method") == "initialize":
            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "oauth-recorder",
                            "version": "0.1.0",
                        },
                    },
                }
            )
        if isinstance(body, dict) and body.get("method") == "tools/list":
            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {
                        "tools": [
                            {
                                "name": "recorder_echo",
                                "description": "Echo input for OAuth recorder tests.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {"text": {"type": "string"}},
                                },
                            }
                        ]
                    },
                }
            )
        return web.json_response({"ok": True})

    def app(self) -> web.Application:
        app = web.Application()
        app.router.add_get("/health", self.health)
        app.router.add_route("*", "/mcp", self.mcp)
        app.router.add_get(
            "/.well-known/oauth-protected-resource/mcp",
            self.protected_resource_metadata,
        )
        app.router.add_get("/.well-known/oauth-protected-resource", self.protected_resource_metadata)
        app.router.add_get("/.well-known/oauth-authorization-server", self.auth_metadata)
        app.router.add_get(
            "/.well-known/oauth-authorization-server/mcp",
            self.auth_metadata,
        )
        app.router.add_get("/.well-known/openid-configuration", self.auth_metadata)
        app.router.add_post("/oauth/register", self.register)
        app.router.add_get("/oauth/authorize", self.authorize)
        app.router.add_post("/oauth/token", self.token)
        return app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record MCP OAuth client behavior")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=41873)
    parser.add_argument(
        "--log",
        type=Path,
        default=Path("plugins/mcp-shared/.manual-state/oauth-recorder/requests.jsonl"),
    )
    parser.add_argument(
        "--token-auth-methods-supported",
        default="client_secret_post,none",
        help="Comma-separated auth methods exposed by OAuth metadata.",
    )
    parser.add_argument(
        "--registered-auth-method",
        default="",
        help="Override token_endpoint_auth_method in registration responses.",
    )
    return parser


async def amain() -> None:
    args = build_parser().parse_args()
    recorder = OAuthMCPRecorder(
        host=args.host,
        port=args.port,
        log_path=args.log,
        token_auth_methods_supported=[
            item.strip()
            for item in args.token_auth_methods_supported.split(",")
            if item.strip()
        ],
        registered_auth_method=args.registered_auth_method or None,
    )
    runner = web.AppRunner(recorder.app())
    await runner.setup()
    site = web.TCPSite(runner, args.host, args.port)
    await site.start()
    print(f"MCP OAuth recorder listening at {recorder.mcp_url}")
    print(f"Log: {args.log}")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        await runner.cleanup()


def main() -> None:
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10+ is required")
    main()