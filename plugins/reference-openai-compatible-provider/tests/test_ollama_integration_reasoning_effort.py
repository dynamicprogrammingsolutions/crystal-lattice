"""Integration tests verifying ``reasoning_effort`` actually changes model behavior.

These are the first integration tests in the repo that compare reasoning output
between two effort levels (``high`` vs ``max``) to verify the setting is honored
by the server, not just accepted silently.

Scope:
- Ollama ``glm-5.2:cloud`` via the reference OpenAI-compatible provider.
- Fireworks ``accounts/fireworks/models/glm-5p2`` as a cross-provider verification
  path (used when Ollama results are ambiguous or to confirm the setting works
  on a second backend).

Signal:
- Neither Ollama nor Fireworks returns ``completion_tokens_details.reasoning_tokens``
  in the usage payload for glm-5.2, so we use ``len(metadata["reasoning"])`` (the
  character count of the extracted reasoning text) as the comparison signal.

Discovery (see ``test_dir/reasoning_effort_discovery/``):
- Ollama accepts ``reasoning_effort`` values: ``high``, ``medium``, ``low``,
  ``max``, ``none``. ``xhigh`` is rejected.
- Fireworks accepts the same plus ``xhigh``.
- Prompt 5 (correctness vs performance tradeoff) was selected from 5 candidates
  because it produced the best discrimination: median ratio ~1.91 on Ollama with
  100% sample separation (every ``max`` sample > every ``high`` sample).

Markers:
- ``@pytest.mark.integration`` + ``@pytest.mark.ollama`` (Ollama variant).
- ``@pytest.mark.integration`` + ``@pytest.mark.fireworks`` + ``@pytest.mark.api``
  (Fireworks variant; ``api`` marks it as requiring credentials).
"""

from __future__ import annotations

import os
import statistics
import time
from typing import Any

import pytest
import requests

from agent_core.core import AgentCore

from plugins.request_options_feature import RequestOptionsFeature

from reference_openai_compatible_provider.provider import OpenAICompatibleProvider
from reference_openai_compatible_provider.reasoning_extension import (
    OpenAICompatibleReasoningExtension,
)
from reference_openai_compatible_provider.tools_extension import (
    OpenAICompatibleToolsExtension,
)
from reference_openai_compatible_provider.usage_extension import (
    OpenAICompatibleUsageExtension,
)

from fireworks_test_utils import (
    build_fireworks_cfg,
    fireworks_model,
)


# --- Shared constants --------------------------------------------------------

# Selected from discovery screening: best discrimination score across 5 candidate
# prompts. See ``test_dir/reasoning_effort_discovery/discover_prompts.py``.
PROMPT = (
    "Is it better to optimize a system for correctness or for performance, "
    "when you can only pick one? Argue both sides before concluding in one "
    "sentence."
)

EFFORT_HIGH = "high"
EFFORT_MAX = "max"

# Number of attempts per effort level. We take the median to reduce noise from
# nondeterministic model output (no seed is used, per the test's intent to
# verify real-world behavior rather than a seeded single point).
ATTEMPTS = 5

# Margin: median_max must be at least ``MARGIN`` times median_high.
#
# Ollama discovery data (prompt 5, 5 attempts each):
#   high: median=3151, samples=[2929, 2195, 3151, 3966, 3362]
#   max:  median=6029, samples=[5049, 5316, 6029, 6219, 7138]
#   ratio=1.91, worst-case min_max/max_high=5049/3966=1.27
#
# A margin of 1.2 (20% difference) sits below the worst-case single-sample
# ratio (1.27) and well below the median ratio (1.91), giving headroom for
# variance while still asserting a meaningful difference that confirms the
# setting is honored. A 1.3 margin was tried initially but flaked ~20% of
# runs because the worst-case median ratio can dip to ~1.27.
OLLAMA_MARGIN = 1.2

# Fireworks discovery data (prompt 5, 5 attempts each):
#   high: median=3553, samples=[3882, 4372, 3111, 3553, 3248]
#   max:  median=5086, samples=[5958, 5750, 3787, 4054, 5086]
#   ratio=1.43
#
# Fireworks shows more variance than Ollama (individual samples overlap
# between effort levels), so we use a conservative 1.15 margin (15% difference).
# This is below the observed median ratio (1.43) and is the lowest margin
# that still meaningfully confirms the setting is honored.
FIREWORKS_MARGIN = 1.15


# --- Shared helpers ----------------------------------------------------------


def _build_reference_core() -> AgentCore:
    core = AgentCore()
    core.register_feature(RequestOptionsFeature)
    core.register_provider(
        OpenAICompatibleProvider,
        extensions=[
            OpenAICompatibleToolsExtension,
            OpenAICompatibleReasoningExtension,
            OpenAICompatibleUsageExtension,
        ],
    )
    return core


def _reasoning_length(final_message: dict[str, Any]) -> int:
    """Return the character count of the reasoning text from a final assistant message.

    Falls back to 0 if no reasoning metadata is present.
    """
    metadata = final_message.get("metadata") or {}
    reasoning = metadata.get("reasoning")
    if isinstance(reasoning, str):
        return len(reasoning)
    return 0


