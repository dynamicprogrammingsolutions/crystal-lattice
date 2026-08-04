from __future__ import annotations

import secrets
import socket
import time
from dataclasses import dataclass, field
from typing import Any

from mcp.server.auth.handlers.authorize import construct_redirect_uri
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    RefreshToken,
)
from mcp.server.auth.routes import create_auth_routes
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.fastmcp import FastMCP
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken


def detect_lan_ip() -> str:
    """Best-effort LAN address detection for phone/simulator manual testing."""

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        host = sock.getsockname()[0]
        if isinstance(host, str) and host and not host.startswith("127."):
            return host
    except OSError:
        pass
    finally:
        sock.close()

    try:
        host = socket.gethostbyname(socket.gethostname())
        if host and not host.startswith("127."):
            return host
    except OSError:
        pass
    return "127.0.0.1"


@dataclass
class DummyMCPAuthProvider:
    clients: dict[str, OAuthClientInformationFull] = field(default_factory=dict)
    codes: dict[str, AuthorizationCode] = field(default_factory=dict)
    access_tokens: dict[str, AccessToken] = field(default_factory=dict)
    refresh_tokens: dict[str, RefreshToken] = field(default_factory=dict)

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        return self.clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        if not client_info.client_id:
            raise ValueError("client_info must include client_id")
        self.clients[client_info.client_id] = client_info

    async def authorize(
        self,
        client: OAuthClientInformationFull,
        params: AuthorizationParams,
    ) -> str:
        if not client.client_id:
            raise ValueError("client must include client_id")
        code_value = secrets.token_urlsafe(32)
        self.codes[code_value] = AuthorizationCode(
            code=code_value,
            scopes=list(params.scopes or []),
            expires_at=time.time() + 300,
            client_id=client.client_id,
            code_challenge=params.code_challenge,
            redirect_uri=params.redirect_uri,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
            resource=params.resource,
        )
        payload: dict[str, str] = {"code": code_value}
        if params.state:
            payload["state"] = params.state
        return construct_redirect_uri(str(params.redirect_uri), **payload)

    async def load_authorization_code(
        self,
        client: OAuthClientInformationFull,
        authorization_code: str,
    ) -> AuthorizationCode | None:
        _ = client
        return self.codes.get(authorization_code)

    async def exchange_authorization_code(
        self,
        client: OAuthClientInformationFull,
        authorization_code: AuthorizationCode,
    ) -> OAuthToken:
        if not client.client_id:
            raise ValueError("client must include client_id")
        self.codes.pop(authorization_code.code, None)
        access_value = secrets.token_urlsafe(32)
        refresh_value = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + 3600
        self.access_tokens[access_value] = AccessToken(
            token=access_value,
            client_id=client.client_id,
            scopes=list(authorization_code.scopes),
            expires_at=expires_at,
            resource=authorization_code.resource,
        )
        self.refresh_tokens[refresh_value] = RefreshToken(
            token=refresh_value,
            client_id=client.client_id,
            scopes=list(authorization_code.scopes),
            expires_at=None,
        )
        return OAuthToken(
            access_token=access_value,
            token_type="Bearer",
            expires_in=3600,
            refresh_token=refresh_value,
            scope=" ".join(authorization_code.scopes) or None,
        )

    async def load_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: str,
    ) -> RefreshToken | None:
        _ = client
        return self.refresh_tokens.get(refresh_token)

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        if not client.client_id:
            raise ValueError("client must include client_id")
        access_value = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + 3600
        self.access_tokens[access_value] = AccessToken(
            token=access_value,
            client_id=client.client_id,
            scopes=list(scopes or refresh_token.scopes),
            expires_at=expires_at,
        )
        return OAuthToken(
            access_token=access_value,
            token_type="Bearer",
            expires_in=3600,
            refresh_token=refresh_token.token,
            scope=" ".join(scopes or refresh_token.scopes) or None,
        )

    async def load_access_token(self, token: str) -> AccessToken | None:
        return self.access_tokens.get(token)

    async def verify_token(self, token: str) -> AccessToken | None:
        return await self.load_access_token(token)

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        token_value = getattr(token, "token", None)
        if isinstance(token_value, str):
            self.access_tokens.pop(token_value, None)
            self.refresh_tokens.pop(token_value, None)


def create_server(
    *,
    host: str = "0.0.0.0",
    port: int = 8765,
    public_url: str | None = None,
    log_level: str = "info",
) -> FastMCP:
    public_url = (public_url or f"http://{detect_lan_ip()}:{port}").rstrip("/")
    provider = DummyMCPAuthProvider()

    # The MCP SDK allows plain HTTP issuers for localhost test servers, but
    # manual phone testing needs a LAN URL such as http://192.168.1.20:8765.
    # This package is explicitly a local dummy server, so relax that check here.
    from mcp.server.auth import routes as auth_routes

    auth_routes.validate_issuer_url = lambda url: None

    server = FastMCP(
        "dummy-mcp-auth-server",
        host=host,
        port=port,
        log_level=log_level.upper(),
        streamable_http_path="/mcp",
        stateless_http=True,
        token_verifier=provider,
        auth=AuthSettings(
            issuer_url=public_url,
            resource_server_url=f"{public_url}/mcp",
            client_registration_options=ClientRegistrationOptions(
                enabled=True,
                valid_scopes=["dummy.read"],
                default_scopes=["dummy.read"],
            ),
            required_scopes=["dummy.read"],
        ),
    )
    server._custom_starlette_routes.extend(  # noqa: SLF001 - local test server wiring
        create_auth_routes(
            provider=provider,
            issuer_url=server.settings.auth.issuer_url,
            service_documentation_url=server.settings.auth.service_documentation_url,
            client_registration_options=server.settings.auth.client_registration_options,
            revocation_options=server.settings.auth.revocation_options,
        )
    )

    @server.tool()
    def dummy_auth_status() -> str:
        """Return a fixed message proving the authenticated MCP tool is callable."""

        return "authenticated as dummy-user"

    return server
