from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
REQUIREMENTS = (
    ROOT / "core/python/docs/development/specifications/session-listing/requirements.md"
)
EVIDENCE_TESTS = (
    ROOT / "core/python/tests/test_application_session_listing.py",
    ROOT / "core/python/tests/test_application_session_filters.py",
    ROOT / "core/python/tests/test_session_list_cache.py",
    ROOT / "application/python/tests/test_session_list_http_contract.py",
    ROOT / "application/python/tests/test_agent_terminal_app_server.py",
)


def test_session_list_requirement_test_evidence_is_current() -> None:
    command = [
        sys.executable,
        str(ROOT / "scripts/update_session_list_requirement_evidence.py"),
        "--check",
        "--requirements",
        str(REQUIREMENTS),
    ]
    for test_path in EVIDENCE_TESTS:
        command.extend(("--test", str(test_path)))

    subprocess.run(command, check=True)
