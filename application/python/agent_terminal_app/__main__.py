from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import socket
import subprocess
import sys
import threading
import uuid
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Optional

from .runtime_layout import RuntimeLayout, load_runtime_layout
from .runtime_environment import (
    collect_additional_dotenv_values as _collect_additional_dotenv_values,
)
from .project_profile import ProjectProfile, ProjectProfileManager
from .bonjour import get_local_ip


def _configure_logging(
    log_file: Optional[str],
    *,
    log_level: Optional[str] = None,
    disable_structlog_colors: bool,
    structlog_output_stream: Any | None = None,
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
        # Ensure the parent directory exists (e.g. .crystal/ may not
        # have been created yet when logging is configured).
        parent = Path(log_file).parent
        if str(parent) and not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
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
        configure_structlog(
            colors=structlog_colors,
            log_file_path=log_file,
            output_stream=structlog_output_stream,
        )
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


# ---------------------------------------------------------------------------
# CLI resolution helpers
# ---------------------------------------------------------------------------


def _resolve_effective_host(args: argparse.Namespace) -> str:
    """Resolve the effective bind host.

    When ``--host`` is not explicitly passed (``None``), auto-select
    ``0.0.0.0`` if Bonjour is enabled (so the server is reachable on the
    LAN), otherwise default to ``127.0.0.1``.
    """
    if args.host is not None:
        return args.host
    return "0.0.0.0" if args.enable_bonjour else "127.0.0.1"


def _resolve_log_file(args: argparse.Namespace) -> Optional[str]:
    """Resolve the log file path.

    Defaults to ``.crystal/crystal.log`` when no ``--log-file`` is given
    and ``--no-log-file`` is not set.  An explicit ``--log-file`` always
    wins, even when ``--no-log-file`` is also present.
    """
    if args.log_file is not None:
        return args.log_file
    if args.no_log_file:
        return None
    return str(Path(".crystal") / "crystal.log")


def _resolve_fastapi_log_file(
    args: argparse.Namespace, log_file: Optional[str]
) -> Optional[str]:
    """Resolve the FastAPI log file, defaulting to the main log file."""
    if args.fastapi_log_file is not None:
        return args.fastapi_log_file
    return log_file


def _read_bridge_url_from_config(config_path: Path) -> Optional[str]:
    """Read ``application.bridge_url`` from the config JSON file.

    This reads the raw config file directly (without creating a full
    ``AgentApplication``) since ``bridge_url`` is a plain string that
    does not require placeholder resolution.  If the user needs env-var
    expansion, they should use ``--bridge-url`` or ``.crystal/profile.json``.
    """
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    app_cfg = raw.get("application")
    if not isinstance(app_cfg, dict):
        return None
    bridge_url = app_cfg.get("bridge_url")
    if isinstance(bridge_url, str) and bridge_url:
        return bridge_url
    return None


def _format_startup_summary(
    *,
    project_name: str,
    config_path: Path,
    session_root: Path,
    host: str,
    port: int,
    bonjour_service_name: Optional[str] = None,
    bridge_url: Optional[str] = None,
    lan_ip: Optional[str] = None,
) -> str:
    """Format a consolidated startup summary for server/console modes.

    When *host* is ``0.0.0.0``, *lan_ip* is used for the displayed HTTP
    URL (the caller resolves it via :func:`bonjour.get_local_ip`).
    Otherwise *host* is shown directly.

    Only lines for active features are included.  The returned string
    does not have a trailing newline.
    """
    if host == "0.0.0.0" and lan_ip is not None:
        http_host = lan_ip
    elif host == "0.0.0.0":
        http_host = "127.0.0.1"
    else:
        http_host = host

    lines = [
        f"[crystal-lattice] Starting {project_name}",
        f"  Config:    {config_path}",
        f"  Sessions:  {session_root}",
        f"  HTTP:      http://{http_host}:{port}",
    ]
    if bonjour_service_name is not None:
        lines.append(
            f"  Bonjour:   {bonjour_service_name} (discoverable on local network)"
        )
    if bridge_url is not None:
        lines.append(f"  Bridge:    {bridge_url}")
    return "\n".join(lines)


def _run_terminal_headless(
    app: Any,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Run the terminal with pipe input and dummy output (no TTY required).

    The full console code path runs (session creation, event polling,
    completer setup, ``Session started`` message).  The prompt blocks on
    a pipe; SIGTERM sends EOF to the pipe, causing ``prompt_async()`` to
    raise ``EOFError`` and the loop to exit cleanly.

    Uses ``prompt_toolkit``'s ``create_pipe_input()`` and ``DummyOutput()``
    via ``create_app_session()`` so that the ``PromptSession`` created inside
    ``_run_terminal()`` picks up the non-TTY input/output without any changes
    to ``terminal.py``.
    """
    from prompt_toolkit.application import create_app_session
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    # run_terminal is imported lazily (same as in main()) to avoid
    # pulling in prompt_toolkit and the terminal module before logging
    # is configured.
    from .terminal import run_terminal

    with create_pipe_input() as pipe_input:
        import signal

        signal.signal(signal.SIGTERM, lambda *_: pipe_input.send_text("\x04"))
        with create_app_session(input=pipe_input, output=DummyOutput()):
            run_terminal(logger=logger, app_instance=app)


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


def _parse_bool_env(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip() in {"1", "true", "True", "yes", "YES"}


def _parse_optional_int_env(
    value: Optional[str], *, default: Optional[int]
) -> Optional[int]:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_float_env(value: Optional[str], *, default: float) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _build_server_integration_config(
    args: argparse.Namespace,
    *,
    server_mod: object,
    profile: Optional[ProjectProfile] = None,
    bridge_url_from_config: Optional[str] = None,
    effective_host: str = "127.0.0.1",
    effective_port: int = 8000,
):
    """Build explicit server integration config from CLI args and profile.

    CLI values override externally supplied environment variables for the same
    bridge/Bonjour settings, but the process environment itself is left
    untouched.

    When *profile* is provided, its resolved values (port, bridge_server_id,
    name, bridge_url) are used as defaults — the profile already incorporates
    CLI overrides passed to ``ProjectProfileManager.resolve()``.
    """

    profile_name = profile.name if profile is not None else None
    profile_bridge_server_id = profile.bridge_server_id if profile is not None else None
    profile_bridge_url = profile.bridge_url if profile is not None else None

    bonjour_config = None
    if args.enable_bonjour:
        port_str = (
            str(args.bonjour_port)
            if args.bonjour_port is not None
            else os.getenv("BONJOUR_PORT") or os.getenv("SERVER_PORT")
        )
        try:
            advertised_port = int(port_str) if port_str else effective_port
        except ValueError:
            advertised_port = effective_port
        service_name = (
            args.bonjour_service_name
            or os.getenv("BONJOUR_SERVICE_NAME")
            or profile_name
            or "Agent Terminal App"
        )
        bonjour_config = server_mod.BonjourRuntimeConfig(  # type: ignore[attr-defined]
            service_name=service_name,
            port=advertised_port,
        )

    # Bridge is enabled when --bridge-url is given OR --enable-bridge is set.
    bridge_enabled = args.bridge_url is not None or args.enable_bridge

    bridge_config = None
    if bridge_enabled:
        # Resolve bridge URL: CLI > profile > config.
        # When profile is provided, it already incorporates the CLI --bridge-url
        # override.  When profile is None, fall back to args.bridge_url directly.
        if profile is not None:
            bridge_url = profile_bridge_url or bridge_url_from_config
        else:
            bridge_url = args.bridge_url or bridge_url_from_config

        if not bridge_url:
            # Bridge was requested but no URL was found.
            print(
                "[agent_terminal_app] Bridge enabled but no bridge URL found "
                "(set --bridge-url, add bridge_url to .crystal/profile.json, "
                "or add application.bridge_url to config.json). "
                "Skipping bridge registration."
            )
        else:
            display_name = (
                args.bridge_display_name
                or os.getenv("BRIDGE_DISPLAY_NAME")
                or profile_name
                or "Agent Terminal App"
            )
            location = args.bridge_location or os.getenv("BRIDGE_LOCATION")
            local_http_base = args.bridge_local_http_base or os.getenv(
                "BRIDGE_LOCAL_HTTP_BASE"
            )
            if not local_http_base:
                host = os.getenv("SERVER_HOST", effective_host)
                port = os.getenv("SERVER_PORT", str(effective_port))
                local_http_base = f"http://{host}:{port}"

            bridge_mod = server_mod.bridge_mod  # type: ignore[attr-defined]
            bridge_config = bridge_mod.BridgeConfig(
                bridge_url=bridge_url,
                server_id=profile_bridge_server_id
                or args.bridge_server_id
                or os.getenv("BRIDGE_SERVER_ID")
                or str(uuid.uuid4()),
                display_name=display_name,
                computer_name=socket.gethostname() or "localhost",
                location=location,
                local_http_base=local_http_base,
                bridge_http_base=getattr(args, "bridge_http_base", None)
                or os.getenv("BRIDGE_HTTP_BASE_URL")
                or None,
                ws_max_size_bytes=_parse_optional_int_env(
                    os.getenv("BRIDGE_WS_MAX_SIZE_BYTES"), default=16 * 1024 * 1024
                ),
                http_timeout_seconds=_parse_float_env(
                    os.getenv("BRIDGE_HTTP_TIMEOUT_SECONDS"), default=120.0
                ),
                request_chunk_size_bytes=int(
                    os.getenv("BRIDGE_HTTP_CHUNK_SIZE_BYTES", str(900 * 1024))
                ),
                request_chunking_threshold_bytes=int(
                    os.getenv("BRIDGE_HTTP_CHUNK_THRESHOLD_BYTES", str(256 * 1024))
                ),
                response_chunking_threshold_bytes=int(
                    os.getenv("BRIDGE_HTTP_CHUNK_THRESHOLD_BYTES", str(256 * 1024))
                ),
                max_body_bytes=int(
                    os.getenv("BRIDGE_HTTP_MAX_BODY_BYTES", str(10 * 1024 * 1024))
                ),
                debug=_parse_bool_env(os.getenv("BRIDGE_DEBUG")),
                exit_on_superseded=args.bridge_exit_on_superseded
                or _parse_bool_env(os.getenv("BRIDGE_EXIT_ON_SUPERSEDED")),
                local_guard=args.bridge_local_guard
                or _parse_bool_env(os.getenv("BRIDGE_LOCAL_GUARD")),
                takeover_local=args.bridge_takeover_local
                or _parse_bool_env(os.getenv("BRIDGE_TAKEOVER_LOCAL")),
            )

    if bonjour_config is None and bridge_config is None:
        return None

    return server_mod.ServerIntegrationRuntimeConfig(  # type: ignore[attr-defined]
        bonjour=bonjour_config,
        bridge=bridge_config,
    )


def _set_terminal_title(title: str) -> None:
    """Best-effort update of the terminal window title.

    On POSIX terminals, use a standard ANSI escape sequence.
    On Windows, fall back to the ``title`` console command.
    Failures are silently ignored so that unsupported terminals
    are unaffected.
    """
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


def _command_argparse_type(expected_type: str):
    if expected_type == "integer":
        return int
    if expected_type == "number":
        return float
    return str


def _application_action_map(agent_app: Any) -> dict[tuple[str, str], dict[str, Any]]:
    get_actions = getattr(agent_app, "get_application_actions", None)
    if not callable(get_actions):
        return {}
    actions = get_actions()
    result: dict[tuple[str, str], dict[str, Any]] = {}
    if not isinstance(actions, list):
        return result
    for action in actions:
        if not isinstance(action, dict):
            continue
        plugin = action.get("plugin")
        action_id = action.get("id")
        if isinstance(plugin, str) and isinstance(action_id, str):
            result[(plugin, action_id)] = action
    return result


def _parse_contributed_command(
    command: dict[str, Any],
    action_def: dict[str, Any],
    argv: list[str],
) -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        prog=f"crystal-lattice {command['name']}",
        description=str(command.get("description") or command["name"]),
    )
    raw_action_inputs = action_def.get("inputs")
    action_inputs = raw_action_inputs if isinstance(raw_action_inputs, dict) else {}
    raw_args = command.get("args")
    args_spec = raw_args if isinstance(raw_args, list) else []
    for entry in args_spec:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        flags = entry.get("flags")
        if not isinstance(name, str) or not name:
            continue
        if not isinstance(flags, list) or not all(
            isinstance(flag, str) and flag for flag in flags
        ):
            continue
        raw_action_input = action_inputs.get(name)
        action_input = raw_action_input if isinstance(raw_action_input, dict) else {}
        expected_type = str(entry.get("type") or action_input.get("type") or "string")
        required = bool(action_input.get("required", False))
        default = action_input.get("default")
        help_text = str(entry.get("help") or "")
        if expected_type == "boolean":
            parser.add_argument(
                *flags,
                dest=name,
                action="store_true",
                default=bool(default) if default is not None else False,
                help=help_text,
            )
        else:
            kwargs: dict[str, Any] = {
                "dest": name,
                "type": _command_argparse_type(expected_type),
                "required": required,
                "help": help_text,
            }
            if default is not None:
                kwargs["default"] = default
            parser.add_argument(*flags, **kwargs)
    parsed = parser.parse_args(argv)
    values = {
        key: value
        for key, value in vars(parsed).items()
        if value is not None and value != []
    }
    return values


def _render_command_result(result: dict[str, Any]) -> None:
    display = result.get("display")
    if isinstance(display, dict):
        title = display.get("title")
        body = display.get("body")
        if isinstance(title, str) and title:
            print(title)
        if isinstance(body, str) and body:
            print(body)
        return
    print(json.dumps(result, indent=2, sort_keys=True))


def _run_builtin_bundle_command(
    args: argparse.Namespace,
    runtime_layout: RuntimeLayout,
    parser: argparse.ArgumentParser,
) -> None:
    bundle_parser = argparse.ArgumentParser(
        prog=f"{Path(sys.argv[0]).name} bundle",
        description="Build an optimized config-specific Crystal Lattice bundle.",
    )
    bundle_parser.add_argument(
        "--config",
        type=str,
        default=args.config,
        required=args.config is None,
        help="config file used to select preinstalled plugins",
    )
    bundle_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="directory where the optimized bundle archive is written",
    )
    bundle_parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="override version used in artifact names",
    )
    bundle_parser.add_argument(
        "--no-archive",
        action="store_true",
        help="build the optimized bundle directory but do not create an archive",
    )

    bundle_args = bundle_parser.parse_args(list(args.command_args or []))
    bundle_script = runtime_layout.bundle_script
    if runtime_layout.layout != "python-runtime" or bundle_script is None:
        parser.error(
            "the bundle command is only supported from the full bundled-Python "
            "Crystal Lattice package"
        )
    if not bundle_script.is_file():
        parser.error(f"bundle builder script is missing: {bundle_script}")

    config_path = Path(bundle_args.config).expanduser().resolve()
    if not config_path.is_file():
        parser.error(f"bundle config does not exist: {config_path}")

    command = [
        sys.executable,
        str(bundle_script),
        "--config",
        str(config_path),
    ]
    if bundle_args.output:
        command.extend(["--output", str(Path(bundle_args.output).expanduser())])
    if bundle_args.version:
        command.extend(["--version", bundle_args.version])
    if bundle_args.no_archive:
        command.append("--no-archive")

    env = os.environ.copy()
    runtime_root = runtime_layout.manifest_dir.parent.parent.parent
    python_paths = [
        runtime_root / "core" / "python",
        runtime_root / "application" / "python",
    ]
    existing_pythonpath = env.get("PYTHONPATH")
    values = [*(str(path) for path in python_paths)]
    if existing_pythonpath:
        values.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(values)
    try:
        subprocess.run(command, cwd=str(bundle_script.parents[1]), env=env, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc


def _resolve_config_and_session_paths(
    args: argparse.Namespace,
    runtime_layout: RuntimeLayout,
    parser: argparse.ArgumentParser,
) -> tuple[Path, Path]:
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
        if default_local_config.is_file():
            config_path = default_local_config
        elif default_home_config.is_file():
            config_path = default_home_config
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

    return config_path.resolve(), session_root.resolve()


_LOCAL_HEADLESS_COMMANDS = frozenset({"agents", "run", "history"})


def _command_parser(name: str, description: str) -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog=f"crystal-lattice {name}",
        description=description,
    )


def _render_progress_to_stderr(progress: Any) -> None:
    suffix = ""
    if progress.kind == "request_started":
        suffix = f" (session={progress.session_id}, request={progress.request_id})"
    print(f"[{progress.kind}] {progress.message}{suffix}", file=sys.stderr)


def _run_agents_command(
    command_args: list[str],
    *,
    config_path: Path,
    session_root: Path,
    runtime_layout: RuntimeLayout,
    env_overrides: dict[str, str],
) -> None:
    command_parser = _command_parser("agents", "List configured agents")
    command_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
    )
    parsed = command_parser.parse_args(command_args)

    from .local_runtime import open_runtime

    try:
        with redirect_stdout(sys.stderr):
            with open_runtime(
                config_path=config_path,
                session_root=session_root,
                runtime_layout=runtime_layout,
                env_overrides=env_overrides,
            ) as runtime:
                agents = runtime.list_agents()
    except (FileNotFoundError, KeyError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc

    if parsed.format == "json":
        print(json.dumps({"agents": list(agents)}, ensure_ascii=False))
        return
    for agent_id in agents:
        print(agent_id)


def _read_run_prompt(
    parsed: argparse.Namespace,
    command_parser: argparse.ArgumentParser,
) -> str:
    if parsed.prompt is not None:
        prompt = parsed.prompt
    elif parsed.prompt_file is not None:
        try:
            prompt = Path(parsed.prompt_file).expanduser().read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            command_parser.error(f"could not read prompt file: {exc}")
    else:
        try:
            prompt = sys.stdin.read()
        except (OSError, UnicodeError) as exc:
            command_parser.error(f"could not read prompt from stdin: {exc}")
    if not isinstance(prompt, str) or not prompt.strip():
        command_parser.error("prompt must not be empty")
    return prompt


def _run_agent_command(
    command_args: list[str],
    *,
    config_path: Path,
    session_root: Path,
    runtime_layout: RuntimeLayout,
    env_overrides: dict[str, str],
) -> None:
    command_parser = _command_parser(
        "run",
        "Run a configured agent task or continue a persisted session",
    )
    target = command_parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--agent")
    target.add_argument("--session")
    prompt_source = command_parser.add_mutually_exclusive_group(required=True)
    prompt_source.add_argument("--prompt")
    prompt_source.add_argument("--prompt-file")
    prompt_source.add_argument("--stdin", action="store_true")
    command_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
    )
    command_parser.add_argument("--timeout", type=float, default=None)
    command_parser.add_argument("--no-progress", action="store_true")
    parsed = command_parser.parse_args(command_args)
    prompt = _read_run_prompt(parsed, command_parser)

    from .local_runtime import open_runtime

    try:
        with redirect_stdout(sys.stderr):
            with open_runtime(
                config_path=config_path,
                session_root=session_root,
                runtime_layout=runtime_layout,
                env_overrides=env_overrides,
            ) as runtime:
                result = runtime.run(
                    prompt,
                    agent_id=parsed.agent,
                    session_id=parsed.session,
                    timeout=parsed.timeout,
                    on_progress=(
                        None if parsed.no_progress else _render_progress_to_stderr
                    ),
                )
    except KeyboardInterrupt as exc:
        print("Agent request interrupted", file=sys.stderr)
        raise SystemExit(130) from exc
    except (FileNotFoundError, KeyError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc

    if parsed.format == "json":
        print(json.dumps(result.to_dict(), ensure_ascii=False))
    else:
        if result.output_text:
            print(result.output_text)
        print(
            f"[session] {result.session_id} (request={result.request_id})",
            file=sys.stderr,
        )

    if result.status == "succeeded":
        return
    if result.error is not None:
        print(result.error.message, file=sys.stderr)
        if result.error.category == "timeout":
            raise SystemExit(124)
    raise SystemExit(1)


def _render_compact_history_text(history: Any) -> None:
    for message in history.messages:
        flags: list[str] = []
        if message.content_truncated:
            flags.append("truncated")
        if message.content_omitted:
            flags.append("content omitted")
        suffix = f" [{' | '.join(flags)}]" if flags else ""
        print(f"[{message.index}] {message.role}: {message.content}{suffix}")
    if history.omitted_message_count:
        print(
            f"[history] {history.omitted_message_count} earlier selected "
            "message(s) omitted",
            file=sys.stderr,
        )


def _run_history_command(
    command_args: list[str],
    *,
    config_path: Path,
    session_root: Path,
    runtime_layout: RuntimeLayout,
    env_overrides: dict[str, str],
) -> None:
    command_parser = _command_parser(
        "history",
        "Inspect compact session history or one canonical message",
    )
    command_parser.add_argument("--session", required=True)
    command_parser.add_argument("--index", type=int)
    command_parser.add_argument("--start", type=int)
    command_parser.add_argument("--end", type=int)
    command_parser.add_argument(
        "--role",
        action="append",
        choices=["system", "user", "assistant", "tool"],
    )
    command_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
    )
    parsed = command_parser.parse_args(command_args)
    if parsed.index is not None and (
        parsed.start is not None or parsed.end is not None or parsed.role is not None
    ):
        command_parser.error("--index cannot be combined with range or role options")

    from .local_runtime import open_runtime

    try:
        with redirect_stdout(sys.stderr):
            with open_runtime(
                config_path=config_path,
                session_root=session_root,
                runtime_layout=runtime_layout,
                env_overrides=env_overrides,
            ) as runtime:
                if parsed.index is not None:
                    full_message = runtime.get_message(
                        parsed.session,
                        parsed.index,
                    )
                    history = None
                else:
                    full_message = None
                    history = runtime.history(
                        parsed.session,
                        start=parsed.start,
                        end=parsed.end,
                        roles=parsed.role,
                    )
    except (FileNotFoundError, IndexError, KeyError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc

    if full_message is not None:
        if parsed.format == "json":
            print(json.dumps(full_message, ensure_ascii=False))
        else:
            print(json.dumps(full_message, ensure_ascii=False, indent=2))
        return

    assert history is not None
    if parsed.format == "json":
        print(json.dumps(history.to_dict(), ensure_ascii=False))
    else:
        _render_compact_history_text(history)


def _run_local_headless_command(
    command: str,
    command_args: list[str],
    *,
    config_path: Path,
    session_root: Path,
    runtime_layout: RuntimeLayout,
    env_overrides: dict[str, str],
) -> None:
    if command == "agents":
        _run_agents_command(
            command_args,
            config_path=config_path,
            session_root=session_root,
            runtime_layout=runtime_layout,
            env_overrides=env_overrides,
        )
        return
    if command == "run":
        _run_agent_command(
            command_args,
            config_path=config_path,
            session_root=session_root,
            runtime_layout=runtime_layout,
            env_overrides=env_overrides,
        )
        return
    if command == "history":
        _run_history_command(
            command_args,
            config_path=config_path,
            session_root=session_root,
            runtime_layout=runtime_layout,
            env_overrides=env_overrides,
        )
        return
    raise ValueError(f"Unknown local headless command: {command}")


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
        "--host",
        default=None,
        help="host to bind the API server to (default: 0.0.0.0 with --enable-bonjour, else 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="port to bind the API server to (default: auto-selected and persisted)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help=(
            "optional path to a log file; output still goes to stdout. "
            "Defaults to .crystal/crystal.log when not specified."
        ),
    )
    parser.add_argument(
        "--no-log-file",
        action="store_true",
        help="disable default file logging (overrides the default .crystal/crystal.log)",
    )
    parser.add_argument(
        "--no-tty",
        action="store_true",
        help=(
            "run --console in non-interactive mode using pipe input and dummy "
            "output (no TTY required). The full console code path runs (session "
            "creation, event polling); SIGTERM exits cleanly. Useful for CI "
            "and subprocess tests."
        ),
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
        "--enable-bridge",
        action="store_true",
        help=(
            "Enable bridge registration. The bridge URL is resolved from "
            "--bridge-url, .crystal/profile.json, ~/.crystal/projects.json, "
            "or application.bridge_url in config.json."
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
        "--bridge-http-base",
        type=str,
        default=None,
        help=(
            "Public HTTP origin used by the server for bridge v2 body "
            "downloads/uploads (default: derived from --bridge-url)."
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
    parser.add_argument(
        "command",
        nargs="?",
        help=(
            "standalone command such as agents, run, history, bundle, "
            "or a configured application-plugin command"
        ),
    )
    parser.add_argument(
        "command_args",
        nargs=argparse.REMAINDER,
        help=argparse.SUPPRESS,
    )

    args = parser.parse_args()
    runtime_layout = load_runtime_layout()

    if args.command == "bundle":
        _run_builtin_bundle_command(args, runtime_layout, parser)
        return

    if args.runtime_layout_json:
        print(json.dumps(runtime_layout.to_resolved_dict(), indent=2, sort_keys=True))
        return

    if args.command in _LOCAL_HEADLESS_COMMANDS:
        if args.console or args.server:
            parser.error(
                f"{args.command} is a standalone command and cannot be combined "
                "with --console or --server"
            )
        config_path, session_root = _resolve_config_and_session_paths(
            args,
            runtime_layout,
            parser,
        )
        log_file = _resolve_log_file(args)
        _configure_logging(
            log_file,
            log_level=args.log_level,
            disable_structlog_colors=False,
            structlog_output_stream=sys.stderr,
        )
        env_overrides = runtime_layout.env_overrides()
        if args.cloud_orchestrator_url:
            env_overrides["CLOUD_ORCHESTRATOR_URL"] = args.cloud_orchestrator_url
        if args.cloud_orchestrator_token:
            env_overrides["CLOUD_ORCHESTRATOR_TOKEN"] = args.cloud_orchestrator_token
        _run_local_headless_command(
            args.command,
            list(args.command_args or []),
            config_path=config_path,
            session_root=session_root,
            runtime_layout=runtime_layout,
            env_overrides=env_overrides,
        )
        return

    run_server = args.server or not args.console
    run_console = args.console

    # --- Resolve project profile (port, name, bridge-server-id, bridge-url) ---
    user_projects_file = Path.home() / ".crystal" / "projects.json"
    profile_manager = ProjectProfileManager(
        user_file=user_projects_file,
        project_dir=Path.cwd(),
    )
    profile = profile_manager.resolve(
        cli_name=args.bonjour_service_name or args.bridge_display_name,
        cli_port=args.port,
        cli_bridge_server_id=args.bridge_server_id,
        cli_bridge_url=args.bridge_url,
    )

    # --- Resolve effective host and port ---
    effective_host = _resolve_effective_host(args)
    effective_port = profile.port

    # --- Resolve log file ---
    log_file = _resolve_log_file(args)
    fastapi_log_file = _resolve_fastapi_log_file(args, log_file)

    # Configure logging before importing application modules so that
    # any module-level loggers created during import respect the
    # selected level (CLI or environment).
    _configure_logging(
        log_file, log_level=args.log_level, disable_structlog_colors=False
    )
    _configure_fastapi_logging(fastapi_log_file)

    if args.app_name:
        _set_terminal_title(args.app_name)

    console_logger: Optional[logging.Logger] = None
    if log_file:
        console_logger = logging.getLogger("agent_terminal_app.console")

    # Delay imports that pull in agent_app / FastAPI wiring until
    # after logging is configured so that their loggers see the
    # correct level.
    from agent_app.application_future import AgentApplication
    from agent_app.application_notifications import (
        SQLiteApplicationNotificationStore,
        resolve_application_notification_store_path,
    )
    from agent_app.application_owner import AgentApplicationOwner, ApplicationControl
    from agent_app.config import load_resolved_config
    from agent_app.events import InMemoryEventStore
    from agent_app.sessions import FilesystemSnapshotSelectionStore
    from .terminal import TerminalApplication, run_terminal

    import agent_terminal_app.server as server_mod  # type: ignore[import-not-found]

    run_api = server_mod.run_api

    env_overrides = runtime_layout.env_overrides()
    if args.cloud_orchestrator_url:
        env_overrides["CLOUD_ORCHESTRATOR_URL"] = args.cloud_orchestrator_url
    if args.cloud_orchestrator_token:
        env_overrides["CLOUD_ORCHESTRATOR_TOKEN"] = args.cloud_orchestrator_token
    config_path, session_root = _resolve_config_and_session_paths(
        args,
        runtime_layout,
        parser,
    )

    config_env = _collect_additional_dotenv_values(config_path)
    resolved_runtime_config, _config_errors, _resolution_env = load_resolved_config(
        config_path,
        config_env=config_env,
        env_overrides=env_overrides,
    )
    application_notification_store_path = resolve_application_notification_store_path(
        config_path,
        resolved_runtime_config,
    )

    def build_application_owner(
        *,
        event_store: InMemoryEventStore,
        snapshot_selection_store: FilesystemSnapshotSelectionStore | None = None,
    ) -> tuple[AgentApplicationOwner, SQLiteApplicationNotificationStore]:
        first_application = True
        owner_epoch = f"owner_{uuid.uuid4().hex}"
        notification_store = SQLiteApplicationNotificationStore(
            application_notification_store_path,
            owner_epoch=owner_epoch,
        )
        application_config = resolved_runtime_config.get("application")
        notification_config = (
            application_config.get("notifications")
            if isinstance(application_config, dict)
            else None
        )
        raw_history_limit = (
            notification_config.get(
                "history_limit",
                notification_config.get("max_items", 500),
            )
            if isinstance(notification_config, dict)
            else 500
        )
        history_limit = (
            raw_history_limit
            if isinstance(raw_history_limit, int)
            and not isinstance(raw_history_limit, bool)
            and raw_history_limit > 0
            else 500
        )
        notification_store.recover_owner_lifetime(
            owner_epoch,
            history_limit=history_limit,
        )

        def factory(control: ApplicationControl) -> AgentApplication:
            nonlocal first_application
            application = AgentApplication(
                str(config_path),
                str(session_root),
                event_store=event_store,
                application_notification_store=notification_store,
                snapshot_selection_store=snapshot_selection_store,
                config_env=_collect_additional_dotenv_values(config_path),
                env_overrides=env_overrides,
                replay_server_settings_on_startup=first_application,
                application_control=control,
                notification_owner_epoch=owner_epoch,
            )
            first_application = False
            return application

        try:
            owner = AgentApplicationOwner(
                factory,
                event_store=event_store,
                owner_epoch=owner_epoch,
            )
        except Exception:
            notification_store.close()
            raise
        return owner, notification_store

    # --- Build integration config (after config is resolved) ---
    bridge_url_from_config = _read_bridge_url_from_config(config_path)
    integration_config = _build_server_integration_config(
        args,
        server_mod=server_mod,
        profile=profile,
        bridge_url_from_config=bridge_url_from_config,
        effective_host=effective_host,
        effective_port=effective_port,
    )
    if integration_config is not None:
        server_mod.configure_integrations(integration_config)

    contributed_command = (
        args.command if isinstance(args.command, str) and args.command else ""
    )

    if contributed_command:
        print(f"[agent_terminal_app] Using config: {config_path}")
        print(f"[agent_terminal_app] Using sessions dir: {session_root}")

        command_app = AgentApplication(
            str(config_path),
            str(session_root),
            config_env=config_env,
            env_overrides=env_overrides,
        )
        try:
            commands = command_app.get_application_commands()
            command_map = {
                command["name"]: command
                for command in commands
                if isinstance(command, dict) and isinstance(command.get("name"), str)
            }
            command_def = command_map.get(contributed_command)
            if command_def is None:
                parser.error(f"unknown command: {contributed_command}")

            if args.console or args.server:
                parser.error(
                    f"{contributed_command} is a standalone command and cannot be combined "
                    "with --console or --server"
                )

            action_id = command_def.get("action_id")
            plugin_id = command_def.get("plugin")
            if not isinstance(action_id, str) or not action_id:
                parser.error(f"command {contributed_command!r} is missing action_id")
            if not isinstance(plugin_id, str) or not plugin_id:
                parser.error(
                    f"command {contributed_command!r} is missing plugin binding"
                )

            action_def = _application_action_map(command_app).get(
                (plugin_id, action_id)
            )
            if action_def is None:
                parser.error(
                    f"command {contributed_command!r} references unknown action {plugin_id}.{action_id}"
                )

            params = _parse_contributed_command(
                command_def,
                action_def,
                list(args.command_args or []),
            )
            try:
                result = command_app.execute_application_action(
                    plugin_id=plugin_id,
                    action_id=action_id,
                    params=params,
                )
            except Exception as exc:
                print(str(exc), file=sys.stderr)
                raise SystemExit(1) from exc
            _render_command_result(result)
            return
        finally:
            command_app.close()

    # --- Consolidated startup summary (server/console modes only) ---
    lan_ip = get_local_ip() if effective_host == "0.0.0.0" else None
    bonjour_name = (
        integration_config.bonjour.service_name
        if integration_config is not None and integration_config.bonjour is not None
        else None
    )
    bridge_url_for_summary = (
        integration_config.bridge.bridge_url
        if integration_config is not None and integration_config.bridge is not None
        else None
    )
    print(
        _format_startup_summary(
            project_name=profile.name,
            config_path=config_path,
            session_root=session_root,
            host=effective_host,
            port=effective_port,
            bonjour_service_name=bonjour_name,
            bridge_url=bridge_url_for_summary,
            lan_ip=lan_ip,
        )
    )

    # Modes:
    # - default (no flags): server only
    # - --console: console only
    # - --console --server: server in background + console in foreground
    if run_console and run_server:
        shared_events = InMemoryEventStore()
        application_owner, application_notification_store = build_application_owner(
            event_store=shared_events,
            snapshot_selection_store=FilesystemSnapshotSelectionStore(
                session_root / ".snapshots"
            ),
        )
        terminal_app = TerminalApplication(
            config_path=str(config_path),
            session_root=str(session_root),
            application_owner=application_owner,
        )

        try:
            import uvicorn  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - optional dependency
            parser.error(
                f"Uvicorn is required for --server mode but could not be imported: {exc}"
            )

        server_mod.configure_application_owner(application_owner)

        os.environ.setdefault("SERVER_HOST", effective_host)
        os.environ.setdefault("SERVER_PORT", str(effective_port))

        from uvicorn.config import LOGGING_CONFIG  # type: ignore[import-not-found]

        config = uvicorn.Config(
            "agent_terminal_app.server:app",
            host=effective_host,
            port=effective_port,
            reload=False,
            log_config=None if fastapi_log_file else LOGGING_CONFIG,
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
            if args.no_tty:
                _run_terminal_headless(terminal_app, console_logger)
            else:
                run_terminal(logger=console_logger, app_instance=terminal_app)
        finally:
            uvicorn_server.should_exit = True
            thread.join()
            terminal_app.close()
            application_owner.close()
            application_notification_store.close()
    elif run_console:
        application_owner, application_notification_store = build_application_owner(
            event_store=InMemoryEventStore(),
        )
        terminal_app = TerminalApplication(
            config_path=str(config_path),
            session_root=str(session_root),
            application_owner=application_owner,
        )
        try:
            if args.no_tty:
                _run_terminal_headless(terminal_app, console_logger)
            else:
                run_terminal(logger=console_logger, app_instance=terminal_app)
        finally:
            terminal_app.close()
            application_owner.close()
            application_notification_store.close()
    else:
        application_owner, application_notification_store = build_application_owner(
            event_store=InMemoryEventStore(),
            snapshot_selection_store=FilesystemSnapshotSelectionStore(
                session_root / ".snapshots"
            ),
        )
        try:
            run_api(
                host=effective_host,
                port=effective_port,
                app_owner=application_owner,
                log_config=None if fastapi_log_file else "default",
            )
        finally:
            application_notification_store.close()


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()
