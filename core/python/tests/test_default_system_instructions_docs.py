from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_ROOT = REPO_ROOT / "docs" / "default-system-instructions"
RUNTIME_SYSTEM_MESSAGES_ROOT = (
    REPO_ROOT / "application" / "python" / "agent_terminal_app" / "system_messages"
)
DEFAULT_CONFIG_ROOT = (
    REPO_ROOT / "application" / "python" / "agent_terminal_app" / "default_config"
)


def test_vendor_instruction_directories_exist() -> None:
    assert DOCS_ROOT.is_dir()
    assert (DOCS_ROOT / "README.md").is_file()

    for vendor in ("codex", "gemini", "qwen", "grok", "kimi"):
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


def test_kimi_docs_have_expected_artifacts() -> None:
    kimi = DOCS_ROOT / "kimi"
    expected = {
        "README.md",
        "template.md",
        "compiled.md",
        "agent-notes.md",
        "reconstruction-notes.md",
        "dynamic-elements.md",
        "static-introduction.md",
        "static-prompt-and-tool-use.md",
        "static-general-guidelines-for-coding.md",
        "static-general-guidelines-for-research-and-data-processing.md",
        "working-environment-section.md",
        "project-information-section.md",
        "skills-section.md",
        "ultimate-reminders.md",
    }
    assert expected.issubset({path.name for path in kimi.iterdir() if path.is_file()})

    template = (kimi / "template.md").read_text(encoding="utf-8")
    assert template.startswith("{{INTRODUCTION}}")
    assert "{{WORKING_ENVIRONMENT_SECTION}}" in template
    assert "{{PROJECT_INFORMATION_SECTION}}" in template
    assert "{{SKILLS_SECTION}}" in template

    dynamic = (kimi / "dynamic-elements.md").read_text(encoding="utf-8")
    assert "Example:" in dynamic
    assert "${KIMI_WORK_DIR}" in dynamic

    compiled = (kimi / "compiled.md").read_text(encoding="utf-8")
    assert "You are Kimi Code CLI" in compiled
    assert "{{" not in compiled


def test_codex_archive_was_moved_under_vendor_layout() -> None:
    codex = DOCS_ROOT / "codex"
    assert (codex / "README.md").is_file()
    assert (codex / "gpt-5.4" / "instructions_default.md").is_file()
    assert not (REPO_ROOT / "docs" / "codex-default-instructions").exists()


def test_runtime_system_message_templates_exist() -> None:
    assert RUNTIME_SYSTEM_MESSAGES_ROOT.is_dir()

    expected_files = {
        "gemini/template.md",
        "gemini/preamble.md",
        "gemini/core-mandates.md",
        "gemini/workflow-section.md",
        "gemini/operational-guidelines.md",
        "gemini/git-section.md",
        "qwen/template.md",
        "qwen/introduction-and-core-mandates.md",
        "qwen/primary-workflows.md",
        "qwen/operational-guidelines.md",
        "qwen/git-section.md",
        "grok/template.md",
        "grok/introduction.md",
        "grok/available-tools-section.md",
        "grok/tool-usage-rules.md",
        "grok/response-guidelines.md",
        "kimi/template.md",
        "kimi/introduction.md",
        "kimi/prompt-and-tool-use.md",
        "kimi/general-guidelines-for-coding.md",
        "kimi/general-guidelines-for-research-and-data-processing.md",
        "kimi/ultimate-reminders.md",
        "helpers/runtime.py",
        "helpers/tasks_ui.py",
        "helpers/render_agents_context_section.py",
        "helpers/render_kimi_working_environment_section.py",
        "helpers/render_kimi_project_information_section.py",
    }

    for relative_path in expected_files:
        assert (RUNTIME_SYSTEM_MESSAGES_ROOT / relative_path).is_file(), relative_path


