from pathlib import Path

from .artifacts import record_paths


def test_record_paths_reads_records_without_descending_into_workspaces(
    tmp_path: Path,
) -> None:
    expected = (
        tmp_path
        / "glm"
        / "runs"
        / "run-1"
        / "records"
        / "task-guidance-producer.json"
    )
    expected.parent.mkdir(parents=True)
    expected.write_text("{}\n", encoding="utf-8")
    transient = tmp_path / "glm" / "runs" / "run-2" / "workspace"
    transient.mkdir(parents=True)
    transient.joinpath("ignored.json").write_text("{}\n", encoding="utf-8")

    assert record_paths(
        tmp_path,
        "task-guidance-producer.json",
    ) == (expected,)