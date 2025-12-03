from __future__ import annotations

import argparse
import logging
import threading
from typing import Optional

from .server import run_api
from .terminal import run_terminal


def _configure_logging(log_file: Optional[str]) -> None:
    """Configure basic logging to also write to a file.

    Stdout logging remains enabled by default; this helper only adds a
    file handler when ``log_file`` is provided so that server and
    terminal output can be captured in a separate file.
    """

    if not log_file:
        return

    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.addHandler(handler)


def main() -> None:  # pragma: no cover - manual execution only
    parser = argparse.ArgumentParser(
        description="Agent Terminal App: FastAPI API + prompt_toolkit console",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="run the interactive terminal client",
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="run the API server (default when no flags are given)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="host to bind the API server to")
    parser.add_argument("--port", type=int, default=8000, help="port to bind the API server to")
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="optional path to a log file; output still goes to stdout",
    )

    args = parser.parse_args()

    _configure_logging(args.log_file)

    console_logger: Optional[logging.Logger] = None
    if args.log_file:
        console_logger = logging.getLogger("agent_terminal_app.console")

    run_server = args.server or not args.console
    run_console = args.console

    # Modes:
    # - default (no flags): server only
    # - --console: console only
    # - --console --server: server in background + console in foreground
    if run_console and run_server:
        thread = threading.Thread(target=run_api, kwargs={"host": args.host, "port": args.port})
        thread.daemon = True
        thread.start()
        run_terminal(logger=console_logger)
    elif run_console:
        run_terminal(logger=console_logger)
    else:
        run_api(host=args.host, port=args.port)


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()
