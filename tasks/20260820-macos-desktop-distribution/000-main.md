# Prepare macOS Desktop Distribution, Bundled CLI Installer, And Workspace Onboarding

Prepare Crystal Lattice Desktop for direct macOS distribution through signed,
notarized downloads. Retain an app-only DMG, add separate architecture-specific
PKG installers that include the CLI, automate both release paths through GitHub
Actions, present both choices clearly on the landing page, and add workspace
onboarding that works with either installation.

## Requirements checklist

- [x] A signed, notarized, stapled app-only DMG is available as a maintained release output.
- [ ] Signed, notarized, stapled Apple Silicon and Intel PKGs are available as separate release outputs and install both the desktop app and the matching CLI runtime.
- [ ] Installing a combined PKG makes `crystal-lattice` available in Terminal without the desktop app starting, owning, or supervising the CLI process.
- [ ] GitHub Actions can build, verify, sign, notarize, and publish both the retained DMG and the combined PKGs without exposing credentials.
- [ ] An app-only release acceptance gate is completed after DMG automation and before bundled-CLI work proceeds.
- [ ] The landing page presents clear “Desktop app only” and “Desktop app + CLI” choices with correct architecture, installation, support, privacy, and release information.
- [ ] “Add Workspace” is included in the desktop application distributed through both DMG and PKG paths, while the existing manual connection workflow remains available.
- [ ] Workspace onboarding selects a directory, discovers available workspace/runtime information, creates the connection, and gives the user the exact Terminal command without launching the CLI.
- [ ] Final release acceptance covers Apple Silicon and Intel, both distribution choices, workspace onboarding, Gatekeeper, installation, upgrade, and public downloads.
- [ ] Current user and maintainer documentation explains the delivered distribution and release workflows without exposing task-phase terminology.

## Reconciled delivery state — October 7, 2026

Progress: partially fulfilled. The app-only build and DMG were delivered by
`tasks/20260928-universal-macos-desktop-fastlane-release.md`; the combined
CLI/PKG/onboarding outcome remains outstanding. The user approved this separate
task/roadmap reconciliation on October 7, 2026. It preserves the original
release history and does not authorize the remaining implementation plans.

- **COMPLETED VIA:** subtasks 030 and 050 have evidence from the approved
  September release. Candidate run `36633536807` succeeded on September 29;
  publication run `36685765746` succeeded on September 30. The public output
  is `Crystal Lattice Desktop 0.9.0 (4)`, universal, notarized and stapled.
- **PARTIALLY COMPLETED VIA:** 010 has the app identity/preflight baseline;
  040 has Developer ID Application signing and notarization. PKG-specific
  preflight and Developer ID Installer delivery remain incomplete.
- **SUPERSEDED BY:** 020, 060 and 070 are retained historical contracts whose
  replacement is `tasks/20260928-universal-macos-desktop-fastlane-release.md`.
  Their unmet original conditions are not marked complete.
- The replacement acceptance record still needs explicit Apple Silicon
  public-artifact human confirmation. The first DMG's Intel hardware waiver
  is not evidence of successful future CLI/PKG architecture acceptance.
- Subtasks 080–130 remain active future work. The app stays universal, both
  CLI architectures remain required, the DMG remains independent, and the
  desktop never owns the user's CLI process.

## Approved scope and decisions

- Direct distribution is outside the Mac App Store; no Mac App Store record is required.
- Product name: `Crystal Lattice Desktop`, as approved for the September release.
- macOS bundle ID: `com.dynamicprogrammingsolutions.crystallatticecontrol.macos`.
- Apple Developer team: `73Q43R2PD4`.
- Initial marketing version target: `0.9.0`; CI supplies monotonically increasing build numbers.
- Minimum deployment target: macOS 14.0 unless preflight finds a verified dependency constraint requiring a user-approved change.
- The GUI application remains universal (`arm64` and `x86_64`).
- The app-only output remains a DMG.
- The combined app-and-CLI output is added as two PKGs, one per CLI architecture; adding PKG must not replace or remove DMG production.
- The combined installer uses Developer ID Application signing for executable code and Developer ID Installer signing for the PKG.
- The existing App Store Connect team API key may be reused for notarization after current Apple behavior is verified.
- Workspace onboarding is present in both distributions. DMG users are assumed to have a compatible `crystal-lattice` command installed separately.
- The desktop app does not start, own, stop, or supervise CLI processes.
- Automatic application updates are excluded and belong to a later task.

