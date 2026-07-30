from __future__ import annotations

import argparse
import json

from .server import create_server


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a deterministic large-output MCP server."
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "streamable-http"],
        help="MCP transport to use.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8775)
    parser.add_argument(
        "--log-level",
        default="warning",
        choices=["debug", "info", "warning", "error", "critical"],
    )
    args = parser.parse_args()

    server = create_server(host=args.host, port=args.port, log_level=args.log_level)
    if args.transport == "streamable-http":
        mcp_url = f"http://{args.host}:{args.port}/mcp"
        print("Dummy MCP output server starting", flush=True)
        print(f"MCP URL: {mcp_url}", flush=True)
        print("Crystal Lattice config snippet:", flush=True)
        print(
            json.dumps(
                {
                    "mcp_enabled": True,
                    "mcp_servers": {
                        "dummy-output": {
                            "enabled": True,
                            "transport": "http",
                            "url": mcp_url,
                            "startup_timeout_seconds": 5,
                            "tool_timeout_seconds": 10,
                        }
                    },
                },
                indent=2,
            ),
            flush=True,
        )
        server.run(transport="streamable-http")
        return

    server.run(transport="stdio")


if __name__ == "__main__":
    main()
