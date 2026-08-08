from __future__ import annotations

from pathlib import Path

from suites.documentation_standard.support import (
    PROFILES,
    SPEC_ROOT,
    candidate_guidance_files,
    candidate_guidance_sha256,
    completed_tool_call_ids,
    extract_blockquote,
)


def test_profiles_pin_requested_models() -> None:
    assert PROFILES["glm"].model == "glm-5.2:cloud"
    assert PROFILES["glm"].hosted is False
    assert PROFILES["gpt"].model == "gpt-5.6-luna"
    assert PROFILES["gpt"].auth_mode == "chatgpt"
    assert PROFILES["gpt"].hosted is True


def test_candidate_guidance_provenance_is_stable() -> None:
    files = candidate_guidance_files()
    assert files
    assert all(len(item.sha256) == 64 for item in files)
    assert len(candidate_guidance_sha256()) == 64


def test_exact_seed_and_branch_prompts_come_from_specification() -> None:
    seed = extract_blockquote(
        SPEC_ROOT / "seed-01-js-single-file-tool-documentation.md",
        "## Exact seed prompt",
    )
    branch = extract_blockquote(
        SPEC_ROOT / "01-small-package-documentation.md",
        "## Exact user prompt",
    )
    assert seed.startswith("Please investigate `plugins/js-single-file-tool`")
    assert branch == (
        "Please implement the documentation improvements identified in the "
        "investigation. Keep the scope to documentation."
    )


def test_all_current_specification_pages_are_indexed() -> None:
    index = SPEC_ROOT.joinpath("index.md").read_text(encoding="utf-8")
    for path in sorted(SPEC_ROOT.glob("[0-9][0-9]-*.md")):
        assert path.name in index
    for path in sorted(SPEC_ROOT.glob("seed-*.md")):
        assert path.name in index


def test_specification_root_exists() -> None:
    assert isinstance(SPEC_ROOT, Path)
    assert SPEC_ROOT.is_dir()


def test_completed_tool_calls_ignore_stream_fragments() -> None:
    partial = {
        "type": "tool_partial",
        "tool_call_id": "call-1",
        "phase": "stream",
    }
    results = {
        "type": "tool_results",
        "messages": [
            {"metadata": {"tool_call_id": "call-1"}},
            {"metadata": {"tool_call_id": "call-2"}},
        ],
    }

    assert completed_tool_call_ids(partial) == ()
    assert completed_tool_call_ids(results) == ("call-1", "call-2")


def test_completed_tool_calls_support_claude_result_shape() -> None:
    event = {
        "type": "tool_results",
        "messages": [
            {
                "metadata": {
                    "tool_call_id": "call_claude",
                    "tool_name": "Bash",
                }
            }
        ],
    }

    assert completed_tool_call_ids(event) == ("call_claude",)