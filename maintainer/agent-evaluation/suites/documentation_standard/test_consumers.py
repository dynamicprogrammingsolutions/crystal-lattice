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
    file_exists,
    file_text,
    matching_paths,
    record_review,
    selected_profile,
)


pytestmark = pytest.mark.agent_eval


def _contains_any(text: str, values: tuple[str, ...]) -> bool:
    return any(value in text for value in values)


def _markdown_requirement_row(text: str, requirement_id: str) -> tuple[str, ...]:
    for line in text.splitlines():
        if requirement_id.lower() not in line.lower() or "|" not in line:
            continue
        return tuple(value.strip().lower() for value in line.strip().strip("|").split("|"))
    return ()


def _raw_session(run) -> dict[str, object]:
    path = run.artifact_dir / "raw/environment/crystal-lattice-session.json"
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _tool_command_observed(run, needle: str) -> bool:
    needle = needle.lower()
    data = _raw_session(run)
    messages = data.get("messages")
    if isinstance(messages, list):
        for message in messages:
            if not isinstance(message, dict) or message.get("role") != "tool":
                continue
            metadata = message.get("metadata")
            if not isinstance(metadata, dict):
                continue
            display = metadata.get("display")
            if not isinstance(display, dict):
                continue
            content = display.get("content")
            if (
                isinstance(content, str)
                and needle in content.lower()
                and (
                    "command:" in content.lower()
                    or display.get("single_line") == "Bash command"
                )
            ):
                return True

    native = data.get("metadata")

    def has_command(value: object) -> bool:
        if isinstance(value, dict):
            for key, item in value.items():
                if (
                    key.lower() in {"command", "cmd"}
                    and isinstance(item, str)
                    and needle in item.lower()
                ):
                    return True
                if has_command(item):
                    return True
        elif isinstance(value, list):
            return any(has_command(item) for item in value)
        return False

    return has_command(native)


def _raw_session_text(run) -> str:
    return json.dumps(_raw_session(run)).lower()


@pytest.fixture(scope="session")
def harness() -> Iterator[DocumentationEvaluationHarness]:
    profile = selected_profile()
    enforce_real_model_gate(profile)
    value = DocumentationEvaluationHarness(profile)
    yield value
    value.close()


def _seed_01(harness: DocumentationEvaluationHarness):
    seed = harness.seed(
        seed_id="seed-01-js-single-file-tool-documentation",
        spec_file="seed-01-js-single-file-tool-documentation.md",
        fixture_id="js-single-file-tool",
    )
    seed.raise_for_error()
    assert seed.value.completed
    assert not seed.changed_paths
    return seed


@pytest.mark.routine
@pytest.mark.requirements("DOCGEN-001", "DOCVAL-008")
def test_01_small_package_documentation(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="01-small-package-documentation",
        spec_file="01-small-package-documentation.md",
        parent=_seed_01(harness),
        fixture_id="js-single-file-tool",
    )
    readme = file_text(run, "plugins/js-single-file-tool/README.md")
    lower = readme.lower()
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "README-only mutation",
            run.changed_paths == ("plugins/js-single-file-tool/README.md",),
            repr(run.changed_paths),
        ),
        AssertionFinding("upper documented", "upper" in lower, "upper is present"),
        AssertionFinding(
            "configuration documented",
            "node:" in readme or "node_tool" in readme,
            "expected node loading form",
        ),
        AssertionFinding(
            "first use documented",
            "hello" in lower and "hello".upper() in readme,
            "expected input/output example",
        ),
        AssertionFinding(
            "verification documented",
            "verif" in lower or "confirm" in lower or "expected" in lower,
            "expected practical verification language",
        ),
    )
    record_review(
        run,
        spec_file="01-small-package-documentation.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.routine
@pytest.mark.requirements(
    "DOCGEN-001",
    "DOCGEN-007",
    "DOCREP-006",
    "DOCVAL-007",
    "DOCVAL-008",
)
def test_02_generated_output_correction(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="02-generated-output-correction",
        spec_file="02-generated-output-correction.md",
        parent=_seed_01(harness),
        fixture_id="js-single-file-tool",
        branch_variant="generated-typo",
    )
    readme = file_text(run, "plugins/js-single-file-tool/README.md")
    prepared = file_text(
        run,
        "docs_site/prepared/plugins/js-single-file-tool/index.md",
    )
    response = run.value.response.lower()
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "authored source corrected",
            "npm --version" in readme and "npm --vesion" not in readme,
            "README should contain corrected command",
        ),
        AssertionFinding(
            "source-only mutation",
            run.changed_paths == ("plugins/js-single-file-tool/README.md",),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "prepared output unchanged",
            "generated from plugins/js-single-file-tool/README.md" in prepared
            and "npm --vesion" in prepared,
            "prepared page should retain the original typo",
        ),
        AssertionFinding(
            "blocked refresh reported",
            _contains_any(
                response,
                ("unavailable", "not available", "missing", "cannot", "could not", "blocked"),
            )
            and _contains_any(response, ("generat", "prepar", "refresh")),
            "expected unavailable generation and remaining refresh action",
        ),
        AssertionFinding(
            "completion remains honest",
            _contains_any(
                response,
                ("not regenerated", "not refreshed", "could not regenerate", "unable to"),
            ),
            "expected explicit statement that generated output was not refreshed",
        ),
    )
    record_review(
        run,
        spec_file="02-generated-output-correction.md",
        findings=findings,
    )
    assert_findings(findings)


