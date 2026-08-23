# Prepare Android Google Play Deployment With GitHub Actions And fastlane

Prepare the Crystal Lattice Control React Native Android app for Google Play
registration, an internal-testing release, and repeatable deployment through
GitHub Actions plus fastlane.

## Requirements checklist

- [ ] The Android app has a production-safe identity, versioning strategy,
      upload-signing configuration, and release bundle.
- [ ] Dynamic Programming Solutions Kft. can register and administer the app in
      a verified Google Play Console organization account.
- [ ] Google Play listing, privacy, App content, Data safety, and reviewer-access
      inputs accurately describe the self-hosted product.
- [ ] A maintainer can build and upload a signed Android App Bundle to the
      internal testing track locally through fastlane.
- [ ] A protected GitHub Actions workflow can verify, build, sign, and upload an
      internal-testing release without exposing credentials.
- [ ] An internal tester can install the Play-delivered build and exercise the
      supported connection, session, message, attachment, and reconnection
      flows.
- [ ] Closed testing and production promotion remain blocked until their
      additional review, media, compliance, and testability requirements are
      satisfied.
- [ ] Maintainers have a current Android release and credential-recovery
      runbook.

## Roadmap status updates

Roadmap:
[Open Source and iOS Release](../../roadmaps/open-source-and-ios-release.md)

Instructions:
[Updating a roadmap through CSV](../../roadmaps/docs/updating-roadmaps.md)

Do not read the linked roadmap or instructions, inspect roadmap state, or
update the roadmap as part of routine task execution or completion. Do so only
when the user explicitly requests a roadmap status update, for example:
“update the task status in the roadmap as per the instructions in the main
task.”

That explicit request authorizes reading the linked files, updating the
authored CSV and generated Markdown, and synchronizing the configured Google
Sheet as required by the instructions. It does not authorize unrelated roadmap
changes. If the user limits the request to local files, do not mutate the
sheet.

## Subtasks

- [ ] `tasks/20260820-android-google-play-github-fastlane/010-play-console-preflight.md`
- [ ] `tasks/20260820-android-google-play-github-fastlane/020-android-release-build-audit.md`
- [ ] `tasks/20260820-android-google-play-github-fastlane/030-android-branding-and-store-assets.md`
- [ ] `tasks/20260820-android-google-play-github-fastlane/040-android-identity-versioning-and-upload-signing.md`
- [ ] `tasks/20260820-android-google-play-github-fastlane/050-google-play-privacy-and-app-content.md`
- [ ] `tasks/20260820-android-google-play-github-fastlane/060-play-console-registration-package.md`
- [ ] `tasks/20260820-android-google-play-github-fastlane/070-fastlane-google-play-release.md`
- [ ] `tasks/20260820-android-google-play-github-fastlane/080-github-actions-android-cd.md`
- [ ] `tasks/20260820-android-google-play-github-fastlane/085-google-play-review-testable-mode.md`
- [ ] `tasks/20260820-android-google-play-github-fastlane/090-first-internal-testing-release.md`
- [ ] `tasks/20260820-android-google-play-github-fastlane/100-closed-and-production-readiness.md`
- [ ] `tasks/20260820-android-google-play-github-fastlane/110-android-release-runbook.md`

## Scope

In scope:

- Android application readiness under
  `mobile/crystal-lattice-control-rn/android`.
- Google Play Console registration and internal-testing metadata.
- Google Play App Signing plus a separately controlled upload key.
- Android lanes in the existing mobile fastlane configuration.
- A dedicated GitHub Actions Android deployment workflow.
- Google Play privacy, App content, reviewer access, and release verification.
- Internal testing first, with explicit gates for closed testing and
  production.

Out of scope unless separately approved:

- Publishing the app to production.
- Introducing a Dynamic Programming Solutions Kft.-operated bridge, cloud
  agent, analytics, advertising, crash-reporting, or user-account service.
- Changing the package name
  `com.dynamicprogrammingsolutions.crystallatticecontrolrn`.
