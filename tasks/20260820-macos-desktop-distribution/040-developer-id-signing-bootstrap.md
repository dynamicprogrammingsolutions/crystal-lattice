# Bootstrap Developer ID Signing

Prepare Developer ID Application and Developer ID Installer signing assets for
local and GitHub Actions use without committing or exposing private material.

## Requirements checklist

- [x] A valid Developer ID Application certificate and private key are available for team `73Q43R2PD4`.
- [ ] A valid Developer ID Installer certificate and private key are available for the same team.
- [ ] Signing assets are encrypted in the approved private signing repository and can be fetched read-only.
- [ ] Local signing and CI signing use controlled keychains and do not depend on interactive prompts.
- [x] Notarization authentication is verified with the approved App Store Connect team API key.
- [ ] Required GitHub secrets, variables, environment protection, rotation, and recovery steps are documented without secret values.

Parent Task: tasks/20260820-macos-desktop-distribution/000-main.md
Depends On: tasks/20260820-macos-desktop-distribution/030-reproducible-macos-release-build.md

## Reconciliation — October 7, 2026

Progress: partially fulfilled through
`tasks/20260928-universal-macos-desktop-fastlane-release.md`.

Developer ID Application import, encrypted storage, read-only retrieval,
controlled local/CI keychains and App Store Connect notarization succeeded in
the September release, including clean hosted run `36633536807`. Application
rotation/recovery and GitHub settings are documented in
`desktop/crystal-lattice-control-desktop-rn/docs/development/macos-release.md`.

Developer ID Installer availability/import/verification is not established.
The requirements covering all signing assets and their complete recovery
documentation remain unchecked until that remaining PKG scope is verified.
Reuse the working Application identity; this task is no longer a DMG blocker.
Its remaining execution plan stays Draft.

## Manual prerequisite

The Apple Developer Account Holder must create Developer ID Application and
Developer ID Installer certificates through the current Apple-supported
workflow if valid certificates do not already exist. The executor must provide
current step-by-step instructions based on official Apple documentation and
must not create, revoke, or replace certificates without explicit approval.

## Execution plan
Status: Draft

Verify current Apple and fastlane support, inspect existing signing repository
contents without printing secrets, create or import the approved certificate
types, and test read-only retrieval into a temporary/local keychain. Configure
notarization authentication using the existing team API key or stop with a
specific permission error if Apple rejects it.

### Implementation decisions and open questions

- Reuse the existing private signing repository and `MATCH_PASSWORD` unless preflight identifies an access-isolation requirement.
- Keep routine CI access read-only.
- Use an ephemeral keychain in CI; do not rely on the login keychain.
- Do not revoke existing certificates as an automated cleanup action.

### Documentation

- Put maintainer signing setup, GitHub environment names, secret names, rotation, recovery, and troubleshooting in desktop release development documentation.
- Do not place secret values, local key paths, certificate private material, or password-manager details in tracked files.

### Task checklist

- [ ] Verify current Apple certificate creation roles and limits.
- [ ] Inventory existing Developer ID certificates without exposing private data.
- [ ] Obtain the Account Holder’s manual certificate creation where needed.
- [ ] Import/encrypt Application and Installer assets in the signing repository.
- [ ] Test read-only retrieval and noninteractive keychain access.
- [ ] Verify `notarytool` authentication.
- [ ] Document GitHub secrets/variables and recovery steps.

### Requirement verification

- Sign a small controlled test or the Release app with Developer ID Application and verify its certificate chain/team.
- Sign a test package or exercise the Installer identity without publishing it.
- Confirm read-only CI-style retrieval succeeds from a clean keychain.
- Confirm no secret/private key is tracked or printed in logs.

### Additional implementation verification

- Inspect certificate expiration and record renewal lead time.
- Verify signing-repository history contains only encrypted signing material and approved metadata.