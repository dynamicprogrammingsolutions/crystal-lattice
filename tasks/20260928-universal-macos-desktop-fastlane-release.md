# Release The Universal macOS Desktop App With Fastlane And GitHub Actions

Prepare and publish the first direct-download release of Crystal Lattice
Desktop for macOS as one universal Apple Silicon and Intel app-only DMG. Use
Fastlane as the local release source of truth, reproduce the same release
through manual GitHub Actions automation, and add a small accessible
download icon to the public website only after the signed and notarized
artifact is publicly available and independently verified.

This is a deliberately narrow release task. It does not replace or modify
`tasks/20260820-macos-desktop-distribution/000-main.md` or any of that task's
subtasks. After this task is complete, its evidence can be used in a separate
user-approved reconciliation of the broader macOS distribution task.

## Requirements checklist

- [ ] Crystal Lattice Desktop `0.9.0` is released outside the Mac App Store as
      one app-only DMG containing a universal `arm64` and `x86_64` application.
- [ ] The released application uses product name `Crystal Lattice Desktop`,
      bundle ID `com.dynamicprogrammingsolutions.crystallatticecontrol.macos`,
      Apple team `73Q43R2PD4`, minimum macOS 14.0, and an intentional,
      inspectable build number.
- [ ] The application has a complete production macOS icon, bundles its
      production JavaScript, launches without Metro or a source checkout, and
      preserves the existing supported connection/session behavior.
- [ ] The application and all nested executable code are signed with a valid
      Developer ID Application identity, Hardened Runtime, a secure timestamp,
      and only justified Release entitlements.
- [ ] The final DMG is signed where applicable, submitted to Apple's current
      notarization service, accepted, stapled, and independently validated by
      Gatekeeper and strict code-signature checks.
- [ ] Package-local Fastlane automation provides repeatable verification,
      universal build, signing, DMG creation, notarization, stapling,
      validation, and checksum generation without committing credentials.
- [ ] A manually dispatched GitHub Actions workflow reproduces the local
      release path, uses read-only signing retrieval and an ephemeral
      keychain, prevents untrusted publication, and optionally publishes the
      DMG, checksum, and bounded verification metadata through the existing
      private-S3/CloudFront download infrastructure without exposing
      credentials.
- [ ] The published DMG is downloaded through its public release URL and
      passes checksum, signature, notarization, stapling, architecture,
      installation, launch, and focused product smoke verification.
- [ ] Human acceptance covers installation and launch on Apple Silicon.
      Universal Intel slices are verified automatically; real Intel hardware
      feedback is intentionally deferred to initial testers and is not a
      pre-release gate.
- [ ] After release acceptance, the landing-page header contains a small,
      keyboard-accessible download icon whose accessible name identifies the
      macOS download and whose HTTPS target is the verified versioned DMG.
- [ ] Current desktop release documentation explains local and GitHub Actions
      release operation, required credentials, verification, recovery, and
      installation without exposing secret values.
- [ ] The existing broader macOS distribution task and subtasks remain
      unchanged during this task.

## Scope

Included:

- Production identity, versioning, icon, Release metadata, and minimum macOS
  target needed for this release.
- One universal app-only DMG.
- Developer ID Application signing.
- Apple notarization and ticket stapling.
- Local Fastlane lanes.
- GitHub Actions verification, signing, notarization, and publication through
  the existing download CDN under a desktop-specific prefix.
- Apple Silicon release acceptance and automated universal-binary validation;
  post-release Intel feedback from initial testers.
- One website header download icon after release acceptance.
- Focused user and maintainer documentation for the delivered release path.

Excluded:

- Mac App Store submission or an App Store Connect app record.
- Developer ID Installer certificates.
- PKG installers.
- Bundling or installing the `crystal-lattice` CLI.
- `/usr/local/bin` installation or package receipts.
- Workspace onboarding or runtime discovery.
- Application-managed CLI processes.
- Automatic updates.
- A separate desktop S3 bucket, CloudFront distribution, certificate, or
  subdomain. The first release reuses the existing CLI download
  infrastructure with a distinct `crystal-lattice-desktop` prefix.
- A full `/desktop` marketing or download page.
- Changes to `tasks/20260820-macos-desktop-distribution/`.

## Human-action legend

- **AGENT:** Safe repository, build, inspection, documentation, and automation
  work that an agent may perform after this plan is approved.
- **HUMAN — MANDATORY:** Work that requires an Apple/GitHub account owner,
  physical hardware, external approval, or credentials an agent must not
  request or handle directly.
- **HUMAN JUDGMENT:** A product, security, visual, or release decision that
  must be explicitly accepted by the user.
- **AGENT + HUMAN:** The agent prepares and verifies the technical work; a
  human performs or confirms the external or subjective boundary.

No human step may be marked complete from agent inference. Record the person,
date, system, decision, or external action that supplies the evidence.

## Local macOS UI automation setup

Native macOS XCUITests require the operating system's Automation Mode. This is
a machine-level developer setting, not an application setting or repository
secret.

For a development or CI-style Mac where unattended local UI tests are
intended, an administrator runs:

```bash
sudo /usr/sbin/DevToolsSecurity -enable
sudo /usr/bin/automationmodetool enable-automationmode-without-authentication
/usr/bin/automationmodetool
```

Enter the administrator password only in the local Terminal prompt. Never put
the password in chat, a task file, shell history arguments, environment
variables, GitHub secrets, or tracked files.

After configuration, this is a valid and expected status before a test starts:

```text
Automation Mode is disabled.
This device DOES NOT REQUIRE user authentication to enable Automation Mode.
```

The two lines describe different state:

- `Automation Mode is disabled` means no current XCTest session has activated
  Automation Mode. It does not mean setup failed.
- `DOES NOT REQUIRE user authentication` confirms the machine policy is
  configured correctly. The next macOS UI test can enable Automation Mode
  automatically without waiting for an administrator prompt.

Run the focused project check with:

```bash
cd desktop/crystal-lattice-control-desktop-rn
npm run test:macos-ui:session-filters
```

If the test still times out while enabling Automation Mode, capture the
`.xcresult` path from `xcodebuild` and inspect the exported XCTest diagnostics
before changing application code or signing settings.

The unattended policy is system-wide and persists until disabled. To restore
the authentication requirement and disable developer-tool authorization, an
administrator runs:

```bash
sudo /usr/bin/automationmodetool disable-automationmode-without-authentication
sudo /usr/sbin/DevToolsSecurity -disable
```

## Developer ID Application certificate setup

The direct-download DMG requires one Developer ID Application certificate and
its paired private key for Apple team `73Q43R2PD4`. A Developer ID Installer
certificate is not needed because this task does not create a PKG.

Apple currently requires the Account Holder role to create this certificate.
The certificate should be created manually so the Apple Account password and
two-factor authentication remain outside automation, chat, tracked files, and
CI.

### 1. Create the certificate signing request

On the signing Mac:

1. Open **Keychain Access**.
2. Choose **Keychain Access → Certificate Assistant → Request a Certificate
   From a Certificate Authority**.
3. Enter the Account Holder's Apple Account email.
4. Use a recognizable common name such as
   `Crystal Lattice Developer ID Application`.
5. Select **Saved to disk**.
6. Save the `.certSigningRequest` file in a private temporary directory.

This creates the private key in the local keychain. Do not delete that private
key after uploading the request.

### 2. Create and install the Apple certificate

The Account Holder:

1. Signs in to Apple Developer **Certificates, Identifiers & Profiles**.
2. Opens **Certificates** and selects the add button.
3. Under **Software**, selects **Developer ID**.
4. Selects **Developer ID Application**, not Developer ID Installer.
5. Uploads the `.certSigningRequest`.
6. Downloads the generated `.cer`.
7. Double-clicks the `.cer` to install it in the same keychain that contains
   the CSR's private key.

In Keychain Access, **My Certificates** must show the Developer ID Application
certificate with an expandable private key beneath it. A certificate without
the paired private key cannot sign the app or be imported into match.

### 3. Export for encrypted match storage

In **My Certificates**:

1. Select the Developer ID Application certificate and its private key.
2. Export them as a password-protected `.p12`.
3. Use a strong temporary export password.
4. Keep the `.cer` and `.p12` only in a private temporary directory with
   restricted permissions.

Do not commit, email, upload to general file sharing, or paste either file or
its password into chat. The `.p12` contains the signing private key.

### 4. Import into the approved private signing repository

The iOS release previously created its Apple Distribution certificate and
App Store provisioning profile through `fastlane ios setup_signing` and saved
both encrypted in the private `crystal-lattice-ios-signing` repository. The
desktop Developer ID Application certificate was created manually by the
Account Holder, so this one-time desktop bootstrap instead imports the
existing `.cer` and paired private key into that same approved encrypted
repository. `match` stores different certificate types in separate folders.
There is no need to create another signing repository for this approved
shared-storage approach.

Before import, restrict the exported `.p12` to the current user (`chmod 600`).
The local helper
`desktop/crystal-lattice-control-desktop-rn/scripts/import_developer_id_signing.sh`
checks the selected certificate fingerprint and paired private key, prompts
locally for the Keychain-exported `.p12` password, creates a temporary
empty-password `.p12` that Fastlane can import in unattended CI, and runs
`fastlane match import --type developer_id` against the approved private
repository. The helper removes its temporary key material after the import.
Do not provide passwords as command arguments or in chat.

If Homebrew OpenSSL 3 reports `unsupported ... RC2-40-CBC` when opening a
Keychain Access `.p12`, the helper enables OpenSSL's legacy provider only
while reading that export. It briefly transfers the identity through a
single-use local keychain, then uses Apple's `security export` to produce
the empty-password `.p12` that macOS can import during read-only CI sync.
The private signing repository encrypts this package at rest. A failed
conversion exits before writing to the signing repository and removes
the temporary keychain and files. Do not send the `.p12` password in chat.