## Subtasks

- [ ] `tasks/20260820-macos-desktop-distribution/010-release-contract-and-preflight.md`
- [ ] `tasks/20260820-macos-desktop-distribution/020-production-identity-metadata-branding.md`
  - SUPERSEDED BY `tasks/20260928-universal-macos-desktop-fastlane-release.md`.
- [x] `tasks/20260820-macos-desktop-distribution/030-reproducible-macos-release-build.md`
  - COMPLETED VIA `tasks/20260928-universal-macos-desktop-fastlane-release.md`.
- [ ] `tasks/20260820-macos-desktop-distribution/040-developer-id-signing-bootstrap.md`
- [x] `tasks/20260820-macos-desktop-distribution/050-app-only-dmg.md`
  - COMPLETED VIA `tasks/20260928-universal-macos-desktop-fastlane-release.md`.
- [ ] `tasks/20260820-macos-desktop-distribution/060-automated-app-only-release.md`
  - SUPERSEDED BY `tasks/20260928-universal-macos-desktop-fastlane-release.md`.
- [ ] `tasks/20260820-macos-desktop-distribution/070-app-only-release-acceptance.md`
  - SUPERSEDED BY `tasks/20260928-universal-macos-desktop-fastlane-release.md`.
- [ ] `tasks/20260820-macos-desktop-distribution/080-desktop-cli-payload.md`
- [ ] `tasks/20260820-macos-desktop-distribution/090-combined-app-cli-pkg.md`
- [ ] `tasks/20260820-macos-desktop-distribution/100-automated-combined-installer-release.md`
- [ ] `tasks/20260820-macos-desktop-distribution/110-desktop-landing-distribution-options.md`
- [ ] `tasks/20260820-macos-desktop-distribution/120-workspace-onboarding.md`
- [ ] `tasks/20260820-macos-desktop-distribution/130-final-release-acceptance.md`

## Historical starting state — August 20, 2026

The following observations describe the original audit, not the current
released application. Current app/build/signing evidence belongs to the
September release task and the reconciled subtask records.

- The React Native macOS app is under `desktop/crystal-lattice-control-desktop-rn`.
- The shared scheme is `CrystalLatticeControlDesktopRN-macOS`.
- The project currently resolves Release architectures to `arm64 x86_64` and has Hardened Runtime enabled.
- Current product naming and bundle identity still contain React Native template values.
- The macOS AppIcon set declares slots but contains no image files.
- Release signing currently uses Apple Development rather than Developer ID Application.
- The entitlement file exists but is not assigned through `CODE_SIGN_ENTITLEMENTS`.
- The Xcode target declares macOS 12.4 while the Podfile declares macOS 14.0.
- A local unsigned archive attempt stopped because generated CocoaPods support files were absent; a complete clean Release archive has not yet been established.
- The CLI already has a relocatable bundled-Python package builder and Darwin ARM64/AMD64 release jobs.
- The locally observed ARM64 CLI runtime is approximately 286 MB, of which approximately 267 MB is the Python tree.
- The landing page has a mobile page and CLI download path but no desktop download page.

## Reference links

- Apple notarization: https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution
- Apple Developer ID certificates: https://developer.apple.com/help/account/certificates/create-developer-id-certificates
- Apple hardened runtime: https://developer.apple.com/documentation/xcode/configuring-the-hardened-runtime
- Apple app sandbox: https://developer.apple.com/documentation/security/app-sandbox
- fastlane match: https://docs.fastlane.tools/actions/match/
- fastlane macOS build: https://docs.fastlane.tools/actions/build_mac_app/
- GitHub-hosted runners: https://docs.github.com/actions/using-github-hosted-runners/about-github-hosted-runners

## Execution plan
Status: Draft

