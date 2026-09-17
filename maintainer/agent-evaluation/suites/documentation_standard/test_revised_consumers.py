from __future__ import annotations

import json
import re
from collections.abc import Iterator

import pytest

from .support import (
    AssertionFinding,
    DocumentationEvaluationHarness,
    assert_findings,
    basic_run_findings,
    enforce_real_model_gate,
    file_text,
    matching_paths,
    record_review,
    require_run_value,
    selected_profile,
)
from .test_consumers import (
    _complete_read_positions,
    _evidence_value,
    _first_mutation_tool_index,
    _placement_communication_is_proportionate,
    _seed_04,
    _seed_05,
    _seed_08,
    _seed_01,
    _seed_02,
    _tool_messages,
)


pytestmark = pytest.mark.agent_eval


@pytest.fixture(scope="session")
def harness() -> Iterator[DocumentationEvaluationHarness]:
    profile = selected_profile()
    enforce_real_model_gate(profile)
    value = DocumentationEvaluationHarness(profile)
    yield value
    value.close()


def _seed_10(harness: DocumentationEvaluationHarness):
    run = harness.seed(
        seed_id="seed-10-requirement-scope",
        spec_file="seed-10-requirement-scope.md",
        fixture_id="requirement-scope",
    )
    run.raise_for_error()
    assert run.value.completed
    assert not run.changed_paths
    return run


def _seed_11(harness: DocumentationEvaluationHarness):
    run = harness.seed(
        seed_id="seed-11-testing-strategy",
        spec_file="seed-11-testing-strategy.md",
        fixture_id="testing-strategy",
    )
    run.raise_for_error()
    assert run.value.completed
    assert not run.changed_paths
    return run


def _requirement_rows(text: str) -> tuple[str, ...]:
    return tuple(
        line.lower()
        for line in text.splitlines()
        if re.match(r"^\|\s*[A-Z][A-Z0-9-]*-\d+\s*\|", line)
    )


def _strategy_paths(run, prefix: str) -> tuple[str, ...]:
    return tuple(
        path
        for path in matching_paths(run, prefix)
        if path.endswith("/testing-strategy.md")
    )


def _routine_checks_are_secondary(response: str) -> bool:
    lower = response.lower()
    acceptance = [
        position
        for term in ("pytest", "test_labels.py", "focused test", "passing test")
        if (position := lower.find(term)) >= 0
    ]
    routine = [
        position
        for term in ("ruff", "lint", "formatting", "mypy", "compilation")
        if (position := lower.find(term)) >= 0
    ]
    return bool(acceptance) and (not routine or min(acceptance) < min(routine))


