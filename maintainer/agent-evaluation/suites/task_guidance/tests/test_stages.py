"""Stage-catalog well-formedness tests.

The catalog in :mod:`stages` defines the fixed meaning of every stage the
configuration can select: the workspace a run starts from, the earlier
stage whose workspace and session prefix a run shares, the expansion, the
config schema, the executor, and the record file. These tests check the
catalog's internal consistency; the configuration tests check that the
manifest selects from it, and the runner tests check that every executor
exists on the harness.
"""

from __future__ import annotations

from ..stages import STAGES


def test_every_entry_name_matches_its_key() -> None:
    for name, spec in STAGES.items():
        assert spec.name == name


def test_parent_linkages_reference_declared_stages() -> None:
    for spec in STAGES.values():
        if spec.parent is not None:
            assert spec.parent in STAGES, spec.parent
            assert spec.parent != spec.name


def test_continuation_is_the_only_stage_sharing_an_earlier_run() -> None:
    with_parent = {spec.name for spec in STAGES.values() if spec.parent}
    assert with_parent == {"continuation"}
    assert STAGES["continuation"].parent == "task-creation"
    assert STAGES["continuation"].workspace == "parent"


def test_record_files_are_unique_per_stage() -> None:
    records = [spec.record for spec in STAGES.values()]
    assert len(records) == len(set(records))
    for record in records:
        assert record.startswith("task-guidance-") and record.endswith(".json")


def test_every_stage_declares_its_expansion_and_workspace() -> None:
    for spec in STAGES.values():
        assert spec.workspace
        assert spec.runs_per
        assert spec.executor
