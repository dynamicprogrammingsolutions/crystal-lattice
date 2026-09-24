from __future__ import annotations

import json
import re
import shutil
from collections.abc import Iterator
from pathlib import Path

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
    require_run_value,
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


def _message_metadata(message: dict[str, object]) -> dict[str, object]:
    for key in ("metadata", "_metadata"):
        value = message.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _message_tool_calls(message: dict[str, object]) -> list[dict[str, object]]:
    value = message.get("tool_calls")
    if not isinstance(value, list):
        value = _message_metadata(message).get("tool_calls")
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _tool_call_details(
    call: dict[str, object],
) -> tuple[str, dict[str, object]]:
    function = call.get("function")
    function_value = function if isinstance(function, dict) else call
    name = str(function_value.get("name", "")).lower()
    raw_arguments = function_value.get("arguments")
    if isinstance(raw_arguments, dict):
        return name, raw_arguments
    if isinstance(raw_arguments, str):
        try:
            parsed = json.loads(raw_arguments)
        except json.JSONDecodeError:
            return name, {"raw": raw_arguments}
        if isinstance(parsed, dict):
            return name, parsed
    return name, {}


def _tool_command_text(arguments: dict[str, object]) -> str:
    value = arguments.get("command") or arguments.get("cmd")
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return ""


def _tool_command_observed(run, needle: str) -> bool:
    needle = needle.lower()
    data = _raw_session(run)
    messages = data.get("messages")
    if isinstance(messages, list):
        for message in messages:
            if not isinstance(message, dict):
                continue
            for call in _message_tool_calls(message):
                name, arguments = _tool_call_details(call)
                if name in {"bash", "shell"} and needle in _tool_command_text(
                    arguments
                ).lower():
                    return True
            if message.get("role") != "tool":
                continue
            metadata = _message_metadata(message)
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

    return has_command(data)


def _raw_session_text(run) -> str:
    return json.dumps(_raw_session(run)).lower()


def _has_case_transform_example(text: str) -> bool:
    for match in re.finditer(r"""["']([a-z][a-z0-9 _-]{1,30})["']""", text):
        value = match.group(1)
        if value.upper() in text:
            return True
    return False


def _external_worktree_roots(run) -> tuple[str, ...]:
    if run.workspace is None:
        return ()
    workspace = str(Path(run.workspace).resolve())
    roots = set(
        re.findall(
            r"/Users/[^/]+/Dev/Mine/ai-agent-platform-worktrees/[^/\\\" ]+",
            json.dumps(_raw_session(run)),
        )
    )
    return tuple(sorted(root for root in roots if not workspace.startswith(f"{root}/")))


def _raw_evidence(run) -> list[dict[str, object]]:
    path = run.artifact_dir / "raw/evidence.json"
    if not path.is_file():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _evidence_value(run, kind: str) -> object | None:
    for item in reversed(_raw_evidence(run)):
        if item.get("kind") == kind:
            return item.get("value")
    return None


def _tool_messages(run) -> list[dict[str, object]]:
    messages = _raw_session(run).get("messages")
    if not isinstance(messages, list):
        return []
    return [
        message
        for message in messages
        if isinstance(message, dict) and message.get("role") == "tool"
    ]


def _first_mutation_tool_index(run) -> int | None:
    mutation_shell_markers = (
        "apply_patch",
        "sed -i",
        "tee ",
        "cat >",
        "cat <<",
        "write_text(",
        "touch ",
        "mkdir ",
        "mv ",
        "cp ",
        "rm ",
    )
    messages = _raw_session(run).get("messages")
    if not isinstance(messages, list):
        return None
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            continue
        for call in _message_tool_calls(message):
            name, arguments = _tool_call_details(call)
            if name in {
                "apply_patch",
                "edit",
                "write",
                "write_file",
            }:
                return index
            if name in {"bash", "shell"}:
                command = _tool_command_text(arguments).lower()
                if any(marker in command for marker in mutation_shell_markers):
                    return index
        if message.get("role") != "tool":
            continue
        metadata_value = _message_metadata(message)
        tool_name = str(metadata_value.get("tool_name", "")).lower()
        if tool_name in {
            "apply_patch",
            "edit",
            "write",
            "write_file",
        }:
            return index
        if tool_name not in {"bash", "shell"}:
            continue
        display = metadata_value.get("display")
        display_value = display if isinstance(display, dict) else {}
        command = str(display_value.get("content", "")).lower()
        if any(marker in command for marker in mutation_shell_markers):
            return index
    return None


