# Add fastlane For iOS Build And TestFlight Upload

Add fastlane configuration so the iOS app can be built, signed, archived, and uploaded to TestFlight repeatably.

## Requirements checklist

- [x] Add/confirm Ruby dependency setup for fastlane under `mobile/crystal-lattice-control-rn`.
- [x] Add iOS fastlane configuration with lanes for verification/build/beta upload.
- [x] Choose and implement signing strategy: recommended `fastlane match`, or a documented manual secret/profile approach.
- [x] Use App Store Connect API key authentication for upload.
- [x] Implement build-number incrementing that works locally and in GitHub Actions.
- [ ] Verify the lane can archive locally when credentials are available.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/060-app-store-connect-registration-package.md

## Known Starting State

Current files:

- `mobile/crystal-lattice-control-rn/Gemfile` exists.
- No `fastlane/` directory was found under the mobile app during the audit.
- No `eas.json`, Codemagic, or Bitrise config was found for this app.

Likely files to add:

- `mobile/crystal-lattice-control-rn/fastlane/Fastfile`
- `mobile/crystal-lattice-control-rn/fastlane/Appfile`
- Possibly `mobile/crystal-lattice-control-rn/fastlane/Matchfile`, if using `match`

Suggested lanes:

- `ios verify`: run app verification such as typecheck/tests/lint where appropriate.
- `ios build`: archive without upload.
- `ios beta`: archive and upload to TestFlight with `pilot`.

Suggested fastlane actions:

- `app_store_connect_api_key`
- `increment_build_number` or explicit build number from CI
- `match` or documented certificate/profile import
- `build_app`
- `pilot`

## Acceptance Criteria

- fastlane configuration is checked in and documented.
- Sensitive credentials are not committed.
- A maintainer with proper Apple credentials can run the beta lane locally.
- The lane archives the `CrystalLatticeControlRN` scheme from the correct workspace.

## Execution plan

Status: Approved

Implement fastlane in the mobile package with a deterministic Ruby toolchain,
App Store Connect API-key authentication, `fastlane match` signing, explicit
build-number resolution, and separate verification/build/upload lanes.

The repository will contain configuration and non-secret defaults only.
Certificates, profiles, API private keys, encryption passwords, and signing-repo
credentials remain external environment variables or GitHub secrets.

The implementation will:

- Pin Ruby `3.4.10` for local and future CI consistency.
- Add fastlane `2.237.0` and commit the Bundler lockfile.
- Configure the bundle identifier, Apple Developer team, and numeric App Store
  Apple ID without storing an Apple login email or password.
- Use App Store Connect API keys from either a local `.p8` filepath or base64
  key content supplied through environment variables.
- Use a private git-backed `match` repository for App Store distribution
  certificates and provisioning profiles.
- Provide `verify`, `setup_signing`, `build`, and `beta` lanes.
- Resolve build numbers in this order:
  1. Explicit `IOS_BUILD_NUMBER`.
  2. The greater of `GITHUB_RUN_NUMBER` and latest TestFlight plus one.
  3. Latest TestFlight plus one outside GitHub Actions.
- Export with Xcode's current `app-store-connect` method and disable Xcode's
  automatic version/build-number management during export.
- Keep the first internal upload waiting policy configurable; default to waiting
  for build processing so the lane can apply TestFlight metadata.

### Implementation decisions and open questions

- Decision: use `fastlane match` rather than manually importing base64
  certificates/profiles into each runner.
- Decision: use App Store Connect API-key authentication, not an Apple password
  or interactive 2FA session.
- Decision: keep the installed app display name `Crystal Lattice`; the exact App
  Store listing name does not affect fastlane and remains a non-blocking owner
  confirmation in task `060`.
- Decision: use App Store numeric Apple ID `6798401926` for TestFlight upload
  targeting.
- Open credential dependency: the owner must create a private signing repository
  and an App Store Connect API key before signed archive/upload verification.
- Open external-review dependency: task `085` remains required before external
  TestFlight review, but it does not block internal testing.

### Documentation

- Add a focused TestFlight/fastlane section to the mobile README.
- Document Ruby/Bundler setup, lane commands, environment variables, one-time
  signing bootstrap, and safe handling of secrets.
- Keep GitHub Actions-specific secret creation details for task `080`, while
  naming the compatible variables here.

### Task checklist

