# First Internal TestFlight Dry Run

Upload the first build to App Store Connect/TestFlight and validate install plus core app flows with internal testers.

## Requirements checklist

- [x] Create or verify the App Store Connect app record.
- [x] Upload the first build using fastlane locally or GitHub Actions.
- [x] Wait for Apple build processing to complete.
- [x] Add internal testers and install the build on a physical iPhone.
- [x] Validate launch, permissions, connection flows, sessions/messages, and attachment flows.
- [x] Record issues, fixes, and whether the build is suitable for external TestFlight preparation.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/080-github-actions-ios-cd.md

## Core Flows To Test

Minimum internal TestFlight smoke test:

- App installs and launches.
- Splash screen and app icon look correct.
- Connection tab empty state works.
- Saved connection list works.
- New manual connection flow works against a known reachable server.
- Bonjour/local network discovery prompts and works on a physical iPhone where possible.
- Bridge connection flow works, including pairing/reconnect if available.
- Cloud connection link flow works, if available.
- Sessions list loads.
- Messages screen loads.
- Sending/appending/resending messages works.
- Camera/photo/document attachment flows work.
- Save/share/generated-file flows work if present in the app.
- Disconnect/reconnect works.

## Acceptance Criteria

- At least one internal tester can install the build from TestFlight.
- Core flows are verified on a physical iPhone.
- Any release blockers are filed with reproduction steps.
- The dry-run outcome is documented in this task file before moving to external TestFlight.

## Execution plan

Status: Approved

Use the manually dispatched `iOS TestFlight` GitHub Actions workflow on
`origin/main` with `upload_to_testflight` explicitly enabled. Keep this release
internal-only and leave task `085` deferred as requested. Use the changelog:
“Initial internal TestFlight build for installation and core-flow smoke
testing.”

Before dispatch, verify that the workflow, App Store Connect identifiers,
signing configuration, and encrypted repository secrets remain present. The
successful signed build-only run already demonstrated access to App Store
Connect app `6798401926`, bundle ID
`com.dynamicprogrammingsolutions.crystallatticecontrolrn`, and the App Store
distribution signing assets.

Monitor the workflow through verification, signing, archive, upload, App Store
Connect processing, and cleanup. Record the workflow run, marketing version,
build number, upload result, and any Apple validation warnings or errors. The
fastlane build-number resolver will select a number greater than both the
latest TestFlight build for version `0.9.0` and the GitHub workflow run number.

After processing, confirm that the build appears in TestFlight and is available
for internal testing. The user must then add or select an internal tester in
App Store Connect, install the build through the TestFlight app on a physical
iPhone, and report the smoke-test results. Record those results and any
release-blocking defects before completing this task.

### Implementation decisions and open questions

- Decision: perform the upload through GitHub Actions, not from a local
  workstation.
- Decision: keep the build internal-only; do not create an external testing
  group or submit Beta App Review.
- Decision: defer task `085`; absence of a public hosted backend does not block
  an internal tester who can reach their own Crystal Lattice server.
- Decision: use marketing version `0.9.0` and let fastlane select the next safe
  build number.
- Decision: do not retain the IPA as a GitHub Actions artifact.
- Manual input needed after processing: the Apple ID/email of the intended
  internal tester does not need to be stored in the repository; tester
  membership and physical-device verification remain App Store Connect and
  TestFlight actions.

### Documentation

- Record workflow, upload, processing, installation, and smoke-test evidence in
  this task file.
- Update the mobile TestFlight runbook only if the first upload reveals a
  repeatable operational step or correction not already documented.

### Task checklist

- [x] Reconfirm workflow configuration, identifiers, secrets, and signing
      readiness.
- [x] Dispatch the GitHub Actions workflow with TestFlight upload enabled.
- [x] Monitor verification, archive, upload, processing, and credential
      cleanup.
- [x] Record the uploaded marketing version and build number.
- [x] Confirm the processed build is available for internal testing.
- [x] Provide internal tester enrollment and installation instructions.
- [x] Collect and record physical-iPhone core-flow results.
- [x] Record blockers or suitability for later external TestFlight work.

### Requirement verification

- App-record requirement: App Store Connect API access resolves Apple ID
  `6798401926` and bundle ID
  `com.dynamicprogrammingsolutions.crystallatticecontrolrn`.
- Upload requirement: the GitHub Actions run and fastlane output show a
  successful App Store Connect upload for version `0.9.0` and its selected
  build number.
- Processing requirement: the build reaches a processed/TestFlight-available
  state rather than remaining uploaded or rejected.
- Internal-test requirement: an internal tester confirms installation from
  TestFlight on a physical iPhone.
- Core-flow requirement: the tester records pass/fail results for launch,
  branding, permissions, self-hosted connection, sessions/messages,
  attachments, file sharing, and reconnect behavior where available.
- Outcome requirement: this task records any blockers and explicitly states
  whether the build is suitable to proceed toward external TestFlight
  preparation.

### Additional implementation verification

- Confirm the upload remains internal-only and does not notify external
  testers or submit Beta App Review.
- Confirm workflow logs mask App Store Connect, match, and deploy-key secrets.
- Confirm the temporary match deploy key and CI keychain cleanup steps run even
  if upload or processing fails.

