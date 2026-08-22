# Add fastlane Android Build And Google Play Upload Lanes

Extend the existing mobile fastlane configuration with repeatable Android
verification, signed AAB build, internal-track upload, and controlled promotion
capabilities.

## Requirements checklist

- [ ] The existing Ruby/Bundler setup supports Android lanes without regressing
      iOS lanes.
- [ ] Android lanes verify the app, build a production-signed AAB, validate Play
      credentials, and upload to the internal track.
- [ ] Version-code selection works locally and in GitHub Actions without
      collisions across Play tracks.
- [ ] Google Play authentication uses narrowly permissioned external
      credentials and no committed secrets.
- [ ] Upload metadata and release notes are deterministic and reviewable.
- [ ] Promotion beyond internal testing requires an explicit lane/input and
      owner approval.
- [ ] A local signed AAB and credential validation succeed before CI deployment.

Parent Task: tasks/20260820-android-google-play-github-fastlane/000-main.md
Depends On: tasks/20260820-android-google-play-github-fastlane/040-android-identity-versioning-and-upload-signing.md
Depends On: tasks/20260820-android-google-play-github-fastlane/060-play-console-registration-package.md

## Required reading

Read the parent task's `Shared required reading`, then:

- `mobile/crystal-lattice-control-rn/Gemfile`
- `mobile/crystal-lattice-control-rn/Gemfile.lock`
- `mobile/crystal-lattice-control-rn/fastlane/Fastfile`
- `mobile/crystal-lattice-control-rn/fastlane/.env.example`
- `mobile/crystal-lattice-control-rn/android/app/build.gradle`
- fastlane upload to Play:
  https://docs.fastlane.tools/actions/upload_to_play_store/
- fastlane Gradle action:
  https://docs.fastlane.tools/actions/gradle/
- Validate Play JSON key:
  https://docs.fastlane.tools/actions/validate_play_store_json_key/
- Google Play track version codes:
  https://docs.fastlane.tools/actions/google_play_track_version_codes/

## Proposed lanes

```text
android verify
android build
android validate_play_credentials
android internal
android promote
```

Expected behavior:

- `verify`: build-number/version-code tests, TypeScript, Jest, Android checks.
- `build`: restore required signing inputs and produce a signed Release AAB
  without upload.
- `validate_play_credentials`: verify service-account/API access.
- `internal`: verify, build, and upload to Play `internal`.
- `promote`: promote an existing tested version between tracks without
  rebuilding; require explicit source/target/version and owner approval.

## Environment contract

Non-secret defaults:

```text
ANDROID_PACKAGE_NAME=com.dynamicprogrammingsolutions.crystallatticecontrolrn
ANDROID_VERSION_NAME=0.9.0
GOOGLE_PLAY_TRACK=internal
```

Secret/local inputs:

```text
ANDROID_UPLOAD_STORE_FILE
ANDROID_UPLOAD_STORE_PASSWORD
ANDROID_UPLOAD_KEY_ALIAS
ANDROID_UPLOAD_KEY_PASSWORD
GOOGLE_PLAY_JSON_KEY_PATH
```

CI may reconstruct files from:

```text
ANDROID_UPLOAD_KEYSTORE_BASE64
GOOGLE_PLAY_SERVICE_ACCOUNT_JSON
```

The fastlane lane should consume file paths; the GitHub workflow owns temporary
file reconstruction and cleanup.

## Version-code strategy

Resolve in this order:

1. Explicit `ANDROID_VERSION_CODE`.
2. A CI candidate based on `GITHUB_RUN_NUMBER`.
3. Highest version code found on relevant Play tracks plus one.

The final selected code must be greater than every known active/draft code and
must be validated as a positive Android-supported integer. Put the resolver in
an isolated tested helper rather than embedding untested arithmetic in the
lane.

## Execution plan

Status: Draft

Add `platform :android` to the existing Fastfile. Reuse shared verification
where appropriate without invoking iOS-only signing. Keep secrets out of lane
output. Build to a deterministic ignored path, validate AAB existence and
certificate, then upload only to the requested internal track. Do not configure
automatic production promotion.

### Implementation decisions and open questions

- Decision: one Fastfile with separate platform blocks.
- Decision: `internal` is the default and only initial upload track.
- Decision: service-account JSON is the initial supported credential form.
- Recommendation: evaluate Workload Identity Federation only after an
  end-to-end proof with fastlane/googleauth; do not weaken the initial
  deliverable for an unverified integration.
- Open question: whether fastlane manages listing metadata immediately or only
  binary/release notes for the first internal release.

### Documentation

- Add Android lane commands and environment-variable names to package release
  documentation.
- Keep `.env.example` values non-secret and platform-separated.
- Document that GitHub Secrets are not an upload-key backup.

### Task checklist

- [ ] Add Android environment constants/helpers.
- [ ] Add isolated version-code resolver and tests.
- [ ] Add `verify`, `build`, credential-validation, and `internal` lanes.
- [ ] Add guarded promotion lane or document deliberate deferral.
- [ ] Add deterministic output and metadata paths.
- [ ] Validate no secret values are logged.
- [ ] Run Android verification lane.
- [ ] Build and inspect a signed AAB locally.
- [ ] Validate Play API credentials.

### Requirement verification

- Existing iOS lanes: lane listing and existing iOS verification remain valid.
- Android lanes: `bundle exec fastlane lanes` and focused lane runs.
- Version code: tests cover explicit, GitHub, Play fallback, and invalid inputs.
- Signing: AAB certificate matches upload key.
- API auth: credential validation reaches the intended Play account/package.
- Upload: internal-track release appears with expected version and notes.

### Additional implementation verification

- Test missing-secret errors for clarity.
- Test a dry local build without modifying tracked version files.
- Verify generated metadata/reports/AABs are ignored or intentionally retained.