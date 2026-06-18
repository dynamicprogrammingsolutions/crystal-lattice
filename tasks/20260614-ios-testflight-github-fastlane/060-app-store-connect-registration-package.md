# Prepare App Store Connect Registration Package

Assemble the metadata and review information required to register the app and submit a TestFlight build.

## Requirements checklist

- [ ] Prepare app identity fields: name, bundle ID, SKU, primary language, category, age rating inputs, copyright.
- [ ] Prepare support URL, marketing URL, and privacy policy URL.
- [ ] Prepare TestFlight beta app description, what-to-test text, feedback email, and review notes.
- [ ] Prepare Apple reviewer testing instructions, including how to access a usable backend/bridge/cloud environment.
- [ ] Confirm export compliance/encryption answers for network communication.
- [ ] Identify screenshots/app previews needed for eventual App Store release, even if not needed for initial internal TestFlight.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/050-privacy-landing-page-compliance.md

## Known Starting State

Likely values to confirm:

- App name: `Crystal Lattice Control`
- Bundle ID: `com.dynamicprogrammingsolutions.crystallatticecontrolrn`
- Platform: iOS
- Category: to be selected by product owner
- First TestFlight target: confirm internal-only vs external testers
- Privacy policy: landing page privacy section URL, to be verified in task `050`

External TestFlight review may require Apple reviewers to actually use the app. Since this app connects to local servers, bridge services, or cloud/orchestrated agents, the registration package should include one of:

- A reachable demo cloud/bridge environment.
- A test account and connection link.
- Clear reviewer notes explaining local-only behavior, if applicable.
- Screenshots/video only as supplementary material, not a substitute for a testable app if Apple expects access.

## Acceptance Criteria

- A product/account owner can create or complete the App Store Connect app record from this package without guessing.
- TestFlight metadata is written in review-ready prose.
- Reviewer access instructions are actionable.
- Any Apple-account-only fields that cannot be completed by the agent are listed with owner/action required.
