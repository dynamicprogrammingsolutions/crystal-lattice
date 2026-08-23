# Automate The Combined PKG Release

Extend protected GitHub Actions release automation to build and publish the
Apple Silicon and Intel combined PKGs while keeping the app-only DMG workflow
available.

## Requirements checklist

- [ ] GitHub Actions builds both architecture-specific CLI payloads and corresponding combined PKGs from an approved source revision.
- [ ] The universal desktop app used by the PKGs is produced through the same verified build contract as the DMG.
- [ ] CI signs all nested code, signs the PKGs, notarizes, staples, and validates both outputs.
- [ ] The DMG remains a separately selectable and separately published build output.
- [ ] GitHub Releases and configured download storage receive both PKGs, the DMG, checksums, and machine-readable release metadata without ambiguous filenames.
- [ ] CI verifies a PKG installation and independent CLI execution on each available matching runner architecture.
- [ ] Permissions, secrets, environments, action pins, OIDC publication, concurrency, diagnostics, and retention meet repository policy.

Parent Task: tasks/20260820-macos-desktop-distribution/000-main.md
Depends On: tasks/20260820-macos-desktop-distribution/090-combined-app-cli-pkg.md

## Execution plan
Status: Draft

Add combined-installer jobs or a dedicated workflow that reuses the accepted
DMG build/sign/notarization primitives without coupling the two publication
choices. Build the CLI payload on matching Intel and ARM runners, package the
universal app with the matching runtime, test installation, notarize, and
publish all outputs under a single coherent desktop release version and
manifest.

### Implementation decisions and open questions

- Keep manual `workflow_dispatch` available even if tag publication is added.
- Preserve independent rerun/recovery for DMG and PKG jobs.
- Do not make the DMG depend on successful CLI payload creation unless the release request explicitly requires all outputs atomically.
- Define whether a partially successful release is withheld or published with explicit missing-output status; recommend withholding tagged public publication until all requested outputs pass.

### Documentation

- Update desktop release development documentation with workflow topology, inputs, environments, runner architecture, secrets/variables, publication, failure recovery, and cost monitoring.
- Document release metadata consumed by the landing page without duplicating CI internals in public pages.

### Task checklist

- [ ] Add ARM64 and Intel CLI payload jobs.
- [ ] Add combined PKG jobs using the accepted universal app.
- [ ] Add architecture-appropriate install/CLI smoke checks.
- [ ] Sign, notarize, staple, and validate both PKGs.
- [ ] Retain and exercise the app-only DMG output.
- [ ] Publish unambiguous filenames, checksums, and release manifest.
- [ ] Validate Actions security and workflow syntax.
- [ ] Run a complete protected manual release.

### Requirement verification

- Confirm one approved release exposes a valid DMG plus ARM64 and Intel PKGs.
- Download each output and compare checksums, versions, signatures, notarization, and manifest entries.
- Confirm the CLI smoke test runs with the desktop app stopped.
- Confirm a PKG job failure does not silently replace or relabel the DMG.

### Additional implementation verification

- Record actual Intel and ARM runner availability, Xcode versions, duration, and billed minutes.
- Verify release retries cannot publish mixed outputs from different source commits or version manifests.