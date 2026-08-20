# Add GitHub Actions iOS Continuous Deployment

Add a GitHub Actions workflow that runs verification and uploads iOS builds to TestFlight through fastlane.

## Requirements checklist

- [ ] Add a GitHub Actions workflow for iOS TestFlight deployment.
- [ ] Trigger manually with `workflow_dispatch`; optionally add tag-based release triggers after approval.
- [ ] Install Node 20 dependencies, Ruby/bundler dependencies, and CocoaPods.
- [ ] Run mobile verification before uploading.
- [ ] Configure Apple authentication and signing through GitHub secrets.
- [ ] Call the fastlane beta lane.
- [ ] Document all required GitHub secrets and environment protections.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/070-fastlane-ios-testflight.md

## Known Starting State

Current `.github/workflows` contains workflows for docs/CLI release, but no mobile iOS deployment workflow was found.

The app package expects:

- Node `>=20`
- React Native `0.82.1`
- npm scripts:
  - `npm run tsc`
  - `npm test`
  - `npm run lint`
  - `npm run pod-install`

Suggested workflow shape:

```yaml
on:
  workflow_dispatch:
```

Suggested job outline:

1. Checkout.
2. Setup Node 20 with npm cache.
3. Install dependencies from `mobile/crystal-lattice-control-rn`.
4. Setup Ruby and Bundler cache.
5. Install pods.
6. Run `npm run tsc`.
7. Run `npm test -- --runInBand`.
8. Run fastlane beta lane with App Store Connect API key and signing credentials.

Secrets to document depend on signing strategy, but likely include:

- App Store Connect API key ID
- App Store Connect issuer ID
- App Store Connect private key
- Apple team ID
- Match git URL/token and match password, if using `match`
- Or encrypted certificate/provisioning-profile secrets, if using manual signing assets

## Acceptance Criteria

- Workflow can be started manually from GitHub Actions.
- Workflow fails before upload if verification fails.
- Workflow does not expose signing material or App Store Connect keys in logs.
- Workflow uploads to TestFlight when secrets and App Store Connect app record are present.

## Execution plan

Status: Approved

Add a manually dispatched GitHub Actions workflow with two explicit modes:

- Safe default: verify and create a production-signed IPA on the ephemeral
  runner without uploading it.
- Explicit upload: verify, archive, and call `fastlane ios beta` to upload an
  internal TestFlight build.

Use the GitHub-hosted `macos-26` arm64 runner and explicitly select its installed
Xcode 26.1.1 toolchain, matching the locally verified Xcode 26.1 release family.
Install Node 20, Ruby 3.4.10, the locked Bundler dependencies, npm dependencies,
and CocoaPods dependencies from the owning mobile package.

Create an ephemeral fastlane keychain on CI before match installs the Apple
Distribution identity. Give CI read-only access to the separate signing
repository through a repository-specific SSH deploy key. Store the match
password and App Store Connect API-key material as encrypted GitHub repository
secrets, and store non-sensitive identifiers as repository variables.

The `dynamicprogrammingsolutions` organization is currently on GitHub Free and
the application repository is private. Protected environments, environment
secrets, and required deployment reviewers are therefore not available for this
repository. Use repository secrets now, keep the workflow manual-only, document
the limitation, and recommend moving the secrets to a protected
`ios-testflight` environment if the repository gains a plan supporting
environments for private repositories.

### Implementation decisions and open questions

- Decision: do not add tag or push triggers yet.
- Decision: default `upload_to_testflight` to `false`; task `090` will perform
  the first explicit upload.
- Decision: use a read-only deploy key limited to
  `crystal-lattice-ios-signing`, not a broad personal access token.
- Decision: use repository secrets because protected environments are
  unavailable under the current GitHub plan/repository visibility.
- Decision: do not upload the signed IPA as a GitHub artifact; the build-only
  mode validates CI and then allows the ephemeral runner to discard it.
- Decision: pin third-party workflow actions to reviewed commit SHAs.
- Open operational decision: if the GitHub plan later changes, migrate all iOS
  release secrets into a protected `ios-testflight` environment and require a
  reviewer for the upload job.

### Documentation

- Extend the mobile TestFlight documentation with workflow inputs, required
  variables/secrets, trigger steps, current protection limitations, and secret
  rotation guidance.
- Keep the first real upload and App Store Connect processing evidence in task
  `090`.

### Task checklist

- [ ] Add CI-safe ephemeral keychain setup to fastlane.
- [ ] Add the manual GitHub Actions iOS workflow.
- [ ] Add safe build-only and explicit TestFlight-upload modes.
- [ ] Configure Node, Ruby, Bundler, npm, CocoaPods, and Xcode validation.
- [ ] Create and register a read-only signing-repository deploy key.
- [ ] Configure required GitHub repository variables and secrets.
- [ ] Validate workflow syntax, action pins, and secret handling.
- [ ] Run the workflow in build-only mode from a GitHub branch where the
      workflow is available.
- [ ] Document operation, protection limitations, and secret rotation.

### Requirement verification

- Workflow requirement: GitHub recognizes the workflow and accepts a manual
  dispatch.
- Toolchain requirement: the build-only run reports Node 20, Ruby 3.4.10,
  bundled CocoaPods 1.16.2, and Xcode 26.
- Verification requirement: `ios verify` passes before either signed-build or
  upload mode continues.
- Secret/signing requirement: CI decrypts match assets through the read-only
  deploy key and signs using an ephemeral keychain without exposing credentials.
- Upload requirement: static inspection confirms the explicit upload branch
  calls `fastlane ios beta`; task `090` records the first real upload.
- Documentation requirement: maintainers have exact setup, trigger, rotation,
  and plan-limitation instructions.

### Additional implementation verification

- Confirm the signing deploy key is read-only and scoped only to the signing
  repository.
- Confirm `.p8`, match password, private deploy key, IPA, and generated keychain
  files are absent from source control and workflow logs.
- Confirm workflow concurrency prevents overlapping iOS signing/deployment runs.

## Implementation Notes

The first build-only workflow run, `32409621399`, started on 2026-08-20 and
confirmed that GitHub recognized the workflow, resolved all required repository
variables/secrets, and scheduled the `macos-26` runner with Xcode 26.6. It
stopped in the Xcode validation step before dependency installation, signing,
or upload.

Cause: the step invoked `xcodebuild -version` a second time through a
short-circuiting `grep` pipeline. After `grep` matched and closed the pipe,
Xcode 26.6 aborted while writing its remaining output. The step now captures
the version output once, prints it, and validates the captured string.

The second build-only run, `32409753046`, passed toolchain setup, CocoaPods, and
the complete mobile verification lane. It also confirmed that the read-only
deploy key cloned the signing repository, match decrypted the repository, and
the ephemeral keychain received the Apple Distribution certificate and App
Store profile. The upload step was skipped as configured.

The archive then failed because the application target inherited the
project-level `iPhone Developer` identity for its Release configuration. On a
clean runner Xcode consequently requested an iOS App Development profile even
though match had installed the App Store profile. The app target now declares
automatic signing for Debug and manual `Apple Distribution` signing with the
named match App Store profile for Release. This target-level override does not
force signing settings onto CocoaPods targets.

The third build-only run, `32410370824`, confirmed the Release signing fix:
Xcode found the installed App Store profile and progressed into native
compilation. It then failed while compiling React Native's `fmt` dependency
under the runner's default Xcode 26.6 because of consteval format-string errors.
The same dependency graph archives successfully under the locally verified
Xcode 26.1 toolchain. The workflow now explicitly selects Xcode 26.1.1, which is
installed on the `macos-26` runner image, before validation and build.
