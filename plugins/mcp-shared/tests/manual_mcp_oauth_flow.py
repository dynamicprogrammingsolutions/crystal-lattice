from __future__ import annotations

import argparse
import asyncio
import base64
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.parse import parse_qs, urlparse

import httpx

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "plugins" / "mcp-shared" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mcp_shared import (  # noqa: E402
    MCPRuntimeManager,
    build_mcp_oauth_login_request,
    build_runtime_config_from_config,
    render_oauth_redirect_uri,
)


DEFAULT_SCENARIO = (
    ROOT
    / "plugins"
    / "mcp-shared"
    / "tests"
    / "manual_oauth_scenarios"
    / "figma.example.json"
)
DEFAULT_STATE_ROOT = ROOT / "plugins" / "mcp-shared" / ".manual-state"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[redacted]" if key in {"client_secret", "access_token", "refresh_token"} else _redact(child)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _manual_config(scenario: dict[str, Any]) -> dict[str, Any]:
    value = scenario.get("mcp_oauth_manual")
    return value if isinstance(value, dict) else {}


def _server_name(scenario: dict[str, Any]) -> str:
    manual = _manual_config(scenario)
    server_name = manual.get("server_name")
    if isinstance(server_name, str) and server_name:
        return server_name
    servers = scenario.get("mcp_servers")
    if isinstance(servers, dict) and len(servers) == 1:
        only_name = next(iter(servers.keys()))
        if isinstance(only_name, str) and only_name:
            return only_name
    raise ValueError("Set mcp_oauth_manual.server_name or provide exactly one mcp_servers entry")


def _server_spec(scenario: dict[str, Any]) -> dict[str, Any]:
    servers = scenario.get("mcp_servers")
    if not isinstance(servers, dict):
        raise ValueError("Scenario must contain an mcp_servers object")
    server_name = _server_name(scenario)
    spec = servers.get(server_name)
    if not isinstance(spec, dict):
        raise ValueError(f"Scenario mcp_servers.{server_name} must be an object")
    return deepcopy(spec)


def _state_dir(scenario: dict[str, Any], state_root: Path | None) -> Path:
    root = state_root or DEFAULT_STATE_ROOT
    scenario_id = str(scenario.get("id") or "manual")
    path = root / scenario_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _pending_path(scenario: dict[str, Any], state_root: Path | None) -> Path:
    return _state_dir(scenario, state_root) / f"{_server_name(scenario)}.pending.json"


def _token_path(scenario: dict[str, Any], state_root: Path | None) -> Path:
    return _state_dir(scenario, state_root) / f"{_server_name(scenario)}.token.json"


def _render_redirect_uri(scenario: dict[str, Any], server_name: str, spec: dict[str, Any]) -> str:
    manual = _manual_config(scenario)
    oauth = spec.get("oauth") if isinstance(spec.get("oauth"), dict) else {}
    template = oauth.get("redirect_uri")
    if not isinstance(template, str) or not template:
        raise ValueError(f"mcp_servers.{server_name}.oauth.redirect_uri must be set")

    callback_port = manual.get("callback_port") or 41793
    rendered = template.replace("{port}", str(callback_port))
    return render_oauth_redirect_uri(
        rendered,
        connection_id=str(manual.get("connection_id") or "manual-connection"),
        session_id=str(manual.get("session_id") or "manual-session"),
        plugin_id=str(manual.get("plugin_id") or "mcp_runtime_app"),
        action_id=str(manual.get("action_id") or "mcp_complete_login"),
        server_name=server_name,
    )


def _configured_token_endpoint_auth_method(spec: dict[str, Any]) -> str | None:
    oauth = spec.get("oauth") if isinstance(spec.get("oauth"), dict) else {}
    value = oauth.get("token_endpoint_auth_method")
    if value in {"none", "client_secret_post", "client_secret_basic"}:
        return str(value)
    return None


async def start_flow(args: argparse.Namespace) -> None:
    scenario = _load_json(args.config)
    server_name = _server_name(scenario)
    spec = _server_spec(scenario)
    server_url = spec.get("url")
    if not isinstance(server_url, str) or not server_url:
        raise ValueError(f"mcp_servers.{server_name}.url must be set")

    redirect_uri = _render_redirect_uri(scenario, server_name, spec)
    login = await build_mcp_oauth_login_request(
        server_url=server_url,
        raw_spec=spec,
        redirect_uri=redirect_uri,
    )

    parsed = urlparse(login["authorization_url"])
    query = parse_qs(parsed.query)
    if query.get("redirect_uri") != [redirect_uri]:
        raise AssertionError("Authorization URL redirect_uri does not match scenario redirect_uri")
    if query.get("state") != [login["state"]]:
        raise AssertionError("Authorization URL state does not match pending state")
    if query.get("code_challenge_method") != ["S256"]:
        raise AssertionError("Authorization URL must use PKCE S256")

    pending = {
        "scenario_id": str(scenario.get("id") or "manual"),
        "server_name": server_name,
        "server_spec": spec,
        "redirect_uri": redirect_uri,
        "authorization_url": login["authorization_url"],
        "token_endpoint": login["token_endpoint"],
        "state": login["state"],
        "client_info": login["client_info"],
        "resource": login.get("resource"),
        "code_verifier": login["code_verifier"],
    }
    pending_path = _pending_path(scenario, args.state_root)
    _write_json(pending_path, pending)

    print("\nOAuth start succeeded.")
    print(f"Pending state: {pending_path}")
    print("\nOpen this URL in your browser:\n")
    print(login["authorization_url"])
    print("\nAfter approving, copy the full callback URL from the browser address bar.")
    print("Then run:\n")
    print(f"python {Path(__file__).as_posix()} finish --config {args.config.as_posix()}")


