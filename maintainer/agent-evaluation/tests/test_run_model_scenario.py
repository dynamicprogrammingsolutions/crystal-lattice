"""Fixture mini-evaluation: the whole run-model mechanism end-to-end.

One semi-complex, short-running scenario exercises everything the layer
promises: a configuration-derived matrix, multiple stages, per-subject
assessments, run labels as provenance, natural provider-failure retries,
deliberate re-execution, and label-based consolidation with per-cell sample
aggregation — entirely against the deterministic echo provider.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from agent_eval.runner import (
    cell_statistics,
    completeness,
    select_cell_records,
)

from fixtures.run_model_scenario import (
    ASSESSMENT_RECORD_NAME,
    MINI_AGENTS,
    PRODUCER_RECORD_NAME,
    MiniHarness,
    expected_produce_cells,
    producer_cell,
)


def _valid_only(
    cells: Mapping[str, tuple[Any, ...]],
) -> dict[str, tuple[Any, ...]]:
    """Suite-style filtering: invalid samples never reach the statistics."""

    return {
        cell: tuple(
            record for record in records if record.value.get("completed") is True
        )
        for cell, records in cells.items()
    }


def test_mini_evaluation_runs_the_full_mechanism(tmp_path: Path) -> None:
    # First batch: the whole matrix, with one injected provider failure
    # that must retry naturally under the same cache.
    first = MiniHarness(
        tmp_path,
        label="batch-a",
        failures={"alpha": ("insufficient quota",)},
    )
    produced: list[dict[str, Any]] = []
    for scenario in ("mini-one", "mini-two"):
        for agent in MINI_AGENTS:
            for effort in MINI_AGENTS[agent].efforts:
                runs = first.produce(agent=agent, scenario=scenario, effort=effort)
                if runs[0].value.errors:
                    # Natural retry: same identity, no flags.
                    runs = first.produce(agent=agent, scenario=scenario, effort=effort)
                produced.extend(
                    {
                        "scenario": scenario,
                        "agent": agent,
                        "effort": effort,
                        "response": run.value.response,
                    }
                    for run in runs
                )
    # Four alpha cells plus one failed attempt retried naturally.
    assert first.environments["alpha"].request_count == 5
    assert first.environments["beta"].request_count == 2

    # Every produced sample is assessed in its own request.
    for subject in produced:
        first.assess(subject=subject)

    # Second batch: one cell re-executed deliberately for variance. The
    # shared environments continue the echo counters, so the fresh sample
    # differs from the first batch's — like a real model re-run.
    second = MiniHarness(tmp_path, label="batch-b", environments=first.environments)
    second.produce(agent="alpha", scenario="mini-one", effort="low", fresh=True)
    second.close()
    first.close()

    # Consolidation across both labels: every cell present, the re-executed
    # cell carries two samples, statistics aggregate them.
    cells = select_cell_records(
        tmp_path,
        record_name=PRODUCER_RECORD_NAME,
        cell_identity=producer_cell,
        labels=("batch-a", "batch-b"),
    )
    status = completeness(expected_produce_cells(), cells)
    assert status["missing"] == []
    assert status["present"] == len(expected_produce_cells())

    statistics = cell_statistics(
        _valid_only(cells), metric=lambda value: value["score"]
    )
    resampled = statistics["mini-one:alpha:low"]
    assert resampled["count"] == 2
    assert resampled["spread"] > 0
    assert {sample["label"] for sample in resampled["samples"]} == {
        "batch-a",
        "batch-b",
    }
    single = statistics["mini-two:beta:low"]
    assert single["count"] == 1
    assert single["spread"] == 0.0

    # The assessment stage scaled with the produced samples, one subject
    # per request.
    assessments = select_cell_records(
        tmp_path,
        record_name=ASSESSMENT_RECORD_NAME,
        cell_identity=lambda value: str(value["subject_cell"]),
    )
    assert len(assessments) == len(expected_produce_cells())


def test_mini_evaluation_replays_unchanged_cells_across_batches(
    tmp_path: Path,
) -> None:
    # An unchanged request identity replays from cache in a later batch:
    # no execution, visible cache hit.
    first = MiniHarness(tmp_path, label="batch-a")
    first.produce(agent="alpha", scenario="mini-one", effort="low")
    first.close()

    second = MiniHarness(tmp_path, label="batch-b")
    unchanged = second.produce(agent="alpha", scenario="mini-one", effort="low")

    assert unchanged[0].cache_hit is True
    assert second.environments["alpha"].request_count == 0
    second.close()
