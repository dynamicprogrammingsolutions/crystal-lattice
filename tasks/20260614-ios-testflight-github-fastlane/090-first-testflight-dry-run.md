# First Internal TestFlight Dry Run

Upload the first build to App Store Connect/TestFlight and validate install plus core app flows with internal testers.

## Requirements checklist

- [ ] Create or verify the App Store Connect app record.
- [ ] Upload the first build using fastlane locally or GitHub Actions.
- [ ] Wait for Apple build processing to complete.
- [ ] Add internal testers and install the build on a physical iPhone.
- [ ] Validate launch, permissions, connection flows, sessions/messages, and attachment flows.
- [ ] Record issues, fixes, and whether the build is suitable for external TestFlight preparation.

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
