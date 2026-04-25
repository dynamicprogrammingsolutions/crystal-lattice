from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Sequence

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
CORE_PY = REPO_ROOT / "core/python"
OPENAI_RESPONSES_SRC = REPO_ROOT / "plugins/openai_responses/src"
TIMESTAMP_EXTENSION_SRC = REPO_ROOT / "plugins/timestamp-extension/src"
FEATURE_SYSTEM_MESSAGE_SRC = REPO_ROOT / "plugins/feature-system-message/src"
TOOL_COMPAT_SHARED_SRC = REPO_ROOT / "plugins/tool-compat-shared/src"
FEATURE_REQUEST_OPTIONS_SRC = REPO_ROOT / "plugins/feature-request-options/src"
REFERENCE_OPENAI_COMPATIBLE_SRC = REPO_ROOT / "plugins/reference-openai-compatible-provider/src"

for candidate in (
    SCRIPTS_DIR,
    REPO_ROOT,
    CORE_PY,
    OPENAI_RESPONSES_SRC,
    TIMESTAMP_EXTENSION_SRC,
    FEATURE_SYSTEM_MESSAGE_SRC,
    TOOL_COMPAT_SHARED_SRC,
    FEATURE_REQUEST_OPTIONS_SRC,
    REFERENCE_OPENAI_COMPATIBLE_SRC,
):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from agent_core import AgentCore  # noqa: E402
from agent_app.config import (  # noqa: E402
    build_agent_config,
    build_config_resolution_env,
    build_runtime_overlay_env,
    load_raw_config,
    resolve_config_mixins,
    resolve_placeholders,
)
from feature_system_message.system_message_feature import SystemMessageFeature  # noqa: E402
from feature_request_options.request_options_feature import RequestOptionsFeature  # noqa: E402
from openai_responses_plugins import (  # noqa: E402
    OpenAIResponsesChatGPTAuthFeature,
    OpenAIResponsesFastModeExtension,
    OpenAIResponsesFlexProcessingExtension,
    OpenAIResponsesProvider,
    OpenAIResponsesUsageExtension,
)
from reference_openai_compatible_provider import (  # noqa: E402
    OpenAICompatibleProvider,
    OpenAICompatibleReasoningExtension,
    OpenAICompatibleUsageExtension,
)
from timestamp_extension.duration_extension import DurationExtension  # noqa: E402
from tool_compat_shared.shell_engine import approx_token_count  # noqa: E402
from openai_responses_tier_matrix_store import (  # noqa: E402
    DEFAULT_RESULTS_JSON_PATH,
    append_results_store,
    requested_tier_from_case,
)


DEFAULT_CHATGPT_AUTH_STATE_DIR = (
    REPO_ROOT / "plugins" / "chatgpt-auth-app" / "tests" / ".manual-state"
)
DEFAULT_DESIRED_INPUT_TOKENS = 10_000
DEFAULT_DESIRED_OUTPUT_TOKENS = 2_000
OPENAI_RESPONSES_FAMILY = "openai_responses"
REFERENCE_OPENAI_COMPATIBLE_FAMILY = "reference_openai_compatible"


@dataclass(frozen=True)
class MatrixCase:
    name: str
    auth_mode: str
    enable_flex_processing: bool = False
    enable_fast_mode: bool = False
    enable_fast_mode_for_api_requests: bool = False


@dataclass(frozen=True)
class BenchmarkPrompt:
    instructions: str
    user_message: str
    approx_instruction_tokens: int
    approx_user_tokens: int
    approx_context_tokens: int
    approx_transform_tokens: int
    approx_total_input_tokens: int


@dataclass(frozen=True)
class RunSpec:
    model: str
    case: MatrixCase
    repeat_index: int
    prompt: BenchmarkPrompt


@dataclass(frozen=True)
class RunResult:
    spec: RunSpec
    status: str
    metrics: Dict[str, Any]
    error: Optional[str]


@dataclass(frozen=True)
class ResolvedBenchmarkTarget:
    family: str
    config: Dict[str, Any]
    model: str


