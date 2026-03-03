from __future__ import annotations

import os
from typing import Any, Dict, List

import pytest

import provider_test_config as cfg
from _helpers import (
    build_core,
    extract_tool_calls,
    import_symbol,
    run_non_streaming,
    run_streaming,
)


pytestmark = [pytest.mark.integration]


INTEGRATION_ENABLED = bool(getattr(cfg, "INTEGRATION_ENABLED", False))


def _load_provider_class() -> type:
    if not cfg.PROVIDER_CLASS_PATH:
        pytest.skip("PROVIDER_CLASS_PATH is not set in provider_test_config.py")
    return import_symbol(cfg.PROVIDER_CLASS_PATH)


def _load_feature_classes() -> List[type]:
    classes: List[type] = []
    for path in getattr(cfg, "FEATURE_CLASS_PATHS", []) or []:
        if not isinstance(path, str) or not path:
            continue
        classes.append(import_symbol(path))
    return classes


def _load_tools_extension_class() -> type:
    if not cfg.TOOLS_EXTENSION_CLASS_PATH:
        pytest.skip("TOOLS_EXTENSION_CLASS_PATH is not set in provider_test_config.py")
    return import_symbol(cfg.TOOLS_EXTENSION_CLASS_PATH)


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

    out: Dict[str, Any] = {"model": cfg.MODEL}

    api_key_env = cfg.API_KEY_ENV_VAR
    if api_key_env:
        api_key = os.getenv(api_key_env)
        if not api_key:
            pytest.skip(f"{api_key_env} is not set")
        out["api_key"] = api_key

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
    not INTEGRATION_ENABLED,
    reason="Integration scaffolds are disabled; set INTEGRATION_ENABLED=True in provider_test_config.py",
    run=False,
)
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_single_tool_call_math(stream: bool) -> None:
    provider_cls = _load_provider_class()
    tools_ext_cls = _load_tools_extension_class()
    feature_classes = _load_feature_classes()
    tool_classes = _load_tool_classes()

    core = build_core(
        provider_cls,
        extensions=[tools_ext_cls],
        features=feature_classes,
        tools=tool_classes,
    )

    config: Dict[str, Any] = {
        **_base_config(),
        "temperature": 0.0,
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. When asked to perform calculations, "
        "you MUST use the provided tools and never calculate manually.",
    )
    session = core.add_message(
        session,
        "user",
        "Use the add tool to calculate 15 + 27. Return only the result.",
    )

    # Round 1: expect tool call
    if stream:
        session, finals, _partial_text = run_streaming(core, session, config)
    else:
        session, finals = run_non_streaming(core, session, config)

    tool_calls = extract_tool_calls(finals)
    assert tool_calls, "expected at least one tool call"

    tool_msgs = core.execute_tool_calls(tool_calls, config)
    assert tool_msgs, "expected tool results"
    for tm in tool_msgs:
        session = core.add_message(
            session,
            role=tm.get("role", "tool"),
            content=str(tm.get("content", "")),
            metadata=tm.get("metadata"),
            config=config,
        )

    # Round 2: expect final answer
    if stream:
        _session2, finals2, _partial_text2 = run_streaming(core, session, config)
    else:
        _session2, finals2 = run_non_streaming(core, session, config)

    assert finals2 and finals2[-1].get("role") == "assistant"
    content = str(finals2[-1].get("content") or "")
    assert "42" in content
