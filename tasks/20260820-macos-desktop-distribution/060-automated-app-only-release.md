# Automate The App-Only DMG Release

Add protected GitHub Actions automation that verifies, builds, signs,
notarizes, and publishes the retained app-only DMG.

## Requirements checklist

- [ ] A manually triggerable GitHub Actions workflow produces the same verified DMG as the local release path.
- [ ] The workflow installs pinned Node, Ruby, CocoaPods, and Xcode dependencies and runs required verification before signing.
- [ ] Signing uses a temporary keychain and read-only signing-repository access.
- [ ] Notarization uses protected secrets and fails with accessible diagnostic logs when rejected.
- [ ] Successful runs publish the DMG, checksum, and release metadata to a controlled GitHub Release and configured download storage.
- [ ] Workflow permissions, action pins, environment protections, concurrency, retention, and secret redaction follow repository policy.
- [ ] The DMG workflow remains independently runnable after PKG automation is later added.

Parent Task: tasks/20260820-macos-desktop-distribution/000-main.md
Depends On: tasks/20260820-macos-desktop-distribution/050-app-only-dmg.md

## Execution plan
Status: Draft

Implement a manual-first protected release workflow using the local release
entry point as the source of truth. Reuse existing repository security checks,
OIDC/download publication patterns, and pinned action conventions. Separate
verification/build from publication where permissions differ. Add a tag trigger
only after manual workflow behavior is accepted.

### Implementation decisions and open questions

- Preserve a standalone DMG job or workflow after combined PKGs are introduced.
- Use GitHub Environments to scope Apple/signing/publication credentials.
- Prefer OIDC for AWS/download publication; do not add long-lived AWS keys.
- Do not publish from pull requests or untrusted forks.

### Documentation

- Document workflow trigger, inputs, environment, variables, secrets, expected outputs, rerun/recovery, and release rollback in desktop release development documentation.
- Keep public installation guidance separate from CI internals.

### Task checklist

- [ ] Define the manual workflow and protected environment.
- [ ] Add dependency caches and deterministic setup.
- [ ] Run desktop verification before signing.
- [ ] Create an ephemeral keychain and fetch signing assets read-only.
- [ ] Build, sign, notarize, staple, and validate the DMG.
- [ ] Upload workflow outputs with appropriate retention.
- [ ] Publish GitHub/download assets only from approved release context.
- [ ] Validate workflow YAML and repository Actions security checks.
- [ ] Run and inspect a successful manual workflow.

### Requirement verification

- Confirm a manual run produces a downloadable DMG matching local metadata and validation checks.
- Confirm verification failures prevent signing/publication.
- Confirm logs contain no private key, API key, match password, token, or keychain password.
- Confirm the published checksum matches the downloaded DMG.

### Additional implementation verification

- Record macOS runner/image/Xcode version and actual billed runtime for capacity planning.
- Exercise a controlled notarization or publication failure and verify maintainers receive actionable diagnostics without credential leakage.