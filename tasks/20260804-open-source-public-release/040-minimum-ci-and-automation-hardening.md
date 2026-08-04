# Add Minimum Public CI And Harden Automation

Ensure untrusted public contributions are validated without receiving deployment
credentials, broad write permissions, or an easy path to unexpected cloud cost.

## Requirements checklist

- [ ] Pull requests run a bounded, credential-free validation workflow covering the primary supported code paths.
- [ ] Pull-request workflows use read-only permissions and do not expose repository, AWS, provider, signing, or deployment secrets.
- [ ] Existing deployment and release workflows grant write/OIDC permissions only to jobs and steps that require them.
- [ ] Third-party Actions use an approved immutable reference strategy.
- [ ] CI concurrency and scope controls prevent obviously wasteful duplicate execution.
- [ ] Public contributors cannot cause production deployment or package publication by opening or modifying a pull request.

Parent Task: tasks/20260804-open-source-public-release/000-main.md
Depends On: tasks/20260804-open-source-public-release/010-sensitive-data-and-history-release-gate.md

## Known starting state

- No general pull-request CI workflow was found.
- Repository Actions currently default to write permission.
- Actions are allowed to approve pull requests.
- All actions are allowed and SHA pinning is not required.
- Static-site deployment uses AWS OIDC.
- CLI release automation has workflow-level `contents: write` and
  `id-token: write`.

## Lean pre-publication scope

The initial required CI should prioritize:

- Core Python unit tests.
- Application Python unit tests.
- Fast shared frontend package tests or type checks that are stable.
- Landing/docs build validation when those files change.
- Cheap static validation such as `git diff --check` or manifest parsing.

Broad provider integration, hosted API, Docker/cloud, mobile native UI, and
multi-platform release matrices remain outside pull-request CI unless already
cheap and deterministic.

## Execution plan
Status: Draft

Add a pull-request workflow with top-level read-only permissions, no secret
references, cancellation of superseded runs, and path-aware jobs where that
does not make required checks unreliable.

Narrow existing release/deploy workflow permissions to the smallest job scope.
Ensure publication triggers cannot run from pull-request code. Pin external
actions to reviewed full commit SHAs or enforce an equivalently immutable
approved-action policy.

Prepare the exact repository settings changes for task `070`: default workflow
permission read-only, Actions PR approval disabled, and external-contributor
workflow approval enabled.

### Implementation decisions and open questions

- Keep the initial required-check set small enough to be reliable and affordable.
- Do not introduce self-hosted runners for untrusted pull requests.
- Hosted-provider tests remain explicitly opt-in.

### Documentation

- Document required checks and how contributors reproduce them locally.
- Record why deployment/release workflows have any remaining write permissions.

### Task checklist

- [ ] Define stable minimum required checks.
- [ ] Add credential-free pull-request CI.
- [ ] Narrow deploy/release workflow permissions.
- [ ] Pin or constrain third-party actions.
- [ ] Add concurrency/cost controls.
- [ ] Validate workflows from a branch without secrets.

### Requirement verification

- A pull request from a fork can run required validation without secrets.
- Workflow permission inspection shows read-only PR jobs and narrowly scoped
  publication permissions.
- A PR cannot trigger AWS deployment, CLI release, or future TestFlight upload.
