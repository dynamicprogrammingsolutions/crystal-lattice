"""
Integration-style test for Example 12: OpenRouter + tools + reasoning.

This test sets up a tiny coding puzzle in a temporary directory and
uses the Example 12 application layer (OpenRouter provider with
FileReaderTool and FileWriterTool) to fix the code.

The assertion only checks that the puzzle's own test function
(`puzzle_main.run_tests`) runs without error on the modified code.
"""

import os
import sys
from pathlib import Path

import pytest

try:  # Load .env from the current working directory (repo root in tests)
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
CORE_PY = os.path.join(ROOT, "core/python")
if CORE_PY not in sys.path:
    sys.path.insert(0, CORE_PY)


@pytest.fixture(scope="module")
def ensure_api_key() -> None:
    """Skip if OpenRouter API key is not configured."""

    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set; skipping Example 12 OpenRouter test")


@pytest.fixture
def puzzle_dir(tmp_path: Path) -> Path:
    """Create a very small coding puzzle spread across two files.

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
        """from puzzle_a import add\nfrom puzzle_b import multiply\n\n\ndef run_tests() -> None:\n    # Very small sanity checks that must pass after the model edits\n    assert add(1, 2) == 3\n    assert multiply(2, 3) == 6\n    print(\"OK\")\n""",
        encoding="utf-8",
    )

    return tmp_path


@pytest.mark.openrouter
def test_example12_openrouter_tools_puzzle(ensure_api_key: None, puzzle_dir: Path) -> None:
    """Solve a tiny coding puzzle via Example 12 using tools.

    The model is instructed to use the read_file and write_file tools to
    inspect and update puzzle_a.py and puzzle_b.py so that
    puzzle_main.run_tests() passes. The assertion only checks that
    run_tests() runs without raising.
    """

    # Make the puzzle directory importable so puzzle_main can be imported
    sys.path.insert(0, str(puzzle_dir))

    try:
        mod = __import__(
            "examples.example12_openrouter_tools_app",
            fromlist=["create_session", "add_message", "send_request"],
        )
    except Exception as exc:  # pragma: no cover - import failure
        pytest.skip(f"Could not import example12_openrouter_tools_app: {exc}")

    create_session = getattr(mod, "create_session")
    add_message = getattr(mod, "add_message")
    send_request = getattr(mod, "send_request")

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

    created = create_session({"system_message": system_message})
    session = created["session"]
    session_id = session["session_id"]

    add_message(session_id, {"role": "user", "content": user_message})

    # Allow the application to run a small tool loop. We only override
    # filesystem-related configuration; OpenRouter model/api_key come
    # from the environment.
    result = send_request(
        session_id,
        {
            "config_overrides": {
                "allowed_paths": [str(puzzle_dir)],
                "working_directory": str(puzzle_dir),
            },
            "max_loops": 6,
        },
    )

    # Regardless of what the model replied, the puzzle is considered
    # solved if puzzle_main.run_tests() passes after its edits.
    import importlib

    puzzle_main = importlib.import_module("puzzle_main")
    puzzle_main.run_tests()

    # If run_tests() raises, the test fails; otherwise we are done.

    # Clean up sys.path entry
    sys.path = [p for p in sys.path if p != str(puzzle_dir)]
