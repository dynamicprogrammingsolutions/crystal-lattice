"""Crystal-lattice mini-evaluation: the run model over the real runtime.

These tests run the whole mechanism — labels, request identity, natural
provider-failure retry, guidance-change cache miss, fresh re-execution,
and consolidation — through the real Crystal Lattice runtime with the
deterministic echo agent, which owns every simple response: the no-tool
producer scenario and all per-subject assessments. Real-model tool
scenarios live in ``test_crystal_mini_ollama.py`` behind the
``agent_eval`` marker.
"""

from __future__ import annotations

import json
from pathlib import Path

from agent_eval.runner import select_cell_records

from fixtures.crystal_mini_scenario import (
    ASSESSMENT_RECORD_NAME,
    ECHO_AGENT,
    ECHO_SCENARIO,
    MINI_GUIDANCE,
    PRODUCER_RECORD_NAME,
    SCENARIO_PROMPTS,
    MiniCrystalHarness,
    expected_produce_cells,
    freeze_mini_dataset,
    producer_cell,
    render_mini_report,
)


def test_guidance_feature_injects_workspace_guidance(tmp_path: Path) -> None:
    from fixtures.crystal_plugins import GuidanceSystemMessage

    guidance_file = tmp_path / "AGENTS.md"
    guidance_file.write_text(MINI_GUIDANCE, encoding="utf-8")
    feature = GuidanceSystemMessage()
    state = feature.init({"guidance_file": str(guidance_file)}, {})
    native = [{"role": "user", "content": "describe the defect", "metadata": {}}]

    injected, _ = feature.initialize_request(native, state)

    assert injected[0]["role"] == "system"
    assert injected[0]["content"] == MINI_GUIDANCE
    assert injected[1] == native[0]


def test_mini_crystal_lifecycle_produces_assesses_and_freezes(
    tmp_path: Path,
) -> None:
    harness = MiniCrystalHarness(tmp_path, agents=(ECHO_AGENT,), label="batch-a")
    produced = harness.produce(agent=ECHO_AGENT, scenario=ECHO_SCENARIO)
    assessed = harness.assess(
        subject={
            "scenario": ECHO_SCENARIO,
            "agent": ECHO_AGENT,
            "response": produced.value.response,
        },
    )
    harness.close()

    produced.raise_for_error()
    value = produced.value
    assert value.completed is True
    assert value.errors == ()
    assert value.valid is True
    assert value.response == f"Echo: {SCENARIO_PROMPTS[ECHO_SCENARIO]}"

    provenance = json.loads(
        (produced.artifact_dir / "records" / "run-model.json").read_text(
            encoding="utf-8"
        )
    )
    assert provenance["label"] == "batch-a"
    assert provenance["cache_hit"] is False

    # One subject per request: the record keeps the subject-to-producer
    # mapping and the parsed verdict.
    assessment = json.loads(
        (assessed.artifact_dir / "records" / ASSESSMENT_RECORD_NAME).read_text(
            encoding="utf-8"
        )
    )
    assert assessment["subject_cell"] == f"{ECHO_SCENARIO}:{ECHO_AGENT}"
    assert assessment["verdict"] == "pass"
    assert assessment["score"] == 1.0
    assert "Subject:" in assessment["prompt"]

    dataset = freeze_mini_dataset(tmp_path, agents=(ECHO_AGENT,))
    assert dataset["completeness"]["missing"] == []
    assert dataset["completeness"]["present"] == len(
        expected_produce_cells((ECHO_AGENT,))
    )
    cell = f"{ECHO_SCENARIO}:{ECHO_AGENT}"
    assert dataset["statistics"][cell]["count"] == 1
    assert dataset["statistics"][cell]["mean"] == 1.0
    assert cell in render_mini_report(dataset)


