from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
import threading
from pathlib import Path
from typing import Optional

from .runtime_layout import RuntimeLayout, load_runtime_layout


def _configure_logging(
    log_file: Optional[str],
    *,
    log_level: Optional[str] = None,
    disable_structlog_colors: bool,
) -> None:
    """Configure logging for the terminal application.

    Stdout logging remains enabled by default; when ``log_file`` is
    provided, a file handler is added so that server and terminal
    output can be captured in a separate file. Structlog (used by the
    core SDK) is configured so that its output can also be routed to
    this file, and ANSI colors can be disabled when sharing a terminal
    with the interactive console.
    """

    # Determine effective level:
    # - CLI flag takes precedence
    # - then LOG_LEVEL env var
    # - finally default to WARNING for this application
    current_env_level = os.getenv("LOG_LEVEL")
    if log_level:
        effective_level_name = log_level.upper()
    elif current_env_level:
        effective_level_name = current_env_level.upper()
    else:
        effective_level_name = "WARNING"

    effective_level = getattr(logging, effective_level_name, logging.WARNING)

    # Keep stdlib logging root configured at the chosen level so
    # uvicorn and other libraries respect it.
    root = logging.getLogger()
    root.setLevel(effective_level)

    # Ensure structlog picks up the same default level:
    # - Respect explicit CLI override even when LOG_LEVEL was already set.
    # - Otherwise, don't overwrite an existing LOG_LEVEL env var.
    if log_level:
        os.environ["LOG_LEVEL"] = effective_level_name
    elif current_env_level is None:
        os.environ["LOG_LEVEL"] = effective_level_name

    # Standard library logging: always keep stdout; optionally add file.
    if log_file:
        handler = logging.FileHandler(log_file)
        handler.setLevel(effective_level)
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)

    # Structlog / core logging:
    # - Always configure structlog after setting LOG_LEVEL so that
    #   core loggers pick up the correct minimum level before any
    #   calls to ``get_logger``.
    # - For console runs, callers may choose to disable colors to
    #   avoid raw ANSI codes in prompt_toolkit's patched stdout.
    # - When ``log_file`` is provided, route structlog output there.
    try:
        from agent_core.utils import configure_logging as configure_structlog

        structlog_colors = None if not disable_structlog_colors else False
        configure_structlog(colors=structlog_colors, log_file_path=log_file)
    except Exception:
        # Defensive: never let logging configuration prevent startup.
        pass


def _configure_fastapi_logging(fastapi_log_file: Optional[str]) -> None:
    """Route uvicorn/FastAPI logs to a dedicated file when requested.

    Uvicorn configures its own logging by default. When running the FastAPI
    server in a background thread alongside the interactive console, that
    default behavior produces noisy stdout output.

    This helper configures relevant loggers with a FileHandler and disables
    propagation so they don't also show up on stdout.
    """

    if not fastapi_log_file:
        return

    try:
        Path(fastapi_log_file).expanduser().resolve().parent.mkdir(
            parents=True, exist_ok=True
        )
    except Exception:
        # If the directory can't be created, let FileHandler raise with a clear error.
        pass

    root_level = logging.getLogger().getEffectiveLevel()

    handler = logging.FileHandler(fastapi_log_file)
    handler.setLevel(root_level)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    handler.setFormatter(formatter)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "starlette"):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(root_level)
        logger.propagate = False


_DEFAULT_CONFIG_COPY_EXCLUDES = {"auth", ".plugin_cache", "__pycache__"}


def _ignore_default_config_entries(_directory: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name in _DEFAULT_CONFIG_COPY_EXCLUDES
        or name.endswith(".pyc")
        or name.endswith(".pyo")
        or name.endswith(".log")
    }


