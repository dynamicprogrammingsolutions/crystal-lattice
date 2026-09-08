from __future__ import annotations

import json
import os
import statistics
from typing import Any
from urllib.request import Request, urlopen

import pytest

from agent_core import AgentCore
from plugins.request_options_feature import RequestOptionsFeature

from anthropic_plugins import (
    AnthropicProvider,
    AnthropicReasoningExtension,
    AnthropicUsageExtension,
)


PROMPT = (
    "Is it better to optimize a system for correctness or for performance, "
    "when you can only pick one? Argue both sides before concluding in one "
    "sentence."
)
ATTEMPTS = 5
MARGIN = 2.0


def _config(effort: str) -> dict[str, Any]:
    return {
        "provider": "anthropic",
        "base_url": os.getenv("OLLAMA_ANTHROPIC_BASE_URL", "http://localhost:11434"),
        "model": os.getenv("OLLAMA_ANTHROPIC_EFFORT_MODEL", "granite4.2:3b"),
        "api_key": "ollama",
        "timeout": float(os.getenv("OLLAMA_ANTHROPIC_EFFORT_TIMEOUT", "180")),
        "max_tokens": 768,
        # Do not add thinking.type here. Ollama gives the explicit boolean
        # thinking mode precedence over output_config.effort, which would make
        # the graded effort value ineffective.
        "request_options": {"output_config": {"effort": effort}},
    }


def _require_model(config: dict[str, Any]) -> None:
    url = f"{str(config['base_url']).rstrip('/')}/api/tags"
    try:
        with urlopen(Request(url), timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        pytest.skip("local Ollama endpoint is not reachable")
    names = {
        model.get("name")
        for model in payload.get("models", [])
        if isinstance(model, dict)
    }
    if config["model"] not in names:
        pytest.skip(f"local Ollama model {config['model']} is not installed")


def _core() -> AgentCore:
    core = AgentCore()
    core.register_feature(RequestOptionsFeature)
    core.register_provider(
        AnthropicProvider,
        extensions=[AnthropicReasoningExtension, AnthropicUsageExtension],
    )
    return core


def _reasoning_samples(effort: str) -> list[int]:
    config = _config(effort)
    _require_model(config)
    core = _core()
    samples: list[int] = []
    for _ in range(ATTEMPTS):
        session = core.add_message(
            core.create_session(),
            "user",
            PROMPT,
            config=config,
        )
        _session, finals = core.send_request(session, config)
        assert finals, f"Granite returned no final message for effort={effort!r}"
        reasoning = (finals[-1].get("metadata") or {}).get("reasoning")
        assert (
            isinstance(reasoning, str) and reasoning.strip()
        ), f"Granite returned no reasoning for effort={effort!r}"
        samples.append(len(reasoning))
    return samples


@pytest.mark.integration
@pytest.mark.ollama
@pytest.mark.slow_integration
def test_granite_reasoning_effort_high_produces_more_reasoning_than_low() -> None:
    """Granite high effort produces materially more reasoning than low effort.

    Calibration on local Ollama 0.32.6 with ``granite4.2:3b`` used five fresh
    attempts per level:

    - low:  [98, 76, 117, 92, 105], median 98
    - high: [625, 581, 982, 1174, 628], median 628

    The observed median ratio was 6.41 and every high sample exceeded the
    largest low sample by at least 4.96x. A 2.0x median margin is deliberately
    conservative while still proving behavioral effectiveness rather than mere
    request acceptance.
    """

    low_samples = _reasoning_samples("low")
    high_samples = _reasoning_samples("high")
    low_median = float(statistics.median(low_samples))
    high_median = float(statistics.median(high_samples))

    assert high_median >= low_median * MARGIN, (
        f"expected median Granite reasoning at effort='high' to be at least "
        f"{MARGIN:.2f}x effort='low'; got low={low_median:.0f} "
        f"{low_samples}, high={high_median:.0f} {high_samples}, "
        f"ratio={high_median / low_median:.2f}"
    )
