# macOS direct-download release

The desktop package builds one universal Apple Silicon and Intel application
for macOS 14 or later. The distributable is an app-only DMG. Fastlane is the
local source of truth for signing, notarization, stapling, and release checks;
the GitHub Actions workflow calls the same lane.

The first release completed both the local and hosted GitHub Actions paths.
Local review builds use the same release lane; publication is a separate
explicit action.

The local and hosted universal Developer ID build, notarization, stapling,
Gatekeeper and launch smoke have been verified. Build-only run `36633536807`
produced `0.9.0 (4)` from clean source
`1a04b8689eab0821727be2c3efc9213e57ebafe7` on September 29, 2026.
Publication run `36685765746` published that exact candidate on September 30
through the existing download CDN.

The DMG contains the application and an Applications shortcut. Mount it, copy
Crystal Lattice Desktop to Applications and launch it there; Metro and a source
checkout are not required. The DMG does not install the CLI. Start a compatible
runtime separately and use the existing Desktop connection flow.

Current source/native website captures may include newer product changes.
They do not establish the contents of a previously published DMG; validate a
fresh signed candidate before publishing those changes.

## Local review DMG

From the repository root, build an installable review DMG with:

```bash
npm run desktop:macos:build
```

This delegates to the desktop package's `macos:build` script and the existing
Ruby wrapper, then runs `fastlane mac release`. The npm script enables all
release verification and forces read-only signing retrieval. It builds the
current working tree, including uncommitted changes. It neither installs nor
publishes the result.

Set up Node/npm dependencies, the pinned Ruby/Bundler environment, and
CocoaPods first. Copy `fastlane/.env.example` to the ignored `fastlane/.env`
inside the desktop package and restrict it to its owner (`chmod 600`).
Configure the existing credentials; a new certificate or signing repository is
not needed while the current ones remain valid:

| Desktop setting | Existing signing configuration |
| --- | --- |
| `APPLE_TEAM_ID` | Existing Apple team |
| `DESKTOP_MATCH_GIT_URL`, `DESKTOP_MATCH_GIT_BRANCH` | Existing mobile `MATCH_GIT_URL`, `MATCH_GIT_BRANCH` |
| `MATCH_PASSWORD` | Existing signing-repository encryption password |
| `DESKTOP_APP_STORE_CONNECT_KEY_ID`, `DESKTOP_APP_STORE_CONNECT_ISSUER_ID` | Existing mobile `APP_STORE_CONNECT_KEY_ID`, `APP_STORE_CONNECT_ISSUER_ID` |
| `DESKTOP_APP_STORE_CONNECT_KEY_PATH` | Absolute path to the existing owner-only `.p8` file; alternatively use the documented inline-key variables |
| `DEVELOPER_ID_APPLICATION_IDENTITY` | Exact Developer ID Application identity name or SHA-1 fingerprint used to sign the DMG |
| `MACOS_MARKETING_VERSION`, `MACOS_BUILD_NUMBER` | Deliberately selected version and positive integer build number |

Keep the desktop bundle ID from the example; do not copy the mobile bundle ID.
The signing repository also requires working SSH access. A configured
`MATCH_GIT_PRIVATE_KEY` may refer to the existing read-only deploy key; otherwise
the local SSH configuration is used. Enter any Keychain password only at the
local prompt. Never put credentials in command arguments, documentation, or
tracked files. Fastlane loads the package-local `.env`; ignored files are not
automatically shared between worktrees.

An exported setting overrides the local `.env`, for example:

```bash
MACOS_BUILD_NUMBER=5 npm run desktop:macos:build
```

The lane checks credentials before verification/build work. It preserves the
preceding `build/macos-release/` directory in a unique directory under
`build/macos-release-history/` before starting the archive. This includes old
DMGs, checksums and metadata, even if the new attempt fails. History is retained
until explicitly removed, so account for archive disk usage.

Success prints the absolute DMG path, version/build, checksum, metadata and
notarization-log paths, source cleanliness, and the exact `open` command.
Output remains under `build/macos-release/`. Open the DMG, quit the existing
app, then drag the app onto its Applications shortcut to install. The CLI is
separate and Metro is not required.

Before accepting a new candidate, mount the actual DMG and check its app's
signature, Gatekeeper acceptance, and ordinary launch without Metro.
Notarization does not prove runtime correctness. Preserve a working DMG until
this launch check passes. Local uncommitted builds have
`source_tree_clean = false`; the public candidate validator still requires a
clean reviewed source commit. The local command does not change the public
version or website download.
/var/folders/j5/g0_m7cb52q935c_px994vbp80000gn/T/crystal-roadmap-move-j8dazge7/0-theirs.txt

## Local toolchain and lanes

From `desktop/crystal-lattice-control-desktop-rn`, use Node 20+, Ruby 3.4.10,
and Xcode 26.1. The GitHub-hosted `macos-26` image uses Xcode 26.1.1.

```bash
npm ci
npm run ruby:check
RBENV_VERSION="$(cat .ruby-version)" rbenv exec bundle install
npm run pod-install
npm run release:verify
npm run release:build
```

The npm Ruby wrapper accepts an already-correct Ruby/Bundler environment, as
used by CI, and otherwise uses the `.ruby-version` installation through
`rbenv exec`. It fails with the expected and detected versions before invoking
CocoaPods or Fastlane. GUI-launched Xcode sources `macos/.xcode.env` and the
ignored `.xcode.env.local` so Node can be resolved from the repository
`.nvmrc` without relying on the GUI process `PATH`.

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
making it public.

After reviewing the run's source commit, version/build, checksum, and
notarization result, dispatch again with `publish_download = true` and set
`candidate_run_id` to that successful build-only run. The publication job
verifies the referenced run is a completed successful execution of this
workflow on `main`, downloads that exact artifact, and sends it to the existing
private S3/CloudFront download infrastructure without rebuilding:

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