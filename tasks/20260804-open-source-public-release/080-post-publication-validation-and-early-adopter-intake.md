# Validate The Public Release And Establish Early-Adopter Intake

Confirm that the newly public repository works for anonymous users and create a
lightweight feedback loop for the first known developers and early adopters.

## Requirements checklist

- [ ] An anonymous user can view and clone the repository and open the public Issues page.
- [ ] A clean anonymous clone follows the documented setup and passes the minimum supported validation.
- [ ] Public workflows run without leaking secrets or triggering unintended deployments.
- [ ] License, support, privacy, security, documentation, and landing-page repository links resolve.
- [ ] Initial GitHub security alerts are triaged for urgent blockers.
- [ ] Early adopters have a simple issue-label and feedback process without requiring a heavyweight governance system.
- [ ] Unexpected cost, abuse, support, or security behavior is monitored during the initial release window.

Parent Task: tasks/20260804-open-source-public-release/000-main.md
Depends On: tasks/20260804-open-source-public-release/070-github-visibility-and-security-settings.md

## Execution plan
Status: Draft

Use a logged-out browser and a clean unauthenticated clone to verify the public
experience. Open a disposable test issue if needed, validate issue forms, and
close it clearly as a release test.

Invite the initial known developers only after validation. Use a small label set
such as `bug`, `enhancement`, `documentation`, `question`, `good first issue`,
and `early-adopter`. Do not create a large roadmap or governance structure
before feedback exists.

Monitor Actions usage, deployment attempts, provider/API failures, GitHub
security alerts, and support email during the first days. Escalate anything that
indicates active credential exposure, abuse, runaway cost, or a major setup
blocker.

### Implementation decisions and open questions

- The public repository may remain explicitly early access.
- Initial feedback should shape tasks `110` through `140`.
- No broad announcement is required during the friends-and-known-developers
  stage.

### Documentation

- Capture durable recurring feedback in issues or the relevant later task.
- Avoid copying private support correspondence into public issues without
  consent.

### Task checklist

- [ ] Verify logged-out repository and Issues access.
- [ ] Clone and validate from a clean environment.
- [ ] Validate issue forms and private security reporting.
- [ ] Verify public workflows and protected deployments.
- [ ] Triage initial security/dependency alerts.
- [ ] Establish minimal labels and invite early adopters.
- [ ] Review cost/security/support signals after the initial release window.

### Requirement verification

- Anonymous/public checks pass and are recorded.
- No critical security, cost, or usability incident remains unresolved.
- Early-adopter feedback has a clear intake path.
