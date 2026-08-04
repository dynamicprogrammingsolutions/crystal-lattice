from __future__ import annotations

import argparse
import json

from .server import create_server, detect_lan_ip


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a dummy OAuth-protected MCP server."
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Bind host. Defaults to 0.0.0.0."
    )
    parser.add_argument(
        "--port", type=int, default=8765, help="Bind port. Defaults to 8765."
    )
    parser.add_argument(
        "--public-host",
        default=None,
        help="Host/IP that clients should use. Defaults to a detected LAN address.",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
    )
    args = parser.parse_args()

    public_host = args.public_host or detect_lan_ip()
    public_url = f"http://{public_host}:{args.port}"
    mcp_url = f"{public_url}/mcp"
    config_snippet = {
        "mcp_enabled": True,
        "mcp_servers": {
            "dummy-auth": {
                "enabled": True,
                "transport": "http",
                "url": mcp_url,
                "startup_timeout_seconds": 5,
                "tool_timeout_seconds": 10,
            }
        },
    }

    print("Dummy MCP auth server starting", flush=True)
    print(f"Bind address: http://{args.host}:{args.port}", flush=True)
    print(f"LAN/public URL: {public_url}", flush=True)
    print(f"MCP URL: {mcp_url}", flush=True)
    print("Crystal Lattice config snippet:", flush=True)
    print(json.dumps(config_snippet, indent=2), flush=True)
    print(flush=True)

    server = create_server(
        host=args.host,
        port=args.port,
        public_url=public_url,
        log_level=args.log_level,
    )
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
