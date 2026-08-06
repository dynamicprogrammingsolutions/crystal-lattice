from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from agent_eval import ArtifactWriter, EvidenceJournal


def test_evidence_projection_records_result() -> None:
    journal = EvidenceJournal()
    journal.emit("value", 2, source="test")

    projected = journal.project(
        "double",
        using=lambda evidence: cast(int, evidence.require("value")) * 2,
    )

    assert projected == 4
    assert journal.require("projection.double") == 4


def test_artifact_writer_rejects_path_escape(tmp_path: Path) -> None:
    writer = ArtifactWriter(tmp_path / "artifacts")

    with pytest.raises(ValueError, match="escapes root"):
        writer.write_text("../outside.txt", "not allowed")


def test_run_record_writes_json_and_text(tmp_path: Path) -> None:
    writer = ArtifactWriter(tmp_path / "artifacts")

    text_path = writer.record("note", "hello")
    json_path = writer.record("score", {"value": 4})

    assert text_path.name == "note.md"
    assert text_path.read_text(encoding="utf-8") == "hello\n"
    assert json_path.name == "score.json"
    assert '"value": 4' in json_path.read_text(encoding="utf-8")