def _complete_read_positions(
    run,
    relative_paths: tuple[str, ...],
) -> dict[str, int | None]:
    if run.workspace is None:
        raise AssertionError("run has no workspace")
    raw_messages = _raw_session(run).get("messages")
    messages = raw_messages if isinstance(raw_messages, list) else []
    positions: dict[str, int | None] = {}
    for relative in relative_paths:
        target = run.workspace / relative
        if not target.is_file():
            positions[relative] = None
            continue
        expected = target.read_text(encoding="utf-8").strip()
        line_count = len(target.read_text(encoding="utf-8").splitlines())
        shell_ranges: list[tuple[int, int]] = []
        position = None
        for index, message in enumerate(messages):
            if not isinstance(message, dict):
                continue
            for call in _message_tool_calls(message):
                name, arguments = _tool_call_details(call)
                if name in {"read", "read_file"}:
                    raw_path = arguments.get("file_path") or arguments.get("path")
                    if not isinstance(raw_path, str):
                        continue
                    read_path = Path(raw_path)
                    normalized_path = raw_path.replace("\\", "/")
                    same_path = (
                        read_path.resolve() == target.resolve()
                        or normalized_path.endswith(relative)
                    )
                    partial = any(
                        arguments.get(key) not in {None, 0}
                        for key in ("limit", "offset")
                    )
                    if same_path and not partial:
                        position = index
                        break
                    continue
                if name not in {"bash", "shell"}:
                    continue
                command = _tool_command_text(arguments).replace("\\", "/")
                if relative not in command:
                    continue
                if re.search(
                    rf"(?:^|[;&|]\s*)cat\s+['\"]?{re.escape(relative)}"
                    rf"['\"]?(?:\s|$)",
                    command,
                ):
                    position = index
                    break
                for match in re.finditer(
                    rf"sed\s+-n\s+['\"]?(\d+),(\d+)p['\"]?\s+"
                    rf"['\"]?{re.escape(relative)}['\"]?",
                    command,
                ):
                    shell_ranges.append(
                        (int(match.group(1)), int(match.group(2)))
                    )
                covered = 0
                for start, end in sorted(shell_ranges):
                    if start > covered + 1:
                        break
                    covered = max(covered, end)
                if line_count and covered >= line_count:
                    position = index
                    break
            if position is not None:
                break
            if message.get("role") != "tool":
                continue
            metadata_value = _message_metadata(message)
            tool_name = str(metadata_value.get("tool_name", "")).lower()
            if tool_name not in {"bash", "read", "read_file", "shell"}:
                continue
            if expected and expected in str(message.get("content", "")):
                position = index
                break
        positions[relative] = position
    return positions