def test_provider_failure_is_not_cached_and_retries_naturally(
    tmp_path: Path,
) -> None:
    harness = MiniCrystalHarness(tmp_path, agents=(ECHO_AGENT,), label="batch-a")
    failed = harness.produce(
        agent=ECHO_AGENT,
        scenario=ECHO_SCENARIO,
        mode="raise_error",
        error_message="insufficient quota",
    )
    recovered = harness.produce(agent=ECHO_AGENT, scenario=ECHO_SCENARIO)
    replay = harness.produce(agent=ECHO_AGENT, scenario=ECHO_SCENARIO)
    harness.close()

    # The provider failure surfaces as a completed run with value errors.
    assert failed.cache_hit is False
    assert failed.value.errors != ()
    assert failed.value.valid is False
    assert "insufficient quota" in failed.value.errors[0]

    # The failed value was not cached: the retry executes genuinely.
    assert recovered.cache_hit is False
    assert recovered.value.valid is True

    # The recovered value is cached: a later replay hits.
    assert replay.cache_hit is True

    # Consolidation keeps both genuine executions as history; only the
    # recovered sample is valid.
    cells = select_cell_records(
        tmp_path,
        record_name=PRODUCER_RECORD_NAME,
        cell_identity=producer_cell,
    )
    samples = cells[f"{ECHO_SCENARIO}:{ECHO_AGENT}"]
    assert len(samples) == 2
    valid_samples = [sample for sample in samples if not sample.value["errors"]]
    assert len(valid_samples) == 1


def test_guidance_change_misses_the_cache(tmp_path: Path) -> None:
    original = MiniCrystalHarness(tmp_path, agents=(ECHO_AGENT,), label="batch-a")
    first = original.produce(agent=ECHO_AGENT, scenario=ECHO_SCENARIO)
    original.close()

    changed = MiniCrystalHarness(
        tmp_path,
        agents=(ECHO_AGENT,),
        label="batch-b",
        guidance=MINI_GUIDANCE + "\nEvery task file ends with a next-step note.\n",
    )
    second = changed.produce(agent=ECHO_AGENT, scenario=ECHO_SCENARIO)
    changed.close()

    assert first.cache_hit is False
    # A changed guidance candidate is a changed request: it must re-execute.
    assert second.cache_hit is False

    cells = select_cell_records(
        tmp_path,
        record_name=PRODUCER_RECORD_NAME,
        cell_identity=producer_cell,
        labels=("batch-a", "batch-b"),
    )
    samples = cells[f"{ECHO_SCENARIO}:{ECHO_AGENT}"]
    assert {sample.label for sample in samples} == {"batch-a", "batch-b"}


def test_second_label_replays_and_fresh_reexecutes(tmp_path: Path) -> None:
    first = MiniCrystalHarness(tmp_path, agents=(ECHO_AGENT,), label="batch-a")
    first.produce(agent=ECHO_AGENT, scenario=ECHO_SCENARIO)
    first.close()

    second = MiniCrystalHarness(tmp_path, agents=(ECHO_AGENT,), label="batch-b")
    replay = second.produce(agent=ECHO_AGENT, scenario=ECHO_SCENARIO)
    resampled = second.produce(agent=ECHO_AGENT, scenario=ECHO_SCENARIO, fresh=True)
    second.close()

    # An unchanged request replays from cache; fresh re-executes deliberately.
    assert replay.cache_hit is True
    assert resampled.cache_hit is False

    cell = f"{ECHO_SCENARIO}:{ECHO_AGENT}"

    # Explicit labels select every genuine sample across both labels.
    dataset = freeze_mini_dataset(
        tmp_path, agents=(ECHO_AGENT,), labels=("batch-a", "batch-b")
    )
    statistics = dataset["statistics"][cell]
    assert statistics["count"] == 2
    assert {sample["label"] for sample in statistics["samples"]} == {
        "batch-a",
        "batch-b",
    }
    # The deterministic echo produces identical samples: spread 0.
    assert statistics["spread"] == 0.0

    # Default selection keeps the latest label per cell only.
    latest = freeze_mini_dataset(tmp_path, agents=(ECHO_AGENT,))
    assert latest["statistics"][cell]["count"] == 1
