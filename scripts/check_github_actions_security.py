#!/usr/bin/env python3
"""Validate the repository's GitHub Actions trust and permission boundaries."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
PUBLIC_CI = WORKFLOWS_DIR / "public-ci.yml"
STATIC_SITE_DEPLOY = WORKFLOWS_DIR / "deploy-static-sites.yml"
STATIC_SITE_OIDC_ROLE = (
    REPO_ROOT / "deploy" / "aws-static-sites" / "github-oidc-role.yaml"
)

EXTERNAL_ACTION_RE = re.compile(r"^\s*uses:\s*([^#\s]+)")
FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
JOB_RE = re.compile(r"^  ([A-Za-z0-9_-]+):\s*$")
WRITE_PERMISSION_RE = re.compile(r"^\s+([A-Za-z0-9_-]+):\s*write\s*(?:#.*)?$")
ENVIRONMENT_RE = re.compile(r"^\s+environment:\s*(?:#.*)?$")
PRIVILEGED_TRIGGER_RE = re.compile(
    r"^  (pull_request_target|workflow_run):\s*(?:\{\})?\s*(?:#.*)?$"
)

ALLOWED_WRITE_PERMISSIONS = {
    ("deploy-static-sites.yml", "deploy", "id-token"),
    ("release-crystal-lattice-cli.yml", "publish", "contents"),
    ("release-crystal-lattice-cli.yml", "publish-downloads", "id-token"),
}

ALLOWED_ENVIRONMENTS = {
    ("deploy-static-sites.yml", "deploy"),
    ("release-crystal-lattice-cli.yml", "publish"),
    ("release-crystal-lattice-cli.yml", "publish-downloads"),
}

PUBLIC_CI_REQUIRED_JOBS = {
    "Repository checks",
    "Python unit tests",
    "Frontend package tests",
    "Landing and docs build",
}

PUBLIC_CI_FORBIDDEN_FRAGMENTS = (
    "secrets.",
    "vars.",
    "id-token: write",
    "environment:",
    "pull_request_target",
    "workflow_run",
    "aws-actions/",
    "softprops/",
    "ALLOW_AWS_DEPLOY",
    "fastlane",
    "testflight",
    "gh release",
    "aws s3",
    "cloudfront",
)


def active_workflows() -> list[Path]:
    return sorted(
        [
            *WORKFLOWS_DIR.glob("*.yml"),
            *WORKFLOWS_DIR.glob("*.yaml"),
        ]
    )


def line_job_map(lines: list[str]) -> list[str | None]:
    current_job: str | None = None
    in_jobs = False
    jobs: list[str | None] = []

    for line in lines:
        if line == "jobs:":
            in_jobs = True
            current_job = None
            jobs.append(None)
            continue

        if in_jobs:
            match = JOB_RE.match(line)
            if match:
                current_job = match.group(1)

        jobs.append(current_job if in_jobs else None)

    return jobs


def validate_action_pins(path: Path, lines: list[str], errors: list[str]) -> None:
    for line_number, line in enumerate(lines, start=1):
        match = EXTERNAL_ACTION_RE.match(line)
        if not match:
            continue

        reference = match.group(1)
        if reference.startswith("./"):
            continue
        if "@" not in reference:
            errors.append(
                f"{path}:{line_number}: action reference has no ref: {reference}"
            )
            continue

        _, ref = reference.rsplit("@", 1)
        if not FULL_SHA_RE.fullmatch(ref):
            errors.append(
                f"{path}:{line_number}: external action must use a full commit SHA: "
                f"{reference}"
            )


def validate_permissions_and_environments(
    path: Path, lines: list[str], errors: list[str]
) -> None:
    jobs = line_job_map(lines)
    for index, line in enumerate(lines):
        line_number = index + 1
        job = jobs[index]

        permission = WRITE_PERMISSION_RE.match(line)
        if permission:
            key = (path.name, job, permission.group(1))
            if key not in ALLOWED_WRITE_PERMISSIONS:
                errors.append(
                    f"{path}:{line_number}: unauthorized write permission "
                    f"{permission.group(1)!r} in job {job!r}"
                )

        if ENVIRONMENT_RE.match(line):
            key = (path.name, job)
            if key not in ALLOWED_ENVIRONMENTS:
                errors.append(
                    f"{path}:{line_number}: unauthorized environment in job {job!r}"
                )


def validate_publication_triggers(
    path: Path, lines: list[str], errors: list[str]
) -> None:
    if path.name not in {
        "deploy-static-sites.yml",
        "release-crystal-lattice-cli.yml",
    }:
        return

    for line_number, line in enumerate(lines, start=1):
        if line == "jobs:":
            break
        if PRIVILEGED_TRIGGER_RE.match(line) or re.match(
            r"^  pull_request:\s*(?:\{\})?\s*(?:#.*)?$", line
        ):
            errors.append(
                f"{path}:{line_number}: publication workflow has a PR-capable trigger"
            )


def validate_public_ci(errors: list[str]) -> None:
    if not PUBLIC_CI.is_file():
        errors.append(f"{PUBLIC_CI}: required workflow is missing")
        return

    text = PUBLIC_CI.read_text(encoding="utf-8")
    lowered = text.lower()
    for fragment in PUBLIC_CI_FORBIDDEN_FRAGMENTS:
        if fragment.lower() in lowered:
            errors.append(f"{PUBLIC_CI}: forbidden privileged fragment: {fragment}")

    if "permissions:\n  contents: read\n" not in text:
        errors.append(f"{PUBLIC_CI}: top-level contents: read permission is missing")
    if "\n  pull_request:\n" not in text:
        errors.append(f"{PUBLIC_CI}: pull_request trigger is missing")

    job_names = set(re.findall(r"^    name:\s*(.+?)\s*$", text, flags=re.MULTILINE))
    missing = sorted(PUBLIC_CI_REQUIRED_JOBS - job_names)
    if missing:
        errors.append(f"{PUBLIC_CI}: missing required job names: {', '.join(missing)}")


def validate_static_site_deploy(errors: list[str]) -> None:
    if not STATIC_SITE_DEPLOY.is_file():
        errors.append(f"{STATIC_SITE_DEPLOY}: required workflow is missing")
        return

    text = STATIC_SITE_DEPLOY.read_text(encoding="utf-8")
    for fragment in ("actions/upload-artifact@", "actions/download-artifact@"):
        if fragment in text:
            errors.append(
                f"{STATIC_SITE_DEPLOY}: static-site deployment must not use "
                f"artifact transfer: {fragment}"
            )

    if re.search(r"^    AWS_ROLE_TO_ASSUME:", text, flags=re.MULTILINE):
        errors.append(f"{STATIC_SITE_DEPLOY}: AWS role secret must not be job-scoped")
    if "role-to-assume: ${{ secrets.AWS_ROLE_TO_ASSUME }}" not in text:
        errors.append(
            f"{STATIC_SITE_DEPLOY}: AWS role must be passed directly to the "
            "credentials step"
        )
    if "environment: production-sites" not in text:
        errors.append(
            f"{STATIC_SITE_DEPLOY}: deployment job must use environment "
            "'production-sites'"
        )

    required_steps = [
        "- name: Build Landing Site",
        "- name: Build Docs Site",
        "- name: Configure AWS Credentials",
        "- name: Deploy Landing Site",
        "- name: Deploy Docs Site",
    ]
    positions = []
    for step in required_steps:
        position = text.find(step)
        if position < 0:
            errors.append(f"{STATIC_SITE_DEPLOY}: missing required step: {step}")
        positions.append(position)
    if all(position >= 0 for position in positions) and positions != sorted(positions):
        errors.append(
            f"{STATIC_SITE_DEPLOY}: sites must be built before AWS credentials "
            "are configured and deployment begins"
        )

    if not STATIC_SITE_OIDC_ROLE.is_file():
        errors.append(f"{STATIC_SITE_OIDC_ROLE}: required IAM template is missing")
        return

    oidc_text = STATIC_SITE_OIDC_ROLE.read_text(encoding="utf-8")
    environment_subject = (
        "token.actions.githubusercontent.com:sub: !Sub "
        '"repo:${GitHubOwner}/${GitHubRepo}:environment:${GitHubEnvironment}"'
    )
    if environment_subject not in oidc_text:
        errors.append(
            f"{STATIC_SITE_OIDC_ROLE}: IAM trust must match the "
            "production-sites environment subject"
        )
    if "ref:refs/heads/${GitHubBranch}" in oidc_text:
        errors.append(
            f"{STATIC_SITE_OIDC_ROLE}: branch OIDC subject is incompatible with "
            "the environment-bound deployment job"
        )


def validate() -> list[str]:
    errors: list[str] = []
    workflows = active_workflows()
    if not workflows:
        return [f"{WORKFLOWS_DIR}: no active workflows found"]

    for path in workflows:
        lines = path.read_text(encoding="utf-8").splitlines()
        validate_action_pins(path, lines, errors)
        validate_permissions_and_environments(path, lines, errors)
        validate_publication_triggers(path, lines, errors)

    validate_public_ci(errors)
    validate_static_site_deploy(errors)
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated {len(active_workflows())} active GitHub Actions workflows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
