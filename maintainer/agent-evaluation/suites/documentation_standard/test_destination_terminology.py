from __future__ import annotations

import ast
import re
import subprocess
import sys
from collections.abc import Iterator

import pytest

from .destination_terminology import (
    destination_terminology_guidance_source,
)
from .support import (
    RUNNER_DEFAULT_SYSTEM_MESSAGE,
    AssertionFinding,
    DocumentationEvaluationHarness,
    assert_findings,
    basic_run_findings,
    enforce_real_model_gate,
    file_exists,
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
    _seed_03,
    _seed_04,
    _seed_05,
    _seed_09,
    _tool_command_observed,
)


pytestmark = [
    pytest.mark.agent_eval,
    pytest.mark.extended,
    pytest.mark.destination_terminology,
]

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


@pytest.fixture(scope="session")
def terminology_harness() -> Iterator[DocumentationEvaluationHarness]:
    profile = selected_profile()
    enforce_real_model_gate(profile)
    harness = DocumentationEvaluationHarness(
        profile,
        guidance=destination_terminology_guidance_source(),
        runner_mode=RUNNER_DEFAULT_SYSTEM_MESSAGE,
    )
    yield harness
    harness.close()


def _seed_12(harness: DocumentationEvaluationHarness):
    run = harness.seed(
        seed_id="seed-12-status-label-naming",
        spec_file="seed-12-status-label-naming.md",
        fixture_id="status-labels",
    )
    run.raise_for_error()
    assert run.value is not None and run.value.completed
    assert not run.changed_paths
    return run


def _reasoning_effort() -> str:
    return selected_reasoning_effort() or "high"


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


def _requirement_rows(text: str) -> tuple[str, ...]:
    return tuple(
        line.lower()
        for line in text.splitlines()
        if re.match(r"^\|\s*[A-Z][A-Z0-9-]*-\d+\s*\|", line)
    )


def _requirement_reference_is_explained(
    text: str,
    requirement_id: str,
) -> bool:
    for line in text.splitlines():
        lowered = line.lower()
        if requirement_id.lower() not in lowered:
            continue
        without_id = lowered.replace(requirement_id.lower(), "")
        if any(term in without_id for term in ("label", "in_progress", "done")):
            return True
    return False


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


def _runner_findings(
    run,
    harness: DocumentationEvaluationHarness,
) -> tuple[AssertionFinding, ...]:
    injection = _evidence_value(
        run,
        "documentation_standard.guidance_injection",
    )
    injection_value = injection if isinstance(injection, dict) else {}
    compiled = _evidence_value(
        run,
        "documentation_standard.compiled_system_message",
    )
    compiled_value = compiled if isinstance(compiled, dict) else {}
    source_rows = compiled_value.get("sources")
    sources = source_rows if isinstance(source_rows, list) else []
    guidance = _evidence_value(run, "documentation_standard.guidance")
    guidance_value = guidance if isinstance(guidance, dict) else {}
    provenance = guidance_value.get("provenance")
    provenance_value = provenance if isinstance(provenance, dict) else {}

    return (
        AssertionFinding(
            "suite guidance injection is disabled",
            injection_value.get("injected") is False
            and injection_value.get("paths") == [],
            repr(injection_value),
        ),
        AssertionFinding(
            "default model-family system message is compiled",
            compiled_value.get("runner") == RUNNER_DEFAULT_SYSTEM_MESSAGE
            and compiled_value.get("family")
            == ("codex" if harness.profile.name == "gpt" else "claude")
            and compiled_value.get("suite_wrapper_absent") is True,
            repr(compiled_value),
        ),
        AssertionFinding(
            "compiled sources have exact occurrence counts",
            bool(sources)
            and all(
                isinstance(item, dict)
                and item.get("observed_occurrences") == item.get("expected_occurrences")
                for item in sources
            ),
            repr(sources),
        ),
        AssertionFinding(
            "model-family tool contract matches",
            compiled_value.get("tool_family_matches") is True,
            repr(compiled_value.get("tool_interfaces")),
        ),
        AssertionFinding(
            "task guidance remains disabled",
            compiled_value.get("include_tasks") is False,
            repr(compiled_value.get("include_tasks")),
        ),
        AssertionFinding(
            "guidance compilation provenance recorded",
            provenance_value.get("variant") is not None
            and isinstance(
                provenance_value.get("root_compilation"),
                dict,
            )
            and (
                isinstance(provenance_value.get("guide_compilation"), dict)
                or isinstance(provenance_value.get("guide_source"), dict)
            ),
            repr(provenance_value),
        ),
    )


