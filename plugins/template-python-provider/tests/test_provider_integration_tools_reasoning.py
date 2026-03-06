from __future__ import annotations

import os
from typing import Any, Dict, List

import pytest

import provider_test_config as cfg
from _helpers import build_core, import_symbol, run_tool_loop


pytestmark = [pytest.mark.integration]


def _load_provider_class() -> type:
    if not cfg.PROVIDER_CLASS_PATH:
        pytest.skip("PROVIDER_CLASS_PATH is not set in provider_test_config.py")
    return import_symbol(cfg.PROVIDER_CLASS_PATH)


def _load_reasoning_extension_class() -> type:
    if not cfg.REASONING_EXTENSION_CLASS_PATH:
        pytest.skip("REASONING_EXTENSION_CLASS_PATH is not set in provider_test_config.py")
    return import_symbol(cfg.REASONING_EXTENSION_CLASS_PATH)


def _load_tools_extension_class() -> type:
    if not cfg.TOOLS_EXTENSION_CLASS_PATH:
        pytest.skip("TOOLS_EXTENSION_CLASS_PATH is not set in provider_test_config.py")
    return import_symbol(cfg.TOOLS_EXTENSION_CLASS_PATH)


def _load_feature_classes() -> List[type]:
    classes: List[type] = []
    for path in getattr(cfg, "FEATURE_CLASS_PATHS", []) or []:
        if not isinstance(path, str) or not path:
            continue
        classes.append(import_symbol(path))
    return classes


def _load_tool_classes() -> List[type]:
    classes: List[type] = []
    for path in getattr(cfg, "TOOL_CLASS_PATHS", []) or []:
        if not isinstance(path, str) or not path:
            continue
        classes.append(import_symbol(path))
    return classes


def _base_config() -> Dict[str, Any]:
    if not cfg.MODEL:
        pytest.skip("MODEL is not set in provider_test_config.py")

    api_key_env = cfg.API_KEY_ENV_VAR
    if not api_key_env:
        pytest.skip("API_KEY_ENV_VAR is not set in provider_test_config.py")

    api_key = os.getenv(api_key_env)
    if not api_key:
        pytest.skip(f"{api_key_env} is not set")

    out: Dict[str, Any] = {"model": cfg.MODEL, "api_key": api_key}

    if cfg.BASE_URL:
        out["base_url"] = cfg.BASE_URL

    timeout = getattr(cfg, "TIMEOUT", None)
    if isinstance(timeout, int) and timeout > 0:
        out["timeout"] = timeout

    extra = getattr(cfg, "EXTRA_CONFIG", None)
    if isinstance(extra, dict) and extra:
        out.update(extra)

    return out


@pytest.mark.xfail(
    reason="Integration scaffold: remove xfail once your provider passes this test",
    strict=True,
)
def test_tools_and_reasoning_work_together() -> None:
    provider_cls = _load_provider_class()
    reasoning_ext_cls = _load_reasoning_extension_class()
    tools_ext_cls = _load_tools_extension_class()
    feature_classes = _load_feature_classes()
    tool_classes = _load_tool_classes()

    core = build_core(
        provider_cls,
        extensions=[reasoning_ext_cls, tools_ext_cls],
        features=feature_classes,
        tools=tool_classes,
    )

    config: Dict[str, Any] = {
        **_base_config(),
        "temperature": 0.0,
        "enable_reasoning": True,
        "reasoning_effort": "low",
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "Use tools for calculations. Also include reasoning if supported.",
    )
    session = core.add_message(
        session,
        "user",
        "Use the add tool to calculate 15 + 27. Return the result.",
    )

    _session2, finals = run_tool_loop(core, session, config, max_iters=5)
    assert finals and finals[-1].get("role") == "assistant"

    content = str(finals[-1].get("content") or "")
    assert "42" in content

    md = finals[-1].get("metadata") or {}
    reasoning = md.get("reasoning")
    assert isinstance(reasoning, str) and reasoning.strip(), "expected non-empty metadata['reasoning']"
