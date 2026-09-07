# Expand CI And Dependency Security After Initial Publication

Add broader automated quality and supply-chain coverage in response to real
contribution patterns and GitHub security findings.

## Requirements checklist

- [ ] CI coverage expands where public changes actually create regression risk.
- [ ] Dependabot or equivalent update automation covers maintained package ecosystems without unmanageable pull-request noise.
- [ ] Static analysis and code scanning are enabled where signal justifies cost and maintenance.
- [ ] Action dependency updates preserve immutable pinning.
- [ ] Security automation cannot access production deployment authority from untrusted code.
- [ ] Existing repository-level deployment, CLI publication, and iOS
  signing/upload secrets are moved to their corresponding protected GitHub
  environments, or an equivalent least-privilege design is reviewed and
  documented.

Parent Task: tasks/20260804-open-source-public-release/000-main.md
Depends On: tasks/20260804-open-source-public-release/080-post-publication-validation-and-early-adopter-intake.md

## Deferred candidates

- Multi-ecosystem `.github/dependabot.yml`
- CodeQL for Python, JavaScript/TypeScript, and other supported languages
- Broader operating-system/version matrices
- Native mobile validation
- Elixir checks
- Dependency/license SBOM generation
- Automated action-SHA update tooling
- Scheduled security and stale-dependency jobs
- Environment-scoped migration of the initial-release repository secrets

## Known post-publication findings

- The root workspace `npm audit` on August 14, 2026 reported 21 findings,
  including two critical findings.
- `npm audit --omit=dev` still reported one critical and eleven high findings
  because npm auto-installs `react-native` for wildcard peer dependencies in
  shared React Native workspace packages.
- The critical `shell-quote` path is:
  `frontend-rn-components`/`react-native-mac-text-view` peer dependency →
  auto-installed `react-native` → `react-devtools-core` → `shell-quote`.
- The audited React Native/Metro tree is contributor/test tooling in the root
  workspace; it is not bundled into the Python CLI and peer dependencies are
  not shipped inside the shared package.
- The initial public CI workflow has no secrets, write token, signing material,
  OIDC, or deployment environment, limiting the consequence of untrusted PR
  code independently of this tooling finding.
- The initial publication intentionally permits existing secret values to
  remain repository-scoped under a trusted-write-collaborator model. This does
  not protect against a deliberately malicious or compromised collaborator
  with workflow write access, so environment-scoped migration remains required
  follow-up rather than being treated as permanently resolved.
- Follow-up should evaluate removal of obsolete `@types/react-native`
  dependencies, explicit peer/dev version constraints, safe lockfile
  overrides, and coordinated React Native/Metro updates rather than applying an
  unreviewed `npm audit fix --force`.

## Execution plan
Status: Draft

Review the initial public pull requests, Actions usage, and security alerts.
Prioritize automation that prevents demonstrated regressions or closes known
security gaps. Introduce updates in small groups so alert and pull-request noise
remains manageable.

### Implementation decisions and open questions

- Hosted-provider and cloud tests remain opt-in and credential-gated.
- Costly matrices require evidence of value.
- CodeQL language scope depends on initial signal and repository plan support.

### Documentation

- Document new required checks, schedules, and alert ownership.

### Task checklist

- [ ] Review early CI failures and security alerts.
- [ ] Select the next high-value automation.
- [ ] Add dependency update configuration.
- [ ] Add selected scanning/matrices.
- [ ] Move deployment, CLI publication, and iOS signing/upload secret values
  into their protected environments and remove the repository-level copies
  after successful workflow verification.
- [ ] Verify secret and environment isolation.

### Requirement verification

- Added automation catches or prevents a documented class of risk.
- Pull-request volume and Actions cost remain acceptable.
- Protected deployment and publication jobs continue to work after
  environment-secret migration, and repository-level copies no longer exist.
