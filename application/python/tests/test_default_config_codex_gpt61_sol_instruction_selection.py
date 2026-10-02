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

# Upstream commit ca466061d64f0b44f416135c7fd06aa7af850bbc (2026-10-02);
# template introduced 2026-09-29 by b1e72963c3b7 (#49318).
GPT_61_DATE = "20260929"
GPT_61_TEMPLATE_SHA256 = (
    "e1bdd4f8f0df4b20f4a0ffc8a861ce819df45325d8cecdfb92e80379cf8d142e"
)
GPT_6_PERSISTENT_SHA256 = (
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


def _asset(model: str, name: str) -> Path:
    return CODEX_DIR / model / name


def test_gpt_61_sol_selects_dated_instruction_asset() -> None:
    text = _instruction_text("gpt-6.1-sol")
    expected = _asset(
        "gpt-6.1-sol", f"instructions_default.{GPT_61_DATE}.md"
    ).read_text(encoding="utf-8")
    assert text == expected


def test_openai_prefixed_gpt_61_sol_selects_correctly() -> None:
    model = "openai/gpt-6.1-sol"
    text = _instruction_text(model)
    expected = _asset(
        model.removeprefix("openai/"),
        f"instructions_default.{GPT_61_DATE}.md",
    ).read_text(encoding="utf-8")
    assert text == expected, model


def test_bare_gpt_6_and_gpt_6_1_aliases_do_not_select_gpt_6_1_template() -> None:
    for alias in ("gpt-6", "gpt-6.1"):
        text = _instruction_text(alias)
        assert text != _asset(
            "gpt-6.1-sol", f"instructions_default.{GPT_61_DATE}.md"
        ).read_text(encoding="utf-8"), alias
        fallback = (CODEX_DIR / "gpt-5" / "instructions_default.md").read_text(
            encoding="utf-8"
        )
        assert text == fallback, alias


def test_personality_selection_resolves_to_same_template() -> None:
    model = "gpt-6.1-sol"
    default_text = _instruction_text(model, "default")
    friendly_text = _instruction_text(model, "friendly")
    pragmatic_text = _instruction_text(model, "pragmatic")
    none_text = _instruction_text(model, None)
    assert default_text == friendly_text == pragmatic_text == none_text


def test_config_rows_have_no_personality_field() -> None:
    raw_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    raw_rows = raw_config["mixins"]["codex_developer_message"][
        "codex_developer_messages"
    ]
    model = "gpt-6\.1-sol"
    row = next(
        (r for r in raw_rows if r.get("model_regex") == rf"^(openai/)?{model}$"),
        None,
    )
    assert row is not None, f"{model} config row missing"
    assert "personality" not in row
    assert f"instructions_default.{GPT_61_DATE}.md" in row["text"]


def test_compiled_instructions_contain_distinctive_gpt_6_substring() -> None:
    text = _instruction_text("gpt-6.1-sol")
    assert GPT_6_DISTINCTIVE_SUBSTRING in text


def test_connector_id_placeholder_is_kept_verbatim() -> None:
    text = _instruction_text("gpt-6.1-sol")
    assert GPT_6_CONNECTOR_PLACEHOLDER in text


def test_instructions_default_is_byte_identical_to_raw_template() -> None:
    effective = _asset(
        "gpt-6.1-sol", f"instructions_default.{GPT_61_DATE}.md"
    ).read_text(encoding="utf-8")
    template = _asset(
        "gpt-6.1-sol", f"model_messages.instructions_template.{GPT_61_DATE}.md"
    ).read_text(encoding="utf-8")
    assert effective == template


def test_gpt_61_sol_assets_match_upstream_sha256() -> None:
    template_sha = _file_sha256(
        _asset("gpt-6.1-sol", f"model_messages.instructions_template.{GPT_61_DATE}.md")
    )
    assert template_sha == GPT_61_TEMPLATE_SHA256
    persistent_sha = _file_sha256(
        _asset(
            "gpt-6.1-sol",
            f"model_messages.persistent_instructions.{GPT_61_DATE}.md",
        )
    )
    assert persistent_sha == GPT_6_PERSISTENT_SHA256


def test_gpt_61_sol_instructions_variables_are_empty() -> None:
    variables = json.loads(
        _asset(
            "gpt-6.1-sol",
            f"model_messages.instructions_variables.{GPT_61_DATE}.json",
        ).read_text(encoding="utf-8")
    )
    assert variables == {}


def test_gpt_61_sol_template_is_distinct_from_other_families() -> None:
    sol61 = _instruction_text("gpt-6.1-sol")
    others = [
        _instruction_text(m)
        for m in ("gpt-6-sol", "gpt-6-luna", "gpt-6-astra", "gpt-5.6-sol")
    ]
    assert all(sol61 != other for other in others)
    # The rest of the GPT-6 family remains pairwise distinct.
    assert len(set(others[:3])) == 3


def test_reference_copies_match_assets() -> None:
    ref_dir = REFERENCE_CODEX_DIR / "gpt-6.1-sol"
    for name in (
        f"instructions_default.{GPT_61_DATE}.md",
        f"model_messages.instructions_template.{GPT_61_DATE}.md",
        f"model_messages.instructions_variables.{GPT_61_DATE}.json",
        f"model_messages.persistent_instructions.{GPT_61_DATE}.md",
    ):
        asset_bytes = (CODEX_DIR / "gpt-6.1-sol" / name).read_bytes()
        ref_bytes = (ref_dir / name).read_bytes()
        assert asset_bytes == ref_bytes, name


def test_gpt_61_sol_row_precedes_gpt_6_family_rows() -> None:
    rows = _load_codex_rows()

    def index_of(pattern: str) -> int:
        return next(i for i, r in enumerate(rows) if r.get("model_regex") == pattern)

    sol61_index = index_of(r"^(openai/)?gpt-6\.1-sol$")
    sol_index = index_of(r"^(openai/)?gpt-6-sol$")
    luna_index = index_of(r"^(openai/)?gpt-6-luna$")
    astra_index = index_of(r"^(openai/)?gpt-6-astra$")
    gpt56_index = index_of(r"^(openai/)?gpt-5\.6-sol$")
    assert sol61_index < sol_index < luna_index < astra_index < gpt56_index