- Replacing the existing React Native architecture or backend protocol.
- Automatically applying forced dependency-audit upgrades.

## Unresolved requirement questions

Answers that change required outcomes must be confirmed before the affected
subtask is executed:

1. Does Dynamic Programming Solutions Kft. already have a verified Google Play
   Console organization developer account?
2. Has a Play Console app record already been created for
   `com.dynamicprogrammingsolutions.crystallatticecontrolrn`?
3. Which Google Cloud project should own Google Play Developer API access?
4. Which Google/Workspace accounts should be initial internal testers?
5. Should the Android release keep supporting arbitrary user-entered `http://`
   and `ws://` self-hosted endpoints? Recommendation: yes, with explicit UI
   warning and preference for HTTPS/WSS.
6. Should Android align with the iOS pre-release marketing version `0.9.0`?
   Recommendation: yes.
7. Is a service-account JSON credential acceptable for the first GitHub
   workflow, with Workload Identity Federation evaluated as a later hardening
   step? Recommendation: yes, provided the key is narrowly permissioned,
   protected by a GitHub Environment, and rotated.
8. Should the first Play release be internal testing only? Recommendation: yes.

## Required reading

Repository and package:

- `AGENTS.md`
- `mobile/crystal-lattice-control-rn/AGENTS.md`
- `mobile/crystal-lattice-control-rn/README.md`
- `mobile/crystal-lattice-control-rn/package.json`
- `mobile/crystal-lattice-control-rn/android/app/build.gradle`
- `mobile/crystal-lattice-control-rn/android/build.gradle`
- `mobile/crystal-lattice-control-rn/android/gradle.properties`
- `mobile/crystal-lattice-control-rn/android/app/src/main/AndroidManifest.xml`
- `mobile/crystal-lattice-control-rn/android/.gitignore`
- `mobile/crystal-lattice-control-rn/Gemfile`
- `mobile/crystal-lattice-control-rn/fastlane/Fastfile`
- `tasks/20260614-ios-testflight-github-fastlane/050-privacy-landing-page-compliance.md`
- `tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md`

Official external resources:

- Create and set up a Play Console app:
  https://support.google.com/googleplay/android-developer/answer/9859152
- Sign an Android app and use Play App Signing:
  https://developer.android.com/studio/publish/app-signing
- Google Play Developer API setup:
  https://developers.google.com/android-publisher/getting_started
- Google Play target API requirements:
  https://support.google.com/googleplay/android-developer/answer/11926878
- Internal, closed, and open testing:
  https://support.google.com/googleplay/android-developer/answer/9845334
- Data safety:
  https://support.google.com/googleplay/android-developer/answer/10787469
- Store-listing graphic requirements:
  https://support.google.com/googleplay/android-developer/answer/9866151
- fastlane Google Play upload action:
  https://docs.fastlane.tools/actions/upload_to_play_store/
- GitHub encrypted secrets:
  https://docs.github.com/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions

## Verified starting state

Verified on 2026-08-20:

- App name: `Crystal Lattice Control`.
- Android namespace/application ID:
  `com.dynamicprogrammingsolutions.crystallatticecontrolrn`.
- `minSdkVersion = 24`.
- `compileSdkVersion = 36`.
- `targetSdkVersion = 36`.
- Gradle wrapper: `9.0.0`.
- Local Java 17 can launch Gradle.
- Android version is currently `versionName "1.0"` / `versionCode 1`, which is
  inconsistent with iOS `0.9.0`.
- The production `release` build currently uses `signingConfigs.debug`; this
  must never be uploaded to Google Play.
- The project has legacy-density and round launcher PNGs plus light/dark splash
  icons, but no adaptive-icon resource set or themed monochrome icon.
- The shared source icons are:
  - `mobile/crystal-lattice-control-rn/src/assets/icons/icon.svg`
  - `mobile/crystal-lattice-control-rn/src/assets/icons/icon_dark.svg`
- The release merged manifest sets `android:usesCleartextTraffic="false"`.
  This conflicts with ordinary self-hosted `http://`/`ws://` connection use and
  requires a product/security decision.