def _manual_state_dir() -> Path:
    raw = os.getenv("CHATGPT_TEST_STATE_DIR")
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()
    return DEFAULT_CHATGPT_AUTH_STATE_DIR


def _default_credentials_path() -> Path:
    return _manual_state_dir() / "auth" / "chatgpt-auth.json"


def _load_saved_credentials(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"saved ChatGPT login at {path} is not a JSON object")
    return payload


def _line_for_index(index: int, *, punctuated: bool) -> str:
    tokens = [
        "quallax",
        "merrin",
        "tavik",
        "sorn",
        "pelago",
        "vintar",
        "halcyon",
        "brindle",
        "noric",
        "zephyr",
        "lattice",
        "fallow",
    ]
    punctuation = [",", ".", ";", ":", "!", "?", "(", ")", "[", "]", "{", "}", "\"", "'", "-", "..."]
    parts: List[str] = []
    for word_idx in range(12):
        token = tokens[(index + word_idx) % len(tokens)]
        if word_idx % 4 == 0:
            token = token.upper()
        if punctuated:
            punct = punctuation[(index * 3 + word_idx) % len(punctuation)]
            token = f"{token}{punct}"
        parts.append(token)
    return f"{index + 1:03d} :: {' '.join(parts)}"


def _build_text_block(target_tokens: int, *, punctuated: bool) -> tuple[str, int]:
    out: List[str] = []
    total = 0
    index = 0
    target = max(1, int(target_tokens))
    while total < target:
        line = _line_for_index(index, punctuated=punctuated)
        out.append(line)
        total = approx_token_count("\n".join(out))
        index += 1
    text = "\n".join(out)
    return text, approx_token_count(text)


def build_benchmark_prompt(
    *,
    case_name: str,
    desired_input_tokens: int,
    desired_output_tokens: int,
) -> BenchmarkPrompt:
    if desired_input_tokens <= desired_output_tokens:
        raise ValueError("desired_input_tokens must be greater than desired_output_tokens")
    if desired_output_tokens <= 0:
        raise ValueError("desired_output_tokens must be positive")

    nonce = datetime.now(timezone.utc).isoformat()
    instructions = (
        f"RUN_NONCE: {nonce}\n"
        f"CASE: {case_name}\n"
        "You are performing a deterministic text transformation benchmark.\n"
        "The user message contains two sections named CONTEXT and TEXT_TO_NORMALIZE.\n"
        "Ignore the CONTEXT section completely.\n"
        "For TEXT_TO_NORMALIZE, remove punctuation only.\n"
        "Preserve word order and line breaks.\n"
        "Keep digits and whitespace.\n"
        "Return only the transformed TEXT_TO_NORMALIZE section.\n"
        "Do not summarize, explain, or mention the CONTEXT section."
    )

    transform_text, approx_transform_tokens = _build_text_block(
        desired_output_tokens,
        punctuated=True,
    )

    user_template = (
        "CONTEXT\n"
        "{context}\n\n"
        "TEXT_TO_NORMALIZE\n"
        "{transform_text}"
    )

    current_user = user_template.format(context="", transform_text=transform_text)
    approx_instruction_tokens = approx_token_count(instructions)
    approx_user_tokens = approx_token_count(current_user)

    remaining = desired_input_tokens - (approx_instruction_tokens + approx_user_tokens)
    context_text = ""
    approx_context_tokens = 0
    if remaining > 0:
        context_text, approx_context_tokens = _build_text_block(remaining, punctuated=False)

    user_message = user_template.format(context=context_text, transform_text=transform_text)
    approx_user_tokens = approx_token_count(user_message)

    return BenchmarkPrompt(
        instructions=instructions,
        user_message=user_message,
        approx_instruction_tokens=approx_instruction_tokens,
        approx_user_tokens=approx_user_tokens,
        approx_context_tokens=approx_context_tokens,
        approx_transform_tokens=approx_transform_tokens,
        approx_total_input_tokens=approx_instruction_tokens + approx_user_tokens,
    )


