# Audit Android Release Build And Runtime Manifest

Produce a reproducible Android release-readiness baseline, identify build and
runtime blockers, and verify the app before production signing is introduced.

## Requirements checklist

- [ ] TypeScript, Jest, and relevant Android component/integration verification
      pass from a clean dependency installation.
- [ ] The Release AAB build reaches a terminal result and all warnings/errors
      relevant to Play delivery are classified.
- [ ] The merged Release manifest, permissions, components, deep links, cleartext
      policy, package, SDK levels, and app metadata are audited.
- [ ] Native libraries and all intended device ABIs are present or deliberately
      narrowed.
- [ ] Release-only behavior that would break self-hosted connections,
      attachments, saved files, sharing, or reconnection is identified.
- [ ] Findings are mapped to owning subtasks without weakening realistic tests.

Parent Task: tasks/20260820-android-google-play-github-fastlane/000-main.md
Depends On: tasks/20260820-android-google-play-github-fastlane/010-play-console-preflight.md

## Required reading

Read the parent task's `Shared required reading`, then:

- `mobile/crystal-lattice-control-rn/android/gradle/wrapper/gradle-wrapper.properties`
- `mobile/crystal-lattice-control-rn/android/app/proguard-rules.pro`
- `mobile/crystal-lattice-control-rn/scripts/ensure_android_debug_keystore.sh`
- `mobile/crystal-lattice-control-rn/e2e/jest.config.js`
- Android App Bundle testing:
  https://developer.android.com/guide/app-bundle/test
- Manifest merger:
  https://developer.android.com/build/manage-manifests
- Network security configuration:
  https://developer.android.com/privacy-and-security/security-config

## Verified baseline

- Java 17 launches Gradle 9.0.0.
- A 2026-08-20 diagnostic `:app:bundleRelease` run progressed through JS
  bundling, manifest processing, Kotlin/Java compilation, and native
  compilation, but the command exceeded five minutes before returning. It is
  not successful evidence.
- Release currently signs with a generated debug keystore.
- Release merged manifest observations:
  - Package: `com.dynamicprogrammingsolutions.crystallatticecontrolrn`
  - Version: `1.0` / code `1`
  - Minimum SDK: 24
  - Target SDK: 36
  - `usesCleartextTraffic="false"`
  - Permissions include internet, Wi-Fi state, multicast state, plus merged
    legacy read/write external-storage permissions.
  - Deep-link scheme: `crystal-lattice`
- Existing native dependency warnings include deprecated namespace/package
  declarations and deprecated APIs. Classify them; do not automatically upgrade
  dependencies merely to silence warnings.

## Execution plan

Status: Draft

Use a clean checkout or cleaned package state with Node 20 and Java 17. Run
mobile verification, then run `bundleRelease` with sufficient timeout and
captured logs. Inspect merged manifests, bundle contents, signing identity, and
native ABIs using Android build tools and `bundletool`. Do not count a timeout,
skipped test, or debug-signed bundle as production readiness.

### Implementation decisions and open questions

- Decision: Java 17 is the baseline for local and CI builds unless the current
  Android Gradle Plugin requires a documented change.
- Decision: retain all four current ABIs during audit; optimize only with size
  evidence and device-support approval.
- Open question: final HTTP/WS policy is owned by task `040`.
- Open question: whether legacy storage permissions can be removed without
  breaking generated-file save/share and attachment behavior.

### Documentation

- Put durable current build/troubleshooting guidance in the mobile package's
  Android development documentation.
- Keep transient warning inventories in this task's implementation notes.

### Task checklist

- [ ] Install dependencies from lockfiles.
- [ ] Run TypeScript and Jest verification.
- [ ] Run Android unit/component/integration checks relevant to release.
- [ ] Complete `:app:bundleRelease` with a terminal result.
- [ ] Inspect merged manifest and dependency-introduced permissions.
- [ ] Inspect AAB modules, ABIs, resources, package, version, and signing state.
- [ ] Assign each blocker to task `030`, `040`, `050`, or `070`.

### Requirement verification

- Verification baseline: successful commands with collected test counts.
- Build baseline: `app-release.aab` exists only after a successful Gradle exit.
- Manifest baseline: checked merged Release manifest, not source manifest alone.
- Bundle baseline: `bundletool` or equivalent inspection of package, SDKs,
  modules, ABIs, and certificate.
- Runtime baseline: physical-device or production-like Release build checks for
  connection, attachment, sharing, and deep-link behavior where available.

### Additional implementation verification

- Run `git diff --check`.
- Confirm generated keystores/build output are ignored.
- Record but do not automatically fix dependency audit findings outside scope.