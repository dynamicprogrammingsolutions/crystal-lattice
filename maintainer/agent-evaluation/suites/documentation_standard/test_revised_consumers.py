from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
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
    selected_reasoning_effort,
)
from .test_consumers import (
    _complete_read_positions,
    _evidence_value,
    _first_mutation_tool_index,
    _placement_communication_is_proportionate,
    _raw_session_text,
    _seed_04,
    _seed_05,
    _seed_08,
    _seed_01,
    _seed_02,
    _tool_command_observed,
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


def _seed_12(harness: DocumentationEvaluationHarness):
    run = harness.seed(
        seed_id="seed-12-status-label-naming",
        spec_file="seed-12-status-label-naming.md",
        fixture_id="status-labels",
    )
    run.raise_for_error()
    assert run.value.completed
    assert not run.changed_paths
    return run


SOURCE_TERM_CASES = (
    pytest.param(
        "task-number",
        "terminology-task-number",
        "## Task-number exact user prompt",
        ("task 010", "task-010", "task_010", "task010"),
        id="task-number",
    ),
    pytest.param(
        "sequence-label",
        "terminology-sequence-label",
        "## Sequence-label exact user prompt",
        ("stage a", "stage-a", "stage_a", "stagea"),
        id="sequence-label",
    ),
    pytest.param(
        "evaluative-wording",
        "terminology-evaluative-wording",
        "## Evaluative-wording exact user prompt",
        ("portable", "useful"),
        id="evaluative-wording",
    ),
)


def _contains_source_term(text: str, terms: tuple[str, ...]) -> bool:
    normalized = text.lower()
    return any(term in normalized for term in terms)


def _markdown_headings(text: str) -> str:
    return "\n".join(
        line.strip() for line in text.splitlines() if line.lstrip().startswith("#")
    )


def _python_function_names(text: str) -> tuple[str, ...]:
    tree = ast.parse(text)
    return tuple(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )


def _python_comments(text: str) -> str:
    return "\n".join(
        line.strip() for line in text.splitlines() if line.lstrip().startswith("#")
    )


def _status_label_behavior_passes(
    run,
    function_name: str,
) -> tuple[bool, str]:
    if run.workspace is None:
        return False, "run has no workspace"
    script = f"""
import sys
sys.path.insert(0, "packages/status-labels/src")
import status_labels

function = getattr(status_labels, {function_name!r})
assert function("in_progress") == "In progress"
assert function("done") == "Done"
try:
    function("unknown")
except KeyError:
    pass
else:
    raise AssertionError("unknown status must raise KeyError")
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=run.workspace,
        check=False,
        capture_output=True,
        text=True,
    )
    detail = (
        "\n".join(value for value in (result.stdout, result.stderr) if value)
        or f"exit code {result.returncode}"
    )
    return result.returncode == 0, detail


def _requirement_reference_is_explained(text: str, requirement_id: str) -> bool:
    for line in text.splitlines():
        lowered = line.lower()
        if requirement_id.lower() not in lowered:
            continue
        without_id = lowered.replace(requirement_id.lower(), "")
        if any(term in without_id for term in ("label", "in_progress", "done")):
            return True
    return False


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
            and (
                "existing" in row_text or "compatib" in row_text or "single" in row_text
            ),
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
                    path.startswith("docs/development/") or "/docs/development/" in path
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
        str(message.get("content", "")) for message in _tool_messages(run)
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
    shared_changes = tuple(path for path in paths if path.startswith("plugins/docs/"))
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
                path.startswith("plugins/js-single-file-tool/docs/") for path in paths
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
                    and any(
                        term in readme for term in ("currently", "existing", "today")
                    )
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


@pytest.mark.extended
@pytest.mark.parametrize(
    ("case_id", "branch_variant", "prompt_heading", "source_terms"),
    SOURCE_TERM_CASES,
)
@pytest.mark.requirements("DOCGUIDE-007", "DOCGUIDE-008", "DOCVAL-011")
def test_30_source_terms_in_specification_records(
    harness: DocumentationEvaluationHarness,
    case_id: str,
    branch_variant: str,
    prompt_heading: str,
    source_terms: tuple[str, ...],
) -> None:
    reasoning_effort = selected_reasoning_effort()
    run = harness.branch(
        test_id=f"30-source-terms-in-specification-records-{case_id}",
        spec_file="30-source-terms-in-specification-records.md",
        parent=_seed_05(harness),
        fixture_id="batch-sync",
        branch_variant=branch_variant,
        prompt_heading=prompt_heading,
        reasoning_effort=reasoning_effort,
    )
    paths = set(run.changed_paths)
    spec_paths = matching_paths(
        run,
        "packages/batch-sdk/docs/development/specifications",
    )
    spec_text = "\n".join(file_text(run, path) for path in spec_paths)
    task = file_text(run, "tasks/batch-offline-sync.md")
    requirements = "\n".join(
        file_text(run, path) for path in spec_paths if path.endswith("/requirements.md")
    )
    development_index = file_text(
        run,
        "packages/batch-sdk/docs/development/index.md",
    )
    identity_text = "\n".join(
        (
            *spec_paths,
            _markdown_headings(spec_text),
            "\n".join(_requirement_rows(requirements)),
            _markdown_headings(development_index),
        )
    )
    destination_text = "\n".join(
        (
            *spec_paths,
            spec_text,
            development_index,
        )
    )
    profile = _evidence_value(run, "documentation_standard.profile")
    profile_value = profile if isinstance(profile, dict) else {}
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "selected reasoning effort recorded",
            reasoning_effort is None
            or profile_value.get("reasoning_effort") == reasoning_effort,
            json.dumps(profile_value, sort_keys=True),
        ),
        AssertionFinding(
            "source wording retained with capability context in task",
            _contains_source_term(task, source_terms)
            and "offline synchronization" in task.lower(),
            task,
        ),
        AssertionFinding(
            "package specification created",
            bool(spec_paths) and any(path.endswith("/index.md") for path in spec_paths),
            repr(spec_paths),
        ),
        AssertionFinding(
            "specification records use capability terms",
            not _contains_source_term(
                identity_text if case_id == "evaluative-wording" else destination_text,
                source_terms,
            ),
            identity_text if case_id == "evaluative-wording" else destination_text,
        ),
        AssertionFinding(
            "requirements remain target-only",
            (
                "not started" in requirements.lower()
                or "not implemented" in requirements.lower()
            )
            and "unverified" in requirements.lower(),
            requirements,
        ),
        AssertionFinding(
            "one decisions file used",
            sum(path.endswith("/decisions.md") for path in spec_paths) == 1
            and not any("/decisions/" in path for path in spec_paths),
            repr(spec_paths),
        ),
        AssertionFinding(
            "development index links the capability",
            "offline" in development_index.lower(),
            development_index,
        ),
        AssertionFinding(
            "scope remains specification-only",
            bool(paths)
            and all(
                path == "tasks/batch-offline-sync.md"
                or path == "packages/batch-sdk/docs/development/index.md"
                or path.startswith(
                    "packages/batch-sdk/docs/development/specifications/"
                )
                for path in paths
            )
            and "packages/batch-sdk/src/batch.py" not in paths,
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="30-source-terms-in-specification-records.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.extended
@pytest.mark.parametrize(
    ("case_id", "branch_variant", "prompt_heading", "source_terms"),
    SOURCE_TERM_CASES,
)
@pytest.mark.requirements("DOCGUIDE-007", "DOCGUIDE-008", "DOCVAL-011")
def test_31_source_terms_in_code_and_tests(
    harness: DocumentationEvaluationHarness,
    case_id: str,
    branch_variant: str,
    prompt_heading: str,
    source_terms: tuple[str, ...],
) -> None:
    reasoning_effort = selected_reasoning_effort()
    run = harness.branch(
        test_id=f"31-source-terms-in-code-and-tests-{case_id}",
        spec_file="31-source-terms-in-code-and-tests.md",
        parent=_seed_12(harness),
        fixture_id="status-labels",
        branch_variant=branch_variant,
        prompt_heading=prompt_heading,
        reasoning_effort=reasoning_effort,
    )
    paths = set(run.changed_paths)
    source_path = "packages/status-labels/src/status_labels.py"
    test_path = "packages/status-labels/tests/test_status_labels.py"
    developer_path = "packages/status-labels/docs/development/status-labels.md"
    requirements_path = (
        "packages/status-labels/docs/development/specifications/"
        "status-labels/requirements.md"
    )
    source = file_text(run, source_path)
    tests = file_text(run, test_path)
    developer = file_text(run, developer_path)
    requirements = file_text(run, requirements_path)
    source_functions = _python_function_names(source)
    test_functions = _python_function_names(tests)
    new_functions = tuple(name for name in source_functions if name != "is_terminal")
    identity_text = "\n".join(
        (
            *paths,
            *source_functions,
            *test_functions,
            _python_comments(source),
            _python_comments(tests),
            _markdown_headings(developer),
            "\n".join(_requirement_rows(requirements)),
        )
    )
    maintained_text = "\n".join((source, tests, developer, requirements))
    behavior_passed, behavior_detail = (
        _status_label_behavior_passes(run, new_functions[0])
        if len(new_functions) == 1
        else (False, f"expected one new public function: {new_functions!r}")
    )
    profile = _evidence_value(run, "documentation_standard.profile")
    profile_value = profile if isinstance(profile, dict) else {}
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "selected reasoning effort recorded",
            reasoning_effort is None
            or profile_value.get("reasoning_effort") == reasoning_effort,
            json.dumps(profile_value, sort_keys=True),
        ),
        AssertionFinding(
            "status-label behavior implemented",
            behavior_passed,
            f"functions={source_functions!r}\n{behavior_detail}",
        ),
        AssertionFinding(
            "established function preserved",
            "is_terminal" in source_functions,
            repr(source_functions),
        ),
        AssertionFinding(
            "source and test identities use behavior terms",
            not _contains_source_term(identity_text, source_terms),
            identity_text,
        ),
        AssertionFinding(
            "maintained implementation text uses behavior terms",
            case_id == "evaluative-wording"
            or not _contains_source_term(maintained_text, source_terms),
            maintained_text,
        ),
        AssertionFinding(
            "requirement traceability explains the assertion",
            _requirement_reference_is_explained(tests, "STATUS-002"),
            tests,
        ),
        AssertionFinding(
            "focused tests executed successfully",
            _tool_command_observed(run, "pytest")
            and "passed" in _raw_session_text(run),
            _raw_session_text(run),
        ),
        AssertionFinding(
            "requirement evidence completed",
            "status-002" in requirements.lower()
            and "implemented" in requirements.lower()
            and "automated" in requirements.lower()
            and "documented" in requirements.lower(),
            requirements,
        ),
        AssertionFinding(
            "developer documentation explains delivered behavior",
            any(name in developer for name in new_functions)
            and "In progress" in developer
            and "Done" in developer,
            developer,
        ),
        AssertionFinding(
            "user documentation and target remain unchanged",
            "packages/status-labels/README.md" not in paths
            and (
                "packages/status-labels/docs/development/specifications/"
                "status-labels/technical-spec.md" not in paths
            ),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "scope remains within approved files",
            bool(paths)
            and all(
                path
                in {
                    "tasks/status-label-formatting.md",
                    source_path,
                    test_path,
                    developer_path,
                    requirements_path,
                }
                for path in paths
            ),
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="31-source-terms-in-code-and-tests.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.extended
@pytest.mark.requirements("DOCGUIDE-007", "DOCGUIDE-008", "DOCVAL-011")
def test_32_inherited_terminology_in_current_user_documentation(
    harness: DocumentationEvaluationHarness,
) -> None:
    """Verify removal of an inherited user-doc label without prompt priming.

    The existing publishing page begins with the internal heading
    ``Milestone Cedar``. The prompt never names that term and asks for current
    supported behavior only. The inherited-label assertion covers
    DOCGUIDE-007, while the user-language, target-exclusion, and one-page scope
    assertions cover DOCGUIDE-008 and DOCVAL-011.
    """

    reasoning_effort = selected_reasoning_effort()
    run = harness.branch(
        test_id="32-inherited-terminology-in-current-user-documentation",
        spec_file="32-inherited-terminology-in-current-user-documentation.md",
        parent=_seed_04(harness),
        fixture_id="event-retry",
        branch_variant="inherited-user-terminology",
        reasoning_effort=reasoning_effort,
    )
    publishing_path = "packages/event-sdk/docs/publishing.md"
    publishing = file_text(run, publishing_path)
    headings = _markdown_headings(publishing)
    lowered = publishing.lower()
    profile = _evidence_value(run, "documentation_standard.profile")
    profile_value = profile if isinstance(profile, dict) else {}
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "selected reasoning effort recorded",
            reasoning_effort is None
            or profile_value.get("reasoning_effort") == reasoning_effort,
            json.dumps(profile_value, sort_keys=True),
        ),
        AssertionFinding(
            "inherited terminology removed",
            "milestone cedar" not in lowered,
            publishing,
        ),
        AssertionFinding(
            "supported publishing behavior preserved",
            "publish(event)" in publishing and "retry" in lowered,
            publishing,
        ),
        AssertionFinding(
            "retry boundary explained",
            ("attempt" in lowered or "limit" in lowered)
            and ("fail" in lowered or "failed" in lowered),
            publishing,
        ),
        AssertionFinding(
            "target-only replay excluded",
            "replay" not in lowered,
            publishing,
        ),
        AssertionFinding(
            "no replacement tracking heading introduced",
            not _contains_source_term(
                headings,
                (
                    "milestone",
                    "phase",
                    "stage",
                    "checkpoint",
                    "workstream",
                    "iteration",
                ),
            ),
            headings,
        ),
        AssertionFinding(
            "page remains independent of internal records",
            not _contains_source_term(
                publishing,
                (
                    "event-001",
                    "event-002",
                    "technical specification",
                    "target-only",
                    "tasks/",
                ),
            ),
            publishing,
        ),
        AssertionFinding(
            "scope remains one current user page",
            run.changed_paths == (publishing_path,),
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="32-inherited-terminology-in-current-user-documentation.md",
        findings=findings,
    )
    assert_findings(findings)