def _build_core(provider_family: str) -> AgentCore:
    core = AgentCore()
    if provider_family == OPENAI_RESPONSES_FAMILY:
        core.register_provider(
            OpenAIResponsesProvider,
            extensions=[
                OpenAIResponsesFlexProcessingExtension,
                OpenAIResponsesFastModeExtension,
                OpenAIResponsesUsageExtension,
            ],
        )
        core.register_feature(OpenAIResponsesChatGPTAuthFeature)
    elif provider_family == REFERENCE_OPENAI_COMPATIBLE_FAMILY:
        core.register_feature(RequestOptionsFeature)
        core.register_provider(
            OpenAICompatibleProvider,
            extensions=[
                OpenAICompatibleReasoningExtension,
                OpenAICompatibleUsageExtension,
            ],
        )
    else:
        raise ValueError(f"unsupported provider family: {provider_family}")
    core.register_feature(SystemMessageFeature)
    core.register_feature(DurationExtension)
    return core


def _base_config(model: str, desired_output_tokens: int) -> Dict[str, Any]:
    config: Dict[str, Any] = {
        "model": model,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "chatgpt_base_url": os.getenv("OPENAI_CHATGPT_BASE_URL") or "https://chatgpt.com/backend-api/codex",
        "timeout": 600,
        "max_output_tokens": max(int(desired_output_tokens * 1.25), desired_output_tokens + 256),
        "verbosity": "low",
    }
    api_key = os.getenv("OPENAI_API_KEY")
    if isinstance(api_key, str) and api_key:
        config["api_key"] = api_key
    return config


def _detect_provider_family(provider_key: str) -> str:
    normalized = provider_key.strip().lower()
    if normalized == OPENAI_RESPONSES_FAMILY:
        return OPENAI_RESPONSES_FAMILY
    if normalized == REFERENCE_OPENAI_COMPATIBLE_FAMILY:
        return REFERENCE_OPENAI_COMPATIBLE_FAMILY
    raise ValueError(f"unsupported provider family {provider_key!r}")


def _resolve_agent_target(config_json: Path, agent_id: str) -> ResolvedBenchmarkTarget:
    resolution_env = build_config_resolution_env(config_json)
    overlay_env = build_runtime_overlay_env(config_json)
    os.environ.update(overlay_env)

    raw_config = load_raw_config(config_json)
    resolved_config, _placeholder_errors = resolve_placeholders(raw_config, env=resolution_env)
    mixin_resolved_config, _mixin_errors = resolve_config_mixins(resolved_config)
    base_agent_config = build_agent_config(mixin_resolved_config, agent_id)

    model = base_agent_config.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError(f"agent {agent_id!r} does not resolve to a non-empty model")
    provider_key = base_agent_config.get("provider")
    if not isinstance(provider_key, str) or not provider_key.strip():
        raise ValueError(f"agent {agent_id!r} does not resolve to a non-empty provider")

    return ResolvedBenchmarkTarget(
        family=_detect_provider_family(provider_key),
        config=base_agent_config,
        model=model.strip(),
    )


def _resolve_simplified_agent_target(agent_config_json: Path) -> ResolvedBenchmarkTarget:
    payload = json.loads(agent_config_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"simplified agent config at {agent_config_json} is not a JSON object")

    base_config = payload.get("base_config")
    if not isinstance(base_config, dict):
        raise RuntimeError(
            f"simplified agent config at {agent_config_json} must define a 'base_config' object"
        )

    family_in = payload.get("provider_family")
    if isinstance(family_in, str) and family_in.strip():
        family = _detect_provider_family(family_in)
    else:
        provider_key = base_config.get("provider")
        if not isinstance(provider_key, str) or not provider_key.strip():
            raise RuntimeError(
                f"simplified agent config at {agent_config_json} must define either "
                "'provider_family' or base_config.provider"
            )
        family = _detect_provider_family(provider_key)

    model = base_config.get("model")
    if not isinstance(model, str) or not model.strip():
        raise RuntimeError(
            f"simplified agent config at {agent_config_json} must define base_config.model"
        )

    return ResolvedBenchmarkTarget(
        family=family,
        config=dict(base_config),
        model=model.strip(),
    )


