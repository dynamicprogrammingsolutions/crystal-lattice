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

GPT_56_SOL_SHA256 = "e9778714d505f3dd04d44db4394024c5fab5bf6554fc9faa3cdf9cf776b63bb9"
GPT_56_TERRA_LUNA_SHA256 = (
    "78a2fc84e1bffa421d865c1a2ade4185d3d33ef38e6a15157f0ff1a89b7d52ec"
)
GPT_56_DISTINCTIVE_SUBSTRING = "You are Codex, an agent based on GPT-5"
SOL_SPECIFIC_PARAGRAPH_POSITION = (
    "they feel like you understand them.\n\n" "When presented with clarifying questions"
)


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


def test_gpt_56_sol_selects_sol_instruction_asset() -> None:
    text = _instruction_text("gpt-5.6-sol")
    expected = (CODEX_DIR / "gpt-5.6-sol" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    assert text == expected


def test_gpt_56_terra_selects_terra_instruction_asset() -> None:
    text = _instruction_text("gpt-5.6-terra")
    expected = (CODEX_DIR / "gpt-5.6-terra" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    assert text == expected


def test_gpt_56_luna_selects_luna_instruction_asset() -> None:
    text = _instruction_text("gpt-5.6-luna")
    expected = (CODEX_DIR / "gpt-5.6-luna" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    assert text == expected


def test_openai_prefixed_gpt_56_ids_select_correctly() -> None:
    for model, expected_dir in (
        ("openai/gpt-5.6-sol", "gpt-5.6-sol"),
        ("openai/gpt-5.6-terra", "gpt-5.6-terra"),
        ("openai/gpt-5.6-luna", "gpt-5.6-luna"),
    ):
        text = _instruction_text(model)
        expected = (CODEX_DIR / expected_dir / "instructions_default.md").read_text(
            encoding="utf-8"
        )
        assert text == expected, (model, expected_dir)


def test_bare_gpt_56_alias_does_not_select_gpt_56_template() -> None:
    text = _instruction_text("gpt-5.6")
    gpt_56_sol = (CODEX_DIR / "gpt-5.6-sol" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    gpt_56_terra = (CODEX_DIR / "gpt-5.6-terra" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    gpt_56_luna = (CODEX_DIR / "gpt-5.6-luna" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    assert text != gpt_56_sol
    assert text != gpt_56_terra
    assert text != gpt_56_luna
    fallback = (CODEX_DIR / "gpt-5" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    assert text == fallback


def test_sol_content_is_distinct_from_terra_luna() -> None:
    sol = (CODEX_DIR / "gpt-5.6-sol" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    terra = (CODEX_DIR / "gpt-5.6-terra" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    luna = (CODEX_DIR / "gpt-5.6-luna" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    assert sol != terra
    assert sol != luna
    assert SOL_SPECIFIC_PARAGRAPH_POSITION in sol
    assert SOL_SPECIFIC_PARAGRAPH_POSITION not in terra
    assert SOL_SPECIFIC_PARAGRAPH_POSITION not in luna


def test_terra_and_luna_mappings_are_both_present() -> None:
    assert (CODEX_DIR / "gpt-5.6-terra" / "instructions_default.md").is_file()
    assert (CODEX_DIR / "gpt-5.6-luna" / "instructions_default.md").is_file()
    raw_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    raw_rows = raw_config["mixins"]["codex_developer_message"][
        "codex_developer_messages"
    ]
    terra_row = next(
        (r for r in raw_rows if r.get("model_regex") == r"^(openai/)?gpt-5\.6-terra$"),
        None,
    )
    luna_row = next(
        (r for r in raw_rows if r.get("model_regex") == r"^(openai/)?gpt-5\.6-luna$"),
        None,
    )
    assert terra_row is not None, "gpt-5.6-terra config row missing"
    assert luna_row is not None, "gpt-5.6-luna config row missing"
    assert "gpt-5.6-terra" in terra_row["text"]
    assert "gpt-5.6-luna" in luna_row["text"]
    # Verify the resolved text matches the file content
    resolved_rows = _load_codex_rows()
    resolved_terra = next(
        (
            r
            for r in resolved_rows
            if r.get("model_regex") == r"^(openai/)?gpt-5\.6-terra$"
        ),
        None,
    )
    resolved_luna = next(
        (
            r
            for r in resolved_rows
            if r.get("model_regex") == r"^(openai/)?gpt-5\.6-luna$"
        ),
        None,
    )
    assert resolved_terra is not None and resolved_luna is not None
    terra_file = (CODEX_DIR / "gpt-5.6-terra" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    luna_file = (CODEX_DIR / "gpt-5.6-luna" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    assert resolved_terra["text"] == terra_file
    assert resolved_luna["text"] == luna_file


def test_terra_and_luna_instructions_are_byte_identical() -> None:
    terra_sha = _file_sha256(CODEX_DIR / "gpt-5.6-terra" / "instructions_default.md")
    luna_sha = _file_sha256(CODEX_DIR / "gpt-5.6-luna" / "instructions_default.md")
    assert terra_sha == luna_sha == GPT_56_TERRA_LUNA_SHA256


def test_personality_selection_resolves_to_same_template() -> None:
    default_text = _instruction_text("gpt-5.6-luna", "default")
    friendly_text = _instruction_text("gpt-5.6-luna", "friendly")
    pragmatic_text = _instruction_text("gpt-5.6-luna", "pragmatic")
    none_text = _instruction_text("gpt-5.6-luna", None)
    assert default_text == friendly_text == pragmatic_text == none_text
    template = (
        CODEX_DIR / "gpt-5.6-luna" / "model_messages.instructions_template.md"
    ).read_text(encoding="utf-8")
    assert default_text == template


def test_older_model_mappings_remain_unchanged() -> None:
    cases = {
        "gpt-5.5": "gpt-5.5/instructions_default.md",
        "gpt-5.4": "gpt-5.4/instructions_default.md",
        "gpt-5.2-codex": "gpt-5.2-codex/instructions_default.md",
        "gpt-5.1-codex": "gpt-5.1-codex/instructions_default.md",
        "gpt-5": "gpt-5/instructions_default.md",
    }
    for model, expected_rel in cases.items():
        text = _instruction_text(model)
        expected = (CODEX_DIR / expected_rel).read_text(encoding="utf-8")
        assert text == expected, (model, expected_rel)


def test_compiled_top_level_instructions_contain_distinctive_gpt_56_substring() -> None:
    for model in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"):
        text = _instruction_text(model)
        assert GPT_56_DISTINCTIVE_SUBSTRING in text, model


def test_gpt_56_source_assets_match_upstream_sha256() -> None:
    sol_sha = _file_sha256(CODEX_DIR / "gpt-5.6-sol" / "base_instructions.md")
    terra_sha = _file_sha256(CODEX_DIR / "gpt-5.6-terra" / "base_instructions.md")
    luna_sha = _file_sha256(CODEX_DIR / "gpt-5.6-luna" / "base_instructions.md")
    assert sol_sha == GPT_56_SOL_SHA256
    assert terra_sha == GPT_56_TERRA_LUNA_SHA256
    assert luna_sha == GPT_56_TERRA_LUNA_SHA256
