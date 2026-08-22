# Prepare Google Play Privacy, Permissions, And App Content Answers

Translate actual Android app behavior and the confirmed self-hosted operating
model into accurate Google Play Data safety, App content, permission, rating,
and reviewer-access answers.

## Requirements checklist

- [ ] The final merged Release manifest and every bundled SDK are audited for
      permissions and data behavior.
- [ ] Unnecessary legacy or sensitive permissions are removed.
- [ ] A Google Play Data safety answer sheet accurately describes collection,
      sharing, security, deletion, and ephemeral processing.
- [ ] Privacy policy, support, ads, account, target-audience, content-rating, and
      app-access answers are prepared.
- [ ] The answer sheet distinguishes user-selected self-hosted transmission from
      data collected by Dynamic Programming Solutions Kft.
- [ ] Internal-testing exemptions are not incorrectly treated as production
      readiness.

Parent Task: tasks/20260820-android-google-play-github-fastlane/000-main.md
Depends On: tasks/20260820-android-google-play-github-fastlane/020-android-release-build-audit.md
Depends On: tasks/20260820-android-google-play-github-fastlane/040-android-identity-versioning-and-upload-signing.md

## Required reading

Read the parent task's `Shared required reading`, then:

- `tasks/20260614-ios-testflight-github-fastlane/050-privacy-landing-page-compliance.md`
- `landing_page/src/pages/privacy.astro`
- `landing_page/src/pages/support.astro`
- Final merged Android Release manifest from task `020`
- Data safety overview:
  https://support.google.com/googleplay/android-developer/answer/10787469
- Data safety definitions:
  https://support.google.com/googleplay/android-developer/answer/10787469#zippy=%2Cdata-collection
- App content:
  https://support.google.com/googleplay/android-developer/answer/9859455
- Permissions policy:
  https://support.google.com/googleplay/android-developer/answer/9888170
- Content ratings:
  https://support.google.com/googleplay/android-developer/answer/9898843

## Confirmed product facts

- No developer-operated production bridge or public cloud-agent service.
- No developer-operated account is required.
- No analytics, advertising, tracking, or crash-reporting SDK is intentionally
  included.
- Saved endpoint details, pairing/cloud tokens, message caches, pinned actions,
  and UI preferences are stored locally for functionality.
- Messages and chosen attachments are sent to environments selected/configured
  by the user and may reach AI providers configured by that environment.
- Dynamic Programming Solutions Kft. does not receive or retain those app data
  flows under the current operating model.
- Support email correspondence is voluntary and retained as business
  correspondence outside the app.
- Existing privacy/support URLs are live.

## Audit focus

- Dependency-introduced `READ_EXTERNAL_STORAGE` and `WRITE_EXTERNAL_STORAGE`.
- Photo/document pickers, camera-roll/save behavior, and share provider.
- Local saved credentials/tokens and whether Android backup is disabled
  (`android:allowBackup="false"` currently is).
- HTTP/WS versus HTTPS/WSS transport and user warning.
- Any SDK update that introduces telemetry or a new permission.
- Deep-link input handling.

## Execution plan

Status: Draft

Audit the exact signed Release AAB/merged manifest, not package.json alone.
Trace each declared data type and permission to app functionality and a
retention/recipient model. Remove permissions that are not required. Prepare
console-ready answers and identify which attestations only an authorized human
can submit.

### Implementation decisions and open questions

- Recommendation: Data safety should state no developer/partner data collection
  under the confirmed operating model, while the privacy policy explains
  user-directed transmission to self-hosted services and configured providers.
- Recommendation: Ads declaration is No.
- Recommendation: no developer account and therefore no in-app account-deletion
  requirement.
- Open question: final content-rating responses for variable AI-generated/user
  content must be answered conservatively by the account owner.
- Open question: reviewer-access solution is owned by task `085`.

### Documentation

- Update the public privacy policy only for verified Android-specific facts.
- Keep console answer sheets and evidence in the task/maintainer release
  documentation.
- Do not claim Data safety completion publicly before Play Console submission.

### Task checklist

- [ ] Audit signed Release manifest and SDKs.
- [ ] Remove unnecessary permissions and rebuild.
- [ ] Map local storage and network transmission.
- [ ] Prepare Data safety responses.
- [ ] Prepare ads, account, target audience, content-rating, and app-access
      responses.
- [ ] Verify privacy/support pages remain accurate and live.
- [ ] Have the authorized owner submit/confirm console attestations.

### Requirement verification

- Manifest: final merged signed-release permission list.
- SDK behavior: source/config inspection plus dependency documentation where
  needed.
- Data safety: saved Play Console answers and owner attestation.
- Privacy/support: live URL inspection and app-access links.
- Permission behavior: physical-device checks for attachment/save/share flows.

### Additional implementation verification

- Compare Play SDK Index warnings for uploaded dependencies.
- Re-run the audit whenever native dependencies or product-operated services
  change.