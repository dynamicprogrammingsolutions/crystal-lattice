from __future__ import annotations

import hashlib
import json
import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))

from agent_app.config import (  # noqa: E402
    build_config_resolution_env,
    resolve_placeholders,
)

CONFIG_PATH = (
    ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "config.json"
)
CODEX_DIR = (
    ROOT / "application" / "python" / "agent_terminal_app" / "default_config" / "codex"
)
REFERENCE_CODEX_DIR = (
    ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "system_messages"
    / "reference"
    / "default-system-instructions"
    / "codex"
)
HELPER_PATH = (
    ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "system_messages"
    / "helpers"
    / "select_codex_developer_message.py"
)

# Upstream commit e9633d7a0226eac91c7a791dc4f92cf8f25df2ae (2026-09-14);
# template content introduced 2026-09-04 by 83b62a02fab5c0fc797cbc9896c332148f1fd9d0.
GPT_6_ASTRA_DATE = "20260904"
GPT_6_ASTRA_TEMPLATE_SHA256 = (
    "152dfaeeb552876190962be1c12c93d426840ff12691f648261554a7675a6698"
)
GPT_6_ASTRA_PERSISTENT_SHA256 = (
    "30747e79e50efb64f91cfff3d5ef1882e347081e81448918d5f7d5358e98c523"
)
GPT_6_DISTINCTIVE_SUBSTRING = "You are Codex, an agent based on GPT-6"
GPT_6_CONNECTOR_PLACEHOLDER = "app://{{connector_id}}"


def _load_codex_rows() -> list[dict]:
    raw_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    resolution_env = build_config_resolution_env(CONFIG_PATH)
    # Force CONFIG_DIR to the default config directory so ${file:...} placeholders
    # resolve against the checked-in default config assets, not a user-installed
    # config dir that may exist in the test environment.
    resolution_env["CONFIG_DIR"] = str(CONFIG_PATH.parent.resolve())
    resolved_config, _errors = resolve_placeholders(raw_config, env=resolution_env)
    return resolved_config["mixins"]["codex_developer_message"][
        "codex_developer_messages"
    ]


def _run_helper(model: str, personality: str | None) -> str:
    rows = _load_codex_rows()
    config: dict = {"codex_developer_messages": rows, "model": model}
    if personality is not None:
        config["codex_personality"] = personality
    namespace = runpy.run_path(str(HELPER_PATH), init_globals={"CONFIG": config})
    return namespace["select_codex_developer_message"]()


def _instruction_text(model: str, personality: str | None = None) -> str:
    return _run_helper(model, personality)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _asset(name: str) -> Path:
    return CODEX_DIR / "gpt-6-astra" / name


def test_gpt_6_astra_selects_dated_instruction_asset() -> None:
    text = _instruction_text("gpt-6-astra")
    expected = _asset(f"instructions_default.{GPT_6_ASTRA_DATE}.md").read_text(
        encoding="utf-8"
    )
    assert text == expected


def test_openai_prefixed_gpt_6_astra_selects_correctly() -> None:
    text = _instruction_text("openai/gpt-6-astra")
    expected = _asset(f"instructions_default.{GPT_6_ASTRA_DATE}.md").read_text(
        encoding="utf-8"
    )
    assert text == expected


def test_bare_gpt_6_alias_does_not_select_gpt_6_astra_template() -> None:
    text = _instruction_text("gpt-6")
    astra = _asset(f"instructions_default.{GPT_6_ASTRA_DATE}.md").read_text(
        encoding="utf-8"
    )
    assert text != astra
    fallback = (CODEX_DIR / "gpt-5" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    assert text == fallback


def test_personality_selection_resolves_to_same_template() -> None:
    default_text = _instruction_text("gpt-6-astra", "default")
    friendly_text = _instruction_text("gpt-6-astra", "friendly")
    pragmatic_text = _instruction_text("gpt-6-astra", "pragmatic")
    none_text = _instruction_text("gpt-6-astra", None)
    assert default_text == friendly_text == pragmatic_text == none_text


def test_config_row_has_no_personality_field() -> None:
    raw_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    raw_rows = raw_config["mixins"]["codex_developer_message"][
        "codex_developer_messages"
    ]
    row = next(
        (r for r in raw_rows if r.get("model_regex") == r"^(openai/)?gpt-6-astra$"),
        None,
    )
    assert row is not None, "gpt-6-astra config row missing"
    assert "personality" not in row
    assert f"instructions_default.{GPT_6_ASTRA_DATE}.md" in row["text"]


def test_compiled_instructions_contain_distinctive_gpt_6_substring() -> None:
    text = _instruction_text("gpt-6-astra")
    assert GPT_6_DISTINCTIVE_SUBSTRING in text


def test_connector_id_placeholder_is_kept_verbatim() -> None:
    text = _instruction_text("gpt-6-astra")
    assert GPT_6_CONNECTOR_PLACEHOLDER in text


def test_instructions_default_is_byte_identical_to_raw_template() -> None:
    effective = _asset(f"instructions_default.{GPT_6_ASTRA_DATE}.md").read_text(
        encoding="utf-8"
    )
    template = _asset(
        f"model_messages.instructions_template.{GPT_6_ASTRA_DATE}.md"
    ).read_text(encoding="utf-8")
    assert effective == template


def test_gpt_6_astra_assets_match_upstream_sha256() -> None:
    template_sha = _file_sha256(
        _asset(f"model_messages.instructions_template.{GPT_6_ASTRA_DATE}.md")
    )
    assert template_sha == GPT_6_ASTRA_TEMPLATE_SHA256
    persistent_sha = _file_sha256(
        _asset(f"model_messages.persistent_instructions.{GPT_6_ASTRA_DATE}.md")
    )
    assert persistent_sha == GPT_6_ASTRA_PERSISTENT_SHA256


def test_gpt_6_astra_instructions_variables_is_empty() -> None:
    variables = json.loads(
        _asset(
            f"model_messages.instructions_variables.{GPT_6_ASTRA_DATE}.json"
        ).read_text(encoding="utf-8")
    )
    assert variables == {}


def test_gpt_6_astra_template_is_distinct_from_gpt_56_family() -> None:
    astra = _instruction_text("gpt-6-astra")
    for model in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"):
        family_text = _instruction_text(model)
        assert astra != family_text, model
    # The GPT-6 template opens with the GPT-6 identity line, not GPT-5.
    assert "based on GPT-6" in astra
    assert "based on GPT-5" not in astra


def test_reference_copies_match_assets() -> None:
    ref_dir = REFERENCE_CODEX_DIR / "gpt-6-astra"
    for name in (
        f"instructions_default.{GPT_6_ASTRA_DATE}.md",
        f"model_messages.instructions_template.{GPT_6_ASTRA_DATE}.md",
        f"model_messages.instructions_variables.{GPT_6_ASTRA_DATE}.json",
        f"model_messages.persistent_instructions.{GPT_6_ASTRA_DATE}.md",
    ):
        asset_bytes = (CODEX_DIR / "gpt-6-astra" / name).read_bytes()
        ref_bytes = (ref_dir / name).read_bytes()
        assert asset_bytes == ref_bytes, name


def test_gpt_6_astra_row_precedes_gpt_56_rows() -> None:
    rows = _load_codex_rows()
    astra_index = next(
        i
        for i, r in enumerate(rows)
        if r.get("model_regex") == r"^(openai/)?gpt-6-astra$"
    )
    sol_index = next(
        i
        for i, r in enumerate(rows)
        if r.get("model_regex") == r"^(openai/)?gpt-5\.6-sol$"
    )
    assert astra_index < sol_index