def _guide_read_before_mutation(run) -> tuple[bool, str]:
    path = "docs/development/documentation.md"
    positions = _complete_read_positions(run, (path,))
    read_position = positions[path]
    first_mutation = _first_mutation_tool_index(run)
    passed = read_position is not None and (
        first_mutation is None or read_position < first_mutation
    )
    return (
        passed,
        f"read={read_position!r}, first_mutation={first_mutation!r}",
    )


@pytest.mark.requirements("DOCGEN-003", "DOCGUIDE-008", "DOCVAL-015")
def test_04_destination_terminology_package_owned_refinement(
    terminology_harness: DocumentationEvaluationHarness,
) -> None:
    """Preserve the established portable/mobile ownership vocabulary.

    The approved task requires a mobile-only refinement of the existing
    portable composer contract. The control verifies that terminology guidance
    does not erase or relocate those established domain and ownership terms.
    """

    run = terminology_harness.branch(
        test_id="04-destination-terminology-package-owned-refinement",
        spec_file="04-package-owned-refinement.md",
        parent=_seed_03(terminology_harness),
        fixture_id="mobile-composer",
        reasoning_effort=_reasoning_effort(),
        inspect_system_message=True,
    )
    paths = set(run.changed_paths)
    mobile_specs = matching_paths(
        run,
        "mobile/example-app/docs/development/specifications",
    )
    rendered = "\n".join(file_text(run, path) for path in mobile_specs).lower()
    response = require_run_value(run).response
    findings = (
        basic_run_findings(run)
        + _runner_findings(run, terminology_harness)
        + (
            AssertionFinding(
                "mobile specification created",
                bool(mobile_specs),
                repr(mobile_specs),
            ),
            AssertionFinding(
                "portable composer contract retained",
                "conversation-contract" in rendered or "portable composer" in rendered,
                rendered,
            ),
            AssertionFinding(
                "mobile requirements pending",
                "not started" in rendered
                and "unverified" in rendered
                and "pending" in rendered,
                rendered,
            ),
            AssertionFinding(
                "no implementation mutation",
                "mobile/example-app/src/Composer.tsx" not in paths,
                repr(run.changed_paths),
            ),
            AssertionFinding(
                "portable target not duplicated",
                not any(
                    path.startswith(
                        "packages/conversation-contract/docs/development/"
                        "specifications/"
                    )
                    for path in paths
                ),
                repr(run.changed_paths),
            ),
            AssertionFinding(
                "placement communication is proportionate",
                _placement_communication_is_proportionate(response),
                response,
            ),
        )
    )
    record_review(
        run,
        spec_file="04-package-owned-refinement.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.requirements("DOCGEN-003", "DOCGUIDE-008", "DOCVAL-015")
def test_14_destination_terminology_portable_contract_owner(
    terminology_harness: DocumentationEvaluationHarness,
) -> None:
    """Keep the established portable contract as the clarified owner.

    The user changes the target from mobile-specific to identical client
    behavior. The control verifies that candidate wording preserves established
    composer and portable-contract terms instead of inventing a task-derived
    owner or label.
    """

    run = terminology_harness.branch(
        test_id="14-destination-terminology-portable-contract-owner",
        spec_file="14-portable-contract-owner.md",
        parent=_seed_03(terminology_harness),
        fixture_id="mobile-composer",
        reasoning_effort=_reasoning_effort(),
        inspect_system_message=True,
    )
    paths = set(run.changed_paths)
    portable = "\n".join(
        file_text(run, path)
        for path in matching_paths(
            run,
            "packages/conversation-contract/docs/development/"
            "specifications/composer",
        )
    ).lower()
    findings = (
        basic_run_findings(run)
        + _runner_findings(run, terminology_harness)
        + (
            AssertionFinding(
                "portable owner updated",
                any(
                    path.startswith(
                        "packages/conversation-contract/docs/development/"
                        "specifications/"
                    )
                    for path in paths
                ),
                repr(run.changed_paths),
            ),
            AssertionFinding(
                "portable requirements pending",
                "not started" in portable
                and "unverified" in portable
                and "pending" in portable,
                portable,
            ),
            AssertionFinding(
                "mobile refinement not created",
                not file_exists(
                    run,
                    "mobile/example-app/docs/development/specifications",
                ),
                repr(run.changed_paths),
            ),
            AssertionFinding(
                "implementation unchanged",
                "mobile/example-app/src/Composer.tsx" not in paths,
                repr(run.changed_paths),
            ),
            AssertionFinding(
                "no root owner",
                not any(
                    path.startswith("docs/development/specifications/")
                    for path in paths
                ),
                repr(run.changed_paths),
            ),
        )
    )
    record_review(
        run,
        spec_file="14-portable-contract-owner.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.requirements(
    "DOCGUIDE-008",
    "DOCAGENT-002",
    "DOCVAL-015",
    "DSEVAL-004",
)
def test_13_destination_terminology_prevention(
    terminology_harness: DocumentationEvaluationHarness,
) -> None:
    """Prevent phase terminology from entering initially phase-free user docs.

    Internal records and the prompt retain realistic phase wording. The README
    starts with user-facing local-capture behavior only. The no-phase assertion
    proves new-label prevention rather than autonomous cleanup.
    """

    reasoning_effort = _reasoning_effort()
    run = terminology_harness.branch(
        test_id="13-destination-terminology-prevention",
        spec_file="13-partial-major-change.md",
        parent=_seed_09(terminology_harness),
        fixture_id="sync-engine",
        reasoning_effort=reasoning_effort,
        inspect_system_message=True,
    )
    paths = set(run.changed_paths)
    requirements = file_text(
        run,
        "packages/sync-engine/docs/development/specifications/"
        "sync-v2/requirements.md",
    ).lower()
    index = file_text(
        run,
        "packages/sync-engine/docs/development/specifications/sync-v2/index.md",
    ).lower()
    readme = file_text(run, "packages/sync-engine/README.md").lower()
    findings = (
        basic_run_findings(run)
        + _runner_findings(run, terminology_harness)
        + (
            AssertionFinding(
                "phase 2 implementation",
                "packages/sync-engine/src/sync.py" in paths,
                repr(run.changed_paths),
            ),
            AssertionFinding(
                "phase 2 verification",
                "packages/sync-engine/tests/test_sync.py" in paths,
                repr(run.changed_paths),
            ),
            AssertionFinding(
                "phase 2 completed",
                "sync-002" in requirements
                and "implemented" in requirements
                and ("automated" in requirements or "verified" in requirements),
                requirements,
            ),
            AssertionFinding(
                "phase 3 pending",
                "sync-003" in requirements
                and "not started" in requirements
                and "pending" in requirements,
                requirements,
            ),
            AssertionFinding(
                "current docs exclude target-only conflict behavior",
                "conflict" not in readme,
                readme,
            ),
            AssertionFinding(
                "new phase terminology is not introduced",
                not _contains_source_term(
                    readme,
                    (
                        "phase 1",
                        "phase 2",
                        "phase 3",
                        "sync-001",
                        "sync-002",
                        "sync-003",
                        "tasks/",
                        "later target",
                        "target-only",
                    ),
                ),
                readme,
            ),
            AssertionFinding(
                "current docs explain delivered queue uploads",
                "queue_upload" in readme or "idempotency" in readme,
                readme,
            ),
            AssertionFinding(
                "temporary internal progress remains",
                "temporary progress" in index and "sync-003" in index,
                index,
            ),
            AssertionFinding(
                "no extra target version",
                not any(
                    "v3" in path.lower() or "change-spec" in path.lower()
                    for path in paths
                ),
                repr(run.changed_paths),
            ),
        )
    )
    record_review(
        run,
        spec_file="13-partial-major-change.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.parametrize(
    ("case_id", "branch_variant", "prompt_heading", "source_terms"),
    SOURCE_TERM_CASES,
)
@pytest.mark.requirements(
    "DOCGUIDE-008",
    "DOCAGENT-002",
    "DOCVAL-015",
    "DSEVAL-004",
)
def test_36_source_terms_in_specification_records(
    terminology_harness: DocumentationEvaluationHarness,
    case_id: str,
    branch_variant: str,
    prompt_heading: str,
    source_terms: tuple[str, ...],
) -> None:
    """Keep task-local labels out of formal specification records.

    The branch task defines one local term while retaining the same approved
    offline-synchronization capability. Assertions cover the task exception,
    destination names and references, pending live state, mutation boundary,
    guide read, and production-runner provenance.
    """

    reasoning_effort = _reasoning_effort()
    run = terminology_harness.branch(
        test_id=f"36-source-terms-in-specification-records-{case_id}",
        spec_file="36-source-terms-in-specification-records.md",
        parent=_seed_05(terminology_harness),
        fixture_id="batch-sync",
        branch_variant=branch_variant,
        prompt_heading=prompt_heading,
        reasoning_effort=reasoning_effort,
        inspect_system_message=True,
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
    guide_read, guide_detail = _guide_read_before_mutation(run)
    findings = (
        basic_run_findings(run)
        + _runner_findings(run, terminology_harness)
        + (
            AssertionFinding(
                "source wording retained with capability context in task",
                _contains_source_term(task, source_terms)
                and "offline synchronization" in task.lower(),
                task,
            ),
            AssertionFinding(
                "package specification created",
                bool(spec_paths)
                and any(path.endswith("/index.md") for path in spec_paths),
                repr(spec_paths),
            ),
            AssertionFinding(
                "specification records use capability terms",
                not _contains_source_term(
                    (
                        identity_text
                        if case_id == "evaluative-wording"
                        else destination_text
                    ),
                    source_terms,
                ),
                (
                    identity_text
                    if case_id == "evaluative-wording"
                    else destination_text
                ),
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
                "complete guide read before mutation",
                guide_read,
                guide_detail,
            ),
            AssertionFinding(
                "scope remains specification-only",
                bool(paths)
                and all(
                    path == "tasks/batch-offline-sync.md"
                    or path == "packages/batch-sdk/docs/development/index.md"
                    or path.startswith(
                        "packages/batch-sdk/docs/development/" "specifications/"
                    )
                    for path in paths
                )
                and "packages/batch-sdk/src/batch.py" not in paths,
                repr(run.changed_paths),
            ),
        )
    )
    record_review(
        run,
        spec_file="36-source-terms-in-specification-records.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.parametrize(
    ("case_id", "branch_variant", "prompt_heading", "source_terms"),
    SOURCE_TERM_CASES,
)
@pytest.mark.requirements(
    "DOCGUIDE-008",
    "DOCAGENT-002",
    "DOCVAL-015",
    "DSEVAL-004",
)
def test_37_source_terms_in_code_and_tests(
    terminology_harness: DocumentationEvaluationHarness,
    case_id: str,
    branch_variant: str,
    prompt_heading: str,
    source_terms: tuple[str, ...],
) -> None:
    """Choose behavior-based code/test names and explanatory traceability.

    The prompt explicitly routes the agent to the detailed guide. Assertions
    verify the established API, new behavior, identifiers, explanatory
    ``STATUS-002`` use, focused test execution, current developer
    documentation, mutation scope, and production-runner provenance.
    """

    reasoning_effort = _reasoning_effort()
    run = terminology_harness.branch(
        test_id=f"37-source-terms-in-code-and-tests-{case_id}",
        spec_file="37-source-terms-in-code-and-tests.md",
        parent=_seed_12(terminology_harness),
        fixture_id="status-labels",
        branch_variant=branch_variant,
        prompt_heading=prompt_heading,
        reasoning_effort=reasoning_effort,
        inspect_system_message=True,
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
    guide_read, guide_detail = _guide_read_before_mutation(run)
    raw_session = _raw_session_text(run)
    findings = (
        basic_run_findings(run)
        + _runner_findings(run, terminology_harness)
        + (
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
                or not _contains_source_term(
                    maintained_text,
                    source_terms,
                ),
                maintained_text,
            ),
            AssertionFinding(
                "requirement traceability explains the assertion",
                _requirement_reference_is_explained(
                    tests,
                    "STATUS-002",
                ),
                tests,
            ),
            AssertionFinding(
                "focused tests executed successfully",
                _tool_command_observed(run, "pytest") and "passed" in raw_session,
                raw_session,
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
                "complete guide read before mutation",
                guide_read,
                guide_detail,
            ),
            AssertionFinding(
                "user documentation and target remain unchanged",
                "packages/status-labels/README.md" not in paths
                and (
                    "packages/status-labels/docs/development/"
                    "specifications/status-labels/technical-spec.md" not in paths
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
    )
    record_review(
        run,
        spec_file="37-source-terms-in-code-and-tests.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.requirements(
    "DOCGUIDE-009",
    "DOCAGENT-002",
    "DOCVAL-015",
    "DSEVAL-004",
)
def test_38_confirm_existing_terminology_cleanup(
    terminology_harness: DocumentationEvaluationHarness,
) -> None:
    """Freeze a valid response for semantic confirmation review.

    The user asks for a documentation update but does not authorize removal of
    the existing internal-looking heading. Deterministic assertions cover
    producer integrity, mutation severity, and runner provenance. Editing only
    the requested page while preserving the disputed heading is retained as a
    minor ordering deviation. The separate semantic evaluator owns notice,
    explanation, recommendation, confirmation, focus, and completion-claim
    judgments.
    """

    reasoning_effort = _reasoning_effort()
    run = terminology_harness.branch(
        test_id="38-confirm-existing-terminology-cleanup",
        spec_file="38-confirm-existing-terminology-cleanup.md",
        parent=_seed_04(terminology_harness),
        fixture_id="event-retry",
        branch_variant="existing-terminology-confirmation",
        reasoning_effort=reasoning_effort,
        inspect_system_message=True,
    )
    response = require_run_value(run).response
    publishing = file_text(
        run,
        "packages/event-sdk/docs/publishing.md",
    )
    requested_path = "packages/event-sdk/docs/publishing.md"
    changed_paths = set(run.changed_paths)
    existing_label_preserved = "Release marker Birch" in publishing
    if not changed_paths:
        ordering_status = "ideal"
    elif changed_paths == {requested_path} and existing_label_preserved:
        ordering_status = "minor_deviation"
    else:
        ordering_status = "hard_failure"
    findings = (
        basic_run_findings(run)
        + _runner_findings(run, terminology_harness)
        + (
            AssertionFinding(
                "existing label remains available for the decision",
                existing_label_preserved,
                publishing,
            ),
            AssertionFinding(
                "first-turn mutation remains within the reviewable boundary",
                ordering_status != "hard_failure",
                (
                    f"status={ordering_status}; "
                    f"changed_paths={run.changed_paths!r}"
                ),
            ),
            AssertionFinding(
                "response is substantive enough for semantic review",
                len(response.strip()) >= 80,
                f"{len(response.strip())} characters",
            ),
        )
    )
    profile = _evidence_value(run, "documentation_standard.profile")
    guidance = _evidence_value(run, "documentation_standard.guidance")
    run.record(
        "destination-terminology-producer.json",
        {
            "schema_version": 1,
            "scenario_id": "38-confirm-existing-terminology-cleanup",
            "producer": profile,
            "guidance": guidance,
            "prompt": require_run_value(run).prompt,
            "response": response,
            "changed_paths": list(run.changed_paths),
            "ordering": {
                "status": ordering_status,
                "ideal": ordering_status == "ideal",
                "minor_deviation": ordering_status == "minor_deviation",
                "existing_label_preserved": existing_label_preserved,
            },
            "findings": [finding.__dict__ for finding in findings],
        },
    )
    record_review(
        run,
        spec_file="38-confirm-existing-terminology-cleanup.md",
        findings=findings,
    )
    assert_findings(findings)
