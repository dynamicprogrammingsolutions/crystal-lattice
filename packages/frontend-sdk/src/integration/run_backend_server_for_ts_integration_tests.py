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

  python packages/frontend-sdk/src/integration/run_backend_server_for_ts_integration_tests.py \
    --config /path/to/config.json \
    --sessions /tmp/sessions \
    --port 9010
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
import time


def _add_repo_paths() -> None:
    repo_root = Path(__file__).resolve().parents[4]
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
    parser.add_argument("--session-save-delay-ms", type=int, default=0)
    parser.add_argument("--checkpoint-delay-ms", type=int, default=0)
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

    from agent_terminal_app.__main__ import _collect_additional_dotenv_values
    from agent_terminal_app import server as server_mod

    class DelayingSessionStore:
        def __init__(self, inner: object, *, save_delay_seconds: float) -> None:
            self._inner = inner
            self._save_delay_seconds = save_delay_seconds

        def load(self, session_id: str):
            return self._inner.load(session_id)  # type: ignore[attr-defined]

        def save(self, session) -> None:
            time.sleep(self._save_delay_seconds)
            self._inner.save(session)  # type: ignore[attr-defined]

        def delete(self, session_id: str) -> None:
            self._inner.delete(session_id)  # type: ignore[attr-defined]

        def get_file_state(self, session_id: str):
            return self._inner.get_file_state(session_id)  # type: ignore[attr-defined]

        def save_backup(self, session, *, request_id: str, suffix: str = "tool-loop-conflict"):
            return self._inner.save_backup(  # type: ignore[attr-defined]
                session,
                request_id=request_id,
                suffix=suffix,
            )

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
        # Mirror the terminal app entrypoint so TS integration tests exercise
        # normal config-adjacent and current-directory dotenv resolution.
        config_env=_collect_additional_dotenv_values(config_path),
    )
    if args.session_save_delay_ms > 0:
        server_mod._agent_app._session_store = DelayingSessionStore(  # type: ignore[attr-defined]
            server_mod._agent_app._session_store,  # type: ignore[attr-defined]
            save_delay_seconds=float(args.session_save_delay_ms) / 1000.0,
        )
    if args.checkpoint_delay_ms > 0:
        original_record_checkpoint = server_mod._agent_app.record_checkpoint

        def _delayed_record_checkpoint(session_id: str, request_id: str | None):
            time.sleep(float(args.checkpoint_delay_ms) / 1000.0)
            return original_record_checkpoint(session_id, request_id)

        server_mod._agent_app.record_checkpoint = _delayed_record_checkpoint  # type: ignore[assignment]

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
