# Package And Sign The Windows Application

Produce maintained, directly downloadable Windows packages with stable
identity, trusted code signing, clean installation, upgrade, and removal
behavior.

## Requirements checklist

- [ ] A ReleaseBundle Windows application is packaged as MSIX for x64.
- [ ] ARM64 MSIX is added and verified after the host path is stable.
- [ ] Package identity, publisher, display metadata, icons, capabilities, versions, architecture, install location, and protocol/file associations are explicit and reproducible.
- [ ] Production packages use a publicly trusted signing path; self-signed certificates are limited to development/test.
- [ ] Signature, package integrity, installation, launch, upgrade, downgrade policy, repair/removal, and user-state preservation are verified.
- [ ] Package filenames, checksums, release manifest, and architecture labels are unambiguous.
- [ ] A future `.msixbundle` can combine architectures without removing separately testable packages if desired.
- [ ] Windows CLI bundling is not introduced implicitly.

Parent Task: tasks/20260820-windows-desktop-target/000-main.md
Depends On: tasks/20260820-windows-desktop-target/060-windows-native-testing.md

## Recommended distribution

- x64 MSIX first.
- ARM64 MSIX after core/native parity is stable.
- Optional MSIX bundle later for one user-facing multi-architecture download.
- Azure Artifact Signing or a current equivalent trusted signing service for production.
- GitHub Release/download-domain publication belongs to subtask 080.

## Execution plan
Status: Draft

Use the generated/maintained Windows packaging project or current supported
MSIX tooling to create unsigned development and signed production packages.
Define stable package/publisher/version contracts, configure capabilities
minimally, integrate development certificate setup, then integrate the approved
production signing provider. Test fresh install, upgrade, uninstall, signatures,
and user-state preservation on clean x64 and ARM64 Windows environments.

### Implementation decisions and open questions

- Prefer OIDC/service-based production signing over storing a long-lived PFX when current provider support permits it.
- Do not use a self-signed package for public distribution.
- Do not add Microsoft Store submission or Store-specific identity without separate approval.
- Determine whether ARM64 is published at first public release based on feature/test parity, not only successful compilation.

### Documentation

- Add Windows installation, architecture selection, upgrade, uninstall, SmartScreen/signature, troubleshooting, and system requirements to Windows user docs.
- Add packaging identity, development certificates, production signing, versioning, validation, recovery, and rotation to Windows release development docs.
- Never commit private certificates or passwords.

### Task checklist

- [ ] Define package/publisher/version/architecture contracts.
- [ ] Configure ReleaseBundle packaging and capabilities.
- [ ] Produce and install development-signed x64 MSIX.
- [ ] Produce and install development-signed ARM64 MSIX.
- [ ] Configure approved production signing.
- [ ] Verify package signatures and integrity.
- [ ] Test clean install, launch, upgrade, removal, and user-state preservation.
- [ ] Generate checksums and release manifest.
- [ ] Evaluate optional `.msixbundle`.

### Requirement verification

- Install production-equivalent signed packages on clean matching-architecture Windows systems.
- Verify signatures with Windows signing tools and inspect package identity/version.
- Verify application launch and core/native tests from installed packages.
- Verify upgrade/removal leaves user-owned connection/session/cache state according to the approved policy.

### Additional implementation verification

- Test Windows App Installer behavior and actionable failure messages.
- Verify architecture mismatch produces clear installation failure rather than a misleading app crash.