def _read_only_seed(
    harness: DocumentationEvaluationHarness,
    *,
    seed_id: str,
    spec_file: str,
    fixture_id: str,
):
    run = harness.seed(
        seed_id=seed_id,
        spec_file=spec_file,
        fixture_id=fixture_id,
    )
    run.raise_for_error()
    assert run.value.completed
    assert not run.changed_paths
    return run


def _seed_02(harness: DocumentationEvaluationHarness):
    return _read_only_seed(
        harness,
        seed_id="seed-02-report-export-row-limit",
        spec_file="seed-02-report-export-row-limit.md",
        fixture_id="report-export",
    )


def _seed_03(harness: DocumentationEvaluationHarness):
    return _read_only_seed(
        harness,
        seed_id="seed-03-mobile-composer-refinement",
        spec_file="seed-03-mobile-composer-refinement.md",
        fixture_id="mobile-composer",
    )


def _seed_04(harness: DocumentationEvaluationHarness):
    return _read_only_seed(
        harness,
        seed_id="seed-04-event-retry-documentation",
        spec_file="seed-04-event-retry-documentation.md",
        fixture_id="event-retry",
    )


def _seed_05(harness: DocumentationEvaluationHarness):
    return _read_only_seed(
        harness,
        seed_id="seed-05-batch-sync-design",
        spec_file="seed-05-batch-sync-design.md",
        fixture_id="batch-sync",
    )


def _seed_06(harness: DocumentationEvaluationHarness):
    return _read_only_seed(
        harness,
        seed_id="seed-06-existing-contract-bugfix",
        spec_file="seed-06-existing-contract-bugfix.md",
        fixture_id="path-policy",
    )


def _seed_07(harness: DocumentationEvaluationHarness):
    return _read_only_seed(
        harness,
        seed_id="seed-07-local-bugfix",
        spec_file="seed-07-local-bugfix.md",
        fixture_id="slug-utils",
    )


def _seed_08(harness: DocumentationEvaluationHarness):
    run = harness.seed(
        seed_id="seed-08-completed-small-implementation",
        spec_file="seed-08-completed-small-implementation.md",
        fixture_id="label-utils",
    )
    run.raise_for_error()
    assert run.value.completed
    assert set(run.changed_paths) == {
        "packages/label-utils/src/labels.py",
        "packages/label-utils/tests/test_labels.py",
    }
    return run


def _seed_09(harness: DocumentationEvaluationHarness):
    return _read_only_seed(
        harness,
        seed_id="seed-09-partial-major-change",
        spec_file="seed-09-partial-major-change.md",
        fixture_id="sync-engine",
    )


