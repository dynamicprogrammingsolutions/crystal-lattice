# Expand CI And Dependency Security After Initial Publication

Add broader automated quality and supply-chain coverage in response to real
contribution patterns and GitHub security findings.

## Requirements checklist

- [ ] CI coverage expands where public changes actually create regression risk.
- [ ] Dependabot or equivalent update automation covers maintained package ecosystems without unmanageable pull-request noise.
- [ ] Static analysis and code scanning are enabled where signal justifies cost and maintenance.
- [ ] Action dependency updates preserve immutable pinning.
- [ ] Security automation cannot access production deployment authority from untrusted code.

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
- [ ] Verify secret and environment isolation.

### Requirement verification

- Added automation catches or prevents a documented class of risk.
- Pull-request volume and Actions cost remain acceptable.