Use the completed app-only baseline rather than repeating superseded work.
Finish remaining preflight in 010 and the replacement app-only human acceptance
record before bundled-CLI execution. Installer preparation in 040 and payload
work in 080 can then proceed independently; both are prerequisites for 090.
Follow with automation 100, onboarding 120, distribution presentation 110 and
final acceptance 130. Onboarding does not wait for marketing publication.

The app-only acceptance gate is owned by
`tasks/20260928-universal-macos-desktop-fastlane-release.md`; do not execute
historical 070 as a second, conflicting gate. The parent remains incomplete
until both release choices and onboarding pass the final matrix.

The implementation must use current official Apple, GitHub Actions, fastlane,
React Native macOS, and relevant packaging documentation. The executor has
internet access and must recheck current certificate, notarization, runner,
action-version, and secret-handling behavior rather than relying only on this
task’s August 20, 2026 snapshot.

### Implementation decisions and open questions

- Decision: the combined PKG is an additional build output; it must not replace the DMG.
- Decision: publish separate ARM64 and Intel PKGs instead of embedding both complete Python runtimes in one installer.
- Decision: keep the GUI application universal in both PKGs.
- Decision: use a system CLI installation location and a `/usr/local/bin/crystal-lattice` entry; do not run the existing user-scoped shell installer from PKG scripts.
- Decision: keep standalone `~/.local` CLI installations user-owned and document command precedence rather than deleting or overwriting them.
- Decision: workspace onboarding is one end-to-end follow-up subtask even though it crosses CLI status reporting, native directory access, desktop persistence, and UI.
- Open implementation question for subtask 010: confirm the final sandbox posture after auditing attachment, download, workspace, global profile, and security-scoped bookmark behavior.
- Open implementation question for subtask 120: decide the no-existing-port behavior and runtime-status file schema during detailed planning without changing the approved user outcome.

### Documentation

- Desktop user documentation belongs under `desktop/crystal-lattice-control-desktop-rn/docs/`, linked from its README.
- Desktop release implementation and runbook documentation belongs under `desktop/crystal-lattice-control-desktop-rn/docs/development/`, linked from its development index.
- CLI installation/coexistence behavior belongs in `application/python/README.md` or focused application package documentation if the README would become unwieldy.
- Public distribution choices, installation summaries, support, and privacy wording belong in authored `landing_page/` sources.
- Generated `docs_site/prepared/`, `docs_site/dist/`, landing build output, release output, and other generated directories must not be edited directly.
- Public documentation must describe current delivered behavior and omit task numbers, phases, requirement IDs, and approval status.

### Task checklist

- [x] Produce the automated app-only DMG release path through the September release task.
- [ ] Finish remaining PKG preflight in 010 and Installer signing in 040.
- [ ] Obtain app-only human acceptance in the replacement September release record.
- [ ] Complete subtasks 080–100 and add the CLI payload and separate combined PKG release path.
- [ ] Complete subtask 110 and publish the two clear desktop download choices.
- [ ] Complete subtask 120 and include workspace onboarding in both distribution outputs.
- [ ] Complete subtask 130 and record final acceptance evidence.
- [ ] Keep this main checklist synchronized with subtask completion evidence.

### Requirement verification

- Verify the DMG requirement with the published September artifact and its replacement acceptance record.
- Verify the combined-installer requirements with both architecture-specific PKGs, installation receipts, terminal command checks, and the 130 matrix.
- Verify automation through successful GitHub Actions runs whose logs contain no credentials and whose outputs match locally verified signing/notarization metadata.
- Verify landing behavior through production URLs and downloads, not only a local static build.
- Verify workspace onboarding through production desktop builds from both distribution paths while the CLI remains an independently started Terminal process.
- Verify documentation through package/landing builds, link checks where available, and comparison against the actual released behavior.

### Additional implementation verification

- Inspect every final executable and native library for expected architecture and Developer ID signature.
- Validate notarization logs, stapled tickets, Gatekeeper assessment, checksums, and package receipts.
- Confirm user-owned config, sessions, credentials, plugin caches, and standalone CLI installations survive app and PKG upgrades.