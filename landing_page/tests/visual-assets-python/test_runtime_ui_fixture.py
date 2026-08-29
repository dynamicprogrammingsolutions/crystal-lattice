from __future__ import annotations

import importlib.util
import json
from pathlib import Path

LANDING_ROOT = Path(__file__).resolve().parents[2]
ROOT = LANDING_ROOT.parent
MODULE_PATH = (
    LANDING_ROOT / "scripts" / "visual-assets" / "refresh_runtime_ui_fixture.py"
)
SPEC = importlib.util.spec_from_file_location("refresh_runtime_ui_fixture", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_canonical_runtime_ui_fixture_is_deterministic_and_plugin_driven() -> None:
    config_path = (
        LANDING_ROOT / "visual_assets" / "runtime" / "mobile-workbench" / "config.json"
    )
    session_fixture_path = (
        ROOT
        / "mobile"
        / "crystal-lattice-control-rn"
        / "src"
        / "testing"
        / "fixtures"
        / "websiteCodingPlanSession.json"
    )

    first = module.build_runtime_ui_fixture(
        repository_root=ROOT,
        config_path=config_path,
        session_fixture_path=session_fixture_path,
        agent_id="codex-openai",
    )
    second = module.build_runtime_ui_fixture(
        repository_root=ROOT,
        config_path=config_path,
        session_fixture_path=session_fixture_path,
        agent_id="codex-openai",
    )

    assert first == second
    session_actions = {
        element["id"]: element
        for element in first["session_application_ui_schema"]
        if element.get("ui_type") == "session_action"
    }
    assert session_actions["copy_session_from_view"]["order"] == 10
    assert session_actions["edit_title_from_view"]["order"] == 15
    assert session_actions["compact_native_history"]["order"] == 46

    message_actions = {
        element["id"]: element
        for element in [
            *first["session_application_ui_schema"],
            *first["session_ui_schema"],
        ]
        if element.get("ui_type") == "message_action"
    }
    assert (
        message_actions["compact_native_history_through_message"]["param_map"][
            "message_index"
        ]
        == "$message.index"
    )
    assert [item["key"] for item in first["session_ui_schema"]] == [
        "model",
        "reasoning_effort",
        "verbosity",
        "enable_prompt_cache_key",
        "enable_web_search",
        "use_compaction_placeholder_transcript",
    ]
    assert [item["reason"] for item in first["snapshots"]] == [
        "Before compacting conversation [:3]",
        "Before deleting messages [3:]",
        "Initial repository review",
    ]

    encoded = json.dumps(first)
    assert "website-runtime-fixture-not-used" not in encoded
    assert str(Path.home()) not in encoded
