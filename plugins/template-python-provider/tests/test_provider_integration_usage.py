from __future__ import annotations

import os
from typing import Any, Dict, List

import pytest

import provider_test_config as cfg
from _helpers import build_core, import_symbol, run_streaming


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


def _load_usage_extension_class() -> type:
    if not cfg.USAGE_EXTENSION_CLASS_PATH:
        pytest.skip("USAGE_EXTENSION_CLASS_PATH is not set in provider_test_config.py")
    return import_symbol(cfg.USAGE_EXTENSION_CLASS_PATH)


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
def test_usage_metadata_attached_streaming_two_turns() -> None:
    provider_cls = _load_provider_class()
    usage_ext_cls = _load_usage_extension_class()
    feature_classes = _load_feature_classes()

    core = build_core(provider_cls, extensions=[usage_ext_cls], features=feature_classes)
    config: Dict[str, Any] = _base_config()

    # ---- First turn ----
    session = core.create_session()
    session = core.add_message(session, "user", "Say a short greeting.")
    session, finals1, _partial_text1 = run_streaming(core, session, config)

    assert finals1 and finals1[-1].get("role") == "assistant"
    md1 = finals1[-1].get("metadata") or {}
    usage1 = md1.get("usage")
    assert isinstance(usage1, dict), "expected metadata['usage'] dict"

    # ---- Second turn ----
    session = core.add_message(session, "user", "Say another short greeting.", config=config)
    _session2, finals2, _partial_text2 = run_streaming(core, session, config)

    assert finals2 and finals2[-1].get("role") == "assistant"
    md2 = finals2[-1].get("metadata") or {}
    usage2 = md2.get("usage")
    assert isinstance(usage2, dict), "expected metadata['usage'] dict"

    # Many usage/cost extensions attach cumulative fields. If your provider does not,
    # adjust the assertions here.
    cumulative_cost = md2.get("usage_total_cost_cumulative")
    cumulative_cost_str = md2.get("usage_total_cost_cumulative_formatted")
    assert isinstance(cumulative_cost, (int, float))
    assert isinstance(cumulative_cost_str, str) and cumulative_cost_str
