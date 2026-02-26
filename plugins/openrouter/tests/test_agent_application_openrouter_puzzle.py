"""OpenRouter tools integration test via AgentApplication.

This is a light end-to-end test that exercises:

- OpenRouter provider
- OpenRouter tools extension
- FileReaderTool + FileWriterTool
- The AgentApplication tool loop

Requires ``OPENROUTER_API_KEY``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import os
import runpy

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


@pytest.fixture(scope="module")
def ensure_api_key() -> None:
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter integration test")


@pytest.fixture
def puzzle_dir(tmp_path: Path) -> Path:
    a = tmp_path / "puzzle_a.py"
    b = tmp_path / "puzzle_b.py"
    main = tmp_path / "puzzle_main.py"

    a.write_text(
        """def add(a, b):\n    # BUG: should add but subtracts\n    return a - b\n""",
        encoding="utf-8",
    )
    b.write_text(
        """def multiply(a, b):\n    # BUG: should multiply but adds\n    return a + b\n""",
        encoding="utf-8",
    )
    main.write_text(
        """from puzzle_a import add\nfrom puzzle_b import multiply\n\n\n"""
        """def run_tests() -> None:\n"""
        """    assert add(1, 2) == 3\n"""
        """    assert multiply(2, 3) == 6\n"""
        """    print('OK')\n""",
        encoding="utf-8",
    )

    return tmp_path


def _make_config(tmp_path: Path, *, working_directory: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "openrouter": {
                "provider": "openrouter",
                "model": "openai/gpt-5-mini",
                "api_key": OPENROUTER_API_KEY,
                "base_url": "https://openrouter.ai/api/v1",
                "timeout": 120,
                "allowed_paths": [str(working_directory)],
                "working_directory": str(working_directory),
            }
        },
        "plugins": [
            "openrouter_plugins.openrouter_provider.OpenRouterProvider",
            "openrouter_plugins.openrouter_tools_extension.OpenRouterToolsExtension",
            "plugins.file_reader_tool.FileReaderTool",
            "plugins.file_writer_tool.FileWriterTool",
        ],
        "agents": {"default": {"provider": "openrouter"}},
    }

    path = tmp_path / "config_openrouter_puzzle.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


@pytest.mark.openrouter
@pytest.mark.integration
def test_openrouter_puzzle_fixed_via_tools(ensure_api_key: None, puzzle_dir: Path) -> None:
    config_path = _make_config(puzzle_dir, working_directory=puzzle_dir)
    session_root = puzzle_dir / "sessions"
    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    system_message = (
        "You are a coding assistant. Use the read_file and write_file tools "
        "to inspect and modify Python files. Do not change puzzle_main.py; "
        "only edit puzzle_a.py and puzzle_b.py so that run_tests() passes."
    )
    user_message = (
        f"In directory {puzzle_dir}, there are puzzle_a.py, puzzle_b.py, and puzzle_main.py. "
        "puzzle_main.run_tests() currently fails. Use the tools to read the "
        "files and then update puzzle_a.py and puzzle_b.py so that "
        "run_tests() passes. When you are done, reply with exactly 'READY'."
    )

    session = core.add_message(session, "system", system_message, metadata=None, config=base_config)
    session = core.add_message(session, "user", user_message, metadata=None, config=base_config)
    app.save_session(session)

    events_out = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    checkpoints = [ev for ev in events_out if ev.get("type") == "session_checkpoint"]
    assert checkpoints, "expected at least one session_checkpoint"
    final_session = checkpoints[-1]["session"]
    app.save_session(final_session)

    finals = [ev for ev in events_out if ev.get("type") == "final"]
    assert finals, "expected a final event"
    last_final = finals[-1]
    messages = last_final.get("messages") or []
    assistants = [m for m in messages if isinstance(m, dict) and m.get("role") == "assistant"]
    assert assistants, "expected an assistant message"
    assert "READY" in str(assistants[-1].get("content") or "")

    ns = runpy.run_path(str(puzzle_dir / "puzzle_main.py"))
    run_tests = ns.get("run_tests")
    assert callable(run_tests)
    run_tests()
