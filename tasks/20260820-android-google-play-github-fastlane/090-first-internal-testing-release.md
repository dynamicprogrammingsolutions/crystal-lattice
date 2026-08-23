# Deliver And Verify The First Google Play Internal Release

Create the first production-signed Android App Bundle, initialize Google Play
App Signing/internal testing as needed, upload the release, and verify it on a
physical Android device.

## Requirements checklist

- [ ] The first signed AAB is built from the intended commit with the approved
      package, version name, version code, and upload certificate.
- [ ] Google Play accepts the AAB and Play App Signing is correctly configured.
- [ ] The release is published only to the internal testing track.
- [ ] Internal testers can opt in and install/update through Google Play.
- [ ] A physical-device smoke test covers core self-hosted app behavior.
- [ ] Play blocking errors, warnings, pre-launch findings, and SDK warnings are
      resolved or explicitly accepted with rationale.
- [ ] Release evidence is recorded without storing secrets.
- [ ] Task `070` and `080` are not marked complete on the strength of a skipped
      or manually substituted path.

Parent Task: tasks/20260820-android-google-play-github-fastlane/000-main.md
Depends On: tasks/20260820-android-google-play-github-fastlane/070-fastlane-google-play-release.md
Depends On: tasks/20260820-android-google-play-github-fastlane/080-github-actions-android-cd.md

## Required reading

Read the parent task's `Shared required reading`, then:

- Outputs from tasks `040`, `060`, `070`, and `080`
- Test an app bundle:
  https://developer.android.com/guide/app-bundle/test
- Internal testing:
  https://support.google.com/googleplay/android-developer/answer/9845334
- Publish a release:
  https://support.google.com/googleplay/android-developer/answer/9859348
- Pre-launch reports:
  https://support.google.com/googleplay/android-developer/answer/9842757

## Preconditions

- Verified organization Play Console account.
- App record exists for the permanent package name.
- Play App Signing choice approved.
- Upload key backed up and configured.
- Service account has required app permissions.
- Internal tester list/Google Group exists.
- Fastlane local signed build and credential validation pass.
- GitHub Environment secrets are configured.

## Required smoke-test scenarios

From a Google Play-installed build on at least one supported physical device:

1. Install/upgrade and verify app label/icon/splash.
2. Open Privacy Policy and Support before connecting.
3. Connect to an approved self-hosted runtime using the supported release
   transport policy.
4. Disconnect and reconnect from saved connection state.
5. List/create/open sessions.
6. Send a message and observe streamed/completed response.
7. Exercise representative plugin action/tool result.
8. Pick an image/document attachment and verify preview/send behavior.
9. Save/share a generated file.
10. Background and resume the app; verify recovery/reconnection.
11. Open a `crystal-lattice://` deep link if included in the release contract.
12. Verify no debug-only/test harness UI is exposed.

## Execution plan

Status: Draft

Prefer the GitHub Actions path for delivery after a local signed AAB proves the
signing setup. If Google requires initial App Signing/package initialization in
the Console, perform that manual step with the exact AAB produced by the
approved flow and record it. Do not weaken automation or upload a differently
built bundle merely to bypass a pipeline defect.

### Implementation decisions and open questions

- Decision: internal track only.
- Decision: physical-device Play install is required evidence.
- Decision: workflow success alone is insufficient without Play processing and
  installation verification.
- Open question: exact internal tester accounts from task `010`.
- Open question: whether first upload must be completed in Console before API
  upload works for this account/package.

### Documentation

- Record release version/code, commit, workflow run, Play release, tester group,
  and findings in task completion notes.
- Update the runbook with any account-specific first-release behavior.

### Task checklist

- [ ] Build/inspect the signed AAB locally.
- [ ] Run the protected GitHub workflow.
- [ ] Complete any required first-time Console/App Signing step.
- [ ] Confirm Play processing and internal publication.
- [ ] Configure/verify testers and opt-in URL.
- [ ] Install from Play on a physical device.
- [ ] Execute every smoke-test scenario.
- [ ] Review pre-launch/SDK/policy warnings.
- [ ] Record evidence and blockers.

### Requirement verification

- Bundle identity: AAB inspection and Play artifact details.
- Deployment: successful workflow run plus Play Console internal release.
- Distribution: tester opt-in and Play install/update.
- Functionality: human-confirmed physical-device checklist.
- Safety: no production rollout; no secrets in logs or evidence.

### Additional implementation verification

- Verify upgrade from an earlier internal build when a second build exists.
- Verify version-code collision handling by preparing the next candidate without
  uploading it.