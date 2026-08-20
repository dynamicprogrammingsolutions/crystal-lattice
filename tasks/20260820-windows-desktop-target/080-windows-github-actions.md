# Add GitHub Actions Windows CI And Release Automation

Automate shared verification, Windows native builds, tests, MSIX packaging,
trusted signing, and publication through protected GitHub Actions workflows.

## Requirements checklist

- [ ] Pull requests and branch pushes run shared tests plus unsigned Windows x64 build/native smoke checks.
- [ ] ARM64 Windows build checks run on an available supported runner or an explicitly documented alternative.
- [ ] Protected manual release builds produce verified x64 and approved ARM64 MSIX outputs from one source/version.
- [ ] Signing is isolated to a protected environment and uses OIDC or protected secrets without exposing credentials.
- [ ] Native unit/integration tests and the selected Appium smoke slice run before publication.
- [ ] Release jobs verify package signatures, install, launch, checksums, metadata, and source/version consistency.
- [ ] GitHub Releases and configured download storage receive unambiguous packages, checksums, and release manifests.
- [ ] Workflow permissions, action pins, concurrency, caches, artifacts, retention, diagnostics, and OIDC publication follow repository security policy.
- [ ] Full UI automation has a maintained workflow for the chosen interactive Windows runner.

Parent Task: tasks/20260820-windows-desktop-target/000-main.md
Depends On: tasks/20260820-windows-desktop-target/070-windows-msix-signing.md

## Recommended workflow split

```text
Shared validation
    ubuntu
    TypeScript/Jest/shared package tests

Windows x64
    windows-2025
    Codegen/native build/ReleaseBundle/native tests/Appium smoke/MSIX

Windows ARM64
    windows-11-arm or approved alternative
    build/native tests/MSIX

Full Windows UI
    persistent self-hosted or disposable interactive Windows runner

Release
    protected environment
    sign/verify/install-smoke/publish
```

## Execution plan
Status: Draft

Add a fast PR workflow and a protected manual-first release workflow. Reuse
package-owned scripts as the source of truth rather than duplicating build
logic in YAML. Pin actions, minimize permissions, cache safe dependencies,
separate unsigned verification from signing/publication, and publish only
outputs tied to one commit/version manifest. Add tag triggers only after manual
release acceptance.

### Implementation decisions and open questions

- Reverify `windows-2025` and `windows-11-arm` availability and image contents at implementation time.
- Use x64 as the required first release architecture; do not silently publish ARM64 when tests are incomplete.
- Treat full Appium runner choice as an operational dependency with explicit health/reset checks.
- Prefer OIDC for signing and download publication.

### Documentation

- Document workflow triggers, inputs, runner images, prerequisites, caches, environments, secrets/variables, signing, outputs, rerun/recovery, runner reset, and costs in Windows release development docs.
- Public docs should link releases/downloads without exposing CI internals.

### Task checklist

- [ ] Add shared and Windows PR/branch CI.
- [ ] Add x64 and ARM64 build/test/package jobs.
- [ ] Add Appium smoke and full-suite runner jobs.
- [ ] Add protected signing and release jobs.
- [ ] Add install/signature/checksum/source-version verification.
- [ ] Add GitHub/download publication.
- [ ] Validate YAML, action pins, permissions, and security checks.
- [ ] Run successful manual non-publishing and publishing workflows.
- [ ] Record runner duration, reliability, and billed usage.

### Requirement verification

- Confirm PR CI fails before packaging when shared/native verification fails.
- Confirm protected release produces downloadable signed packages matching the source/version manifest.
- Confirm logs contain no certificate private data, signing token, password, or publication credential.
- Confirm the downloaded package installs and launches in a clean Windows test environment.

### Additional implementation verification

- Exercise controlled signing, Appium-runner, and publication failures and verify actionable diagnostics.
- Verify retries cannot combine outputs from different commits or architecture jobs.