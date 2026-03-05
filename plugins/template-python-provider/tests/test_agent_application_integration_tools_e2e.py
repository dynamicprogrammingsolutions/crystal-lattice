from __future__ import annotations

import os
import runpy
from pathlib import Path
from typing import Any, Dict, List

import pytest

import provider_test_config as cfg
from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


pytestmark = [pytest.mark.integration]


def _require_api_key() -> str:
    api_key_env = cfg.API_KEY_ENV_VAR
    if not api_key_env:
        pytest.skip("API_KEY_ENV_VAR is not set in provider_test_config.py")
    value = os.getenv(api_key_env)
    if not value:
        pytest.skip(f"{api_key_env} is not set")
    return value


def _make_app_config(tmp_path: Path, *, working_directory: Path) -> Path:
    if not cfg.PROVIDER_CLASS_PATH:
        pytest.skip("PROVIDER_CLASS_PATH is not set in provider_test_config.py")
    if not cfg.MODEL:
        pytest.skip("MODEL is not set in provider_test_config.py")
    if not cfg.TOOLS_EXTENSION_CLASS_PATH:
        pytest.skip("TOOLS_EXTENSION_CLASS_PATH is not set in provider_test_config.py")

    provider_cfg: Dict[str, Any] = {
        # Use the fully-qualified class path to avoid depending on the provider's short name.
        "provider": cfg.PROVIDER_CLASS_PATH,
        "model": cfg.MODEL,
        "timeout": getattr(cfg, "TIMEOUT", 120),
        "allowed_paths": [str(working_directory)],
        "working_directory": str(working_directory),
        "max_file_size": 1024 * 1024,
    }

    provider_cfg["api_key"] = _require_api_key()
    if cfg.BASE_URL:
        provider_cfg["base_url"] = cfg.BASE_URL

    extra = getattr(cfg, "EXTRA_CONFIG", None)
    if isinstance(extra, dict) and extra:
        provider_cfg.update(extra)

    # Force sandbox-related fields for this test after applying extras.
    provider_cfg["allowed_paths"] = [str(working_directory)]
    provider_cfg["working_directory"] = str(working_directory)

    plugins: List[str] = [
        cfg.PROVIDER_CLASS_PATH,
        cfg.TOOLS_EXTENSION_CLASS_PATH,
        "plugins.file_reader_tool.FileReaderTool",
        "plugins.file_writer_tool.FileWriterTool",
    ]

    for p in getattr(cfg, "FEATURE_CLASS_PATHS", []) or []:
        if isinstance(p, str) and p:
            plugins.append(p)

    app_cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {"under_test": provider_cfg},
        "plugins": plugins,
        "agents": {"default": {"provider": "under_test"}},
    }

    config_path = tmp_path / "config_provider_e2e.json"
    config_path.write_text(__import__("json").dumps(app_cfg), encoding="utf-8")
    return config_path


@pytest.mark.xfail(
    reason="Integration scaffold: remove xfail once your provider passes this test",
    strict=True,
)
def test_agent_application_tool_loop_puzzle(tmp_path: Path) -> None:
    # Write a tiny puzzle the model can fix using read_file + write_file.
    puzzle_dir = tmp_path / "puzzle"
    puzzle_dir.mkdir(parents=True, exist_ok=True)

    a = puzzle_dir / "puzzle_a.py"
    b = puzzle_dir / "puzzle_b.py"
    main = puzzle_dir / "puzzle_main.py"

    a.write_text(
        """def add(a, b):\n    # BUG: should add but subtracts\n    return a - b\n""",
        encoding="utf-8",
    )
    b.write_text(
        """def multiply(a, b):\n    # BUG: should multiply but adds\n    return a + b\n""",
        encoding="utf-8",
    )
    main.write_text(
        "from puzzle_a import add\nfrom puzzle_b import multiply\n\n\n"
        "def run_tests() -> None:\n"
        "    assert add(1, 2) == 3\n"
        "    assert multiply(2, 3) == 6\n"
        "    print('OK')\n",
        encoding="utf-8",
    )

    config_path = _make_app_config(tmp_path, working_directory=puzzle_dir)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    core, base_config, session = app.create_session("default")

    system_message = (
        "You are a coding assistant. Use the read_file and write_file tools "
        "to inspect and modify Python files. Do not change puzzle_main.py; "
        "only edit puzzle_a.py and puzzle_b.py so that run_tests() passes. "
        "When you are done, reply with exactly 'READY'."
    )
    user_message = (
        f"In directory {puzzle_dir}, there are puzzle_a.py, puzzle_b.py, and puzzle_main.py. "
        "puzzle_main.run_tests() currently fails. Use the tools to read the "
        "files and then update puzzle_a.py and puzzle_b.py so that "
        "run_tests() passes."
    )

    session = core.add_message(session, "system", system_message, metadata=None, config=base_config)
    session = core.add_message(session, "user", user_message, metadata=None, config=base_config)
    app.save_session(session)

    events_out = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    finals = [ev for ev in events_out if ev.get("type") == "final"]
    assert finals, "expected at least one final event"

    last_final = finals[-1]
    messages = last_final.get("messages") or []
    assistants = [m for m in messages if isinstance(m, dict) and m.get("role") == "assistant"]
    assert assistants, "expected an assistant message"
    assert "READY" in str(assistants[-1].get("content") or "")

    ns = runpy.run_path(str(puzzle_dir / "puzzle_main.py"))
    run_tests = ns.get("run_tests")
    assert callable(run_tests)
    run_tests()