Normal desktop builds and GitHub Actions use read-only `match` retrieval, as
the iOS workflow does. GitHub Actions can use the existing read-only deploy
key scoped to this signing repository; write access is needed only for the
local one-time import.

After the encrypted import is verified:

1. Remove the temporary CSR, `.cer`, and exported `.p12`.
2. Keep the certificate/private key in the protected macOS keychain.
3. Confirm read-only match retrieval into a clean temporary keychain.
4. Record the certificate identifier and expiration date, but never its
   private key or passwords.

If the Account Holder prefers the agent to prepare the exact interactive match
command, first confirm that the certificate appears under **My Certificates**
with its private key. No write-enabled match action should run before that
confirmation.

## Requirement questions and human decisions

1. **RESOLVED HUMAN JUDGMENT — Public binary hosting:** On September 29,
   2026, the user selected the existing CLI private-S3/CloudFront download
   infrastructure and approved using the same
   `download.crystallattice.dev` subdomain when possible. Desktop files use
   the separate `crystal-lattice-desktop` prefix. No public source repository,
   new domain, new bucket, or new distribution is required.
2. **HUMAN JUDGMENT — App Transport Security:** The current app permits
   arbitrary network loads so users can connect to self-hosted HTTP runtimes.
   Before release, decide whether `0.9.0` must preserve arbitrary HTTP
   destinations or may narrow this to local-network/HTTPS behavior. The agent
   must document the concrete compatibility and security consequences before
   requesting the decision. Do not silently remove required self-hosted
   connectivity or retain an unnecessarily broad exception.
3. **HUMAN — MANDATORY — Developer ID certificate:** The Apple Developer
   Account Holder must create or authorize use of a valid Developer ID
   Application certificate for team `73Q43R2PD4` when no suitable certificate
   and private key already exist. The agent must not create, revoke, rotate, or
   replace Developer ID certificates without explicit confirmation.
4. **RESOLVED HUMAN JUDGMENT — Intel acceptance:** On September 29, 2026, the
   user removed a real Intel Mac from the pre-release acceptance gate.
   Automated slice and signing validation remains mandatory. Initial tester
   feedback supplies later real-hardware evidence, and any Intel-specific
   failure becomes release follow-up rather than being silently ignored.
5. **HUMAN JUDGMENT — Release publication:** A human must approve the exact
   source commit, version, build number, release notes, and checksums before the
   CloudFront download is made public.
6. **HUMAN JUDGMENT — Website publication:** A human must approve the download
   icon's final placement and visible/accessible presentation and confirm that
   the public release should be linked from the production website.

## Research and supporting facts

- Direct distribution outside the Mac App Store requires an appropriate
  Developer ID signature. Apple's notarization guidance requires valid code
  signing, Hardened Runtime for modern software, a secure timestamp, correctly
  formatted entitlements, and avoidance of development entitlements such as
  `get-task-allow`.
- Apple's notarization service accepts UDIF disk images. The final distribution
  container should be submitted with `notarytool`, the resulting log reviewed,
  and the ticket stapled and validated for reliable offline Gatekeeper
  behavior.
- Apple currently states that Developer ID Application and Developer ID
  Installer certificate creation requires the Account Holder role. Only the
  Application certificate is needed for this app-only DMG.
- Fastlane `match` supports `developer_id`; routine CI use should be read-only.
  Current Fastlane guidance states that Developer ID renewal cannot rely on an
  App Store Connect API key alone, so creation/renewal remains a controlled
  Account Holder operation rather than a CI responsibility.
- GitHub-hosted macOS image names, architectures, installed Xcode versions,
  and preview/stable status change over time. Execution must verify the
  selected runner and Xcode against the official runner-images inventory
  rather than assuming a label from this September 28, 2026 plan.
- Current project inspection on September 28, 2026 found:
  - Release resolves `arm64 x86_64` with `ONLY_ACTIVE_ARCH = NO`.
  - Hardened Runtime is enabled.
  - Release still uses Apple Development signing.
  - Product name and bundle ID still contain React Native template values.
  - Xcode declares macOS 12.4 while the Podfile declares macOS 14.0.
  - The AppIcon asset catalog has declarations but no image files.
  - `Info.plist` hard-codes version `1.0` and build `1`.
  - A privacy manifest is included.
  - An App Sandbox entitlement file exists but is not assigned through
    `CODE_SIGN_ENTITLEMENTS`.
  - The active login keychain has Apple Development and Apple Distribution
    identities but no Developer ID Application identity.
  - The desktop package has no committed `Gemfile.lock` or Fastlane
    configuration.
  - The macOS Pod lockfile records CocoaPods `1.16.2`.

Primary references to recheck during execution:

- Apple notarization:
  https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution
- Apple custom notarization workflow:
  https://developer.apple.com/documentation/security/customizing-the-notarization-workflow
- Apple Developer ID certificates:
  https://developer.apple.com/help/account/certificates/create-developer-id-certificates
- Apple Hardened Runtime:
  https://developer.apple.com/documentation/xcode/configuring-the-hardened-runtime
- Fastlane `match`:
  https://docs.fastlane.tools/actions/match/
- Fastlane `build_mac_app`:
  https://docs.fastlane.tools/actions/build_mac_app/
- GitHub-hosted runners:
  https://docs.github.com/actions/reference/runners/github-hosted-runners
- GitHub runner image inventory:
  https://github.com/actions/runner-images
- GitHub Actions security hardening:
  https://docs.github.com/actions/security-guides/security-hardening-for-github-actions

## Release contract

- Product name: `Crystal Lattice Desktop`
- Marketing version: `0.9.0`
- Bundle ID:
  `com.dynamicprogrammingsolutions.crystallatticecontrol.macos`
- Apple team: `73Q43R2PD4`
- Minimum system: macOS 14.0
- App architectures: `arm64` and `x86_64` in one application
- Distribution: direct download outside the Mac App Store
- Release container: app-only UDIF DMG
- Signing identity: Developer ID Application
- Notarization client: `xcrun notarytool`
- Release tag: `crystal-lattice-desktop-v0.9.0`
- DMG name:
  `Crystal-Lattice-Desktop-v0.9.0-universal.dmg`
- Checksum name:
  `Crystal-Lattice-Desktop-v0.9.0-universal.dmg.sha256`
- Public hosting: existing private S3 origin and CloudFront distribution at
  `https://download.crystallattice.dev/crystal-lattice-desktop`
- Website link:
  `https://download.crystallattice.dev/crystal-lattice-desktop/Crystal-Lattice-Desktop-v0.9.0-universal.dmg`
- CLI payload: none
- Automatic updates: none

**Publication design correction:** The GitHub repository is private, so its
release assets cannot satisfy anonymous downloads. The user approved the
existing CLI download CDN with a desktop-specific prefix instead.

The CI build number must be an integer. Prefer an explicitly supplied
`MACOS_BUILD_NUMBER`; otherwise use a documented value derived from
`GITHUB_RUN_NUMBER`. The selected number must be printed in non-secret logs,
embedded as `CFBundleVersion`, included in release metadata, and kept
consistent across the archive, DMG, checksum manifest, and acceptance record.

## Credential and security boundary

Tracked files may contain names of variables and non-secret defaults only.
They must never contain private keys, API key content, match passwords,
keychain passwords, deploy keys, or exported certificate packages.

GitHub repository secrets and variables are used. The organization is on
GitHub Free with a private application repository, so this release does not
claim an environment approval or required-reviewer gate.

Expected non-secret variables (reuse the existing matching iOS values where
appropriate):

- `IOS_APPLE_TEAM_ID`
- `IOS_MATCH_GIT_URL`
- `IOS_MATCH_GIT_BRANCH`

Expected existing encrypted repository secrets:

- `IOS_APP_STORE_CONNECT_KEY_ID`
- `IOS_APP_STORE_CONNECT_ISSUER_ID`
- `IOS_APP_STORE_CONNECT_KEY_CONTENT`
- `IOS_MATCH_PASSWORD`
- `IOS_MATCH_GIT_PRIVATE_KEY`
- `CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME`

Expected existing download variables:

- `AWS_REGION`
- `CLI_DOWNLOADS_BUCKET`
- `CLI_DOWNLOADS_PREFIX`
- `CLI_DOWNLOADS_BASE_URL`
- `CLI_DOWNLOADS_CLOUDFRONT_DISTRIBUTION_ID`

Expected added non-secret download variables:

- `DESKTOP_DOWNLOADS_PREFIX=crystal-lattice-desktop`
- `DESKTOP_DOWNLOADS_BASE_URL=https://download.crystallattice.dev/crystal-lattice-desktop`

Equivalent existing secrets may be reused only when their permissions and
ownership are appropriate for the desktop release. Do not duplicate secret
values merely to satisfy naming preferences.

The App Store Connect key is used for notarization authentication. The private
signing repository stores encrypted signing material. Its CI deploy key must
be read-only. The GitHub workflow must create an ephemeral keychain, import
the signing identity through read-only synchronization, limit key access to
the required Apple tools, and delete temporary key, keychain, and API-key
files under an `always()` cleanup step.

The publication job alone may receive `id-token: write` to assume the existing
download role. It does not need repository write access. Build and
verification jobs use `contents: read`. Repository checkout credentials must
not persist. Third-party GitHub Actions must be pinned to full commit SHAs.
Pull requests and untrusted forks must never gain signing or publication
credentials. The AWS role remains prefix-scoped to CLI and desktop download
objects plus invalidation of the one existing distribution.

