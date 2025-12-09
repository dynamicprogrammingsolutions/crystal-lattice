from __future__ import annotations

import argparse
import logging
import threading
from pathlib import Path
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
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="path to JSON config file (default: ./.crystal/config.json)",
    )
    parser.add_argument(
        "--sessions-dir",
        type=str,
        default=None,
        help="directory for session files (default: ./crystal/sessions)",
    )

    args = parser.parse_args()

    run_server = args.server or not args.console
    run_console = args.console

    _configure_logging(args.log_file, disable_structlog_colors=False)

    console_logger: Optional[logging.Logger] = None
    if args.log_file:
        console_logger = logging.getLogger("agent_terminal_app.console")

    from .server import run_api
    from .terminal import TerminalApplication, run_terminal

    default_config_path = Path(".crystal") / "config.json"
    default_session_root = Path("crystal") / "sessions"

    config_path = Path(args.config) if args.config is not None else default_config_path
    session_root = Path(args.sessions_dir) if args.sessions_dir is not None else default_session_root

    if not config_path.is_file():
        parser.error(f"Config file not found: {config_path}")

    try:
        session_root.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        parser.error(f"Could not create sessions directory {session_root}: {exc}")

    # Modes:
    # - default (no flags): server only
    # - --console: console only
    # - --console --server: server in background + console in foreground
    if run_console and run_server:
        shared_events = InMemoryEventStore()

        server_app = AgentApplication(str(config_path), str(session_root), event_store=shared_events)
        terminal_agent_app = AgentApplication(str(config_path), str(session_root), event_store=shared_events)
        terminal_app = TerminalApplication(
            config_path=str(config_path),
            session_root=str(session_root),
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
        agent_app = AgentApplication(str(config_path), str(session_root))
        terminal_app = TerminalApplication(
            config_path=str(config_path),
            session_root=str(session_root),
            agent_app=agent_app,
        )
        run_terminal(logger=console_logger, app_instance=terminal_app)
    else:
        app_instance = AgentApplication(str(config_path), str(session_root))
        run_api(host=args.host, port=args.port, app_instance=app_instance)


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()
