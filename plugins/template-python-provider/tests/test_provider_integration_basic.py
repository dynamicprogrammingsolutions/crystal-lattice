from __future__ import annotations

import os
from typing import Any, Dict, List

import pytest

import provider_test_config as cfg
from _helpers import build_core, import_symbol, run_non_streaming, run_streaming


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
def test_basic_non_streaming() -> None:
    provider_cls = _load_provider_class()
    feature_classes = _load_feature_classes()
    config = _base_config()

    core = build_core(provider_cls, features=feature_classes)
    session = core.create_session()
    session = core.add_message(session, "user", "Say 'Hello' and nothing else.")

    _session2, finals = run_non_streaming(core, session, config)
    assert finals and finals[-1].get("role") == "assistant"
    assert isinstance(finals[-1].get("content"), str) and finals[-1]["content"]


@pytest.mark.xfail(
    not INTEGRATION_ENABLED,
    reason="Integration scaffolds are disabled; set INTEGRATION_ENABLED=True in provider_test_config.py",
    run=False,
)
def test_basic_streaming() -> None:
    provider_cls = _load_provider_class()
    feature_classes = _load_feature_classes()
    config = _base_config()

    core = build_core(provider_cls, features=feature_classes)
    session = core.create_session()
    session = core.add_message(session, "user", "Write a short haiku about programming.")

    _session2, finals, partial_text = run_streaming(core, session, config)
    assert partial_text, "expected at least one partial content fragment"
    assert finals and finals[-1].get("role") == "assistant"