## Execution plan
Status: Approved

Execute this plan only after the user approves it. Work in the existing
`main`-branch worktree. Preserve unrelated work and do not edit the broader
macOS distribution task. Implement the local release path first, prove it
through the credential and notarization boundary, then reproduce it in GitHub
Actions. Publish the website icon only after the release candidate has passed
both architecture acceptance boundaries.

### Phase 1 — Reconfirm the release baseline

1. **AGENT:** Confirm `main` is clean enough for the scoped work and record the
   starting commit.
2. **AGENT:** Read current desktop package guidance and inspect the workspace,
   scheme, target, Podfile, lockfiles, asset catalogs, entitlements,
   `Info.plist`, privacy manifest, Release bundle script, and native
   dependencies.
3. **AGENT:** Recheck the official Apple, Fastlane, GitHub Actions, and
   runner-image references listed above. Record changed constraints in
   Implementation Notes before changing the plan.
4. **AGENT:** Run `xcodebuild -list` and Release
   `xcodebuild -showBuildSettings` against the checked-in workspace and shared
   scheme.
5. **AGENT:** Confirm that the production Release path bundles JavaScript and
   does not require Metro.
6. **AGENT:** Audit Mach-O architecture support in the app and all native
   dependencies. Treat any required dependency without both `arm64` and
   `x86_64` support as a release blocker rather than silently dropping Intel.
7. **AGENT:** Record the exact compatible Xcode, macOS SDK, Node, Ruby,
   Bundler, CocoaPods, and Fastlane versions selected for local and CI use.

### Phase 2 — Production identity, metadata, icon, and security posture

1. **AGENT:** Set Release product/display/menu naming to
   `Crystal Lattice Desktop` while preserving internal React Native module
   identifiers unless changing them is required for correct packaging.
2. **AGENT:** Set the Release app bundle ID, team, marketing version, build
   version source, and minimum macOS target from the release contract.
3. **AGENT:** Replace hard-coded `Info.plist` version values with the selected
   Xcode build settings so one source controls version and build.
4. **AGENT:** Generate every required macOS AppIcon representation
   reproducibly from an approved existing Crystal Lattice icon source. Keep
   the source and generation command identifiable.
5. **AGENT:** Reuse the exact approved iOS application icon artwork and verify
   the generated macOS representations in Dock, Finder, and About. No
   additional human visual approval is required when the artwork is unchanged.
   If implementation cannot reuse the same artwork exactly, stop and request
   human visual approval before substituting or modifying it.
6. **AGENT:** Verify that the privacy manifest and required resources are
   packaged in Release.
7. **AGENT:** Keep Hardened Runtime enabled. Do not add broad runtime
   exceptions preemptively. Add only an entitlement required by a demonstrated
   Release runtime failure and document why it is necessary.
8. **AGENT:** Audit the unused App Sandbox entitlement file. App Sandbox is not
   required for this direct release and must not be enabled merely because the
   file exists. If enabling it is proposed, stop for a separate compatibility
   and security decision.
9. **AGENT:** Test whether App Transport Security can be narrowed while
   preserving approved self-hosted connection behavior. Provide the exact
   successful and failing connection matrix.
10. **HUMAN JUDGMENT:** Decide the App Transport Security policy using the
    agent's compatibility/security evidence.
11. **AGENT:** Verify that Release entitlements exclude `get-task-allow`,
    unnecessary library validation exceptions, unnecessary unsigned
    executable memory, and unrelated Apple capabilities.
12. **AGENT:** Run desktop TypeScript, Jest, focused native launch/UI, and
    connection checks after identity changes.

### Phase 3 — Reproducible local toolchain and Fastlane lanes

1. **AGENT:** Add a package-local `.ruby-version`, exact Bundler dependencies,
   and committed `Gemfile.lock`. Initial compatibility candidates are Ruby
   `3.4.10`, CocoaPods `1.16.2`, and Fastlane `2.240.1`; adjust a candidate only
   for a demonstrated compatibility issue and record the evidence.
2. **AGENT:** Ensure a clean checkout can run `npm ci`, `bundle install`, and
   `bundle exec pod install --project-directory=macos`.
3. **AGENT:** Add package-local Fastlane configuration and a non-secret
   `.env.example`.
4. **AGENT:** Implement `mac verify` to run:
   - Fastlane helper/unit tests;
   - TypeScript checking;
   - desktop Jest tests appropriate to a release;
   - Release configuration/build-setting validation;
   - selected native smoke verification that does not need credentials.
5. **AGENT:** Implement `mac build` to create a clean, credential-free
   universal Release archive or app suitable for inspecting JavaScript
   bundling, metadata, architectures, resources, dependency paths, and
   pre-signing failures.
6. **AGENT:** Implement a build-number resolver covering explicit local input
   and GitHub Actions input, with automated tests.
7. **AGENT:** Implement `mac setup_signing` as an explicitly write-enabled,
   local-only signing bootstrap. It must never run automatically in CI.
8. **AGENT:** Implement `mac release` as the single local source of truth for:
   - release verification unless explicitly and safely skipped by an already
     successful CI verification job;
   - read-only Developer ID signing retrieval;
   - controlled local/CI keychain setup;
   - clean universal Release archive/export;
   - strict nested code-signature inspection;
   - staging the app plus an `/Applications` symlink;
   - creating the UDIF DMG with native `hdiutil` unless a third-party tool is
     demonstrably necessary;
   - signing the final distribution container where applicable;
   - `notarytool submit --wait`;
   - saving and reviewing notarization status/log output;
   - stapling and validating the accepted ticket;
   - Gatekeeper assessment;
   - SHA-256 checksum and machine-readable release metadata generation.
9. **AGENT:** Use app-relative absolute paths so Fastlane works regardless of
   whether invocation starts from the package root or `fastlane/`.
10. **AGENT:** Disable Fastlane anonymous usage reporting.
11. **AGENT:** Ignore local `.env`, API keys, Fastlane reports, archives,
    DerivedData, temporary keychains, notarization credentials, and release
    output while keeping templates and deterministic metadata sources tracked.

### Phase 4 — Developer ID signing bootstrap

1. **AGENT:** List current signing identities and certificate expiration
   metadata without printing private material.
2. **AGENT:** Inspect the private signing repository only through commands that
   do not expose decrypted private keys or secret values.
3. **AGENT:** Determine whether a valid Developer ID Application certificate
   and paired private key for team `73Q43R2PD4` already exist.
4. **HUMAN — MANDATORY:** If absent, the Account Holder creates or authorizes
   creation of one Developer ID Application certificate. No Developer ID
   Installer certificate is needed.
5. **AGENT + HUMAN:** Import the resulting identity into a controlled local
   keychain and encrypted signing repository. The human supplies credentials
   through local secure entry or GitHub's secret interface; credentials must
   not be pasted into task files, chat, shell history, or tracked files.
6. **AGENT:** Verify read-only `match(type: "developer_id")` retrieval into a
   clean temporary keychain.
7. **AGENT:** Verify App Store Connect API-key authentication with
   `notarytool`. Stop and report the exact role or authorization error if Apple
   rejects the existing key.
8. **AGENT:** Sign a controlled app build and verify the Developer ID
   certificate chain, team identifier, secure timestamp, Hardened Runtime, and
   entitlements.
9. **HUMAN JUDGMENT:** Approve continued use of the selected Developer ID
   identity and its expiration/renewal plan before public release.

### Phase 5 — First local signed, notarized universal DMG

1. **AGENT:** Run the complete local Fastlane release lane with version
   `0.9.0` and an explicit build number.
2. **AGENT:** Verify `arm64` and `x86_64` slices in the main executable and
   every required bundled native binary.
3. **AGENT:** Verify the final app name, bundle ID, team, version, build,
   minimum macOS version, resources, privacy manifest, JavaScript bundle,
   entitlements, dependency load paths, and absence of development-only
   content.
4. **AGENT:** Run strict `codesign`, `spctl`, `notarytool`, and `stapler`
   validation and retain bounded diagnostic evidence.
5. **AGENT:** Mount the DMG, confirm it contains only the application and the
   Applications shortcut, copy the app to a temporary Applications-equivalent
   location, and launch it without Metro.
6. **AGENT:** Exercise a focused connection/session/message/relaunch smoke flow
   against a separately started self-hosted runtime.
7. **HUMAN JUDGMENT:** Inspect Finder, mounted-DMG presentation, icon, native
   menus, first-launch Gatekeeper presentation, and basic interaction on Apple
   Silicon.
8. **AGENT:** Record the DMG size, SHA-256 checksum, notarization submission
   ID, accepted status, source commit, tool versions, and local acceptance
   results.

### Phase 6 — Manual GitHub Actions release automation

1. **AGENT:** Add a dedicated desktop release workflow with:
   - a manual build-only dispatch path;
   - a separately authorized manual publication path tied to the exact
     reviewed release-candidate artifact and source commit;
   - concurrency that prevents overlapping desktop releases;
   - explicit timeouts;
   - repository secrets already used by the iOS workflow, without a
     required-reviewer environment;
   - current supported macOS runner and Xcode selection validated against the
     official runner image;
   - exact Node/Ruby/CocoaPods/Fastlane setup from the local lockfiles;
   - `npm ci` and deterministic Pod installation;
   - verification before secret-bearing signing work;
   - ephemeral keychain setup;
   - read-only match access;
   - Fastlane `mac release`;
   - unconditional cleanup.
2. **AGENT:** Pin all third-party actions to full commit SHAs and disable
   persisted checkout credentials.
3. **AGENT:** Separate CDN publication into a job whose only elevated
   permission is AWS OIDC `id-token: write`.
