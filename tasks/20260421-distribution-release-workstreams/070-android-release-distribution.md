# Android Release Distribution

Prepare the React Native Android app for signed Play Store releases and tester distribution.

## Requirements checklist

- [ ] Finalize Android versioning and signing strategy for release builds.
- [ ] Produce a signed release `.aab` suitable for Play Console upload.
- [ ] Document Play Console setup, internal testing, and production rollout steps.
- [ ] Capture listing, privacy policy, and Data safety requirements specific to this app.

Parent Task: `tasks/20260421-distribution-release-workstreams/000-main.md`

## Current state

- Android app identifiers and version fields are already present in `mobile/crystal-lattice-control-rn/android/app/build.gradle:75-107`.
- The current release build still uses the debug signing config in `mobile/crystal-lattice-control-rn/android/app/build.gradle:88-106`, so production signing is not yet configured.
- The app already has a stable package name: `com.dynamicprogrammingsolutions.crystallatticecontrolrn`.

## Proposed solution from conversation

- Use Google Play Console as the primary Android distribution channel.
- Replace the temporary debug release signing setup with a proper upload keystore and Play App Signing workflow.
- Build Android release artifacts as `.aab` bundles using `./gradlew bundleRelease`.
- Start with Play internal testing, then promote the same pipeline to production once release validation and store metadata are complete.
- Treat Play listing assets, privacy policy, and Data safety answers as part of release readiness rather than a separate afterthought.

## Deliverables

- Android signing/config notes.
- Release build instructions and output path.
- Play Console release checklist.