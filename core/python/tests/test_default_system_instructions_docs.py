from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_ROOT = REPO_ROOT / "docs" / "default-system-instructions"


def test_vendor_instruction_directories_exist() -> None:
    assert DOCS_ROOT.is_dir()
    assert (DOCS_ROOT / "README.md").is_file()

    for vendor in ("codex", "gemini", "qwen", "grok"):
        assert (DOCS_ROOT / vendor).is_dir(), vendor


def test_gemini_docs_have_expected_artifacts() -> None:
    gemini = DOCS_ROOT / "gemini"
    expected = {
        "README.md",
        "template.md",
        "compiled.md",
        "agent-notes.md",
        "available-subagents-section.md",
        "available-skills-section.md",
        "hook-context-section.md",
        "workflow-section.md",
        "yolo-section.md",
        "sandbox-section.md",
        "git-section.md",
        "context-files-section.md",
        "static-preamble.md",
        "static-core-mandates.md",
        "static-operational-guidelines.md",
        "dynamic-elements.md",
    }
    assert expected.issubset({path.name for path in gemini.iterdir() if path.is_file()})

    template = (gemini / "template.md").read_text(encoding="utf-8")
    assert template.startswith("{{PREAMBLE}}")
    assert "{{AVAILABLE_SUBAGENTS_SECTION}}" in template
    assert "{{WORKFLOW_SECTION}}" in template
    assert "{{CONTEXT_FILES_SECTION}}" in template

    dynamic = (gemini / "dynamic-elements.md").read_text(encoding="utf-8")
    assert "Example:" in dynamic
    assert "{{INTERACTION_MODE}}" in dynamic

    compiled = (gemini / "compiled.md").read_text(encoding="utf-8")
    assert "You are Gemini CLI" in compiled
    assert "{{" not in compiled


def test_qwen_docs_have_expected_artifacts() -> None:
    qwen = DOCS_ROOT / "qwen"
    expected = {
        "README.md",
        "template.md",
        "compiled.md",
        "agent-notes.md",
        "sandbox-section.md",
        "git-section.md",
        "model-tool-call-examples.md",
        "user-memory-suffix.md",
        "static-introduction-and-core-mandates.md",
        "static-task-management.md",
        "static-primary-workflows.md",
        "static-operational-guidelines.md",
        "dynamic-elements.md",
    }
    assert expected.issubset({path.name for path in qwen.iterdir() if path.is_file()})

    template = (qwen / "template.md").read_text(encoding="utf-8")
    assert template.startswith("{{INTRODUCTION_AND_CORE_MANDATES}}")
    assert "{{MODEL_TOOL_CALL_EXAMPLES}}" in template
    assert "{{SANDBOX_SECTION}}" in template
    assert "{{USER_MEMORY_SUFFIX}}" in template

    dynamic = (qwen / "dynamic-elements.md").read_text(encoding="utf-8")
    assert "Example:" in dynamic
    assert "{{TOOL_CALL_EXAMPLE_STYLE}}" in dynamic

    compiled = (qwen / "compiled.md").read_text(encoding="utf-8")
    assert "You are Qwen Code" in compiled
    assert "{{" not in compiled


def test_grok_docs_have_expected_artifacts() -> None:
    grok = DOCS_ROOT / "grok"
    expected = {
        "README.md",
        "template.md",
        "compiled.md",
        "agent-notes.md",
        "available-tools-section.md",
        "working-directory-line.md",
        "static-introduction.md",
        "static-tool-usage-rules.md",
        "static-workflow-and-response-guidance.md",
        "dynamic-elements.md",
    }
    assert expected.issubset({path.name for path in grok.iterdir() if path.is_file()})

    template = (grok / "template.md").read_text(encoding="utf-8")
    assert template.startswith("{{INTRODUCTION}}")
    assert "{{AVAILABLE_TOOLS_SECTION}}" in template
    assert "{{WEB_AND_REALTIME_CAPABILITIES_SECTION}}" in template
    assert "{{WORKING_DIRECTORY_LINE}}" in template

    dynamic = (grok / "dynamic-elements.md").read_text(encoding="utf-8")
    assert "Example:" in dynamic
    assert "{{WORKING_DIRECTORY_LINE}}" in dynamic

    compiled = (grok / "compiled.md").read_text(encoding="utf-8")
    assert "You are Grok CLI" in compiled
    assert "{{" not in compiled


def test_codex_archive_was_moved_under_vendor_layout() -> None:
    codex = DOCS_ROOT / "codex"
    assert (codex / "README.md").is_file()
    assert (codex / "gpt-5.4" / "instructions_default.md").is_file()
    assert not (REPO_ROOT / "docs" / "codex-default-instructions").exists()