4. **AGENT:** Upload the DMG, checksum, notarization summary, and release
   metadata as short-retention workflow artifacts for build-only runs.
5. **AGENT:** On an explicitly selected manual dispatch, publish the verified
   versioned DMG, checksum, release metadata, and notarization result under
   the existing CloudFront host's `crystal-lattice-desktop` prefix and update
   that prefix's `latest.txt`.
6. **AGENT:** Validate asset count, names, checksum, version, build, source
   commit, signatures, and notarization before release publication.
7. **AGENT:** Confirm the existing GitHub repository variables, secrets, and
   read-only signing-repository deploy key are sufficient for desktop signing.
   **HUMAN — MANDATORY** only if an unavailable credential must be created
   through GitHub's secure interface.
8. **AGENT:** Run a build-only workflow and verify successful cleanup and
   secret masking.
9. **AGENT:** Compare the CI artifact with the local release contract and
   validation results.
10. **HUMAN JUDGMENT:** Approve the exact release source commit, version,
    build, assets, checksum, and Apple Silicon candidate acceptance before
    enabling CDN publication.
11. **HUMAN — MANDATORY:** Explicitly dispatch the workflow with
    `publish_download = true`. There is no GitHub required-reviewer gate.
12. **AGENT:** Monitor build, signing, notarization, publication, and cleanup.
    Record the workflow run, tag, release URL, artifact URL, checksum,
    notarization result, and any warning requiring action.

### Phase 7 — Public artifact acceptance on both architectures

1. **AGENT:** Download the DMG through the public versioned CloudFront URL,
   not from a local build directory or internal workflow artifact.
2. **AGENT:** Verify the published checksum and rerun signature, Gatekeeper,
   notarization, stapling, metadata, resource, and architecture inspection.
3. **AGENT + HUMAN:** On a clean or release-clean Apple Silicon environment,
   install through Finder, observe Gatekeeper, launch, connect to a separately
   running runtime, exercise sessions/messages and relevant file flows, quit,
   relaunch, and confirm persisted settings/state.
4. **AGENT:** Record Apple Silicon acceptance and automated `x86_64` slice
   evidence. Collect real Intel feedback from initial testers after
   publication when available.
5. **HUMAN JUDGMENT:** Accept or reject the release based on Apple Silicon
   behavior and the automated universal checks. Any unresolved signing,
   notarization, launch, connection, data-loss, or architecture problem found
   before publication remains a blocker.

### Phase 8 — Website download icon after release acceptance

1. **AGENT:** Add one maintained desktop release metadata source under the
   landing-page authored sources containing the accepted version, exact
   versioned HTTPS DMG URL, supported macOS version, universal architecture,
   and SHA-256 checksum.
2. **AGENT:** Add a small download-icon link to the shared website header near
   the existing theme/GitHub controls.
3. **AGENT:** Give the link an accessible name such as
   `Download Crystal Lattice Desktop for macOS`, visible focus styling, and an
   ordinary link destination that works without JavaScript.
4. **AGENT:** Do not use browser architecture detection and do not imply that
   the DMG installs the CLI.
5. **AGENT:** Ensure the icon remains usable in desktop and mobile header
   layouts and does not displace required navigation.
6. **AGENT:** Add focused content/link tests that fail for missing release
   metadata, a non-HTTPS URL, an unexpected filename, or an absent accessible
   name.
7. **AGENT:** Run landing-page analytics/content tests, production build,
   responsive checks, keyboard/semantic accessibility checks, and a real
   download/checksum verification.
8. **HUMAN JUDGMENT:** Review and approve the icon placement, affordance, and
   public copy.
9. **HUMAN — MANDATORY:** Approve production website publication.
10. **AGENT:** After explicit publication authorization, use the existing
    protected static-site deployment path and verify the production header
    link downloads the accepted DMG with the displayed checksum.

### Phase 9 — Closeout and future task reconciliation evidence

1. **AGENT:** Update current desktop user documentation with supported macOS,
   universal architecture, installation, Gatekeeper expectations, checksum
   verification, self-hosted runtime requirement, and the fact that the DMG
   does not install the CLI.
2. **AGENT:** Add maintainer documentation for Fastlane lanes, toolchain setup,
   signing bootstrap, GitHub variables/secrets by name, workflow operation,
   build-number rules, notarization diagnostics, renewal, rollback, and
   release recovery.
3. **AGENT:** Record a concise crosswalk in this task's Completion Notes
   identifying which outcomes overlap the untouched broader macOS distribution
   task, which were deliberately skipped, and which remain future work.
4. **AGENT:** Do not edit the broader macOS task during this task.
5. **AGENT:** Append immutable Completion Notes only after every requirement
   has evidence or is explicitly recorded as incomplete.

### Implementation decisions and open questions

- Decision: produce one universal app-only DMG; do not create PKGs.
- Decision: ship both Apple Silicon and Intel slices. Require Apple Silicon
  human acceptance and automated universal validation before publication;
  defer real Intel hardware feedback to initial testers.
- Decision: use Fastlane as the local source of truth and have GitHub Actions
  invoke the same lane rather than duplicate release shell logic.
- Decision: use Developer ID Application signing only.
- Decision: use a read-only signing path in CI and keep signing
  bootstrap local and write-enabled only by explicit action.
- Decision (2026-09-29, user): use manual-only GitHub Actions publication with
  repository secrets and explicit release approval; required reviewers and
  a protected environment are not required.
- Decision: use App Store Connect API-key authentication for notarization; do
  not use an Apple password or interactive 2FA session in CI.
- Decision: publish under the existing private-S3/CloudFront download host at
  the desktop-specific prefix and use the exact versioned CDN URL on the
  website.
- Decision: add only a header download icon, not a full desktop page.
- Decision: desktop maintains its own `latest.txt` under
  `crystal-lattice-desktop`; it does not affect the CLI prefix.
- Decision: keep App Sandbox out of this release unless separately proposed
  and approved after compatibility evidence.
- Open human decision: final App Transport Security policy.
- Open human dependency: Account Holder Developer ID certificate action.
- Open human decision: release publication approval.
- Open human decision: website icon and production publication approval.

### Documentation

- Update `desktop/crystal-lattice-control-desktop-rn/README.md` with a concise
  installation/release entry point.
- Add detailed release-maintainer guidance under
  `desktop/crystal-lattice-control-desktop-rn/docs/development/` and link it
  from the development index.
- Add or update focused desktop installation guidance under
  `desktop/crystal-lattice-control-desktop-rn/docs/` if the README would become
  unwieldy.
- Keep public download metadata and icon behavior in authored
  `landing_page/` sources.
- Update `landing_page/README.md` only if maintainers need a new release
  metadata input or build requirement.
- Do not edit generated `docs_site/prepared/`, `docs_site/dist/`,
  `landing_page/dist/`, Xcode archives, DMGs, DerivedData, or generated
  notarization output directly.
- Public documentation must describe delivered behavior and must not mention
  task phases, task numbers, approval state, match passwords, key paths, or
  internal secret storage.

### Task checklist

- [x] **AGENT:** Complete the current-guidance and repository preflight.
- [x] **AGENT:** Finalize production identity, metadata, icon, target, and
      version/build sources.
- [x] **AGENT + HUMAN JUDGMENT:** Resolve the App Transport Security policy.
- [x] **AGENT:** Establish the pinned local Ruby/Fastlane/CocoaPods release
      toolchain.
- [x] **AGENT:** Implement and test `mac verify`, `mac build`,
      `mac setup_signing`, and `mac release`.
- [x] **HUMAN — MANDATORY:** Supply or authorize the Developer ID Application
      certificate boundary (G2 certificate created and paired private key
      exported; encrypted match import remains pending).
- [x] **AGENT:** Verify read-only signing retrieval and notarization
      authentication.
- [ ] **AGENT + HUMAN JUDGMENT:** Produce and accept the first local signed,
      notarized, stapled universal DMG.
- [x] **AGENT:** Implement the manual GitHub Actions desktop release
      workflow.
- [x] **AGENT + HUMAN as needed:** Confirm the existing GitHub variables,
      secrets, and read-only deploy key; create new credentials only if needed.
- [x] **AGENT:** Complete a successful build-only workflow.
- [ ] **HUMAN JUDGMENT:** Approve the release source, version, build, notes,
      assets, and checksums.
- [ ] **AGENT + HUMAN:** Publish and verify the versioned CloudFront download.
- [ ] **AGENT + HUMAN:** Complete Apple Silicon public-artifact acceptance.
- [x] **HUMAN JUDGMENT:** Defer real Intel hardware acceptance to initial
      tester feedback while retaining mandatory automated `x86_64` checks.
- [ ] **HUMAN JUDGMENT:** Accept the release for public universal download.
- [ ] **AGENT:** Add and test the website download metadata and header icon.
- [ ] **HUMAN JUDGMENT:** Approve the icon placement and presentation.
- [ ] **HUMAN — MANDATORY:** Approve production website publication.
- [ ] **AGENT:** Deploy through the existing protected site workflow and
      verify the production download.
- [ ] **AGENT:** Complete user/maintainer documentation and the future
      reconciliation crosswalk without modifying the broader macOS task.

### Requirement verification

- Universal DMG requirement:
  - Inspect the main executable and every required native binary with `lipo`,
    `file`, or equivalent and prove both `arm64` and `x86_64` slices.
  - Verify the published DMG on Apple Silicon and retain initial tester
    feedback as follow-up evidence for real Intel hardware.
- Product identity requirement:
  - Inspect the built app's `Info.plist`, resolved Xcode settings, native menus,
    Finder name, icon, bundle identifier, version/build, team, and deployment
    target.
