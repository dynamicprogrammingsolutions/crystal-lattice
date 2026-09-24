"""Live crystal-lattice mini-evaluation: real local Ollama models.

Both downloaded qwen models produce the tool scenarios through the real
tool loop with the core read/write tools; the deterministic echo agent
assesses every subject. These tests are marked ``agent_eval`` (plus
``ollama``) and never run under a bare pytest invocation. They skip when
the local Ollama OpenAI-compatible endpoint is unreachable.
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

import pytest

from fixtures.crystal_mini_scenario import (
    ASSESSMENT_RECORD_NAME,
    OLLAMA_AGENTS,
    PRODUCER_RECORD_NAME,
    TOOL_SCENARIOS,
    MiniCrystalHarness,
    expected_produce_cells,
    freeze_mini_dataset,
    render_mini_report,
)

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"


def _ollama_available(base_url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{base_url.rstrip('/')}/models", timeout=2):
            return True
    except OSError:
        return False


@pytest.mark.agent_eval
@pytest.mark.ollama
def test_both_qwen_models_produce_the_tool_scenarios(tmp_path: Path) -> None:
    base_url = os.environ.get("OLLAMA_OPENAI_BASE_URL", DEFAULT_OLLAMA_BASE_URL)
    if not _ollama_available(base_url):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    harness = MiniCrystalHarness(
        tmp_path, agents=("echo", *OLLAMA_AGENTS), label="live-matrix"
    )
    try:
        for agent in OLLAMA_AGENTS:
            for scenario in TOOL_SCENARIOS:
                run = harness.produce(agent=agent, scenario=scenario)
                value = run.value
                # The mechanism holds for real models: completed, no
                # provider errors, the tool loop engaged.
                assert value.completed is True, value
                assert value.errors == (), value
                assert value.tool_event_count > 0, value
                # Validity derivation is self-consistent with the
                # workspace: whatever the model did, valid matches its
                # checks, and the record carries them for review.
                assert value.valid == all(value.checks.values()), value
                record = json.loads(
                    (run.artifact_dir / "records" / PRODUCER_RECORD_NAME).read_text(
                        encoding="utf-8"
                    )
                )
                assert record["checks"] == dict(value.checks)
    finally:
        harness.close()

    dataset = freeze_mini_dataset(tmp_path, agents=OLLAMA_AGENTS)
    assert dataset["completeness"]["missing"] == []
    assert dataset["completeness"]["present"] == len(
        expected_produce_cells(OLLAMA_AGENTS)
    )


@pytest.mark.agent_eval
@pytest.mark.ollama
def test_ollama_production_is_assessed_frozen_and_replayed(tmp_path: Path) -> None:
    base_url = os.environ.get("OLLAMA_OPENAI_BASE_URL", DEFAULT_OLLAMA_BASE_URL)
    if not _ollama_available(base_url):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    harness = MiniCrystalHarness(
        tmp_path, agents=("echo", *OLLAMA_AGENTS), label="live-a"
    )
    try:
        produced = harness.produce(agent="qwen3", scenario="mini-task")
        assessed = harness.assess(
            subject={
                "scenario": "mini-task",
                "agent": "qwen3",
                "response": produced.value.response,
            },
        )
        replay = harness.produce(agent="qwen3", scenario="mini-task")
    finally:
        harness.close()

    assert produced.value.completed is True
    assert produced.value.errors == ()
    # Real production replays from cache: no second model call.
    assert replay.cache_hit is True

    assessment = json.loads(
        (assessed.artifact_dir / "records" / ASSESSMENT_RECORD_NAME).read_text(
            encoding="utf-8"
        )
    )
    assert assessment["subject_cell"] == "mini-task:qwen3"
    assert assessment["verdict"] in {"pass", "fail"}

    dataset = freeze_mini_dataset(tmp_path, agents=("qwen3",))
    assert dataset["completeness"]["present"] == 1
    assert "mini-task:qwen3" in render_mini_report(dataset)