def _ensure_default_config(path: Path, layout: RuntimeLayout) -> Path:
    """Create the bundled portable default config at ``path`` if missing.

    The default configuration lives under ``default_config/`` alongside the
    prompt assets it references via ``${env:CONFIG_DIR}``. Bootstrapping a
    new config therefore copies those support files into the target config
    directory and writes the bundled ``config.json`` content to the requested
    path.
    """

    template_dir = layout.default_config_template
    template = template_dir / "config.json"

    try:
        text = template.read_text(encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(
            f"Could not read default config template at {template}: {exc}"
        ) from exc

    target = path.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)

    for source in template_dir.iterdir():
        if source.name == "config.json" or source.name in _DEFAULT_CONFIG_COPY_EXCLUDES:
            continue

        destination = target.parent / source.name
        if destination.exists():
            continue

        if source.is_dir():
            shutil.copytree(source, destination, ignore=_ignore_default_config_entries)
        else:
            shutil.copy2(source, destination)

    target.write_text(text, encoding="utf-8")
    return target


def _ensure_crystal_gitignore(crystal_dir: Path) -> None:
    """Ensure a .gitignore exists in the given .crystal directory.

    The file ignores all contents of the directory except the .gitignore
    itself so that generated sessions and configs are not committed by
    default.
    """

    try:
        gitignore = crystal_dir / ".gitignore"
        if gitignore.exists():
            return
        crystal_dir.mkdir(parents=True, exist_ok=True)
        gitignore.write_text("*\n!.gitignore\n", encoding="utf-8")
    except Exception:
        # Defensive: failures here should not prevent startup.
        pass


def _load_additional_dotenvs(config_path: Path) -> None:
    """Load .env files related to the resolved config path.

    The search order is:
      1. ``<config_dir>/.env`` where ``config_dir`` is ``config_path.parent``
      2. ``./.crystal/.env`` (project-local overrides)
      3. ``~/.crystal/.env`` (user-level overrides)
      4. Standard ``.env`` discovered from the current directory/parents
    Earlier files take precedence because ``override=False`` is used.
    """

    try:
        from dotenv import load_dotenv  # type: ignore[import-not-found]
    except Exception:
        return

    # 1) .env next to the actual config file.
    try:
        config_dir = config_path.expanduser().resolve().parent
    except Exception:
        config_dir = config_path.parent
    config_env = config_dir / ".env"
    if config_env.is_file():
        try:
            load_dotenv(str(config_env), override=False)
        except Exception:
            pass

    # 2) Local project .crystal/.env.
    try:
        local_crystal = Path(".crystal").resolve()
        local_env = local_crystal / ".env"
        if local_env.is_file():
            try:
                load_dotenv(str(local_env), override=False)
            except Exception:
                pass
    except Exception:
        pass

    # 3) User-level ~/.crystal/.env.
    user_crystal = Path.home() / ".crystal"
    user_env = user_crystal / ".env"
    if user_env.is_file():
        try:
            load_dotenv(str(user_env), override=False)
        except Exception:
            pass

    # 4) Finally, standard .env search from CWD/parents.
    try:
        load_dotenv(override=False)
    except Exception:
        pass