def _placement_communication_is_proportionate(response: str) -> bool:
    lower = response.lower()
    if _contains_any(
        lower,
        (
            "honest owner",
            "honest normative owner",
            "documentation owner",
        ),
    ):
        return False
    return not any(
        re.search(pattern, lower)
        for pattern in (
            r"(?:which|what) package .*\\?",
            r"where should .*\\?",
            r"confirm (?:the )?(?:owner|placement|location)",
            r"please confirm .*?(?:owner|placement|location)",
        )
    )


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
@pytest.mark.obsolete
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
    response = require_run_value(run).response.lower()
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
                (
                    "unavailable",
                    "not available",
                    "missing",
                    "cannot",
                    "could not",
                    "blocked",
                    "no such file",
                    "does not contain",
                    "not present",
                ),
            )
            and _contains_any(response, ("generat", "prepar", "refresh")),
            "expected unavailable generation and remaining refresh action",
        ),
        AssertionFinding(
            "completion remains honest",
            (
                "unchanged" in response
                and _contains_any(response, ("prepared", "generated"))
            )
            or _contains_any(
                response,
                (
                    "not regenerated",
                    "not refreshed",
                    "could not regenerate",
                    "unable to",
                ),
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
    assert _tool_command_observed(run, "pytest")
    assert "passed" in _raw_session_text(run)
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
    response = require_run_value(run).response
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
        AssertionFinding(
            "placement communication is proportionate",
            _placement_communication_is_proportionate(response),
            response,
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
    publishing = file_text(run, "packages/event-sdk/docs/publishing.md").lower()
    current_docs = "\n".join(
        file_text(run, path)
        for path in matching_paths(run, "packages/event-sdk/docs")
        if "/development/" not in path
    ).lower()
    consumer_text = f"{readme}\n{current_docs}"
    paths = set(run.changed_paths)
    response = require_run_value(run).response
    requirements = file_text(
        run,
        "packages/event-sdk/docs/development/specifications/"
        "event-lifecycle/requirements.md",
    ).lower()
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "package discovery improved",
            (
                re.search(r"\bretr(?:y|ies|ied|ying)\b", readme) is not None
                and "retry" in index
            )
            or (
                ("docs/index.md" in readme or "user documentation" in readme)
                and "publishing.md" in index
                and "retr" in publishing
            ),
            "expected a direct retry route or README → docs index → publishing",
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
            "authoritative target not rewritten",
            not any("event-lifecycle/technical-spec.md" in path for path in paths)
            and "event-002" in requirements
            and "not started" in requirements
            and "pending" in requirements,
            f"paths={run.changed_paths!r}\nrequirements={requirements}",
        ),
        AssertionFinding(
            "implementation unchanged",
            not any(path.startswith("packages/event-sdk/src/") for path in paths),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "placement communication is proportionate",
            _placement_communication_is_proportionate(response),
            response,
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
            all(term in response for term in ("owner", "scope"))
            and _contains_any(
                response,
                (
                    "file",
                    "document",
                    "specification",
                    "requirements",
                ),
            ),
            "expected owner, scope, and proposed specification files",
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
    response = require_run_value(run).response.lower()
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
            "placement communication is proportionate",
            _placement_communication_is_proportionate(run.value.response),
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
@pytest.mark.obsolete
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
    response = require_run_value(run).response.lower()
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
    response = require_run_value(run).response.lower()
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
                    "left the generated output unchanged",
                    "left generated output unchanged",
                    "left the prepared output unchanged",
                    "prepared output remains unchanged",
                    "left the generated file unchanged",
                    "did not claim a refresh",
                    "still contains",
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


@pytest.mark.routine
@pytest.mark.obsolete
@pytest.mark.requirements(
    "DOCREP-001",
    "DOCREP-003",
    "DOCREP-004",
    "DOCREP-005",
)
def test_17_public_package_profile(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="17-public-package-profile",
        spec_file="17-public-package-profile.md",
        parent=_seed_04(harness),
        fixture_id="event-retry",
    )
    paths = set(run.changed_paths)
    readme = file_text(run, "packages/event-sdk/README.md").lower()
    docs_index = file_text(run, "packages/event-sdk/docs/index.md").lower()
    quickstart = file_text(run, "packages/event-sdk/docs/quickstart.md").lower()
    development = file_text(
        run,
        "packages/event-sdk/docs/development/index.md",
    ).lower()
    implementation_path = "packages/event-sdk/docs/development/implementation.md"
    implementation = (
        file_text(run, implementation_path).lower()
        if file_exists(run, implementation_path)
        else ""
    )
    agents_path = "packages/event-sdk/AGENTS.md"
    agents = file_text(run, agents_path).lower() if file_exists(run, agents_path) else ""
    public_text = "\n".join((readme, docs_index, quickstart))
    allowed_prefix = "packages/event-sdk/"
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "package-local documentation only",
            bool(paths)
            and all(path.startswith(allowed_prefix) for path in paths)
            and not any(
                path.startswith(
                    (
                        "packages/event-sdk/src/",
                        "packages/event-sdk/tests/",
                    )
                )
                for path in paths
            ),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "quickstart created",
            file_exists(run, "packages/event-sdk/docs/quickstart.md")
            and "publish" in quickstart
            and "created" in quickstart
            and ("published" in quickstart or "status" in quickstart),
            quickstart,
        ),
        AssertionFinding(
            "user entry points route to quickstart",
            "quickstart" in docs_index
            and (
                _contains_any(readme, ("quickstart", "quick start"))
                or (
                    ("docs/index.md" in readme or "documentation" in readme)
                    and "quickstart.md" in docs_index
                )
                or (
                    "first use" in readme
                    and "publish" in readme
                    and ("docs/index.md" in readme or "user documentation" in readme)
                )
            ),
            f"README:\n{readme}\n\nINDEX:\n{docs_index}",
        ),
        AssertionFinding(
            "optional package AGENTS is useful",
            not agents
            or all(
                term in agents
                for term in (
                    "src/events.py",
                    "tests/test_events.py",
                    "docs/index.md",
                    "docs/development/index.md",
                    "pytest",
                )
            ),
            agents or "inherited guidance retained",
        ),
        AssertionFinding(
            "development index routes implementation and target",
            (
                (
                    "src/events.py" in development
                    and "tests/test_events.py" in development
                )
                or (
                    "implementation.md" in development
                    and "src/events.py" in implementation
                    and "tests/test_events.py" in implementation
                )
            )
            and "event-lifecycle" in development,
            f"INDEX:\n{development}\n\nIMPLEMENTATION:\n{implementation}",
        ),
        AssertionFinding(
            "public pages remain current and audience-safe",
            "replay_failed" not in public_text
            and "maintainer/" not in public_text
            and "tasks/" not in public_text
            and "docrep-" not in public_text
            and "development/specifications" not in public_text,
            public_text,
        ),
        AssertionFinding(
            "no root or placeholder output",
            not any(
                path.startswith(
                    (
                        "docs/",
                        "maintainer/",
                        "tasks/",
                        "docs_site/",
                    )
                )
                or "/reference/" in path
                for path in paths
            ),
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="17-public-package-profile.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.routine
@pytest.mark.requirements("DOCREP-002")
def test_18_shared_plugin_authoring_boundary(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="18-shared-plugin-authoring-boundary",
        spec_file="18-shared-plugin-authoring-boundary.md",
        parent=_seed_01(harness),
        fixture_id="js-single-file-tool",
    )
    paths = set(run.changed_paths)
    readme_original = file_text(run, "plugins/js-single-file-tool/README.md")
    readme = readme_original.lower()
    canonical_path = "plugins/docs/node-tool-plugins.md"
    shared_paths = matching_paths(run, "plugins/docs")
    focused_paths = tuple(
        path
        for path in shared_paths
        if path
        not in {
            "plugins/docs/index.md",
            canonical_path,
            "plugins/docs/AGENTS.md",
            "plugins/docs/plugin-packaging-and-loading.md",
            "plugins/docs/testing-and-validation.md",
            "plugins/docs/tool-interop.md",
            "plugins/docs/tool-plugins.md",
        }
    )
    shared = "\n".join(
        file_text(run, path).lower()
        for path in (canonical_path, *focused_paths)
    )
    canonical = file_text(run, canonical_path).lower()
    shared_index = file_text(run, "plugins/docs/index.md").lower()
    response = require_run_value(run).response.lower()
    rendered = "\n".join((readme, shared))
    unsupported_loader_claims = (
        "plugin id defaults to the file stem",
        "id defaults to the file stem",
        "plugin_policy.base_dir",
        "node:./plugins/js-single-file-tool/uppertool.ts",
        "generated cached package",
        "tiny cached package",
        "esbuild in devdependencies",
        "esbuild` in `devdependencies",
    )
    external_roots = _external_worktree_roots(run)
    external_checkout_language = (
        "sibling worktree",
        "reference checkout",
        "editable checkout",
        "parent worktree",
    )
    node_unavailable_claim = bool(
        re.search(
            r"(?:node(?:\.js)?|node runtime|node executable).{0,80}"
            r"(?:not available|unavailable|isn't available|aren't available)",
            response,
            re.DOTALL,
        )
    )
    allowed_paths = {
        "plugins/js-single-file-tool/README.md",
        "plugins/docs/index.md",
        canonical_path,
        *focused_paths,
    }
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "package and shared owners both updated",
            "plugins/js-single-file-tool/README.md" in paths
            and (canonical_path in paths or bool(focused_paths)),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "plugin example is complete",
            "uppertool" in readme
            and _contains_any(readme, ("node:", "node_tool", '"file"'))
            and _has_case_transform_example(readme_original)
            and _contains_any(readme, ("verify", "expected", "confirm")),
            readme,
        ),
        AssertionFinding(
            "shared single-file workflow added",
            "single-file" in shared
            and _contains_any(shared, ("object export", "object-export", "export object"))
            and _contains_any(shared, ("node:", "node_tool", '"file"'))
            and _contains_any(shared, ("verify", "validation", "test")),
            shared,
        ),
        AssertionFinding(
            "plugin behavior not universalized",
            "all node tools uppercase" not in shared
            and "every node tool uppercase" not in shared
            and "must export uppertool" not in shared,
            shared,
        ),
        AssertionFinding(
            "claims remain supported by the bounded fixture",
            not any(term in rendered for term in unsupported_loader_claims),
            "\n".join(
                term for term in unsupported_loader_claims if term in rendered
            )
            or "no unsupported loader claim detected",
        ),
        AssertionFinding(
            "fixture boundary retained",
            not external_roots
            and not any(term in response for term in external_checkout_language),
            (
                f"external_roots={external_roots!r}; "
                f"response={run.value.response}"
            ),
        ),
        AssertionFinding(
            "environment limitations are accurate",
            not (shutil.which("node") is not None and node_unavailable_claim),
            run.value.response,
        ),
        AssertionFinding(
            "shared page remains indexed",
            "node-tool-plugins.md" in shared_index
            and all(path.rsplit("/", 1)[-1] in shared_index for path in focused_paths)
            and all(path.rsplit("/", 1)[-1] in canonical for path in focused_paths),
            f"INDEX:\n{shared_index}\n\nCANONICAL:\n{canonical}",
        ),
        AssertionFinding(
            "scope remains documentation-only",
            len(focused_paths) <= 1
            and paths <= allowed_paths,
            repr(run.changed_paths),
        ),
    )
    record_review(
        run,
        spec_file="18-shared-plugin-authoring-boundary.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.extended
@pytest.mark.requirements(
    "DOCREP-005",
    "DOCREP-006",
    "DOCVAL-007",
)
def test_19_apply_versus_maintain_boundary(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="19-apply-versus-maintain-boundary",
        spec_file="19-apply-versus-maintain-boundary.md",
        parent=_seed_04(harness),
        fixture_id="event-retry",
    )
    response = require_run_value(run).response.lower()
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "no internal provenance mutation",
            not run.changed_paths,
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "package audience boundary explained",
            _contains_any(
                response,
                (
                    "package user",
                    "sdk user",
                    "consumer documentation",
                    "consumer-facing",
                    "readme audience",
                    "user-facing sdk documentation",
                    "user-facing sdk readme",
                        "public package readme",
                        "public package readmes",
                        "package-user documentation",
                    "audience boundary",
                        "audience-boundary",
                ),
            ),
            run.value.response,
        ),
        AssertionFinding(
            "maintainer and evaluation material excluded",
            "maintainer" in response
            and _contains_any(
                response,
                (
                    "internal",
                    "non-public",
                    "not public",
                    "inappropriate",
                    "should not",
                    "must not",
                ),
            )
            and _contains_any(response, ("evaluation", "agent-behavior", "test")),
            run.value.response,
        ),
        AssertionFinding(
            "application and maintenance contexts distinguished",
            _contains_any(
                response,
                (
                    "package user",
                    "sdk user",
                    "consumer documentation",
                    "consumer-facing",
                    "public package readme",
                    "package-user documentation",
                    "user-facing sdk",
                ),
            )
            and _contains_any(
                response,
                (
                    "standards-maintenance",
                    "maintenance files",
                    "maintenance material",
                    "maintenance specifications",
                    "maintainer",
                    "development documentation",
                    "contributor",
                    "internal rationale",
                    "internal decision",
                ),
            ),
            run.value.response,
        ),
        AssertionFinding(
            "public alternative offered",
            _contains_any(
                response,
                (
                    "repository policy",
                    "contributor",
                    "development/repository",
                        "development documentation",
                        "development docs",
                        "development page",
                        "package development page",
                        "docs/development/",
                    "public guidance",
                        "readme-compatible alternative",
                ),
            ),
            run.value.response,
        ),
        AssertionFinding(
            "completion remains honest",
            not _contains_any(
                response,
                (
                    "updated the readme",
                    "readme has been updated",
                    "added the section",
                ),
            ),
            run.value.response,
        ),
    )
    record_review(
        run,
        spec_file="19-apply-versus-maintain-boundary.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.extended
@pytest.mark.obsolete
@pytest.mark.requirements("DOCREP-007", "DOCVAL-009")
def test_20_routed_guidance_reading(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="20-routed-guidance-reading",
        spec_file="20-routed-guidance-reading.md",
        parent=_seed_04(harness),
        fixture_id="event-retry",
        guidance_instruction_paths=("AGENTS.md",),
    )
    required_reads = (
        "docs/development/repository/index.md",
        "docs/development/standards/index.md",
        "docs/development/repository/documentation.md",
        "docs/development/standards/documentation.md",
    )
    positions = _complete_read_positions(run, required_reads)
    first_mutation = _first_mutation_tool_index(run)
    injection = _evidence_value(
        run,
        "documentation_standard.guidance_injection",
    )
    injection_value = injection if isinstance(injection, dict) else {}
    tool_output_parts: list[str] = []
    for message in _tool_messages(run):
        metadata = message.get("metadata")
        if not isinstance(metadata, dict):
            continue
        display = metadata.get("display")
        if isinstance(display, dict):
            tool_output_parts.append(str(display.get("content", "")))
    tool_output = "\n".join(tool_output_parts).lower()
    paths = set(run.changed_paths)
    quickstart = (
        file_text(run, "packages/event-sdk/docs/quickstart.md").lower()
        if file_exists(run, "packages/event-sdk/docs/quickstart.md")
        else ""
    )
    public_text = "\n".join(
        file_text(run, path).lower()
        for path in matching_paths(run, "packages/event-sdk/docs")
        if "/development/" not in path
    )
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "routing-only guidance injected",
            injection_value.get("paths") == ["AGENTS.md"],
            repr(injection_value),
        ),
        AssertionFinding(
            "routed pages read completely",
            all(position is not None for position in positions.values()),
            repr(positions),
        ),
        AssertionFinding(
            "routed pages read before mutation",
            first_mutation is not None
            and all(
                position is not None and position < first_mutation
                for position in positions.values()
            ),
            f"reads={positions!r}, first_mutation={first_mutation!r}",
        ),
        AssertionFinding(
            "maintainer-only routing not followed",
            "# documentation and specification standard" not in tool_output
            and "# documentation and specification standard requirements"
            not in tool_output,
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
            "user and maintainer routes completed",
            (
                bool(quickstart)
                or (
                    "first use"
                    in file_text(run, "packages/event-sdk/README.md").lower()
                    and "publish"
                    in file_text(run, "packages/event-sdk/README.md").lower()
                )
                or (
                    "get started"
                    in file_text(run, "packages/event-sdk/docs/index.md").lower()
                    and "publish"
                    in file_text(run, "packages/event-sdk/docs/index.md").lower()
                )
            )
            and file_exists(run, "packages/event-sdk/docs/development/index.md"),
            (
                quickstart
                or file_text(run, "packages/event-sdk/README.md")
                + "\n"
                + file_text(run, "packages/event-sdk/docs/index.md")
            ),
        ),
        AssertionFinding(
            "public pages remain current",
            "replay_failed" not in public_text
            and "phase " not in public_text
            and "development/specifications" not in public_text,
            public_text,
        ),
    )
    record_review(
        run,
        spec_file="20-routed-guidance-reading.md",
        findings=findings,
    )
    assert_findings(findings)


