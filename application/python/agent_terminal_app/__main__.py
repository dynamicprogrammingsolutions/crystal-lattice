from __future__ import annotations

import argparse
import logging
import threading
from typing import Optional

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core.utils import configure_logging as configure_structlog


def _configure_logging(log_file: Optional[str], *, disable_structlog_colors: bool) -> None:
    """Configure logging for the terminal application.

    Stdout logging remains enabled by default; when ``log_file`` is
    provided, a file handler is added so that server and terminal
    output can be captured in a separate file. Structlog (used by the
    core SDK) is configured so that its output can also be routed to
    this file, and ANSI colors can be disabled when sharing a terminal
    with the interactive console.
    """

    # Standard library logging: always keep stdout; optionally add file.
    if log_file:
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
        handler.setFormatter(formatter)

        root = logging.getLogger()
        root.addHandler(handler)

    # Structlog / core logging:
    # - For console runs, disable colors to avoid raw ANSI codes being
    #   rendered literally by prompt_toolkit's patched stdout.
    # - When log_file is provided, route structlog output to that file.
    try:
        if disable_structlog_colors or log_file:
            structlog_colors = not disable_structlog_colors
            configure_structlog(colors=structlog_colors, log_file_path=log_file)
    except Exception:
        # Defensive: never let logging configuration prevent startup.
        pass


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

    run_server = args.server or not args.console
    run_console = args.console

    _configure_logging(args.log_file, disable_structlog_colors=run_console)

    console_logger: Optional[logging.Logger] = None
    if args.log_file:
        console_logger = logging.getLogger("agent_terminal_app.console")

    from .server import (
        _DEFAULT_CONFIG_PATH as SERVER_CONFIG,
        _DEFAULT_SESSION_ROOT as SERVER_SESSIONS,
        run_api,
    )
    from .terminal import (
        _DEFAULT_CONFIG_PATH as TERM_CONFIG,
        _DEFAULT_SESSION_ROOT as TERM_SESSIONS,
        TerminalApplication,
        run_terminal,
    )

    # Modes:
    # - default (no flags): server only
    # - --console: console only
    # - --console --server: server in background + console in foreground
    if run_console and run_server:
        shared_events = InMemoryEventStore()

        server_app = AgentApplication(str(SERVER_CONFIG), str(SERVER_SESSIONS), event_store=shared_events)
        terminal_agent_app = AgentApplication(str(TERM_CONFIG), str(TERM_SESSIONS), event_store=shared_events)
        terminal_app = TerminalApplication(
            config_path=str(TERM_CONFIG),
            session_root=str(TERM_SESSIONS),
            agent_app=terminal_agent_app,
        )

        thread = threading.Thread(
            target=run_api,
            kwargs={"host": args.host, "port": args.port, "app_instance": server_app},
        )
        thread.daemon = True
        thread.start()

        run_terminal(logger=console_logger, app_instance=terminal_app)
    elif run_console:
        run_terminal(logger=console_logger)
    else:
        run_api(host=args.host, port=args.port)


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()
