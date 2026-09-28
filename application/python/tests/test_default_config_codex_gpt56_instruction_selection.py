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

# 2026-07-13 import (commit 2f7d89b1419bf7064346855b0acde23514b1ebc5),
# retained in the unversioned files for provenance.
GPT_56_SOL_20260713_SHA256 = (
    "e9778714d505f3dd04d44db4394024c5fab5bf6554fc9faa3cdf9cf776b63bb9"
)
GPT_56_TERRA_LUNA_20260713_SHA256 = (
    "78a2fc84e1bffa421d865c1a2ade4185d3d33ef38e6a15157f0ff1a89b7d52ec"
)
# 2026-07-18 upstream refresh (commit d26a9bf671b1c03aabfc32e1092d137c1feb3962),
# imported as the dated 20260718 files. All three family members share one
# template; Sol's distinct variant is gone upstream.
GPT_56_20260718_SHA256 = (
    "cbefa6b0bede0e332d957fca70ccacf9f12f4c0ecdf81b819e5cbe1a3b16e265"
)
# 2026-09-23 upstream refresh (commit 24462234b2ae, #47397): one-line
# heading change ("# Destructive Actions" -> "# Destructive actions").
# Imported as the dated 20260923 files; still one shared template.
GPT_56_20260923_SHA256 = (
    "a91357a1cd2727a0be06d461248d6e3a7274746e38108f548a3adf2cc2430415"
)
GPT_56_20260923_HEADING = "# Destructive actions"
GPT_56_DISTINCTIVE_SUBSTRING = "You are Codex, an agent based on GPT-5"
# Sol-specific paragraph in the 2026-07-13 template, removed upstream by the
# 2026-07-18 refresh.
SOL_20260713_PARAGRAPH = (
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


def test_gpt_56_sol_selects_dated_instruction_asset() -> None:
    text = _instruction_text("gpt-5.6-sol")
    expected = (
        CODEX_DIR / "gpt-5.6-sol" / "instructions_default.20260923.md"
    ).read_text(encoding="utf-8")
    assert text == expected


def test_gpt_56_terra_selects_dated_instruction_asset() -> None:
    text = _instruction_text("gpt-5.6-terra")
    expected = (
        CODEX_DIR / "gpt-5.6-terra" / "instructions_default.20260923.md"
    ).read_text(encoding="utf-8")
    assert text == expected


def test_gpt_56_luna_selects_dated_instruction_asset() -> None:
    text = _instruction_text("gpt-5.6-luna")
    expected = (
        CODEX_DIR / "gpt-5.6-luna" / "instructions_default.20260923.md"
    ).read_text(encoding="utf-8")
    assert text == expected


def test_openai_prefixed_gpt_56_ids_select_correctly() -> None:
    for model, expected_dir in (
        ("openai/gpt-5.6-sol", "gpt-5.6-sol"),
        ("openai/gpt-5.6-terra", "gpt-5.6-terra"),
        ("openai/gpt-5.6-luna", "gpt-5.6-luna"),
    ):
        text = _instruction_text(model)
        expected = (
            CODEX_DIR / expected_dir / "instructions_default.20260923.md"
        ).read_text(encoding="utf-8")
        assert text == expected, (model, expected_dir)


def test_bare_gpt_56_alias_does_not_select_gpt_56_template() -> None:
    text = _instruction_text("gpt-5.6")
    for model_dir in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"):
        gpt_56 = (CODEX_DIR / model_dir / "instructions_default.20260923.md").read_text(
            encoding="utf-8"
        )
        assert text != gpt_56, model_dir
    fallback = (CODEX_DIR / "gpt-5" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    assert text == fallback


def test_gpt_56_family_shares_one_template_since_20260718() -> None:
    sol = (CODEX_DIR / "gpt-5.6-sol" / "instructions_default.20260923.md").read_text(
        encoding="utf-8"
    )
    terra = (
        CODEX_DIR / "gpt-5.6-terra" / "instructions_default.20260923.md"
    ).read_text(encoding="utf-8")
    luna = (CODEX_DIR / "gpt-5.6-luna" / "instructions_default.20260923.md").read_text(
        encoding="utf-8"
    )
    assert sol == terra == luna
    # The Sol-specific paragraph from the 2026-07-13 template is gone.
    assert SOL_20260713_PARAGRAPH not in sol


def test_terra_and_luna_mappings_are_both_present() -> None:
    assert (CODEX_DIR / "gpt-5.6-terra" / "instructions_default.20260923.md").is_file()
    assert (CODEX_DIR / "gpt-5.6-luna" / "instructions_default.20260923.md").is_file()
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
    assert "20260923" in terra_row["text"]
    assert "20260923" in luna_row["text"]
    # Verify the resolved text matches the dated file content
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
    terra_file = (
        CODEX_DIR / "gpt-5.6-terra" / "instructions_default.20260923.md"
    ).read_text(encoding="utf-8")
    luna_file = (
        CODEX_DIR / "gpt-5.6-luna" / "instructions_default.20260923.md"
    ).read_text(encoding="utf-8")
    assert resolved_terra["text"] == terra_file
    assert resolved_luna["text"] == luna_file


def test_gpt_56_dated_files_match_upstream_sha256() -> None:
    for model_dir in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"):
        sha = _file_sha256(CODEX_DIR / model_dir / "instructions_default.20260923.md")
        assert sha == GPT_56_20260923_SHA256, model_dir
        # The 2026-09-23 refresh changed only the Destructive-actions heading.
        text_2026 = (
            CODEX_DIR / model_dir / "instructions_default.20260923.md"
        ).read_text(encoding="utf-8")
        assert GPT_56_20260923_HEADING in text_2026, model_dir
        old_sha = _file_sha256(
            CODEX_DIR / model_dir / "instructions_default.20260718.md"
        )
        assert old_sha == GPT_56_20260718_SHA256, model_dir


def test_gpt_56_previous_version_files_are_retained() -> None:
    # The unversioned 2026-07-13 files remain for provenance and rollback.
    sol_sha = _file_sha256(CODEX_DIR / "gpt-5.6-sol" / "instructions_default.md")
    terra_sha = _file_sha256(CODEX_DIR / "gpt-5.6-terra" / "instructions_default.md")
    luna_sha = _file_sha256(CODEX_DIR / "gpt-5.6-luna" / "instructions_default.md")
    assert sol_sha == GPT_56_SOL_20260713_SHA256
    assert terra_sha == GPT_56_TERRA_LUNA_20260713_SHA256
    assert luna_sha == GPT_56_TERRA_LUNA_20260713_SHA256
    # The old Sol-specific paragraph exists only in the retained Sol file.
    old_sol = (CODEX_DIR / "gpt-5.6-sol" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    old_terra = (CODEX_DIR / "gpt-5.6-terra" / "instructions_default.md").read_text(
        encoding="utf-8"
    )
    assert SOL_20260713_PARAGRAPH in old_sol
    assert SOL_20260713_PARAGRAPH not in old_terra


def test_personality_selection_resolves_to_same_template() -> None:
    default_text = _instruction_text("gpt-5.6-luna", "default")
    friendly_text = _instruction_text("gpt-5.6-luna", "friendly")
    pragmatic_text = _instruction_text("gpt-5.6-luna", "pragmatic")
    none_text = _instruction_text("gpt-5.6-luna", None)
    assert default_text == friendly_text == pragmatic_text == none_text
    template = (
        CODEX_DIR / "gpt-5.6-luna" / "model_messages.instructions_template.20260923.md"
    ).read_text(encoding="utf-8")
    assert default_text == template


def test_gpt_55_default_row_selects_dated_friendly_embedded_asset() -> None:
    text = _instruction_text("gpt-5.5")
    expected = (CODEX_DIR / "gpt-5.5" / "instructions_default.20260911.md").read_text(
        encoding="utf-8"
    )
    assert text == expected
    # The 2026-09-11 upstream template embeds the friendly personality and
    # equals the retained base_instructions.md.
    base = (CODEX_DIR / "gpt-5.5" / "base_instructions.md").read_text(encoding="utf-8")
    assert expected == base


def test_gpt_55_friendly_and_pragmatic_rows_keep_previous_files() -> None:
    friendly_text = _instruction_text("gpt-5.5", "friendly")
    pragmatic_text = _instruction_text("gpt-5.5", "pragmatic")
    friendly = (CODEX_DIR / "gpt-5.5" / "instructions_friendly.md").read_text(
        encoding="utf-8"
    )
    pragmatic = (CODEX_DIR / "gpt-5.5" / "instructions_pragmatic.md").read_text(
        encoding="utf-8"
    )
    assert friendly_text == friendly
    assert pragmatic_text == pragmatic


def test_gpt_54_default_row_selects_dated_friendly_embedded_asset() -> None:
    text = _instruction_text("gpt-5.4")
    expected = (CODEX_DIR / "gpt-5.4" / "instructions_default.20260911.md").read_text(
        encoding="utf-8"
    )
    assert text == expected


def test_gpt_54_friendly_and_pragmatic_rows_keep_previous_files() -> None:
    friendly_text = _instruction_text("gpt-5.4", "friendly")
    pragmatic_text = _instruction_text("gpt-5.4", "pragmatic")
    friendly = (CODEX_DIR / "gpt-5.4" / "instructions_friendly.md").read_text(
        encoding="utf-8"
    )
    pragmatic = (CODEX_DIR / "gpt-5.4" / "instructions_pragmatic.md").read_text(
        encoding="utf-8"
    )
    assert friendly_text == friendly
    assert pragmatic_text == pragmatic


def test_older_model_mappings_remain_unchanged() -> None:
    cases = {
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
