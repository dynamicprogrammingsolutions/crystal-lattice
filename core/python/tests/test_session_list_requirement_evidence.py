from __future__ import annotations

import runpy
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
REQUIREMENTS = (
    ROOT / "core/python/docs/development/specifications/session-listing/requirements.md"
)
EVIDENCE_TESTS = (
    ROOT / "application/python/tests/test_session_listing_requirements_integration.py",
    ROOT / "application/python/tests/test_session_data_query_http.py",
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


def test_session_list_requirement_evidence_rejects_unmarked_tests(
    tmp_path: Path,
) -> None:
    updater = runpy.run_path(
        str(ROOT / "scripts/update_session_list_requirement_evidence.py")
    )
    test_path = tmp_path / "test_unmarked.py"
    test_path.write_text(
        "\n".join(
            (
                "# Requirements:",
                "# - SLIST-001: This must not count as integration evidence.",
                "def test_unmarked() -> None:",
                "    pass",
                "",
            )
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not marked pytest.mark.integration"):
        updater["_parse_test_evidence"](test_path)