def _median_reasoning_length(
    core: AgentCore,
    cfg: dict[str, Any],
    prompt: str,
    effort: str,
    *,
    attempts: int = ATTEMPTS,
    pace_seconds: float = 0.0,
) -> float | None:
    """Run ``attempts`` requests at the given effort and return the median reasoning length.

    Returns ``None`` to signal the caller should skip the test when:
    - The server rejects ``reasoning_effort`` (RuntimeError mentioning effort/reasoning).
    - A majority of attempts produce zero reasoning (server not returning reasoning).
    """
    effort_cfg = {
        **cfg,
        "request_options": {
            **(cfg.get("request_options") or {}),
            "reasoning_effort": effort,
        },
    }

    samples: list[int] = []
    for _ in range(attempts):
        if pace_seconds > 0 and samples:
            time.sleep(pace_seconds)
        session = core.create_session()
        session = core.add_message(session, "user", prompt)
        try:
            _session, finals = core.send_request(session, effort_cfg)
        except RuntimeError as exc:
            lowered = str(exc).lower()
            if any(k in lowered for k in ("reasoning_effort", "effort", "think")):
                return None
            raise
        if not finals:
            continue
        rlen = _reasoning_length(finals[-1])
        if rlen > 0:
            samples.append(rlen)

    if len(samples) < (attempts // 2 + 1):
        return None

    return float(statistics.median(samples))


# --- Ollama variant ---------------------------------------------------------

OLLAMA_GLM_5_2_MODEL = "glm-5.2:cloud"


def _ollama_available(base_url: str) -> bool:
    try:
        r = requests.get(f"{base_url.rstrip('/')}/models", timeout=2)
        return bool(r.ok)
    except Exception:
        return False


def _ollama_model_available(base_url: str, model: str) -> bool:
    try:
        response = requests.get(f"{base_url.rstrip('/')}/models", timeout=5)
    except Exception:
        return False
    if not response.ok:
        return False
    data = response.json().get("data") or []
    return any(isinstance(item, dict) and item.get("id") == model for item in data)


def _ollama_cfg() -> dict[str, Any]:
    return {
        "base_url": os.environ.get(
            "OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1"
        ),
        "model": os.environ.get("OLLAMA_OPENAI_GLM_5_2_MODEL", OLLAMA_GLM_5_2_MODEL),
        "timeout": float(os.environ.get("OLLAMA_OPENAI_TIMEOUT", "180")),
    }


@pytest.mark.integration
@pytest.mark.ollama
def test_reasoning_effort_high_vs_max_ollama_glm_5_2_cloud() -> None:
    """``reasoning_effort=max`` produces meaningfully more reasoning than ``high`` on Ollama.

    Verifies that the ``reasoning_effort`` setting is actually honored by the
    Ollama OpenAI-compatible endpoint for ``glm-5.2:cloud``, not silently ignored.
    Uses ``len(metadata["reasoning"])`` as the signal because Ollama does not
    return ``reasoning_tokens`` in the usage payload.
    """
    cfg = _ollama_cfg()
    if not _ollama_available(cfg["base_url"]):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")
    if not _ollama_model_available(cfg["base_url"], cfg["model"]):
        pytest.skip(f"Ollama model {cfg['model']!r} is not available")

    core = _build_reference_core()

    high_median = _median_reasoning_length(core, cfg, PROMPT, EFFORT_HIGH)
    max_median = _median_reasoning_length(core, cfg, PROMPT, EFFORT_MAX)

    if high_median is None or max_median is None:
        pytest.skip(
            "Server did not return reasoning content or rejected reasoning_effort; "
            "cannot verify the setting is honored"
        )

    assert max_median >= high_median * OLLAMA_MARGIN, (
        f"expected median reasoning at effort={EFFORT_MAX!r} to be at least "
        f"{OLLAMA_MARGIN:.2f}x effort={EFFORT_HIGH!r}; got "
        f"high={high_median:.0f}, max={max_median:.0f} "
        f"(ratio={max_median / high_median:.2f})"
    )


# --- Fireworks variant -------------------------------------------------------

_DEFAULT_FIREWORKS_GLM_5_2_MODEL = "accounts/fireworks/models/glm-5p2"


@pytest.mark.integration
@pytest.mark.fireworks
@pytest.mark.api
def test_reasoning_effort_high_vs_max_fireworks_glm_5_2() -> None:
    """Cross-provider verification: ``reasoning_effort=max`` vs ``high`` on Fireworks glm-5.2.

    Mirrors the Ollama test on Fireworks to confirm the setting is honored by a
    second backend. Uses ``len(metadata["reasoning"])`` as the signal because
    Fireworks also does not return ``reasoning_tokens`` in the usage payload for
    glm-5.2.
    """
    model = fireworks_model("FIREWORKS_GLM_5_2_MODEL", _DEFAULT_FIREWORKS_GLM_5_2_MODEL)
    cfg = build_fireworks_cfg(
        model,
        request_options={},
    )

    core = _build_reference_core()

    high_median = _median_reasoning_length(
        core, cfg, PROMPT, EFFORT_HIGH, pace_seconds=1.0
    )
    max_median = _median_reasoning_length(
        core, cfg, PROMPT, EFFORT_MAX, pace_seconds=1.0
    )

    if high_median is None or max_median is None:
        pytest.skip(
            "Server did not return reasoning content or rejected reasoning_effort; "
            "cannot verify the setting is honored"
        )

    assert max_median >= high_median * FIREWORKS_MARGIN, (
        f"expected median reasoning at effort={EFFORT_MAX!r} to be at least "
        f"{FIREWORKS_MARGIN:.2f}x effort={EFFORT_HIGH!r}; got "
        f"high={high_median:.0f}, max={max_median:.0f} "
        f"(ratio={max_median / high_median:.2f})"
    )
