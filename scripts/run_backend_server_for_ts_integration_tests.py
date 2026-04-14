"""Run the FastAPI backend for TypeScript integration tests.

This script is intended to be spawned by Vitest/Jest integration tests.
It boots the real `agent_terminal_app.server` FastAPI app, but injects a
custom `AgentApplication` instance using a provided config + session root.

The goal is a deterministic, hermetic backend for end-to-end tests that
exercise:

- Python plugins (providers, features)
- Session persistence and event store semantics
- The TypeScript SDK (`RestAgentBackend`, `ChatController`)

Usage:

  python scripts/run_backend_server_for_ts_integration_tests.py \
    --config /path/to/config.json \
    --sessions /tmp/sessions \
    --port 9010
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _add_repo_paths() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    core_python = repo_root / "core" / "python"
    application_python = repo_root / "application" / "python"

    sys.path.insert(0, str(core_python))
    sys.path.insert(0, str(application_python))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--sessions", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--log-level", default="warning")
    parser.add_argument("--max-events-global", type=int)
    parser.add_argument("--max-event-age-seconds", type=float)
    parser.add_argument(
        "--enable-test-control",
        action="store_true",
        help="Enable backend test-control endpoints (C1).",
    )
    args = parser.parse_args()

    _add_repo_paths()

    if args.enable_test_control:
        os.environ["AGENT_APP_TEST_CONTROL"] = "1"

    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    from agent_terminal_app import server as server_mod

    config_path = Path(args.config).expanduser().resolve()
    sessions_root = Path(args.sessions).expanduser().resolve()
    sessions_root.mkdir(parents=True, exist_ok=True)

    server_mod._agent_app = AgentApplication(
        str(config_path),
        str(sessions_root),
        event_store=InMemoryEventStore(
            max_events_global=args.max_events_global,
            max_event_age_seconds=args.max_event_age_seconds,
        ),
    )

    import uvicorn

    uvicorn.run(
        server_mod.app,
        host=args.host,
        port=int(args.port),
        log_level=args.log_level,
        access_log=False,
    )


if __name__ == "__main__":
    main()