- Standalone Release requirement:
  - Launch the installed app with Metro stopped and without a source checkout.
  - Exercise a focused real self-hosted connection/session/message flow.
- Signing/security requirement:
  - Run strict `codesign` verification on the app and nested code.
  - Inspect certificate chain, team, secure timestamp, Hardened Runtime, and
    entitlements.
  - Confirm `get-task-allow` and unjustified runtime exceptions are absent.
- Notarization requirement:
  - Record an accepted `notarytool` submission and review its log.
  - Run `stapler validate` and Gatekeeper assessment against the final DMG/app.
- Fastlane requirement:
  - `bundle check`, `bundle exec fastlane --version`, and
    `bundle exec fastlane lanes` pass.
  - Fastlane helper tests and credential-free verify/build lanes pass.
  - The signed release lane completes with controlled credentials.
- GitHub Actions requirement:
  - A successful run from the approved source commit performs verification,
    ephemeral-keychain signing, notarization, cleanup, and release publication.
  - Logs are inspected for secret masking and contain no private material.
  - The downloaded release checksum matches CI-generated metadata.
- Public release requirement:
  - The exact versioned public URL returns the expected DMG.
  - Asset filename, version, build, checksum, source commit, signature, and
    notarization records agree.
- Human architecture acceptance requirement:
  - A named human records installation, Gatekeeper, launch, smoke flow, and
    relaunch results on Apple Silicon. Initial testers report Intel behavior
    after publication when available.
- Website requirement:
  - Production HTML contains an accessible macOS download link.
  - Keyboard and responsive behavior pass.
  - The production link downloads the accepted versioned DMG and its checksum
    matches the displayed/maintained value.
- Existing-task preservation requirement:
  - `git diff` confirms no files under
    `tasks/20260820-macos-desktop-distribution/` changed during this task.
- Documentation requirement:
  - Package and landing builds pass and current documentation agrees with the
    released artifact and workflow.

### Additional implementation verification

- Verify there are no unexpected absolute non-system library paths with
  `otool -L`.
- Verify no generated archive, DMG, API key, keychain, `.env`, notarization
  credential, or decrypted signing file is tracked.
- Verify the app does not gain a CLI payload or terminal installation side
  effect.
- Verify installation/reinstallation preserves user-owned connection and
  session state.
- Verify the DMG remains valid after downloading on another machine and that
  moving the app out of the mounted DMG does not alter its signature.
- Verify offline launch after ticket stapling and one successful online
  installation.
- Verify a controlled verification failure prevents signing and publication.
- Verify a controlled publication precondition failure leaves no partial
  public release.
- Verify the workflow cleans temporary deploy keys, API-key files, and
  keychains under success and failure.
- Verify action pins, workflow permissions, environment protections,
  concurrency, timeouts, and artifact retention against repository policy.
- Record certificate expiration and a renewal lead time without exposing
  private certificate material.
- Record GitHub-hosted runner image, architecture, Xcode version, workflow
  duration, and any preview-image risk observed during the successful release.

## Implementation Notes

Execution began on September 28, 2026 in the existing `main` worktree from
merge commit `467e160240aff876ff0e536eb8309a87cf8af393`.

### Phase 1 findings

- Rechecked current Apple notarization, Developer ID, Fastlane `match`, GitHub
  Actions security, and hosted-runner guidance from the primary references
  listed in this task.
- Local release environment:
  - macOS `26.5.2`, Apple Silicon;
  - Xcode `26.1` / build `17B55`;
  - macOS SDK `26.1`;
  - Node `20.19.5`;
  - Ruby `3.4.10`;
  - Bundler `4.0.15`;
  - CocoaPods `1.16.2`;
  - Fastlane `2.240.1`.
- Clean `npm ci` completed. It reported 23 total npm audit findings before
  filtering development dependencies.
- `npm audit --omit=dev` reported 19 findings: 1 low, 8 moderate, 10 high, and
  0 critical.
  - Several high findings are in build/tooling chains such as Metro, Babel,
    glob, and YAML processing.
  - Runtime Markdown dependencies are also affected:
    `react-native-markdown-display@7.0.2` resolves
    `markdown-it@10.0.0` and `linkify-it@2.2.0`;
    `react-syntax-highlighter@6.1.2` resolves `highlight.js@9.12.0` and
    `lowlight@1.9.2`.
  - The runtime dependency upgrades are major-version changes with no
    automatic compatible fix reported by npm. No forced audit fix or
    unverified override was applied.
- The tracked Pod lock was stale only for Hermes:
  - package lock resolves React Native `0.81.6` and React Native macOS
    `0.81.8`;
  - the Pod lock still recorded Hermes `0.81.5`;
  - focused `pod update hermes-engine --no-repo-update` updated Hermes to
    `0.81.6` and clean CocoaPods installation then completed.
- CocoaPods emitted existing React Native deprecation/output warnings but no
  dependency installation error after the focused lock update.

### Phase 2 implementation

- Release product name is now `Crystal Lattice Desktop`.
- Release bundle ID remains the approved
  `com.dynamicprogrammingsolutions.crystallatticecontrol.macos`.
- Release metadata resolves:
  - marketing version `0.9.0`;
  - build number `1`;
  - minimum macOS `14.0`;
  - architectures `arm64 x86_64`;
  - Hardened Runtime enabled;
  - Developer ID Application / manual signing selected for Release.
- Debug keeps Apple Development signing so local native UI tests remain
  buildable.
- The React Native module/target/project identifiers remain internal and
  unchanged.
- Finder, application-menu, About, Hide, Quit, Help, and test expectations now
  use `Crystal Lattice Desktop`.
- `Info.plist` now takes marketing/build versions from Xcode settings.
- The React Native bundle phases no longer contain a developer-specific
  absolute Node path. They resolve `NODE_BINARY` from the environment/PATH and
  fail with an actionable message when Node is unavailable.
- The macOS icon set is generated reproducibly from the approved iOS
  1024-by-1024 icon.
  - iOS source SHA-256:
    `3f65bd81b0f8a7e134dbf7d13294c614252913a547978d43a3eee8789abeb7da`
  - macOS 1024-by-1024 output SHA-256:
    `3f65bd81b0f8a7e134dbf7d13294c614252913a547978d43a3eee8789abeb7da`
  - The exact source bytes are preserved at the largest macOS representation;
    smaller representations are generated with `sips`.
- The Release target does not assign the existing App Sandbox entitlement
  file. Resolved Release settings show no `CODE_SIGN_ENTITLEMENTS` and no JIT,
  unsigned-executable-memory, library-validation, debugger, or DYLD runtime
  exception.
- The privacy manifest remains packaged.
- App Transport Security was reviewed and the user selected the narrower
  local-network/HTTPS policy:
  - current `Info.plist` has `NSAllowsArbitraryLoads = true`;
  - the desktop connection implementation accepts only manual records and
    always constructs `http://host:port`;
  - Apple's macOS 14 local-network ATS exception can cover local hosts/IP
    addresses, but narrowing to it would intentionally block remote plaintext
    HTTP hosts;
  - implementation is intentionally deferred until the requested UI
    automation repair is complete.

### Phase 3 implementation and verification

- Added package-local Ruby/Fastlane configuration:
  - `.ruby-version` `3.4.10`;
  - exact CocoaPods `1.16.2`, xcodeproj `1.27.0`, and Fastlane `2.240.1`;
  - committed-source `Gemfile.lock`;
  - non-secret `.env.example`;
  - `Appfile`, `Matchfile`, and `Fastfile`.
- Added lanes:
  - `mac verify`;
  - `mac build`;
  - `mac setup_signing`;
  - `mac release`.
- Added a tested build-number resolver:
  - explicit `MACOS_BUILD_NUMBER`;
  - otherwise `GITHUB_RUN_NUMBER`;
  - otherwise local default `1`;
  - positive integer validation.
- Added release verification for product identity, version/build, macOS 14,
  JavaScript bundle, privacy manifest, and universal Mach-O slices.
- Added signed-release scaffolding for:
  - read-only Developer ID `match`;
  - controlled CI keychain setup;
  - universal signed archive;
  - app and Applications-symlink DMG staging;
  - native `hdiutil` DMG creation;
  - Developer ID DMG signing;
  - App Store Connect API-key `notarytool submit --wait`;
  - notarization JSON retention;
  - stapling, Gatekeeper, checksum, and release metadata.
- `bundle check`: passed.
- `bundle exec fastlane --version`: Fastlane `2.240.1`.
- `bundle exec fastlane lanes`: all four macOS lanes listed.
- Build-number tests: 6 runs / 8 assertions passed.
- The merged desktop tree initially had TypeScript errors unrelated to release
  metadata. They were corrected rather than excluded:
  - React Native's incomplete ambient `URL` typing at the bridge URL boundary;
  - rich session-action state declaration order;
  - required attachment owner/plugin validation;
  - use of a nonexistent `Theme.shadow` field.
- `npm run tsc`: passed after those corrections.
- Desktop Jest: 41 suites / 194 tests passed. Existing non-failing React
  `act(...)` warnings remain in human-time telemetry tests.
- Frontend SDK Vitest: 48 files / 349 tests passed.
- `bundle exec fastlane mac verify`: passed.
- `bundle exec fastlane mac build`: passed.
  - `xcodebuild archive` succeeded without production credentials.
  - Archive app:
    `build/macos-release/CrystalLatticeDesktop.xcarchive/Products/Applications/Crystal Lattice Desktop.app`
  - App size: approximately 26 MB.
  - App executable: universal `x86_64 arm64`.
  - Embedded Hermes framework: universal `x86_64 arm64`.
  - Inspector verified 2 universal Mach-O files.
  - Metadata reports `Crystal Lattice Desktop`, the approved bundle ID,
    `0.9.0 (1)`, and macOS 14.0.
  - `main.jsbundle`, `PrivacyInfo.xcprivacy`, compiled `Assets.car`, and
    Feather font are packaged.
  - Load-command inspection found only system libraries/frameworks and the
    expected `@rpath` Hermes framework.
  - The unsigned Release application launched successfully for five seconds
    with Metro disabled.
