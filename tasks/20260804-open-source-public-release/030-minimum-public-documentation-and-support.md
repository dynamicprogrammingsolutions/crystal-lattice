# Add Minimum Public Documentation And Support Paths

Provide only the documentation and issue intake needed for early adopters to
understand, use, support, and safely report problems with the repository.

## Requirements checklist

- [ ] The root README clearly states project status, supported primary workflows, installation entrypoints, license, and where to ask for help.
- [ ] Contributors have concise setup, test, contribution-license, and pull-request guidance.
- [ ] Security researchers have a private reporting path and are told not to open public vulnerability issues.
- [ ] Users have a support path that distinguishes usage questions, bugs, feature requests, and security issues.
- [ ] GitHub issue forms collect actionable bug and feature information and redirect security reports.
- [ ] Documentation does not promise support levels, compatibility, hosted services, or release stability that the project does not yet provide.

Parent Task: tasks/20260804-open-source-public-release/000-main.md
Depends On: tasks/20260804-open-source-public-release/020-claude-tools-license-and-provenance-restoration.md

## Lean pre-publication scope

Create or update:

- `CONTRIBUTING.md`
- `SECURITY.md`
- `SUPPORT.md`
- `.github/ISSUE_TEMPLATE/bug.yml`
- `.github/ISSUE_TEMPLATE/feature.yml`
- `.github/ISSUE_TEMPLATE/config.yml`
- A concise pull-request template if it materially improves test/review quality
- Root README links and early-access status

Defer a full code of conduct, governance model, maintainer ladder, Discussions,
and automated DCO/CLA policy to task `110`.

## Execution plan
Status: Draft

Write concise documents oriented to a first-time external developer. Reuse the
existing architecture and development documentation by linking rather than
duplicating it. State that contributions are submitted under the license that
applies to the changed directory, consistent with `LICENSING.md`.

Use `support@dynamicprogrammingsolutions.com` for private security and support
contact until GitHub private vulnerability reporting is enabled in task `070`.
Configure issue forms so security reports cannot be mistaken for normal bugs.

Make the README explicit that the repository is early-stage and that public APIs,
plugin contracts, and deployment processes may evolve with early-adopter
feedback.

### Implementation decisions and open questions

- No CLA is required for the initial release.
- No automated DCO enforcement is required before publication.
- A full code of conduct is deferred, but contribution guidance should require
  respectful and constructive participation.

### Documentation

- All output of this task is documentation or GitHub issue/PR metadata.
- Avoid adding a large documentation navigation overhaul.

### Task checklist

- [ ] Audit root README from an anonymous newcomer perspective.
- [ ] Add concise contribution guidance.
- [ ] Add private security-reporting guidance.
- [ ] Add support routing.
- [ ] Add issue forms and optional PR template.
- [ ] Validate links and rendered YAML.

### Requirement verification

- A clean-clone reviewer can identify setup, tests, license, support, security,
  and issue paths in under five minutes.
- Issue forms render successfully and security intake points away from public
  issues.
- Documentation links resolve within the repository or to the production site.
