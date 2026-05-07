from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parents[3]
    path = root / "scripts" / "run_openai_responses_tier_matrix.py"
    spec = importlib.util.spec_from_file_location("run_openai_responses_tier_matrix", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_models_dedupes_and_preserves_order() -> None:
    module = _load_module()

    models = module.parse_models("gpt-5.4-mini", "gpt-5.4-mini,gpt-5.2,gpt-5.2,gpt-5.5")

    assert models == ["gpt-5.4-mini", "gpt-5.2", "gpt-5.5"]


def test_build_matrix_cases_respects_scope() -> None:
    module = _load_module()

    api_cases = module.build_matrix_cases("api", module.OPENAI_RESPONSES_FAMILY)
    chatgpt_cases = module.build_matrix_cases("chatgpt", module.OPENAI_RESPONSES_FAMILY)
    both_cases = module.build_matrix_cases("both", module.OPENAI_RESPONSES_FAMILY)

    assert [case.name for case in api_cases] == ["api-default", "api-flex", "api-priority"]
    assert [case.name for case in chatgpt_cases] == ["chatgpt-default", "chatgpt-priority"]
    assert [case.name for case in both_cases] == [
        "api-default",
        "api-flex",
        "api-priority",
        "chatgpt-default",
        "chatgpt-priority",
    ]


def test_build_benchmark_prompt_targets_input_and_output_tokens() -> None:
    module = _load_module()

    prompt = module.build_benchmark_prompt(
        case_name="unit-test",
        desired_input_tokens=5_000,
        desired_output_tokens=1_000,
    )

    assert "CONTEXT" in prompt.user_message
    assert "TEXT_TO_NORMALIZE" in prompt.user_message
    assert prompt.approx_transform_tokens >= 1_000
    assert prompt.approx_total_input_tokens >= 5_000
    assert prompt.approx_total_input_tokens > prompt.approx_transform_tokens
    assert prompt.approx_context_tokens > 0


def test_build_run_specs_expands_repeats_for_each_model_and_case() -> None:
    module = _load_module()

    cases = module.build_matrix_cases("chatgpt", module.OPENAI_RESPONSES_FAMILY)
    specs = module.build_run_specs(
        models=["gpt-5.4", "gpt-5.5"],
        cases=cases,
        repeat=2,
        desired_input_tokens=5_000,
        desired_output_tokens=500,
    )

    assert len(specs) == 8
    assert specs[0].model == "gpt-5.4"
    assert specs[0].case.name == "chatgpt-default"
    assert specs[0].repeat_index == 1
    assert specs[1].repeat_index == 2
    assert specs[-1].model == "gpt-5.5"
    assert specs[-1].case.name == "chatgpt-priority"
    assert specs[-1].repeat_index == 2


def test_parse_case_names_filters_available_cases() -> None:
    module = _load_module()

    cases = module.build_matrix_cases("both", module.OPENAI_RESPONSES_FAMILY)
    selected = module.parse_case_names("api-default,chatgpt-default", cases)

    assert [case.name for case in selected] == ["api-default", "chatgpt-default"]


def test_reference_openai_compatible_family_uses_standard_case() -> None:
    module = _load_module()

    cases = module.build_matrix_cases("both", module.REFERENCE_OPENAI_COMPATIBLE_FAMILY)

    assert [case.name for case in cases] == ["standard"]


def test_resolve_simplified_agent_target_reads_provider_family_and_base_config(tmp_path: Path) -> None:
    module = _load_module()

    path = tmp_path / "agent.json"
    path.write_text(
        """
        {
          "provider_family": "reference_openai_compatible",
          "base_config": {
            "provider": "reference_openai_compatible",
            "model": "kimi-k2.6:cloud",
            "base_url": "http://localhost:11434/v1"
          }
        }
        """,
        encoding="utf-8",
    )

    target = module._resolve_simplified_agent_target(path)

    assert target.family == module.REFERENCE_OPENAI_COMPATIBLE_FAMILY
    assert target.model == "kimi-k2.6:cloud"
    assert target.config["base_url"] == "http://localhost:11434/v1"