- `SKIP_DESKTOP_VERIFICATION=true bundle exec fastlane mac release` stopped at
  the intended boundary with missing
  `DESKTOP_APP_STORE_CONNECT_KEY_ID` and
  `DESKTOP_APP_STORE_CONNECT_ISSUER_ID`; no signing or notarization operation
  was attempted.
- Focused macOS UI test status:
  - The first two Session Filters UI test invocations built and signed
    successfully but failed before test collection because XCTest timed out
    enabling macOS automation mode.
  - After the human-authenticated machine setup documented under
    `Local macOS UI automation setup`, the focused suite was rerun on
    September 29, 2026.
  - XCTest enabled Automation Mode automatically even though the pre-test
    status said `Automation Mode is disabled`.
  - Session Filters UI test result: 7 tests, 0 failures, passed in
    approximately 162 seconds.
  - Result bundle:
    `~/Library/Developer/Xcode/DerivedData/CrystalLatticeControlDesktopRN-cofvhxptimwfhybpfpzrkjptuvrp/Logs/Test/Test-CrystalLatticeControlDesktopRN-macOS-2026.09.29_10-23-35-+0200.xcresult`

### Pause before Phase 4

Execution is intentionally paused before Developer ID signing bootstrap.
No Developer ID certificate was created, imported, revoked, or changed. No
signing repository was accessed. No GitHub secret, environment, workflow, tag,
release, or public website state was changed.

Human decisions/actions required before continuation:

The user subsequently confirmed:

1. App Transport Security will be narrowed to local-network HTTP plus HTTPS.
2. Runtime Markdown/highlighting dependencies will be upgraded and tested
   before release.
3. The Apple Developer Account Holder is available for Developer ID
   Application certificate work.
4. The existing private signing repository and match password may be reused.
5. The existing App Store Connect team API key may be reused for
   `notarytool`.
6. The macOS UI automation failure must be resolved before any other release
   work continues.

UI automation investigation:

- Both focused UI test attempts built and signed the app and test runner.
- Exported XCTest diagnostics show:
  - `testmanagerd` accepted and authorized the runner process;
  - the runner loaded the selected UI test bundle;
  - the target application path and renamed bundle ID were resolved correctly;
  - initialization then waited exactly 60 seconds for
    `enabling automation mode` and timed out before test collection.
- Both the Debug app and UI test runner pass strict code-signature
  verification.
- `/usr/bin/automationmodetool` reports:
  - before human setup:
    `Automation Mode is disabled. This device requires user authentication to
    enable Automation Mode.`;
  - after the human-authenticated setup:
    `Automation Mode is disabled. This device DOES NOT REQUIRE user
    authentication to enable Automation Mode.`
- The post-setup output is successful: disabled is the current inactive state,
  while no-authentication-required is the persistent policy that lets the next
  XCTest session activate Automation Mode automatically.
- The administrator commands and rollback procedure are documented in
  `Local macOS UI automation setup` near the top of this task.
- On September 29, 2026 the next focused XCUITest session activated Automation
  Mode without an authentication prompt and passed all 7 selected tests.

### Accepted security follow-up implemented

- App Transport Security now permits local-network HTTP and HTTPS without the
  previous global arbitrary-load exception:
  - `NSAllowsLocalNetworking = true`;
  - the existing explicit localhost HTTP exception remains;
  - `NSAllowsArbitraryLoads` is absent;
  - the Release verifier fails if arbitrary loads return.
- The runtime Markdown stack was upgraded and verified:
  - `markdown-it` `10.0.0` → `15.0.2`;
  - `linkify-it` `2.2.0` → `6.1.0`;
  - `react-syntax-highlighter` `6.1.2` → `15.6.6`;
  - obsolete `react-native-syntax-highlighter` was replaced with a
    package-owned Highlight.js-only React Native adapter preserving native
    `Text`, font-size, and line-height behavior.
- The upgraded Markdown/linkification/highlighting runtime no longer appears
  in the production audit findings.
- Clean-install production audit after the upgrade reports:
  - 0 critical;
  - 7 high;
  - 5 moderate;
  - 1 low.
- Remaining findings are in Babel, Metro, Jest, glob/matching, YAML, image-size,
  and WebSocket tooling/development chains. No further broad or forced npm
  update was applied.
- Post-upgrade verification:
  - clean `npm ci`: passed;
  - TypeScript: passed;
  - Markdown renderer tests: 8 passed;
  - full desktop Jest: 41 suites / 194 tests passed;
  - `fastlane mac verify`: passed;
  - fresh universal `fastlane mac build`: passed;
  - Release ATS assertion and both universal Mach-O checks passed.

### Phase 4 read-only discovery

- Local keychain inventory still contains Apple Development and Apple
  Distribution identities, but no Developer ID Application or Developer ID
  Installer identity.
- The approved private signing repository was cloned read-only into a
  temporary directory and removed after inspection.
- Its encrypted contents currently contain:
  - one Apple Distribution `.cer`;
  - one Apple Distribution `.p12`;
  - one iOS App Store provisioning profile;
  - no Developer ID certificate material.
- The existing App Store Connect API private key:
  - exists with mode `0600`;
  - is owned by the current user;
  - successfully authenticated to `notarytool history`;
  - returned one previous notarization submission with status `Accepted`.
- No Apple certificate, keychain item, signing-repository content, GitHub
  secret, release, or public deployment was created or modified during these
  checks.
- Phase 4 initially awaited the Account Holder certificate creation and
  private-key export/import procedure documented under
  `Developer ID Application certificate setup`. Creation and export have
  since occurred; encrypted match import remains pending.

### iOS signing precedent checked before desktop import

- `tasks/20260614-ios-testflight-github-fastlane/070-fastlane-ios-testflight.md`
  records that `ios setup_signing` used App Store Connect API authentication
  and write-enabled `match` to create the Apple Distribution certificate and
  App Store provisioning profile on August 19, 2026. The encrypted
  certificate, `.p12`, and profile were pushed to the private
  `crystal-lattice-ios-signing` repository.
- `tasks/20260614-ios-testflight-github-fastlane/080-github-actions-ios-cd.md`
  records read-only SSH deploy-key access to that repository, read-only match
  synchronization, and an ephemeral CI keychain. The successful build-only
  workflow run was `32412350634`.
- Those tasks do not describe a Keychain Access `.cer` import error or a
  manual `fastlane match import` step. Desktop differs because Apple
  Developer ID Application certificate creation required Account Holder
  involvement and has already occurred outside Fastlane. The existing
  encrypted repository can hold the Developer ID certificate type alongside
  the iOS certificate without mixing their separate match directories.
- The iOS task recorded that GitHub Free did not offer required reviewers or
  environment secrets for the private application repository at the time.
  Current read-only GitHub inspection on September 29, 2026 confirms the
  organization still reports the Free plan. The `testflight` environment
  exists with a branch-policy rule, no required-reviewer rule, and no
  environment secrets. The user approved a manual-only desktop workflow
  using existing repository secrets without required reviewers.

### Developer ID installation diagnostic (September 29, 2026)

- The Account Holder created a G2 Developer ID Application certificate for
  team `73Q43R2PD4`.
- Opening `developerID_application.cer` in Keychain Access with the import
  destination set to **iCloud** reported error `-25294`. On this Mac,
  `security error -25294` translates to “The specified keychain could not be
  found.” Avoid importing into the iCloud destination.
- Read-only inspection found the new certificate already present in
  `/Library/Keychains/System.keychain`, issued by **Developer ID Certification
  Authority (G2)**, valid from September 29, 2026 through September 17,
  2031. Its SHA-256 fingerprint is
  `55:6C:A7:37:C1:9D:FF:54:C2:CA:9A:3D:9E:19:8E:C1:74:63:FD:E2:DF:02:BC:24:7A:A9:11:C8:F2:29:AC:FC`.
- `security find-identity -v -p codesigning` across default stores lists a
  valid Developer ID Application identity (SHA-1
  `A3635DBF9F2A7C2324773D6A788449AF3C5BCE51`), but listing the System
  keychain alone reports zero signing identities and the login keychain alone
  has no Developer ID Application certificate. This shows the certificate
  exists and macOS can resolve an identity across stores; it does **not** yet
  prove that the paired private key is exportable from Keychain Access.
- The Account Holder subsequently found the valid identity in Keychain
  Access and exported a password-protected `.p12` containing the paired
  private key. The exported file was found with mode `0644`; it was changed
  to owner-only mode `0600` on September 29, 2026. Do not revoke or recreate
  the certificate because the duplicate `.cer` import to iCloud failed.
  The next human action is to enter the export password locally when running
  the prepared import helper. Do not expose the private key or export password
  in chat.

### Desktop signing import and manual CI workflow preparation

- The existing iOS signing repository and its read-only GitHub deploy key
  are approved for this Developer ID certificate type. `fastlane match import`
  will write the certificate only after the Account Holder enters the `.p12`
  password in a local OpenSSL prompt. The helper validates the pinned G2
  certificate fingerprint, compares the private key with the certificate,
  and removes owner-only temporary key material on exit.
- A disposable test certificate confirmed that macOS LibreSSL requires an
  intermediate owner-only PEM file for this PKCS#12 conversion. That file is
  removed immediately after conversion, with an exit trap for failures.
  `bash -n` passed; the real private key and remote signing repository have
  not yet been used by the helper.