@pytest.mark.routine
@pytest.mark.requirements("DOCGEN-002")
def test_03_target_specification_workflow(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="03-target-specification-workflow",
        spec_file="03-target-specification-workflow.md",
        parent=_seed_02(harness),
        fixture_id="report-export",
    )
    paths = set(run.changed_paths)
    requirement = file_text(
        run,
        "packages/report-export-sdk/docs/development/specifications/"
        "export-limits/requirements.md",
    ).lower()
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "implementation changed",
            "packages/report-export-sdk/src/report_export.py" in paths,
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "tests changed",
            "packages/report-export-sdk/tests/test_report_export.py" in paths,
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "target changed",
            any("export-limits" in path and path.endswith(".md") for path in paths),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "current README changed",
            "packages/report-export-sdk/README.md" in paths,
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "requirement tracks delivery",
            "max_rows" in requirement
            and "implemented" in requirement
            and ("automated" in requirement or "verified" in requirement),
            "expected completed max_rows evidence",
        ),
        AssertionFinding(
            "no unnecessary target version",
            not any("v2" in path.lower() or "change-spec" in path.lower() for path in paths),
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="03-target-specification-workflow.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.routine
@pytest.mark.requirements("DOCGEN-003")
def test_04_package_owned_refinement(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="04-package-owned-refinement",
        spec_file="04-package-owned-refinement.md",
        parent=_seed_03(harness),
        fixture_id="mobile-composer",
    )
    paths = set(run.changed_paths)
    mobile_specs = matching_paths(
        run,
        "mobile/example-app/docs/development/specifications",
    )
    rendered = "\n".join(file_text(run, path) for path in mobile_specs).lower()
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "mobile specification created",
            bool(mobile_specs),
            repr(mobile_specs),
        ),
        AssertionFinding(
            "portable contract linked",
            "conversation-contract" in rendered or "portable composer" in rendered,
            "expected link/reference to portable owner",
        ),
        AssertionFinding(
            "mobile requirements pending",
            "not started" in rendered
            and "unverified" in rendered
            and "pending" in rendered,
            "expected pending live state",
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
                    "packages/conversation-contract/docs/development/specifications/"
                )
                for path in paths
            ),
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="04-package-owned-refinement.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.routine
@pytest.mark.requirements(
    "DOCGEN-004",
    "DOCGEN-006",
    "DOCREP-006",
    "DOCVAL-007",
    "DOCVAL-008",
)
def test_05_normative_owner_and_discoverability(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="05-normative-owner-and-discoverability",
        spec_file="05-normative-owner-and-discoverability.md",
        parent=_seed_04(harness),
        fixture_id="event-retry",
    )
    readme = file_text(run, "packages/event-sdk/README.md").lower()
    index = file_text(run, "packages/event-sdk/docs/index.md").lower()
    current_docs = "\n".join(
        file_text(run, path)
        for path in matching_paths(run, "packages/event-sdk/docs")
        if "/development/" not in path
    ).lower()
    consumer_text = f"{readme}\n{current_docs}"
    paths = set(run.changed_paths)
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "package discovery improved",
            (
                re.search(r"\bretr(?:y|ies|ied|ying)\b", readme) is not None
                or "publishing.md" in readme
            )
            and "retry" in index,
            "README and docs index should route to retry lifecycle",
        ),
        AssertionFinding(
            "implemented lifecycle explained",
            "retrying" in current_docs and "failed" in current_docs,
            "expected retry states in current user docs",
        ),
        AssertionFinding(
            "target-only replay excluded",
            "replay_failed" not in current_docs
            and "replay persisted failed" not in current_docs,
            "future replay must remain target-only",
        ),
        AssertionFinding(
            "consumer docs exclude internal target links",
            "development/specifications" not in consumer_text
            and "event-lifecycle/technical-spec" not in consumer_text,
            "consumer docs must not depend on the internal target",
        ),
        AssertionFinding(
            "consumer docs exclude internal tracking context",
            not _contains_any(
                consumer_text,
                ("event-002", "target-only", "temporary progress", "tasks/"),
            ),
            "consumer docs should use package-user vocabulary",
        ),
        AssertionFinding(
            "normative target not duplicated",
            not any(
                "event-lifecycle/technical-spec.md" in path
                or "event-lifecycle/requirements.md" in path
                for path in paths
            ),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "implementation unchanged",
            not any(path.startswith("packages/event-sdk/src/") for path in paths),
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="05-normative-owner-and-discoverability.md",
        findings=findings,
    )
    assert_findings(findings)


