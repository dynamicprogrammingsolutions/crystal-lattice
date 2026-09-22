from __future__ import annotations

import importlib.util
from pathlib import Path


HOOK_PATH = Path(__file__).resolve().parents[1] / "hooks" / "analytics.py"
SPEC = importlib.util.spec_from_file_location("docs_analytics_hook", HOOK_PATH)
assert SPEC and SPEC.loader
analytics_hook = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analytics_hook)


def config(script_url: str = "", website_id: str = "") -> dict:
    return {
        "extra": {
            "crystal_lattice": {
                "analytics": {
                    "script_url": script_url,
                    "website_id": website_id,
                }
            }
        }
    }


def test_valid_configuration_is_enabled() -> None:
    result = analytics_hook.on_config(
        config(
            analytics_hook.APPROVED_SCRIPT_URL,
            "123e4567-e89b-42d3-a456-426614174000",
        )
    )
    analytics = result["extra"]["crystal_lattice"]["analytics"]
    assert analytics["enabled"] is True
    assert analytics["domain"] == "docs.crystallattice.dev"


def test_missing_or_invalid_configuration_is_disabled() -> None:
    config_after = analytics_hook.on_config(config())
    assert config_after["extra"]["crystal_lattice"]["analytics"]["enabled"] is False
    invalid_url = analytics_hook.on_config(
        config("https://example.com/insight.js", "123e4567-e89b-42d3-a456-426614174000")
    )
    assert invalid_url["extra"]["crystal_lattice"]["analytics"]["enabled"] is False
    invalid_id = analytics_hook.on_config(
        config(analytics_hook.APPROVED_SCRIPT_URL, "not-a-uuid")
    )
    assert invalid_id["extra"]["crystal_lattice"]["analytics"]["enabled"] is False