- The user explicitly removed the required-reviewer/protected-environment
  expectation. The desktop GitHub Actions workflow is manual-only on `main`,
  reuses the existing iOS GitHub variables and secrets, and performs
  verification before loading signing secrets. Public publication is an
  optional job with AWS OIDC `id-token: write`; it requires a deliberate
  `publish_download = true` dispatch after reviewing the precise DMG and
  checksum.
- The GitHub Actions runner-image inventory checked on September 29, 2026
  lists Xcode 26.1.1 and the macOS 26.1 SDK on `macos-26-arm64`. The workflow
  selects this toolchain to match the locally verified Xcode 26.1 release
  build.
- Static checks passed: `actionlint`, repository Actions security validator,
  Fastlane syntax/lane listing, Ruby build-number tests (6 runs, 8
  assertions), and five persistent candidate-metadata tests covering a
  valid artifact plus changed digest, source commit, notarization status,
  and unexpected extra asset.
  The actual signed, notarized CI build is still blocked by a usable
  Developer ID `.p12` in `match` and by publication of the workflow from
  `main`.
- The current GitHub repository already contains the necessary iOS signing
  secrets and non-secret variables; no new credentials are required for the
  shared-repository approach.
- GitHub API read-only inspection on September 29, 2026 confirmed the
  application repository has `private: true`, so its release assets cannot
  meet the anonymous website download requirement. The user subsequently
  approved the existing CLI S3/CloudFront infrastructure and same download
  subdomain with a desktop-specific prefix. No public desktop asset has yet
  been created.

### Developer ID import-helper fingerprint correction

- The first local helper invocation stopped before reading the private key:
  it reported that the `.cer` was not the expected G2 certificate.
- Inspection confirmed the downloaded `.cer` still has the pinned SHA-256
  fingerprint and matches the installed G2 Developer ID Application
  certificate. The cause was a parser that expected LibreSSL's
  `SHA256 Fingerprint=` label; the user environment can run Homebrew
  OpenSSL 3, which emits `sha256 Fingerprint=`.
- The helper now computes the SHA-256 of the normalized DER certificate
  directly, including when comparing the certificate inside the `.p12`.
  Both `/usr/bin/openssl` (LibreSSL) and Homebrew OpenSSL 3 now produce the
  expected fingerprint. A throwaway password-protected PKCS#12 also passed
  conversion with OpenSSL 3. No Developer ID private key was opened or
  signing-repository write attempted during this correction.

### Developer ID export compatibility correction

- The next local helper attempt reached the Keychain `.p12` conversion, then
  OpenSSL 3 rejected the export's `RC2-40-CBC` algorithm because its legacy
  provider was not enabled. This stopped before the Fastlane import; no
  signing-repository content changed.
- The helper now passes `-legacy` only to OpenSSL 3 when reading the original
  export. Its first revision wrote a new `.p12` using OpenSSL's default
  algorithm. A disposable `-legacy` PKCS#12 fixture passed read, conversion,
  certificate-fingerprint equality, and private-key extraction checks.
  The actual Developer ID `.p12` and password were not accessed by the agent.

### Read-only match verification exposed incompatible key packaging

- The Account Holder completed `fastlane match import`. A read-only GitHub
  repository inspection confirmed Developer ID files
  `5M2DJ2L8A7.cer` and `5M2DJ2L8A7.p12` in the private encrypted signing
  repository at commit `959df17256b87426309a4d67506533f963d31da7`
  (September 29, 2026, 11:57 UTC).
- A clean temporary keychain showed why this was insufficient for CI:
  read-only match decrypted and imported the public certificate, then
  `security import` rejected the OpenSSL-exported empty-password `.p12`
  with `MAC verification failed during PKCS12 import`. Fastlane nevertheless
  printed its generic success message. The temporary keychain had zero
  valid signing identities and was deleted afterward.
- Disposable identity tests established that macOS `security import`
  rejects blank-password PKCS#12 files written by both OpenSSL 3 and
  LibreSSL, including their legacy options, while accepting an
  Apple `security export -P ''` package. A temporary one-identity keychain
  using a scoped `/usr/bin/security` access rule exported such a package;
  another fresh keychain imported it successfully. The certificate
  fingerprint and private key were verified with test fixtures.
- The helper now uses this tested Apple export path, cleans up its
  owner-only temporary keychain and intermediate files, and validates
  the selected public certificate and private-key pairing before it runs
  `match import` again. The imported repository `.p12` must be replaced
  by that helper and rechecked in a fresh temporary keychain before any
  signed release.

### Developer ID import repaired and local release started

- The Account Holder reran the corrected import helper. The private signing
  repository's `main` branch now contains replacement encrypted Developer ID
  files at commit `dfd88bca126078d2becd2ef8bdf050126a62bb9e`
  (September 29, 2026, 15:24 UTC).
- Read-only `match developer_id` decrypted and imported this replacement
  into a clean temporary keychain. `security find-identity -v -p codesigning`
  returned **one valid identity**, SHA-1
  `A3635DBF9F2A7C2324773D6A788449AF3C5BCE51`, for team `73Q43R2PD4`.
  Match emitted no `security import` error. The temporary keychain and log
  directory were deleted after verification.
- The existing App Store Connect key had already authenticated successfully
  with `notarytool history`. The full local Fastlane release for `0.9.0 (1)`
  started in the background on September 29; PID `93412`, owner-only log
  `/var/folders/j5/g0_m7cb52q935c_px994vbp80000gn/T//crystal-lattice-desktop-release.RNvoRqLr/fastlane-release.log`.
  It stopped after TypeScript and all 194 Jest tests passed: Fastlane's
  `developer_id` match type looked for a direct-distribution provisioning
  profile and failed because this first app-only release has none. The
  current entitlements do not require a restricted capability profile.
  `skip_provisioning_profiles: true` is now explicit in both the desktop
  release lane and the Matchfile; the signed build and notarization have
  not yet completed.
- The corrected full `mac release` rerun started in the background, PID
  `93669`, owner-only log
  `/var/folders/j5/g0_m7cb52q935c_px994vbp80000gn/T//crystal-lattice-desktop-release.uJY8238q/fastlane-release.log`.
  Verification again passed all 194 Jest tests. Read-only signing completed,
  the Release archive succeeded with Developer ID signing, and the archive
  verifier found two universal Mach-O files. Apple accepted notarization
  submission `aab75b06-a9d6-4531-b2b3-98d01bea3694`; stapling,
  `codesign --verify --deep --strict`, and `spctl --assess` passed.
  The lane then failed while writing release metadata because
  `with_notary_key` discarded its block result for an existing local `.p8`
  path. The accepted DMG is an internal candidate; the release lane itself
  did not finish successfully.
- `with_notary_key` now returns the notarization result for both local-path
  and inline-key variants. Two focused Fastfile consumer tests (6 assertions)
  passed, including owner-only temporary inline-key storage and cleanup.
  A complete rerun started in the background as PID `98532`, owner-only log
  `/var/folders/j5/g0_m7cb52q935c_px994vbp80000gn/T//crystal-lattice-desktop-release.vXQzvEOm/fastlane-release.log`.
  That rerun stopped in TypeScript checking: the previous DMG staging folder
  retained its `/Applications` shortcut, and TypeScript's broad source glob
  followed the symlink into installed IntelliJ declaration files.
- The release lane now deletes its DMG staging folder in an `ensure` block,
  including on failure. The desktop TypeScript config excludes generated
  `build/` output. `npm run tsc` passed while the old staging symlink was still
  present, proving the source-scan fix before cleanup and another release run.
- The third full release attempt started in the background as PID `98698`,
  owner-only log
  `/var/folders/j5/g0_m7cb52q935c_px994vbp80000gn/T//crystal-lattice-desktop-release.htvnCmCR/fastlane-release.log`.
  It completed successfully.

### First complete local signed and notarized DMG

- `bundle exec fastlane mac release` completed for `0.9.0 (1)` on
  September 29, 2026.
- Release verification passed:
  - build-number tests: 6 runs / 8 assertions;
  - notarization-key tests: 2 runs / 6 assertions;
  - TypeScript;
  - 41 Jest suites / 194 tests;
  - Xcode Release build-setting inspection.
- Read-only match installed the G2 Developer ID identity. Xcode archived with
  `Developer ID Application: Dynamic Programming Solutions Korlatolt
  Felelossegu Tarsasag (73Q43R2PD4)`.
- The Release archive succeeded. The app verifier found both `arm64` and
  `x86_64` in the main executable and Hermes framework.
- Apple accepted notarization submission
  `1d7ff3bb-f262-4655-a04e-696fca96c1cd`. Stapling and staple validation
  succeeded.
- `codesign --verify --deep --strict` passed. Gatekeeper accepted both the
  app and DMG with source `Notarized Developer ID`.
- The app signature has team `73Q43R2PD4`, a secure timestamp, Hardened
  Runtime `26.1.0`, and an empty Release entitlement dictionary. It does not
  contain `get-task-allow`, sandbox, unsigned-memory, or library-validation
  exceptions.
- The app metadata is:
  - display name: `Crystal Lattice Desktop`;
  - bundle ID: `com.dynamicprogrammingsolutions.crystallatticecontrol.macos`;
  - version/build: `0.9.0 (1)`;
  - minimum macOS: `14.0`.
- The app-only DMG is 10,269,868 bytes. SHA-256:
  `e25e94dd95cf69b9a64e3251d1afc522d3b7ca2b322b0ff5d1d820aa5a5e88cb`.
  The signed DMG timestamp is September 29, 2026 at 17:44:17 local time.
