"""Consolidation core tests: label selection, samples, aggregation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agent_eval.runner import (
    aggregate_metric,
    cell_statistics,
    completeness,
    record_paths,
    render_selection,
    select_cell_records,
)

from fixtures.run_model_scenario import (
    MINI_AGENTS,
    PRODUCER_RECORD_NAME,
    MiniHarness,
    producer_cell,
)


def _cells(artifact_root: Path, **kwargs: Any) -> dict[str, tuple[Any, ...]]:
    return select_cell_records(
        artifact_root,
        record_name=PRODUCER_RECORD_NAME,
        cell_identity=producer_cell,
        **kwargs,
    )


def _produce_all(harness: MiniHarness) -> None:
    for scenario in ("mini-one", "mini-two"):
        for agent in MINI_AGENTS:
            for effort in MINI_AGENTS[agent].efforts:
                harness.produce(agent=agent, scenario=scenario, effort=effort)


class TestLabelSelection:
    def test_default_selection_takes_the_latest_label_per_cell(
        self, tmp_path: Path
    ) -> None:
        first = MiniHarness(tmp_path, label="batch-a")
        _produce_all(first)
        first.close()
        second = MiniHarness(tmp_path, label="batch-b")
        second.produce(agent="alpha", scenario="mini-one", effort="low", fresh=True)
        second.close()

        cells = _cells(tmp_path)

        assert len(cells) == 6
        late_cell = "mini-one:alpha:low"
        assert {record.label for record in cells[late_cell]} == {"batch-b"}
        early_cell = "mini-one:alpha:high"
        assert {record.label for record in cells[early_cell]} == {"batch-a"}

    def test_explicit_labels_select_all_samples(self, tmp_path: Path) -> None:
        first = MiniHarness(tmp_path, label="batch-a")
        first.produce(agent="alpha", scenario="mini-one", effort="low")
        first.close()
        second = MiniHarness(tmp_path, label="batch-b", environments=first.environments)
        second.produce(agent="alpha", scenario="mini-one", effort="low", fresh=True)
        second.close()

        cells = _cells(tmp_path, labels=("batch-a", "batch-b"))

        cell = cells["mini-one:alpha:low"]
        assert [record.label for record in cell] == ["batch-a", "batch-b"]
        assert len({record.value["response"] for record in cell}) == 2

    def test_replays_do_not_duplicate_samples(self, tmp_path: Path) -> None:
        harness = MiniHarness(tmp_path, label="batch-a")
        harness.produce(agent="alpha", scenario="mini-one", effort="low")
        harness.produce(agent="alpha", scenario="mini-one", effort="low")
        harness.close()

        cells = _cells(tmp_path)

        cell = cells["mini-one:alpha:low"]
        assert len(cell) == 1
        assert cell[0].cache_hit is False

    def test_records_without_labels_are_skipped(self, tmp_path: Path) -> None:
        harness = MiniHarness(tmp_path, label="batch-a")
        harness.produce(agent="alpha", scenario="mini-one", effort="low")
        harness.close()
        record_path = record_paths(tmp_path / "artifacts", PRODUCER_RECORD_NAME)[0]
        record_path.parent.joinpath("run-model.json").unlink()

        cells = _cells(tmp_path)

        assert cells == {}

    def test_legacy_attempt_records_are_selectable_as_labels(
        self, tmp_path: Path
    ) -> None:
        # Historical datasets embed the legacy attempt field; the core
        # treats it as the run label so old runs stay selectable.
        root = tmp_path / "artifacts"
        import os

        for index, (scenario, response) in enumerate(
            (
                ("mini-one", "legacy-mini-one"),
                ("mini-two", "legacy-mini-two"),
                ("mini-two", "legacy-mini-two-rerun"),
            )
        ):
            records_dir = root / "runs" / f"legacy-run-{index}" / "records"
            records_dir.mkdir(parents=True)
            record = {
                "schema": 1,
                "scenario": scenario,
                "agent": "alpha",
                "effort": "low",
                "response": response,
                "run_attempt": "legacy-attempt",
            }
            record_path = records_dir / PRODUCER_RECORD_NAME
            record_path.write_text(json.dumps(record), encoding="utf-8")
            stamp = 1_000_000_000 + index
            os.utime(record_path, (stamp, stamp))

        selected = _cells(root, labels=("legacy-attempt",))

        assert set(selected) == {"mini-one:alpha:low", "mini-two:alpha:low"}
        for samples in selected.values():
            assert len(samples) == 1
            assert samples[0].label == "legacy-attempt"
        assert (
            selected["mini-two:alpha:low"][0].value["response"]
            == "legacy-mini-two-rerun"
        )


class TestAggregation:
    def test_multi_label_statistics_aggregate_with_spread_and_provenance(
        self, tmp_path: Path
    ) -> None:
        first = MiniHarness(tmp_path, label="batch-a")
        first.produce(agent="alpha", scenario="mini-one", effort="low")
        first.close()
        second = MiniHarness(tmp_path, label="batch-b", environments=first.environments)
        second.produce(agent="alpha", scenario="mini-one", effort="low", fresh=True)
        second.close()

        cells = _cells(tmp_path, labels=("batch-a", "batch-b"))
        statistics = cell_statistics(cells, metric=lambda value: value["score"])

        entry = statistics["mini-one:alpha:low"]
        values = [sample["value"] for sample in entry["samples"]]
        assert entry["count"] == 2
        assert entry["mean"] == sum(values) / len(values)
        assert entry["spread"] == max(values) - min(values)
        assert entry["spread"] > 0
        assert entry["min"] == min(values)
        assert entry["max"] == max(values)
        assert [sample["label"] for sample in entry["samples"]] == [
            "batch-a",
            "batch-b",
        ]
        assert all(sample["run_id"] for sample in entry["samples"])

    def test_single_sample_statistics_match_historical_behavior(
        self, tmp_path: Path
    ) -> None:
        harness = MiniHarness(tmp_path, label="batch-a")
        harness.produce(agent="alpha", scenario="mini-one", effort="low")
        harness.close()

        cells = _cells(tmp_path)
        statistics = cell_statistics(cells, metric=lambda value: value["score"])

        entry = statistics["mini-one:alpha:low"]
        assert entry["count"] == 1
        assert entry["spread"] == 0.0
        assert entry["min"] == entry["max"] == entry["mean"]

    def test_aggregate_metric_requires_values(self) -> None:
        with pytest.raises(ValueError):
            aggregate_metric([])

    def test_samples_within_one_label_are_kept(self, tmp_path: Path) -> None:
        harness = MiniHarness(tmp_path, label="batch-a")
        harness.produce(agent="alpha", scenario="mini-one", effort="low", samples=3)
        harness.close()

        cells = _cells(tmp_path)

        cell = cells["mini-one:alpha:low"]
        assert len(cell) == 3
        assert len({record.value["score"] for record in cell}) == 3


class TestSelectionReporting:
    def test_render_selection_lists_cells_labels_and_sample_counts(
        self, tmp_path: Path
    ) -> None:
        first = MiniHarness(tmp_path, label="batch-a")
        first.produce(agent="alpha", scenario="mini-one", effort="low")
        first.close()
        second = MiniHarness(tmp_path, label="batch-b")
        second.produce(agent="alpha", scenario="mini-one", effort="low", fresh=True)
        second.close()

        cells = _cells(tmp_path, labels=("batch-a", "batch-b"))
        rendered = render_selection(cells)

        assert "mini-one:alpha:low" in rendered
        assert "batch-a" in rendered
        assert "batch-b" in rendered

    def test_completeness_reports_missing_cells(self, tmp_path: Path) -> None:
        harness = MiniHarness(tmp_path, label="batch-a")
        harness.produce(agent="alpha", scenario="mini-one", effort="low")
        harness.close()

        cells = _cells(tmp_path)
        from fixtures.run_model_scenario import expected_produce_cells

        status = completeness(expected_produce_cells(), cells)

        assert status["expected"] == 6
        assert status["present"] == 1
        assert len(status["missing"]) == 5
        assert "mini-one:alpha:low" not in status["missing"]
