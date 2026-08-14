from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from suites.documentation_standard.support import (
    BASELINE_GUIDANCE_REVISION,
    PROFILES,
    REPOSITORY_ROOT,
    SPEC_ROOT,
    GuidanceSource,
    DocumentationEvaluationHarness,
    ScenarioWorkspaceFactory,
    apply_fixture,
    baseline_guidance_source,
    candidate_guidance_files,
    candidate_guidance_sha256,
    completed_tool_call_ids,
    extract_blockquote,
    fixture_revision,
    _project_config_for_profile,
    EVALUATION_TOOL_PLUGINS,
    GUIDANCE_CONFIG_KEY,
    GUIDANCE_FEATURE_PLUGIN,
    PLUGIN_RUNTIME_CONSTRAINTS,
)
from suites.documentation_standard.guidance_feature import (
    DocumentationStandardGuidanceFeature,
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


def test_baseline_guidance_is_pinned_and_distinct() -> None:
    baseline = baseline_guidance_source()

    assert baseline.revision == BASELINE_GUIDANCE_REVISION
    assert len(baseline.sha256()) == 64
    assert baseline.sha256() != candidate_guidance_sha256()
    agents = baseline.read_bytes("AGENTS.md").decode("utf-8")
    assert "Preserve artifact and audience boundaries" not in agents


def test_explicit_guidance_source_participates_in_workspace_fingerprint(
    tmp_path: Path,
) -> None:
    for item in candidate_guidance_files():
        target = tmp_path / item.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(REPOSITORY_ROOT.joinpath(item.path).read_bytes())
    source = GuidanceSource(name="short-candidate", root=tmp_path)
    factory = ScenarioWorkspaceFactory(
        fixture_id="js-single-file-tool",
        candidate_guidance=True,
        guidance=source,
    )

    fingerprint = factory.fingerprint()

    assert fingerprint["guidance_name"] == "short-candidate"
    assert fingerprint["guidance_revision"] is None
    assert fingerprint["guidance_sha256"] == source.sha256()


def test_guidance_is_injected_before_the_branch_task_prompt(tmp_path: Path) -> None:
    source = GuidanceSource(name="candidate")

    class Core:
        calls: list[dict[str, object]] = []

        def add_message(
            self,
            session: object,
            role: str,
            content: str,
            metadata: object,
            config: object,
            *,
            after_index: int,
        ) -> object:
            self.calls.append(
                {
                    "session": session,
                    "role": role,
                    "content": content,
                    "metadata": metadata,
                    "config": config,
                    "after_index": after_index,
                }
            )
            return object()

    class Application:
        def save_session(self, session: object) -> object:
            return session

    class Services:
        def record(self, _name: str, _value: object) -> None:
            return None

    class Context:
        workspace = tmp_path
        session_or_none = object()
        config: dict[str, object] = {}
        services = Services()
        application = Application()
        core = Core()
        base_config: dict[str, object] = {}
        session = session_or_none
        messages: list[tuple[str, str]] = []

        def effective_config(self) -> dict[str, object]:
            return {"model": "test"}

        def replace_runtime(
            self,
            *,
            core: object,
            base_config: object,
            session: object,
        ) -> None:
            self.core = core
            self.base_config = base_config
            self.session = session
            self.session_or_none = session

        def add_message(self, role: str, content: str) -> None:
            self.messages.append((role, content))

        def request(self, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(
                final_response="done",
                completed=True,
                cancelled=False,
                error_messages=(),
                tool_event_count=0,
                mutation_count=0,
                duration_seconds=0.1,
            )

    harness = object.__new__(DocumentationEvaluationHarness)
    harness.profile = PROFILES["glm"]
    context = Context()

    value = harness._turn(
        context,
        "Please continue.",
        guidance=source,
        inject_guidance=True,
    )

    instruction = context.core.calls[0]
    assert instruction["role"] == "system"
    assert instruction["after_index"] == -1
    assert instruction["metadata"] is None
    assert '<repository-guidance path="AGENTS.md">' in str(instruction["content"])
    assert REPOSITORY_ROOT.joinpath("AGENTS.md").read_text() in str(
        instruction["content"]
    )
    assert context.messages == [("user", "Please continue.")]
    assert value.guidance_injected is True


def test_chatgpt_guidance_uses_late_request_feature(tmp_path: Path) -> None:
    source = GuidanceSource(name="candidate")

    class Services:
        def record(self, _name: str, _value: object) -> None:
            return None

    class Context:
        workspace = tmp_path
        session_or_none = object()
        config: dict[str, object] = {}
        services = Services()
        messages: list[tuple[str, str]] = []

        def add_message(self, role: str, content: str) -> None:
            self.messages.append((role, content))

        def request(self, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(
                final_response="done",
                completed=True,
                cancelled=False,
                error_messages=(),
                tool_event_count=0,
                mutation_count=0,
                duration_seconds=0.1,
            )

    harness = object.__new__(DocumentationEvaluationHarness)
    harness.profile = PROFILES["gpt"]
    context = Context()

    harness._turn(
        context,
        "Please continue.",
        guidance=source,
        inject_guidance=True,
    )

    guidance = context.config[GUIDANCE_CONFIG_KEY]
    assert '<repository-guidance path="AGENTS.md">' in str(guidance)
    assert REPOSITORY_ROOT.joinpath("AGENTS.md").read_text() in str(guidance)
    assert context.messages == [("user", "Please continue.")]


def test_guidance_feature_preserves_compiled_instruction_and_strips_request_item() -> None:
    feature = DocumentationStandardGuidanceFeature()
    leading = {
        "type": "message",
        "role": "developer",
        "content": [{"type": "input_text", "text": "Normal Codex instruction"}],
    }
    user = {
        "type": "message",
        "role": "user",
        "content": [{"type": "input_text", "text": "Do the task"}],
    }
    native = [leading, user]
    state = {
        "config": {GUIDANCE_CONFIG_KEY: "Exact repository guidance"},
        "request": {
            "payload": {
                "model": "gpt-test",
                "instructions": "Payload instruction",
            },
            "messages": native,
        },
    }

    returned_native, returned_state = feature.initialize_request(native, state)

    assert returned_native is native
    request = returned_state["request"]
    assert request["messages"] == [user]
    assert request["payload"] == {"model": "gpt-test"}
    assert request["instructions"] == (
        "Payload instruction\n\n"
        "Normal Codex instruction\n\n"
        "Exact repository guidance"
    )
    evidence = returned_state["_documentation_standard_guidance_injection"]
    assert evidence["leading_instruction_preserved"] is True
    assert evidence["request_message_stripped"] is True


def test_guidance_feature_is_noop_without_suite_config() -> None:
    feature = DocumentationStandardGuidanceFeature()
    native = [{"role": "system", "content": "Normal instruction"}]
    state = {"config": {}, "request": {"messages": native}}

    returned_native, returned_state = feature.initialize_request(native, state)

    assert returned_native is native
    assert returned_state is state


def test_profile_config_projection_excludes_other_agent_tool_stacks(
    tmp_path: Path,
) -> None:
    source = tmp_path / "config.json"
    source.write_text(
        json.dumps(
            {
                "plugin_cache_dir": "shared",
                "plugins": [
                    "path:/plugins/feature-request-options",
                    "path:/plugins/feature-system-message",
                    "path:/plugins/openai_responses",
                    "path:/plugins/codex-tools",
                    "path:/plugins/chatgpt-auth-app",
                    "path:/plugins/reference-openai-compatible-provider",
                    "path:/plugins/claude-tools",
                    "plugins.tool_call_preview_feature.ToolCallPreviewFeature",
                ],
                "providers": {"openai": {}, "ollama": {}},
                "mixins": {"shared": {}},
                "application": {"setting": True},
                "agents": {
                    "codex-openai": {
                        "provider": "openai",
                        "plugins": ["path:/plugins/codex-tools"],
                    },
                    "glm-ollama": {
                        "provider": "ollama",
                        "plugins": ["path:/plugins/claude-tools"],
                    },
                },
            }
        )
    )

    target = _project_config_for_profile(
        source,
        artifact_root=tmp_path / "artifacts",
        profile=PROFILES["gpt"],
    )
    projected = json.loads(target.read_text())

    assert set(projected["agents"]) == {"codex-openai"}
    assert any("openai_responses" in item for item in projected["plugins"])
    assert any("chatgpt-auth-app" in item for item in projected["plugins"])
    assert any("ToolCallPreviewFeature" in item for item in projected["plugins"])
    assert not any("claude-tools" in item for item in projected["plugins"])
    assert projected["agents"]["codex-openai"]["plugins"] == [
        GUIDANCE_FEATURE_PLUGIN,
        *EVALUATION_TOOL_PLUGINS,
    ]
    assert projected["providers"] == {"openai": {}, "ollama": {}}
    assert projected["mixins"] == {"shared": {}}
    assert projected["application"] == {"setting": True}
    assert "plugin-cache/gpt/" in projected["plugin_cache_dir"]
    assert projected["plugin_cache_dir"].endswith("-v4")


def test_plugin_runtime_constraints_pin_validated_openai_sdk() -> None:
    assert PLUGIN_RUNTIME_CONSTRAINTS.read_text().splitlines()[-1] == (
        "openai==2.53.0"
    )


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
    failed_refresh = extract_blockquote(
        SPEC_ROOT / "16-failed-generated-refresh.md",
        "## Exact user prompt",
    )
    assert failed_refresh == (
        "The npm verification command in "
        "`docs_site/prepared/plugins/js-single-file-tool/index.md` says "
        "`npm --vesion`. Please fix that documentation issue."
    )
    public_profile = extract_blockquote(
        SPEC_ROOT / "17-public-package-profile.md",
        "## Exact user prompt",
    )
    assert public_profile == (
        "Please finish the documentation setup for `packages/event-sdk` so a "
        "new SDK user can get started and a package maintainer can find the "
        "implementation and specification entry points. Keep the work "
        "documentation-only."
    )
    plugin_boundary = extract_blockquote(
        SPEC_ROOT / "18-shared-plugin-authoring-boundary.md",
        "## Exact user prompt",
    )
    assert plugin_boundary == (
        "Please make `plugins/js-single-file-tool` usable as a complete "
        "example, and add a focused shared explanation of the single-file "
        "object-export, loading/configuration, and verification workflow for "
        "other Node tool authors. Keep plugin-specific behavior with the "
        "example and keep the work documentation-only."
    )
    maintainer_boundary = extract_blockquote(
        SPEC_ROOT / "19-apply-versus-maintain-boundary.md",
        "## Exact user prompt",
    )
    assert maintainer_boundary == (
        "Please add a short “Why these docs are structured this way” section "
        "to `packages/event-sdk/README.md` that links the "
        "standards-maintenance specification and the agent-behavior evaluation "
        "covering this package, so SDK users can trace the internal decision."
    )


def test_all_current_specification_pages_are_indexed() -> None:
    index = SPEC_ROOT.joinpath("index.md").read_text(encoding="utf-8")
    for path in sorted(SPEC_ROOT.glob("[0-9][0-9]-*.md")):
        assert path.name in index
        text = path.read_text(encoding="utf-8")
        assert "## Semantic assessment" in text
        assert "## Human review" in text
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


def test_all_seed_and_consumer_prompts_are_extractable() -> None:
    for path in sorted(SPEC_ROOT.glob("seed-*.md")):
        assert extract_blockquote(path, "## Exact seed prompt")
    for path in sorted(SPEC_ROOT.glob("[0-9][0-9]-*.md")):
        headings = (
            ("## First exact user prompt", "## Second exact user prompt")
            if path.name.startswith("06-")
            else ("## Exact user prompt",)
        )
        for heading in headings:
            assert extract_blockquote(path, heading)


def test_seed_prompts_name_the_exact_bounded_fixture_paths() -> None:
    required_paths = {
        "seed-02-report-export-row-limit.md": (
            "tasks/report-export-max-rows.md",
            "packages/report-export-sdk/README.md",
            "packages/report-export-sdk/src/report_export.py",
            "packages/report-export-sdk/tests/test_report_export.py",
            "packages/report-export-sdk/docs/development/index.md",
            "packages/report-export-sdk/docs/development/specifications/"
            "export-limits/index.md",
            "packages/report-export-sdk/docs/development/specifications/"
            "export-limits/product-spec.md",
            "packages/report-export-sdk/docs/development/specifications/"
            "export-limits/technical-spec.md",
            "packages/report-export-sdk/docs/development/specifications/"
            "export-limits/requirements.md",
        ),
        "seed-03-mobile-composer-refinement.md": (
            "tasks/mobile-composer-ux.md",
            "packages/conversation-contract/docs/development/specifications/"
            "composer/index.md",
            "packages/conversation-contract/docs/development/specifications/"
            "composer/product-spec.md",
            "packages/conversation-contract/docs/development/specifications/"
            "composer/requirements.md",
            "mobile/example-app/src/Composer.tsx",
            "mobile/example-app/docs/development/index.md",
        ),
        "seed-05-batch-sync-design.md": (
            "packages/batch-sdk/src/batch.py",
            "packages/transport-contract/docs/development/specifications/"
            "transport/index.md",
            "packages/persistence-contract/docs/development/specifications/"
            "persistence/index.md",
        ),
        "seed-06-existing-contract-bugfix.md": (
            "tasks/path-policy-home-relative-bug.md",
            "packages/path-policy/README.md",
            "packages/path-policy/src/path_policy.py",
            "packages/path-policy/tests/test_path_policy.py",
            "packages/path-policy/docs/development/specifications/"
            "path-normalization/index.md",
            "packages/path-policy/docs/development/specifications/"
            "path-normalization/technical-spec.md",
            "packages/path-policy/docs/development/specifications/"
            "path-normalization/requirements.md",
        ),
        "seed-07-local-bugfix.md": (
            "packages/slug-utils/src/slug_cache.py",
            "packages/slug-utils/tests/test_slug_cache.py",
        ),
        "seed-08-completed-small-implementation.md": (
            "packages/label-utils/src/labels.py",
            "packages/label-utils/tests/test_labels.py",
            "packages/label-utils/docs/development/specifications/"
            "label-normalization/technical-spec.md",
        ),
        "seed-09-partial-major-change.md": (
            "tasks/sync-v2.md",
            "packages/sync-engine/README.md",
            "packages/sync-engine/src/sync.py",
            "packages/sync-engine/tests/test_sync.py",
            "packages/sync-engine/docs/development/specifications/"
            "sync-v2/index.md",
            "packages/sync-engine/docs/development/specifications/"
            "sync-v2/product-spec.md",
            "packages/sync-engine/docs/development/specifications/"
            "sync-v2/technical-spec.md",
            "packages/sync-engine/docs/development/specifications/"
            "sync-v2/requirements.md",
        ),
    }
    for filename, paths in required_paths.items():
        prompt = extract_blockquote(
            SPEC_ROOT / filename,
            "## Exact seed prompt",
        )
        assert all(path in prompt for path in paths), filename


def test_synthetic_fixtures_contain_expected_seed_sources(tmp_path: Path) -> None:
    fixtures = {
        "report-export": "tasks/report-export-max-rows.md",
        "mobile-composer": "tasks/mobile-composer-ux.md",
        "event-retry": "packages/event-sdk/src/events.py",
        "batch-sync": "packages/batch-sdk/src/batch.py",
        "path-policy": "tasks/path-policy-home-relative-bug.md",
        "slug-utils": "packages/slug-utils/src/slug_cache.py",
        "label-utils": (
            "packages/label-utils/docs/development/specifications/"
            "label-normalization/technical-spec.md"
        ),
        "sync-engine": "tasks/sync-v2.md",
    }
    for fixture_id, expected in fixtures.items():
        workspace = tmp_path / fixture_id
        workspace.mkdir()
        workspace.joinpath(".git").write_text("fixture\n", encoding="utf-8")
        apply_fixture(workspace, fixture_id, "base")
        assert workspace.joinpath("AGENTS.md").is_file()
        assert workspace.joinpath(expected).is_file()


def test_synthetic_python_fixture_baselines_are_runnable(tmp_path: Path) -> None:
    package_paths = {
        "report-export": "packages/report-export-sdk/tests",
        "event-retry": "packages/event-sdk/tests",
        "path-policy": "packages/path-policy/tests",
        "slug-utils": "packages/slug-utils/tests",
        "label-utils": "packages/label-utils/tests",
        "sync-engine": "packages/sync-engine/tests",
    }
    for fixture_id, tests_path in package_paths.items():
        workspace = tmp_path / fixture_id
        workspace.mkdir()
        workspace.joinpath(".git").write_text("fixture\n", encoding="utf-8")
        apply_fixture(workspace, fixture_id, "base")

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", tests_path],
            cwd=workspace,
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f"{fixture_id} fixture baseline failed:\n"
            f"{result.stdout}\n{result.stderr}"
        )


def test_fixture_revision_participates_in_workspace_fingerprint() -> None:
    factory = ScenarioWorkspaceFactory(
        fixture_id="slug-utils",
        candidate_guidance=False,
    )

    assert fixture_revision("slug-utils") == "v2"
    assert factory.fingerprint()["fixture_revision"] == "v2"
    assert fixture_revision("js-single-file-tool") == "v4"
    assert fixture_revision("event-retry") == "v5"


def test_failed_generator_fixture_preserves_prepared_output(tmp_path: Path) -> None:
    factory = ScenarioWorkspaceFactory(
        fixture_id="js-single-file-tool",
        candidate_guidance=False,
        branch_variant="generated-typo-failing-generator",
    )
    workspace = factory(tmp_path)
    try:
        prepared = workspace / "docs_site/prepared/plugins/js-single-file-tool/index.md"
        before = prepared.read_text(encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "docs_site/scripts/prepare_mkdocs_site.py"],
            cwd=workspace,
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "mkdocs-material-extensions" in result.stderr
        assert prepared.read_text(encoding="utf-8") == before
    finally:
        factory.cleanup(workspace)


def test_batch_approved_task_variant_adds_authorization(tmp_path: Path) -> None:
    workspace = tmp_path / "batch"
    workspace.mkdir()
    workspace.joinpath(".git").write_text("fixture\n", encoding="utf-8")

    apply_fixture(workspace, "batch-sync", "approved-task")

    task = workspace.joinpath("tasks/batch-offline-sync.md")
    assert task.is_file()
    assert "Status: Approved" in task.read_text(encoding="utf-8")