def _set_terminal_title(title: str) -> None:
    """Best-effort update of the terminal window title.

    On POSIX terminals, use a standard ANSI escape sequence.
    On Windows, fall back to the ``title`` console command.
    Failures are silently ignored so that unsupported terminals
    are unaffected.
    """
    print(f"Setting terminal title to: {title}")
    try:
        # Windows consoles (cmd/PowerShell) don't reliably support the
        # xterm title escape, but they do support the "title" command.
        if sys.platform.startswith("win"):
            import os

            os.system(f"title {title}")
        else:
            sys.stdout.write(f"\033]0;{title}\a")
            sys.stdout.flush()
    except Exception:
        # Never let title handling break startup.
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
    parser.add_argument(
        "--host", default="127.0.0.1", help="host to bind the API server to"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="port to bind the API server to"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="optional path to a log file; output still goes to stdout",
    )
    parser.add_argument(
        "--fastapi-log-file",
        type=str,
        default=None,
        help=(
            "optional path to a FastAPI/uvicorn log file. When provided, uvicorn "
            "and FastAPI logs are routed to this file (instead of stdout), which "
            "is useful when running --server and --console together."
        ),
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help=(
            "log level for application and core logs "
            "(default: WARNING; overridden by LOG_LEVEL env var)"
        ),
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="path to JSON config file (default search: ./.crystal/config.json, then ~/.crystal/config.json)",
    )
    parser.add_argument(
        "--config-local",
        action="store_true",
        help="force use of local ./.crystal/config.json, creating a default if missing",
    )
    parser.add_argument(
        "--sessions-dir",
        type=str,
        default=None,
        help="directory for session files (default: ./.crystal/sessions)",
    )
    parser.add_argument(
        "--app-name",
        type=str,
        default="crystal-lattice",
        help="optional name to set as the terminal title",
    )
    parser.add_argument(
        "--runtime-layout-json",
        action="store_true",
        help="print resolved Crystal Lattice runtime layout paths as JSON and exit",
    )

    # Optional integrations: Bonjour and bridge
    parser.add_argument(
        "--enable-bonjour",
        action="store_true",
        help="advertise the HTTP API via Bonjour/mDNS (uses zeroconf)",
    )
    parser.add_argument(
        "--bonjour-port",
        type=int,
        default=None,
        help=("port to advertise over Bonjour (default: server port or 8000)"),
    )
    parser.add_argument(
        "--bonjour-service-name",
        type=str,
        default=None,
        help=(
            "Bonjour service name to advertise as " "(default: 'Agent Terminal App')"
        ),
    )

    parser.add_argument(
        "--bridge-url",
        type=str,
        default=None,
        help=(
            "Bridge WebSocket URL (e.g. ws://localhost:4000/ws/websocket). "
            "When provided, the server registers itself with the bridge "
            "and accepts proxied HTTP requests from paired clients."
        ),
    )
    parser.add_argument(
        "--bridge-display-name",
        type=str,
        default=None,
        help=(
            "Human-friendly name for this server when registering with "
            "the bridge (default: 'Agent Terminal App')."
        ),
    )
    parser.add_argument(
        "--bridge-location",
        type=str,
        default=None,
        help="Optional location string reported to the bridge (e.g. 'Office')",
    )
    parser.add_argument(
        "--bridge-local-http-base",
        type=str,
        default=None,
        help=(
            "Base URL of the local HTTP server as seen from the bridge "
            "(default: http://<SERVER_HOST>:<SERVER_PORT>)."
        ),
    )
    parser.add_argument(
        "--bridge-server-id",
        type=str,
        default=None,
        help=(
            "Optional stable server_id for this process when registering "
            "with the bridge (default: random UUID)."
        ),
    )
    parser.add_argument(
        "--cloud-orchestrator-url",
        type=str,
        default=None,
        help=(
            "Cloud orchestrator HTTP base URL. Config files can reference this "
            "as ${env:CLOUD_ORCHESTRATOR_URL}."
        ),
    )
    parser.add_argument(
        "--cloud-orchestrator-token",
        type=str,
        default=None,
        help=(
            "Optional cloud orchestrator bearer token/secret. Config files can "
            "reference this as ${env:CLOUD_ORCHESTRATOR_TOKEN}."
        ),
    )
    parser.add_argument(
        "--bridge-exit-on-superseded",
        action="store_true",
        help=(
            "Exit the current process if the bridge indicates this server was "
            "superseded by a newer connection."
        ),
    )
    parser.add_argument(
        "--bridge-local-guard",
        action="store_true",
        help=(
            "Opt-in local single-instance guard for the bridge server_id "
            "(lockfile under ~/.crystal/bridge_locks)."
        ),
    )
    parser.add_argument(
        "--bridge-takeover-local",
        action="store_true",
        help=(
            "When --bridge-local-guard is enabled, attempt to SIGTERM the "
            "existing local process holding the lock and take over."
        ),
    )

    args = parser.parse_args()
    runtime_layout = load_runtime_layout()

    if args.runtime_layout_json:
        print(json.dumps(runtime_layout.to_resolved_dict(), indent=2, sort_keys=True))
        return

    # Map CLI flags for Bonjour / bridge integrations onto environment
    # variables so that the FastAPI server and helper modules can read a
    # single configuration source regardless of how the app was started
    # (``python -m agent_terminal_app`` vs direct uvicorn invocation).
    if args.enable_bonjour:
        os.environ["ENABLE_BONJOUR"] = "1"
        if args.bonjour_port is not None:
            os.environ["BONJOUR_PORT"] = str(args.bonjour_port)
        if args.bonjour_service_name:
            os.environ["BONJOUR_SERVICE_NAME"] = args.bonjour_service_name

        advertised_port = args.bonjour_port or args.port
        service_name = args.bonjour_service_name or "Agent Terminal App"
        print(
            f"[agent_terminal_app] Bonjour enabled: service={service_name!r} "
            f"port={advertised_port}"
        )

    if args.bridge_url:
        os.environ["BRIDGE_URL"] = args.bridge_url
        if args.bridge_display_name:
            os.environ["BRIDGE_DISPLAY_NAME"] = args.bridge_display_name
        if args.bridge_location:
            os.environ["BRIDGE_LOCATION"] = args.bridge_location
        if args.bridge_local_http_base:
            os.environ["BRIDGE_LOCAL_HTTP_BASE"] = args.bridge_local_http_base
        if args.bridge_server_id:
            os.environ["BRIDGE_SERVER_ID"] = args.bridge_server_id
        if args.bridge_exit_on_superseded:
            os.environ["BRIDGE_EXIT_ON_SUPERSEDED"] = "1"
        if args.bridge_local_guard:
            os.environ["BRIDGE_LOCAL_GUARD"] = "1"
        if args.bridge_takeover_local:
            os.environ["BRIDGE_TAKEOVER_LOCAL"] = "1"

        display_name = args.bridge_display_name or "Agent Terminal App"
        print(
            f"[agent_terminal_app] Bridge enabled: url={args.bridge_url!r} "
            f"display_name={display_name!r}"
        )

    # Configure logging before importing application modules so that
    # any module-level loggers created during import respect the
    # selected level (CLI or environment).
    run_server = args.server or not args.console
    run_console = args.console

    _configure_logging(
        args.log_file, log_level=args.log_level, disable_structlog_colors=False
    )
    _configure_fastapi_logging(args.fastapi_log_file)

    if args.app_name:
        _set_terminal_title(args.app_name)

    console_logger: Optional[logging.Logger] = None
    if args.log_file:
        console_logger = logging.getLogger("agent_terminal_app.console")

    # Delay imports that pull in agent_app / FastAPI wiring until
    # after logging is configured so that their loggers see the
    # correct level.
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_app.sessions import FilesystemSnapshotSelectionStore
    from .server import run_api
    from .terminal import TerminalApplication, run_terminal

    env_overrides = runtime_layout.env_overrides()
    if args.cloud_orchestrator_url:
        env_overrides["CLOUD_ORCHESTRATOR_URL"] = args.cloud_orchestrator_url
    if args.cloud_orchestrator_token:
        env_overrides["CLOUD_ORCHESTRATOR_TOKEN"] = args.cloud_orchestrator_token
    default_local_config = runtime_layout.user_path("local_config")
    default_home_config = runtime_layout.user_path("home_config")
    default_config = runtime_layout.user_path("default_config")
    default_session_root = runtime_layout.user_path("default_sessions_dir")

    if args.config_local:
        config_path = default_local_config
        if not config_path.is_file():
            try:
                config_path = _ensure_default_config(config_path, runtime_layout)
            except Exception as exc:  # pragma: no cover - defensive
                parser.error(f"Could not create default config at {config_path}: {exc}")
    elif args.config is not None:
        config_path = Path(args.config).expanduser()
        if not config_path.is_file():
            try:
                config_path = _ensure_default_config(config_path, runtime_layout)
            except Exception as exc:  # pragma: no cover - defensive
                parser.error(f"Could not create default config at {config_path}: {exc}")
    else:
        local_config = default_local_config
        home_config = default_home_config
        if local_config.is_file():
            config_path = local_config
        elif home_config.is_file():
            config_path = home_config
        else:
            try:
                config_path = _ensure_default_config(default_config, runtime_layout)
            except Exception as exc:  # pragma: no cover - defensive
                parser.error(
                    f"Could not create default config at {default_config}: {exc}"
                )

    session_root = (
        Path(args.sessions_dir).expanduser()
        if args.sessions_dir is not None
        else default_session_root
    )

    try:
        session_root.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        parser.error(f"Could not create sessions directory {session_root}: {exc}")

    # Ensure a .gitignore for any .crystal directory we control.
    crystal_from_config = (
        config_path.parent if config_path.parent.name == ".crystal" else None
    )
    crystal_from_sessions = (
        session_root
        if session_root.name == ".crystal"
        else session_root.parent if session_root.parent.name == ".crystal" else None
    )
    for crystal_dir in (crystal_from_config, crystal_from_sessions):
        if crystal_dir is not None:
            _ensure_crystal_gitignore(crystal_dir)

    _load_additional_dotenvs(config_path)

    print(f"[agent_terminal_app] Using config: {config_path}")
    print(f"[agent_terminal_app] Using sessions dir: {session_root}")

    # Modes:
    # - default (no flags): server only
    # - --console: console only
    # - --console --server: server in background + console in foreground
    if run_console and run_server:
        shared_events = InMemoryEventStore()

        server_app = AgentApplication(
            str(config_path),
            str(session_root),
            event_store=shared_events,
            snapshot_selection_store=FilesystemSnapshotSelectionStore(
                session_root / ".snapshots"
            ),
            env_overrides=env_overrides,
        )
        terminal_agent_app = AgentApplication(
            str(config_path),
            str(session_root),
            event_store=shared_events,
            env_overrides=env_overrides,
        )
        terminal_app = TerminalApplication(
            config_path=str(config_path),
            session_root=str(session_root),
            agent_app=terminal_agent_app,
        )

        try:
            import uvicorn  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - optional dependency
            parser.error(
                f"Uvicorn is required for --server mode but could not be imported: {exc}"
            )

        import agent_terminal_app.server as server_mod  # type: ignore[import-not-found]

        server_mod._agent_app = server_app  # type: ignore[attr-defined]

        os.environ.setdefault("SERVER_HOST", args.host)
        os.environ.setdefault("SERVER_PORT", str(args.port))

        from uvicorn.config import LOGGING_CONFIG  # type: ignore[import-not-found]

        config = uvicorn.Config(
            "agent_terminal_app.server:app",
            host=args.host,
            port=args.port,
            reload=False,
            log_config=None if args.fastapi_log_file else LOGGING_CONFIG,
        )
        uvicorn_server = uvicorn.Server(config)

        def _run_uvicorn() -> None:
            import asyncio

            asyncio.run(uvicorn_server.serve())

        thread = threading.Thread(
            target=_run_uvicorn, name="agent_terminal_app.uvicorn"
        )
        thread.start()

        try:
            run_terminal(logger=console_logger, app_instance=terminal_app)
        finally:
            uvicorn_server.should_exit = True
            thread.join()
    elif run_console:
        agent_app = AgentApplication(
            str(config_path),
            str(session_root),
            env_overrides=env_overrides,
        )
        terminal_app = TerminalApplication(
            config_path=str(config_path),
            session_root=str(session_root),
            agent_app=agent_app,
        )
        run_terminal(logger=console_logger, app_instance=terminal_app)
    else:
        app_instance = AgentApplication(
            str(config_path),
            str(session_root),
            snapshot_selection_store=FilesystemSnapshotSelectionStore(
                session_root / ".snapshots"
            ),
            env_overrides=env_overrides,
        )
        run_api(
            host=args.host,
            port=args.port,
            app_instance=app_instance,
            log_config=None if args.fastapi_log_file else "default",
        )


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()