def _case_config(
    provider_family: str,
    case: MatrixCase,
    model: str,
    credentials_path: Optional[Path],
    desired_output_tokens: int,
    base_agent_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if provider_family == OPENAI_RESPONSES_FAMILY:
        config = _base_config(model, desired_output_tokens)
        config["auth_mode"] = case.auth_mode
        config["enable_flex_processing"] = case.enable_flex_processing
        config["enable_fast_mode"] = case.enable_fast_mode
        config["enable_fast_mode_for_api_requests"] = case.enable_fast_mode_for_api_requests
        if case.auth_mode == "chatgpt":
            if credentials_path is None:
                raise RuntimeError("ChatGPT credentials path is required for chatgpt runs")
            config["chatgpt_credentials_path"] = str(credentials_path)
            config["show_openai_auth_mode"] = True
        return config

    if provider_family == REFERENCE_OPENAI_COMPATIBLE_FAMILY:
        if not isinstance(base_agent_config, dict):
            raise RuntimeError("base_agent_config is required for reference_openai_compatible runs")
        return {
            **base_agent_config,
            "model": model,
            "timeout": base_agent_config.get("timeout", 600),
            "max_output_tokens": max(int(desired_output_tokens * 1.25), desired_output_tokens + 256),
        }

    raise ValueError(f"unsupported provider family: {provider_family}")


def _send_streaming_request(
    provider_family: str,
    config: Dict[str, Any],
    spec: RunSpec,
) -> Dict[str, Any]:
    core = _build_core(provider_family)
    run_config = dict(config)
    if provider_family == OPENAI_RESPONSES_FAMILY and spec.case.auth_mode == "chatgpt":
        run_config["system_message_as_instructions"] = True
        run_config["system_message"] = spec.prompt.instructions
    elif provider_family == REFERENCE_OPENAI_COMPATIBLE_FAMILY:
        run_config["system_message"] = spec.prompt.instructions

    session = core.create_session()
    if not (
        provider_family == OPENAI_RESPONSES_FAMILY and spec.case.auth_mode == "chatgpt"
    ):
        session = core.add_message(session, "developer", spec.prompt.instructions, config=run_config)
    session = core.add_message(session, "user", spec.prompt.user_message, config=run_config)

    final_session = None
    final_messages = None
    for chunk in core.send_request_stream(session, run_config):
        if chunk.get("type") == "final":
            final_session = chunk.get("session")
            final_messages = chunk.get("messages")

    if final_session is None or not isinstance(final_messages, list) or not final_messages:
        raise RuntimeError("stream did not yield a final assistant message")

    final = final_messages[-1]
    if not isinstance(final, dict):
        raise RuntimeError("final assistant message is not a dict")
    return final


def _safe_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    return None


def _safe_float(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _extract_metrics(final: Dict[str, Any], prompt: BenchmarkPrompt) -> Dict[str, Any]:
    metadata = final.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}
    usage = metadata.get("usage") or {}
    if not isinstance(usage, dict):
        usage = {}

    input_tokens = _safe_int(usage.get("input_tokens"))
    output_tokens = _safe_int(usage.get("output_tokens"))
    duration_ms = _safe_int(metadata.get("duration_ms"))
    turn_tps = _safe_float(metadata.get("turn_tps"))
    if turn_tps is None and duration_ms and output_tokens is not None and duration_ms > 0:
        turn_tps = output_tokens / (duration_ms / 1000.0)

    content = final.get("content")
    output_chars = len(content) if isinstance(content, str) else None

    return {
        "reported_service_tier": metadata.get("usage_service_tier") or "default",
        "effective_auth_mode": metadata.get("usage_effective_auth_mode") or "",
        "duration_ms": duration_ms,
        "duration_seconds": (duration_ms / 1000.0) if isinstance(duration_ms, int) else None,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "turn_tps": turn_tps,
        "output_chars": output_chars,
        "approx_input_tokens_target": prompt.approx_total_input_tokens,
        "approx_output_tokens_target": prompt.approx_transform_tokens,
    }


def build_matrix_cases(run_scope: str, provider_family: str) -> List[MatrixCase]:
    if provider_family == REFERENCE_OPENAI_COMPATIBLE_FAMILY:
        return [MatrixCase(name="standard", auth_mode="standard")]

    normalized = run_scope.strip().lower()
    if normalized not in {"api", "chatgpt", "both"}:
        raise ValueError(f"unsupported run_scope: {run_scope}")

    cases: List[MatrixCase] = []
    if normalized in {"api", "both"}:
        cases.extend(
            [
                MatrixCase(name="api-default", auth_mode="api"),
                MatrixCase(name="api-flex", auth_mode="api", enable_flex_processing=True),
                MatrixCase(
                    name="api-priority",
                    auth_mode="api",
                    enable_fast_mode=True,
                    enable_fast_mode_for_api_requests=True,
                ),
            ]
        )
    if normalized in {"chatgpt", "both"}:
        cases.extend(
            [
                MatrixCase(name="chatgpt-default", auth_mode="chatgpt"),
                MatrixCase(name="chatgpt-priority", auth_mode="chatgpt", enable_fast_mode=True),
            ]
        )
    return cases


def parse_case_names(case_names: Optional[str], available_cases: Sequence[MatrixCase]) -> List[MatrixCase]:
    if not isinstance(case_names, str) or not case_names.strip():
        return list(available_cases)
    wanted = [item.strip() for item in case_names.split(",") if item.strip()]
    wanted_set = set(wanted)
    out = [case for case in available_cases if case.name in wanted_set]
    if not out:
        raise ValueError(f"no cases matched case_names={case_names!r}")
    return out


def parse_models(model: Optional[str], models: Optional[str]) -> List[str]:
    out: List[str] = []
    if isinstance(model, str) and model.strip():
        out.append(model.strip())
    if isinstance(models, str) and models.strip():
        out.extend(item.strip() for item in models.split(",") if item.strip())
    deduped: List[str] = []
    seen: set[str] = set()
    for item in out:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped or ["gpt-5.4-mini"]


def build_run_specs(
    *,
    models: Sequence[str],
    cases: Sequence[MatrixCase],
    repeat: int,
    desired_input_tokens: int,
    desired_output_tokens: int,
) -> List[RunSpec]:
    if repeat <= 0:
        raise ValueError("repeat must be positive")
    out: List[RunSpec] = []
    for model in models:
        for case in cases:
            for repeat_index in range(1, repeat + 1):
                prompt = build_benchmark_prompt(
                    case_name=f"{model}:{case.name}:repeat-{repeat_index}",
                    desired_input_tokens=desired_input_tokens,
                    desired_output_tokens=desired_output_tokens,
                )
                out.append(
                    RunSpec(
                        model=model,
                        case=case,
                        repeat_index=repeat_index,
                        prompt=prompt,
                    )
                )
    return out


def _run_single_spec(
    provider_family: str,
    spec: RunSpec,
    credentials_path: Optional[Path],
    desired_output_tokens: int,
    base_agent_config: Optional[Dict[str, Any]] = None,
) -> RunResult:
    config = _case_config(
        provider_family,
        spec.case,
        spec.model,
        credentials_path,
        desired_output_tokens,
        base_agent_config=base_agent_config,
    )
    try:
        final = _send_streaming_request(provider_family, config, spec)
        metrics = _extract_metrics(final, spec.prompt)
        return RunResult(spec=spec, status="ok", metrics=metrics, error=None)
    except Exception as exc:
        return RunResult(spec=spec, status="error", metrics={}, error=str(exc))


def run_specs(
    provider_family: str,
    *,
    specs: Sequence[RunSpec],
    credentials_path: Optional[Path],
    desired_output_tokens: int,
    execution_mode: str,
    max_workers: int,
    base_agent_config: Optional[Dict[str, Any]] = None,
) -> List[RunResult]:
    normalized = execution_mode.strip().lower()
    if normalized not in {"sequential", "parallel"}:
        raise ValueError(f"unsupported execution mode: {execution_mode}")

    if normalized == "sequential" or len(specs) <= 1:
        return [
            _run_single_spec(
                provider_family,
                spec,
                credentials_path,
                desired_output_tokens,
                base_agent_config=base_agent_config,
            )
            for spec in specs
        ]

    out: List[RunResult] = []
    worker_count = max(1, min(max_workers, len(specs)))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {
            executor.submit(
                _run_single_spec,
                provider_family,
                spec,
                credentials_path,
                desired_output_tokens,
                base_agent_config,
            ): spec
            for spec in specs
        }
        for future in as_completed(future_map):
            out.append(future.result())

    order = {
        (spec.model, spec.case.name, spec.repeat_index): idx
        for idx, spec in enumerate(specs)
    }
    out.sort(key=lambda item: order[(item.spec.model, item.spec.case.name, item.spec.repeat_index)])
    return out


def _format_metric_lines(result: RunResult) -> Iterable[str]:
    spec = result.spec
    yield f"[model={spec.model} case={spec.case.name} repeat={spec.repeat_index}]"
    yield f"auth_mode={spec.case.auth_mode}"
    yield f"enable_flex_processing={spec.case.enable_flex_processing}"
    yield f"enable_fast_mode={spec.case.enable_fast_mode}"
    yield f"enable_fast_mode_for_api_requests={spec.case.enable_fast_mode_for_api_requests}"
    yield f"approx_input_tokens_target={spec.prompt.approx_total_input_tokens}"
    yield f"approx_output_tokens_target={spec.prompt.approx_transform_tokens}"
    yield f"approx_context_tokens={spec.prompt.approx_context_tokens}"
    if result.error is not None:
        yield "status=error"
        yield f"error={result.error}"
        yield ""
        return

    yield "status=ok"
    yield f"effective_auth_mode={result.metrics.get('effective_auth_mode')}"
    yield f"reported_service_tier={result.metrics.get('reported_service_tier')}"
    yield f"duration_seconds={result.metrics.get('duration_seconds')}"
    yield f"input_tokens={result.metrics.get('input_tokens')}"
    yield f"output_tokens={result.metrics.get('output_tokens')}"
    yield f"tps={result.metrics.get('turn_tps')}"
    yield f"output_chars={result.metrics.get('output_chars')}"
    yield ""


def _group_key(result: RunResult) -> tuple[str, str]:
    return result.spec.model, result.spec.case.name


def _aggregate_results(results: Sequence[RunResult]) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[str, str], List[RunResult]] = {}
    for result in results:
        grouped.setdefault(_group_key(result), []).append(result)

    summaries: List[Dict[str, Any]] = []
    for (model, case_name), items in sorted(grouped.items()):
        successes = [item for item in items if item.status == "ok"]
        tps_values = [
            float(item.metrics["turn_tps"])
            for item in successes
            if isinstance(item.metrics.get("turn_tps"), (int, float))
        ]
        duration_values = [
            float(item.metrics["duration_seconds"])
            for item in successes
            if isinstance(item.metrics.get("duration_seconds"), (int, float))
        ]
        summaries.append(
            {
                "model": model,
                "case": case_name,
                "runs": len(items),
                "successes": len(successes),
                "errors": len(items) - len(successes),
                "mean_tps": mean(tps_values) if tps_values else None,
                "min_tps": min(tps_values) if tps_values else None,
                "max_tps": max(tps_values) if tps_values else None,
                "mean_duration_seconds": mean(duration_values) if duration_values else None,
            }
        )
    return summaries


