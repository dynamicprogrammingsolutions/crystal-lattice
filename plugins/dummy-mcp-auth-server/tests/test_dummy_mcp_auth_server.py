from __future__ import annotations

import asyncio
import base64
import hashlib

from mcp.server.auth.provider import AuthorizationParams
from mcp.shared.auth import OAuthClientInformationFull

from dummy_mcp_auth_server import DummyMCPAuthProvider, create_server, detect_lan_ip


def test_detect_lan_ip_returns_string() -> None:
    assert detect_lan_ip()


def test_dummy_auth_provider_authorize_and_exchange() -> None:
    async def run() -> None:
        provider = DummyMCPAuthProvider()
        client = OAuthClientInformationFull(
            client_id="client-123",
            redirect_uris=["crystal-lattice://action/conn/session/plugin/action"],
            token_endpoint_auth_method="none",
        )
        await provider.register_client(client)
        verifier = "verifier-123"
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )
        redirect = await provider.authorize(
            client,
            AuthorizationParams(
                state="state-123",
                scopes=["dummy.read"],
                code_challenge=challenge,
                redirect_uri="crystal-lattice://action/conn/session/plugin/action",
                redirect_uri_provided_explicitly=True,
                resource="http://127.0.0.1:8765/mcp",
            ),
        )
        assert "code=" in redirect
        assert "state=state-123" in redirect
        code = next(iter(provider.codes.values()))
        token = await provider.exchange_authorization_code(client, code)
        assert token.access_token
        assert await provider.verify_token(token.access_token)

    asyncio.run(run())


def test_create_server_allows_lan_http_public_url() -> None:
    server = create_server(
        host="0.0.0.0",
        port=8765,
        public_url="http://192.168.1.20:8765",
        log_level="error",
    )

    app = server.streamable_http_app()
    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/mcp" in paths
    assert "/authorize" in paths
    assert "/token" in paths
    assert "/.well-known/oauth-protected-resource/mcp" in paths