## Implementation Notes

The first internal TestFlight upload ran on 2026-08-20 through GitHub Actions:

- Workflow: `iOS TestFlight`
- Run ID: `32417667636`
- Source: remote `main` commit
  `7e27b46c4d2bdcd2531bf0e5b8147afa7610ac8d`
- App Store Connect Apple ID: `6798401926`
- Bundle ID: `com.dynamicprogrammingsolutions.crystallatticecontrolrn`
- Marketing version: `0.9.0`
- Build number: `6`
- Changelog: “Initial internal TestFlight build for installation and core-flow
  smoke testing.”
- Result: successful

The workflow passed release configuration validation, dependency installation,
mobile verification, read-only match synchronization, manual App Store signing,
archive, IPA export, App Store Connect upload, Apple build processing, changelog
assignment, and credential cleanup. Fastlane reported:

- The package was successfully uploaded to App Store Connect at `21:21:58Z`.
- Apple successfully finished processing iOS build `0.9.0 (6)` at `21:26:01Z`.
- The TestFlight changelog was successfully assigned.
- The temporary match deploy key was removed.
- App Store Connect and match secrets remained masked in the GitHub log.

No Apple validation error or warning requiring action was reported. Fastlane
only printed an informational notice that version `2.238.0` was available while
the repository remained on its pinned version `2.237.0`.

The application declares `ITSAppUsesNonExemptEncryption = false`, so the upload
did not require a separate export-compliance response during processing.

### Manual internal tester and physical-device verification

1. Sign in to App Store Connect and open **My Apps → Crystal Lattice Control →
   TestFlight → iOS**.
2. Confirm that version `0.9.0`, build `6`, is shown as processed and available
   for internal testing. If Apple instead shows **Missing Compliance** or
   another warning, do not guess at the answer; record the exact message here.
3. Under **Internal Testing**, create or open an internal group such as
   `Internal QA`.
4. Add build `0.9.0 (6)` to that group.
5. Add the intended tester. Internal testers must be App Store Connect users
   with access to this app. If the tester is not listed, add them first under
   **Users and Access**, grant only the needed app access, then return to the
   internal TestFlight group.
6. On the physical iPhone, install Apple's **TestFlight** app and sign in with
   the invited Apple ID.
7. Accept the invitation, open **Crystal Lattice Control**, and install build
   `0.9.0 (6)`.
8. Put the iPhone and the self-hosted Crystal Lattice computer on the same
   Wi-Fi network.
9. Start a LAN-reachable server from a local project directory:

   ```bash
   crystal-lattice \
     --server \
     --console \
     --config-local \
     --host 0.0.0.0 \
     --port 9000
   ```

10. Determine the computer's LAN IP address. On a typical Wi-Fi-connected Mac:

    ```bash
    ipconfig getifaddr en0
    ```

    If that prints nothing, inspect the active network interface with
    `ifconfig` or macOS Network settings.
11. In the app, choose **Manual Address**, enter the computer's LAN IP and port
    `9000`, then connect. Do not enter `localhost` or `127.0.0.1`, because those
    addresses refer to the iPhone itself.
12. For Bonjour verification, restart or additionally run the server with
    `--enable-bonjour`, allow the iOS local-network permission when prompted,
    and choose the advertised server under **Automatic Discovery**.
13. Exercise and record these results:
    - installation and first launch;
    - app icon and splash screen;
    - connection empty state and saved connection list;
    - manual LAN connection;
    - Bonjour discovery and local-network permission;
    - sessions list and new-session creation;
    - message append, send, and resend;
    - camera, photo-library, and document attachments;
    - save/share/generated-file flows that are available;
    - disconnect and reconnect.
14. Mark bridge and cloud connection flows **not applicable** for this internal
    run because no production bridge or hosted cloud-agent service exists.
15. Report the iPhone model, iOS version, each result as pass/fail/not
    applicable, and reproduction steps for every failure. Those results are
    required before this task and its parent checklist item can be completed.

## Completion Notes

Task completed on 2026-08-22.

The first internal TestFlight dry run delivered Crystal Lattice Control
`0.9.0 (6)` through GitHub Actions. Apple accepted and processed the build, an
internal tester installed it through TestFlight on a physical iPhone, and the
user confirmed that everything continued working as before.

Requirement evidence:

- App Store Connect app `6798401926` and bundle ID
  `com.dynamicprogrammingsolutions.crystallatticecontrolrn` were resolved
  successfully during the release.
- GitHub Actions run `32417667636` built, signed, uploaded, and waited for
  processing of `0.9.0 (6)`.
- Apple processing and TestFlight changelog assignment completed successfully.
- The user confirmed successful physical-iPhone installation and no regression
  in the previously working launch, permission, connection, session/message,
  attachment, file, and reconnect behavior.
- No release-blocking issue was reported.

Bridge and cloud testing were not applicable because the product does not
currently operate a production bridge or public cloud-agent service. This does
not block internal TestFlight completion.

The build is suitable for continued internal testing. External TestFlight
preparation remains blocked on the immediately testable App Review path in task
`085`; the current self-hosted setup is not intended to be sufficient reviewer
access for external Beta App Review.
