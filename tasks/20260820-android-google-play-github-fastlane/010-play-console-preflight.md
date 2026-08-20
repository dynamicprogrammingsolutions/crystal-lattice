# Confirm Google Play Account And Release Preconditions

Establish the account, app-record, package-name, tester, API-project, and product
decisions required before permanent Android signing or Play deployment state is
created.

## Requirements checklist

- [ ] Google Play Console account ownership, organization verification, and
      authorized operators are confirmed.
- [ ] The intended Play Console app record and permanent package name are
      confirmed without ambiguity.
- [ ] The Google Cloud project and service-account ownership model are decided.
- [ ] Initial internal testers and the internal-only first-release boundary are
      confirmed.
- [ ] Android marketing version and insecure self-hosted connection behavior are
      decided.
- [ ] Account-only actions and their responsible human owner are documented.

Parent Task: tasks/20260820-android-google-play-github-fastlane/000-main.md

## Required reading

Read the parent task's `Shared required reading`, then:

- `mobile/crystal-lattice-control-rn/android/app/build.gradle`
- `mobile/crystal-lattice-control-rn/android/app/src/main/AndroidManifest.xml`
- Create and set up an app:
  https://support.google.com/googleplay/android-developer/answer/9859152
- Developer account types and verification:
  https://support.google.com/googleplay/android-developer/answer/13628312
- Google Play Developer API:
  https://developers.google.com/android-publisher/getting_started
- Testing tracks:
  https://support.google.com/googleplay/android-developer/answer/9845334

## Known facts

- Legal entity: Dynamic Programming Solutions Kft.
- Proposed Play app name: `Crystal Lattice Control`.
- Permanent package-name candidate:
  `com.dynamicprogrammingsolutions.crystallatticecontrolrn`.
- Default language recommendation: English (United States).
- App/game recommendation: App.
- Price recommendation: Free.
- Category recommendation: Productivity.
- First release recommendation: internal testing only.
- Support/review contact:
  `support@dynamicprogrammingsolutions.com`.
- The app has no developer-operated account, production bridge, or public cloud
  agent.

## Questions requiring owner answers

1. Does the company already have a verified Play Console organization account?
2. Who is the Play Console Account Owner, and which maintainers should receive
   Admin or Release Manager access?
3. Does an app record already exist for the package name?
4. Which Google Cloud project should own the Android Publisher API integration?
5. Which Google/Workspace email addresses should be internal testers?
6. Confirm `versionName 0.9.0` for the first Android release.
7. Confirm whether arbitrary local/self-hosted HTTP and WS connections remain a
   supported production requirement.
8. Confirm that closed/open/production promotion requires separate explicit
   approval.

## Execution plan

Status: Draft

Inspect Play Console and Google Cloud state with the authorized owner. Record
facts; do not create or change an app, project, service account, tester list, or
agreement without explicit authorization. Resolve package-name and connection
behavior before upload-key creation because both affect durable release
configuration.

### Implementation decisions and open questions

- Recommendation: organization account owned by Dynamic Programming Solutions
  Kft., not a personal developer account.
- Recommendation: keep the package name unchanged.
- Recommendation: align Android to `0.9.0`.
- Recommendation: preserve self-hosted HTTP/WS support with a visible insecure
  connection warning and preference for HTTPS/WSS.
- Recommendation: use a company-owned Google Cloud project dedicated or clearly
  scoped to release automation.
- All owner-answer questions above remain open until confirmed.

### Documentation

- Record account ownership and recovery roles in the private release runbook,
  not public user documentation.
- Do not record private identifiers, secrets, payment details, or personal
  recovery data in the task.

### Task checklist

- [ ] Confirm Play Console organization account status.
- [ ] Confirm app-record/package-name status.
- [ ] Confirm Cloud project and API-authentication owner.
- [ ] Confirm initial testers.
- [ ] Confirm version and HTTP/WS behavior.
- [ ] Record manual prerequisites and blockers for dependent tasks.

### Requirement verification

- Account state: human confirmation or read-only console inspection.
- Package/app state: Play Console app dashboard evidence.
- Cloud ownership: confirmed project ID and responsible owner without secret
  material.
- Tester/release boundary: owner-confirmed list and internal-only decision.
- Product decisions: explicit recorded answers for version and connection
  behavior.