def _test_06_first_turn(harness: DocumentationEvaluationHarness):
    return harness.branch(
        test_id="06-substantial-specification-approval-first",
        spec_file="06-substantial-specification-approval.md",
        parent=_seed_05(harness),
        fixture_id="batch-sync",
        prompt_heading="## First exact user prompt",
    )


@pytest.mark.routine
@pytest.mark.requirements("DOCGEN-005", "DOCVAL-008")
def test_06_substantial_specification_approval(
    harness: DocumentationEvaluationHarness,
) -> None:
    first = _test_06_first_turn(harness)
    response = first.value.response.lower()
    first_findings = basic_run_findings(first) + (
        AssertionFinding(
            "no pre-approval mutation",
            not first.changed_paths,
            repr(first.changed_paths),
        ),
        AssertionFinding(
            "approval requested",
            "approv" in response,
            "expected explicit approval request",
        ),
        AssertionFinding(
            "proposal is concrete",
            all(term in response for term in ("owner", "scope", "artifact")),
            "expected owner, scope, and artifacts",
        ),
        AssertionFinding(
            "overlap considered",
            "transport" in response and "persistence" in response,
            "expected relationship to existing contracts",
        ),
        AssertionFinding(
            "approval-ready proposal remains concise",
            len(first.value.response) <= 6000,
            f"{len(first.value.response)} characters",
        ),
    )
    record_review(
        first,
        spec_file="06-substantial-specification-approval.md",
        findings=first_findings,
    )
    assert_findings(first_findings)

    second = harness.branch_from_parent_workspace(
        test_id="06-substantial-specification-approval-second",
        spec_file="06-substantial-specification-approval.md",
        parent=first,
        fixture_id="batch-sync",
        branch_variant="approved-conversation",
        prompt_heading="## Second exact user prompt",
    )
    specs = matching_paths(
        second,
        "packages/batch-sdk/docs/development/specifications",
    )
    rendered = "\n".join(file_text(second, path) for path in specs).lower()
    second_findings = basic_run_findings(second) + (
        AssertionFinding("package specification created", bool(specs), repr(specs)),
        AssertionFinding(
            "substantial behavior covered",
            all(
                term in rendered
                for term in ("conflict", "migration", "compatibility", "recovery")
            ),
            "expected approved protocol dimensions",
        ),
        AssertionFinding(
            "requirements pending",
            "not started" in rendered
            and "unverified" in rendered
            and "pending" in rendered,
            "expected target-only live state",
        ),
        AssertionFinding(
            "no implementation",
            not any(
                path.startswith("packages/batch-sdk/src/")
                for path in second.changed_paths
            ),
            repr(second.changed_paths),
        ),
        AssertionFinding(
            "no root specification",
            not any(path.startswith("docs/development/specifications/") for path in second.changed_paths),
            repr(second.changed_paths),
        ),
    )
    record_review(
        second,
        spec_file="06-substantial-specification-approval.md",
        findings=second_findings,
    )
    assert_findings(second_findings)


def _test_07_run(harness: DocumentationEvaluationHarness):
    return harness.branch(
        test_id="07-approved-task-specification-only",
        spec_file="07-approved-task-specification-only.md",
        parent=_seed_02(harness),
        fixture_id="report-export",
    )