@pytest.mark.routine
@pytest.mark.parametrize("reasoning_effort", ("low", "high", "max"))
@pytest.mark.requirements("DOCGUIDE-005", "DOCVAL-010")
def test_22_requirement_scope_restraint(
    harness: DocumentationEvaluationHarness,
    reasoning_effort: str,
) -> None:
    run = harness.branch(
        test_id=f"22-requirement-scope-restraint-{reasoning_effort}",
        spec_file="22-requirement-scope-restraint.md",
        parent=_seed_10(harness),
        fixture_id="requirement-scope",
        reasoning_effort=reasoning_effort,
    )
    spec_paths = matching_paths(
        run,
        "packages/offline-queue/docs/development/specifications",
    )
    requirement_paths = tuple(
        path for path in spec_paths if path.endswith("/requirements.md")
    )
    rendered = "\n".join(file_text(run, path) for path in spec_paths).lower()
    rows = _requirement_rows(
        "\n".join(file_text(run, path) for path in requirement_paths)
    )
    row_text = "\n".join(rows)
    profile = _evidence_value(run, "documentation_standard.profile")
    profile_value = profile if isinstance(profile, dict) else {}
    unapproved = ("encryption", "telemetry", "dashboard", "compression", "replication")
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "package-local specification created",
            bool(spec_paths) and bool(requirement_paths),
            repr(spec_paths),
        ),
        AssertionFinding(
            "approved outcomes covered",
            all(
                term in row_text
                for term in ("batch", "order", "empty", "max", "enqueue")
            )
            and ("before" in row_text or "without changing" in row_text)
            and ("existing" in row_text or "compatib" in row_text or "single" in row_text),
            row_text,
        ),
        AssertionFinding(
            "unapproved ideas excluded from requirements",
            not any(term in row_text for term in unapproved),
            row_text,
        ),
        AssertionFinding(
            "requirement set remains reviewable",
            4 <= len(rows) <= 7,
            f"{len(rows)} rows: {rows!r}",
        ),
        AssertionFinding(
            "requirements begin pending",
            "not started" in rendered
            and "unverified" in rendered
            and "pending" in rendered,
            rendered,
        ),
        AssertionFinding(
            "scope remains specification-only",
            bool(run.changed_paths)
            and all(
                path.startswith("packages/offline-queue/docs/development/")
                for path in run.changed_paths
            ),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "reasoning effort recorded",
            profile_value.get("reasoning_effort") == reasoning_effort,
            json.dumps(profile_value, sort_keys=True),
        ),
    )
    record_review(
        run,
        spec_file="22-requirement-scope-restraint.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.routine
@pytest.mark.requirements("DOCGUIDE-006", "DOCVAL-010")
def test_23_testing_without_overspecification(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="23-testing-without-overspecification",
        spec_file="23-testing-without-overspecification.md",
        parent=_seed_11(harness),
        fixture_id="testing-strategy",
        branch_variant="local-option",
    )
    strategies = _strategy_paths(
        run,
        "plugins/ui-options/docs/development/specifications",
    )
    text = "\n".join(file_text(run, path) for path in strategies).lower()
    non_contractual = (
        "_debug_origin",
        "private metadata",
        "key order",
        "complete mapping",
        "helper call",
        "internal call",
    )
    exclusion_language = (
        "do not",
        "don't",
        "avoid",
        "exclude",
        "not part",
        "outside",
        "unnecessary",
    )
    expensive_layers = ("integration", "end-to-end", "e2e")
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "one package testing strategy",
            len(strategies) == 1,
            repr(strategies),
        ),
        AssertionFinding(
            "observable option behavior covered",
            "advanced" in text
            and "capabil" in text
            and any(term in text for term in ("absent", "omitted", "none", "present")),
            text,
        ),
        AssertionFinding(
            "local test boundary selected",
            "unit" in text or "component" in text,
            text,
        ),
        AssertionFinding(
            "non-contractual details deliberately excluded",
            any(term in text for term in non_contractual)
            and any(term in text for term in exclusion_language),
            text,
        ),
        AssertionFinding(
            "no unrelated test layer required",
            not any(term in text for term in expensive_layers)
            or any(
                phrase in text
                for phrase in (
                    "not needed",
                    "not required",
                    "do not add",
                    "out of scope",
                    "unnecessary",
                    "omit",
                )
            ),
            text,
        ),
        AssertionFinding(
            "scope remains planning-only",
            bool(run.changed_paths)
            and all(
                path.endswith(".md") and "/docs/development/" in path
                for path in run.changed_paths
            ),
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="23-testing-without-overspecification.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.routine
@pytest.mark.requirements("DOCGUIDE-006", "DOCVAL-010")
def test_24_testing_important_layer_crossing(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="24-testing-important-layer-crossing",
        spec_file="24-testing-important-layer-crossing.md",
        parent=_seed_11(harness),
        fixture_id="testing-strategy",
        branch_variant="cross-layer",
    )
    strategies = _strategy_paths(
        run,
        "docs/development/specifications",
    )
    text = "\n".join(file_text(run, path) for path in strategies).lower()
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "one cross-package testing strategy",
            len(strategies) == 1,
            repr(strategies),
        ),
        AssertionFinding(
            "all production boundaries represented",
            "plugin" in text
            and any(term in text for term in ("endpoint", "http", "api"))
            and "frontend" in text
            and "adapter" in text,
            text,
        ),
        AssertionFinding(
            "real integration crossing selected",
            "integration" in text
            and any(term in text for term in ("production", "real", "public")),
            text,
        ),
        AssertionFinding(
            "not unit-only or mock-only",
            "unit" in text
            and (
                "mock" not in text
                or any(
                    phrase in text
                    for phrase in (
                        "not only",
                        "not sufficient",
                        "insufficient",
                        "does not replace",
                        "avoid mocking",
                        "no mocks",
                        "no mocked",
                    )
                )
            ),
            text,
        ),
        AssertionFinding(
            "scope remains planning-only",
            bool(run.changed_paths)
            and all(
                path.endswith(".md")
                and (
                    path.startswith("docs/development/")
                    or "/docs/development/" in path
                )
                for path in run.changed_paths
            ),
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="24-testing-important-layer-crossing.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.routine
@pytest.mark.requirements("DOCGUIDE-006", "DOCVAL-010")
def test_25_focused_verification_report(
    harness: DocumentationEvaluationHarness,
) -> None:
    parent = _seed_08(harness)
    run = harness.branch_from_parent_workspace(
        test_id="25-focused-verification-report",
        spec_file="25-focused-verification-report.md",
        parent=parent,
        fixture_id="label-utils",
        branch_variant="report-only",
    )
    response = require_run_value(run).response
    lower = response.lower()
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "no mutation",
            not run.changed_paths,
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "delivered behavior named",
            "trim" in lower and "whitespace" in lower,
            response,
        ),
        AssertionFinding(
            "focused passing evidence named",
            any(
                term in lower
                for term in ("pytest", "test_labels.py", "focused test", "passing test")
            )
            and "pass" in lower,
            response,
        ),
        AssertionFinding(
            "remaining tracking visible",
            any(term in lower for term in ("readme", "documentation", "requirement"))
            and any(
                term in lower
                for term in (
                    "remain",
                    "pending",
                    "stale",
                    "not updated",
                    "left for follow-up",
                )
            ),
            response,
        ),
        AssertionFinding(
            "acceptance evidence is primary",
            _routine_checks_are_secondary(response),
            response,
        ),
        AssertionFinding(
            "response remains concise",
            len(response) <= 1800,
            f"{len(response)} characters",
        ),
    )
    record_review(
        run,
        spec_file="25-focused-verification-report.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.extended
@pytest.mark.requirements("DOCGUIDE-002", "DOCLOCAL-001", "DOCVAL-010")
def test_26_explicit_optional_layout(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="26-explicit-optional-layout",
        spec_file="26-explicit-optional-layout.md",
        parent=_seed_05(harness),
        fixture_id="batch-sync",
        branch_variant="approved-task-single-decisions",
    )
    paths = set(run.changed_paths)
    specs = matching_paths(
        run,
        "packages/batch-sdk/docs/development/specifications",
    )
    decisions = tuple(path for path in specs if path.endswith("/decisions.md"))
    decision_children = tuple(path for path in specs if "/decisions/" in path)
    rendered = "\n".join(file_text(run, path) for path in specs).lower()
    indexes = "\n".join(
        file_text(run, path).lower() for path in specs if path.endswith("/index.md")
    )
    response = require_run_value(run).response
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "package specification created",
            bool(specs),
            repr(specs),
        ),
        AssertionFinding(
            "approved decision layout honored",
            len(decisions) == 1 and not decision_children,
            f"decisions={decisions!r}, children={decision_children!r}",
        ),
        AssertionFinding(
            "created pages indexed",
            "decisions.md" in indexes and "requirements" in indexes,
            indexes,
        ),
        AssertionFinding(
            "required subjects retained",
            all(
                term in rendered
                for term in (
                    "conflict",
                    "migration",
                    "compatibility",
                    "recovery",
                    "transport",
                    "persistence",
                )
            ),
            rendered,
        ),
        AssertionFinding(
            "requirements pending",
            "not started" in rendered
            and "unverified" in rendered
            and "pending" in rendered,
            rendered,
        ),
        AssertionFinding(
            "no implementation or current README mutation",
            not any(
                path.startswith("packages/batch-sdk/src/")
                or path == "packages/batch-sdk/README.md"
                for path in paths
            ),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "no duplicate approval or shape coercion",
            _placement_communication_is_proportionate(response)
            and "please approve" not in response.lower()
            and "need your approval" not in response.lower()
            and "mandatory directory" not in response.lower(),
            response,
        ),
    )
    record_review(
        run,
        spec_file="26-explicit-optional-layout.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.extended
@pytest.mark.requirements("DOCAGENT-001", "DOCLOCAL-001", "DOCVAL-010")
def test_27_routed_current_guidance(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="27-routed-current-guidance",
        spec_file="27-routed-current-guidance.md",
        parent=_seed_04(harness),
        fixture_id="event-retry",
        guidance_instruction_paths=("AGENTS.md",),
    )
    required_reads = (
        "docs/development/documentation.md",
        "docs/development/crystal-lattice-documentation.md",
    )
    positions = _complete_read_positions(run, required_reads)
    first_mutation = _first_mutation_tool_index(run)
    injection = _evidence_value(run, "documentation_standard.guidance_injection")
    injection_value = injection if isinstance(injection, dict) else {}
    tool_output = "\n".join(
        str(message.get("content", ""))
        for message in _tool_messages(run)
    ).lower()
    paths = set(run.changed_paths)
    public_text = "\n".join(
        file_text(run, path).lower()
        for path in matching_paths(run, "packages/event-sdk/docs")
        if "/development/" not in path
    )
    target_api_mentioned = "replay_failed" in public_text
    target_marked_unavailable = any(
        phrase in public_text
        for phrase in (
            "not currently",
            "not available",
            "no replay",
            "does not exist",
            "future",
            "planned",
            "target-only",
        )
    )
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "routing-only root guidance injected",
            injection_value.get("paths") == ["AGENTS.md"],
            repr(injection_value),
        ),
        AssertionFinding(
            "current pages read completely",
            all(position is not None for position in positions.values()),
            repr(positions),
        ),
        AssertionFinding(
            "current pages read before mutation",
            first_mutation is not None
            and all(
                position is not None and position < first_mutation
                for position in positions.values()
            ),
            f"reads={positions!r}, first_mutation={first_mutation!r}",
        ),
        AssertionFinding(
            "maintainer specification not read",
            "# documentation and specification standard" not in tool_output,
            tool_output,
        ),
        AssertionFinding(
            "package-local documentation only",
            bool(paths)
            and all(path.startswith("packages/event-sdk/") for path in paths)
            and not any(
                path.startswith(
                    ("packages/event-sdk/src/", "packages/event-sdk/tests/")
                )
                for path in paths
            ),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "target-only behavior not presented as available",
            not target_api_mentioned or target_marked_unavailable,
            public_text,
        ),
        AssertionFinding(
            "user documentation does not link internal specifications",
            "development/specifications" not in public_text,
            public_text,
        ),
    )
    record_review(
        run,
        spec_file="27-routed-current-guidance.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.routine
@pytest.mark.requirements("DOCGUIDE-002", "DOCGUIDE-003", "DOCVAL-010")
def test_28_small_package_proportionate_documentation(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="28-small-package-proportionate-documentation",
        spec_file="28-small-package-proportionate-documentation.md",
        parent=_seed_01(harness),
        fixture_id="js-single-file-tool",
    )
    paths = set(run.changed_paths)
    readme_path = "plugins/js-single-file-tool/README.md"
    readme = file_text(run, readme_path).lower()
    shared_changes = tuple(
        path for path in paths if path.startswith("plugins/docs/")
    )
    shared = "\n".join(file_text(run, path).lower() for path in shared_changes)
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "package README improved",
            readme_path in paths
            and "hello" in readme
            and "upper" in readme
            and any(term in readme for term in ("node:", "node_tool", '"file"')),
            readme,
        ),
        AssertionFinding(
            "structure remains small",
            len(shared_changes) <= 1
            and all(
                path == readme_path or path.startswith("plugins/docs/")
                for path in paths
            )
            and not any(
                path.startswith("plugins/js-single-file-tool/docs/")
                for path in paths
            ),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "shared change remains general",
            not shared_changes
            or (
                "single-file" in shared
                and "all node tools uppercase" not in shared
                and "every node tool uppercase" not in shared
                and "must export uppertool" not in shared
            ),
            shared or "no shared change",
        ),
    )
    record_review(
        run,
        spec_file="28-small-package-proportionate-documentation.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.routine
@pytest.mark.requirements("DOCGUIDE-004", "DOCVAL-010")
def test_29_early_user_documentation_is_explicit(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="29-early-user-documentation-is-explicit",
        spec_file="29-early-user-documentation-is-explicit.md",
        parent=_seed_02(harness),
        fixture_id="report-export",
    )
    readme_path = "packages/report-export-sdk/README.md"
    readme = file_text(run, readme_path).lower()
    changed = readme_path in run.changed_paths
    response = require_run_value(run).response.lower()
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "scope remains documentation-only",
            all(
                path == readme_path
                or path.startswith(
                    "packages/report-export-sdk/docs/development/specifications/"
                )
                for path in run.changed_paths
            ),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "target-only text is explicit",
            not changed or "not implemented" in readme,
            readme,
        ),
        AssertionFinding(
            "current behavior remains distinguishable",
            "export_rows" in readme
            and (
                not changed
                or (
                    "not implemented" in readme
                    and any(term in readme for term in ("currently", "existing", "today"))
                )
            ),
            readme,
        ),
        AssertionFinding(
            "temporary status is reported",
            not changed
            or (
                "not implemented" in response
                and any(term in response for term in ("remove", "temporary", "once"))
            ),
            response,
        ),
        AssertionFinding(
            "no implementation mutation",
            not any(
                path.startswith(
                    (
                        "packages/report-export-sdk/src/",
                        "packages/report-export-sdk/tests/",
                    )
                )
                for path in run.changed_paths
            ),
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="29-early-user-documentation-is-explicit.md",
        findings=findings,
    )
    assert_findings(findings)