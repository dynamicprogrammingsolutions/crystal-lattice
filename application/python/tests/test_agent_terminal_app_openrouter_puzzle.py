"""OpenRouter integration test for agent_terminal_app.

This test mirrors the Example 13 OpenRouter tools app-layer test but
uses the agent_terminal_app FastAPI-style functions instead of the
examples module.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

try:  # Load .env from the repo root
    from dotenv import load_dotenv

    # Repo root is three levels up from this tests module
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    load_dotenv(os.path.join(ROOT, ".env"))
except Exception:
    pass

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
APP_PY = os.path.join(ROOT, "application/python")
if APP_PY not in sys.path:
    sys.path.insert(0, APP_PY)
CORE_PY = os.path.join(ROOT, "core/python")
if CORE_PY not in sys.path:
    sys.path.insert(0, CORE_PY)


@pytest.fixture(scope="module")
def ensure_api_key() -> None:
    """Skip if OpenRouter API key is not configured."""

    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter integration test")


@pytest.fixture
def puzzle_dir(tmp_path: Path) -> Path:
    """Create a small coding puzzle across a few files.

    Files:
      - puzzle_a.py: broken add(a, b)
      - puzzle_b.py: broken multiply(a, b)
      - puzzle_main.py: run_tests() asserting correct behaviour
    """

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
        """from puzzle_a import add\nfrom puzzle_b import multiply\n\n\ndef run_tests() -> None:\n    # Very small sanity checks that must pass after the model edits\n    assert add(1, 2) == 3\n    assert multiply(2, 3) == 6\n    print("OK")\n""",
        encoding="utf-8",
    )

    return tmp_path


@pytest.mark.openrouter
def test_agent_terminal_app_openrouter_puzzle(ensure_api_key: None, puzzle_dir: Path) -> None:
    """Solve a tiny coding puzzle via agent_terminal_app using tools."""

    # Make the puzzle directory importable so puzzle_main can be imported
    sys.path.insert(0, str(puzzle_dir))

    try:
        from agent_terminal_app import server as app_mod
        from agent_terminal_app.server import ServerApplication
    except Exception as exc:  # pragma: no cover - import failure
        pytest.skip(f"Could not import agent_terminal_app.server: {exc}")

    base_dir = Path(app_mod.__file__).resolve().parent
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = puzzle_dir / "sessions"
    app = ServerApplication(config_path=config_path, session_root=session_root)

    system_message = (
        "You are a coding assistant. Use the read_file and write_file tools "
        "to inspect and modify Python files. Do not change puzzle_main.py; "
        "only edit puzzle_a.py and puzzle_b.py so that run_tests() passes."
    )
    user_message = (
        "In directory "
        f"{puzzle_dir}, there are puzzle_a.py, puzzle_b.py, and puzzle_main.py. "
        "puzzle_main.run_tests() currently fails. Use the tools to read the "
        "files and then update puzzle_a.py and puzzle_b.py so that "
        "run_tests() passes. When you are done, reply with exactly 'READY'."
    )

    session = app.create_session(agent_id="default", system_message=system_message)
    session_id = session.session_id

    app.add_message(session_id, role="user", content=user_message, metadata=None)

    final_session_dict, messages, request_id = app.send_request(
        session_id,
        overrides={
            "allowed_paths": [str(puzzle_dir)],
            "working_directory": str(puzzle_dir),
        },
        stream=True,
    )

    # Regardless of what the model replied, the puzzle is considered
    # solved if puzzle_main.run_tests() passes after its edits.
    import importlib

    puzzle_main = importlib.import_module("puzzle_main")
    puzzle_main.run_tests()

    # Clean up sys.path entry
    sys.path = [p for p in sys.path if p != str(puzzle_dir)]
