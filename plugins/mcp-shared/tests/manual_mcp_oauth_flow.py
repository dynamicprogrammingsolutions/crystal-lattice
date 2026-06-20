from __future__ import annotations

import argparse
import asyncio
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "plugins" / "mcp-shared" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mcp_shared import (  # noqa: E402
    MCPRuntimeManager,
    build_mcp_oauth_pending_login,
    build_runtime_config_from_config,
    exchange_mcp_oauth_code_for_token,
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


def _server_name(scenario: dict[str, Any], selected: str | None = None) -> str:
    server_name = selected
    if isinstance(server_name, str) and server_name:
        return server_name
    servers = scenario.get("mcp_servers")
    if isinstance(servers, dict) and len(servers) == 1:
        only_name = next(iter(servers.keys()))
        if isinstance(only_name, str) and only_name:
            return only_name
    raise ValueError("Pass --server or provide exactly one mcp_servers entry")


def _server_spec(scenario: dict[str, Any], selected: str | None = None) -> dict[str, Any]:
    servers = scenario.get("mcp_servers")
    if not isinstance(servers, dict):
        raise ValueError("Scenario must contain an mcp_servers object")
    server_name = _server_name(scenario, selected)
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


def _pending_path(
    scenario: dict[str, Any], state_root: Path | None, selected: str | None = None
) -> Path:
    return _state_dir(scenario, state_root) / f"{_server_name(scenario, selected)}.pending.json"


def _token_path(
    scenario: dict[str, Any], state_root: Path | None, selected: str | None = None
) -> Path:
    return _state_dir(scenario, state_root) / f"{_server_name(scenario, selected)}.token.json"


def _render_redirect_uri(
    server_name: str,
    spec: dict[str, Any],
    *,
    callback_port: int,
) -> str:
    oauth = spec.get("oauth") if isinstance(spec.get("oauth"), dict) else {}
    template = oauth.get("redirect_uri")
    if not isinstance(template, str) or not template:
        raise ValueError(f"mcp_servers.{server_name}.oauth.redirect_uri must be set")

    rendered = template.replace("{port}", str(callback_port))
    return render_oauth_redirect_uri(
        rendered,
        connection_id="manual-connection",
        session_id="manual-session",
        plugin_id="mcp_runtime_app",
        action_id="mcp_complete_login",
        server_name=server_name,
    )


async def start_flow(args: argparse.Namespace) -> None:
    scenario = _load_json(args.config)
    server_name = _server_name(scenario, args.server)
    spec = _server_spec(scenario, args.server)
    server_url = spec.get("url")
    if not isinstance(server_url, str) or not server_url:
        raise ValueError(f"mcp_servers.{server_name}.url must be set")

    redirect_uri = _render_redirect_uri(
        server_name,
        spec,
        callback_port=args.callback_port,
    )
    login = await build_mcp_oauth_pending_login(
        server_name=server_name,
        server_url=server_url,
        raw_spec=spec,
        redirect_uri=redirect_uri,
        connection_id="manual-connection",
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
        "server_spec": spec,
        "authorization_url": login["authorization_url"],
        "state": login["state"],
        "pending_login": login["pending"],
    }
    pending_path = _pending_path(scenario, args.state_root, args.server)
    _write_json(pending_path, pending)

    print("\nOAuth start succeeded.")
    print(f"Pending state: {pending_path}")
    print("\nOpen this URL in your browser:\n")
    print(login["authorization_url"])
    print("\nAfter approving, copy the full callback URL from the browser address bar.")
    print("Then run:\n")
    server_arg = f" --server {args.server}" if args.server else ""
    print(
        f"python {Path(__file__).as_posix()} finish "
        f"--config {args.config.as_posix()}{server_arg}"
    )


async def finish_flow(args: argparse.Namespace) -> None:
    scenario = _load_json(args.config)
    pending_path = _pending_path(scenario, args.state_root, args.server)
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

    pending_login = pending.get("pending_login")
    if not isinstance(pending_login, dict):
        raise ValueError("Pending state is missing pending_login")

    try:
        token_result = await exchange_mcp_oauth_code_for_token(
            pending_login=pending_login,
            code=code,
        )
    except Exception as exc:
        print("Token exchange failed.")
        print(str(exc))
        raise SystemExit(1) from exc

    token = token_result.model_dump(mode="json", exclude_none=True)

    saved = {
        "scenario_id": pending.get("scenario_id"),
        "server_name": pending_login.get("server_name"),
        "server_spec": pending.get("server_spec"),
        "redirect_uri": pending_login.get("redirect_uri"),
        "token": token,
    }
    token_path = _token_path(scenario, args.state_root, args.server)
    _write_json(token_path, saved)

    print("\nOAuth token exchange succeeded.")
    print(f"Saved login: {token_path}")
    print("\nRun verification:\n")
    server_arg = f" --server {args.server}" if args.server else ""
    print(
        f"python {Path(__file__).as_posix()} verify "
        f"--config {args.config.as_posix()}{server_arg}"
    )


async def verify_flow(args: argparse.Namespace) -> None:
    scenario = _load_json(args.config)
    token_path = _token_path(scenario, args.state_root, args.server)
    if not token_path.exists():
        raise FileNotFoundError(f"Missing saved login. Run finish first: {token_path}")
    saved = _load_json(token_path)

    server_name = str(saved.get("server_name") or _server_name(scenario, args.server))
    spec = saved.get("server_spec")
    if not isinstance(spec, dict):
        spec = _server_spec(scenario, args.server)
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
        "--server",
        default="",
        help="MCP server name. If omitted, the config must contain exactly one server.",
    )
    parser.add_argument(
        "--callback-url",
        default="",
        help="Callback URL for finish. If omitted, finish prompts for it.",
    )
    parser.add_argument(
        "--callback-port",
        type=int,
        default=41793,
        help="Port used when replacing {port} in oauth.redirect_uri.",
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