@pytest.mark.routine
@pytest.mark.requirements("DOCGEN-002", "DOCVAL-008")
def test_07_approved_task_specification_only(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = _test_07_run(harness)
    paths = set(run.changed_paths)
    spec_text = "\n".join(
        file_text(run, path)
        for path in matching_paths(
            run,
            "packages/report-export-sdk/docs/development/specifications/export-limits",
        )
    ).lower()
    max_rows_row = _markdown_requirement_row(spec_text, "max_rows")
    findings = basic_run_findings(run) + (
        AssertionFinding("target prepared", "max_rows" in spec_text, "missing max_rows"),
        AssertionFinding(
            "requirements pending",
            len(max_rows_row) >= 6
            and max_rows_row[2] == "not started"
            and max_rows_row[3] == "unverified"
            and max_rows_row[4] == "pending",
            repr(max_rows_row),
        ),
        AssertionFinding(
            "no code or test mutation",
            not any(
                path.startswith("packages/report-export-sdk/src/")
                or path.startswith("packages/report-export-sdk/tests/")
                for path in paths
            ),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "no current README mutation",
            "packages/report-export-sdk/README.md" not in paths,
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="07-approved-task-specification-only.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.extended
@pytest.mark.requirements("DOCGEN-002")
def test_08_approved_specification_implementation(
    harness: DocumentationEvaluationHarness,
) -> None:
    parent = _test_07_run(harness)
    run = harness.branch_from_parent_workspace(
        test_id="08-approved-specification-implementation",
        spec_file="08-approved-specification-implementation.md",
        parent=parent,
        fixture_id="report-export",
        branch_variant="prepared-target",
    )
    paths = set(run.changed_paths)
    requirement = file_text(
        run,
        "packages/report-export-sdk/docs/development/specifications/"
        "export-limits/requirements.md",
    ).lower()
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "implementation delivered",
            "packages/report-export-sdk/src/report_export.py" in paths,
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "verification delivered",
            "packages/report-export-sdk/tests/test_report_export.py" in paths,
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "current docs delivered",
            "packages/report-export-sdk/README.md" in paths,
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "live evidence completed",
            "implemented" in requirement
            and ("automated" in requirement or "verified" in requirement)
            and "documented" in requirement,
            "expected completed requirement evidence",
        ),
        AssertionFinding(
            "no new target version",
            not any("v2" in path.lower() or "change-spec" in path.lower() for path in paths),
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="08-approved-specification-implementation.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.extended
@pytest.mark.requirements("DOCGEN-002", "DOCGEN-003", "DOCGEN-005")
def test_09_task_authorized_new_specification(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="09-task-authorized-new-specification",
        spec_file="09-task-authorized-new-specification.md",
        parent=_seed_05(harness),
        fixture_id="batch-sync",
        branch_variant="approved-task",
    )
    specs = matching_paths(
        run,
        "packages/batch-sdk/docs/development/specifications",
    )
    rendered = "\n".join(file_text(run, path) for path in specs).lower()
    response = run.value.response.lower()
    findings = basic_run_findings(run) + (
        AssertionFinding("package specification created", bool(specs), repr(specs)),
        AssertionFinding(
            "approved task used",
            "approv" in response and "task" in response,
            "expected task authorization in response",
        ),
        AssertionFinding(
            "no duplicate approval request",
            "please approve" not in response and "need your approval" not in response,
            run.value.response,
        ),
        AssertionFinding(
            "requirements pending",
            "not started" in rendered
            and "unverified" in rendered
            and "pending" in rendered,
            "expected target-only states",
        ),
        AssertionFinding(
            "no implementation",
            not any(path.startswith("packages/batch-sdk/src/") for path in run.changed_paths),
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="09-task-authorized-new-specification.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.routine
@pytest.mark.requirements("DOCGEN-002")
def test_10_bug_fix_with_existing_specification(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="10-bug-fix-with-existing-specification",
        spec_file="10-bug-fix-with-existing-specification.md",
        parent=_seed_06(harness),
        fixture_id="path-policy",
    )
    paths = set(run.changed_paths)
    requirement = file_text(
        run,
        "packages/path-policy/docs/development/specifications/"
        "path-normalization/requirements.md",
    ).lower()
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "implementation fixed",
            "packages/path-policy/src/path_policy.py" in paths,
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "regression added",
            "packages/path-policy/tests/test_path_policy.py" in paths,
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "target remains stable",
            "packages/path-policy/docs/development/specifications/"
            "path-normalization/technical-spec.md"
            not in paths,
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "live evidence updated",
            "verified" in requirement or "automated" in requirement,
            "expected regression evidence",
        ),
        AssertionFinding(
            "no new specification",
            len(
                matching_paths(
                    run,
                    "packages/path-policy/docs/development/specifications",
                )
            )
            == 3,
            "expected only existing index/technical/requirements",
        ),
    )
    record_review(
        run,
        spec_file="10-bug-fix-with-existing-specification.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.routine
@pytest.mark.requirements("DOCGEN-002", "DOCGEN-005")
def test_11_local_bugfix_without_durable_specification(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="11-local-bugfix-without-durable-specification",
        spec_file="11-local-bugfix-without-durable-specification.md",
        parent=_seed_07(harness),
        fixture_id="slug-utils",
    )
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "code and test only",
            set(run.changed_paths)
            == {
                "packages/slug-utils/src/slug_cache.py",
                "packages/slug-utils/tests/test_slug_cache.py",
            },
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "no specification",
            not file_exists(run, "packages/slug-utils/docs"),
            "unexpected docs tree",
        ),
        AssertionFinding(
            "README unchanged",
            "packages/slug-utils/README.md" not in run.changed_paths,
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="11-local-bugfix-without-durable-specification.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.extended
@pytest.mark.requirements("DOCGEN-002", "DOCGEN-004")
def test_12_documentation_followup_after_implementation(
    harness: DocumentationEvaluationHarness,
) -> None:
    parent = _seed_08(harness)
    run = harness.branch_from_parent_workspace(
        test_id="12-documentation-follow-up-after-implementation",
        spec_file="12-documentation-follow-up-after-implementation.md",
        parent=parent,
        fixture_id="label-utils",
        branch_variant="implemented",
    )
    paths = set(run.changed_paths)
    requirement = file_text(
        run,
        "packages/label-utils/docs/development/specifications/"
        "label-normalization/requirements.md",
    ).lower()
    readme = file_text(run, "packages/label-utils/README.md").lower()
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "implementation remains unchanged",
            not any(
                path.startswith("packages/label-utils/src/")
                or path.startswith("packages/label-utils/tests/")
                for path in paths
            ),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "current README updated",
            "trim_whitespace" in readme,
            "expected delivered option in README",
        ),
        AssertionFinding(
            "tracking completed",
            "implemented" in requirement
            and ("automated" in requirement or "verified" in requirement)
            and "documented" in requirement,
            "expected completed live evidence",
        ),
        AssertionFinding(
            "target stable",
            "packages/label-utils/docs/development/specifications/"
            "label-normalization/technical-spec.md"
            not in paths,
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="12-documentation-follow-up-after-implementation.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.routine
@pytest.mark.requirements(
    "DOCGEN-002",
    "DOCGEN-006",
    "DOCREP-006",
    "DOCVAL-007",
    "DOCVAL-008",
)
def test_13_partial_major_change(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="13-partial-major-change",
        spec_file="13-partial-major-change.md",
        parent=_seed_09(harness),
        fixture_id="sync-engine",
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
    findings = basic_run_findings(run) + (
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
            "expected Phase 2 completed evidence",
        ),
        AssertionFinding(
            "phase 3 pending",
            "sync-003" in requirements
            and "not started" in requirements
            and "pending" in requirements,
            "expected Phase 3 pending",
        ),
        AssertionFinding(
            "current docs exclude phase 3",
            "conflict" not in readme,
            "README should describe only delivered phases",
        ),
        AssertionFinding(
            "current docs exclude internal progress vocabulary",
            not _contains_any(
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
            "expected delivered behavior in package-user vocabulary",
        ),
        AssertionFinding(
            "temporary progress remains",
            "temporary progress" in index and "sync-003" in index,
            "expected remaining progress boundary",
        ),
        AssertionFinding(
            "no extra target version",
            not any("v3" in path.lower() or "change-spec" in path.lower() for path in paths),
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="13-partial-major-change.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.extended
@pytest.mark.requirements("DOCGEN-003")
def test_14_portable_contract_owner(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="14-portable-contract-owner",
        spec_file="14-portable-contract-owner.md",
        parent=_seed_03(harness),
        fixture_id="mobile-composer",
    )
    paths = set(run.changed_paths)
    portable = "\n".join(
        file_text(run, path)
        for path in matching_paths(
            run,
            "packages/conversation-contract/docs/development/specifications/composer",
        )
    ).lower()
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "portable owner updated",
            any(
                path.startswith(
                    "packages/conversation-contract/docs/development/specifications/"
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
            "expected pending portable target",
        ),
        AssertionFinding(
            "mobile refinement not created",
            not file_exists(
                run,
                "mobile/example-app/docs/development/specifications",
            ),
            "unexpected mobile refinement",
        ),
        AssertionFinding(
            "implementation unchanged",
            "mobile/example-app/src/Composer.tsx" not in paths,
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "no root owner",
            not any(path.startswith("docs/development/specifications/") for path in paths),
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="14-portable-contract-owner.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.routine
@pytest.mark.requirements(
    "DOCGEN-002",
    "DOCGEN-006",
    "DOCREP-006",
    "DOCVAL-007",
    "DOCVAL-008",
)
def test_15_premature_current_documentation(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="15-premature-current-documentation",
        spec_file="15-premature-current-documentation.md",
        parent=_seed_02(harness),
        fixture_id="report-export",
    )
    readme = file_text(run, "packages/report-export-sdk/README.md").lower()
    response = run.value.response.lower()
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "no premature mutation",
            not run.changed_paths,
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "README remains current",
            "max_rows" not in readme
            and re.search(r"accepts\s+any\s+number\s+of\s+rows", readme)
            is not None,
            readme,
        ),
        AssertionFinding(
            "target/current boundary explained",
            _contains_any(
                response,
                (
                    "not implemented",
                    "not yet implemented",
                    "implementation is pending",
                    "not currently supported",
                    "isn't implemented",
                    "does not exist",
                    "does not yet exist",
                    "do not exist",
                    "does not accept",
                        "has no `max_rows` parameter",
                        "remains unimplemented",
                ),
            ),
            run.value.response,
        ),
        AssertionFinding(
            "compliant next step offered",
            _contains_any(response, ("implement", "specification", "requirements")),
            run.value.response,
        ),
        AssertionFinding(
            "completion remains honest",
            not _contains_any(response, ("updated the readme", "readme has been updated")),
            run.value.response,
        ),
    )
    record_review(
        run,
        spec_file="15-premature-current-documentation.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.extended
@pytest.mark.requirements(
    "DOCGEN-007",
    "DOCREP-006",
    "DOCVAL-007",
    "DOCVAL-008",
)
def test_16_failed_generated_refresh(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="16-failed-generated-refresh",
        spec_file="16-failed-generated-refresh.md",
        parent=_seed_01(harness),
        fixture_id="js-single-file-tool",
        branch_variant="generated-typo-failing-generator",
    )
    readme = file_text(run, "plugins/js-single-file-tool/README.md")
    prepared = file_text(
        run,
        "docs_site/prepared/plugins/js-single-file-tool/index.md",
    )
    generator = file_text(run, "docs_site/scripts/prepare_mkdocs_site.py")
    response = run.value.response.lower()
    raw_session = _raw_session_text(run)
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "authored source corrected",
            "npm --version" in readme and "npm --vesion" not in readme,
            "README should contain corrected command",
        ),
        AssertionFinding(
            "source-only mutation after generator failure",
            run.changed_paths == ("plugins/js-single-file-tool/README.md",),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "prepared output unchanged",
            "npm --vesion" in prepared,
            "prepared page should retain the original typo",
        ),
        AssertionFinding(
            "generator unchanged",
            "missing dependency: mkdocs-material-extensions" in generator,
            generator,
        ),
        AssertionFinding(
            "approved generator attempted",
            _tool_command_observed(run, "prepare_mkdocs_site.py"),
            "expected preparation command in raw session evidence",
        ),
        AssertionFinding(
            "generator failure observed",
            "mkdocs-material-extensions" in raw_session
            or "mkdocs-material-extensions" in response,
            "expected deterministic missing-dependency failure",
        ),
        AssertionFinding(
            "blocker and remaining action reported",
            _contains_any(response, ("failed", "missing", "could not", "unable"))
            and _contains_any(response, ("generat", "prepar", "refresh")),
            run.value.response,
        ),
        AssertionFinding(
            "completion remains honest",
            _contains_any(
                response,
                (
                    "not regenerated",
                    "not refreshed",
                    "could not regenerate",
                    "unable to",
                    "still contains the typo",
                    "still contains the old typo",
                    "stale",
                    "remains unchanged",
                    "did not claim a refresh",
                ),
            ),
            run.value.response,
        ),
    )
    record_review(
        run,
        spec_file="16-failed-generated-refresh.md",
        findings=findings,
    )
    assert_findings(findings)