- A read-only mount contained exactly:
  - `Crystal Lattice Desktop.app`;
  - an `Applications -> /Applications` shortcut.
  The mounted app independently passed strict signature and Gatekeeper checks.
- A temporary copy of the app from the DMG stayed running for eight seconds
  without Metro, missing-bundle, development-server, fatal, or uncaught
  exception diagnostics. The agent terminated only that smoke-test process
  and removed the temporary copy.
- The DMG staging directory is now deleted in an `ensure` block. TypeScript
  excludes generated `build/` output so a retained artifact cannot lead source
  checking through an `/Applications` symlink.

### Release-source integrity boundary

- The successful local DMG was built from the current uncommitted working
  tree. Its recorded HEAD is `467e160240aff876ff0e536eb8309a87cf8af393`,
  but it is **not** commit-exact and must not be published.
- Release metadata now records `source_tree_clean`. The GitHub candidate
  verifier requires it to be exactly `true` and rejects dirty-source
  candidates. Six tests cover a valid handoff plus changed DMG, mismatched
  source commit, dirty source tree, rejected notarization, and an extra asset.
- The current local DMG predates the new `source_tree_clean` metadata field,
  so the hardened candidate validator rejects it as intended. It is suitable
  for local technical and human acceptance only. A publishable candidate must
  be rebuilt by the committed `main` workflow from a clean checkout.
- Final credential-free verification against the current files passed on
  September 29, 2026:
  - `fastlane mac verify`;
  - build-number tests: 6 runs / 8 assertions;
  - notarization-key tests: 2 runs / 6 assertions;
  - TypeScript;
  - 41 Jest suites / 194 tests;
  - Xcode Release build-setting inspection;
  - candidate verifier tests: 6 passed;
  - `actionlint`;
  - repository GitHub Actions security validator;
  - `git diff --check`.
  Existing non-failing React `act(...)` warnings remain in the human-time
  telemetry tests.

### Shared CDN publication implementation

- On September 29, 2026, the user approved reusing the CLI download
  infrastructure and same public subdomain. The selected desktop base URL is
  `https://download.crystallattice.dev/crystal-lattice-desktop`.
- The existing CloudFormation downloads stack now declares the desktop prefix
  and long-cache behaviors for versioned `.dmg`, `.sha256`, and `.json`
  objects. It continues to use the same private bucket, Origin Access Control,
  certificate, DNS records, and CloudFront distribution.
- The existing GitHub OIDC role template remains branch/tag/environment
  constrained and now permits object operations under both the CLI and
  desktop prefixes. It does not grant bucket-wide object writes. The role
  retains only distribution invalidation beyond S3 prefix access.
- `deploy/aws-desktop-downloads/publish-assets.sh` revalidates the clean-source
  candidate before upload, applies immutable cache headers to versioned files,
  updates the desktop-only `latest.txt`, and invalidates only the five desktop
  paths it changed.
- `deploy/aws-desktop-downloads/smoke.sh` downloads the public DMG, checksum,
  versioned metadata, and notarization result; verifies SHA-256, clean-source
  metadata, version identity, and accepted notarization.
- The manual desktop workflow's default remains build-only. Its
  `publish_download = true` job verifies the candidate before AWS
  authentication, assumes the existing OIDC role, publishes the desktop
  prefix, and retries public smoke verification for up to five minutes.
- The current production infrastructure must be updated once before the first
  desktop workflow publication:
  1. deploy the existing download stack template update;
  2. deploy the existing OIDC role template update;
  3. refresh GitHub variables to add `DESKTOP_DOWNLOADS_PREFIX` and
     `DESKTOP_DOWNLOADS_BASE_URL`.
  These steps do not require a new bucket, distribution, domain, certificate,
  or long-lived AWS credential.
- AWS CloudFormation accepted both updated templates in read-only
  `validate-template` checks. A complete desktop publisher dry run verified
  the exact five S3 objects, content types, cache controls, invalidation
  paths, and final public URL without changing AWS.
- A local HTTP fixture exercised the public smoke script end to end: it
  downloaded the DMG, checksum, metadata, and notarization result; SHA-256
  verification passed; clean-source and accepted-notarization metadata
  checks passed.
- Final current-tree verification after the CDN changes passed:
  `fastlane mac verify`, all six candidate tests, `actionlint`, the repository
  Actions security validator, shell syntax checks, ShellCheck with only
  existing dynamic-source informational messages, both CloudFormation
  template validations, and `git diff --check`.

### Human acceptance changes

- The user reported that the local DMG was inspected.
- The user explicitly waived a real Intel Mac as a pre-release requirement
  and chose to rely on automated `x86_64` slice verification plus initial
  tester feedback. The task requirements and verification mapping were
  updated accordingly; the product still ships a universal binary and any
  reported Intel-specific defect remains release follow-up.

### Production download infrastructure and first hosted run

- The user authorized the proposed push, production stack updates, GitHub
  variables, and build-only workflow run.
- Local `main`, including the `develop` merge and release commit
  `52aa5d9c7a9c4053959eadd9c9c2d34f20a86969`, was pushed to `origin/main`
  on September 29, 2026.
- Production stack `crystal-lattice-cli-downloads-prod` reached
  `UPDATE_COMPLETE`. It preserved bucket
  `crystal-lattice-cli-downloads-prod-874087778966`, distribution
  `EJ5QPW5TUT5U9`, domain `download.crystallattice.dev`, certificate, and
  CLI prefix while adding:
  - `DesktopDownloadsPrefix = crystal-lattice-desktop`;
  - `DesktopDownloadsBaseUrl =
    https://download.crystallattice.dev/crystal-lattice-desktop`;
  - desktop immutable-file cache behaviors.
- OIDC stack `crystal-lattice-cli-downloads-github-oidc-prod` reached
  `UPDATE_COMPLETE`. Read-only IAM inspection confirmed:
  - trust for `main`, CLI tags, desktop tags, and the existing CLI
    environment;
  - `s3:ListBucket` constrained to CLI and desktop prefixes;
  - object operations constrained to those two prefix ARNs;
  - CloudFront invalidation constrained to distribution `EJ5QPW5TUT5U9`.
- GitHub repository variables `DESKTOP_DOWNLOADS_PREFIX` and
  `DESKTOP_DOWNLOADS_BASE_URL` were created with the approved values.
- Build-only workflow run `36629046745` used commit `52aa5d9c...` and had
  publication disabled. Checkout, configuration, Xcode 26.1.1, Node, Ruby,
  Bundler, CocoaPods, and the Fastlane helper tests succeeded. It failed in
  TypeScript before loading signing credentials because a clean runner had
  installed only the desktop lockfile: shared package source under
  `packages/frontend-rn-components` could not resolve root-workspace React
  types.
- The workflow now runs root `npm ci` followed by desktop `npm ci` and caches
  both lockfiles. A fresh detached worktree with no preexisting
  `node_modules` passed both installs and desktop TypeScript. No CI-only
  resolution override or product-code shortcut was added.
- Follow-up build-only run `36629766253` on commit `63625af5...` passed
  clean-checkout dependency installation, release verification, read-only
  signing retrieval, universal Developer ID archive, Apple notarization,
  stapling, and Gatekeeper validation. It failed before artifact upload
  because metadata measured source cleanliness after the generated native
  build and reported a dirty tree.
- A second fresh detached worktree remained clean after root npm, desktop npm,
  Bundler, and CocoaPods setup. The release contract now captures commit and
  clean-tree state at the start of `mac release`, before generated build work,
  and carries that immutable state into metadata. The workflow independently
  runs `git diff --exit-code` and checks porcelain status after verification
  and before loading signing credentials. Candidate validation still requires
  `source_tree_clean = true`; the guard was moved to the correct boundary, not
  weakened.
- Build-only run `36632820887` on commit `3573c47f...` passed dependency
  installation and release verification, then the explicit pre-signing clean
  check found one tracked tooling mutation:
  `ruby/setup-ruby` had rewritten the package's `.bundle/config` from its
  committed relative path to an absolute hosted-runner path and added
  deployment mode. The workflow now restores that tracked config immediately
  after the cached bundle installation. The installed gems remain available,
  while CocoaPods, verification, and release source capture see the committed
  configuration.
- Build-only workflow run `36633536807` completed successfully on clean commit
  `1a04b8689eab0821727be2c3efc9213e57ebafe7` from September 29, 2026
  21:28–21:49 UTC. The publication job was skipped.
- Hosted candidate evidence:
  - marketing version/build: `0.9.0 (4)`;
  - architectures: `arm64`, `x86_64`;
  - minimum macOS: `14.0`;
  - source tree clean: `true`;
  - notarization submission:
    `72cd6073-9071-4bfa-aad5-56d7ea704be2`, status `Accepted`;
  - DMG size: 10,268,972 bytes;
  - SHA-256:
    `8bbd119552de60eee53dd4d45fb8cd360faa1a7a788b780114e274ee46959bb5`.
- The downloaded workflow artifact independently passed:
  - the four-file candidate validator against the exact source commit;
  - checksum verification;
  - Developer ID DMG signature and timestamp inspection;
  - staple validation and Gatekeeper DMG acceptance;
  - mounted app strict deep signature and Gatekeeper acceptance;
  - exact app-plus-Applications-shortcut contents;
  - universal `x86_64 arm64` executable inspection;
  - embedded build number `4`.
- Publication was redesigned before use so human approval can refer to this
  exact checksum. A publication dispatch must set
  `publish_download = true` and `candidate_run_id = 36633536807`. The publish
  job verifies the referenced run is this workflow, completed successfully on
  `main`, obtains its source commit from GitHub, downloads that retained
  artifact, revalidates it, and only then assumes AWS credentials. It does not
  rebuild or substitute a new candidate.