async def finish_flow(args: argparse.Namespace) -> None:
    scenario = _load_json(args.config)
    pending_path = _pending_path(scenario, args.state_root)
    if not pending_path.exists():
        raise FileNotFoundError(f"Missing pending state. Run start first: {pending_path}")
    pending = _load_json(pending_path)

    callback_url = args.callback_url
    if not callback_url:
        print("Paste the full callback URL from the browser, then press Enter:")
        callback_url = input("> ").strip()
    if not callback_url:
        raise ValueError("Callback URL is required")

    query = parse_qs(urlparse(callback_url).query)
    code = query.get("code", [None])[0]
    returned_state = query.get("state", [None])[0]
    if not code:
        raise ValueError("Callback URL does not contain a code parameter")
    if returned_state != pending.get("state"):
        raise ValueError("Callback URL state does not match pending OAuth state")

    client_info = pending.get("client_info")
    if not isinstance(client_info, dict):
        raise ValueError("Pending state is missing client_info")

    form: dict[str, Any] = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": pending["redirect_uri"],
        "client_id": client_info["client_id"],
        "code_verifier": pending["code_verifier"],
    }
    if pending.get("resource"):
        form["resource"] = pending["resource"]

    headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
    server_spec = pending.get("server_spec") if isinstance(pending.get("server_spec"), dict) else {}
    auth_method = (
        _configured_token_endpoint_auth_method(server_spec)
        or client_info.get("token_endpoint_auth_method")
        or "none"
    )
    client_secret = client_info.get("client_secret")
    if auth_method == "client_secret_post" and client_secret:
        form["client_secret"] = client_secret
    elif auth_method == "client_secret_basic" and client_secret:
        encoded_id = quote(str(client_info["client_id"]), safe="")
        encoded_secret = quote(str(client_secret), safe="")
        credentials = base64.b64encode(f"{encoded_id}:{encoded_secret}".encode()).decode()
        headers["Authorization"] = f"Basic {credentials}"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            pending["token_endpoint"],
            data=form,
            headers=headers,
        )

    if response.status_code >= 400:
        print("Token exchange failed.")
        print(f"HTTP {response.status_code}")
        print(response.text)
        raise SystemExit(1)

    token = response.json()
    access_token = token.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        print("Token response did not contain access_token.")
        print(json.dumps(_redact(token), indent=2, sort_keys=True))
        raise SystemExit(1)

    saved = {
        "scenario_id": pending.get("scenario_id"),
        "server_name": pending.get("server_name"),
        "server_spec": pending.get("server_spec"),
        "redirect_uri": pending.get("redirect_uri"),
        "token": token,
    }
    token_path = _token_path(scenario, args.state_root)
    _write_json(token_path, saved)

    print("\nOAuth token exchange succeeded.")
    print(f"Saved login: {token_path}")
    print("\nRun verification:\n")
    print(f"python {Path(__file__).as_posix()} verify --config {args.config.as_posix()}")


async def verify_flow(args: argparse.Namespace) -> None:
    scenario = _load_json(args.config)
    token_path = _token_path(scenario, args.state_root)
    if not token_path.exists():
        raise FileNotFoundError(f"Missing saved login. Run finish first: {token_path}")
    saved = _load_json(token_path)

    server_name = str(saved.get("server_name") or _server_name(scenario))
    spec = saved.get("server_spec")
    if not isinstance(spec, dict):
        spec = _server_spec(scenario)
    token = saved.get("token")
    if not isinstance(token, dict):
        raise ValueError("Saved login is missing token")
    access_token = token.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise ValueError("Saved login token is missing access_token")

    runtime_spec = deepcopy(spec)
    headers = runtime_spec.get("headers")
    if not isinstance(headers, dict):
        headers = {}
    headers["Authorization"] = f"Bearer {access_token}"
    runtime_spec["headers"] = headers
    runtime_spec["enabled"] = True

    config = {
        "mcp_fail_on_startup_error": True,
        "mcp_servers": {
            server_name: runtime_spec,
        },
    }

    manager = MCPRuntimeManager()
    try:
        await manager.start(build_runtime_config_from_config(config))
        snapshot = manager.status_snapshot()
        tools = await manager.list_tools()
        print("\nMCP verification succeeded.")
        print("Status:")
        for item in snapshot:
            print(f"- {item.name}: {item.state} ({item.tool_count} tools)")
        print(f"\nTool count: {len(tools)}")
        for tool in tools[: args.limit]:
            print(f"- {tool.raw_name}")
    finally:
        await manager.close()


def _path_arg(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manual MCP OAuth flow helper")
    parser.add_argument(
        "command",
        choices=["start", "finish", "verify"],
        help="OAuth flow step to run",
    )
    parser.add_argument(
        "--config",
        type=_path_arg,
        default=DEFAULT_SCENARIO,
        help=f"Scenario/config JSON path. Default: {DEFAULT_SCENARIO}",
    )
    parser.add_argument(
        "--state-root",
        type=_path_arg,
        default=None,
        help=f"Directory for pending/token state. Default: {DEFAULT_STATE_ROOT}",
    )
    parser.add_argument(
        "--callback-url",
        default="",
        help="Callback URL for finish. If omitted, finish prompts for it.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum tools to print during verify.",
    )
    return parser


async def amain() -> None:
    args = build_parser().parse_args()
    if args.command == "start":
        await start_flow(args)
    elif args.command == "finish":
        await finish_flow(args)
    elif args.command == "verify":
        await verify_flow(args)
    else:
        raise AssertionError(args.command)


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()