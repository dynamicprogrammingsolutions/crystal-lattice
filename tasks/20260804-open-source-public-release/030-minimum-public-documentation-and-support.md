# Add Minimum Public Documentation And Support Paths

Provide only the documentation and issue intake needed for early adopters to
understand, use, support, and safely report problems with the repository.

## Requirements checklist

- [x] The root README clearly states project status, supported primary workflows, installation entrypoints, license, and where to ask for help.
- [x] Contributors have concise setup, test, contribution-license, and pull-request guidance.
- [x] Security researchers have a private reporting path and are told not to open public vulnerability issues.
- [x] Users have a support path that distinguishes usage questions, bugs, feature requests, and security issues.
- [x] GitHub issue forms collect actionable bug and feature information and redirect security reports.
- [x] Documentation does not promise support levels, compatibility, hosted services, or release stability that the project does not yet provide.

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

## Known findings

- The root README already provides substantial terminal/server installation,
  mobile setup, plugin development, core development, architecture,
  documentation, version, and licensing guidance.
- The README does not identify the repository as an early public release and
  has no direct support, security, issue-intake, or contribution entrypoint.
- Root `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, code-of-conduct, and
  governance files do not exist.
- `.github/` currently contains workflows only. There are no issue forms,
  issue-template configuration, or pull-request template.
- GitHub Issues are enabled, Discussions are disabled, and the repository is
  still private.
- The standard `bug`, `enhancement`, `documentation`, `question`, and related
  default labels already exist.
- GitHub's community profile currently recognizes the README and Apache-2.0
  license but reports no contribution guide, security policy, issue template,
  pull-request template, or code of conduct.
- The production landing site has live `/support` and `/privacy` routes.
- The current support page sends reproducible defects to the generic Issues
  page and tells security-sensitive reporters to use email, but it does not
  clearly separate bugs, feature requests, usage questions, and security
  reports.
- The landing support/privacy content already states that users operate their
  own runtime, bridge, or cloud environment and that Dynamic Programming
  Solutions Kft. does not operate a public production bridge or cloud-agent
  service.
- The root README and production site both link to
  `dynamicprogrammingsolutions/crystal-lattice`, which is the intended public
  repository.

## Execution plan
Status: Approved

### Phase 1: Add the public repository entrypoints

Update the root README without restructuring its existing technical content:

1. Add a concise early-development notice near the introduction:
   - the repository is in an early public-release stage;
   - releases and primary workflows are usable for evaluation and development;
   - APIs, configuration, plugin contracts, and deployment procedures may
     change based on early-adopter feedback;
   - users should not infer a long-term compatibility or support commitment.
2. Add a compact "Community and support" section linking to:
   - `CONTRIBUTING.md`;
   - `SUPPORT.md`;
   - `SECURITY.md`;
   - the GitHub issue chooser;
   - the production support page.
3. Keep the existing quickstart, development, architecture, status, and
   licensing sections as the primary workflow entrypoints.
4. State plainly that the optional bridge and cloud-orchestrator components are
   self-hosted and no public production bridge/cloud service is promised.

Do not turn the README into a governance document or duplicate package-specific
installation and test guides.

### Phase 2: Add concise contribution guidance

Create `CONTRIBUTING.md` for first-time external developers. Cover:

- choosing the narrowest package/subsystem and reading its README and public
  development documentation before editing;
- Python 3.10+ core/application setup;
- installing only the plugin packages being changed;
- frontend workspace installation and package-local test commands where
  applicable;
- using focused unit tests first and running integration/API/Docker tests only
  when the changed boundary requires them;
- updating tests and owning-package documentation for public behavior changes;
- keeping pull requests focused and explaining behavior, tests, risks, and
  deferred work;
- never committing credentials, private conversations, runtime session data,
  local machine paths, or generated caches;
- respectful, constructive participation while the full code of conduct remains
  deferred;
- inbound-equals-outbound contribution licensing: contributions are submitted
  under the license that applies to the changed file/subtree, consistent with
  `LICENSING.md`.

Do not require a CLA, DCO signoff, issue assignment, or prior maintainer
approval for ordinary pull requests in this initial guide.

### Phase 3: Establish private security reporting

Create `SECURITY.md` that:

- instructs reporters not to open public issues for suspected vulnerabilities;
- uses `support@dynamicprogrammingsolutions.com` with a clear subject prefix
  such as `SECURITY:`;
- asks for the affected component/version or commit, impact, reproduction
  details, and sanitized supporting evidence;
- tells reporters not to email live credentials or unnecessary personal/private
  data and to revoke exposed credentials first where applicable;
- explains that GitHub private vulnerability reporting will become another
  intake option once enabled in task `070`;
- makes no response-time, remediation-time, bounty, embargo, backport, or
  long-term version-support promise;
- says security work is prioritized against the current development line and
  latest release as practical, without defining a fixed support window.

### Phase 4: Route support requests by category

Create `SUPPORT.md` with four explicit routes:

- Usage, installation, mobile connection, and self-hosting questions:
  production `/support` page or support email.
- Reproducible non-sensitive bugs: GitHub bug form.
- Feature and enhancement proposals: GitHub feature form.
- Security vulnerabilities or reports containing sensitive/private data:
  private process in `SECURITY.md`, never a public issue.

Also state:

- no guaranteed response time or support SLA;
- no public production bridge or cloud-agent service;
- logs and screenshots must be sanitized;
- provider, Apple, Google, GitHub, hosting, and self-hosted operator support
  remain separate from Crystal Lattice project support.

### Phase 5: Add structured GitHub intake

Create:

- `.github/ISSUE_TEMPLATE/bug.yml`
- `.github/ISSUE_TEMPLATE/feature.yml`
- `.github/ISSUE_TEMPLATE/config.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`

The bug form will:

- begin with a visible security/private-data warning;
- apply the existing `bug` label;
- collect affected area, version/commit, installation method, operating
  system/device, reproduction steps, expected behavior, actual behavior, and
  sanitized logs or screenshots;
- require confirmation that no secret/private data is included and that the
  issue is not a security vulnerability.

The feature form will:

- apply the existing `enhancement` label;
- collect the problem/use case, proposed outcome, affected area, alternatives,
  and compatibility/operational considerations;
- avoid requesting implementation detail before the desired outcome is clear.

The issue-template configuration will:

- disable blank issues;
- provide contact links for product/usage support and private security
  reporting;
- use the production support page as the stable external redirect while the
  repository is private and before GitHub private vulnerability reporting is
  enabled.

The pull-request template will ask for:

- concise outcome and scope;
- relevant issue link when one exists;
- verification performed;
- documentation/public behavior impact;
- security/privacy or compatibility considerations;
- confirmation that no credentials/private runtime data are included.

It will not require a checklist item that is irrelevant to every pull request,
nor imply that all repository-wide test suites must run for every change.

### Phase 6: Align the production support content

Update `landing_page/src/content/markdown/support.md` so the public support page
uses the same four-way routing:

- support email/page for usage and connection questions;
- bug issue form for reproducible defects;
- feature issue form for proposals;
- `SECURITY:` email route for vulnerabilities and sensitive reports.

Add a stable "Report a security vulnerability" heading so the GitHub issue
chooser can link directly to it. Retain the existing privacy warnings and
self-hosted-service statement.

Update the landing-page README route inventory to include `/support`, since the
route exists but is omitted from the documented structure.

Do not change the privacy policy or terms unless implementation review finds a
direct contradiction. Their current support-email and self-hosting statements
are compatible with this plan.

### Phase 7: Validate newcomer usability and metadata

Run automated checks that:

- parse all issue-form YAML;
- verify required issue-form keys, IDs, labels, and contact-link URLs;
- confirm referenced labels exist in the GitHub repository;
- check repository-local Markdown links in README, contribution, support, and
  security files;
- build the landing site;
- inspect generated `/support` HTML for the support, issue, feature, and
  security routes;
- search for accidental SLA, hosted-service, stability, CLA, or DCO promises
  introduced by this task;
- confirm no security form allows or encourages public vulnerability details.

Perform a clean-clone/read-only walkthrough and confirm that a first-time
developer can find installation, contribution, testing, license, support,
security, and issue paths from the root README in under five minutes.

After the files reach `main`, GitHub community-profile recognition and rendered
issue forms can be checked again during tasks `060`/`080`; repository privacy
means the public anonymous boundary cannot be fully tested in this subtask.

### Implementation decisions and open questions

- No CLA is required for the initial release.
- No automated DCO enforcement is required before publication.
- A full code of conduct is deferred, but contribution guidance should require
  respectful and constructive participation.
- Keep Discussions disabled and route usage questions to the production support
  page/email for the initial release.
- Use `support@dynamicprogrammingsolutions.com` for both ordinary support and
  private security intake, differentiated by a `SECURITY:` subject prefix.
- Disable blank issues and provide only bug and feature forms for the initial
  public release.
- Add a concise pull-request template because the repository spans Python,
  React Native, Elixir, deployment, and documentation boundaries where explicit
  verification and risk notes materially improve review.
- Do not add a code of conduct, governance file, CODEOWNERS, CLA/DCO automation,
  Discussions categories, or maintainership policy in this task.
- No unresolved material question remains. Approval of this plan authorizes the
  root and landing support documentation changes described above.

### Documentation

- Add root contribution, security, and support guides for external developers
  and users.
- Add only the README links/status language needed to expose those guides.
- Align the existing product-facing support page with repository intake.
- Add GitHub issue/PR metadata.
- Avoid a large documentation navigation overhaul or duplication of
  package-owned guidance.

### Task checklist

- [x] Audit root README from an anonymous newcomer perspective.
- [x] Add concise contribution guidance.
- [x] Add private security-reporting guidance.
- [x] Add support routing.
- [x] Add bug and feature forms, issue chooser routing, and PR template.
- [x] Align the production landing support page.
- [x] Validate links, YAML structure, labels, and landing build.
- [x] Complete the clean-clone newcomer walkthrough.

### Requirement verification

- A clean-clone reviewer can identify setup, tests, license, support, security,
  and issue paths in under five minutes.
- Issue forms render successfully and security intake points away from public
  issues.
- Documentation links resolve within the repository or to the production site.
- Repository and landing support documentation distinguish usage questions,
  bugs, features, and security reports consistently.
- Searches and human review confirm that the documents make no unsupported SLA,
  stability, hosted-service, compatibility-window, CLA, or DCO promise.

### Additional implementation verification

- Confirm root and landing-page files changed by unrelated work are not
  overwritten; stage only task-owned files or hunks.
- Confirm no deployment workflow or GitHub repository setting is changed by
  this documentation task.
- Confirm the issue forms use labels already present in the repository.

## Implementation Notes

### Public repository entrypoints

- Added an early-development status section to the root README.
- The status language identifies the terminal/server, mobile connection, SDK,
  and plugin-authoring workflows while warning that APIs, configuration,
  plugin contracts, packaging, and deployment procedures may change.
- Added a root community/support section linking contribution, support,
  security, issue chooser, and production support paths.
- The README states that bridge and cloud-orchestrator components are
  self-hosted and that no public production bridge/cloud-agent service or
  support SLA is promised.

### Contributor, support, and security guidance

- Added `CONTRIBUTING.md` with scoped setup, test, documentation, pull-request,
  sensitive-data, participation, and contribution-license guidance.
- Added `SUPPORT.md` with separate routes for usage questions, bugs, features,
  and private security/sensitive reports.
- Added `SECURITY.md` using
  `support@dynamicprogrammingsolutions.com` and a `SECURITY:` subject prefix.
- The security policy does not promise response/remediation timelines,
  backports, a fixed support window, embargo terms, or a bounty.
- Public documentation contains no task-file or maintainer-workflow references.

### GitHub intake

- Added structured bug and feature issue forms using the existing `bug` and
  `enhancement` labels.
- The bug form requires version/environment/reproduction evidence and explicit
  confirmation that the issue is sanitized and not a vulnerability.
- The issue chooser disables blank issues and redirects usage support and
  security reports to the production support page.
- Added a concise pull-request template covering outcome, actual verification,
  documentation/compatibility effects, and sensitive-data safety.

### Landing support alignment

- Updated the authored support page to use the same four-way support routing as
  `SUPPORT.md`.
- Added a stable `report-a-security-vulnerability` anchor for the issue chooser.
- Retained the privacy warning and self-hosted-service boundary.
- Updated the landing-page README to include the existing `/support` route.

### Verification findings

- The landing build succeeded and generated all five routes.
- Astro emitted a duplicate content ID warning for the support Markdown during
  content synchronization. The generated `/support` route contained the
  intended content and anchor; the warning did not fail or alter the build.
- GitHub repository settings and workflows were not changed.
- Code of conduct, governance, CODEOWNERS, CLA/DCO automation, and Discussions
  remain deferred.

## Completion Notes

Completed on August 14, 2026.

### Outcome

- A first-time repository visitor can reach installation, contribution,
  testing, licensing, support, issue, and private security guidance from the
  root README.
- Public support routes now consistently separate usage questions,
  reproducible bugs, feature proposals, and security-sensitive reports.
- GitHub issue metadata is ready for the initial public release without adding
  speculative governance or support commitments.

### Requirement evidence

- README status/support requirement: root status and community sections expose
  the existing quickstart/development/license paths and the new support,
  contribution, issue, and security paths.
- Contributor requirement: `CONTRIBUTING.md` covers setup, focused tests,
  package-owned documentation, pull-request expectations, sensitive data, and
  inbound-equals-outbound licensing.
- Security requirement: `SECURITY.md`, the bug-form warning, issue chooser, and
  production support source all prohibit public vulnerability disclosure and
  route private reports to the support email.
- Support requirement: `SUPPORT.md` and the landing support page contain the
  same four request categories.
- Issue intake requirement: bug and feature YAML parsed successfully, required
  fields and unique IDs were inspected, blank issues are disabled, and the
  referenced `bug` and `enhancement` labels exist.
- Promise-boundary requirement: human review confirmed that the documents state
  the absence of an SLA, fixed compatibility/security window, public hosted
  bridge/cloud service, bounty, CLA, and DCO requirement rather than promising
  them.

### Verification performed

- `yarn --cwd landing_page build`
  - passed; five static routes generated
- Issue-form YAML parse and structural validation
  - passed for bug, feature, and chooser configuration
- GitHub label inspection
  - `bug` and `enhancement` exist
- Repository-local Markdown and landing-route link validation
  - `58` targets resolved
- Production URL checks
  - `https://crystallattice.dev/support` returned HTTP `200`
  - `https://crystallattice.dev/privacy` returned HTTP `200`
- Generated support-page inspection
  - support email, bug form, feature form, security route, stable anchor,
    self-hosting boundary, and no-SLA language present
- Read-only newcomer entrypoint walkthrough
  - setup, tests, license, support, issue, and security paths discoverable from
    the root README
- Whitespace, task scope, and workflow-change checks
  - passed

### Deferred public-boundary checks

The repository is still private and these files are not yet on `main`.
GitHub's rendered community profile, public issue chooser, anonymous links, and
private vulnerability reporting UI must therefore be verified again during the
publication readiness and post-publication tasks.