def _format_summary_lines(summaries: Sequence[Dict[str, Any]]) -> Iterable[str]:
    yield "[summary]"
    for item in summaries:
        yield (
            f"model={item['model']} case={item['case']} runs={item['runs']} "
            f"successes={item['successes']} errors={item['errors']} "
            f"mean_tps={item['mean_tps']} min_tps={item['min_tps']} "
            f"max_tps={item['max_tps']} mean_duration_seconds={item['mean_duration_seconds']}"
        )
    yield ""


def _default_output_path(models: Sequence[str]) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if len(models) == 1:
        label = models[0].replace("/", "_")
    else:
        label = f"{len(models)}models"
    return REPO_ROOT / "artifacts" / f"openai_responses_tier_matrix_{label}_{timestamp}.txt"


def _default_profile(desired_input_tokens: int, desired_output_tokens: int) -> str:
    return f"input{desired_input_tokens}-output{desired_output_tokens}"


def _build_result_records(
    *,
    results: Sequence[RunResult],
    profile: str,
    artifact_path: Path,
    batch_started_at: str,
    desired_input_tokens: int,
    desired_output_tokens: int,
    execution_mode: str,
    max_workers: int,
    run_scope: str,
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for result in results:
        spec = result.spec
        metrics = result.metrics if isinstance(result.metrics, dict) else {}
        records.append(
            {
                "profile": profile,
                "model": spec.model,
                "case_name": spec.case.name,
                "auth_mode": spec.case.auth_mode,
                "requested_tier": requested_tier_from_case(spec.case.name),
                "repeat_index": spec.repeat_index,
                "execution_mode": execution_mode,
                "max_workers": max_workers,
                "run_scope": run_scope,
                "desired_input_tokens": desired_input_tokens,
                "desired_output_tokens": desired_output_tokens,
                "status": result.status,
                "error": result.error,
                "artifact_path": str(artifact_path),
                "batch_started_at": batch_started_at,
                "reported_service_tier": metrics.get("reported_service_tier"),
                "effective_auth_mode": metrics.get("effective_auth_mode"),
                "input_tokens": metrics.get("input_tokens"),
                "output_tokens": metrics.get("output_tokens"),
                "duration_seconds": metrics.get("duration_seconds"),
                "turn_tps": metrics.get("turn_tps"),
                "output_chars": metrics.get("output_chars"),
                "approx_input_tokens_target": spec.prompt.approx_total_input_tokens,
                "approx_output_tokens_target": spec.prompt.approx_transform_tokens,
                "approx_context_tokens": spec.prompt.approx_context_tokens,
            }
        )
    return records


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an OpenAI Responses tier benchmark matrix.")
    parser.add_argument(
        "--agent-config-json",
        help="Simplified benchmark agent config JSON with provider_family and base_config.",
    )
    parser.add_argument("--config-json", help="Optional config JSON path used to resolve an agent config.")
    parser.add_argument("--agent-id", help="Agent id to resolve from --config-json.")
    parser.add_argument("--model", help="Single model to benchmark.")
    parser.add_argument("--models", help="Comma-separated model list to benchmark.")
    parser.add_argument("--case-names", help="Comma-separated explicit case names to run.")
    parser.add_argument("--repeat", type=int, default=1, help="Repeat count for each row.")
    parser.add_argument(
        "--execution-mode",
        choices=("sequential", "parallel"),
        default="sequential",
        help="Whether to run rows sequentially or in parallel.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=2,
        help="Maximum worker count when execution mode is parallel.",
    )
    parser.add_argument(
        "--run-scope",
        choices=("api", "chatgpt", "both"),
        default="both",
        help="Whether to run API rows, ChatGPT rows, or both.",
    )
    parser.add_argument(
        "--desired-input-tokens",
        type=int,
        default=DEFAULT_DESIRED_INPUT_TOKENS,
        help="Approximate target input tokens for each request.",
    )
    parser.add_argument(
        "--desired-output-tokens",
        type=int,
        default=DEFAULT_DESIRED_OUTPUT_TOKENS,
        help="Approximate target output tokens for the transformed text.",
    )
    parser.add_argument(
        "--output",
        help="Path to the report text file. Defaults to artifacts/openai_responses_tier_matrix_<label>_<timestamp>.txt",
    )
    parser.add_argument(
        "--profile",
        help="Logical profile label stored in the cumulative JSON results.",
    )
    parser.add_argument(
        "--results-json",
        default=str(DEFAULT_RESULTS_JSON_PATH),
        help="Path to the cumulative JSON results store.",
    )
    parser.add_argument(
        "--chatgpt-credentials-path",
        default=str(_default_credentials_path()),
        help="Path to saved ChatGPT credentials JSON.",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")
    args = _parse_args()

    resolved_target: Optional[ResolvedBenchmarkTarget] = None
    if args.agent_config_json:
        if args.config_json or args.agent_id:
            raise RuntimeError(
                "--agent-config-json cannot be combined with --config-json/--agent-id"
            )
        resolved_target = _resolve_simplified_agent_target(
            Path(args.agent_config_json).expanduser()
        )
    elif args.config_json or args.agent_id:
        if not (args.config_json and args.agent_id):
            raise RuntimeError("--config-json and --agent-id must be provided together")
        resolved_target = _resolve_agent_target(Path(args.config_json).expanduser(), args.agent_id)

    models = parse_models(
        args.model or (resolved_target.model if resolved_target is not None else None),
        args.models,
    )
    batch_started_at = datetime.now(timezone.utc).isoformat()
    output_path = Path(args.output).expanduser() if args.output else _default_output_path(models)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_json_path = Path(args.results_json).expanduser()
    profile = args.profile or _default_profile(args.desired_input_tokens, args.desired_output_tokens)

    provider_family = (
        resolved_target.family if resolved_target is not None else OPENAI_RESPONSES_FAMILY
    )
    cases = parse_case_names(args.case_names, build_matrix_cases(args.run_scope, provider_family))
    credentials_path: Optional[Path] = None
    if provider_family == OPENAI_RESPONSES_FAMILY and any(case.auth_mode == "chatgpt" for case in cases):
        credentials_path = Path(args.chatgpt_credentials_path).expanduser()
        _load_saved_credentials(credentials_path)

    if (
        provider_family == OPENAI_RESPONSES_FAMILY
        and any(case.auth_mode == "api" for case in cases)
        and not os.getenv("OPENAI_API_KEY")
    ):
        raise RuntimeError("OPENAI_API_KEY is required for API matrix rows")

    specs = build_run_specs(
        models=models,
        cases=cases,
        repeat=args.repeat,
        desired_input_tokens=args.desired_input_tokens,
        desired_output_tokens=args.desired_output_tokens,
    )
    results = run_specs(
        provider_family,
        specs=specs,
        credentials_path=credentials_path,
        desired_output_tokens=args.desired_output_tokens,
        execution_mode=args.execution_mode,
        max_workers=args.max_workers,
        base_agent_config=(resolved_target.config if resolved_target is not None else None),
    )
    summaries = _aggregate_results(results)

    lines: List[str] = [
        f"models={','.join(models)}",
        f"provider_family={provider_family}",
        f"started_at={batch_started_at}",
        f"profile={profile}",
        f"repeat={args.repeat}",
        f"execution_mode={args.execution_mode}",
        f"max_workers={args.max_workers}",
        f"run_scope={args.run_scope}",
        f"desired_input_tokens={args.desired_input_tokens}",
        f"desired_output_tokens={args.desired_output_tokens}",
        "",
    ]

    for result in results:
        lines.extend(_format_metric_lines(result))
    lines.extend(_format_summary_lines(summaries))

    output_path.write_text("\n".join(lines), encoding="utf-8")
    append_results_store(
        results_json_path,
        _build_result_records(
            results=results,
            profile=profile,
            artifact_path=output_path,
            batch_started_at=batch_started_at,
            desired_input_tokens=args.desired_input_tokens,
            desired_output_tokens=args.desired_output_tokens,
            execution_mode=args.execution_mode,
            max_workers=args.max_workers,
            run_scope=args.run_scope,
        ),
    )
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())