def test_runtime_templates_and_portable_default_config_omit_deliberately_empty_placeholders() -> None:
    runtime_templates = {
        "gemini/template.md": {
            "{{AVAILABLE_SUBAGENTS_SECTION}}",
            "{{AVAILABLE_SKILLS_SECTION}}",
            "{{HOOK_CONTEXT_SECTION}}",
            "{{YOLO_SECTION}}",
            "{{SANDBOX_SECTION}}",
        },
        "qwen/template.md": {
            "{{TASK_MANAGEMENT}}",
            "{{SANDBOX_SECTION}}",
            "{{MODEL_TOOL_CALL_EXAMPLES}}",
            "{{USER_MEMORY_SUFFIX}}",
        },
        "grok/template.md": {
            "{{CUSTOM_INSTRUCTIONS_SECTION}}",
            "{{WEB_AND_REALTIME_CAPABILITIES_SECTION}}",
        },
        "kimi/template.md": {
            "{{SKILLS_SECTION}}",
            "{{PLAN_MODE_SECTION}}",
            "{{ADDITIONAL_DIRECTORIES_SECTION}}",
        },
    }

    for relative_path, removed_markers in runtime_templates.items():
        template_text = (RUNTIME_SYSTEM_MESSAGES_ROOT / relative_path).read_text(
            encoding="utf-8"
        )
        for marker in removed_markers:
            assert marker not in template_text, (relative_path, marker)

    portable_config_path = DEFAULT_CONFIG_ROOT / "config.json"
    portable_config = json.loads(portable_config_path.read_text(encoding="utf-8"))

    removed_variable_keys = {
        "gemini": {
            "AVAILABLE_SUBAGENTS_SECTION",
            "AVAILABLE_SKILLS_SECTION",
            "HOOK_CONTEXT_SECTION",
            "YOLO_SECTION",
            "SANDBOX_SECTION",
        },
        "qwen": {
            "TASK_MANAGEMENT",
            "SANDBOX_SECTION",
            "MODEL_TOOL_CALL_EXAMPLES",
            "USER_MEMORY_SUFFIX",
        },
        "grok": {
            "CUSTOM_INSTRUCTIONS_SECTION",
            "WEB_AND_REALTIME_CAPABILITIES_SECTION",
        },
        "kimi": {
            "SKILLS_SECTION",
            "PLAN_MODE_SECTION",
            "ADDITIONAL_DIRECTORIES_SECTION",
        },
    }

    for agent_id, removed_keys in removed_variable_keys.items():
        provider_id = portable_config["agents"][agent_id]["provider"]
        variables = portable_config["providers"][provider_id]["system_message"]["variables"]
        for key in removed_keys:
            assert key not in variables, (agent_id, key)


def test_portable_default_config_is_self_contained() -> None:
    config_path = DEFAULT_CONFIG_ROOT / "config.json"
    assert config_path.is_file()
    assert (DEFAULT_CONFIG_ROOT / "system_messages").is_dir()
    assert (DEFAULT_CONFIG_ROOT / "codex").is_dir()

    config = json.loads(config_path.read_text(encoding="utf-8"))
    codex_rows = config["providers"]["openrouter_codex_tools"]["codex_developer_messages"]

    for row in codex_rows:
        text = row["text"]
        assert text.startswith("${file:${env:CONFIG_DIR}/codex/")
        assert "../../../docs/" not in text

        relative_path = text[len("${file:${env:CONFIG_DIR}/") : -1]
        assert (DEFAULT_CONFIG_ROOT / relative_path).is_file(), relative_path

    helper_paths = [
        "system_messages/helpers/runtime.py",
        "system_messages/helpers/tasks_ui.py",
        "system_messages/helpers/render_agents_context_section.py",
        "system_messages/helpers/render_kimi_working_environment_section.py",
        "system_messages/helpers/render_kimi_project_information_section.py",
        "system_messages/helpers/select_codex_developer_message.py",
        "TASKS_v5.md",
        "CLAUDE_CODE_DEFAULT.md",
        "system_messages/codex/template.md",
        "system_messages/gemini/template.md",
        "system_messages/qwen/template.md",
        "system_messages/grok/template.md",
        "system_messages/kimi/template.md",
        "system_messages/kimi/introduction.md",
        "system_messages/kimi/prompt-and-tool-use.md",
        "system_messages/kimi/general-guidelines-for-coding.md",
        "system_messages/kimi/general-guidelines-for-research-and-data-processing.md",
        "system_messages/kimi/ultimate-reminders.md",
    ]

    for relative_path in helper_paths:
        assert (DEFAULT_CONFIG_ROOT / relative_path).is_file(), relative_path
