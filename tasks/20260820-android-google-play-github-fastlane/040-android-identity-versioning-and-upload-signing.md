# Configure Android Identity, Versioning, Network Policy, And Upload Signing

Replace debug release signing, align Android release identity/versioning, and
define secure network and upload-key behavior compatible with local and CI
builds.

## Requirements checklist

- [ ] The production package name remains
      `com.dynamicprogrammingsolutions.crystallatticecontrolrn`.
- [ ] The installed app name remains `Crystal Lattice Control`.
- [ ] Android marketing version and monotonically increasing version-code
      strategy are explicit and work locally and in GitHub Actions.
- [ ] The Release variant cannot fall back to the public debug keystore.
- [ ] A dedicated upload key is generated, backed up, and loaded only from
      environment/secret-backed configuration.
- [ ] Google Play App Signing ownership and upload-key recovery are documented.
- [ ] Production behavior for user-entered HTTP/WS endpoints is deliberately
      implemented and communicated.
- [ ] Release signing and network configuration contain no committed secrets.

Parent Task: tasks/20260820-android-google-play-github-fastlane/000-main.md
Depends On: tasks/20260820-android-google-play-github-fastlane/010-play-console-preflight.md
Depends On: tasks/20260820-android-google-play-github-fastlane/020-android-release-build-audit.md

## Required reading

Read the parent task's `Shared required reading`, then:

- `mobile/crystal-lattice-control-rn/android/app/build.gradle`
- `mobile/crystal-lattice-control-rn/android/.gitignore`
- `mobile/crystal-lattice-control-rn/App.tsx`
- `mobile/crystal-lattice-control-rn/src/ConnectionScreen.tsx`
- Android app signing:
  https://developer.android.com/studio/publish/app-signing
- Sign from Gradle:
  https://developer.android.com/studio/publish/app-signing#sign-gradle
- Network security configuration:
  https://developer.android.com/privacy-and-security/security-config
- Google Play upload-key reset:
  https://support.google.com/googleplay/android-developer/answer/9842756

## Starting configuration and risk

Current `release` uses:

```groovy
signingConfig signingConfigs.debug
```

This is prohibited for Play release. The debug keystore is public, reproducible,
and unsuitable as a durable upload identity.

Current version:

```text
versionName 1.0
versionCode 1
```

Recommended first release:

```text
versionName 0.9.0
versionCode supplied by release automation
```

Current merged Release manifest disables cleartext traffic. The app's documented
manual/Bonjour/bridge flows commonly use user-entered HTTP and WS endpoints, so
the existing release policy can break core self-hosted use.

## Secret model

Local inputs should be environment variables or an ignored properties file:

```text
ANDROID_UPLOAD_STORE_FILE
ANDROID_UPLOAD_STORE_PASSWORD
ANDROID_UPLOAD_KEY_ALIAS
ANDROID_UPLOAD_KEY_PASSWORD
ANDROID_VERSION_CODE
ANDROID_VERSION_NAME
```

GitHub Environment secrets should contain the keystore as base64 plus passwords:

```text
ANDROID_UPLOAD_KEYSTORE_BASE64
ANDROID_UPLOAD_STORE_PASSWORD
ANDROID_UPLOAD_KEY_ALIAS
ANDROID_UPLOAD_KEY_PASSWORD
```

GitHub is not the only backup. Keep an encrypted offline keystore copy and
password-manager records accessible to at least two authorized company
operators.

## Execution plan

Status: Draft

After owner decisions from task `010`, generate a new upload key with company
identity, protect it, and record its certificate fingerprints. Configure Gradle
to require production signing values for Release and fail clearly when absent.
Allow unsigned diagnostic configuration only through an explicit non-release
path. Supply version code through Gradle properties/environment without
rewriting source files during CI.

Implement the approved HTTP/WS policy. If insecure self-hosted connections stay
supported, prefer an explicit user opt-in/warning rather than silently treating
cleartext as secure.

### Implementation decisions and open questions

- Decision: use Google Play App Signing and a separate upload key.
- Decision: do not use another private git signing repository for Android.
- Decision: never commit the keystore or passwords.
- Recommendation: `versionName 0.9.0`.
- Recommendation: version code is an explicit CI/local input chosen to be
  greater than all Play track version codes.
- Material open question: require TLS only, or support cleartext self-hosted
  connections with explicit warning/consent.
- Material open question: whether the upload key uses PKCS12 or JKS. Prefer
  PKCS12 unless tooling compatibility requires JKS.

### Documentation

- Document local signing input names and recovery procedures without example
  real secrets.
- Put upload-key custody and reset procedures in the private operational
  runbook.
- Update user-facing connection guidance if Release security behavior changes.

### Task checklist

- [ ] Confirm version and HTTP/WS decisions.
- [ ] Generate and securely back up the upload key.
- [ ] Record SHA-1/SHA-256 fingerprints and alias in the password manager.
- [ ] Add ignore rules for all plausible upload-keystore/property paths.
- [ ] Add environment/property-driven production signing.
- [ ] Make missing Release signing inputs fail clearly.
- [ ] Add environment/property-driven version name/code.
- [ ] Implement and test the approved network policy.
- [ ] Build and inspect a signed AAB.

### Requirement verification

- Identity: inspect AAB package and installed app label.
- Versioning: build twice with distinct version codes without source mutation;
  reject invalid/non-increasing inputs in release automation.
- Signing: verify AAB certificate matches the recorded upload-key fingerprint
  and differs from the debug certificate.
- Secret safety: `git status`, ignore checks, and secret-pattern scans.
- Network behavior: production-like build tests for HTTPS/WSS and the approved
  HTTP/WS behavior on a physical device.

### Additional implementation verification

- Verify the key can sign on a clean machine using only documented inputs.
- Verify backup restoration before relying on the key for a permanent package.