- [x] Pin the Ruby version and add fastlane to Bundler dependencies.
- [x] Generate and commit a compatible Bundler lockfile.
- [x] Add `Appfile`, `Matchfile`, and `Fastfile`.
- [x] Add a non-secret environment-variable template.
- [x] Add verification, signing bootstrap, signed build, and beta upload lanes.
- [x] Add deterministic local/CI build-number resolution.
- [x] Document local setup and the manual credential boundary.
- [x] Run fastlane configuration/syntax and lane-list verification.
- [x] Run the credential-free verification lane.
- [x] Exercise the archive command to the credential boundary and document the
      expected signing blocker if credentials are unavailable.

### Requirement verification

- Ruby dependency requirement: `bundle exec fastlane --version` and Bundler
  lockfile inspection.
- Lane/configuration requirement: `bundle exec fastlane lanes` lists the
  documented iOS lanes.
- Signing requirement: `match` configuration uses a private git URL supplied by
  environment and contains no secret values.
- API authentication requirement: configuration accepts key ID, issuer ID, and
  `.p8` content/path without Apple password authentication.
- Build numbering requirement: automated tests or lane execution cover explicit,
  GitHub, and TestFlight-fallback selection.
- Archive requirement: the build lane targets the checked-in workspace/scheme;
  full signed archive evidence is recorded when signing credentials are
  available.

### Additional implementation verification

- Run mobile TypeScript and Jest verification through the fastlane lane.
- Run `plutil`/Xcode build-setting inspection for bundle ID, version, build, and
  export-compliance declarations.
- Confirm generated reports, IPA archives, API keys, and local `.env` files are
  ignored.

## Implementation Notes

Implemented in the `main` worktree on 2026-08-05:

- Ruby `3.4.10`, Bundler lockfile, fastlane `2.237.0`, CocoaPods `1.16.2`,
  and xcodeproj `1.27.0`.
- `Appfile`, `Matchfile`, `Fastfile`, non-secret `.env.example`, and isolated
  build-number resolver tests.
- `ios verify`, `ios setup_signing`, `ios build`, and `ios beta` lanes.
- App Store Connect API-key loading from a local `.p8` filepath or base64
  content.
- Private git-backed match configuration with read-only normal/CI operation and
  an explicit write-enabled setup lane.
- Build-number selection that prefers an explicit value and otherwise avoids
  collisions with existing TestFlight builds.
- App-relative absolute paths so fastlane execution from the `fastlane/`
  directory targets the correct workspace, project, tests, and output folder.
- fastlane anonymous usage reporting disabled.

Verification evidence:

- `bundle check`: passed.
- `bundle exec fastlane --version`: fastlane `2.237.0`.
- `bundle exec fastlane lanes`: all four documented iOS lanes listed.
- Build-number tests: 5 tests / 7 assertions passed.
- `bundle exec fastlane ios verify`: passed; TypeScript and 26 Jest suites /
  110 tests passed.
- `bundle exec pod install --project-directory=ios`: passed with CocoaPods
  `1.16.2`.
- Unsigned Release device archive with build-number override `2`: passed.
- Archived app inspection: display name `Crystal Lattice`, bundle ID
  `com.dynamicprogrammingsolutions.crystallatticecontrolrn`, version `0.9.0`,
  build `2`, non-exempt encryption `false`, and privacy manifests packaged.
- `bundle exec fastlane ios build` without credentials: stopped at the intended
  boundary with missing `APP_STORE_CONNECT_KEY_ID` and
  `APP_STORE_CONNECT_ISSUER_ID`.
- `plutil` validation and `git diff --check`: passed.
- `.env`, fastlane reports, and `build/` archives are ignored; `.env.example`
  remains eligible for source control.

Remaining requirement evidence:

- A signed archive and IPA export require the owner to create the App Store
  Connect API key and private match repository, then run `ios setup_signing` and
  `ios build`. Until that evidence exists, this task and its parent checklist
  remain open.

Findings outside this task:

- `npm ci` reports existing dependency advisories: 1 low, 18 moderate, 12 high,
  and 2 critical. No automatic audit fix was applied because forced dependency
  upgrades could change React Native behavior.
- Existing Jest output includes a non-failing VirtualizedList `act(...)`
  warning.
- The unsigned archive includes existing warnings for always-run React Native
  script phases and low deployment targets in several pod resource targets.