- The release merged manifest contains
  `READ_EXTERNAL_STORAGE` and `WRITE_EXTERNAL_STORAGE` introduced by
  dependencies even though the source manifest does not declare them.
- A diagnostic `:app:bundleRelease` run passed JavaScript bundling, manifest
  merging, Java/Kotlin compilation, and native ABI compilation but exceeded a
  five-minute command window before Gradle returned a terminal result. No AAB
  was counted as successful evidence.
- The diagnostic run created only ignored build output and an ignored debug
  keystore.
- Current public URLs:
  - Privacy: `https://crystallattice.dev/privacy`
  - Support: `https://crystallattice.dev/support`
  - Marketing: `https://crystallattice.dev/mobile`
- Confirmed operating model:
  - No developer-operated production bridge.
  - No public cloud-agent service.
  - No analytics, advertising, tracking, or crash-reporting SDK.
  - Users connect to environments they or their organizations operate.
  - Support correspondence is retained as business correspondence.

## Release architecture

Use one mobile fastlane installation but separate iOS and Android lanes.

Android release path:

1. GitHub Actions starts manually on an Ubuntu runner.
2. Node 20, Java 17, Ruby 3.4.10, Bundler, and Gradle dependencies are restored.
3. TypeScript, Jest, build-number/version-code tests, and Android release checks
   run.
4. The upload keystore is restored from a protected GitHub secret.
5. Gradle builds a signed Release AAB.
6. fastlane authenticates to Google Play through a narrowly permissioned
   service account.
7. fastlane uploads the AAB to the `internal` track.
8. Google Play App Signing signs device APKs with the Google-controlled app
   signing key.

Unlike iOS, do not create a separate signing repository. Store the Android
upload keystore as an encrypted GitHub Environment secret and keep a separate
encrypted offline backup plus password-manager records.

## Execution plan

Status: Draft

Execute subtasks in dependency order. Complete account and code preflight
before creating permanent upload-signing state. Keep the first release on the
internal track. Require explicit owner approval before closed testing,
production rollout, package-name changes, service creation, or any action that
could replace signing identity.

### Implementation decisions and open questions

- Decision: use a separate Android task directory while extending the existing
  mobile `Fastfile`.
- Decision: use Google Play App Signing with a locally controlled upload key.
- Decision: use a dedicated GitHub Environment such as
  `android-google-play`.
- Decision: start with `workflow_dispatch`; do not enable tag/push deployment
  until the first internal release succeeds.
- Decision: internal testing does not authorize closed/open/production
  promotion.
- Open questions are listed above and remain owner decisions where they change
  product behavior, account ownership, or credential architecture.

### Documentation

- Keep the mobile README concise and link a package-owned Android release
  maintainer guide.
- Put detailed current release operation under
  `mobile/crystal-lattice-control-rn/docs/development/`.
- Do not expose task identifiers, approval state, or secrets in public user
  documentation.

### Task checklist

- [ ] Complete every listed subtask with evidence.
- [ ] Keep parent and child requirement status synchronized.
- [ ] Preserve existing iOS release behavior while extending shared fastlane
      and documentation.
- [ ] Obtain explicit approval before any release-track promotion beyond
      internal testing.

### Requirement verification

- Production identity/signing: inspect the final AAB certificate, package,
  version name, and version code.
- Registration/compliance: inspect saved Play Console app, App content, Data
  safety, privacy URL, and internal-track state.
- Local automation: run the Android fastlane verification/build/upload lanes
  against the intended account.
- CI automation: observe a successful protected GitHub Actions run and matching
  Google Play internal release.
- Tester outcome: human confirmation from a Play-installed build on a physical
  Android device.
- Runbook: a maintainer not involved in implementation can follow it without
  undisclosed setup.

### Additional implementation verification

- Verify a clean checkout build on Linux-compatible tooling.
- Inspect the final merged manifest and Play pre-launch report.
- Verify upload-key backup and recovery instructions without exposing secrets.
- Revalidate current target API requirements immediately before delivery.