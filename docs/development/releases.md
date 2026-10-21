# Release quick reference

This page collects the short release sequences for the distributable Crystal
Lattice packages. Run commands from the repository root unless a section says
otherwise.

Use this page as an operational checklist. The package-owned documentation
linked under [Detailed release documentation](#detailed-release-documentation)
remains authoritative for credentials, signing, failure recovery, versioning,
and infrastructure setup.

In VS Code, open **Tasks: Run Task** from the Command Palette and filter for
`Release:`. Tasks that publish, upload, create tags, or make downloads public
are deliberately separate from verification and candidate-build tasks.

## Current release paths

| Package | Official release path | Published result |
| --- | --- | --- |
| Crystal Lattice CLI | Root release script and tag-triggered GitHub Actions matrix | GitHub Release and public CLI download CDN |
| Desktop for macOS | GitHub candidate build followed by a separate candidate-publication dispatch | Signed and notarized universal DMG on the public download CDN |
| Mobile for iOS | Local Fastlane or manually dispatched GitHub Actions workflow | Internal TestFlight build |
| Mobile for Android | No production release path is currently implemented | No Google Play release |

## CLI

The CLI release command requires a clean `main` worktree whose `HEAD` matches
`origin/main`. It validates the release state, creates and pushes the version
tag, watches the complete platform matrix, publishes the GitHub Release, and
publishes the download CDN.

| Sequence | Command | VS Code task |
| --- | --- | --- |
| 1. Bump the patch version | `npm run release:cli:version:bump-patch` | `Release: CLI: Bump Patch Version` |
| 2. Review, commit, and push the version change | Use the normal reviewed Git workflow | — |
| 3. Preview the release without changing Git or GitHub | `npm run release:cli:plan` | `Release: CLI: Plan` |
| 4. Run the complete local gate without creating a tag | `npm run release:cli:gate` | `Release: CLI: Gate` |
| 5. Create and publish the release | `npm run release:cli` | `Release: CLI: Publish` |
| 6. Verify the public installers and downloads | `npm run release:cli:smoke` | `Release: CLI: Smoke Test` |

Minor and major version changes are currently edited deliberately instead of
being exposed as one-click release tasks. The final tag must be
`crystal-lattice-cli-v<version>`.

## Desktop for macOS

### Local candidate preparation

These commands do not publish a download:

| Purpose | Command | VS Code task |
| --- | --- | --- |
| Run the desktop release verification lane | `npm run desktop:macos:release:verify` | `Release: Desktop: Verify Locally` |
| Build an unsigned universal archive | `npm run desktop:macos:release:build` | `Release: Desktop: Build Unsigned Universal Archive` |
| Build a signed, notarized, and stapled DMG | `MACOS_BUILD_NUMBER=<number> npm run desktop:macos:build` | `Release: Desktop: Build Signed and Notarized DMG Locally` |

The signed local build uses the current worktree and remains under the ignored
desktop `build/macos-release/` directory. Inspect and launch-test the actual DMG
before treating it as a viable candidate.

### Official GitHub candidate and publication

The official path is intentionally two-stage. The first workflow run builds and
stores a candidate without publishing it. The second workflow run publishes
that exact candidate by its successful workflow run ID.

| Sequence | Command | VS Code task |
| --- | --- | --- |
| 1. Start the candidate build from `main` | `MACOS_BUILD_NUMBER=<number> npm run desktop:macos:release:candidate:start` | `Release: Desktop: Start GitHub Candidate Build` |
| 2. Watch the candidate workflow | `npm run desktop:macos:release:watch` | `Release: Desktop: Watch Latest GitHub Run` |
| 3. Review its commit, DMG checksum, metadata, and notarization result | Inspect the completed GitHub Actions run and record its run ID | — |
| 4. Publish the reviewed candidate | `DESKTOP_CANDIDATE_RUN_ID=<run-id> npm run desktop:macos:release:publish:start` | `Release: Desktop: Publish GitHub Candidate` |
| 5. Watch publication and CDN verification | `npm run desktop:macos:release:watch` | `Release: Desktop: Watch Latest GitHub Run` |

The VS Code candidate tasks prompt for the optional build number and the
required publication candidate run ID.

## Mobile for iOS

### Local TestFlight path

Local builds require the pinned Ruby/Bundler dependencies and an ignored
`mobile/crystal-lattice-control-rn/fastlane/.env` containing the documented
App Store Connect and read-only `match` credentials.

| Purpose | Command | VS Code task |
| --- | --- | --- |
| Run release verification | `npm run mobile:ios:release:verify` | `Release: Mobile iOS: Verify Locally` |
| Build a signed IPA without uploading it | `npm run mobile:ios:release:build` | `Release: Mobile iOS: Build Signed IPA Locally` |
| Verify, build, and upload to internal TestFlight | `TESTFLIGHT_CHANGELOG="<text>" npm run mobile:ios:release:testflight` | `Release: Mobile iOS: Upload to TestFlight Locally` |

The changelog is optional. The VS Code upload task prompts for it and passes it
as TestFlight's **What to Test** text.

### GitHub Actions TestFlight path

The GitHub workflow is manual-only and always dispatches from `main`.

| Sequence | Command | VS Code task |
| --- | --- | --- |
| 1. Run verification and create a signed IPA without uploading | `npm run mobile:ios:testflight:build:start` | `Release: Mobile iOS: Start GitHub Build Only` |
| 2. Watch the build-only run | `npm run mobile:ios:testflight:watch` | `Release: Mobile iOS: Watch Latest GitHub Run` |
| 3. Start the internal TestFlight upload | `TESTFLIGHT_CHANGELOG="<text>" npm run mobile:ios:testflight:start` | `Release: Mobile iOS: Start GitHub TestFlight Upload` |
| 4. Watch the upload run | `npm run mobile:ios:testflight:watch` | `Release: Mobile iOS: Watch Latest GitHub Run` |

Use the build-only mode after rotating signing or App Store Connect
credentials. It proves verification, signing, archive, and export without
uploading or retaining the IPA.

## Mobile for Android

Android development builds exist, but production upload signing, Android
Fastlane release lanes, and a Google Play deployment workflow are not
implemented. Do not treat `npm run mobile:android` or a debug-signed Gradle
release build as a Google Play release sequence.

## Detailed release documentation

- [CLI release and distribution](https://github.com/dynamicprogrammingsolutions/crystal-lattice/blob/main/application/python/README.md#making-a-cli-release)
- [Desktop macOS direct-download release](../packages/crystal-lattice-control-desktop/development/macos-release.md)
- [Mobile iOS TestFlight with Fastlane](https://github.com/dynamicprogrammingsolutions/crystal-lattice/blob/main/mobile/crystal-lattice-control-rn/README.md#testflight-with-fastlane)
- [CLI download infrastructure and release recovery](https://github.com/dynamicprogrammingsolutions/crystal-lattice/blob/main/deploy/aws-cli-downloads/README.md#release-orchestration)
- [VS Code task definitions](https://github.com/dynamicprogrammingsolutions/crystal-lattice/blob/main/.vscode/tasks.json)
- [Root command definitions](https://github.com/dynamicprogrammingsolutions/crystal-lattice/blob/main/package.json)