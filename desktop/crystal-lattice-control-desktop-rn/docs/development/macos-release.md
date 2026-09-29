# macOS direct-download release

The desktop package builds one universal Apple Silicon and Intel application
for macOS 14 or later. The distributable is an app-only DMG. Fastlane is the
local source of truth for signing, notarization, stapling, and release checks;
the GitHub Actions workflow calls the same lane.

The local universal Developer ID build, notarization, stapling, Gatekeeper,
and launch smoke have been verified. The hosted GitHub Actions run remains
pending until the workflow is committed and available on `main`.

## Local toolchain and lanes

From `desktop/crystal-lattice-control-desktop-rn`, use Node 20+, Ruby 3.4.10,
and Xcode 26.1. The GitHub-hosted `macos-26` image uses Xcode 26.1.1.

```bash
npm ci
bundle install
bundle exec pod install --project-directory=macos
bundle exec fastlane mac verify
bundle exec fastlane mac build
```

`verify` runs build-number tests, TypeScript, Jest, and Xcode Release
configuration inspection. `build` creates an unsigned universal archive for
checking bundled resources, metadata, and native architectures without Apple
credentials. `release` runs verification, downloads signing from `match`
read-only, creates a signed archive and app-only DMG, submits the DMG for
notarization, staples its ticket, checks Gatekeeper, and writes its SHA-256
checksum and `release-metadata.json` under the ignored
`build/macos-release/` directory.

Do not run `mac setup_signing` on CI. The Developer ID Application certificate
was created manually by the Apple Developer Account Holder. For this first
release, import its paired `.cer` and `.p12` into the existing private
`crystal-lattice-ios-signing` repository with:

```bash
bash scripts/import_developer_id_signing.sh \
  /path/to/developerID_application.cer \
  /path/to/Certificates.p12
```

The helper uses the existing ignored mobile `fastlane/.env` for signing
repository and App Store Connect API-key settings. It checks the selected
certificate fingerprint and private-key pairing; enter the `.p12` export
password only at the local OpenSSL prompt. At Fastlane's three prompts, enter
the two file paths printed by the helper, then press Return to omit the
provisioning profile. The helper transfers the identity through an
owner-only temporary keychain and produces a blank-password `.p12` using
Apple's `security export`, because macOS `security import` rejects the
equivalent empty-password OpenSSL package on a fresh keychain. This is a
**write** to the private encrypted signing repository; CI always reads it.
Confirm the synced identity appears as valid in a fresh keychain; Fastlane's
generic success text alone does not prove the private key was imported.
Normal Developer ID signing for this app syncs the certificate without a
provisioning profile; the Release entitlements do not request a capability
that requires one.
The original export contains the private key: keep it owner-readable only
and remove it when read-only retrieval has been verified. If the
certificate is renewed, review the pinned fingerprint in the helper before
importing its replacement.

After import, set the variables from `fastlane/.env.example` in an ignored local
file or the process environment. `MATCH_PASSWORD` is the existing encryption
password; `DESKTOP_MATCH_GIT_URL` is the same private git repository as iOS.
The App Store Connect key supplies notarization authentication. Use an
explicit build number when preparing a release for review:

```bash
MACOS_BUILD_NUMBER=1 bundle exec fastlane mac release
```

On CI, the build number defaults to the positive GitHub run number. Inspect
the output checksum, `notarization.json`, metadata, and DMG. A notarization
failure, a failed Gatekeeper assessment, or a missing architecture is a
release failure; do not distribute its DMG. The local archive is rebuilt from
the current working tree, so use a reviewed commit for a release candidate.

## GitHub Actions

The `Crystal Lattice Desktop release` workflow runs **only by manual dispatch
from `main`**. Its safe default, `publish_download = false`, verifies, signs,
notarizes, and stores the candidate as a seven-day workflow artifact without
making it public. Setting `publish_download = true` sends that exact verified
candidate to the existing private S3/CloudFront download infrastructure:

```text
https://download.crystallattice.dev/crystal-lattice-desktop/
```

The public files are the versioned DMG and checksum, versioned release and
notarization JSON, and `latest.txt`. The publisher rechecks the candidate
before AWS authentication; the public smoke test downloads the DMG and
checksum, verifies SHA-256, and checks clean-source and accepted-notarization
metadata. The application repository remains private.

The workflow reuses these **existing repository variables**:
`IOS_APPLE_TEAM_ID`, `IOS_MATCH_GIT_URL`, and `IOS_MATCH_GIT_BRANCH`. It reuses
these **existing repository secrets**:
`IOS_APP_STORE_CONNECT_KEY_ID`, `IOS_APP_STORE_CONNECT_ISSUER_ID`,
`IOS_APP_STORE_CONNECT_KEY_CONTENT`, `IOS_MATCH_PASSWORD`, and
`IOS_MATCH_GIT_PRIVATE_KEY`. These values refer to the same Apple team and
private signing repository as the iOS release. The SSH deploy key is
read-only and scoped to that repository. The workflow creates a temporary
keychain and removes the keychain and deploy-key file after the run.

Publication reuses `AWS_REGION`, `CLI_DOWNLOADS_BUCKET`,
`CLI_DOWNLOADS_PREFIX`, `CLI_DOWNLOADS_BASE_URL`,
`CLI_DOWNLOADS_CLOUDFRONT_DISTRIBUTION_ID`, and the
`CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME` secret. It additionally requires
`DESKTOP_DOWNLOADS_PREFIX=crystal-lattice-desktop` and the derived
`DESKTOP_DOWNLOADS_BASE_URL`. Before the first run, update the existing
CloudFormation downloads stack and OIDC role as documented in
`deploy/aws-desktop-downloads/README.md`.

GitHub Free on this private repository does not provide a required-reviewer
gate for this release. The workflow has no push or pull-request trigger, runs
only on `main`, keeps checkout credentials out of the working tree, and grants
AWS OIDC only to the optional publication job. Human approval is represented
by deliberately dispatching with `publish_download = true`. Website
publication remains separate.

To recover from a failed candidate, inspect the Fastlane log and Apple's
`notarization.json`, repair the cause in source or signing configuration,
then run the workflow again. Do not overwrite existing release assets. To
rotate the signing identity, perform the Account Holder certificate step
locally, import into the private match repository, and verify a read-only
build before removing the previous identity. To rotate an API or deploy key,
replace the existing iOS repository secret through GitHub's secure interface,
run the desktop build-only mode, and retire the old key only after a
successful build. The iOS workflow shares those credentials, so verify it
after rotation as well.