@pytest.mark.extended
@pytest.mark.obsolete
@pytest.mark.requirements(
    "DOCGEN-008",
    "DOCGEN-009",
    "DOCGEN-010",
    "DOCVAL-009",
)
def test_21_explicit_specification_layout_override(
    harness: DocumentationEvaluationHarness,
) -> None:
    run = harness.branch(
        test_id="21-explicit-specification-layout-override",
        spec_file="21-explicit-specification-layout-override.md",
        parent=_seed_05(harness),
        fixture_id="batch-sync",
        branch_variant="approved-task-single-decisions",
    )
    paths = set(run.changed_paths)
    specs = matching_paths(
        run,
        "packages/batch-sdk/docs/development/specifications",
    )
    decision_files = tuple(path for path in specs if path.endswith("/decisions.md"))
    decision_directories = tuple(path for path in specs if "/decisions/" in path)
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
            "single decisions file honored",
            len(decision_files) == 1 and not decision_directories,
            f"files={decision_files!r}, directory_files={decision_directories!r}",
        ),
        AssertionFinding(
            "decision file indexed",
            "decisions.md" in indexes,
            indexes,
        ),
        AssertionFinding(
            "required specification content retained",
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
            "concrete specification terminology",
            not re.search(
                r"(?mi)^#+\s+(?:specification\s+)?artifacts?\s*:?\s*$",
                rendered,
            )
            and not any(
                phrase in rendered
                for phrase in (
                    "artifact role",
                    "artifact set",
                    "artifact tree",
                    "documentation artifact",
                    "output artifact",
                    "specification artifact",
                    "work-tracking artifact",
                )
            ),
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
            "no duplicate approval or ownership jargon",
            _placement_communication_is_proportionate(response)
            and "please approve" not in response.lower()
            and "need your approval" not in response.lower()
            and "mandatory directory" not in response.lower(),
            response,
        ),
    )
    record_review(
        run,
        spec_file="21-explicit-specification-layout-override.md",
        findings=findings,
    )
    assert_findings(findings)